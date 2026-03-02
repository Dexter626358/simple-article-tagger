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

  const clamp = (v, min, max) => Math.max(min, Math.min(max, v));

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

  const getPageMetrics = (pageView) => {
    const viewport = pageView?.viewport;
    const pdfPage = pageView?.pdfPage;
    const canvas = pageView?.div?.querySelector("canvas");
    if (!viewport || !pdfPage || !canvas) return null;

    const pageRect = pdfPage.view; // [x1, y1, x2, y2]
    const pdfWidth = pageRect[2] - pageRect[0];
    const pdfHeight = pageRect[3] - pageRect[1];
    const scale = canvas.offsetWidth / viewport.width;

    return { viewport, pdfWidth, pdfHeight, scale };
  };

  const pdfSelectionToScreenRect = (pageView, selection) => {
    const metrics = getPageMetrics(pageView);
    if (!metrics || !selection) return null;
    const { viewport, pdfHeight, scale } = metrics;

    const pdfY1Inv = pdfHeight - selection.pdf_y1;
    const pdfY2Inv = pdfHeight - selection.pdf_y2;
    const [vpX1, vpY1] = viewport.convertToViewportPoint(selection.pdf_x1, pdfY1Inv);
    const [vpX2, vpY2] = viewport.convertToViewportPoint(selection.pdf_x2, pdfY2Inv);

    const sx1 = vpX1 * scale;
    const sy1 = vpY1 * scale;
    const sx2 = vpX2 * scale;
    const sy2 = vpY2 * scale;

    return {
      left: Math.min(sx1, sx2),
      top: Math.min(sy1, sy2),
      width: Math.abs(sx2 - sx1),
      height: Math.abs(sy2 - sy1),
    };
  };

  const screenRectToPdfCoords = (pageView, rect) => {
    const metrics = getPageMetrics(pageView);
    if (!metrics || !rect) return null;
    const { viewport, pdfWidth, pdfHeight, scale } = metrics;

    const vpX1 = rect.left / scale;
    const vpY1 = rect.top / scale;
    const vpX2 = (rect.left + rect.width) / scale;
    const vpY2 = (rect.top + rect.height) / scale;

    const [pdfX1, pdfY1] = viewport.convertToPdfPoint(vpX1, vpY1);
    const [pdfX2, pdfY2] = viewport.convertToPdfPoint(vpX2, vpY2);

    return {
      pdf_x1: Math.min(pdfX1, pdfX2),
      pdf_y1: Math.min(pdfHeight - pdfY1, pdfHeight - pdfY2),
      pdf_x2: Math.max(pdfX1, pdfX2),
      pdf_y2: Math.max(pdfHeight - pdfY1, pdfHeight - pdfY2),
      page_width: pdfWidth,
      page_height: pdfHeight,
    };
  };

  const extractAndApplySelectionText = async (selection) => {
    if (!selection) return;
    const extractEndpoint = getConfig("extractEndpoint", "/api/pdf-extract-text");
    const isReferencesField =
      selection.field_id === "references_ru" || selection.field_id === "references_en";

    const options = isReferencesField
      ? {
          fix_hyphenation: true,
          strip_prefix: false,
          join_lines: false,
          merge_by_field: false,
        }
      : {
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
          options,
        }),
      });

      const data = await resp.json();
      const extracted = data?.extracted?.[0]?.text;
      if (!extracted) return;
      const applyFn = getConfig("applyExtractedText", defaultApplyExtractedText);
      applyFn(selection.field_id, extracted);
    } catch (err) {
      console.warn("PDF extract failed:", err);
    }
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
        if (e.target.closest(".bbox-rect")) return;
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

        const normalized = screenRectToPdfCoords(pageViewLocal, { left, top, width, height });
        if (!normalized) return;

        // ===== РЁРђР“ 7: РЎРѕС…СЂР°РЅСЏРµРј =====
        const selection = {
          schema: "pdfbbox-v2",
          id: window.crypto?.randomUUID?.() || 
              Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
          field_id: state.activeFieldId,
          page: Number(overlay.dataset.pageIndex),
          pdf_x1: normalized.pdf_x1,
          pdf_y1: normalized.pdf_y1,
          pdf_x2: normalized.pdf_x2,
          pdf_y2: normalized.pdf_y2,
          page_width: normalized.page_width,
          page_height: normalized.page_height,
          pending_apply: true,
        };

        // Р”РѕР±Р°РІР»СЏРµРј РЅРѕРІС‹Р№ bbox (РЅРµ СѓРґР°Р»СЏРµРј РїСЂРµРґС‹РґСѓС‰РёРµ вЂ” СЂР°Р·СЂРµС€Р°РµРј РјРЅРѕР¶РµСЃС‚РІРµРЅРЅРѕРµ РІС‹РґРµР»РµРЅРёРµ)
        state.selections.push(selection);
        renderBboxes(app);
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

    const metrics = getPageMetrics(pageView);
    if (!metrics) return;

    const getColor = getConfig("getFieldColor", defaultGetFieldColor);
    const getLabel = getConfig("getFieldLabel", defaultGetFieldLabel);

    state.selections
      .filter((s) => s.page === pageIndex)
      .forEach((s) => {
        const sr = pdfSelectionToScreenRect(pageView, s);
        if (!sr) return;
        const left = sr.left;
        const top = sr.top;
        const width = sr.width;
        const height = sr.height;

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

        const applyBtn = ownerDoc.createElement("button");
        applyBtn.type = "button";
        applyBtn.className = "bbox-apply-btn";
        applyBtn.title = "Вставить выделенный фрагмент";
        applyBtn.textContent = "✓";
        applyBtn.style.position = "absolute";
        applyBtn.style.right = "-10px";
        applyBtn.style.bottom = "-10px";
        applyBtn.style.width = "18px";
        applyBtn.style.height = "18px";
        applyBtn.style.border = `1px solid ${color}`;
        applyBtn.style.borderRadius = "50%";
        applyBtn.style.background = "#fff";
        applyBtn.style.color = "#15803d";
        applyBtn.style.fontSize = "12px";
        applyBtn.style.fontWeight = "700";
        applyBtn.style.lineHeight = "16px";
        applyBtn.style.cursor = "pointer";
        applyBtn.style.padding = "0";
        applyBtn.style.zIndex = "10002";
        applyBtn.style.display = s.pending_apply === true ? "block" : "none";
        applyBtn.addEventListener("click", async (ev) => {
          ev.preventDefault();
          ev.stopPropagation();
          const idx = state.selections.findIndex((x) => x.id === s.id);
          if (idx < 0) return;
          await extractAndApplySelectionText(state.selections[idx]);
          state.selections[idx] = { ...state.selections[idx], pending_apply: false };
          renderBboxes(app);
        });
        rect.appendChild(applyBtn);

        rect.addEventListener("click", (e) => {
          e.stopPropagation();
          setActiveField(s.field_id);
          document.getElementById(s.field_id)?.focus();
        });

        const handleDefs = [
          { dir: "nw", x: 0, y: 0, cursor: "nwse-resize" },
          { dir: "n", x: 50, y: 0, cursor: "ns-resize" },
          { dir: "ne", x: 100, y: 0, cursor: "nesw-resize" },
          { dir: "e", x: 100, y: 50, cursor: "ew-resize" },
          { dir: "se", x: 100, y: 100, cursor: "nwse-resize" },
          { dir: "s", x: 50, y: 100, cursor: "ns-resize" },
          { dir: "sw", x: 0, y: 100, cursor: "nesw-resize" },
          { dir: "w", x: 0, y: 50, cursor: "ew-resize" },
        ];

        handleDefs.forEach((h) => {
          const handle = ownerDoc.createElement("div");
          handle.className = `bbox-handle bbox-handle-${h.dir}`;
          handle.style.position = "absolute";
          handle.style.width = "8px";
          handle.style.height = "8px";
          handle.style.background = "#fff";
          handle.style.border = `1px solid ${color}`;
          handle.style.borderRadius = "2px";
          handle.style.left = `${h.x}%`;
          handle.style.top = `${h.y}%`;
          handle.style.transform = "translate(-50%, -50%)";
          handle.style.cursor = h.cursor;
          handle.style.zIndex = "10001";
          handle.style.pointerEvents = "auto";

          handle.addEventListener("mousedown", (ev) => {
            ev.preventDefault();
            ev.stopPropagation();

            const startMouseX = ev.clientX;
            const startMouseY = ev.clientY;
            const startRect = { left, top, width, height };
            const minSize = 6;
            const overlayWidth = overlay.clientWidth;
            const overlayHeight = overlay.clientHeight;

            const onMove = (mv) => {
              const dx = mv.clientX - startMouseX;
              const dy = mv.clientY - startMouseY;

              let nl = startRect.left;
              let nt = startRect.top;
              let nw = startRect.width;
              let nh = startRect.height;

              if (h.dir.includes("e")) nw = startRect.width + dx;
              if (h.dir.includes("s")) nh = startRect.height + dy;
              if (h.dir.includes("w")) {
                nl = startRect.left + dx;
                nw = startRect.width - dx;
              }
              if (h.dir.includes("n")) {
                nt = startRect.top + dy;
                nh = startRect.height - dy;
              }

              if (nw < minSize) {
                if (h.dir.includes("w")) nl -= minSize - nw;
                nw = minSize;
              }
              if (nh < minSize) {
                if (h.dir.includes("n")) nt -= minSize - nh;
                nh = minSize;
              }

              nl = clamp(nl, 0, overlayWidth - minSize);
              nt = clamp(nt, 0, overlayHeight - minSize);
              nw = clamp(nw, minSize, overlayWidth - nl);
              nh = clamp(nh, minSize, overlayHeight - nt);

              rect.style.left = `${nl}px`;
              rect.style.top = `${nt}px`;
              rect.style.width = `${nw}px`;
              rect.style.height = `${nh}px`;
            };

            const onUp = async () => {
              ownerDoc.removeEventListener("mousemove", onMove);
              ownerDoc.removeEventListener("mouseup", onUp);

              const finalRect = {
                left: parseFloat(rect.style.left || "0"),
                top: parseFloat(rect.style.top || "0"),
                width: parseFloat(rect.style.width || "0"),
                height: parseFloat(rect.style.height || "0"),
              };

              const next = screenRectToPdfCoords(pageView, finalRect);
              if (!next) return;

              const idx = state.selections.findIndex((x) => x.id === s.id);
              if (idx < 0) return;
              state.selections[idx] = {
                ...state.selections[idx],
                ...next,
                pending_apply: true,
              };

              renderBboxes(app);
            };

            ownerDoc.addEventListener("mousemove", onMove);
            ownerDoc.addEventListener("mouseup", onUp);
          });

          rect.appendChild(handle);
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



