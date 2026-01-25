(() => {
  const state = {
    initialized: false,
    activeFieldId: null,
    activePageIndex: 0,
    selections: [],
    config: {},
    pdfIframe: null,
    // Шаблоны bbox
    templateSuggestions: {},
    currentIssn: null,
    journalName: null,
  };

  const boundOverlays = new WeakSet();

  /* =======================
     Utility helpers
  ======================= */

  const debounce = (fn, wait) => {
    let timer = null;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), wait);
    };
  };

  const notify = (message, level = "info") => {
    if (typeof window.toast === "function") {
      window.toast(message, level === "error" ? "error" : "info");
    } else {
      console[level === "error" ? "warn" : "info"](message);
    }
  };

  const normalizeRotation = (point, rotation, width, height) => {
    const rot = ((rotation || 0) % 360 + 360) % 360;
    const [x, y] = point;
    if (rot === 90) return [y, width - x];
    if (rot === 180) return [width - x, height - y];
    if (rot === 270) return [height - y, x];
    return [x, y];
  };

  const applyRotation = (point, rotation, width, height) => {
    const rot = ((rotation || 0) % 360 + 360) % 360;
    const [x, y] = point;
    if (rot === 90) return [width - y, x];
    if (rot === 180) return [width - x, height - y];
    if (rot === 270) return [y, height - x];
    return [x, y];
  };

  const getConfig = (key, fallback) => {
    const value = state.config[key];
    return value === undefined ? fallback : value;
  };

  /* =======================
     Field helpers
  ======================= */

  const defaultGetFieldColor = (fieldId) => {
    if (!fieldId) return "#1e88e5";
    if (fieldId.startsWith("author_")) return "#2e7d32";
    if (fieldId.startsWith("title")) return "#1e88e5";
    if (fieldId.startsWith("annotation")) return "#ef6c00";
    if (fieldId.startsWith("keywords")) return "#6a1b9a";
    if (fieldId.startsWith("references")) return "#616161";
    if (fieldId.startsWith("funding")) return "#00897b";
    return "#1e88e5";
  };

  const defaultGetFieldLabel = (fieldId) => {
    const btn = document.querySelector(`.field-btn[data-assign="${fieldId}"]`);
    return btn ? btn.textContent.trim() : fieldId;
  };

  const defaultApplyExtractedText = (fieldId, text) => {
    if (!fieldId || !text) return;
    const field = document.getElementById(fieldId);
    if (!field) return;

    let value = text.trim();

    if (fieldId === "keywords" || fieldId === "keywords_en") {
      if (typeof window.processKeywords === "function") {
        value = window.processKeywords(value);
      }
    } else if (fieldId === "references_ru" || fieldId === "references_en") {
      // Для списка литературы НЕ обрабатываем текст при извлечении —
      // оставляем как есть, чтобы можно было добавлять несколько областей
      // Обработка будет при финальном сохранении или по кнопке
    } else if (fieldId === "annotation" || fieldId === "annotation_en") {
      if (window.processAnnotation) {
        value = window.processAnnotation(value, fieldId === "annotation_en" ? "en" : "ru");
      }
    } else if (fieldId === "doi") {
      if (typeof window.extractDOI === "function") {
        const doi = window.extractDOI(value);
        if (doi) value = doi;
      }
    } else if (fieldId === "udc") {
      if (typeof window.extractUDC === "function") {
        const udc = window.extractUDC(value);
        if (udc) value = udc;
      }
    } else if (fieldId === "funding" || fieldId === "funding_en") {
      if (typeof window.processFunding === "function") {
        value = window.processFunding(value, fieldId === "funding_en" ? "en" : "ru");
      }
    }

    // Добавляем текст к существующему (если поле не пустое)
    if (field.value.trim()) {
      // Определяем разделитель в зависимости от типа поля
      let separator = " ";
      if (fieldId === "references_ru" || fieldId === "references_en") {
        separator = "\n";
      } else if (fieldId === "keywords" || fieldId === "keywords_en") {
        separator = ", ";
      }
      field.value = field.value.trim() + separator + value;
    } else {
      field.value = value;
    }

    field.dispatchEvent(new Event("input", { bubbles: true }));
    field.focus();
  };

  /* =======================
     Active field
  ======================= */

  const setActiveField = (fieldId) => {
    if (!fieldId) return;

    state.activeFieldId = fieldId;

    const label = document.querySelector(
      getConfig("activeFieldLabelSelector", "#bboxActiveField")
    );

    const getLabel = getConfig("getFieldLabel", defaultGetFieldLabel);

    if (label) {
      label.textContent = getLabel(fieldId) || fieldId;
    }

    document.querySelectorAll(".field-btn").forEach((b) => b.classList.remove("active"));
    document
      .querySelector(`.field-btn[data-assign="${fieldId}"]`)
      ?.classList.add("active");
  };

  /* =======================
     PDF.js bootstrap
  ======================= */

  const waitForPdfApp = () =>
    new Promise((resolve) => {
      let attempts = 0;
      const timer = setInterval(() => {
        attempts++;
        if (!document.body.contains(state.pdfIframe)) {
          clearInterval(timer);
          resolve(null);
          return;
        }
        const pdfWin = state.pdfIframe?.contentWindow;
        const app = pdfWin && pdfWin.PDFViewerApplication;
        if (app?.pdfViewer && app.eventBus) {
          clearInterval(timer);
          resolve(app);
        }
        if (attempts > 120) {
          clearInterval(timer);
          resolve(null);
        }
      }, 250);
    });

  /* =======================
     Overlay handling
  ======================= */

  const ensureOverlay = (pageView) => {
    if (!pageView || !pageView.div) return null;

    const canvas = pageView.div.querySelector("canvas");
    if (!canvas) return null;

    const pageContainer = canvas.parentElement;
    if (!pageContainer) return null;
    pageContainer.style.position = "relative";

    let overlay = pageContainer.querySelector(".bbox-overlay");

    if (!overlay) {
      // Создаём элемент в контексте документа iframe
      const ownerDoc = pageView.div.ownerDocument || document;
      overlay = ownerDoc.createElement("div");
      overlay.className = "bbox-overlay";
      overlay.style.position = "absolute";
      overlay.style.zIndex = "999";
      overlay.style.pointerEvents = "auto";
      pageContainer.appendChild(overlay);
    }

    overlay.style.left = `${canvas.offsetLeft}px`;
    overlay.style.top = `${canvas.offsetTop}px`;
    overlay.style.width = `${canvas.offsetWidth}px`;
    overlay.style.height = `${canvas.offsetHeight}px`;
    overlay.dataset.pageIndex = String(pageView.id - 1);

    if (!boundOverlays.has(overlay)) {
      boundOverlays.add(overlay);

      let drag = null;

      const getOverlayPoint = (e) => {
        // Получаем позицию курсора относительно overlay
        const rect = overlay.getBoundingClientRect();
        
        // Позиция курсора на экране минус позиция overlay на экране
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        if (e.type === "mousedown") {
          console.log("=== MOUSEDOWN ===");
          console.log("cursor clientX/Y:", e.clientX, e.clientY);
          console.log("overlay rect:", rect.left, rect.top, rect.width, rect.height);
          console.log("result x/y:", x, y);
        }
        
        return { x, y };
      };

      overlay.addEventListener("mousedown", (e) => {
        console.log("=== MOUSEDOWN EVENT ===");
        console.log("e.button:", e.button);
        console.log("state.activeFieldId:", state.activeFieldId);
        
        if (e.button !== 0) return;
        if (!state.activeFieldId) {
          notify("Выберите поле для bbox.");
          return;
        }

        const point = getOverlayPoint(e);
        console.log("point:", point);

        drag = {
          startX: point.x,
          startY: point.y,
          el: null,
        };

        // Создаём элемент в контексте документа iframe (не родительского окна)
        const ownerDoc = overlay.ownerDocument || document;
        const temp = ownerDoc.createElement("div");
        temp.className = "bbox-rect temp";
        temp.style.position = "absolute";
        temp.style.border = "2px solid red";
        temp.style.background = "rgba(255,0,0,0.2)";
        temp.style.pointerEvents = "none";
        temp.style.left = `${drag.startX}px`;
        temp.style.top = `${drag.startY}px`;
        temp.style.width = "0px";
        temp.style.height = "0px";
        temp.style.zIndex = "9999";

        console.log("temp style:", temp.style.cssText);
        
        overlay.appendChild(temp);
        drag.el = temp;
        
        console.log("temp appended, overlay children:", overlay.children.length);
        
        e.preventDefault();
      });

      overlay.addEventListener("mousemove", (e) => {
        if (!drag?.el) return;

        const { x, y } = getOverlayPoint(e);

        const left = Math.min(drag.startX, x);
        const top = Math.min(drag.startY, y);
        const width = Math.abs(x - drag.startX);
        const height = Math.abs(y - drag.startY);

        drag.el.style.left = `${left}px`;
        drag.el.style.top = `${top}px`;
        drag.el.style.width = `${width}px`;
        drag.el.style.height = `${height}px`;
        
        // Логируем каждые 10 пикселей движения
        if (width > 10 || height > 10) {
          console.log("DRAG:", { left, top, width, height });
        }
      });

      overlay.addEventListener("mouseup", async (e) => {
        if (!drag?.el) return;

        const { x: endX, y: endY } = getOverlayPoint(e);
        const { startX, startY } = drag;

        const left = Math.min(startX, endX);
        const top = Math.min(startY, endY);
        const width = Math.abs(endX - startX);
        const height = Math.abs(endY - startY);

        drag.el.remove();
        drag = null;

        if (width < 4 || height < 4) return;

        const pdfWin = state.pdfIframe?.contentWindow;
        const app = pdfWin?.PDFViewerApplication;
        const pageViewLocal = app?.pdfViewer?.getPageView(
          Number(overlay.dataset.pageIndex)
        );

        const viewport = pageViewLocal?.viewport;
        const pdfPage = pageViewLocal?.pdfPage;
        if (!viewport || !pdfPage) return;

        // ===== ШАГ 1: Получаем реальные размеры PDF страницы =====
        const pageRect = pdfPage.view; // [x1, y1, x2, y2] в PDF координатах
        const pdfWidth = pageRect[2] - pageRect[0];
        const pdfHeight = pageRect[3] - pageRect[1];
        
        console.log("PDF page size:", pdfWidth, "x", pdfHeight);

        // ===== ШАГ 2: Находим canvas и его размеры =====
        const canvas = pageViewLocal.div.querySelector("canvas");
        const canvasWidth = canvas.offsetWidth;
        const canvasHeight = canvas.offsetHeight;
        
        console.log("Canvas size:", canvasWidth, "x", canvasHeight);
        console.log("Viewport size:", viewport.width, "x", viewport.height);

        // ===== ШАГ 3: Масштаб из экранных координат в viewport =====
        const scale = viewport.width / canvasWidth;
        
        console.log("Scale factor:", scale);

        // ===== ШАГ 4: Преобразуем экранные координаты в viewport =====
        const vp_x1 = left * scale;
        const vp_y1 = top * scale;
        const vp_x2 = (left + width) * scale;
        const vp_y2 = (top + height) * scale;
        
        console.log("Viewport coords:", vp_x1, vp_y1, vp_x2, vp_y2);

        // ===== ШАГ 5: Преобразуем viewport в PDF координаты =====
        const [pdf_x1, pdf_y1] = viewport.convertToPdfPoint(vp_x1, vp_y1);
        const [pdf_x2, pdf_y2] = viewport.convertToPdfPoint(vp_x2, vp_y2);
        
        console.log("PDF coords (raw):", pdf_x1, pdf_y1, pdf_x2, pdf_y2);

        // ===== ШАГ 6: Нормализуем (PDF координаты идут снизу вверх) =====
        const normalized = {
          x1: Math.min(pdf_x1, pdf_x2),
          y1: Math.min(pdfHeight - pdf_y1, pdfHeight - pdf_y2),
          x2: Math.max(pdf_x1, pdf_x2),
          y2: Math.max(pdfHeight - pdf_y1, pdfHeight - pdf_y2),
        };
        
        console.log("Normalized PDF coords:", normalized);

        // ===== ШАГ 7: Сохраняем =====
        const selection = {
          schema: "pdfbbox-v2",
          id: window.crypto?.randomUUID?.() || 
              Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
          field_id: state.activeFieldId,
          page: Number(overlay.dataset.pageIndex),
          pdf_x1: normalized.x1,
          pdf_y1: normalized.y1,
          pdf_x2: normalized.x2,
          pdf_y2: normalized.y2,
          page_width: pdfWidth,
          page_height: pdfHeight,
        };

        // Добавляем новый bbox (не удаляем предыдущие — разрешаем множественное выделение)
        state.selections.push(selection);
        renderBboxes(app);

        const extractEndpoint = getConfig(
          "extractEndpoint",
          "/api/pdf-extract-text"
        );

        // Определяем тип поля для настройки опций
        const isReferencesField = selection.field_id === "references_ru" || selection.field_id === "references_en";
        
        // Для списка литературы: не удалять префиксы, не склеивать строки
        const options = isReferencesField ? {
          fix_hyphenation: true,
          strip_prefix: false,    // НЕ удалять номера [1], 1. и т.д.
          join_lines: false,      // НЕ склеивать строки (каждый источник на своей строке)
          merge_by_field: false,
        } : {
          fix_hyphenation: true,
          strip_prefix: true,
          join_lines: true,
          merge_by_field: false,
        };

        try {
          const resp = await fetch(extractEndpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              pdf_file: getConfig("pdfFile", ""),
              selections: [selection],
              options: options,
            }),
          });

          const data = await resp.json();
          const extracted = data?.extracted?.[0]?.text;

          if (extracted) {
            const applyFn = getConfig(
              "applyExtractedText",
              defaultApplyExtractedText
            );
            applyFn(selection.field_id, extracted);
            
            // Автоматически сохраняем в шаблон если ISSN установлен
            if (state.currentIssn) {
              saveToTemplate(selection.field_id, {
                page: selection.page,
                pdf_x1: selection.pdf_x1,
                pdf_y1: selection.pdf_y1,
                pdf_x2: selection.pdf_x2,
                pdf_y2: selection.pdf_y2,
                page_width: pdfWidth,
                page_height: pdfHeight,
              });
            }
          }
        } catch (err) {
          console.warn("PDF extract failed:", err);
        }
      });
    }

    return overlay;
  };

  /* =======================
     Rendering bboxes
  ======================= */

  const renderBboxes = (app) => {
    if (!app?.pdfViewer) return;

    const pageIndex = app.page - 1;
    state.activePageIndex = pageIndex;

    const pageView = app.pdfViewer.getPageView(pageIndex);
    if (!pageView) return;

    pageView.textLayer?.div &&
      (pageView.textLayer.div.style.pointerEvents = "none");
    pageView.annotationLayer?.div &&
      (pageView.annotationLayer.div.style.pointerEvents = "none");

    const overlay = ensureOverlay(pageView);
    if (!overlay) return;

    overlay.querySelectorAll(".bbox-rect").forEach((el) => el.remove());

    const viewport = pageView.viewport;
    const pdfPage = pageView.pdfPage;
    if (!pdfPage) return;

    // ===== ШАГ 1: Размеры PDF страницы =====
    const pageRect = pdfPage.view;
    const pdfWidth = pageRect[2] - pageRect[0];
    const pdfHeight = pageRect[3] - pageRect[1];

    // ===== ШАГ 2: Масштаб viewport → экран =====
    const canvas = pageView.div.querySelector("canvas");
    const scale = canvas ? canvas.offsetWidth / viewport.width : 1;

    const getColor = getConfig("getFieldColor", defaultGetFieldColor);
    const getLabel = getConfig("getFieldLabel", defaultGetFieldLabel);

    state.selections
      .filter((s) => s.page === pageIndex)
      .forEach((s) => {
        // ===== ШАГ 3: Обратное преобразование: PDF → viewport =====
        // Инвертируем Y (PDF координаты снизу вверх → сверху вниз)
        const pdf_y1_inverted = pdfHeight - s.pdf_y1;
        const pdf_y2_inverted = pdfHeight - s.pdf_y2;

        // Преобразуем в viewport (учитывает rotation автоматически)
        const [vp_x1, vp_y1] = viewport.convertToViewportPoint(s.pdf_x1, pdf_y1_inverted);
        const [vp_x2, vp_y2] = viewport.convertToViewportPoint(s.pdf_x2, pdf_y2_inverted);

        // ===== ШАГ 4: Viewport → экранные координаты =====
        const screen_x1 = vp_x1 * scale;
        const screen_y1 = vp_y1 * scale;
        const screen_x2 = vp_x2 * scale;
        const screen_y2 = vp_y2 * scale;

        const left = Math.min(screen_x1, screen_x2);
        const top = Math.min(screen_y1, screen_y2);
        const width = Math.abs(screen_x2 - screen_x1);
        const height = Math.abs(screen_y2 - screen_y1);

        // ===== ШАГ 5: Создаём элемент =====
        const ownerDoc = overlay.ownerDocument || document;
        const rect = ownerDoc.createElement("div");
        rect.className = "bbox-rect";
        const color = getColor(s.field_id);

        rect.style.position = "absolute";
        rect.style.borderColor = color;
        rect.style.border = `2px solid ${color}`;
        rect.style.background = `${color}22`;
        rect.style.left = `${left}px`;
        rect.style.top = `${top}px`;
        rect.style.width = `${width}px`;
        rect.style.height = `${height}px`;
        rect.style.pointerEvents = "auto";
        rect.style.boxSizing = "border-box";

        if (s.field_id === state.activeFieldId) {
          rect.classList.add("active");
        }

        const label = ownerDoc.createElement("div");
        label.className = "bbox-label";
        label.style.background = color;
        label.style.position = "absolute";
        label.style.top = "-18px";
        label.style.left = "0";
        label.style.fontSize = "10px";
        label.style.padding = "1px 4px";
        label.style.color = "white";
        label.style.borderRadius = "2px";
        label.style.whiteSpace = "nowrap";
        label.textContent = getLabel(s.field_id) || "bbox";

        rect.appendChild(label);

        rect.addEventListener("click", (e) => {
          e.stopPropagation();
          setActiveField(s.field_id);
          document.getElementById(s.field_id)?.focus();
        });

        overlay.appendChild(rect);
      });
  };

  /* =======================
     Controls
  ======================= */

  const clearPageSelections = () => {
    const pdfWin = state.pdfIframe?.contentWindow;
    const app = pdfWin?.PDFViewerApplication;
    if (!app) return;

    state.selections = state.selections.filter(
      (s) => s.page !== state.activePageIndex
    );

    renderBboxes(app);
  };

  const bindEscape = () => {
    document.addEventListener("keydown", (e) => {
      if (e.key !== "Escape") return;
      if (!state.pdfIframe || state.selections.length === 0) return;
      clearPageSelections();
    });
  };

  /* =======================
     Init
  ======================= */

  const init = (config = {}) => {
    if (state.initialized) return;

    state.config = config;
    state.pdfIframe = document.querySelector(
      getConfig("iframeSelector", "#pdfViewerIframe")
    );

    if (!state.pdfIframe) return;

    document
      .querySelector(getConfig("clearButtonSelector", "#bboxClearBtn"))
      ?.addEventListener("click", clearPageSelections);

    bindEscape();

    const boot = async () => {
      const app = await waitForPdfApp();
      if (!app) return;

      state.initialized = true;

      ensureOverlay(app.pdfViewer.getPageView(app.page - 1));
      renderBboxes(app);

      const debouncedRender = debounce(() => renderBboxes(app), 50);

      ["pagechanging", "scalechanging", "rotationchanging", "pagerendered", "pagesloaded"]
        .forEach(ev => app.eventBus.on(ev, debouncedRender));
    };

    state.pdfIframe.addEventListener("load", boot);

    if (state.pdfIframe.contentDocument?.readyState === "complete") {
      boot();
    } else {
      setTimeout(boot, 300);
    }
  };

  const saveSelections = async () => {
    if (!state.pdfIframe || state.selections.length === 0) return;

    const pdfWin = state.pdfIframe.contentWindow;
    const app = pdfWin?.PDFViewerApplication;

    const totalPages = app?.pagesCount || 0;
    const saveEndpoint = getConfig("saveEndpoint", "/api/pdf-save-coordinates");

    try {
      await fetch(saveEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          schema: "pdfbbox-v2",
          pdf_file: getConfig("pdfFile", ""),
          total_pages: totalPages,
          selections: state.selections,
        }),
      });
    } catch (err) {
      console.warn("PDF save failed:", err);
    }
  };

  /* =======================
     Template Functions
  ======================= */

  const loadTemplateSuggestions = async (issn, pageWidth = 595, pageHeight = 842) => {
    if (!issn) return null;
    
    state.currentIssn = issn;
    
    try {
      const resp = await fetch(
        `/api/bbox-templates/suggestions?issn=${encodeURIComponent(issn)}&page_width=${pageWidth}&page_height=${pageHeight}`
      );
      const data = await resp.json();
      
      if (data.suggestions && Object.keys(data.suggestions).length > 0) {
        state.templateSuggestions = data.suggestions;
        state.journalName = data.journal_name || "";
        console.log(`Loaded ${Object.keys(data.suggestions).length} template suggestions for ${issn}`);
        return data;
      }
    } catch (err) {
      console.warn("Failed to load template suggestions:", err);
    }
    
    return null;
  };

  const saveToTemplate = async (fieldId, coords) => {
    if (!state.currentIssn || !fieldId || !coords) return;
    
    try {
      const resp = await fetch("/api/bbox-templates/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          issn: state.currentIssn,
          journal_name: state.journalName || "",
          field_id: fieldId,
          coords: coords,
        }),
      });
      
      const data = await resp.json();
      if (data.success && data.suggestions) {
        state.templateSuggestions = data.suggestions.suggestions || {};
        console.log(`Saved template for ${fieldId}, confidence: ${data.suggestions.suggestions?.[fieldId]?.confidence || 0}`);
      }
    } catch (err) {
      console.warn("Failed to save to template:", err);
    }
  };

  const applySuggestion = async (fieldId) => {
    const suggestion = state.templateSuggestions[fieldId];
    if (!suggestion) {
      notify(`Нет шаблона для поля ${fieldId}`, "error");
      return null;
    }
    
    const coords = suggestion.coords;
    const pdfWin = state.pdfIframe?.contentWindow;
    const app = pdfWin?.PDFViewerApplication;
    
    if (!app) return null;
    
    // Создаём selection из шаблона
    const selection = {
      schema: "pdfbbox-v2",
      id: window.crypto?.randomUUID?.() || Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
      field_id: fieldId,
      page: coords.page,
      pdf_x1: coords.pdf_x1,
      pdf_y1: coords.pdf_y1,
      pdf_x2: coords.pdf_x2,
      pdf_y2: coords.pdf_y2,
      page_width: coords.page_width,
      page_height: coords.page_height,
      from_template: true,
      confidence: suggestion.confidence,
    };
    
    // Удаляем предыдущие bbox для этого поля
    state.selections = state.selections.filter(s => s.field_id !== fieldId);
    state.selections.push(selection);
    renderBboxes(app);
    
    // Извлекаем текст
    const extractEndpoint = getConfig("extractEndpoint", "/api/pdf-extract-text");
    const isReferencesField = fieldId === "references_ru" || fieldId === "references_en";
    
    const options = isReferencesField ? {
      fix_hyphenation: true,
      strip_prefix: false,
      join_lines: false,
      merge_by_field: false,
    } : {
      fix_hyphenation: true,
      strip_prefix: true,
      join_lines: true,
      merge_by_field: false,
    };
    
    try {
      const resp = await fetch(extractEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          pdf_file: getConfig("pdfFile", ""),
          selections: [selection],
          options: options,
        }),
      });
      
      const data = await resp.json();
      const extracted = data?.extracted?.[0]?.text;
      
      if (extracted) {
        const applyFn = getConfig("applyExtractedText", defaultApplyExtractedText);
        applyFn(fieldId, extracted);
        notify(`Шаблон применён (уверенность: ${Math.round(suggestion.confidence * 100)}%)`, "info");
        return extracted;
      }
    } catch (err) {
      console.warn("Failed to apply suggestion:", err);
    }
    
    return null;
  };

  const applyAllSuggestions = async () => {
    const suggestions = state.templateSuggestions;
    if (!suggestions || Object.keys(suggestions).length === 0) {
      notify("Нет доступных шаблонов", "error");
      return;
    }
    
    notify(`Применение ${Object.keys(suggestions).length} шаблонов...`, "info");
    
    for (const fieldId of Object.keys(suggestions)) {
      await applySuggestion(fieldId);
      // Небольшая задержка между запросами
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    notify("Все шаблоны применены", "info");
  };

  const getSuggestionStatus = () => {
    const suggestions = state.templateSuggestions;
    const fields = Object.keys(suggestions);
    
    return {
      available: fields.length > 0,
      count: fields.length,
      fields: fields.map(f => ({
        field_id: f,
        confidence: suggestions[f].confidence,
        sample_count: suggestions[f].sample_count,
      })),
      issn: state.currentIssn,
      journal_name: state.journalName,
    };
  };

  const showSuggestionsPanel = () => {
    const status = getSuggestionStatus();
    if (!status.available) {
      notify("Нет доступных шаблонов для этого журнала", "info");
      return;
    }
    
    // Создаём или показываем панель
    let panel = document.getElementById("bbox-suggestions-panel");
    if (!panel) {
      panel = document.createElement("div");
      panel.id = "bbox-suggestions-panel";
      panel.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        padding: 20px;
        z-index: 10000;
        max-width: 500px;
        max-height: 80vh;
        overflow-y: auto;
      `;
      document.body.appendChild(panel);
    }
    
    const fieldLabels = {
      title: "Название (рус)",
      title_en: "Название (англ)",
      annotation: "Аннотация (рус)",
      annotation_en: "Аннотация (англ)",
      keywords: "Ключевые слова (рус)",
      keywords_en: "Ключевые слова (англ)",
      references_ru: "Список литературы (рус)",
      references_en: "Список литературы (англ)",
      funding: "Финансирование (рус)",
      funding_en: "Финансирование (англ)",
    };
    
    let html = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
        <h3 style="margin: 0;">Шаблоны bbox</h3>
        <button onclick="document.getElementById('bbox-suggestions-panel').style.display='none'" 
                style="background: none; border: none; font-size: 20px; cursor: pointer;">×</button>
      </div>
      <p style="color: #666; margin-bottom: 15px;">
        Журнал: <strong>${status.journal_name || status.issn}</strong><br>
        Доступно шаблонов: <strong>${status.count}</strong>
      </p>
      <div style="margin-bottom: 15px;">
    `;
    
    for (const field of status.fields) {
      const label = fieldLabels[field.field_id] || field.field_id;
      const confidence = Math.round(field.confidence * 100);
      const color = confidence >= 70 ? "#4caf50" : confidence >= 40 ? "#ff9800" : "#f44336";
      
      html += `
        <div style="display: flex; align-items: center; padding: 8px; border-bottom: 1px solid #eee; gap: 5px;">
          <span style="flex: 1;">${label}</span>
          <span style="color: ${color}; min-width: 40px; text-align: right;">${confidence}%</span>
          <span style="color: #999; font-size: 11px; min-width: 30px;">(${field.sample_count})</span>
          <button onclick="window.PdfBbox.applySuggestion('${field.field_id}')" 
                  style="padding: 4px 10px; cursor: pointer; background: #e3f2fd; border: 1px solid #90caf9; border-radius: 3px;"
                  title="Применить шаблон">✓</button>
          <button onclick="window.PdfBbox.resetFieldTemplate('${field.field_id}')" 
                  style="padding: 4px 10px; cursor: pointer; background: #ffebee; border: 1px solid #ef9a9a; border-radius: 3px;"
                  title="Сбросить шаблон (удалить образцы)">✕</button>
        </div>
      `;
    }
    
    html += `
      </div>
      <p style="color: #888; font-size: 12px; margin: 10px 0;">
        💡 <strong>Подсказка:</strong> Если шаблон промахнулся — просто выделите правильную область вручную. 
        Новый образец улучшит точность. Кнопка ✕ сбрасывает все образцы для поля.
      </p>
      <div style="display: flex; gap: 10px; flex-wrap: wrap;">
        <button onclick="window.PdfBbox.applyAllSuggestions(); document.getElementById('bbox-suggestions-panel').style.display='none';"
                style="flex: 1; min-width: 120px; padding: 10px; background: #1976d2; color: white; border: none; border-radius: 4px; cursor: pointer;">
          ✓ Применить все
        </button>
        <button onclick="document.getElementById('bbox-suggestions-panel').style.display='none'"
                style="flex: 1; min-width: 120px; padding: 10px; background: #eee; border: none; border-radius: 4px; cursor: pointer;">
          Закрыть
        </button>
      </div>
      <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee;">
        <button onclick="window.PdfBbox.resetAllTemplates()"
                style="width: 100%; padding: 8px; background: #fff; color: #d32f2f; border: 1px solid #d32f2f; border-radius: 4px; cursor: pointer; font-size: 12px;">
          🗑 Удалить все шаблоны для этого журнала
        </button>
      </div>
    `;
    
    panel.innerHTML = html;
    panel.style.display = "block";
  };

  const resetFieldTemplate = async (fieldId) => {
    if (!state.currentIssn || !fieldId) {
      notify("Не удалось сбросить шаблон", "error");
      return false;
    }
    
    if (!confirm(`Сбросить все образцы для поля "${fieldId}"?\nЭто удалит накопленные данные шаблона.`)) {
      return false;
    }
    
    try {
      const resp = await fetch("/api/bbox-templates/reset-field", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          issn: state.currentIssn,
          field_id: fieldId,
        }),
      });
      
      const data = await resp.json();
      if (data.success) {
        // Удаляем из локального состояния
        delete state.templateSuggestions[fieldId];
        // Удаляем bbox для этого поля
        state.selections = state.selections.filter(s => s.field_id !== fieldId);
        
        // Перерисовываем
        const pdfWin = state.pdfIframe?.contentWindow;
        const app = pdfWin?.PDFViewerApplication;
        if (app) renderBboxes(app);
        
        notify(`Шаблон для "${fieldId}" сброшен`, "info");
        
        // Обновляем панель
        showSuggestionsPanel();
        return true;
      } else {
        notify(data.error || "Ошибка сброса шаблона", "error");
      }
    } catch (err) {
      console.warn("Failed to reset field template:", err);
      notify("Ошибка сброса шаблона", "error");
    }
    
    return false;
  };

  const resetAllTemplates = async () => {
    if (!state.currentIssn) {
      notify("ISSN журнала не установлен", "error");
      return false;
    }
    
    if (!confirm(`Удалить ВСЕ шаблоны для журнала ${state.currentIssn}?\nЭто действие нельзя отменить.`)) {
      return false;
    }
    
    try {
      const resp = await fetch("/api/bbox-templates/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ issn: state.currentIssn }),
      });
      
      const data = await resp.json();
      if (data.success) {
        state.templateSuggestions = {};
        state.selections = [];
        
        const pdfWin = state.pdfIframe?.contentWindow;
        const app = pdfWin?.PDFViewerApplication;
        if (app) renderBboxes(app);
        
        notify("Все шаблоны удалены", "info");
        
        // Закрываем панель
        const panel = document.getElementById("bbox-suggestions-panel");
        if (panel) panel.style.display = "none";
        
        // Удаляем кнопку применения шаблонов
        const btn = document.getElementById("applyTemplatesBtn");
        if (btn) btn.remove();
        
        return true;
      }
    } catch (err) {
      console.warn("Failed to reset all templates:", err);
    }
    
    return false;
  };

  window.PdfBbox = {
    init,
    setActiveField,
    saveSelections,
    clearPageSelections,
    getState: () => ({
      activeFieldId: state.activeFieldId,
      activePageIndex: state.activePageIndex,
      initialized: state.initialized,
      selections: state.selections.map((s) => ({ ...s })),
    }),
    // Template functions
    loadTemplateSuggestions,
    saveToTemplate,
    applySuggestion,
    applyAllSuggestions,
    getSuggestionStatus,
    showSuggestionsPanel,
    resetFieldTemplate,
    resetAllTemplates,
    setIssn: (issn, journalName = "") => {
      state.currentIssn = issn;
      state.journalName = journalName;
    },
  };
})();
