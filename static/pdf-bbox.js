(() => {
  const state = {
    initialized: false,
    activeFieldId: null,
    activePageIndex: 0,
    selections: [],
    config: {},
    pdfIframe: null,
    // РЁР°Р±Р»РѕРЅС‹ bbox
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
      // Р”Р»СЏ СЃРїРёСЃРєР° Р»РёС‚РµСЂР°С‚СѓСЂС‹ РќР• РѕР±СЂР°Р±Р°С‚С‹РІР°РµРј С‚РµРєСЃС‚ РїСЂРё РёР·РІР»РµС‡РµРЅРёРё вЂ”
      // РѕСЃС‚Р°РІР»СЏРµРј РєР°Рє РµСЃС‚СЊ, С‡С‚РѕР±С‹ РјРѕР¶РЅРѕ Р±С‹Р»Рѕ РґРѕР±Р°РІР»СЏС‚СЊ РЅРµСЃРєРѕР»СЊРєРѕ РѕР±Р»Р°СЃС‚РµР№
      // РћР±СЂР°Р±РѕС‚РєР° Р±СѓРґРµС‚ РїСЂРё С„РёРЅР°Р»СЊРЅРѕРј СЃРѕС…СЂР°РЅРµРЅРёРё РёР»Рё РїРѕ РєРЅРѕРїРєРµ
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

    // Р”РѕР±Р°РІР»СЏРµРј С‚РµРєСЃС‚ Рє СЃСѓС‰РµСЃС‚РІСѓСЋС‰РµРјСѓ (РµСЃР»Рё РїРѕР»Рµ РЅРµ РїСѓСЃС‚РѕРµ)
    if (field.value.trim()) {
      // РћРїСЂРµРґРµР»СЏРµРј СЂР°Р·РґРµР»РёС‚РµР»СЊ РІ Р·Р°РІРёСЃРёРјРѕСЃС‚Рё РѕС‚ С‚РёРїР° РїРѕР»СЏ
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
      // РЎРѕР·РґР°С‘Рј СЌР»РµРјРµРЅС‚ РІ РєРѕРЅС‚РµРєСЃС‚Рµ РґРѕРєСѓРјРµРЅС‚Р° iframe
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
        // РџРѕР»СѓС‡Р°РµРј РїРѕР·РёС†РёСЋ РєСѓСЂСЃРѕСЂР° РѕС‚РЅРѕСЃРёС‚РµР»СЊРЅРѕ overlay
        const rect = overlay.getBoundingClientRect();
        
        // РџРѕР·РёС†РёСЏ РєСѓСЂСЃРѕСЂР° РЅР° СЌРєСЂР°РЅРµ РјРёРЅСѓСЃ РїРѕР·РёС†РёСЏ overlay РЅР° СЌРєСЂР°РЅРµ
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
          notify("Р’С‹Р±РµСЂРёС‚Рµ РїРѕР»Рµ РґР»СЏ bbox.");
          return;
        }

        const point = getOverlayPoint(e);
        console.log("point:", point);

        drag = {
          startX: point.x,
          startY: point.y,
          el: null,
        };

        // РЎРѕР·РґР°С‘Рј СЌР»РµРјРµРЅС‚ РІ РєРѕРЅС‚РµРєСЃС‚Рµ РґРѕРєСѓРјРµРЅС‚Р° iframe (РЅРµ СЂРѕРґРёС‚РµР»СЊСЃРєРѕРіРѕ РѕРєРЅР°)
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
        
        // Р›РѕРіРёСЂСѓРµРј РєР°Р¶РґС‹Рµ 10 РїРёРєСЃРµР»РµР№ РґРІРёР¶РµРЅРёСЏ
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

        // ===== РЁРђР“ 1: РџРѕР»СѓС‡Р°РµРј СЂРµР°Р»СЊРЅС‹Рµ СЂР°Р·РјРµСЂС‹ PDF СЃС‚СЂР°РЅРёС†С‹ =====
        const pageRect = pdfPage.view; // [x1, y1, x2, y2] РІ PDF РєРѕРѕСЂРґРёРЅР°С‚Р°С…
        const pdfWidth = pageRect[2] - pageRect[0];
        const pdfHeight = pageRect[3] - pageRect[1];
        
        console.log("PDF page size:", pdfWidth, "x", pdfHeight);

        // ===== РЁРђР“ 2: РќР°С…РѕРґРёРј canvas Рё РµРіРѕ СЂР°Р·РјРµСЂС‹ =====
        const canvas = pageViewLocal.div.querySelector("canvas");
        const canvasWidth = canvas.offsetWidth;
        const canvasHeight = canvas.offsetHeight;
        
        console.log("Canvas size:", canvasWidth, "x", canvasHeight);
        console.log("Viewport size:", viewport.width, "x", viewport.height);

        // ===== РЁРђР“ 3: РњР°СЃС€С‚Р°Р± РёР· СЌРєСЂР°РЅРЅС‹С… РєРѕРѕСЂРґРёРЅР°С‚ РІ viewport =====
        const scale = viewport.width / canvasWidth;
        
        console.log("Scale factor:", scale);

        // ===== РЁРђР“ 4: РџСЂРµРѕР±СЂР°Р·СѓРµРј СЌРєСЂР°РЅРЅС‹Рµ РєРѕРѕСЂРґРёРЅР°С‚С‹ РІ viewport =====
        const vp_x1 = left * scale;
        const vp_y1 = top * scale;
        const vp_x2 = (left + width) * scale;
        const vp_y2 = (top + height) * scale;
        
        console.log("Viewport coords:", vp_x1, vp_y1, vp_x2, vp_y2);

        // ===== РЁРђР“ 5: РџСЂРµРѕР±СЂР°Р·СѓРµРј viewport РІ PDF РєРѕРѕСЂРґРёРЅР°С‚С‹ =====
        const [pdf_x1, pdf_y1] = viewport.convertToPdfPoint(vp_x1, vp_y1);
        const [pdf_x2, pdf_y2] = viewport.convertToPdfPoint(vp_x2, vp_y2);
        
        console.log("PDF coords (raw):", pdf_x1, pdf_y1, pdf_x2, pdf_y2);

        // ===== РЁРђР“ 6: РќРѕСЂРјР°Р»РёР·СѓРµРј (PDF РєРѕРѕСЂРґРёРЅР°С‚С‹ РёРґСѓС‚ СЃРЅРёР·Сѓ РІРІРµСЂС…) =====
        const normalized = {
          x1: Math.min(pdf_x1, pdf_x2),
          y1: Math.min(pdfHeight - pdf_y1, pdfHeight - pdf_y2),
          x2: Math.max(pdf_x1, pdf_x2),
          y2: Math.max(pdfHeight - pdf_y1, pdfHeight - pdf_y2),
        };
        
        console.log("Normalized PDF coords:", normalized);

        // ===== РЁРђР“ 7: РЎРѕС…СЂР°РЅСЏРµРј =====
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

        // Р”РѕР±Р°РІР»СЏРµРј РЅРѕРІС‹Р№ bbox (РЅРµ СѓРґР°Р»СЏРµРј РїСЂРµРґС‹РґСѓС‰РёРµ вЂ” СЂР°Р·СЂРµС€Р°РµРј РјРЅРѕР¶РµСЃС‚РІРµРЅРЅРѕРµ РІС‹РґРµР»РµРЅРёРµ)
        state.selections.push(selection);
        renderBboxes(app);

        const extractEndpoint = getConfig(
          "extractEndpoint",
          "/api/pdf-extract-text"
        );

        // РћРїСЂРµРґРµР»СЏРµРј С‚РёРї РїРѕР»СЏ РґР»СЏ РЅР°СЃС‚СЂРѕР№РєРё РѕРїС†РёР№
        const isReferencesField = selection.field_id === "references_ru" || selection.field_id === "references_en";
        
        // Р”Р»СЏ СЃРїРёСЃРєР° Р»РёС‚РµСЂР°С‚СѓСЂС‹: РЅРµ СѓРґР°Р»СЏС‚СЊ РїСЂРµС„РёРєСЃС‹, РЅРµ СЃРєР»РµРёРІР°С‚СЊ СЃС‚СЂРѕРєРё
        const options = isReferencesField ? {
          fix_hyphenation: true,
          strip_prefix: false,    // РќР• СѓРґР°Р»СЏС‚СЊ РЅРѕРјРµСЂР° [1], 1. Рё С‚.Рґ.
          join_lines: false,      // РќР• СЃРєР»РµРёРІР°С‚СЊ СЃС‚СЂРѕРєРё (РєР°Р¶РґС‹Р№ РёСЃС‚РѕС‡РЅРёРє РЅР° СЃРІРѕРµР№ СЃС‚СЂРѕРєРµ)
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
            
            // РђРІС‚РѕРјР°С‚РёС‡РµСЃРєРё СЃРѕС…СЂР°РЅСЏРµРј РІ С€Р°Р±Р»РѕРЅ РµСЃР»Рё ISSN СѓСЃС‚Р°РЅРѕРІР»РµРЅ
            // BBox templates are disabled: keep only per-article manual selections.
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

    // ===== РЁРђР“ 1: Р Р°Р·РјРµСЂС‹ PDF СЃС‚СЂР°РЅРёС†С‹ =====
    const pageRect = pdfPage.view;
    const pdfWidth = pageRect[2] - pageRect[0];
    const pdfHeight = pageRect[3] - pageRect[1];

    // ===== РЁРђР“ 2: РњР°СЃС€С‚Р°Р± viewport в†’ СЌРєСЂР°РЅ =====
    const canvas = pageView.div.querySelector("canvas");
    const scale = canvas ? canvas.offsetWidth / viewport.width : 1;

    const getColor = getConfig("getFieldColor", defaultGetFieldColor);
    const getLabel = getConfig("getFieldLabel", defaultGetFieldLabel);

    state.selections
      .filter((s) => s.page === pageIndex)
      .forEach((s) => {
        // ===== РЁРђР“ 3: РћР±СЂР°С‚РЅРѕРµ РїСЂРµРѕР±СЂР°Р·РѕРІР°РЅРёРµ: PDF в†’ viewport =====
        // РРЅРІРµСЂС‚РёСЂСѓРµРј Y (PDF РєРѕРѕСЂРґРёРЅР°С‚С‹ СЃРЅРёР·Сѓ РІРІРµСЂС… в†’ СЃРІРµСЂС…Сѓ РІРЅРёР·)
        const pdf_y1_inverted = pdfHeight - s.pdf_y1;
        const pdf_y2_inverted = pdfHeight - s.pdf_y2;

        // РџСЂРµРѕР±СЂР°Р·СѓРµРј РІ viewport (СѓС‡РёС‚С‹РІР°РµС‚ rotation Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРё)
        const [vp_x1, vp_y1] = viewport.convertToViewportPoint(s.pdf_x1, pdf_y1_inverted);
        const [vp_x2, vp_y2] = viewport.convertToViewportPoint(s.pdf_x2, pdf_y2_inverted);

        // ===== РЁРђР“ 4: Viewport в†’ СЌРєСЂР°РЅРЅС‹Рµ РєРѕРѕСЂРґРёРЅР°С‚С‹ =====
        const screen_x1 = vp_x1 * scale;
        const screen_y1 = vp_y1 * scale;
        const screen_x2 = vp_x2 * scale;
        const screen_y2 = vp_y2 * scale;

        const left = Math.min(screen_x1, screen_x2);
        const top = Math.min(screen_y1, screen_y2);
        const width = Math.abs(screen_x2 - screen_x1);
        const height = Math.abs(screen_y2 - screen_y1);

        // ===== РЁРђР“ 5: РЎРѕР·РґР°С‘Рј СЌР»РµРјРµРЅС‚ =====
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
    void issn;
    void pageWidth;
    void pageHeight;
    state.templateSuggestions = {};
    return null;
  };

  const saveToTemplate = async (fieldId, coords) => {
    void fieldId;
    void coords;
    return;
  };

  const applySuggestion = async (fieldId) => {
    void fieldId;
    notify("BBox templates are disabled.", "info");
    return null;
  };

  const applyAllSuggestions = async () => {
    notify("BBox templates are disabled.", "info");
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
    notify("BBox templates are disabled.", "info");
  };

  const resetFieldTemplate = async (fieldId) => {
    void fieldId;
    notify("BBox templates are disabled.", "info");
    return false;
  };

  const resetAllTemplates = async () => {
    notify("BBox templates are disabled.", "info");
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



