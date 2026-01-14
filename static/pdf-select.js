  let pdfDoc = null;
  let pdfData = null;
  let currentPage = 0;
  let scaleFactor = 1.5;
  let selections = [];
  let currentPageView = null;
  let isDragging = false;
  let dragStart = null;
  let dragRect = null;

  const FIELD_DEFS = [
    { id: 'title', label: '\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 (\u0440\u0443\u0441)' },
    { id: 'title_en', label: '\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 (\u0430\u043d\u0433\u043b)' },
    { id: 'doi', label: 'DOI' },
    { id: 'udc', label: '\u0423\u0414\u041a' },
    { id: 'bbk', label: '\u0411\u0411\u041a' },
    { id: 'edn', label: 'EDN' },
    { id: 'annotation', label: '\u0410\u043d\u043d\u043e\u0442\u0430\u0446\u0438\u044f (\u0440\u0443\u0441)' },
    { id: 'annotation_en', label: '\u0410\u043d\u043d\u043e\u0442\u0430\u0446\u0438\u044f (\u0430\u043d\u0433\u043b)' },
    { id: 'keywords', label: '\u041a\u043b\u044e\u0447\u0435\u0432\u044b\u0435 \u0441\u043b\u043e\u0432\u0430 (\u0440\u0443\u0441)' },
    { id: 'keywords_en', label: '\u041a\u043b\u044e\u0447\u0435\u0432\u044b\u0435 \u0441\u043b\u043e\u0432\u0430 (\u0430\u043d\u0433\u043b)' },
    { id: 'references_ru', label: '\u0421\u043f\u0438\u0441\u043e\u043a \u043b\u0438\u0442\u0435\u0440\u0430\u0442\u0443\u0440\u044b (\u0440\u0443\u0441)' },
    { id: 'references_en', label: '\u0421\u043f\u0438\u0441\u043e\u043a \u043b\u0438\u0442\u0435\u0440\u0430\u0442\u0443\u0440\u044b (\u0430\u043d\u0433\u043b)' },
    { id: 'pages', label: '\u0421\u0442\u0440\u0430\u043d\u0438\u0446\u044b' },
    { id: 'received_date', label: '\u0414\u0430\u0442\u0430 \u043f\u043e\u043b\u0443\u0447\u0435\u043d\u0438\u044f' },
    { id: 'reviewed_date', label: '\u0414\u0430\u0442\u0430 \u0434\u043e\u0440\u0430\u0431\u043e\u0442\u043a\u0438' },
    { id: 'accepted_date', label: '\u0414\u0430\u0442\u0430 \u043f\u0440\u0438\u043d\u044f\u0442\u0438\u044f' },
    { id: 'date_publication', label: '\u0414\u0430\u0442\u0430 \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0438' },
    { id: 'funding', label: '\u0424\u0438\u043d\u0430\u043d\u0441\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435 (\u0440\u0443\u0441)' },
    { id: 'funding_en', label: '\u0424\u0438\u043d\u0430\u043d\u0441\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435 (\u0430\u043d\u0433\u043b)' },
    { id: 'author_surname_rus', label: '\u0410\u0432\u0442\u043e\u0440: \u0424\u0430\u043c\u0438\u043b\u0438\u044f (\u0440\u0443\u0441)' },
    { id: 'author_surname_eng', label: '\u0410\u0432\u0442\u043e\u0440: \u0424\u0430\u043c\u0438\u043b\u0438\u044f (\u0430\u043d\u0433\u043b)' },
    { id: 'author_initials_rus', label: '\u0410\u0432\u0442\u043e\u0440: \u0418\u043d\u0438\u0446\u0438\u0430\u043b\u044b (\u0440\u0443\u0441)' },
    { id: 'author_initials_eng', label: '\u0410\u0432\u0442\u043e\u0440: \u0418\u043d\u0438\u0446\u0438\u0430\u043b\u044b (\u0430\u043d\u0433\u043b)' },
    { id: 'author_org_rus', label: '\u0410\u0432\u0442\u043e\u0440: \u041e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u044f (\u0440\u0443\u0441)' },
    { id: 'author_org_eng', label: '\u0410\u0432\u0442\u043e\u0440: \u041e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u044f (\u0430\u043d\u0433\u043b)' },
    { id: 'author_address_rus', label: '\u0410\u0432\u0442\u043e\u0440: \u0410\u0434\u0440\u0435\u0441 (\u0440\u0443\u0441)' },
    { id: 'author_address_eng', label: '\u0410\u0432\u0442\u043e\u0440: \u0410\u0434\u0440\u0435\u0441 (\u0430\u043d\u0433\u043b)' },
    { id: 'author_email', label: '\u0410\u0432\u0442\u043e\u0440: Email' },
    { id: 'author_other_rus', label: '\u0410\u0432\u0442\u043e\u0440: \u0414\u043e\u043f. \u0438\u043d\u0444\u043e (\u0440\u0443\u0441)' },
    { id: 'author_other_eng', label: '\u0410\u0432\u0442\u043e\u0440: \u0414\u043e\u043f. \u0438\u043d\u0444\u043e (\u0430\u043d\u0433\u043b)' },
    { id: 'author_spin', label: '\u0410\u0432\u0442\u043e\u0440: SPIN' },
    { id: 'author_orcid', label: '\u0410\u0432\u0442\u043e\u0440: ORCID' },
    { id: 'author_scopusid', label: '\u0410\u0432\u0442\u043e\u0440: Scopus ID' },
    { id: 'author_researcherid', label: '\u0410\u0432\u0442\u043e\u0440: Researcher ID' },
  ];
  let activeFieldId = null;

  function getEl(id) {
    return document.getElementById(id);
  }

  function getFieldLabel(fieldId) {
    const field = FIELD_DEFS.find((item) => item.id === fieldId);
    return field ? field.label : fieldId;
  }

  function setActiveField(fieldId) {
    activeFieldId = fieldId;
    const buttons = getEl('fieldButtons');
    if (buttons) {
      buttons.querySelectorAll('.field-btn').forEach((btn) => {
        const isActive = btn.dataset.fieldId === fieldId;
        btn.classList.toggle('active', isActive);
      });
    }
  }

  function appendToField(fieldId, text) {
    if (!fieldId) return;
    const textarea = getEl(`field-${fieldId}`);
    if (!textarea) return;
    const cleaned = (text || '').trim();
    if (!cleaned) return;
    if (textarea.value) {
      textarea.value += '\n' + cleaned;
    } else {
      textarea.value = cleaned;
    }
  }

  function clearFieldBlocks() {
    const blocks = getEl('fieldBlocks');
    if (!blocks) return;
    blocks.querySelectorAll('textarea').forEach((area) => {
      area.value = '';
    });
  }

  function filterFieldBlocks(query) {
    const term = (query || '').trim().toLowerCase();
    const buttons = getEl('fieldButtons');
    const blocks = getEl('fieldBlocks');
    if (!buttons || !blocks) return;

    buttons.querySelectorAll('.field-btn').forEach((btn) => {
      const label = (btn.textContent || '').toLowerCase();
      const id = (btn.dataset.fieldId || '').toLowerCase();
      const show = !term || label.includes(term) || id.includes(term);
      btn.style.display = show ? 'inline-flex' : 'none';
    });

    blocks.querySelectorAll('.field-block').forEach((block) => {
      const label = (block.querySelector('label')?.textContent || '').toLowerCase();
      const id = (block.dataset.fieldId || '').toLowerCase();
      const show = !term || label.includes(term) || id.includes(term);
      block.style.display = show ? 'flex' : 'none';
    });
  }

  function initFieldSearch() {
    const input = getEl('fieldSearch');
    if (!input) return;
    input.addEventListener('input', () => {
      filterFieldBlocks(input.value);
    });
  }

  function renderFieldBlocks() {
    const buttons = getEl('fieldButtons');
    const blocks = getEl('fieldBlocks');
    if (!buttons || !blocks) return;

    buttons.innerHTML = '';
    blocks.innerHTML = '';

    FIELD_DEFS.forEach((field) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'field-btn';
      btn.dataset.fieldId = field.id;
      btn.textContent = field.label;
      btn.addEventListener('click', () => setActiveField(field.id));
      buttons.appendChild(btn);

      const block = document.createElement('div');
      block.className = 'field-block';
      block.dataset.fieldId = field.id;

      const label = document.createElement('label');
      label.textContent = field.label;

      const textarea = document.createElement('textarea');
      textarea.id = `field-${field.id}`;
      textarea.addEventListener('focus', () => setActiveField(field.id));

      block.appendChild(label);
      block.appendChild(textarea);
      blocks.appendChild(block);
    });

    if (FIELD_DEFS.length) {
      setActiveField(FIELD_DEFS[0].id);
    }
  }

  function setStatus(message) {
    const el = getEl('statusBar');
    if (el) {
      el.textContent = message;
    }
  }

  function showError(message) {
    const el = getEl('error');
    if (el) {
      el.textContent = message;
      el.style.display = 'block';
    }
  }

  function clearError() {
    const el = getEl('error');
    if (el) {
      el.textContent = '';
      el.style.display = 'none';
    }
  }

  function showLoading(isVisible) {
    const el = getEl('loading');
    if (el) {
      el.style.display = isVisible ? 'block' : 'none';
    }
  }

  function showMainContent(isVisible) {
    const el = getEl('mainContent');
    if (el) {
      el.style.display = isVisible ? 'flex' : 'none';
    }
  }

  function updatePageLabel() {
    const el = getEl('pageLabel');
    if (el && pdfDoc) {
      el.textContent = `\u0421\u0442\u0440\u0430\u043d\u0438\u0446\u0430: ${currentPage + 1}/${pdfDoc.numPages}`;
    }
  }

  function clampValue(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function getCanvasCoords(event, canvas) {
    const rect = canvas.getBoundingClientRect();
    const x = clampValue(event.clientX - rect.left, 0, canvas.width);
    const y = clampValue(event.clientY - rect.top, 0, canvas.height);
    return { x, y };
  }

  function updateSelectionsList() {
    const list = getEl('selectionsList');
    if (!list) return;
    list.innerHTML = '';

    if (!selections.length) {
      setStatus('\u041d\u0435\u0442 \u0432\u044b\u0434\u0435\u043b\u0435\u043d\u043d\u044b\u0445 \u043e\u0431\u043b\u0430\u0441\u0442\u0435\u0439');
      return;
    }

    selections.forEach((sel, idx) => {
      const item = document.createElement('div');
      item.className = 'selection-item';
      item.textContent = `#${idx + 1} | \u0441\u0442\u0440. ${sel.page + 1} | ${getFieldLabel(sel.field_id || activeFieldId)} | ${Math.round(sel.screen_x1)}:${Math.round(sel.screen_y1)} - ${Math.round(sel.screen_x2)}:${Math.round(sel.screen_y2)}`;
      item.addEventListener('click', async () => {
        if (!pdfDoc) return;
        currentPage = sel.page;
        await renderPage();
      });
      list.appendChild(item);
    });

    setStatus(`\u0412\u044b\u0434\u0435\u043b\u0435\u043d\u043e \u043e\u0431\u043b\u0430\u0441\u0442\u0435\u0439: ${selections.length}`);
  }

  function renderSelectionsForPage() {
    if (!currentPageView) return;
    const pageDiv = currentPageView.pageDiv;
    if (!pageDiv) return;

    pageDiv.querySelectorAll('.selection-overlay').forEach(node => node.remove());

    selections
      .filter(sel => sel.page === currentPage)
      .forEach(sel => {
        const overlay = document.createElement('div');
        overlay.className = 'selection-overlay';
        overlay.style.left = `${Math.min(sel.screen_x1, sel.screen_x2)}px`;
        overlay.style.top = `${Math.min(sel.screen_y1, sel.screen_y2)}px`;
        overlay.style.width = `${Math.abs(sel.screen_x2 - sel.screen_x1)}px`;
        overlay.style.height = `${Math.abs(sel.screen_y2 - sel.screen_y1)}px`;
        pageDiv.appendChild(overlay);
      });
  }

  async function loadPdfFiles() {
    const select = getEl('pdfFile');
    if (!select) return;
    try {
      const response = await fetch('/api/pdf-files');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const files = await response.json();
      select.innerHTML = '';

      if (!Array.isArray(files) || files.length === 0) {
        const option = document.createElement('option');
        option.value = '';
        option.textContent = '-- \u0050\u0044\u0046 \u0444\u0430\u0439\u043b\u044b \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u044b --';
        option.disabled = true;
        select.appendChild(option);
        return;
      }

      const option = document.createElement('option');
      option.value = '';
      option.textContent = '-- \u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0050\u0044\u0046 \u0444\u0430\u0439\u043b --';
      select.appendChild(option);

      files.forEach(file => {
        const opt = document.createElement('option');
        opt.value = file;
        opt.textContent = file;
        select.appendChild(opt);
      });
    } catch (error) {
      showError(`\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u0437\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u0441\u043f\u0438\u0441\u043e\u043a \u0050\u0044\u0046: ${error.message}`);
    }
  }

  async function openPdf(filename) {
    if (typeof pdfjsLib === 'undefined') {
      throw new Error('PDF.js \u043d\u0435 \u0437\u0430\u0433\u0440\u0443\u0436\u0435\u043d');
    }

    pdfjsLib.GlobalWorkerOptions.workerSrc = '/static/pdf.worker.min.js';
    const pdfUrl = `/pdf/${encodeURIComponent(filename)}`;
    const loadingTask = pdfjsLib.getDocument({ url: pdfUrl, verbosity: 0 });
    pdfDoc = await loadingTask.promise;
    pdfData = {
      pdf_file: filename,
      total_pages: pdfDoc.numPages,
      pages: []
    };
  }

  async function renderPage() {
    if (!pdfDoc) return;

    const viewer = getEl('pdfViewer');
    if (!viewer) return;

    viewer.innerHTML = '';

    const page = await pdfDoc.getPage(currentPage + 1);
    const viewport = page.getViewport({ scale: scaleFactor });

    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.width = viewport.width;
    canvas.height = viewport.height;
    canvas.style.display = 'block';

    const pageDiv = document.createElement('div');
    pageDiv.className = 'pdf-page';
    pageDiv.style.width = `${viewport.width}px`;
    pageDiv.style.height = `${viewport.height}px`;
    pageDiv.style.position = 'relative';
    pageDiv.style.margin = '10px auto';
    pageDiv.appendChild(canvas);
    viewer.appendChild(pageDiv);

    currentPageView = { page, viewport, canvas, pageDiv };

    await page.render({ canvasContext: context, viewport }).promise;
    updatePageLabel();
    renderSelectionsForPage();
  }

  async function loadPdf() {
    const select = getEl('pdfFile');
    const filename = select ? select.value.trim() : '';
    if (!filename) {
      showError('\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0050\u0044\u0046 \u0444\u0430\u0439\u043b');
      return;
    }

    clearError();
    showLoading(true);
    showMainContent(false);

    try {
      selections = [];
      currentPage = 0;
      clearFieldBlocks();
      await openPdf(filename);
      await renderPage();
      updateSelectionsList();
      showMainContent(true);
      setStatus(`\u0050\u0044\u0046 \u0437\u0430\u0433\u0440\u0443\u0436\u0435\u043d, \u0441\u0442\u0440\u0430\u043d\u0438\u0446: ${pdfDoc.numPages}`);
    } catch (error) {
      showError(`\u041e\u0448\u0438\u0431\u043a\u0430 \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438 \u0050\u0044\u0046: ${error.message}`);
    } finally {
      showLoading(false);
    }
  }

  async function prevPage() {
    if (!pdfDoc || currentPage <= 0) return;
    currentPage -= 1;
    await renderPage();
  }

  async function nextPage() {
    if (!pdfDoc || currentPage >= pdfDoc.numPages - 1) return;
    currentPage += 1;
    await renderPage();
  }

  async function extractText() {
    if (!pdfDoc || !pdfData) {
      showError('\u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u0437\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u0435 \u0050\u0044\u0046');
      return;
    }
    if (!selections.length) {
      showError('\u041d\u0435\u0442 \u0432\u044b\u0434\u0435\u043b\u0435\u043d\u043d\u044b\u0445 \u043e\u0431\u043b\u0430\u0441\u0442\u0435\u0439');
      return;
    }

    clearError();
    try {
      const response = await fetch('/api/pdf-extract-text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pdf_file: pdfData.pdf_file,
          selections: selections
        })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || '\u041e\u0448\u0438\u0431\u043a\u0430 \u0438\u0437\u0432\u043b\u0435\u0447\u0435\u043d\u0438\u044f \u0442\u0435\u043a\u0441\u0442\u0430');
      }

      const extracted = Array.isArray(data.extracted) ? data.extracted : [];

      extracted.forEach((item, idx) => {
        const selection = selections[idx];
        if (!selection) return;
        selection.text = item && item.text ? item.text : '';
        const fieldId = selection.field_id || activeFieldId;
        if (fieldId) {
          appendToField(fieldId, selection.text);
        }
      });

      updateSelectionsList();
    } catch (error) {
      showError(`\u041e\u0448\u0438\u0431\u043a\u0430 \u0438\u0437\u0432\u043b\u0435\u0447\u0435\u043d\u0438\u044f \u0442\u0435\u043a\u0441\u0442\u0430: ${error.message}`);
    }
  }

  async function saveCoordinates() {
    if (!pdfDoc || !pdfData) {
      showError('\u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u0437\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u0435 \u0050\u0044\u0046');
      return;
    }
    if (!selections.length) {
      showError('\u041d\u0435\u0442 \u0432\u044b\u0434\u0435\u043b\u0435\u043d\u043d\u044b\u0445 \u043e\u0431\u043b\u0430\u0441\u0442\u0435\u0439');
      return;
    }

    clearError();
    try {
      const response = await fetch('/api/pdf-save-coordinates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pdf_file: pdfData.pdf_file,
          total_pages: pdfData.total_pages,
          selections: selections
        })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || '\u041e\u0448\u0438\u0431\u043a\u0430 \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u044f \u043a\u043e\u043e\u0440\u0434\u0438\u043d\u0430\u0442');
      }

      setStatus(`\u041a\u043e\u043e\u0440\u0434\u0438\u043d\u0430\u0442\u044b \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u044b: ${data.file_name || ''}`);
    } catch (error) {
      showError(`\u041e\u0448\u0438\u0431\u043a\u0430 \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u044f \u043a\u043e\u043e\u0440\u0434\u0438\u043d\u0430\u0442: ${error.message}`);
    }
  }

  function clearSelections() {
    selections = [];
    if (dragRect) {
      dragRect.remove();
      dragRect = null;
    }
    updateSelectionsList();
    renderSelectionsForPage();
  }
  function initSelectionHandlers() {
    const container = getEl('pdfViewerContainer');
    if (!container) return;

    container.addEventListener('mousedown', (event) => {
      if (!currentPageView) return;
      const canvas = currentPageView.canvas;
      if (!canvas || !event.target.closest('.pdf-page')) return;
      const coords = getCanvasCoords(event, canvas);
      dragStart = coords;
      isDragging = true;

      if (dragRect) {
        dragRect.remove();
        dragRect = null;
      }

      dragRect = document.createElement('div');
      dragRect.className = 'selection-overlay';
      dragRect.style.left = `${coords.x}px`;
      dragRect.style.top = `${coords.y}px`;
      dragRect.style.width = '0px';
      dragRect.style.height = '0px';
      currentPageView.pageDiv.appendChild(dragRect);
    });

    container.addEventListener('mousemove', (event) => {
      if (!isDragging || !dragStart || !currentPageView || !dragRect) return;
      const canvas = currentPageView.canvas;
      if (!canvas) return;
      const coords = getCanvasCoords(event, canvas);
      const x1 = Math.min(dragStart.x, coords.x);
      const y1 = Math.min(dragStart.y, coords.y);
      const x2 = Math.max(dragStart.x, coords.x);
      const y2 = Math.max(dragStart.y, coords.y);
      dragRect.style.left = `${x1}px`;
      dragRect.style.top = `${y1}px`;
      dragRect.style.width = `${x2 - x1}px`;
      dragRect.style.height = `${y2 - y1}px`;
    });

    container.addEventListener('mouseup', (event) => {
      if (!isDragging || !dragStart || !currentPageView) return;
      const canvas = currentPageView.canvas;
      if (!canvas) return;

      const coords = getCanvasCoords(event, canvas);
      const x1 = Math.min(dragStart.x, coords.x);
      const y1 = Math.min(dragStart.y, coords.y);
      const x2 = Math.max(dragStart.x, coords.x);
      const y2 = Math.max(dragStart.y, coords.y);

      isDragging = false;
      dragStart = null;

      if (dragRect) {
        dragRect.remove();
        dragRect = null;
      }

      if (Math.abs(x2 - x1) < 8 || Math.abs(y2 - y1) < 8) {
        return;
      }

      const page = currentPageView.page;
      const viewport = currentPageView.viewport;
      const pageSize = page.view;

      const pdf_x1 = (x1 / viewport.width) * pageSize[2];
      const pdf_x2 = (x2 / viewport.width) * pageSize[2];
      const pdf_y1 = pageSize[3] - (y2 / viewport.height) * pageSize[3];
      const pdf_y2 = pageSize[3] - (y1 / viewport.height) * pageSize[3];

      if (!activeFieldId) {
      showError('\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0431\u043b\u043e\u043a \u0434\u043b\u044f \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u044f \u0442\u0435\u043a\u0441\u0442\u0430');
        return;
      }

      selections.push({
        page: currentPage,
        screen_x1: x1,
        screen_y1: y1,
        screen_x2: x2,
        screen_y2: y2,
        pdf_x1: Math.min(pdf_x1, pdf_x2),
        pdf_y1: pdf_y1,
        pdf_x2: Math.max(pdf_x1, pdf_x2),
        pdf_y2: pdf_y2,
        field_id: activeFieldId,
        text: ''
      });

      updateSelectionsList();
      renderSelectionsForPage();
    });
  }

  function initReloadButton() {
    const btn = getEl('btnReloadPdfFiles');
    if (!btn) return;
    btn.addEventListener('click', () => {
      loadPdfFiles();
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    initReloadButton();
    initSelectionHandlers();
    renderFieldBlocks();
    initFieldSearch();
  });

  window.loadPdfFiles = loadPdfFiles;
  window.loadPdf = loadPdf;
  window.prevPage = prevPage;
  window.nextPage = nextPage;
  window.extractText = extractText;
  window.saveCoordinates = saveCoordinates;
  window.clearSelections = clearSelections;
