# Auto-generated from app.py templates

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Работа с метаданными статей</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body {
      height: auto;
      min-height: 100vh;
    }
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: #1e2029;
      padding: 24px;
      margin: 0;
      color: #e6e8ee;
    }
    .container {
      max-width: 1200px;
      margin: 0 auto;
      background: transparent;
      border-radius: 16px;
      box-shadow: none;
      min-height: auto;
      height: auto;
      padding-bottom: 20px;
    }
    .header {
      background: #2a2d3a;
      color: #e6e8ee;
      padding: 24px;
      text-align: center;
      border-radius: 16px;
      box-shadow: 0 10px 26px rgba(0, 0, 0, 0.35);
      border: 1px solid #3a3f52;
    }
    .header h1 {
      font-size: 26px;
      margin-bottom: 6px;
    }
    .header p {
      opacity: 0.85;
      font-size: 14px;
      color: #a7aec2;
    }
    .header-actions {
      margin-top: 16px;
      display: flex;
      gap: 12px;
      justify-content: center;
      flex-wrap: wrap;
      align-items: center;
    }
    .checkbox-inline {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
      color: #d4d8e6;
      background: #323545;
      border-radius: 999px;
      padding: 8px 12px;
      border: 1px solid #3a3f52;
    }
    .checkbox-inline small {
      color: #9aa2b6;
    }
    .step-bar {
      margin-top: 16px;
      display: flex;
      gap: 10px;
      justify-content: center;
      align-items: stretch;
      flex-wrap: wrap;
    }
    .step {
      flex: 1 1 160px;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 10px 14px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 600;
      color: #b7bfd1;
      border: 1px solid #3a3f52;
      background: #2f3342;
    }
    .step.active {
      background: #6c63ff;
      border-color: #6c63ff;
      color: #fff;
    }
    .step.done {
      background: #243832;
      border-color: #2f5a46;
      color: #6dd08a;
    }
    .upload-help ul {
      margin: 0;
      padding-left: 18px;
    }
    .upload-help li {
      margin: 4px 0;
    }
    .status-chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 8px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 600;
      color: #e6e8ee;
      background: #303346;
      border: 1px solid #3a3f52;
    }
    .content {
      padding: 20px 0 0 0;
      min-height: auto;
      height: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .card {
      background: #2a2d3a;
      border: 1px solid #3a3f52;
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 10px 26px rgba(0, 0, 0, 0.28);
    }
    .upload-panel {
      margin: 0;
    }
    .upload-title {
      font-weight: 700;
      font-size: 16px;
      color: #e6e8ee;
      margin-bottom: 4px;
    }
    .upload-subtitle {
      font-size: 13px;
      color: #a7aec2;
      margin-bottom: 12px;
    }
    .upload-form {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
    }
    .upload-form input[type="file"] {
      flex: 1 1 260px;
      padding: 6px;
      font-size: 12px;
      border: 1px solid #3a3f52;
      border-radius: 4px;
      background: #232633;
      color: #e6e8ee;
    }
    .upload-status {
      font-size: 12px;
      color: #a7aec2;
      min-height: 18px;
    }
    .progress-bar {
      position: relative;
      width: 260px;
      height: 10px;
      background: #2b2f3d;
      border-radius: 6px;
      overflow: hidden;
    }
    .progress-bar-fill {
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, #6c63ff, #7f75ff);
      transition: width 0.3s ease;
    }
    .details-card {
      margin-top: 10px;
      background: #2f3342;
      border: 1px solid #3a3f52;
      border-radius: 10px;
      padding: 10px 12px;
      font-size: 12px;
      color: #c6cbe0;
    }
    .details-card summary {
      cursor: pointer;
      font-weight: 600;
      color: #cfd4e6;
    }
    .details-card ul {
      margin: 8px 0 0 18px;
    }
    .file-list {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
      gap: 8px;
      margin-top: 0;
    }
    .file-item {
      background: #f8f9fa;
      border: 1px solid #e0e0e0;
      border-radius: 4px;
      padding: 8px;
      cursor: pointer;
      transition: all 0.2s;
      text-decoration: none;
      color: #333;
      display: block;
    }
    .file-item.active {
      border-color: #2196f3;
      background: #e3f2fd;
      box-shadow: 0 2px 8px rgba(33, 150, 243, 0.3);
    }
    .file-item:hover {
      background: #e3f2fd;
      border-color: #2196f3;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(33, 150, 243, 0.2);
    }
    .file-item:active {
      transform: translateY(0);
    }
    .file-item.processed {
      border-color: #4caf50;
      background: #f1f8f4;
    }
    .file-item.processed:hover {
      border-color: #45a049;
      background: #e8f5e9;
    }
    .file-name {
      font-weight: 600;
      font-size: 11px;
      margin-bottom: 4px;
      color: #2196f3;
      display: flex;
      align-items: center;
      gap: 4px;
      line-height: 1.3;
    }
    .file-name.processed {
      color: #2e7d32;
    }
    .status-icon {
      font-size: 12px;
      line-height: 1;
      flex-shrink: 0;
    }
    .status-icon.processed {
      color: #4caf50;
    }
    .file-info {
      font-size: 9px;
      color: #666;
      line-height: 1.3;
    }
    .form-field-group {
      margin-bottom: 20px;
    }
    .form-field-group label {
      display: block;
      font-weight: 600;
      margin-bottom: 8px;
      color: #cfd4e6;
      font-size: 13px;
    }
    .form-field-group input,
    .form-field-group textarea,
    .form-field-group select {
      width: 100%;
      padding: 10px;
      border: 1px solid #3a3f52;
      border-radius: 4px;
      font-size: 14px;
      font-family: inherit;
      transition: border-color 0.2s;
      background: #232633;
      color: #e6e8ee;
    }
    .form-field-group input:focus,
    .form-field-group textarea:focus,
    .form-field-group select:focus {
      outline: none;
      border-color: #6c63ff;
      box-shadow: 0 0 0 3px rgba(108, 99, 255, 0.2);
    }
    .form-field-group textarea {
      min-height: 60px;
      resize: vertical;
    }
    .form-instructions {
      background: #2f3342;
      border: 1px solid #3a3f52;
      border-radius: 8px;
      padding: 12px;
      margin-bottom: 20px;
      font-size: 12px;
      color: #c6cbe0;
    }
    .form-instructions h3 {
      margin: 0 0 8px 0;
      color: #e6e8ee;
      font-size: 14px;
    }
    .form-instructions ul {
      margin: 0;
      padding-left: 20px;
      color: #c6cbe0;
    }
    .form-instructions li {
      margin: 4px 0;
    }
    .article-start-marker {
      background: #fff9c4 !important;
      border-left: 4px solid #ff9800 !important;
      font-weight: 600 !important;
      position: relative;
    }
    .article-start-marker::before {
      content: "📍 Начало статьи";
      position: absolute;
      top: -20px;
      left: 0;
      background: #ff9800;
      color: white;
      padding: 2px 8px;
      border-radius: 3px;
      font-size: 11px;
      font-weight: 600;
    }
    /* Стили для формы из MARKUP_TEMPLATE */
    .instructions{background:#2f3342;border:1px solid #3a3f52;border-radius:8px;padding:15px;margin-bottom:20px;color:#c6cbe0;}
    .instructions h3{margin-bottom:10px;color:#e6e8ee;font-size:14px;}
    .instructions ul{margin-left:20px;color:#c6cbe0;}
    .instructions li{margin:5px 0;}
    .field-group{margin-bottom:20px;}
    .field-group label{display:block;font-weight:600;margin-bottom:8px;color:#cfd4e6;font-size:14px;}
    .field-group input,.field-group textarea,.field-group select{width:100%;padding:10px;border:1px solid #3a3f52;border-radius:4px;font-size:14px;font-family:inherit;background:#232633;color:#e6e8ee;}
    .field-group textarea{min-height:80px;resize:vertical;}
    .selected-lines{margin-top:5px;font-size:12px;color:#666;}
    .keywords-count{margin-top:5px;font-size:12px;color:#666;font-style:italic;}
    .keywords-textarea{min-height:72px;resize:none;overflow:hidden;line-height:1.4;}
    .field-group.active{background:#e3f2fd;border:2px solid #2196f3;border-radius:4px;padding:10px;}
    .buttons{display:flex;gap:10px;margin-top:20px;}
    .btn-secondary{background:#e0e0e0;color:#333;}
    .btn-secondary:hover{background:#d0d0d0;}
    .btn-success{background:#4caf50;color:#fff;}
    .btn-success:hover{background:#45a049;}
    .selection-panel{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#fff;border:2px solid #667eea;border-radius:8px;padding:15px 20px;box-shadow:0 4px 20px rgba(0,0,0,0.2);z-index:1000;display:none;min-width:400px;max-width:calc(100vw - 24px);cursor:grab;}
    .selection-panel.active{display:block;}
    .selection-panel h4{margin:0 0 10px 0;color:#667eea;font-size:14px;}
    .selection-panel.dragging{cursor:grabbing;user-select:none;}
    .field-buttons{display:flex;flex-wrap:wrap;gap:8px;}
    .field-btn{padding:8px 12px;border:1px solid #667eea;background:#fff;color:#667eea;border-radius:4px;cursor:pointer;font-size:12px;transition:all .2s;}
    .field-btn:hover{background:#667eea;color:#fff;}
    .view-refs-btn{background:#2196f3;color:#fff;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;font-size:12px;margin-top:5px;transition:all .2s;}
    .view-refs-btn:hover{background:#1976d2;}
    .author-item{margin-bottom:10px;border:1px solid #ddd;border-radius:4px;overflow:hidden;}
    .author-header{display:flex;justify-content:space-between;align-items:center;padding:12px 15px;background:#f8f9fa;cursor:pointer;transition:background .2s;}
    .author-header:hover{background:#e9ecef;}
    .author-name{font-weight:600;color:#333;font-size:14px;}
    .author-toggle{color:#666;font-size:12px;transition:transform .2s;}
    .author-item.expanded .author-toggle{transform:rotate(180deg);}
    .author-actions{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;gap:10px;}
    .author-field textarea.author-textarea{min-height:54px;resize:vertical;}
    .author-collapse-actions{display:flex;justify-content:flex-end;margin-top:12px;}
    .author-collapse-btn{background:#e0e0e0;color:#333;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;font-size:12px;transition:all .2s;}
    .author-collapse-btn:hover{background:#d0d0d0;}
    .author-actions label{margin:0;flex:1;}
    .add-author-btn{background:#667eea;color:#fff;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;font-size:12px;transition:all .2s;display:inline-flex;align-items:center;gap:4px;white-space:nowrap;}
    .add-author-btn:hover{background:#5568d3;}
    .delete-author-btn{background:#d32f2f;color:#fff;border:none;padding:4px 8px;border-radius:3px;cursor:pointer;font-size:11px;transition:all .2s;min-width:24px;height:24px;display:inline-flex;align-items:center;justify-content:center;}
    .delete-author-btn:hover{background:#b71c1c;}
    .author-details{padding:15px;background:#fff;border-top:1px solid #e0e0e0;}
    .author-section{margin-bottom:20px;}
    .author-section:last-child{margin-bottom:0;}
    .author-section h4{margin:0 0 12px 0;color:#667eea;font-size:14px;font-weight:600;border-bottom:1px solid #e0e0e0;padding-bottom:5px;}
    .author-field{margin-bottom:10px;}
    .author-field label{display:block;font-size:12px;color:#666;margin-bottom:4px;font-weight:500;}
    .author-field input,.author-field textarea{width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;font-size:13px;font-family:inherit;}
    .author-field input:focus,.author-field textarea:focus{outline:2px solid #667eea;outline-offset:2px;border-color:#667eea;}
    .correspondence-toggle{margin-top:5px;}
    .toggle-label{display:flex;align-items:center;gap:8px;cursor:pointer;}
    .toggle-label input[type="checkbox"]{width:18px;height:18px;cursor:pointer;}
    .toggle-text{font-size:14px;color:#333;}
    .modal{display:none;position:fixed;z-index:2000;left:0;top:0;width:100%;height:100%;background:transparent;overflow:auto;pointer-events:none;}
    .modal.active{display:flex;align-items:center;justify-content:center;}
    .modal-content{background:#fff;padding:30px;border-radius:8px;max-width:800px;width:90%;max-height:80vh;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.3);pointer-events:auto;display:flex;flex-direction:column;position:relative;}
    .modal-content.resizable{resize:both;overflow:auto;min-width:360px;min-height:240px;width:90vw;height:70vh;max-width:95vw;max-height:90vh;}
    .modal-content.resizable{resize:both;overflow:auto;min-width:360px;min-height:240px;width:90vw;height:70vh;max-width:95vw;max-height:90vh;}
    .refs-modal-content{overflow-y:auto;}
    .refs-modal-content,
    .refs-modal-content .ref-text,
    .refs-modal-content .ref-text[contenteditable="true"]{font-family:"Segoe UI","Segoe UI Symbol","Arial Unicode MS",Arial,sans-serif;}
    .annotation-modal-content{height:80vh;min-height:0;}
    .modal-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;border-bottom:2px solid #e0e0e0;padding-bottom:15px;cursor:move;}
    .modal-header h2{margin:0;color:#333;font-size:20px;}
    .modal-close{background:none;border:none;font-size:28px;cursor:pointer;color:#999;padding:0;width:30px;height:30px;line-height:30px;text-align:center;}
    .modal-close:hover{color:#333;}
    .modal-resize-handle{position:absolute;z-index:15;user-select:none;touch-action:none;}
    .modal-resize-handle.n{top:-5px;left:10px;right:10px;height:10px;cursor:ns-resize;}
    .modal-resize-handle.s{bottom:-5px;left:10px;right:10px;height:10px;cursor:ns-resize;}
    .modal-resize-handle.e{top:10px;right:-5px;bottom:10px;width:10px;cursor:ew-resize;}
    .modal-resize-handle.w{top:10px;left:-5px;bottom:10px;width:10px;cursor:ew-resize;}
    .modal-resize-handle.ne{top:-6px;right:-6px;width:12px;height:12px;cursor:nesw-resize;}
    .modal-resize-handle.nw{top:-6px;left:-6px;width:12px;height:12px;cursor:nwse-resize;}
    .modal-resize-handle.se{bottom:-6px;right:-6px;width:12px;height:12px;cursor:nwse-resize;}
    .modal-resize-handle.sw{bottom:-6px;left:-6px;width:12px;height:12px;cursor:nesw-resize;}
    .refs-list{margin:0;padding:0;}
    .ref-item{background:#f8f9fa;border-left:4px solid #2196f3;padding:15px;margin-bottom:10px;border-radius:4px;line-height:1.6;position:relative;}
    .ref-number{display:inline-block;width:30px;font-weight:600;color:#2196f3;vertical-align:top;}
    .ref-text{margin-left:35px;color:#333;min-height:24px;line-height:1.7;padding:3px 0;display:block;overflow:visible;}
    .ref-text[contenteditable="true"]{outline:2px solid #2196f3;outline-offset:2px;padding:8px 10px 10px;border-radius:4px;background:#fff;cursor:text;line-height:1.7;overflow:visible;}
    .ref-text[contenteditable="true"]:focus{background:#fff;box-shadow:0 0 0 3px rgba(33,150,243,0.2);}
    .modal-footer{display:flex;justify-content:flex-end;gap:10px;margin-top:20px;padding-top:20px;border-top:2px solid #e0e0e0;}
    .modal-btn{padding:10px 20px;border:none;border-radius:4px;cursor:pointer;font-size:14px;font-weight:600;transition:all .2s;}
    .modal-btn-save{background:#4caf50;color:#fff;}
    .modal-btn-save:hover{background:#45a049;}
    .modal-btn-cancel{background:#e0e0e0;color:#333;}
    .modal-btn-cancel:hover{background:#d0d0d0;}
    .annotation-editor-toolbar{display:flex;flex-direction:column;gap:8px;margin:0 0 12px 0;flex-shrink:0;}
    .annotation-toolbar-row{display:flex;flex-wrap:wrap;align-items:center;gap:8px;}
    .annotation-toolbar-label{font-size:12px;color:#666;font-weight:600;}
    .annotation-select{background:#fff;border:1px solid #ddd;padding:6px 8px;border-radius:4px;font-size:12px;color:#333;}
    .annotation-select:focus{outline:2px solid rgba(102,126,234,0.3);outline-offset:1px;}
    .annotation-divider{width:1px;height:22px;background:#e0e0e0;display:inline-block;margin:0 2px;}
    .annotation-editor-btn{background:#f5f5f7;border:1px solid #d7d7d7;padding:6px 10px;border-radius:4px;cursor:pointer;font-size:13px;line-height:1;min-width:30px;display:inline-flex;align-items:center;justify-content:center;}
    .annotation-editor-btn:hover{background:#eaeaea;}
    .annotation-color-input{width:28px;height:28px;border:1px solid #d7d7d7;border-radius:4px;padding:0;background:#fff;cursor:pointer;}
    .annotation-editor{width:100%;min-height:0;flex:1;padding:24px;border:2px solid #ddd;border-radius:6px;font-size:14px;font-family:inherit;line-height:1.7;background:#fff;overflow-y:scroll;white-space:pre-wrap;box-sizing:border-box;scrollbar-gutter:stable;}
    .annotation-modal-body{position:relative;display:flex;flex-direction:column;gap:8px;flex:1;min-height:0;}
    .annotation-editor:focus{outline:none;border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,0.15);}
    .annotation-editor.preview{background:#f9f9f9;}
    .annotation-editor sup{font-size:0.8em;vertical-align:super;}
    .annotation-editor sub{font-size:0.8em;vertical-align:sub;}
    .annotation-editor table.annotation-table{border-collapse:collapse;width:100%;margin:8px 0;}
    .annotation-editor table.annotation-table td,.annotation-editor table.annotation-table th{border:1px solid #d5d5d5;padding:6px 8px;font-size:13px;}
    .annotation-editor .annotation-code-block{background:#f4f6f8;border:1px solid #d9e1ea;border-radius:4px;padding:8px;font-family:Consolas,Monaco,monospace;font-size:12px;white-space:pre-wrap;}
    .annotation-bookmark{background:#fff7e6;border:1px solid #ffe2a8;border-radius:4px;padding:2px 6px;font-size:12px;color:#7a4b00;display:inline-flex;align-items:center;gap:4px;}
    .annotation-code-view{font-family:Consolas,Monaco,monospace;padding:24px;box-sizing:border-box;}
    .annotation-editor-footer{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:14px;padding-top:14px;border-top:2px solid #e0e0e0;flex-shrink:0;}
    .annotation-editor-stats{display:flex;align-items:center;gap:12px;font-size:12px;color:#666;}
    .annotation-word-count{font-weight:600;color:#333;}
    .annotation-lang-indicator{padding:3px 8px;border-radius:12px;background:#eef2ff;color:#3f51b5;font-weight:600;font-size:11px;letter-spacing:.4px;}
    .annotation-editor-actions{display:flex;align-items:center;gap:10px;}
    .annotation-modal-body{position:relative;display:flex;flex-direction:column;gap:8px;flex:1;min-height:0;}
    .annotation-symbols-panel{position:absolute;right:0;top:52px;width:min(520px,90%);background:#fff;border:1px solid #d8d8d8;border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,0.12);padding:12px;z-index:50;display:none;}
    .annotation-symbols-panel.active{display:block;}
    .annotation-symbols-header{display:flex;gap:8px;align-items:center;margin-bottom:8px;}
    .annotation-symbols-search{flex:1;padding:6px 8px;border:1px solid #ddd;border-radius:4px;font-size:12px;}
    .annotation-symbols-category{padding:6px 8px;border:1px solid #ddd;border-radius:4px;font-size:12px;background:#fff;}
    .annotation-symbols-toggles{display:flex;gap:12px;align-items:center;font-size:12px;color:#555;margin-bottom:8px;}
    .annotation-symbols-toggles label{display:flex;align-items:center;gap:6px;cursor:pointer;}
    .annotation-symbols-grid{display:grid;grid-template-columns:repeat(8,minmax(0,1fr));gap:6px;margin-bottom:8px;}
    .annotation-symbol-cell{position:relative;}
    .annotation-symbol-btn{width:100%;border:1px solid #e1e1e1;border-radius:6px;background:#f9f9f9;padding:10px 6px;font-size:18px;cursor:pointer;}
    .annotation-symbol-btn:hover{background:#f0f0f0;}
    .annotation-symbol-btn:focus{outline:2px solid rgba(102,126,234,0.4);outline-offset:1px;}
    .annotation-symbol-fav{position:absolute;top:4px;right:4px;background:transparent;border:none;font-size:12px;cursor:pointer;color:#aaa;}
    .annotation-symbol-fav.active{color:#f4b400;}
    .annotation-symbols-footer{border-top:1px solid #eee;padding-top:8px;font-size:12px;color:#666;}
    .annotation-symbols-section{margin-bottom:6px;}
    .annotation-symbols-title{font-weight:600;color:#333;margin-right:6px;}
    .annotation-symbols-recent,.annotation-symbols-favorites{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px;}
    .annotation-symbol-chip{border:1px solid #e1e1e1;border-radius:6px;background:#fff;padding:4px 6px;cursor:pointer;}
    .annotation-symbols-info{font-size:11px;color:#777;margin-top:6px;}
    @media (max-width:900px){.annotation-symbols-grid{grid-template-columns:repeat(6,minmax(0,1fr));}}
    @media (max-width:600px){.annotation-symbols-grid{grid-template-columns:repeat(4,minmax(0,1fr));}}
    .annotation-modal-body{position:relative;display:flex;flex-direction:column;gap:8px;flex:1;min-height:0;}
    .annotation-symbols-panel{position:absolute;right:0;top:52px;width:min(520px,90%);background:#fff;border:1px solid #d8d8d8;border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,0.12);padding:12px;z-index:50;display:none;}
    .annotation-symbols-panel.active{display:block;}
    .annotation-symbols-header{display:flex;gap:8px;align-items:center;margin-bottom:8px;}
    .annotation-symbols-search{flex:1;padding:6px 8px;border:1px solid #ddd;border-radius:4px;font-size:12px;}
    .annotation-symbols-category{padding:6px 8px;border:1px solid #ddd;border-radius:4px;font-size:12px;background:#fff;}
    .annotation-symbols-toggles{display:flex;gap:12px;align-items:center;font-size:12px;color:#555;margin-bottom:8px;}
    .annotation-symbols-toggles label{display:flex;align-items:center;gap:6px;cursor:pointer;}
    .annotation-symbols-grid{display:grid;grid-template-columns:repeat(8,minmax(0,1fr));gap:6px;margin-bottom:8px;}
    .annotation-symbol-cell{position:relative;}
    .annotation-symbol-btn{width:100%;border:1px solid #e1e1e1;border-radius:6px;background:#f9f9f9;padding:10px 6px;font-size:18px;cursor:pointer;}
    .annotation-symbol-btn:hover{background:#f0f0f0;}
    .annotation-symbol-btn:focus{outline:2px solid rgba(102,126,234,0.4);outline-offset:1px;}
    .annotation-symbol-fav{position:absolute;top:4px;right:4px;background:transparent;border:none;font-size:12px;cursor:pointer;color:#aaa;}
    .annotation-symbol-fav.active{color:#f4b400;}
    .annotation-symbols-footer{border-top:1px solid #eee;padding-top:8px;font-size:12px;color:#666;}
    .annotation-symbols-section{margin-bottom:6px;}
    .annotation-symbols-title{font-weight:600;color:#333;margin-right:6px;}
    .annotation-symbols-recent,.annotation-symbols-favorites{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px;}
    .annotation-symbol-chip{border:1px solid #e1e1e1;border-radius:6px;background:#fff;padding:4px 6px;cursor:pointer;}
    .annotation-symbols-info{font-size:11px;color:#777;margin-top:6px;}
    @media (max-width:900px){.annotation-symbols-grid{grid-template-columns:repeat(6,minmax(0,1fr));}}
    @media (max-width:600px){.annotation-symbols-grid{grid-template-columns:repeat(4,minmax(0,1fr));}}
    .ref-actions{position:absolute;top:5px;right:5px;display:flex;gap:5px;}
    .ref-action-btn{background:#fff;border:1px solid #ddd;padding:4px 8px;border-radius:3px;cursor:pointer;font-size:11px;color:#666;}
    .ref-action-btn:hover{background:#f0f0f0;color:#333;}
    .ref-action-btn.delete{color:#d32f2f;border-color:#d32f2f;}
    .ref-action-btn.delete:hover{background:#ffebee;}
    .ref-action-btn.merge{color:#2196f3;border-color:#2196f3;}
    .ref-action-btn.merge:hover{background:#e3f2fd;}
    .line-editor-modal{display:none;position:fixed;z-index:2000;left:0;top:0;width:100%;height:100%;background:rgba(0,0,0,0.5);overflow:auto;}
    .line-editor-modal.active{display:flex;align-items:center;justify-content:center;}
    .line-editor-content{background:#fff;padding:20px;border-radius:8px;max-width:700px;width:80%;max-height:70vh;box-shadow:0 4px 20px rgba(0,0,0,0.3);}
    .line-editor-content.resizable{resize:both;overflow:auto;min-width:320px;min-height:200px;width:80vw;height:60vh;max-width:95vw;max-height:90vh;}
    .line-editor-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;border-bottom:2px solid #e0e0e0;padding-bottom:10px;}
    .line-editor-header h2{margin:0;color:#333;font-size:18px;}
    .line-editor-textarea{width:100%;min-height:150px;max-height:400px;padding:12px;border:2px solid #3a3f52;border-radius:4px;font-size:14px;font-family:inherit;line-height:1.6;resize:vertical;background:#232633;color:#e6e8ee;}
    .line-editor-textarea:focus{outline:none;border-color:#6c63ff;background:#1f2230;}
    .annotation-editor-toolbar{display:flex;flex-direction:column;gap:8px;margin:0 0 12px 0;flex-shrink:0;}
    .annotation-toolbar-row{display:flex;flex-wrap:wrap;align-items:center;gap:8px;}
    .annotation-toolbar-label{font-size:12px;color:#666;font-weight:600;}
    .annotation-select{background:#fff;border:1px solid #ddd;padding:6px 8px;border-radius:4px;font-size:12px;color:#333;}
    .annotation-select:focus{outline:2px solid rgba(102,126,234,0.3);outline-offset:1px;}
    .annotation-divider{width:1px;height:22px;background:#e0e0e0;display:inline-block;margin:0 2px;}
    .annotation-editor-btn{background:#f5f5f7;border:1px solid #d7d7d7;padding:6px 10px;border-radius:4px;cursor:pointer;font-size:13px;line-height:1;min-width:30px;display:inline-flex;align-items:center;justify-content:center;}
    .annotation-editor-btn:hover{background:#eaeaea;}
    .annotation-color-input{width:28px;height:28px;border:1px solid #d7d7d7;border-radius:4px;padding:0;background:#fff;cursor:pointer;}
    .annotation-editor{width:100%;min-height:0;flex:1;padding:24px;border:2px solid #ddd;border-radius:6px;font-size:14px;font-family:inherit;line-height:1.7;background:#fff;overflow-y:scroll;white-space:pre-wrap;box-sizing:border-box;scrollbar-gutter:stable;}
    .annotation-modal-body{position:relative;display:flex;flex-direction:column;gap:8px;flex:1;min-height:0;}
    .annotation-editor:focus{outline:none;border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,0.15);}
    .annotation-editor.preview{background:#f9f9f9;}
    .annotation-editor sup{font-size:0.8em;vertical-align:super;}
    .annotation-editor sub{font-size:0.8em;vertical-align:sub;}
    .annotation-editor table.annotation-table{border-collapse:collapse;width:100%;margin:8px 0;}
    .annotation-editor table.annotation-table td,.annotation-editor table.annotation-table th{border:1px solid #d5d5d5;padding:6px 8px;font-size:13px;}
    .annotation-editor .annotation-code-block{background:#f4f6f8;border:1px solid #d9e1ea;border-radius:4px;padding:8px;font-family:Consolas,Monaco,monospace;font-size:12px;white-space:pre-wrap;}
    .annotation-bookmark{background:#fff7e6;border:1px solid #ffe2a8;border-radius:4px;padding:2px 6px;font-size:12px;color:#7a4b00;display:inline-flex;align-items:center;gap:4px;}
    .annotation-code-view{font-family:Consolas,Monaco,monospace;padding:24px;box-sizing:border-box;}
    .annotation-editor-footer{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:14px;padding-top:14px;border-top:2px solid #e0e0e0;flex-shrink:0;}
    .annotation-editor-stats{display:flex;align-items:center;gap:12px;font-size:12px;color:#666;}
    .annotation-word-count{font-weight:600;color:#333;}
    .annotation-lang-indicator{padding:3px 8px;border-radius:12px;background:#eef2ff;color:#3f51b5;font-weight:600;font-size:11px;letter-spacing:.4px;}
    .annotation-editor-actions{display:flex;align-items:center;gap:10px;}
    .line-editor-actions{display:flex;justify-content:flex-end;gap:10px;margin-top:15px;padding-top:15px;border-top:1px solid #e0e0e0;}
    .line {
      padding: 8px 12px;
      margin: 2px 0;
      border-radius: 4px;
      cursor: pointer;
      transition: all .2s;
      border-left: 3px solid transparent;
      font-size: 14px;
      line-height: 1.5;
      user-select: none;
      position: relative;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .line:hover {
      background: #f0f0f0;
      border-left-color: #667eea;
    }
    .line.selected {
      background: #e3f2fd !important;
      border-left-color: #2196f3 !important;
      font-weight: 500;
    }
    .line-number {
      display: inline-block;
      width: 50px;
      color: #999;
      font-size: 12px;
      flex-shrink: 0;
    }
    .line-text {
      flex: 1;
      padding-right: 20px;
    }
    .line-copy-btn {
      position: absolute;
      right: 8px;
      top: 50%;
      transform: translateY(-50%);
      opacity: 0;
      transition: opacity .2s, transform .2s;
      background: rgba(211, 47, 47, 0.1);
      border: none;
      padding: 2px;
      margin: 0;
      cursor: pointer;
      font-size: 16px;
      width: 22px;
      height: 22px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      line-height: 1;
      z-index: 10;
      border-radius: 3px;
      color: #d32f2f;
    }
    .line:hover .line-copy-btn {
      opacity: 0.9;
      background: rgba(211, 47, 47, 0.15);
    }
    .line-copy-btn:hover {
      opacity: 1 !important;
      background: rgba(211, 47, 47, 0.25);
      transform: translateY(-50%) scale(1.2);
      color: #b71c1c;
    }
    .empty-state {
      text-align: center;
      padding: 32px 20px;
      color: #a7aec2;
      background: #242834;
      border: 1px dashed #3a3f52;
    }
    .empty-state h3 {
      margin-bottom: 8px;
      color: #e6e8ee;
      font-size: 18px;
    }
    .empty-state code {
      background: #2f3342;
      padding: 2px 6px;
      border-radius: 6px;
      color: #c6cbe0;
    }
    .back-link {
      display: inline-block;
      margin-bottom: 20px;
      color: #2196f3;
      text-decoration: none;
      font-weight: 500;
      transition: color 0.2s;
    }
    .back-link:hover {
      color: #1976d2;
      text-decoration: underline;
    }
    .viewer-container {
      padding: 20px;
      background: #fff;
    }
    .viewer-content {
      max-width: 900px;
      margin: 0 auto;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      line-height: 1.6;
      color: #333;
    }
    .viewer-content p {
      margin: 1em 0;
      text-align: justify;
    }
    .viewer-content blockquote {
      border-left: 4px solid #3498db;
      margin: 1em 0;
      padding-left: 1em;
      color: #555;
      font-style: italic;
    }
    .viewer-content h1, .viewer-content h2, .viewer-content h3,
    .viewer-content h4, .viewer-content h5, .viewer-content h6 {
      margin-top: 1.5em;
      margin-bottom: 0.5em;
      color: #2c3e50;
    }
    .btn,
    .btn-primary,
    .btn-secondary,
    .btn-danger {
      padding: 10px 18px;
      border: none;
      border-radius: 10px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      justify-content: center;
    }
    .btn-primary {
      background: #6c63ff;
      color: #fff;
      box-shadow: 0 8px 18px rgba(108, 99, 255, 0.25);
    }
    .btn-primary:hover {
      background: #5a52ea;
    }
    .btn.is-disabled {
      opacity: 0.6;
      cursor: not-allowed;
      pointer-events: auto;
    }
    .btn-secondary {
      background: #2f3342;
      color: #e6e8ee;
      border: 1px solid #3a3f52;
    }
    .btn-secondary:hover {
      background: #3a3f52;
    }
    .btn-danger {
      background: #3b2527;
      color: #ff9aa5;
      border: 1px solid #5a3438;
    }
    .btn-danger:hover {
      background: #4a2b2f;
    }
    .btn-hero {
      padding: 12px 26px;
      font-size: 15px;
      border-radius: 12px;
    }
    .status-card {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      background: #2f3342;
      border: 1px solid #3a3f52;
      border-radius: 10px;
      font-size: 12px;
      color: #c6cbe0;
    }
    .actions-row {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
    }
    .muted-text {
      color: #a7aec2;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Работа с метаданными статей</h1>
      <p>Загрузите выпуск и сгенерируйте XML</p>
      <div class="header-actions">
        {% set total_files = files|length %}
        {% set processed_files = files|selectattr('is_processed')|list|length %}
        {% set progress_pct = (processed_files * 100 // total_files) if total_files else 0 %}
        <button id="generateXmlBtn" data-progress-pct="{{ progress_pct }}" class="btn btn-primary btn-hero" style="{% if progress_pct < 100 %} opacity: 0.6; cursor: not-allowed;{% endif %}"{% if progress_pct < 100 %} disabled title="Кнопка доступна после обработки 100% файлов"{% endif %}>
          🚀 Сгенерировать XML
        </button>
        <label class="checkbox-inline">
          <input type="checkbox" id="allowPartialXml" style="transform: translateY(1px);">
          Генерировать XML даже при ошибках
          <small>(не все статьи могут быть обработаны)</small>
        </label>
      </div>
      <script>
        window.handleArchiveUpload = window.handleArchiveUpload || function(event) {
          if (event && event.preventDefault) event.preventDefault();
          const fileInput = document.getElementById("inputArchiveFile");
          const status = document.getElementById("inputArchiveStatus");
          if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
            if (status) {
              status.textContent = "Выберите ZIP файл.";
              status.style.color = "#c62828";
            }
            return false;
          }
          const formData = new FormData();
          formData.append("archive", fileInput.files[0]);
          if (status) {
            status.textContent = "Загрузка архива...";
            status.style.color = "#555";
          }
          fetch("/upload-input-archive", {
            method: "POST",
            body: formData
          })
            .then((response) => response.json().catch(() => ({})).then((data) => ({ response, data })))
            .then(({ response, data }) => {
              if (!response.ok || !data.success) {
                if (status) {
                  status.textContent = data.error || "Ошибка загрузки архива.";
                  status.style.color = "#c62828";
                }
                return;
              }
              if (status) {
                status.textContent = data.message || "Архив загружен.";
                status.style.color = "#2e7d32";
              }
              const form = document.getElementById("inputArchiveForm");
              if (form) {
                const existing = document.getElementById("archiveUploadNotice");
                if (existing) existing.remove();
                const notice = document.createElement("div");
                notice.id = "archiveUploadNotice";
                notice.style.cssText = "margin-top:10px;background:#e8f5e9;border:1px solid #81c784;color:#2e7d32;padding:8px 10px;border-radius:4px;font-size:12px;font-weight:600;";
                notice.textContent = "Архив успешно загружен. Нажмите «Обработать выпуск», чтобы начать обработку.";
                form.appendChild(notice);
              }
              if (data.archive) {
                window.currentArchive = data.archive;
                sessionStorage.setItem("lastArchiveName", data.archive);
              }
              if (typeof fetchArchiveStatus === "function") {
                fetchArchiveStatus();
              } else if (typeof updateArchiveUi === "function") {
                updateArchiveUi({ status: "idle", archive: data.archive });
              } else if (processArchiveBtn) {
                processArchiveBtn.classList.remove("is-disabled");
                processArchiveBtn.removeAttribute("aria-disabled");
              }
            })
            .catch(() => {
              if (status) {
                status.textContent = "Ошибка загрузки архива.";
                status.style.color = "#c62828";
              }
            });
          return false;
        };
      </script>
      <div class="step-bar" id="stepBar" data-total="{{ files|length if files else 0 }}" data-processed="{{ files|selectattr('is_processed')|list|length if files else 0 }}">
        <div class="step" data-step="1" data-label="1 Загрузка">1 Загрузка</div>
        <div class="step" data-step="2" data-label="2 Разметка">2 Разметка</div>
        <div class="step" data-step="3" data-label="3 Экспорт XML">3 Экспорт XML</div>
      </div>
    </div>
    <div class="content">
      <div class="upload-panel card">
        <div class="upload-title">📦 Загрузите архив выпуска</div>
        <div class="upload-subtitle">ZIP с PDF статей и дополнительными файлами (DOCX, RTF, HTML, IDML, LaTeX).</div>
        <form id="inputArchiveForm" class="upload-form" enctype="multipart/form-data" action="/upload-input-archive" method="post">
          <input type="file" id="inputArchiveFile" name="archive" accept=".zip,application/zip" required>
          <button type="button" id="uploadArchiveBtn" class="btn btn-primary">Загрузить архив</button>
          <span id="inputArchiveStatus" class="upload-status"></span>
        </form>
        <details class="details-card">
          <summary>Показать требования к архиву</summary>
          <ul>
            <li>📁 Без папок внутри</li>
            <li>🏷 Имя: <code>issn_год_том_номер</code> или <code>issn_год_номер_выпуска</code></li>
            <li>📄 Обязательно: PDF статей выпуска</li>
            <li>📝 Дополнительно: DOCX / RTF / HTML / IDML / LaTeX</li>
            <li>📦 Общий файл: <code>full_issue</code> (например, <code>full_issue.docx</code> или <code>full_issue.tex</code>)</li>
          </ul>
        </details>
        <div style="margin-top: 10px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center;">
          <button type="button" id="processArchiveBtn" class="btn btn-primary">Обработать выпуск с помощью ИИ</button>
          <div id="archiveProgressBar" class="progress-bar" aria-hidden="true">
            <div id="archiveProgressFill" class="progress-bar-fill"></div>
          </div>
          <span id="archiveProgress" class="status-card"></span>
        </div>
        <div style="margin-top: 6px; display:flex; gap: 10px; flex-wrap: wrap; align-items:center;">
          <span id="archiveDetails" class="upload-status"></span>
        </div>
                <div id="projectModal" class="modal">
          <div class="modal-content" style="max-width: 520px;">
            <div class="modal-header">
              <h2>Выбор проекта</h2>
              <button type="button" class="modal-close" data-action="close">×</button>
            </div>
            <div style="display:flex; flex-direction:column; gap:12px;">
              <label style="font-weight:600; font-size:14px;">Проект</label>
              <select id="projectSelect" style="width:100%; padding:10px; border:1px solid #ddd; border-radius:4px; font-size:14px;"></select>
              <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:8px;">
                <button type="button" class="modal-btn modal-btn-cancel" data-action="cancel">Отмена</button>
                <button type="button" id="projectOpenConfirm" class="modal-btn modal-btn-save">Открыть</button>
              </div>
            </div>
          </div>
        </div>
        <div class="actions-row" style="margin-top: 10px;">
          <button type="button" id="saveProjectBtn" class="btn btn-primary" onclick="window.saveProject && window.saveProject()">💾 Сохранить проект</button>
          <button type="button" id="openProjectBtn" class="btn btn-secondary" onclick="window.openProject && window.openProject()">📂 Открыть проект</button>
          <button type="button" id="deleteProjectBtn" class="btn btn-danger" onclick="window.deleteProject && window.deleteProject()">🗑 Удалить выпуск</button>
          <button type="button" id="downloadProjectBtn" class="btn btn-secondary">⬇ Скачать проект</button>
          <button type="button" id="restoreProjectBtn" class="btn btn-secondary">📤 Восстановить проект</button>
          <input type="file" id="restoreProjectArchiveInput" accept=".zip,application/zip" style="display:none;">
          <span id="projectStatus" class="upload-status muted-text"></span>
        </div>
        
        <script>
          window.saveProject = async () => {
            const issue = window.prompt("Укажите имя выпуска (папки):");
            if (!issue) {
              return;
            }
            const status = document.getElementById("projectStatus");
            if (status) {
              status.textContent = "Сохранение проекта...";
              status.style.color = "#555";
            }
            try {
              const resp = await fetch("/project-save", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ issue })
              });
              const data = await resp.json().catch(() => ({}));
              if (!resp.ok || !data.success) {
                if (status) {
                  status.textContent = data.error || "Ошибка сохранения проекта.";
                  status.style.color = "#c62828";
                }
                return;
              }
              if (status) {
                status.textContent = "Проект сохранен: " + (data.issue || issue);
                status.style.color = "#2e7d32";
              }
              setTimeout(() => window.location.reload(), 1200);
            } catch (_) {
              if (status) {
                status.textContent = "Ошибка сохранения проекта.";
                status.style.color = "#c62828";
              }
            }
          };

          window.openProject = async () => {
          const status = document.getElementById("projectStatus");
          const modal = document.getElementById("projectModal");
          const select = document.getElementById("projectSelect");
          if (status) {
            status.textContent = "Загрузка списка проектов...";
            status.style.color = "#555";
          }
          try {
            const resp = await fetch("/project-snapshots");
            const data = await resp.json().catch(() => ({}));
            const snapshots = data.snapshots || [];
            const options = [];
            snapshots.forEach((run) => {
              (run.issues || []).forEach((issue) => {
                options.push({ run: run.run, issue });
              });
            });
            if (!options.length) {
              if (status) {
                status.textContent = "Нет сохраненных проектов.";
                status.style.color = "#c62828";
              }
              return;
            }
            if (select) {
              select.innerHTML = "";
              options.forEach((opt) => {
                const option = document.createElement("option");
                option.value = JSON.stringify(opt);
                const runLabel = opt.run === "current" ? "текущий" : `архив ${opt.run}`;
                option.textContent = `${opt.issue} (${runLabel})`;
                select.appendChild(option);
              });
            }
            if (modal) {
              modal.classList.add("active");
            }
            if (status) {
              status.textContent = "";
            }
          } catch (_) {
            if (status) {
              status.textContent = "Ошибка загрузки проектов.";
              status.style.color = "#c62828";
            }
          }
        };

        const projectModal = document.getElementById("projectModal");
        const projectSelect = document.getElementById("projectSelect");
        const projectOpenConfirm = document.getElementById("projectOpenConfirm");
        const closeProjectModal = () => {
          if (projectModal) projectModal.classList.remove("active");
        };
        if (projectModal) {
          projectModal.addEventListener("click", (e) => {
            const target = e.target;
            if (!target) return;
            if (target === projectModal) {
              closeProjectModal();
              return;
            }
            const btn = target.closest("button");
            if (!btn) return;
            const action = btn.dataset.action;
            if (action === "close" || action === "cancel") {
              closeProjectModal();
            }
          });
        }
        if (projectOpenConfirm) {
          projectOpenConfirm.addEventListener("click", async () => {
            const status = document.getElementById("projectStatus");
            if (!projectSelect || !projectSelect.value) {
              if (status) {
                status.textContent = "Выберите проект.";
                status.style.color = "#c62828";
              }
              return;
            }
            let target = null;
            try {
              target = JSON.parse(projectSelect.value);
            } catch (_) {
              target = null;
            }
            if (!target) {
              if (status) {
                status.textContent = "Некорректный выбор проекта.";
                status.style.color = "#c62828";
              }
              return;
            }
            const restore = async (overwrite) => {
              const restoreResp = await fetch("/project-restore", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ run: target.run, issue: target.issue, overwrite })
              });
              return restoreResp.json().catch(() => ({}));
            };
            let restoreData = await restore(false);
            if (!restoreData.success && restoreData.code === "dest_exists") {
              const confirmOverwrite = window.confirm("Папка выпуска уже существует. Перезаписать?");
              if (!confirmOverwrite) {
                if (status) {
                  status.textContent = "Восстановление отменено.";
                  status.style.color = "#555";
                }
                closeProjectModal();
                return;
              }
              restoreData = await restore(true);
            }
            if (!restoreData.success) {
              if (status) {
                status.textContent = restoreData.error || "Ошибка восстановления.";
                status.style.color = "#c62828";
              }
              return;
            }
            if (status) {
              status.textContent = "Проект восстановлен: " + target.issue;
              status.style.color = "#2e7d32";
            }
            closeProjectModal();
            setTimeout(() => window.location.reload(), 1200);
          });
        }
              let restoreData = await restore(false);
              if (!restoreData.success && restoreData.code === "dest_exists") {
                const confirmOverwrite = window.confirm("Папка выпуска уже существует. Перезаписать?");
                if (!confirmOverwrite) {
                  if (status) {
                    status.textContent = "Восстановление отменено.";
                    status.style.color = "#555";
                  }
                  return;
                }
                restoreData = await restore(true);
              }
              if (!restoreData.success) {
                if (status) {
                  status.textContent = restoreData.error || "Ошибка восстановления.";
                  status.style.color = "#c62828";
                }
                return;
              }
              if (status) {
                status.textContent = "Проект восстановлен: " + target.issue;
                status.style.color = "#2e7d32";
              }
              setTimeout(() => window.location.reload(), 1200);
            } catch (_) {
              if (status) {
                status.textContent = "Ошибка восстановления.";
                status.style.color = "#c62828";
              }
            }
          };
        </script>
      </div>
      {% if files %}
        <div class="upload-panel" style="margin-top: 12px;">
          <div class="upload-title">Статус разметки</div>
          <div style="display:flex;gap:12px;flex-wrap:wrap;font-size:12px;color:#444;">
            <div>Всего статей: <strong>{{ files|length }}</strong></div>
            <div>Размечено: <strong>{{ files|selectattr('is_processed')|list|length }}</strong></div>
            <div>Осталось: <strong>{{ (files|length) - (files|selectattr('is_processed')|list|length) }}</strong></div>
            {% set total_files = files|length %}
            {% set processed_files = files|selectattr('is_processed')|list|length %}
            {% set progress_pct = (processed_files * 100 // total_files) if total_files else 0 %}
            {% set progress_color = '#c62828' if progress_pct <= 30 else ('#f9a825' if progress_pct <= 70 else '#2e7d32') %}
            <div class="status-chip" style="background: {{ progress_color }}; color: #fff;">
              {{ progress_pct }}% готово
            </div>
            <a href="/markup/{{ files[0].name }}" class="btn-secondary" style="text-decoration:none; padding:6px 10px;">
              Перейти к разметке
            </a>
          </div>
        </div>
        <div class="file-list">
          {% for file in files %}
            <a href="/markup/{{ file.name }}" style="text-decoration: none; color: inherit;">
              <div class="file-item {% if file.is_processed %}processed{% endif %}" data-filename="{{ file.name }}">
                <div class="file-name {% if file.is_processed %}processed{% endif %}">
                  <span class="status-icon {% if file.is_processed %}processed{% endif %}">
                    {% if file.is_processed %}✓{% else %}○{% endif %}
                  </span>
                  <span style="word-break: break-word;">{{ file.display_name }}</span>
                </div>
                <div class="file-info">
                  {{ file.size_kb }} KB • {{ file.modified }}
                  {% if file.is_processed %}
                  <br><span style="color: #4caf50; font-weight: 600;">✓</span>
                  {% endif %}
                </div>
              </div>
            </a>
          {% endfor %}
        </div>
        
        <script>
          // Обработчик кнопки генерации XML
          const generateXmlBtn = document.getElementById("generateXmlBtn");
          if (generateXmlBtn) {
            const allowPartialXml = document.getElementById("allowPartialXml");
            const progressPct = parseInt(generateXmlBtn.dataset.progressPct || "0", 10);
            const canGenerateXml = progressPct >= 100;

            const updateXmlButtonState = () => {
              const allow = allowPartialXml && allowPartialXml.checked;
              if (canGenerateXml || allow) {
                generateXmlBtn.disabled = false;
                generateXmlBtn.style.opacity = "1";
                generateXmlBtn.style.cursor = "pointer";
                generateXmlBtn.title = allow && !canGenerateXml
                  ? "XML будет сгенерирован даже при неполной обработке"
                  : "";
              } else {
                generateXmlBtn.disabled = true;
                generateXmlBtn.style.opacity = "0.6";
                generateXmlBtn.style.cursor = "not-allowed";
                generateXmlBtn.title = "Кнопка доступна после обработки 100% файлов";
              }
            };

            updateXmlButtonState();
            if (allowPartialXml) {
              allowPartialXml.addEventListener("change", updateXmlButtonState);
            }

            generateXmlBtn.addEventListener("click", async function() {
            const btn = this;
            const originalText = btn.textContent;

            if (!canGenerateXml && !(allowPartialXml && allowPartialXml.checked)) {
              alert("XML доступен после обработки 100% файлов. Включите чек-бокс, если хотите сгенерировать XML раньше.");
              return;
            }
            
            // Блокируем кнопку и показываем процесс
            btn.disabled = true;
            btn.textContent = "⏳ Генерация XML...";
            btn.style.background = "#999";
            
            try {
              const response = await fetch("/generate-xml", {
                method: "POST",
                headers: {
                  "Content-Type": "application/json"
                }
              });
              
              const data = await response.json();
              
              if (data.success) {
                btn.textContent = "✅ " + data.message;
                btn.style.background = "#4caf50";
                
                // Скачиваем все XML файлы по очереди
                if (data.files && data.files.length > 0) {
                  // Функция для скачивания файла
                  const downloadFile = (url, filename) => {
                    return new Promise((resolve) => {
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = filename;
                      a.style.display = "none";
                      document.body.appendChild(a);
                      a.click();
                      document.body.removeChild(a);
                      // Небольшая задержка между скачиваниями
                      setTimeout(resolve, 300);
                    });
                  };
                  
                  // Скачиваем все файлы последовательно
                  for (const file of data.files) {
                    await downloadFile(file.url, file.name);
                  }
                  
                  const currentArchive = window.currentArchive || sessionStorage.getItem("lastArchiveName");
                  if (currentArchive) {
                    sessionStorage.setItem(`xml_done_${currentArchive}`, "1");
                  }
                }
                
                // Показываем уведомление
                const notification = document.createElement("div");
                notification.style.cssText = "position:fixed;top:20px;right:20px;background:#4caf50;color:#fff;padding:15px 20px;border-radius:4px;box-shadow:0 4px 12px rgba(0,0,0,0.2);z-index:3000;font-size:14px;max-width:400px;";
                notification.innerHTML = "<strong>Успешно!</strong><br>" + data.message + "<br><small>Скачано файлов: " + ((data.files && data.files.length) ? data.files.length : 0) + "</small>";
                document.body.appendChild(notification);
                
                setTimeout(() => {
                  notification.remove();
                }, 1000);
                // Сбрасываем состояние выпуска, чтобы можно было загрузить новый архив
                const currentArchive = window.currentArchive || sessionStorage.getItem("lastArchiveName");
                if (currentArchive) {
                  sessionStorage.removeItem(`xml_done_${currentArchive}`);
                }
                sessionStorage.removeItem("lastArchiveName");
                sessionStorage.removeItem("archive_done_reloaded");
                window.currentArchive = null;
                window.location.reload();
              } else {
                btn.textContent = "❌ Ошибка";
                btn.style.background = "#f44336";
                
                alert("Ошибка при генерации XML: " + (data.error || "Неизвестная ошибка"));
                
                setTimeout(() => {
                  btn.textContent = originalText;
                  btn.style.background = "#4caf50";
                  btn.disabled = false;
                }, 3000);
              }
            } catch (error) {
              btn.textContent = "❌ Ошибка";
              btn.style.background = "#f44336";
              alert("Ошибка при генерации XML: " + error.message);
              
              setTimeout(() => {
                btn.textContent = originalText;
                btn.style.background = "#4caf50";
                btn.disabled = false;
              }, 3000);
            }
          });
          }
          
          // Теперь используем прямые ссылки на /markup/<filename> вместо AJAX загрузки
          
          // Проверяем localStorage для файлов, которые были только что сохранены
          // и подсвечиваем их как обработанные
          (function() {
            try {
              const savedFiles = JSON.parse(localStorage.getItem("recently_saved_files") || "[]");
              if (savedFiles.length > 0) {
                savedFiles.forEach(function(filename) {
                  const fileItem = document.querySelector('.file-item[data-filename="' + filename + '"]');
                  if (fileItem) {
                    // Добавляем класс processed, если его еще нет
                    if (!fileItem.classList.contains("processed")) {
                      fileItem.classList.add("processed");
                      const fileName = fileItem.querySelector(".file-name");
                      const statusIcon = fileItem.querySelector(".status-icon");
                      const fileInfo = fileItem.querySelector(".file-info");
                      
                      if (fileName) fileName.classList.add("processed");
                      if (statusIcon) {
                        statusIcon.classList.add("processed");
                        statusIcon.textContent = "✓";
                      }
                      if (fileInfo) {
                        const processedText = fileInfo.querySelector("span[style*='#4caf50']");
                        if (!processedText) {
                          const processedSpan = document.createElement("span");
                          processedSpan.style.cssText = "color: #4caf50; font-weight: 600;";
                          processedSpan.textContent = "✓ Обработано";
                          fileInfo.appendChild(document.createElement("br"));
                          fileInfo.appendChild(processedSpan);
                        }
                      }
                    }
                  }
                });
                // Очищаем список после применения (чтобы не применять повторно при обновлении)
                localStorage.removeItem("recently_saved_files");
              }
            } catch (e) {
              console.error("Ошибка при проверке сохраненных файлов:", e);
            }
          })();
        </script>
        
        <!-- Модальные окна для формы -->
        <div id="refsModal" class="modal">
          <div class="modal-content resizable refs-modal-content" id="refsModalContent" style="resize:both;overflow:auto;min-width:360px;min-height:240px;">
            <div class="modal-header">
              <h2 id="modalTitle">Список литературы</h2>
              <div class="modal-header-actions">
                <button class="modal-expand-btn" id="refsModalExpandBtn" onclick="toggleRefsModalSize()" title="Увеличить/уменьшить окно">⛶</button>
                <button class="modal-close" onclick="closeRefsModal()">&times;</button>
              </div>
            </div>
            <div id="refsList" class="refs-list"></div>
            <div class="modal-footer">
              <button class="modal-btn modal-btn-cancel" onclick="closeRefsModal()">Отмена</button>
              <button class="modal-btn modal-btn-save" onclick="saveEditedReferences()">Сохранить изменения</button>
            </div>
          </div>
        </div>
        
        <div id="annotationModal" class="modal">
          <div class="modal-content resizable annotation-modal-content" id="annotationModalContent" style="resize:both;overflow:auto;min-width:360px;min-height:240px;">
            <div class="modal-header">
              <h2 id="annotationModalTitle">Аннотация</h2>
              <div class="modal-header-actions">
                <button class="modal-expand-btn" id="annotationModalExpandBtn" onclick="toggleAnnotationModalSize()" title="Увеличить/уменьшить окно">⛶</button>
                <button class="modal-close" onclick="closeAnnotationModal()">&times;</button>
              </div>
            </div>
            <div class="annotation-modal-body">
            <div class="annotation-editor-toolbar">
              <div class="annotation-toolbar-row">
                <select id="annotationStyleSelect" class="annotation-select" data-action="format-block" title="Стили абзаца">
                  <option value="p">Normal</option>
                  <option value="h1">Heading 1</option>
                  <option value="h2">Heading 2</option>
                  <option value="h3">Heading 3</option>
                </select>
                <select id="annotationFontSelect" class="annotation-select" data-action="font-name" title="Шрифт">
                  <option value="">Шрифт</option>
                  <option value="Times New Roman">Times New Roman</option>
                  <option value="Arial">Arial</option>
                  <option value="Calibri">Calibri</option>
                  <option value="Georgia">Georgia</option>
                  <option value="Cambria">Cambria</option>
                </select>
                <select id="annotationFontSizeSelect" class="annotation-select" data-action="font-size" title="Размер">
                  <option value="">Размер</option>
                  <option value="2">12</option>
                  <option value="3">14</option>
                  <option value="4">16</option>
                  <option value="5">18</option>
                  <option value="6">24</option>
                </select>
                <span class="annotation-divider"></span>
                <button type="button" class="annotation-editor-btn" data-action="bold" tabindex="-1" title="Полужирный"><strong>B</strong></button>
                <button type="button" class="annotation-editor-btn" data-action="italic" tabindex="-1" title="Курсив"><em>I</em></button>
                <button type="button" class="annotation-editor-btn" data-action="strike" tabindex="-1" title="Зачёркнутый"><span style="text-decoration:line-through;">S</span></button>
                <button type="button" class="annotation-editor-btn" data-action="annotation-sup" tabindex="-1" title="Верхний индекс">x<sup>2</sup></button>
                <button type="button" class="annotation-editor-btn" data-action="annotation-sub" tabindex="-1" title="Нижний индекс">x<sub>2</sub></button>
                <input type="color" class="annotation-color-input" data-action="text-color" title="Цвет текста" value="#1f1f1f">
                <input type="color" class="annotation-color-input" data-action="highlight-color" title="Маркер" value="#fff3a3">
                <span class="annotation-divider"></span>
                <button type="button" class="annotation-editor-btn" data-action="align-left" tabindex="-1" title="По левому краю">≡</button>
                <button type="button" class="annotation-editor-btn" data-action="align-center" tabindex="-1" title="По центру">≡</button>
                <button type="button" class="annotation-editor-btn" data-action="align-right" tabindex="-1" title="По правому краю">≡</button>
                <button type="button" class="annotation-editor-btn" data-action="align-justify" tabindex="-1" title="По ширине">≡</button>
                <button type="button" class="annotation-editor-btn" data-action="unordered-list" tabindex="-1" title="Маркированный список">•⋯</button>
                <button type="button" class="annotation-editor-btn" data-action="ordered-list" tabindex="-1" title="Нумерованный список">1.</button>
                <button type="button" class="annotation-editor-btn" data-action="link" tabindex="-1" title="Ссылка">🔗</button>
                <button type="button" class="annotation-editor-btn" data-action="bookmark" tabindex="-1" title="Закладка">🔖</button>
              </div>
              <div class="annotation-toolbar-row">
                <span class="annotation-toolbar-label">Вставка:</span>
                <button type="button" class="annotation-editor-btn" data-action="insert-table" tabindex="-1" title="Таблица">▦</button>
                <button type="button" class="annotation-editor-btn" data-action="insert-image" tabindex="-1" title="Изображение">🖼</button>
                <button type="button" class="annotation-editor-btn" data-action="insert-video" tabindex="-1" title="Видео">▶</button>
                <button type="button" class="annotation-editor-btn" data-action="insert-code" tabindex="-1" title="Вставка кода">&lt;/&gt;</button>
                <button type="button" class="annotation-editor-btn" data-action="toggle-symbols-panel" tabindex="-1" title="Специальные символы" onclick="toggleAnnotationSymbolsPanel()">Ω</button>
                <button type="button" class="annotation-editor-btn" data-action="toggle-preview" tabindex="-1" title="Просмотр">👁</button>
                <button type="button" class="annotation-editor-btn" data-action="toggle-fullscreen" tabindex="-1" title="Полноэкранный режим">⛶</button>
                <button type="button" class="annotation-editor-btn" data-action="toggle-code-view" tabindex="-1" title="HTML / Code View">HTML</button>
                <button type="button" class="annotation-editor-btn" data-action="insert-latex" tabindex="-1" title="LaTeX">LaTeX</button>
                <button type="button" class="annotation-editor-btn" data-action="insert-formula" tabindex="-1" title="Формула">Σ</button>
              </div>
            </div>
            <div id="annotationSymbolsPanel" class="annotation-symbols-panel" role="dialog" aria-label="Специальные символы" aria-hidden="true" style="display:none;">
              <div class="annotation-symbols-header">
                <input id="annotationSymbolsSearch" class="annotation-symbols-search" type="text" placeholder="Поиск: alpha, μ, degree, ≤" autocomplete="off">
                <select id="annotationSymbolsCategory" class="annotation-symbols-category">
                  <option value="all">Все</option>
                  <option value="greek">Греческий</option>
                  <option value="math">Математика</option>
                  <option value="arrows">Стрелки</option>
                  <option value="indices">Индексы</option>
                  <option value="units">Единицы</option>
                  <option value="currency">Валюты</option>
                  <option value="typography">Типографика</option>
                  <option value="latin">Диакритика</option>
                  <option value="other">Прочее</option>
                </select>
              </div>
              <div class="annotation-symbols-toggles">
                <label><input id="annotationSymbolsLatex" type="checkbox"> Как LaTeX</label>
                <label><input id="annotationSymbolsAutoClose" type="checkbox" checked> Автозакрытие</label>
              </div>
              <div id="annotationSymbolsGrid" class="annotation-symbols-grid" role="listbox" aria-label="Символы"></div>
              <div class="annotation-symbols-footer">
                <div class="annotation-symbols-section">
                  <span class="annotation-symbols-title">Недавние</span>
                  <div id="annotationSymbolsRecent" class="annotation-symbols-recent"></div>
                </div>
                <div class="annotation-symbols-section">
                  <span class="annotation-symbols-title">Избранное</span>
                  <div id="annotationSymbolsFavorites" class="annotation-symbols-favorites"></div>
                </div>
                <div class="annotation-symbols-info">Вставится в позицию курсора.</div>
              </div>
            </div>
            <div id="annotationModalEditor" class="annotation-editor" contenteditable="true" spellcheck="true" autocomplete="off" autocorrect="off" autocapitalize="off" data-ms-editor="false" data-gramm="false" style="padding:24px;box-sizing:border-box;height:32vh;max-height:32vh;overflow-y:scroll;"></div>
            <textarea id="annotationModalTextarea" class="line-editor-textarea annotation-code-view" style="display:none;"></textarea>
            <div class="annotation-editor-footer">
              <div class="annotation-editor-stats">
                <span id="annotationWordCount" class="annotation-word-count">СЛОВ: 0</span>
                <span id="annotationLangIndicator" class="annotation-lang-indicator">RU</span>
              </div>
              <div class="annotation-editor-actions">
                <button class="modal-btn modal-btn-cancel" onclick="closeAnnotationModal()">Отмена</button>
                <button class="modal-btn modal-btn-save" onclick="saveEditedAnnotation()">Сохранить изменения</button>
              </div>
            </div>
            </div>
          </div>
        </div>
        
        <div id="lineCopyModal" class="line-editor-modal">
          <div class="line-editor-content resizable" style="resize:both;overflow:auto;min-width:320px;min-height:200px;">
            <div class="line-editor-header">
              <h2>Копирование строки</h2>
              <button class="modal-close" data-action="close-copy">&times;</button>
            </div>
            <textarea id="lineCopyTextarea" class="line-editor-textarea" readonly></textarea>
            <div class="line-editor-actions">
              <button class="modal-btn modal-btn-cancel" data-action="close-copy">Закрыть</button>
              <button class="modal-btn modal-btn-save" data-action="copy-from-modal">Копировать целиком</button>
            </div>
          </div>
        </div>
        
        <!-- Глобальные JavaScript функции для работы с формой -->
        <script>
        // Глобальные функции для работы с модальным окном списка литературы
        function escapeHtml(text) {
          const div = document.createElement("div");
          div.textContent = text;
          return div.innerHTML;
        }
        
        let currentRefsFieldId = null;
        
        function viewReferences(fieldId, title) {
          const field = document.getElementById(fieldId);
          if (!field) return;
          
          currentRefsFieldId = fieldId;
          
          const refsText = field.value.trim();
          if (!refsText) {
            alert("Список литературы пуст");
            return;
          }
          
          const refs = refsText.split("\\n")
            .map(s => s.trim())
            .filter(Boolean);
          
          const modal = document.getElementById("refsModal");
          const modalTitle = document.getElementById("modalTitle");
          const refsList = document.getElementById("refsList");
          
          if (!modal || !modalTitle || !refsList) return;
          
          modalTitle.textContent = title;
          refsList.innerHTML = "";
          
          if (refs.length === 0) {
            refsList.innerHTML = "<p style='color:#999;text-align:center;padding:20px;'>Список литературы пуст</p>";
          } else {
            refs.forEach((ref, index) => {
              const refItem = document.createElement("div");
              refItem.className = "ref-item";
              refItem.dataset.index = index;
              const hasNext = index < refs.length - 1;
              refItem.innerHTML = `
                <span class="ref-number">${index + 1}.</span>
                <span class="ref-text" contenteditable="true" spellcheck="false">${escapeHtml(ref)}</span>
                <div class="ref-actions">
                  ${hasNext ? `<button class="ref-action-btn merge" onclick="mergeWithNext(this)" title="Объединить со следующим">⇅</button>` : ''}
                  <button class="ref-action-btn delete" onclick="deleteReference(this)" title="Удалить">✕</button>
                </div>
              `;
              attachRefTextHandlers(refItem);
              refsList.appendChild(refItem);
            });
          }
          
          modal.classList.add("active");
        }
        
        function syncReferencesField() {
          if (!currentRefsFieldId) return;
          const field = document.getElementById(currentRefsFieldId);
          if (!field) return;
          const refItems = document.querySelectorAll("#refsList .ref-item");
          const refs = Array.from(refItems)
            .map(item => {
              const textSpan = item.querySelector(".ref-text");
              return textSpan ? textSpan.textContent.trim() : "";
            })
            .filter(ref => ref.length > 0);
          field.value = refs.join("\\n");
          field.dispatchEvent(new Event("input", { bubbles: true }));
          if (window.updateReferencesCount) {
            window.updateReferencesCount(currentRefsFieldId);
          }
        }

        function mergeWithNext(btn) {
          const refItem = btn.closest(".ref-item");
          if (!refItem) return;
          
          const nextItem = refItem.nextElementSibling;
          if (!nextItem || !nextItem.classList.contains("ref-item")) {
            alert("Нет следующего источника для объединения");
            return;
          }
          
          const currentText = refItem.querySelector(".ref-text")?.textContent.trim() || "";
          const nextText = nextItem.querySelector(".ref-text")?.textContent.trim() || "";
          
          if (!currentText || !nextText) {
            alert("Нельзя объединить пустые источники");
            return;
          }
          
          const mergedText = currentText + " " + nextText;
          const currentTextSpan = refItem.querySelector(".ref-text");
          if (currentTextSpan) {
            currentTextSpan.textContent = mergedText;
          }
          nextItem.remove();
          renumberReferences();
          updateMergeButtons();
          syncReferencesField();
        }
        
        function updateMergeButtons() {
          const refItems = document.querySelectorAll("#refsList .ref-item");
          refItems.forEach((item, index) => {
            const actions = item.querySelector(".ref-actions");
            if (!actions) return;
            
            const hasNext = index < refItems.length - 1;
            const existingMergeBtn = actions.querySelector(".ref-action-btn.merge");
            
            if (hasNext && !existingMergeBtn) {
              const deleteBtn = actions.querySelector(".ref-action-btn.delete");
              if (deleteBtn) {
                const mergeBtn = document.createElement("button");
                mergeBtn.className = "ref-action-btn merge";
                mergeBtn.onclick = () => mergeWithNext(mergeBtn);
                mergeBtn.title = "Объединить со следующим";
                mergeBtn.textContent = "⇅";
                actions.insertBefore(mergeBtn, deleteBtn);
              }
            } else if (!hasNext && existingMergeBtn) {
              existingMergeBtn.remove();
            }
          });
        }
        
        function deleteReference(btn) {
          const refItem = btn.closest(".ref-item");
          if (refItem && confirm("Удалить эту ссылку из списка?")) {
            refItem.remove();
            renumberReferences();
            updateMergeButtons();
          }
        }
        
        function renumberReferences() {
          const refItems = document.querySelectorAll("#refsList .ref-item");
          refItems.forEach((item, index) => {
            const numberSpan = item.querySelector(".ref-number");
            if (numberSpan) {
              numberSpan.textContent = (index + 1) + ".";
            }
          });
          updateMergeButtons();
        }

        function attachRefTextHandlers(refItem) {
          const refText = refItem.querySelector(".ref-text");
          if (!refText) return;
          refText.addEventListener("keydown", handleRefKeydown);
        }

        function handleRefKeydown(event) {
          if (event.key !== "Enter") return;
          event.preventDefault();
          const refText = event.currentTarget;
          splitReferenceAtCursor(refText);
        }

        function splitReferenceAtCursor(refText) {
          const refItem = refText.closest(".ref-item");
          if (!refItem) return;

          const fullText = refText.textContent || "";
          const caretOffset = getCaretOffset(refText);
          const left = fullText.slice(0, caretOffset).trim();
          const right = fullText.slice(caretOffset).trim();

          if (!left && !right) return;

          refText.textContent = left;

          const newItem = document.createElement("div");
          newItem.className = "ref-item";
          newItem.innerHTML = `
            <span class="ref-number"></span>
            <span class="ref-text" contenteditable="true" spellcheck="false">${escapeHtml(right)}</span>
            <div class="ref-actions">
              <button class="ref-action-btn merge" onclick="mergeWithNext(this)" title="Объединить со следующим">⇅</button>
              <button class="ref-action-btn delete" onclick="deleteReference(this)" title="Удалить">✕</button>
            </div>
          `;

          refItem.insertAdjacentElement("afterend", newItem);
          attachRefTextHandlers(newItem);
          renumberReferences();
          updateMergeButtons();
          syncReferencesField();

          const newText = newItem.querySelector(".ref-text");
          if (newText) {
            placeCaretAtStart(newText);
          }
        }

        function getCaretOffset(element) {
          const selection = window.getSelection();
          if (!selection || selection.rangeCount === 0) {
            return (element.textContent || "").length;
          }
          const range = selection.getRangeAt(0);
          if (!element.contains(range.startContainer)) {
            return (element.textContent || "").length;
          }
          const preRange = range.cloneRange();
          preRange.selectNodeContents(element);
          preRange.setEnd(range.startContainer, range.startOffset);
          return preRange.toString().length;
        }

        function placeCaretAtStart(element) {
          element.focus();
          const range = document.createRange();
          range.selectNodeContents(element);
          range.collapse(true);
          const selection = window.getSelection();
          if (!selection) return;
          selection.removeAllRanges();
          selection.addRange(range);
        }
        
        function saveEditedReferences() {
          if (!currentRefsFieldId) return;
          
          const field = document.getElementById(currentRefsFieldId);
          if (!field) return;
          
          const refItems = document.querySelectorAll("#refsList .ref-item");
          const refs = Array.from(refItems)
            .map(item => {
              const textSpan = item.querySelector(".ref-text");
              return textSpan ? textSpan.textContent.trim() : "";
            })
            .filter(ref => ref.length > 0);
          
          field.value = refs.join("\\n");
          field.dispatchEvent(new Event("input", { bubbles: true }));
          if (window.updateReferencesCount) {
            window.updateReferencesCount(currentRefsFieldId);
          }
          closeRefsModal();
          
          const notification = document.createElement("div");
          notification.style.cssText = "position:fixed;top:20px;right:20px;background:#4caf50;color:#fff;padding:15px 20px;border-radius:4px;box-shadow:0 4px 12px rgba(0,0,0,0.2);z-index:3000;font-size:14px;";
          notification.textContent = "Список литературы обновлен";
          document.body.appendChild(notification);
          setTimeout(() => {
            notification.remove();
          }, 2000);
        }
        
        function closeRefsModal() {
          const modal = document.getElementById("refsModal");
          const modalContent = document.getElementById("refsModalContent");
          const expandBtn = document.getElementById("refsModalExpandBtn");
          if (modal) {
            modal.classList.remove("active");
            // Сбрасываем размер при закрытии
            if (modalContent) {
              modalContent.classList.remove("expanded");
            }
            if (expandBtn) {
              expandBtn.classList.remove("expanded");
            }
          }
        }
        
        function toggleRefsModalSize() {
          const modalContent = document.getElementById("refsModalContent");
          const expandBtn = document.getElementById("refsModalExpandBtn");
          if (modalContent && expandBtn) {
            const isExpanded = modalContent.classList.contains("expanded");
            if (isExpanded) {
              modalContent.classList.remove("expanded");
              expandBtn.classList.remove("expanded");
              expandBtn.title = "Увеличить окно";
            } else {
              modalContent.classList.add("expanded");
              expandBtn.classList.add("expanded");
              expandBtn.title = "Уменьшить окно";
            }
          }
        }
        
        let currentAnnotationFieldId = null;

function annotationTextToHtml(text) {
  if (!text) return "";
  const escaped = escapeHtml(text);
  return escaped
    .replace(/&lt;(sup|sub)&gt;/gi, "<$1>")
    .replace(/&lt;\/(sup|sub)&gt;/gi, "</$1>")
    .replace(/&lt;br\s*\/?&gt;/gi, "<br>")
    .replace(/\n/g, "<br>");
}

function annotationHtmlToText(html) {
  const container = document.createElement("div");
  container.innerHTML = html || "";
  let output = "";

  const walk = (node) => {
    if (node.nodeType === Node.TEXT_NODE) {
      output += node.nodeValue;
      return;
    }
    if (node.nodeType !== Node.ELEMENT_NODE) {
      return;
    }

    const tag = node.tagName;
    const verticalAlign = node.style && node.style.verticalAlign;

    if (verticalAlign === "super") {
      output += "<sup>";
      node.childNodes.forEach(walk);
      output += "</sup>";
      return;
    }
    if (verticalAlign === "sub") {
      output += "<sub>";
      node.childNodes.forEach(walk);
      output += "</sub>";
      return;
    }

    if (tag === "BR") {
      output += "\\n";
      return;
    }
    if (tag === "DIV" || tag === "P") {
      if (output && !output.endsWith("\\n")) {
        output += "\\n";
      }
      node.childNodes.forEach(walk);
      if (!output.endsWith("\\n")) {
        output += "\\n";
      }
      return;
    }
    if (tag === "SUP") {
      output += "<sup>";
      node.childNodes.forEach(walk);
      output += "</sup>";
      return;
    }
    if (tag === "SUB") {
      output += "<sub>";
      node.childNodes.forEach(walk);
      output += "</sub>";
      return;
    }

    node.childNodes.forEach(walk);
  };

  container.childNodes.forEach(walk);
  return output.replace(/\n{3,}/g, "\n\n").trim();
}

function wrapAnnotationRange(range, tag) {
  const editor = document.getElementById("annotationModalEditor");
  if (!editor) return;
  if (!range || !editor.contains(range.commonAncestorContainer)) return;
  if (range.collapsed) return;

  const selection = window.getSelection();
  const wrapper = document.createElement(tag);

  const content = range.extractContents();
  wrapper.appendChild(content);
  range.insertNode(wrapper);

  const newRange = document.createRange();
  newRange.selectNodeContents(wrapper);
  if (selection) {
    selection.removeAllRanges();
    selection.addRange(newRange);
  }
}



let lastAnnotationSelection = null;
let lastAnnotationOffsets = null;

function getNodeTextLength(node) {
  if (!node) return 0;
  if (node.nodeType === Node.TEXT_NODE) {
    return node.nodeValue.length;
  }
  if (node.nodeType === Node.ELEMENT_NODE) {
    if (node.tagName === "BR") return 1;
    let total = 0;
    node.childNodes.forEach((child) => {
      total += getNodeTextLength(child);
    });
    return total;
  }
  return 0;
}

function computeOffset(editor, container, offset) {
  let total = 0;
  let found = false;

  const walk = (node) => {
    if (found) return;
    if (node === container) {
      if (node.nodeType === Node.TEXT_NODE) {
        total += offset;
      } else {
        for (let i = 0; i < offset; i += 1) {
          total += getNodeTextLength(node.childNodes[i]);
        }
      }
      found = true;
      return;
    }

    if (node.nodeType === Node.TEXT_NODE) {
      total += node.nodeValue.length;
      return;
    }
    if (node.nodeType === Node.ELEMENT_NODE) {
      if (node.tagName === "BR") {
        total += 1;
        return;
      }
      node.childNodes.forEach(walk);
    }
  };

  walk(editor);
  return found ? total : null;
}

function resolveOffset(editor, target) {
  let total = 0;
  let result = null;

  const walk = (node) => {
    if (result) return;
    if (node.nodeType === Node.TEXT_NODE) {
      const len = node.nodeValue.length;
      if (total + len >= target) {
        result = { node: node, offset: target - total };
        return;
      }
      total += len;
      return;
    }
    if (node.nodeType === Node.ELEMENT_NODE) {
      if (node.tagName === "BR") {
        if (total + 1 >= target) {
          const parent = node.parentNode || editor;
          const idx = Array.prototype.indexOf.call(parent.childNodes, node);
          result = { node: parent, offset: Math.max(0, idx) + 1 };
          return;
        }
        total += 1;
        return;
      }
      node.childNodes.forEach(walk);
    }
  };

  walk(editor);
  if (!result) {
    result = { node: editor, offset: editor.childNodes.length };
  }
  return result;
}

function saveAnnotationSelection() {
  const editor = document.getElementById("annotationModalEditor");
  if (!editor) return;
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) return;
  const range = selection.getRangeAt(0);
  if (!editor.contains(range.commonAncestorContainer)) return;

  const start = computeOffset(editor, range.startContainer, range.startOffset);
  const end = computeOffset(editor, range.endContainer, range.endOffset);
  if (start === null || end === null) return;

  lastAnnotationOffsets = { start: start, end: end };
  lastAnnotationSelection = range.cloneRange();
}

function restoreAnnotationSelection() {
  const editor = document.getElementById("annotationModalEditor");
  if (!editor) return;
  if (!lastAnnotationOffsets) return;

  const selection = window.getSelection();
  if (!selection) return;
  const startPos = resolveOffset(editor, lastAnnotationOffsets.start);
  const endPos = resolveOffset(editor, lastAnnotationOffsets.end);
  const range = document.createRange();
  range.setStart(startPos.node, startPos.offset);
  range.setEnd(endPos.node, endPos.offset);
  selection.removeAllRanges();
  selection.addRange(range);
  lastAnnotationSelection = range.cloneRange();
}
function getAnnotationRangeFromOffsets() {
  const editor = document.getElementById("annotationModalEditor");
  if (!editor) return null;
  if (!lastAnnotationOffsets) return null;
  const startPos = resolveOffset(editor, lastAnnotationOffsets.start);
  const endPos = resolveOffset(editor, lastAnnotationOffsets.end);
  if (!startPos || !endPos) return null;
  const range = document.createRange();
  range.setStart(startPos.node, startPos.offset);
  range.setEnd(endPos.node, endPos.offset);
  return range;
}



function unwrapTag(node) {
  if (!node || !node.parentNode) return;
  const parent = node.parentNode;
  const first = node.firstChild;
  const last = node.lastChild;
  while (node.firstChild) {
    parent.insertBefore(node.firstChild, node);
  }
  parent.removeChild(node);

  const selection = window.getSelection();
  if (!selection) return;
  const range = document.createRange();
  if (first && last) {
    range.setStartBefore(first);
    range.setEndAfter(last);
  } else {
    range.selectNodeContents(parent);
  }
  selection.removeAllRanges();
  selection.addRange(range);
}

function unwrapTagInPlace(node) {
  if (!node || !node.parentNode) return;
  const parent = node.parentNode;
  while (node.firstChild) {
    parent.insertBefore(node.firstChild, node);
  }
  parent.removeChild(node);
}


function unwrapTagInPlace(node) {
  if (!node || !node.parentNode) return;
  const parent = node.parentNode;
  while (node.firstChild) {
    parent.insertBefore(node.firstChild, node);
  }
  parent.removeChild(node);
}

function findAncestorTag(node, tag, editor) {
  let current = node;
  const upper = tag.toUpperCase();
  while (current && current !== editor) {
    if (current.nodeType === Node.ELEMENT_NODE && current.tagName === upper) {
      return current;
    }
    current = current.parentNode;
  }
  return null;
}
function applyAnnotationFormat(action, rangeOverride) {
  const editor = document.getElementById("annotationModalEditor");
  if (!editor) return;

  let range = null;
  if (rangeOverride) {
    const node = rangeOverride.commonAncestorContainer;
    if (!rangeOverride.collapsed && node && editor.contains(node)) {
      range = rangeOverride.cloneRange();
    }
  }
  if (!range) {
    range = getAnnotationRangeFromOffsets();
  }
  if (!range) {
    restoreAnnotationSelection();
    const selection = window.getSelection();
    if (selection && selection.rangeCount > 0) {
      const candidate = selection.getRangeAt(0);
      if (!candidate.collapsed && editor.contains(candidate.commonAncestorContainer)) {
        range = candidate.cloneRange();
      }
    }
  }
  if (!range) return;

  const tag = action === "sup" ? "sup" : "sub";
  const startTag = findAncestorTag(range.startContainer, tag, editor);
  const endTag = findAncestorTag(range.endContainer, tag, editor);
  if (startTag && startTag === endTag) {
    saveAnnotationSelection();
    unwrapTagInPlace(startTag);
    restoreAnnotationSelection();
    return;
  }

  const candidates = Array.from(editor.querySelectorAll(tag));
  const toUnwrap = candidates.filter((node) => {
    try {
      return range.intersectsNode(node);
    } catch (e) {
      return node.contains(range.startContainer) || node.contains(range.endContainer);
    }
  });

  if (toUnwrap.length) {
    saveAnnotationSelection();
    toUnwrap.forEach(unwrapTagInPlace);
    restoreAnnotationSelection();
    return;
  }

  wrapAnnotationRange(range, tag);
  saveAnnotationSelection();
}

function setAnnotationCodeView(enabled) {
  const editor = document.getElementById("annotationModalEditor");
  const textarea = document.getElementById("annotationModalTextarea");
  if (!editor || !textarea) return;
  annotationCodeViewEnabled = enabled;
  annotationPreviewEnabled = false;
  editor.contentEditable = "true";
  editor.classList.remove("preview");
  if (enabled) {
    textarea.value = editor.innerHTML;
    textarea.style.display = "block";
    editor.style.display = "none";
  } else {
    editor.innerHTML = textarea.value;
    textarea.style.display = "none";
    editor.style.display = "block";
  }
  updateAnnotationStats();
  initAnnotationSymbolsPanel();
}

function toggleAnnotationPreview() {
  const editor = document.getElementById("annotationModalEditor");
  if (!editor) return;
  annotationPreviewEnabled = !annotationPreviewEnabled;
  editor.contentEditable = annotationPreviewEnabled ? "false" : "true";
  editor.classList.toggle("preview", annotationPreviewEnabled);
}

function getAnnotationPlainText() {
  const editor = document.getElementById("annotationModalEditor");
  const textarea = document.getElementById("annotationModalTextarea");
  if (annotationCodeViewEnabled && textarea) {
    return annotationHtmlToText(textarea.value || "");
  }
  if (editor) {
    return annotationHtmlToText(editor.innerHTML || "");
  }
  return "";
}

function updateAnnotationStats() {
  const countEl = document.getElementById("annotationWordCount");
  const langEl = document.getElementById("annotationLangIndicator");
  const modal = document.getElementById("annotationModal");
  const fieldId = modal?.dataset?.fieldId || currentAnnotationFieldId;
  if (langEl) {
    langEl.textContent = fieldId === "annotation_en" ? "EN" : "RU";
  }
  const text = getAnnotationPlainText();
  const words = text.trim() ? text.trim().split(/\s+/).filter(Boolean) : [];
  if (countEl) {
    countEl.textContent = `СЛОВ: ${words.length}`;
  }
}

function getSelectionText() {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) return "";
  return selection.toString();
}

function insertAnnotationHtml(html) {
  document.execCommand("insertHTML", false, html);
}

function applyAnnotationCommand(action, value) {
  if (!action) return;
  if (action === "annotation-sup") {
    applyAnnotationFormat("sup");
    return;
  }
  if (action === "annotation-sub") {
    applyAnnotationFormat("sub");
    return;
  }
  const editor = document.getElementById("annotationModalEditor");
  if (editor && editor.style.display !== "none") {
    editor.focus();
  }
  switch (action) {
    case "bold":
      document.execCommand("bold");
      break;
    case "italic":
      document.execCommand("italic");
      break;
    case "strike":
      document.execCommand("strikeThrough");
      break;
    case "align-left":
      document.execCommand("justifyLeft");
      break;
    case "align-center":
      document.execCommand("justifyCenter");
      break;
    case "align-right":
      document.execCommand("justifyRight");
      break;
    case "align-justify":
      document.execCommand("justifyFull");
      break;
    case "unordered-list":
      document.execCommand("insertUnorderedList");
      break;
    case "ordered-list":
      document.execCommand("insertOrderedList");
      break;
    case "text-color":
      document.execCommand("foreColor", false, value);
      break;
    case "highlight-color":
      document.execCommand("hiliteColor", false, value);
      break;
    case "format-block":
      if (value) document.execCommand("formatBlock", false, value);
      break;
    case "font-name":
      if (value) document.execCommand("fontName", false, value);
      break;
    case "font-size":
      if (value) document.execCommand("fontSize", false, value);
      break;
    case "link": {
      const url = prompt("Введите ссылку:", "https://");
      if (!url) break;
      const selected = getSelectionText();
      if (selected) {
        document.execCommand("createLink", false, url);
      } else {
        insertAnnotationHtml(`<a href="${escapeHtml(url)}" target="_blank" rel="noopener">${escapeHtml(url)}</a>`);
      }
      break;
    }
    case "bookmark": {
      const name = prompt("Название закладки:");
      if (!name) break;
      insertAnnotationHtml(`<span class="annotation-bookmark">🔖 ${escapeHtml(name)}</span>`);
      break;
    }
    case "insert-table": {
      const rows = parseInt(prompt("Количество строк:", "2"), 10);
      const cols = parseInt(prompt("Количество столбцов:", "2"), 10);
      if (!rows || !cols) break;
      let html = '<table class="annotation-table">';
      for (let r = 0; r < rows; r += 1) {
        html += "<tr>";
        for (let c = 0; c < cols; c += 1) {
          html += "<td>&nbsp;</td>";
        }
        html += "</tr>";
      }
      html += "</table>";
      insertAnnotationHtml(html);
      break;
    }
    case "insert-image": {
      const url = prompt("Ссылка на изображение:");
      if (!url) break;
      insertAnnotationHtml(`<img src="${escapeHtml(url)}" alt="image" style="max-width:100%;height:auto;">`);
      break;
    }
    case "insert-video": {
      const url = prompt("Ссылка на видео (iframe/url):");
      if (!url) break;
      insertAnnotationHtml(`<iframe src="${escapeHtml(url)}" frameborder="0" allowfullscreen style="width:100%;height:320px;"></iframe>`);
      break;
    }
    case "insert-code": {
      const selected = getSelectionText() || "код";
      const escaped = escapeHtml(selected);
      insertAnnotationHtml(`<pre class="annotation-code-block"><code>${escaped}</code></pre>`);
      break;
    }
    case "toggle-symbols-panel":
      toggleAnnotationSymbolsPanel();
      break;
    case "insert-latex": {
      const latex = prompt("LaTeX формула:");
      if (!latex) break;
      document.execCommand("insertText", false, `\\(${latex}\\)`);
      break;
    }
    case "insert-formula": {
      const formula = prompt("Формула:");
      if (!formula) break;
      document.execCommand("insertText", false, `∑ ${formula}`);
      break;
    }
    case "toggle-preview":
      toggleAnnotationPreview();
      break;
    case "toggle-fullscreen":
      toggleAnnotationModalSize();
      break;
    case "toggle-code-view":
      setAnnotationCodeView(!annotationCodeViewEnabled);
      break;
    default:
      break;
  }
  updateAnnotationStats();
}

let annotationCodeViewEnabled = false;
let annotationPreviewEnabled = false;

function setAnnotationCodeView(enabled) {
  const editor = document.getElementById("annotationModalEditor");
  const textarea = document.getElementById("annotationModalTextarea");
  if (!editor || !textarea) return;
  annotationCodeViewEnabled = enabled;
  annotationPreviewEnabled = false;
  editor.contentEditable = "true";
  editor.classList.remove("preview");
  if (enabled) {
    textarea.value = editor.innerHTML;
    textarea.style.display = "block";
    editor.style.display = "none";
  } else {
    editor.innerHTML = textarea.value;
    textarea.style.display = "none";
    editor.style.display = "block";
  }
  updateAnnotationStats();
}

function toggleAnnotationPreview() {
  const editor = document.getElementById("annotationModalEditor");
  if (!editor) return;
  annotationPreviewEnabled = !annotationPreviewEnabled;
  editor.contentEditable = annotationPreviewEnabled ? "false" : "true";
  editor.classList.toggle("preview", annotationPreviewEnabled);
}

function getAnnotationPlainText() {
  const editor = document.getElementById("annotationModalEditor");
  const textarea = document.getElementById("annotationModalTextarea");
  if (annotationCodeViewEnabled && textarea) {
    return annotationHtmlToText(textarea.value || "");
  }
  if (editor) {
    return annotationHtmlToText(editor.innerHTML || "");
  }
  return "";
}

function updateAnnotationStats() {
  const countEl = document.getElementById("annotationWordCount");
  const langEl = document.getElementById("annotationLangIndicator");
  const modal = document.getElementById("annotationModal");
  const fieldId = modal?.dataset?.fieldId || currentAnnotationFieldId;
  if (langEl) {
    langEl.textContent = fieldId === "annotation_en" ? "EN" : "RU";
  }
  const text = getAnnotationPlainText();
  const words = text.trim() ? text.trim().split(/\s+/).filter(Boolean) : [];
  if (countEl) {
    countEl.textContent = `СЛОВ: ${words.length}`;
  }
}

function getSelectionText() {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) return "";
  return selection.toString();
}

function insertAnnotationHtml(html) {
  document.execCommand("insertHTML", false, html);
}

function applyAnnotationCommand(action, value) {
  if (!action) return;
  if (action === "annotation-sup") {
    applyAnnotationFormat("sup");
    return;
  }
  if (action === "annotation-sub") {
    applyAnnotationFormat("sub");
    return;
  }
  const editor = document.getElementById("annotationModalEditor");
  if (editor && editor.style.display !== "none") {
    editor.focus();
  }
  switch (action) {
    case "bold":
      document.execCommand("bold");
      break;
    case "italic":
      document.execCommand("italic");
      break;
    case "strike":
      document.execCommand("strikeThrough");
      break;
    case "align-left":
      document.execCommand("justifyLeft");
      break;
    case "align-center":
      document.execCommand("justifyCenter");
      break;
    case "align-right":
      document.execCommand("justifyRight");
      break;
    case "align-justify":
      document.execCommand("justifyFull");
      break;
    case "unordered-list":
      document.execCommand("insertUnorderedList");
      break;
    case "ordered-list":
      document.execCommand("insertOrderedList");
      break;
    case "text-color":
      document.execCommand("foreColor", false, value);
      break;
    case "highlight-color":
      document.execCommand("hiliteColor", false, value);
      break;
    case "format-block":
      if (value) document.execCommand("formatBlock", false, value);
      break;
    case "font-name":
      if (value) document.execCommand("fontName", false, value);
      break;
    case "font-size":
      if (value) document.execCommand("fontSize", false, value);
      break;
    case "link": {
      const url = prompt("Введите ссылку:", "https://");
      if (!url) break;
      const selected = getSelectionText();
      if (selected) {
        document.execCommand("createLink", false, url);
      } else {
        insertAnnotationHtml(`<a href="${escapeHtml(url)}" target="_blank" rel="noopener">${escapeHtml(url)}</a>`);
      }
      break;
    }
    case "bookmark": {
      const name = prompt("Название закладки:");
      if (!name) break;
      insertAnnotationHtml(`<span class="annotation-bookmark">🔖 ${escapeHtml(name)}</span>`);
      break;
    }
    case "insert-table": {
      const rows = parseInt(prompt("Количество строк:", "2"), 10);
      const cols = parseInt(prompt("Количество столбцов:", "2"), 10);
      if (!rows || !cols) break;
      let html = '<table class="annotation-table">';
      for (let r = 0; r < rows; r += 1) {
        html += "<tr>";
        for (let c = 0; c < cols; c += 1) {
          html += "<td>&nbsp;</td>";
        }
        html += "</tr>";
      }
      html += "</table>";
      insertAnnotationHtml(html);
      break;
    }
    case "insert-image": {
      const url = prompt("Ссылка на изображение:");
      if (!url) break;
      insertAnnotationHtml(`<img src="${escapeHtml(url)}" alt="image" style="max-width:100%;height:auto;">`);
      break;
    }
    case "insert-video": {
      const url = prompt("Ссылка на видео (iframe/url):");
      if (!url) break;
      insertAnnotationHtml(`<iframe src="${escapeHtml(url)}" frameborder="0" allowfullscreen style="width:100%;height:320px;"></iframe>`);
      break;
    }
    case "insert-code": {
      const selected = getSelectionText() || "код";
      const escaped = escapeHtml(selected);
      insertAnnotationHtml(`<pre class="annotation-code-block"><code>${escaped}</code></pre>`);
      break;
    }
    case "toggle-symbols-panel":
      toggleAnnotationSymbolsPanel();
      break;
    case "insert-latex": {
      const latex = prompt("LaTeX формула:");
      if (!latex) break;
      document.execCommand("insertText", false, `\\(${latex}\\)`);
      break;
    }
    case "insert-formula": {
      const formula = prompt("Формула:");
      if (!formula) break;
      document.execCommand("insertText", false, `∑ ${formula}`);
      break;
    }
    case "toggle-preview":
      toggleAnnotationPreview();
      break;
    case "toggle-fullscreen":
      toggleAnnotationModalSize();
      break;
    case "toggle-code-view":
      setAnnotationCodeView(!annotationCodeViewEnabled);
      break;
    default:
      break;
  }
  updateAnnotationStats();
}

function setAnnotationCodeView(enabled) {
  const editor = document.getElementById("annotationModalEditor");
  const textarea = document.getElementById("annotationModalTextarea");
  if (!editor || !textarea) return;
  annotationCodeViewEnabled = enabled;
  annotationPreviewEnabled = false;
  editor.contentEditable = "true";
  editor.classList.remove("preview");
  if (enabled) {
    textarea.value = editor.innerHTML;
    textarea.style.display = "block";
    editor.style.display = "none";
  } else {
    editor.innerHTML = textarea.value;
    textarea.style.display = "none";
    editor.style.display = "block";
  }
  updateAnnotationStats();
}

function toggleAnnotationPreview() {
  const editor = document.getElementById("annotationModalEditor");
  if (!editor) return;
  annotationPreviewEnabled = !annotationPreviewEnabled;
  editor.contentEditable = annotationPreviewEnabled ? "false" : "true";
  editor.classList.toggle("preview", annotationPreviewEnabled);
}

function getAnnotationPlainText() {
  const editor = document.getElementById("annotationModalEditor");
  const textarea = document.getElementById("annotationModalTextarea");
  if (annotationCodeViewEnabled && textarea) {
    return annotationHtmlToText(textarea.value || "");
  }
  if (editor) {
    return annotationHtmlToText(editor.innerHTML || "");
  }
  return "";
}

function updateAnnotationStats() {
  const countEl = document.getElementById("annotationWordCount");
  const langEl = document.getElementById("annotationLangIndicator");
  const modal = document.getElementById("annotationModal");
  const fieldId = modal?.dataset?.fieldId || currentAnnotationFieldId;
  if (langEl) {
    langEl.textContent = fieldId === "annotation_en" ? "EN" : "RU";
  }
  const text = getAnnotationPlainText();
  const words = text.trim() ? text.trim().split(/\s+/).filter(Boolean) : [];
  if (countEl) {
    countEl.textContent = `СЛОВ: ${words.length}`;
  }
}

function getSelectionText() {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) return "";
  return selection.toString();
}

function insertAnnotationHtml(html) {
  document.execCommand("insertHTML", false, html);
}

function applyAnnotationCommand(action, value) {
  if (!action) return;
  if (action === "annotation-sup") {
    applyAnnotationFormat("sup");
    return;
  }
  if (action === "annotation-sub") {
    applyAnnotationFormat("sub");
    return;
  }
  const editor = document.getElementById("annotationModalEditor");
  if (editor && editor.style.display !== "none") {
    editor.focus();
  }
  switch (action) {
    case "bold":
      document.execCommand("bold");
      break;
    case "italic":
      document.execCommand("italic");
      break;
    case "strike":
      document.execCommand("strikeThrough");
      break;
    case "align-left":
      document.execCommand("justifyLeft");
      break;
    case "align-center":
      document.execCommand("justifyCenter");
      break;
    case "align-right":
      document.execCommand("justifyRight");
      break;
    case "align-justify":
      document.execCommand("justifyFull");
      break;
    case "unordered-list":
      document.execCommand("insertUnorderedList");
      break;
    case "ordered-list":
      document.execCommand("insertOrderedList");
      break;
    case "text-color":
      document.execCommand("foreColor", false, value);
      break;
    case "highlight-color":
      document.execCommand("hiliteColor", false, value);
      break;
    case "format-block":
      if (value) document.execCommand("formatBlock", false, value);
      break;
    case "font-name":
      if (value) document.execCommand("fontName", false, value);
      break;
    case "font-size":
      if (value) document.execCommand("fontSize", false, value);
      break;
    case "link": {
      const url = prompt("Введите ссылку:", "https://");
      if (!url) break;
      const selected = getSelectionText();
      if (selected) {
        document.execCommand("createLink", false, url);
      } else {
        insertAnnotationHtml(`<a href="${escapeHtml(url)}" target="_blank" rel="noopener">${escapeHtml(url)}</a>`);
      }
      break;
    }
    case "bookmark": {
      const name = prompt("Название закладки:");
      if (!name) break;
      insertAnnotationHtml(`<span class="annotation-bookmark">🔖 ${escapeHtml(name)}</span>`);
      break;
    }
    case "insert-table": {
      const rows = parseInt(prompt("Количество строк:", "2"), 10);
      const cols = parseInt(prompt("Количество столбцов:", "2"), 10);
      if (!rows || !cols) break;
      let html = '<table class="annotation-table">';
      for (let r = 0; r < rows; r += 1) {
        html += "<tr>";
        for (let c = 0; c < cols; c += 1) {
          html += "<td>&nbsp;</td>";
        }
        html += "</tr>";
      }
      html += "</table>";
      insertAnnotationHtml(html);
      break;
    }
    case "insert-image": {
      const url = prompt("Ссылка на изображение:");
      if (!url) break;
      insertAnnotationHtml(`<img src="${escapeHtml(url)}" alt="image" style="max-width:100%;height:auto;">`);
      break;
    }
    case "insert-video": {
      const url = prompt("Ссылка на видео (iframe/url):");
      if (!url) break;
      insertAnnotationHtml(`<iframe src="${escapeHtml(url)}" frameborder="0" allowfullscreen style="width:100%;height:320px;"></iframe>`);
      break;
    }
    case "insert-code": {
      const selected = getSelectionText() || "код";
      const escaped = escapeHtml(selected);
      insertAnnotationHtml(`<pre class="annotation-code-block"><code>${escaped}</code></pre>`);
      break;
    }
    case "toggle-symbols-panel":
      toggleAnnotationSymbolsPanel();
      break;
    case "insert-latex": {
      const latex = prompt("LaTeX формула:");
      if (!latex) break;
      document.execCommand("insertText", false, `\\(${latex}\\)`);
      break;
    }
    case "insert-formula": {
      const formula = prompt("Формула:");
      if (!formula) break;
      document.execCommand("insertText", false, `∑ ${formula}`);
      break;
    }
    case "toggle-preview":
      toggleAnnotationPreview();
      break;
    case "toggle-fullscreen":
      toggleAnnotationModalSize();
      break;
    case "toggle-code-view":
      setAnnotationCodeView(!annotationCodeViewEnabled);
      break;
    default:
      break;
  }
  updateAnnotationStats();
}









if (!window.__annotationSelectionHandlerAdded) {
  document.addEventListener("selectionchange", saveAnnotationSelection);
  window.__annotationSelectionHandlerAdded = true;
}

if (!window.__annotationSelectionSyncAdded) {
  document.addEventListener("mouseup", saveAnnotationSelection, true);
  document.addEventListener("keyup", saveAnnotationSelection, true);
  document.addEventListener("touchend", saveAnnotationSelection, true);
  window.__annotationSelectionSyncAdded = true;
}

if (!window.__annotationEditorMouseDownAdded) {
  const handler = (event) => {
    const button = event.target.closest(".annotation-editor-btn");
    if (!button) return;
    event.preventDefault();
    event.stopPropagation();
    const action = button.getAttribute("data-action");
    applyAnnotationCommand(action);
  };
  document.addEventListener("pointerdown", handler, true);
  document.addEventListener("mousedown", handler, true);
  window.__annotationEditorMouseDownAdded = true;
}
if (!window.__annotationEditorHandlersAdded) {
  document.addEventListener("change", (event) => {
    const select = event.target.closest(".annotation-select");
    if (select) {
      applyAnnotationCommand(select.getAttribute("data-action"), select.value);
      return;
    }
    const color = event.target.closest(".annotation-color-input");
    if (color) {
      applyAnnotationCommand(color.getAttribute("data-action"), color.value);
    }
  });
  document.addEventListener("input", (event) => {
    const editor = event.target.closest("#annotationModalEditor");
    const textarea = event.target.closest("#annotationModalTextarea");
    if (editor || textarea) {
      updateAnnotationStats();
    }
  });
  window.__annotationEditorHandlersAdded = true;
}

function ensureAnnotationSymbolsData() {
  if (window.__annotationSymbolsData) return;
  window.__annotationSymbolsData = [
    { id: "alpha", char: "α", name_ru: "альфа", name_en: "alpha", codepoint: "U+03B1", category: "greek", aliases: ["alpha", "альфа"], latex: "\\alpha" },
    { id: "beta", char: "β", name_ru: "бета", name_en: "beta", codepoint: "U+03B2", category: "greek", aliases: ["beta", "бета"], latex: "\\beta" },
    { id: "gamma", char: "γ", name_ru: "гамма", name_en: "gamma", codepoint: "U+03B3", category: "greek", aliases: ["gamma", "гамма"], latex: "\\gamma" },
    { id: "delta", char: "δ", name_ru: "дельта", name_en: "delta", codepoint: "U+03B4", category: "greek", aliases: ["delta", "дельта"], latex: "\\delta" },
    { id: "epsilon", char: "ε", name_ru: "эпсилон", name_en: "epsilon", codepoint: "U+03B5", category: "greek", aliases: ["epsilon", "эпсилон"], latex: "\\epsilon" },
    { id: "theta", char: "θ", name_ru: "тета", name_en: "theta", codepoint: "U+03B8", category: "greek", aliases: ["theta", "тета"], latex: "\\theta" },
    { id: "lambda", char: "λ", name_ru: "лямбда", name_en: "lambda", codepoint: "U+03BB", category: "greek", aliases: ["lambda", "лямбда"], latex: "\\lambda" },
    { id: "mu", char: "μ", name_ru: "мю", name_en: "mu", codepoint: "U+03BC", category: "greek", aliases: ["mu", "micro", "мю"], latex: "\\mu" },
    { id: "pi", char: "π", name_ru: "пи", name_en: "pi", codepoint: "U+03C0", category: "greek", aliases: ["pi", "пи"], latex: "\\pi" },
    { id: "sigma", char: "σ", name_ru: "сигма", name_en: "sigma", codepoint: "U+03C3", category: "greek", aliases: ["sigma", "сигма"], latex: "\\sigma" },
    { id: "phi", char: "φ", name_ru: "фи", name_en: "phi", codepoint: "U+03C6", category: "greek", aliases: ["phi", "фи"], latex: "\\phi" },
    { id: "psi", char: "ψ", name_ru: "пси", name_en: "psi", codepoint: "U+03C8", category: "greek", aliases: ["psi", "пси"], latex: "\\psi" },
    { id: "omega", char: "ω", name_ru: "омега", name_en: "omega", codepoint: "U+03C9", category: "greek", aliases: ["omega", "омега"], latex: "\\omega" },
    { id: "Omega", char: "Ω", name_ru: "омега (верхн.)", name_en: "Omega", codepoint: "U+03A9", category: "greek", aliases: ["omega", "омега"], latex: "\\Omega" },
    { id: "plusminus", char: "±", name_ru: "плюс-минус", name_en: "plus-minus", codepoint: "U+00B1", category: "math", aliases: ["plusminus", "+-"], latex: "\\pm" },
    { id: "times", char: "×", name_ru: "умножить", name_en: "times", codepoint: "U+00D7", category: "math", aliases: ["times", "multiply"], latex: "\\times" },
    { id: "divide", char: "÷", name_ru: "деление", name_en: "divide", codepoint: "U+00F7", category: "math", aliases: ["divide"], latex: "\\div" },
    { id: "leq", char: "≤", name_ru: "меньше либо равно", name_en: "leq", codepoint: "U+2264", category: "math", aliases: ["leq", "<="], latex: "\\leq" },
    { id: "geq", char: "≥", name_ru: "больше либо равно", name_en: "geq", codepoint: "U+2265", category: "math", aliases: ["geq", ">="], latex: "\\geq" },
    { id: "neq", char: "≠", name_ru: "не равно", name_en: "not equal", codepoint: "U+2260", category: "math", aliases: ["neq", "!="], latex: "\\neq" },
    { id: "approx", char: "≈", name_ru: "примерно", name_en: "approx", codepoint: "U+2248", category: "math", aliases: ["approx"], latex: "\\approx" },
    { id: "infty", char: "∞", name_ru: "бесконечность", name_en: "infinity", codepoint: "U+221E", category: "math", aliases: ["infty", "infinity"], latex: "\\infty" },
    { id: "sum", char: "∑", name_ru: "сумма", name_en: "sum", codepoint: "U+2211", category: "math", aliases: ["sum"], latex: "\\sum" },
    { id: "prod", char: "∏", name_ru: "произведение", name_en: "prod", codepoint: "U+220F", category: "math", aliases: ["prod"], latex: "\\prod" },
    { id: "sqrt", char: "√", name_ru: "корень", name_en: "sqrt", codepoint: "U+221A", category: "math", aliases: ["sqrt"], latex: "\\sqrt{}" },
    { id: "int", char: "∫", name_ru: "интеграл", name_en: "integral", codepoint: "U+222B", category: "math", aliases: ["integral"], latex: "\\int" },
    { id: "partial", char: "∂", name_ru: "частная производная", name_en: "partial", codepoint: "U+2202", category: "math", aliases: ["partial"], latex: "\\partial" },
    { id: "nabla", char: "∇", name_ru: "набла", name_en: "nabla", codepoint: "U+2207", category: "math", aliases: ["nabla"], latex: "\\nabla" },
    { id: "arrow_left", char: "←", name_ru: "стрелка влево", name_en: "left arrow", codepoint: "U+2190", category: "arrows", aliases: ["left", "arrow"], latex: "\\leftarrow" },
    { id: "arrow_right", char: "→", name_ru: "стрелка вправо", name_en: "right arrow", codepoint: "U+2192", category: "arrows", aliases: ["right", "arrow"], latex: "\\rightarrow" },
    { id: "arrow_up", char: "↑", name_ru: "стрелка вверх", name_en: "up arrow", codepoint: "U+2191", category: "arrows", aliases: ["up", "arrow"], latex: "\\uparrow" },
    { id: "arrow_down", char: "↓", name_ru: "стрелка вниз", name_en: "down arrow", codepoint: "U+2193", category: "arrows", aliases: ["down", "arrow"], latex: "\\downarrow" },
    { id: "arrow_lr", char: "↔", name_ru: "двунаправленная", name_en: "leftright arrow", codepoint: "U+2194", category: "arrows", aliases: ["leftright", "arrow"], latex: "\\leftrightarrow" },
    { id: "sup1", char: "¹", name_ru: "верхний 1", name_en: "superscript 1", codepoint: "U+00B9", category: "indices", aliases: ["superscript", "1"] },
    { id: "sup2", char: "²", name_ru: "верхний 2", name_en: "superscript 2", codepoint: "U+00B2", category: "indices", aliases: ["superscript", "2"] },
    { id: "sup3", char: "³", name_ru: "верхний 3", name_en: "superscript 3", codepoint: "U+00B3", category: "indices", aliases: ["superscript", "3"] },
    { id: "sub1", char: "₁", name_ru: "нижний 1", name_en: "subscript 1", codepoint: "U+2081", category: "indices", aliases: ["subscript", "1"] },
    { id: "sub2", char: "₂", name_ru: "нижний 2", name_en: "subscript 2", codepoint: "U+2082", category: "indices", aliases: ["subscript", "2"] },
    { id: "sub3", char: "₃", name_ru: "нижний 3", name_en: "subscript 3", codepoint: "U+2083", category: "indices", aliases: ["subscript", "3"] },
    { id: "degree", char: "°", name_ru: "градус", name_en: "degree", codepoint: "U+00B0", category: "units", aliases: ["degree"], latex: "^\\circ" },
    { id: "permil", char: "‰", name_ru: "промилле", name_en: "per mille", codepoint: "U+2030", category: "units", aliases: ["permil"], latex: "\\permil" },
    { id: "angstrom", char: "Å", name_ru: "ангстрем", name_en: "angstrom", codepoint: "U+00C5", category: "units", aliases: ["angstrom"], latex: "\\AA" },
    { id: "celsius", char: "℃", name_ru: "цельсий", name_en: "celsius", codepoint: "U+2103", category: "units", aliases: ["celsius"] },
    { id: "euro", char: "€", name_ru: "евро", name_en: "euro", codepoint: "U+20AC", category: "currency", aliases: ["euro"] },
    { id: "ruble", char: "₽", name_ru: "рубль", name_en: "ruble", codepoint: "U+20BD", category: "currency", aliases: ["ruble", "рубль"] },
    { id: "pound", char: "£", name_ru: "фунт", name_en: "pound", codepoint: "U+00A3", category: "currency", aliases: ["pound"] },
    { id: "yen", char: "¥", name_ru: "иена", name_en: "yen", codepoint: "U+00A5", category: "currency", aliases: ["yen"] },
    { id: "emdash", char: "—", name_ru: "длинное тире", name_en: "em dash", codepoint: "U+2014", category: "typography", aliases: ["emdash"] },
    { id: "endash", char: "–", name_ru: "короткое тире", name_en: "en dash", codepoint: "U+2013", category: "typography", aliases: ["endash"] },
    { id: "laquo", char: "«", name_ru: "кавычки елочки", name_en: "guillemets", codepoint: "U+00AB", category: "typography", aliases: ["quotes"] },
    { id: "raquo", char: "»", name_ru: "кавычки елочки", name_en: "guillemets", codepoint: "U+00BB", category: "typography", aliases: ["quotes"] },
    { id: "ellipsis", char: "…", name_ru: "многоточие", name_en: "ellipsis", codepoint: "U+2026", category: "typography", aliases: ["ellipsis"] },
    { id: "sect", char: "§", name_ru: "параграф", name_en: "section", codepoint: "U+00A7", category: "typography", aliases: ["section"] },
    { id: "para", char: "¶", name_ru: "абзац", name_en: "paragraph", codepoint: "U+00B6", category: "typography", aliases: ["paragraph"] },
    { id: "acute_e", char: "é", name_ru: "е с акутом", name_en: "e acute", codepoint: "U+00E9", category: "latin", aliases: ["e", "acute"] },
    { id: "umlaut_u", char: "ü", name_ru: "у с умляутом", name_en: "u umlaut", codepoint: "U+00FC", category: "latin", aliases: ["u", "umlaut"] },
    { id: "ring_a", char: "å", name_ru: "а с кружком", name_en: "a ring", codepoint: "U+00E5", category: "latin", aliases: ["a", "ring"] }
  ];
}

function getAnnotationSymbolsStorage(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch (e) {
    return fallback;
  }
}

function setAnnotationSymbolsStorage(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (e) {}
}

function getAnnotationSymbolsElements() {
  return {
    panel: document.getElementById("annotationSymbolsPanel"),
    search: document.getElementById("annotationSymbolsSearch"),
    category: document.getElementById("annotationSymbolsCategory"),
    grid: document.getElementById("annotationSymbolsGrid"),
    recent: document.getElementById("annotationSymbolsRecent"),
    favorites: document.getElementById("annotationSymbolsFavorites"),
    latexToggle: document.getElementById("annotationSymbolsLatex"),
    autoCloseToggle: document.getElementById("annotationSymbolsAutoClose")
  };
}

function renderAnnotationSymbolsPanel() {
  ensureAnnotationSymbolsData();
  const { search, category, grid } = getAnnotationSymbolsElements();
  if (!search || !category || !grid) return;
  const query = (search.value || "").trim().toLowerCase();
  const selectedCategory = category.value || "all";
  const favorites = new Set(getAnnotationSymbolsStorage("annotation_symbols_favorites", []));
  const symbols = (window.__annotationSymbolsData || []).filter((item) => {
    if (selectedCategory !== "all" && item.category !== selectedCategory) return false;
    if (!query) return true;
    const hay = [
      item.char,
      item.name_ru,
      item.name_en,
      item.codepoint,
      item.category,
      ...(item.aliases || []),
      item.latex || ""
    ].join(" ").toLowerCase();
    return hay.includes(query);
  });
  grid.innerHTML = "";
  symbols.forEach((item, index) => {
    const cell = document.createElement("div");
    cell.className = "annotation-symbol-cell";
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "annotation-symbol-btn";
    btn.dataset.symbolId = item.id;
    btn.dataset.index = String(index);
    btn.textContent = item.char;
    btn.title = `${item.name_ru} (${item.codepoint})`;
    btn.addEventListener("click", () => insertAnnotationSymbol(item));
    const fav = document.createElement("button");
    fav.type = "button";
    fav.className = "annotation-symbol-fav" + (favorites.has(item.id) ? " active" : "");
    fav.textContent = favorites.has(item.id) ? "★" : "☆";
    fav.title = "В избранное";
    fav.tabIndex = -1;
    fav.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      toggleAnnotationSymbolFavorite(item.id);
    });
    cell.appendChild(btn);
    cell.appendChild(fav);
    grid.appendChild(cell);
  });
  renderAnnotationSymbolsLists();
}

function renderAnnotationSymbolsLists() {
  const { recent, favorites } = getAnnotationSymbolsElements();
  if (!recent || !favorites) return;
  const recentIds = getAnnotationSymbolsStorage("annotation_symbols_recent", []);
  const favoriteIds = getAnnotationSymbolsStorage("annotation_symbols_favorites", []);
  recent.innerHTML = "";
  favorites.innerHTML = "";
  const data = window.__annotationSymbolsData || [];
  recentIds.forEach((id) => {
    const item = data.find((symbol) => symbol.id === id);
    if (!item) return;
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "annotation-symbol-chip";
    chip.textContent = item.char;
    chip.title = item.name_ru;
    chip.addEventListener("click", () => insertAnnotationSymbol(item));
    recent.appendChild(chip);
  });
  favoriteIds.forEach((id) => {
    const item = data.find((symbol) => symbol.id === id);
    if (!item) return;
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "annotation-symbol-chip";
    chip.textContent = item.char;
    chip.title = item.name_ru;
    chip.addEventListener("click", () => insertAnnotationSymbol(item));
    favorites.appendChild(chip);
  });
}

function toggleAnnotationSymbolFavorite(id) {
  const current = new Set(getAnnotationSymbolsStorage("annotation_symbols_favorites", []));
  if (current.has(id)) {
    current.delete(id);
  } else {
    current.add(id);
  }
  setAnnotationSymbolsStorage("annotation_symbols_favorites", Array.from(current));
  renderAnnotationSymbolsPanel();
}

function insertAnnotationSymbol(item) {
  const editor = document.getElementById("annotationModalEditor");
  const { latexToggle, autoCloseToggle, panel } = getAnnotationSymbolsElements();
  if (!editor) return;
  restoreAnnotationSelection();
  editor.focus();
  const useLatex = latexToggle && latexToggle.checked && item.latex;
  const text = useLatex ? item.latex : item.char;
  document.execCommand("insertText", false, text);
  const recent = getAnnotationSymbolsStorage("annotation_symbols_recent", []);
  const filtered = recent.filter((id) => id !== item.id);
  filtered.unshift(item.id);
  setAnnotationSymbolsStorage("annotation_symbols_recent", filtered.slice(0, 20));
  renderAnnotationSymbolsLists();
  updateAnnotationStats();
  if (autoCloseToggle && autoCloseToggle.checked && panel) {
    closeAnnotationSymbolsPanel();
  }
  editor.focus();
}

function openAnnotationSymbolsPanel() {
  const { panel, search } = getAnnotationSymbolsElements();
  if (!panel) return;
  saveAnnotationSelection();
  renderAnnotationSymbolsPanel();
  panel.classList.add("active");
  panel.style.display = "block";
  panel.setAttribute("aria-hidden", "false");
  if (search) {
    search.focus();
    search.select();
  }
}

function closeAnnotationSymbolsPanel() {
  const { panel } = getAnnotationSymbolsElements();
  if (!panel) return;
  panel.classList.remove("active");
  panel.style.display = "none";
  panel.setAttribute("aria-hidden", "true");
}

function toggleAnnotationSymbolsPanel() {
  const { panel } = getAnnotationSymbolsElements();
  if (!panel) return;
  if (panel.classList.contains("active")) {
    closeAnnotationSymbolsPanel();
  } else {
    openAnnotationSymbolsPanel();
  }
}

function initAnnotationSymbolsPanel() {
  if (window.__annotationSymbolsHandlersAdded) return;
  window.__annotationSymbolsHandlersAdded = true;
  const { panel, search, category, grid } = getAnnotationSymbolsElements();
  if (search) search.addEventListener("input", renderAnnotationSymbolsPanel);
  if (category) category.addEventListener("change", renderAnnotationSymbolsPanel);
  document.addEventListener("mousedown", (event) => {
    const target = event.target;
    const button = target.closest("[data-action='toggle-symbols-panel']");
    const panelEl = getAnnotationSymbolsElements().panel;
    if (!panelEl || !panelEl.classList.contains("active")) return;
    if (panelEl.contains(target) || button) return;
    closeAnnotationSymbolsPanel();
  });
  document.addEventListener("keydown", (event) => {
    const panelEl = getAnnotationSymbolsElements().panel;
    if (!panelEl || !panelEl.classList.contains("active")) return;
    if (event.key === "Escape") {
      event.preventDefault();
      closeAnnotationSymbolsPanel();
      document.getElementById("annotationModalEditor")?.focus();
    }
  });
  if (grid) {
    grid.addEventListener("keydown", (event) => {
      const buttons = Array.from(grid.querySelectorAll(".annotation-symbol-btn"));
      if (!buttons.length) return;
      const active = document.activeElement;
      const index = buttons.indexOf(active);
      if (index === -1) return;
      const columns = getComputedStyle(grid).gridTemplateColumns.split(" ").length || 8;
      let nextIndex = index;
      if (event.key === "ArrowRight") nextIndex = Math.min(buttons.length - 1, index + 1);
      if (event.key === "ArrowLeft") nextIndex = Math.max(0, index - 1);
      if (event.key === "ArrowDown") nextIndex = Math.min(buttons.length - 1, index + columns);
      if (event.key === "ArrowUp") nextIndex = Math.max(0, index - columns);
      if (nextIndex !== index) {
        event.preventDefault();
        buttons[nextIndex].focus();
      }
      if (event.key === "Enter") {
        event.preventDefault();
        buttons[index].click();
      }
    });
  }
}

function viewAnnotation(fieldId, title) {
  const field = document.getElementById(fieldId);
  if (!field) return;

  currentAnnotationFieldId = fieldId;

  const annotationText = field.value.trim();

  const modal = document.getElementById("annotationModal");
  const modalTitle = document.getElementById("annotationModalTitle");
  const modalEditor = document.getElementById("annotationModalEditor");

  if (!modal || !modalTitle || !modalEditor) return;

  modalTitle.textContent = title;
  modalEditor.innerHTML = annotationTextToHtml(annotationText);
  modal.dataset.fieldId = fieldId;
  closeAnnotationSymbolsPanel();
  if (fieldId === "annotation" || fieldId === "annotation_en") {
    const lang = fieldId === "annotation_en" ? "en" : "ru";
    const textarea = document.getElementById("annotationModalTextarea");
    annotationCodeViewEnabled = false;
    annotationPreviewEnabled = false;
    if (textarea) textarea.style.display = "none";
    modalEditor.style.display = "block";
    modalEditor.contentEditable = "true";
    modalEditor.classList.remove("preview");
    modalEditor.lang = lang;
    const normalize = () => {
      const cleaned = window.processAnnotation(annotationHtmlToText(modalEditor.innerHTML), lang);
      modalEditor.innerHTML = annotationTextToHtml(cleaned);
    };
    modalEditor.onpaste = () => {
      setTimeout(normalize, 0);
    };
    modalEditor.onblur = normalize;
  } else {
    modalEditor.onpaste = null;
    modalEditor.onblur = null;
  }
  updateAnnotationStats();
  initAnnotationSymbolsPanel();

  modal.classList.add("active");
  setTimeout(() => {
    modalEditor.focus();
    const range = document.createRange();
    range.selectNodeContents(modalEditor);
    range.collapse(true);
    const selection = window.getSelection();
    if (selection) {
      selection.removeAllRanges();
      selection.addRange(range);
      saveAnnotationSelection();
    }
  }, 100);
}

function saveEditedAnnotation() {
  const modal = document.getElementById("annotationModal");
  const fallbackFieldId = modal?.dataset?.fieldId || null;
  const targetFieldId = currentAnnotationFieldId || fallbackFieldId;
  if (!targetFieldId) return;

  const field = document.getElementById(targetFieldId);
  const modalEditor = document.getElementById("annotationModalEditor");
  const modalTextarea = document.getElementById("annotationModalTextarea");

  if (!field || !modalEditor) return;

  const html = annotationCodeViewEnabled && modalTextarea ? modalTextarea.value : modalEditor.innerHTML;
  const rawText = annotationHtmlToText(html);
  let cleaned = rawText;
  if (targetFieldId === "annotation" || targetFieldId === "annotation_en") {
    const lang = targetFieldId === "annotation_en" ? "en" : "ru";
    cleaned = window.processAnnotation(rawText, lang);
  }
  field.value = cleaned;
  closeAnnotationModal();

  const notification = document.createElement("div");
  notification.style.cssText = "position:fixed;top:20px;right:20px;background:#4caf50;color:#fff;padding:15px 20px;border-radius:4px;box-shadow:0 4px 12px rgba(0,0,0,0.2);z-index:3000;font-size:14px;";
  notification.textContent = "\u0410\u043d\u043d\u043e\u0442\u0430\u0446\u0438\u044f \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0430";
  document.body.appendChild(notification);
  setTimeout(() => {
    notification.remove();
  }, 2000);
}

function closeAnnotationModal() {
          const modal = document.getElementById("annotationModal");
          const modalContent = document.getElementById("annotationModalContent");
          const expandBtn = document.getElementById("annotationModalExpandBtn");
          if (modal) {
            modal.classList.remove("active");
            // Сбрасываем размер при закрытии
            if (modalContent) {
              modalContent.classList.remove("expanded");
            }
            if (expandBtn) {
              expandBtn.classList.remove("expanded");
            }
          }
          annotationCodeViewEnabled = false;
          annotationPreviewEnabled = false;
          currentAnnotationFieldId = null;
        }
        
        function toggleAnnotationModalSize() {
          const modalContent = document.getElementById("annotationModalContent");
          const expandBtn = document.getElementById("annotationModalExpandBtn");
          if (modalContent && expandBtn) {
            const isExpanded = modalContent.classList.contains("expanded");
            if (isExpanded) {
              modalContent.classList.remove("expanded");
              expandBtn.classList.remove("expanded");
              expandBtn.title = "Увеличить окно";
            } else {
              modalContent.classList.add("expanded");
              expandBtn.classList.add("expanded");
              expandBtn.title = "Уменьшить окно";
            }
          }
        }

        function enableModalDragging(modalId, contentId) {
          const modal = document.getElementById(modalId);
          const content = document.getElementById(contentId);
          if (!modal || !content) return;
          const header = content.querySelector(".modal-header");
          if (!header) return;
          let isDragging = false;
          let offsetX = 0;
          let offsetY = 0;

          const onMouseDown = (event) => {
            if (event.button !== 0) return;
            isDragging = true;
            const rect = content.getBoundingClientRect();
            offsetX = event.clientX - rect.left;
            offsetY = event.clientY - rect.top;
            content.style.position = "fixed";
            content.style.margin = "0";
            content.style.left = `${rect.left}px`;
            content.style.top = `${rect.top}px`;
          };

          const onMouseMove = (event) => {
            if (!isDragging) return;
            const maxX = window.innerWidth - content.offsetWidth;
            const maxY = window.innerHeight - content.offsetHeight;
            const nextX = Math.min(Math.max(0, event.clientX - offsetX), Math.max(0, maxX));
            const nextY = Math.min(Math.max(0, event.clientY - offsetY), Math.max(0, maxY));
            content.style.left = `${nextX}px`;
            content.style.top = `${nextY}px`;
          };

          const onMouseUp = () => {
            isDragging = false;
          };

          header.addEventListener("mousedown", onMouseDown);
          document.addEventListener("mousemove", onMouseMove);
          document.addEventListener("mouseup", onMouseUp);
        }

        enableModalDragging("refsModal", "refsModalContent");
        enableModalDragging("annotationModal", "annotationModalContent");
        
        function openCopyModal(text) {
          const modal = document.getElementById("lineCopyModal");
          const ta = document.getElementById("lineCopyTextarea");
          if (!modal || !ta) return;
        
          ta.value = text;
          modal.classList.add("active");
          setTimeout(() => {
            ta.focus();
            ta.select();
          }, 0);
        }
        
        function closeCopyModal() {
          document.getElementById("lineCopyModal")?.classList.remove("active");
        }
        
        function toast(message) {
          const notification = document.createElement("div");
          notification.style.cssText = "position:fixed;top:20px;right:20px;background:#4caf50;color:#fff;padding:15px 20px;border-radius:4px;box-shadow:0 4px 12px rgba(0,0,0,0.2);z-index:3000;font-size:14px;";
          notification.textContent = message;
          document.body.appendChild(notification);
          setTimeout(() => {
            notification.remove();
          }, 2000);
        }
        
        // Обработчик кликов для копирования и закрытия модальных окон
        document.addEventListener("click", async (e) => {
          const openBtn = e.target.closest('[data-action="open-copy"]');
          if (openBtn) {
            const lineEl = openBtn.closest(".line");
            const text = lineEl?.querySelector(".line-text")?.textContent ?? "";
            openCopyModal(text);
            return;
          }
        
          if (e.target.closest('[data-action="close-copy"]')) {
            closeCopyModal();
            return;
          }
        
          if (e.target.closest('[data-action="copy-from-modal"]')) {
            const ta = document.getElementById("lineCopyTextarea");
            const text = ta?.value ?? "";
            if (!text) return;
            try {
              await navigator.clipboard.writeText(text);
              toast("Скопировано");
              closeCopyModal();
            } catch (err) {
              console.error("Ошибка копирования:", err);
              alert("Не удалось скопировать текст. Попробуйте выделить текст и использовать Ctrl+C");
            }
            return;
          }
        
          const refsModal = document.getElementById("refsModal");
          if (e.target === refsModal) {
            closeRefsModal();
          }
          
          const annotationModal = document.getElementById("annotationModal");
          if (e.target === annotationModal) {
            closeAnnotationModal();
          }
          
          const lineCopyModal = document.getElementById("lineCopyModal");
          if (e.target === lineCopyModal) {
            closeCopyModal();
          }
        });
        
        // Закрытие модальных окон по Escape
        document.addEventListener("keydown", (e) => {
          if (e.key === "Escape") {
            closeRefsModal();
            closeAnnotationModal();
            closeCopyModal();
          }
        });
        
        // Глобальные переменные для работы с выделением строк
        window.markupSelected = new Set();
        window.markupCurrentFieldId = null;
        
        // Функция для обновления панели выбора
        window.markupUpdatePanel = function() {
          const panel = document.getElementById("selectionPanel");
          const count = document.getElementById("selectedCount");
          console.log('Обновление панели. Panel:', panel, 'Count:', count, 'Selected:', window.markupSelected.size);
          if (!panel || !count) {
            console.warn('Панель выбора не найдена!');
            return;
          }
          if (window.markupSelected.size > 0) {
            panel.classList.add("active");
            count.textContent = String(window.markupSelected.size);
            console.log('Панель активирована, выделено:', window.markupSelected.size);
          } else {
            panel.classList.remove("active");
            count.textContent = "0";
          }
        };
        
        // Функция для очистки выделения
        window.markupClearSelection = function() {
          window.markupSelected.clear();
          document.querySelectorAll(".line.selected").forEach(el => el.classList.remove("selected"));
          window.markupUpdatePanel();
        };
        
        // Функция для получения текста выделенных строк
        window.getSelectedTexts = function() {
          return Array.from(window.markupSelected)
            .map(id => {
              const line = document.querySelector(`.line[data-id="${CSS.escape(id)}"]`);
              return line ? line.querySelector('.line-text')?.textContent || '' : '';
            })
            .map(t => t.trim())
            .filter(Boolean);
        };
        
        // Вспомогательные функции для извлечения данных из текста
        window.extractDOI = function(text) {
          const match = text.match(/10\.\d{4,}\/[^\s\)]+/);
          return match ? match[0] : null;
        };
        
        window.extractEmail = function(text) {
          const match = text.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
          return match ? match[0] : null;
        };
        
        window.extractORCID = function(text) {
          // ORCID формат: 0000-0000-0000-0000 (16 цифр, разделенных дефисами)
          // Также может быть в формате https://orcid.org/0000-0000-0000-0000
          const orcidPattern = /(?:orcid\.org\/)?(\d{4}-\d{4}-\d{4}-\d{3}[\dX])/i;
          const match = text.match(orcidPattern);
          return match ? match[1] : null;
        };
        
        window.extractScopusID = function(text) {
          // Scopus ID - числовой код, может быть указан как "Scopus ID: 123456789" или просто число
          const scopusPattern = /(?:Scopus\s*ID[:\s]*)?(\d{8,})/i;
          const match = text.match(scopusPattern);
          return match ? match[1] : null;
        };
        
        window.extractResearcherID = function(text) {
          // Researcher ID может быть в формате A-XXXX-XXXX или просто числовой код
          const researcherPattern = /(?:Researcher\s*ID[:\s]*)?([A-Z]-\d{4}-\d{4}|\d{8,})/i;
          const match = text.match(researcherPattern);
          return match ? match[1] : null;
        };
        
        window.extractSPIN = function(text) {
          // SPIN обычно числовой код, может быть указан как "SPIN: 1234-5678", "SPIN-код 264275" или просто число
          // Поддерживаем различные форматы: SPIN-код, SPIN код, SPIN:, AuthorID и т.д.
          // SPIN код обычно состоит из 4-8 цифр, может быть с дефисами или без
          
          // Сначала ищем явные упоминания SPIN или AuthorID
          const explicitPatterns = [
            /(?:SPIN[-]?код|SPIN\s*код|SPIN[:\s-]+|AuthorID[:\s]+)\s*(\d{4,8}(?:[-.\s]\d+)*)/i,
          ];
          
          for (const pattern of explicitPatterns) {
            const match = text.match(pattern);
            if (match) {
              // Убираем дефисы, точки и пробелы, оставляем только цифры
              const spin = match[1].replace(/[-.\s]/g, '');
              // SPIN код обычно от 4 до 8 цифр
              if (spin.length >= 4 && spin.length <= 8) {
                // Проверяем, что это не часть email или другого кода
                const beforeMatch = text.substring(0, match.index);
                const afterMatch = text.substring(match.index + match[0].length);
                // Исключаем числа, которые являются частью email
                if (!beforeMatch.match(/@[\w.-]*$/) && !afterMatch.match(/^[\w.-]*@/)) {
                  return spin;
                }
              }
            }
          }
          
          // Если явных упоминаний нет, ищем числа 4-8 цифр, но только если они не являются частью других кодов
          // Исключаем числа, которые являются частью email, DOI, ORCID, Scopus ID и т.д.
          const standaloneNumberPattern = /\b(\d{4,8})\b/g;
          const matches = [...text.matchAll(standaloneNumberPattern)];
          
          for (const match of matches) {
            const number = match[1];
            const matchIndex = match.index;
            const beforeText = text.substring(Math.max(0, matchIndex - 20), matchIndex);
            const afterText = text.substring(matchIndex + number.length, Math.min(text.length, matchIndex + number.length + 20));
            
            // Пропускаем, если это часть email
            if (beforeText.match(/@[\w.-]*$/) || afterText.match(/^[\w.-]*@/)) {
              continue;
            }
            
            // Пропускаем, если это часть DOI (10.xxxx/...)
            if (beforeText.match(/10\.\d{4,}/) || afterText.match(/^\/[^\s\)]+/)) {
              continue;
            }
            
            // Пропускаем, если это часть ORCID (0000-0000-0000-0000)
            if (beforeText.match(/orcid/i) || afterText.match(/^-\d{4}-\d{4}-\d{3}/)) {
              continue;
            }
            
            // Пропускаем, если это часть Scopus ID (обычно 8+ цифр)
            if (beforeText.match(/scopus/i) || number.length >= 8) {
              continue;
            }
            
            // Пропускаем, если это часть Researcher ID (A-1234-5678)
            if (beforeText.match(/researcher\s*id/i) || afterText.match(/^-\d{4}-\d{4}/)) {
              continue;
            }
            
            // Если число не является частью других кодов, возвращаем его как SPIN
            return number;
          }
          
          return null;
        };
        
        window.processAnnotation = function(text) {
          // Удаляем префиксы "Аннотация", "Annotation", "Abstract"
          return text.replace(/^(Аннотация|Annotation|Abstract)[\s:]+/i, '').trim();
        };
        
        // Упрощенная версия функции applySelectionToField для работы с выделенными строками
        window.applySelectionToField = function(fieldId) {
          const texts = window.getSelectedTexts();
          if (!texts.length) {
            alert('Нет выделенных строк');
            return;
          }
          const fullText = texts.join(' ');
          
          // Находим поле по ID
          const field = document.getElementById(fieldId);
          if (!field) {
            console.warn('Поле не найдено:', fieldId);
            return;
          }
          
          let value = '';
          
          // Обработка специальных полей
          if (fieldId === 'doi') {
            const doi = window.extractDOI(fullText);
            if (!doi) {
              alert('DOI не найден в выделенном тексте. Нужен формат 10.xxxx/xxxxx');
              return;
            }
            value = doi;
          } else if (fieldId === 'annotation' || fieldId === 'annotation_en') {
            value = window.processAnnotation(fullText);
          } else {
            // Для остальных полей просто вставляем текст
            value = fullText.trim();
          }
          
          field.value = value;
          field.focus();
          
          // Очищаем выделение
          window.markupClearSelection();
        };
        
        // Функция для инициализации обработчиков формы из MARKUP_TEMPLATE
        window.initializeMarkupFormHandlers = function(filename) {
          console.log('Инициализация обработчиков формы для:', filename);
          
          // Очищаем предыдущее выделение
          window.markupSelected.clear();
          window.markupUpdatePanel();
          
          // Находим контейнер с текстом статьи (в главном шаблоне это articleTextPanel)
          const textPanel = document.getElementById('articleTextPanel');
          if (!textPanel) {
            console.error('Не найден элемент articleTextPanel');
            return;
          }
          
          // Находим контейнер с текстом внутри (может быть #textContent или просто div с классом)
          const textContent = textPanel.querySelector('#textContent') || textPanel;
          
          console.log('Найден textContent:', textContent);
          const linesCount = textContent.querySelectorAll('.line').length;
          console.log('Количество строк:', linesCount);
          
          if (linesCount === 0) {
            console.error('Строки не найдены! Проверьте структуру HTML.');
            // Попробуем найти строки через некоторое время
            setTimeout(() => {
              const retryLines = textPanel.querySelectorAll('.line').length;
              console.log('Повторная проверка строк:', retryLines);
            }, 1000);
            return;
          }
          
          // Устанавливаем один простой обработчик клика через делегирование событий
          textPanel.addEventListener("click", function(e) {
            // Пропускаем клики по кнопке копирования
            if (e.target.closest('.line-copy-btn') || e.target.classList.contains('line-copy-btn')) {
              return;
            }
            
            const line = e.target.closest(".line");
            if (!line) return;
            
            const id = line.dataset.id;
            if (!id) {
              console.warn('У строки нет data-id:', line);
              return;
            }
            
            console.log('Клик по строке:', id);
            
            // Простое переключение выделения
            if (window.markupSelected.has(id)) {
              window.markupSelected.delete(id);
              line.classList.remove("selected");
            } else {
              window.markupSelected.add(id);
              line.classList.add("selected");
            }
            
            console.log('Выделено строк:', window.markupSelected.size);
            window.markupUpdatePanel();
          });
          
          // Устанавливаем обработчик фокуса для полей формы
          document.addEventListener("focusin", function(e) {
            const el = e.target;
            if (!el) return;
            if ((el.tagName === "INPUT" || el.tagName === "TEXTAREA") && el.id) {
              window.markupCurrentFieldId = el.id;
            }
          });
          
          // Устанавливаем обработчик для кнопки очистки выделения
          const clearBtn = document.getElementById("clearBtn");
          if (clearBtn) {
            clearBtn.addEventListener("click", function() {
              window.markupClearSelection();
            });
          }
          
          // Устанавливаем обработчик для панели выбора полей
          const panel = document.getElementById("selectionPanel");
          console.log('Панель selectionPanel:', panel);
          if (panel) {
            console.log('Панель найдена, устанавливаем обработчик');
            panel.addEventListener("click", function(e) {
              const btn = e.target.closest("button");
              if (!btn) return;
              const action = btn.dataset.action;
              if (action === "cancel") {
                window.markupClearSelection();
                return;
              }
              const assign = btn.dataset.assign;
              console.log('Клик по кнопке панели:', assign);
              if (assign && typeof window.applySelectionToField === 'function') {
                window.applySelectionToField(assign);
              } else {
                console.warn('Функция applySelectionToField не найдена!');
              }
            });
          } else {
            console.error('Панель selectionPanel не найдена! Проверьте, что она загружена в форме.');
            // Попробуем найти панель через некоторое время
            setTimeout(() => {
              const retryPanel = document.getElementById("selectionPanel");
              if (retryPanel) {
                console.log('Панель найдена при повторной проверке');
                retryPanel.addEventListener("click", function(e) {
                  const btn = e.target.closest("button");
                  if (!btn) return;
                  const action = btn.dataset.action;
                  if (action === "cancel") {
                    window.markupClearSelection();
                    return;
                  }
                  const assign = btn.dataset.assign;
                  if (assign && typeof window.applySelectionToField === 'function') {
                    window.applySelectionToField(assign);
                  }
                });
              } else {
                console.error('Панель selectionPanel все еще не найдена!');
              }
            }, 1000);
          }
          
          console.log('Обработчики формы инициализированы');
        };
        </script>
      {% else %}
        <div class="empty-state card">
          <h3>JSON-файлы не найдены</h3>
          <p>Загрузите или поместите JSON-файлы в папку:</p>
          <p style="margin-top: 12px; font-size: 14px;">
            <code>input_files/имя_архива/json</code>
          </p>
          <div style="margin-top: 14px;">
            <button type="button" id="openJsonFolderBtn" class="btn btn-secondary">📂 Открыть папку выпуска</button>
          </div>
        </div>
      {% endif %}
      <script>
        const inputArchiveForm = document.getElementById("inputArchiveForm");
        const processArchiveBtn = document.getElementById("processArchiveBtn");
        const saveProjectBtn = document.getElementById("saveProjectBtn");
        const openProjectBtn = document.getElementById("openProjectBtn");
        const deleteProjectBtn = document.getElementById("deleteProjectBtn");
        const downloadProjectBtn = document.getElementById("downloadProjectBtn");
        const restoreProjectBtn = document.getElementById("restoreProjectBtn");
        const restoreProjectArchiveInput = document.getElementById("restoreProjectArchiveInput");
        const openJsonFolderBtn = document.getElementById("openJsonFolderBtn");
        if (openProjectBtn) {
          openProjectBtn.addEventListener("click", () => {
            if (window.openProject) window.openProject();
          });
        }
        if (openJsonFolderBtn) {
          openJsonFolderBtn.addEventListener("click", async () => {
            try {
              const resp = await fetch("/open-json-input");
              const data = await resp.json().catch(() => ({}));
              if (!resp.ok || !data.success) {
                window.alert(data.error || "Не удалось открыть папку.");
              }
            } catch (_) {
              window.alert("Не удалось открыть папку.");
            }
          });
        }

        const archiveProgress = document.getElementById("archiveProgress");
        const archiveProgressFill = document.getElementById("archiveProgressFill");
        const archiveDetails = document.getElementById("archiveDetails");
        const projectStatus = document.getElementById("projectStatus");
        const stepBar = document.getElementById("stepBar");
        const allowPartialXml = document.getElementById("allowPartialXml");
        window.currentArchive = window.currentArchive || null;
        let archivePollTimer = null;
        const archiveReloadKey = "archive_done_reloaded";

        const stopArchivePolling = () => {
          if (archivePollTimer) {
            clearInterval(archivePollTimer);
            archivePollTimer = null;
          }
        };

        const updateSteps = () => {
          if (!stepBar) return;
          const total = Number(stepBar.dataset.total || 0);
          const processedTotal = Number(stepBar.dataset.processed || 0);
          const step1 = stepBar.querySelector('[data-step="1"]');
          const step2 = stepBar.querySelector('[data-step="2"]');
          const step3 = stepBar.querySelector('[data-step="3"]');
          const allowPartialXml = document.getElementById("allowPartialXml");
          const setStep = (el, state) => {
            if (!el) return;
            const label = el.dataset.label || el.textContent || "";
            el.classList.remove("active", "done");
            if (state === "done") {
              el.classList.add("done");
              el.textContent = `✔ ${label}`;
            } else if (state === "active") {
              el.classList.add("active");
              el.textContent = `▶ ${label}`;
            } else {
              el.textContent = label;
            }
          };
          const archiveReady = !!window.currentArchive;
          const status = window.archiveStatus || "idle";
          const step2Done = total > 0 && processedTotal === total;
          const step2Active = archiveReady && !step2Done;
          const xmlKey = window.currentArchive ? `xml_done_${window.currentArchive}` : null;
          const xmlDone = xmlKey ? sessionStorage.getItem(xmlKey) === "1" : false;
          const allowXml = allowPartialXml && allowPartialXml.checked;

          setStep(step1, archiveReady ? "done" : "active");
          if (archiveReady) {
            const step2State = allowXml && !step2Done ? "" : (step2Done ? "done" : (step2Active ? "active" : ""));
            setStep(step2, step2State);
          } else {
            setStep(step2, "");
          }
          if (step2Done) {
            setStep(step3, xmlDone ? "done" : "active");
          } else if (allowXml && archiveReady) {
            setStep(step3, xmlDone ? "done" : "active");
          } else {
            setStep(step3, "");
          }
        };

        const updateArchiveUi = (data) => {
          const status = data?.status || "idle";
          const processed = Number(data?.processed || 0);
          const total = Number(data?.total || 0);
          window.archiveStatus = status;
          window.archiveProcessed = processed;
          window.archiveTotal = total;
          if (status !== "done") {
            sessionStorage.removeItem(archiveReloadKey);
          }
          if (data?.archive) {
            window.currentArchive = data.archive;
            sessionStorage.setItem("lastArchiveName", data.archive);
            if (status !== "done") {
              sessionStorage.removeItem(`xml_done_${data.archive}`);
            }
          } else if (!window.currentArchive) {
            const cachedArchive = sessionStorage.getItem("lastArchiveName");
            if (cachedArchive) {
              window.currentArchive = cachedArchive;
            }
          }
          updateSteps();
          if (processArchiveBtn) {
            const disabled = !window.currentArchive || status === "running";
            processArchiveBtn.classList.toggle("is-disabled", disabled);
            processArchiveBtn.setAttribute("aria-disabled", disabled ? "true" : "false");
          }
          if (!archiveProgress) return;
          if (archiveProgressFill) {
            const safeTotal = total > 0 ? total : 1;
            const pct = Math.max(0, Math.min(100, Math.round((processed / safeTotal) * 100)));
            archiveProgressFill.style.width = `${pct}%`;
          }
          const setArchiveDetails = (color) => {
            if (!archiveDetails) return;
            const pdfCount = data?.pdf_count ?? null;
            const extraCount = data?.extra_count ?? null;
            const details = [];
            if (pdfCount !== null) details.push(`PDF: ${pdfCount}`);
            if (extraCount !== null) details.push(`Доп. файлов: ${extraCount}`);
            if (data?.message) details.push(data.message);
            archiveDetails.textContent = details.join(" • ");
            archiveDetails.style.color = color || "#555";
          };
          if (status === "running") {
            archiveProgress.textContent = `Обработка: ${processed}/${total}`;
            archiveProgress.style.color = "#555";
            setArchiveDetails("#555");
            if (!archivePollTimer) {
              archivePollTimer = setInterval(fetchArchiveStatus, 1000);
            }
            return;
          }
          if (status === "done") {
            archiveProgress.textContent = "Выпуск успешно обработан";
            archiveProgress.style.color = "#2e7d32";
            setArchiveDetails("#2e7d32");
            stopArchivePolling();
            if (!sessionStorage.getItem(archiveReloadKey)) {
              sessionStorage.setItem(archiveReloadKey, "1");
              setTimeout(() => window.location.reload(), 1200);
            }
            return;
          }
          if (status === "error") {
            archiveProgress.textContent = data?.message || "Ошибка обработки.";
            archiveProgress.style.color = "#c62828";
            setArchiveDetails("#c62828");
            if (archiveProgressFill) {
              archiveProgressFill.style.width = "0%";
            }
            stopArchivePolling();
            return;
          }
          if (window.currentArchive) {
            archiveProgress.textContent = `Архив готов: ${window.currentArchive}`;
            archiveProgress.style.color = "#555";
            setArchiveDetails("#555");
            if (archiveProgressFill && status !== "running") {
              archiveProgressFill.style.width = "0%";
            }
          } else {
            archiveProgress.textContent = "";
            if (archiveDetails) {
              archiveDetails.textContent = "";
            }
            if (archiveProgressFill) {
              archiveProgressFill.style.width = "0%";
            }
          }
          stopArchivePolling();
        };

        if (allowPartialXml) {
          allowPartialXml.addEventListener("change", () => {
            updateSteps();
          });
        }

        const fetchArchiveStatus = async () => {
          try {
            const resp = await fetch("/process-archive-status");
            const data = await resp.json().catch(() => ({}));
            updateArchiveUi(data);
          } catch (_) {
            // ignore
          }
        };
        fetchArchiveStatus();

        if (!window.toast) {
          window.toast = function(message) {
            const notification = document.createElement("div");
            notification.style.cssText = "position:fixed;top:20px;right:20px;background:#4caf50;color:#fff;padding:15px 20px;border-radius:4px;box-shadow:0 4px 12px rgba(0,0,0,0.2);z-index:3000;font-size:14px;";
            notification.textContent = message;
            document.body.appendChild(notification);
            setTimeout(() => {
              notification.remove();
            }, 2000);
          };
        }

        if (processArchiveBtn) {
          processArchiveBtn.addEventListener("click", async () => {
            if (!window.currentArchive) {
              updateArchiveUi({ status: "idle", archive: null });
              window.toast("Сначала загрузите архив выпуска, затем нажмите обработку.");
              return;
            }
            const uploadNotice = document.getElementById("archiveUploadNotice");
            if (uploadNotice) {
              uploadNotice.remove();
            }
            if (processArchiveBtn.classList.contains("is-disabled")) {
              window.toast("Подождите завершения текущей обработки.");
              return;
            }
            if (archiveProgress) {
              archiveProgress.textContent = "Запуск обработки...";
              archiveProgress.style.color = "#555";
            }
            try {
              const resp = await fetch("/process-archive", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ archive: window.currentArchive })
              });
              const data = await resp.json().catch(() => ({}));
              if (!resp.ok || !data.success) {
                if (archiveProgress) {
                  archiveProgress.textContent = data.error || "Ошибка запуска обработки.";
                  archiveProgress.style.color = "#c62828";
                }
                return;
              }
              fetchArchiveStatus();
            } catch (_) {
              if (archiveProgress) {
                archiveProgress.textContent = "Ошибка запуска обработки.";
                archiveProgress.style.color = "#c62828";
              }
            }
          });
        }

        const setProjectStatus = (text, color) => {
          if (!projectStatus) return;
          projectStatus.textContent = text;
          projectStatus.style.color = color || "#555";
        };

        window.saveProject = async () => {
          const issue = (window.currentArchive || sessionStorage.getItem("lastArchiveName") || "").trim();
          if (!issue) {
            setProjectStatus("Нет текущего загруженного выпуска.", "#c62828");
            return;
          }
          setProjectStatus("Сохранение проекта...", "#555");
          try {
            const resp = await fetch("/project-save", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ issue })
            });
            const data = await resp.json().catch(() => ({}));
            if (!resp.ok || !data.success) {
              setProjectStatus(data.error || "Ошибка сохранения проекта.", "#c62828");
              return;
            }
            setProjectStatus(`Проект сохранен: ${data.issue || issue}`, "#2e7d32");
            sessionStorage.removeItem("lastArchiveName");
            sessionStorage.removeItem("archive_done_reloaded");
            window.currentArchive = null;
            setTimeout(() => window.location.reload(), 1200);
          } catch (_) {
            setProjectStatus("Ошибка сохранения проекта.", "#c62828");
          }
        };

        window.openProject = async () => {
          setProjectStatus("Загрузка списка проектов...", "#555");
          const projectModal = document.getElementById("projectModal");
          const projectSelect = document.getElementById("projectSelect");
          const projectOpenConfirm = document.getElementById("projectOpenConfirm");
          if (!projectModal || !projectSelect || !projectOpenConfirm) {
            setProjectStatus("Окно выбора проектов недоступно.", "#c62828");
            return;
          }
          try {
            const resp = await fetch("/project-snapshots");
            const data = await resp.json().catch(() => ({}));
            const snapshots = data.snapshots || [];
            const options = [];
            snapshots.forEach((run) => {
              (run.issues || []).forEach((issue) => {
                options.push({ run: run.run, issue });
              });
            });
            if (!options.length) {
              setProjectStatus("Нет сохраненных проектов.", "#c62828");
              return;
            }
            projectSelect.innerHTML = "";
            options.forEach((opt) => {
              const item = document.createElement("option");
              item.value = JSON.stringify(opt);
              const runLabel = opt.run === "current" ? "текущий" : `архив ${opt.run}`;
              item.textContent = `${opt.issue} (${runLabel})`;
              projectSelect.appendChild(item);
            });
            projectModal.classList.add("active");

            const closeModal = () => projectModal.classList.remove("active");
            const onBackdrop = (e) => {
              if (e.target === projectModal) closeModal();
            };
            const onCancel = (e) => {
              const btn = e.target.closest("button");
              if (btn && btn.dataset.action === "cancel") closeModal();
            };
            projectModal.addEventListener("click", onBackdrop, { once: true });
            projectModal.addEventListener("click", onCancel, { once: true });

            projectOpenConfirm.onclick = async () => {
              if (!projectSelect.value) {
                setProjectStatus("Выберите проект.", "#c62828");
                return;
              }
              let target = null;
              try {
                target = JSON.parse(projectSelect.value);
              } catch (_) {
                target = null;
              }
              if (!target) {
                setProjectStatus("Некорректный выбор проекта.", "#c62828");
                return;
              }
              const restore = async (overwrite) => {
                const restoreResp = await fetch("/project-restore", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ run: target.run, issue: target.issue, overwrite })
                });
                return restoreResp.json().catch(() => ({}));
              };
              let restoreData = await restore(false);
              if (!restoreData.success && restoreData.code === "dest_exists") {
                const confirmOverwrite = window.confirm("Папка выпуска уже существует. Перезаписать?");
                if (!confirmOverwrite) {
                  setProjectStatus("Восстановление отменено.", "#555");
                  closeModal();
                  return;
                }
                restoreData = await restore(true);
              }
              if (!restoreData.success) {
                setProjectStatus(restoreData.error || "Ошибка восстановления.", "#c62828");
                closeModal();
                return;
              }
              setProjectStatus(`Проект восстановлен: ${target.issue}`, "#2e7d32");
              closeModal();
              setTimeout(() => window.location.reload(), 1200);
            };
          } catch (_) {
            setProjectStatus("Ошибка восстановления.", "#c62828");
          }
        };

        window.deleteProject = async () => {
          const issue = (window.currentArchive || sessionStorage.getItem("lastArchiveName") || "").trim();
          if (!issue) {
            setProjectStatus("Нет текущего загруженного выпуска.", "#c62828");
            return;
          }
          const confirmDelete = window.confirm(`Вы уверены, что хотите удалить выпуск "${issue}"? Это действие необратимо.`);
          if (!confirmDelete) {
            setProjectStatus("Удаление отменено.", "#555");
            return;
          }
          setProjectStatus("Удаление выпуска...", "#555");
          try {
            const resp = await fetch("/project-delete", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ issue })
            });
            const data = await resp.json().catch(() => ({}));
            if (!resp.ok || !data.success) {
              setProjectStatus(data.error || "Ошибка удаления выпуска.", "#c62828");
              return;
            }
            setProjectStatus(`Выпуск удалён: ${data.issue || issue}`, "#2e7d32");
            setTimeout(() => window.location.reload(), 1200);
          } catch (_) {
            setProjectStatus("Ошибка удаления выпуска.", "#c62828");
          }
        };

        window.downloadProject = async () => {
          const issue = (window.currentArchive || sessionStorage.getItem("lastArchiveName") || "").trim();
          if (!issue) {
            setProjectStatus("Нет текущего загруженного выпуска.", "#c62828");
            return;
          }
          setProjectStatus("Подготовка архива проекта...", "#555");
          try {
            const url = `/project-download?issue=${encodeURIComponent(issue)}`;
            const link = document.createElement("a");
            link.href = url;
            link.download = `${issue}_project.zip`;
            document.body.appendChild(link);
            link.click();
            link.remove();
            setProjectStatus(`Архив проекта скачивается: ${issue}`, "#2e7d32");
          } catch (_) {
            setProjectStatus("Ошибка скачивания проекта.", "#c62828");
          }
        };

        window.restoreProjectFromArchive = async (file) => {
          if (!file) return;
          setProjectStatus("Загрузка архива проекта...", "#555");
          const tryRestore = async (overwrite) => {
            const formData = new FormData();
            formData.append("archive", file);
            if (overwrite) {
              formData.append("overwrite", "true");
            }
            const resp = await fetch("/project-upload-archive", {
              method: "POST",
              body: formData,
            });
            const data = await resp.json().catch(() => ({}));
            return { resp, data };
          };
          try {
            let { resp, data } = await tryRestore(false);
            if ((!resp.ok || !data.success) && data.code === "dest_exists") {
              const confirmOverwrite = window.confirm("Папка выпуска уже существует. Перезаписать?");
              if (!confirmOverwrite) {
                setProjectStatus("Восстановление отменено.", "#555");
                return;
              }
              ({ resp, data } = await tryRestore(true));
            }
            if (!resp.ok || !data.success) {
              setProjectStatus(data.error || "Ошибка восстановления проекта.", "#c62828");
              return;
            }
            const issueName = data.issue || data.archive || "проект";
            setProjectStatus(`Проект восстановлен: ${issueName}`, "#2e7d32");
            window.currentArchive = issueName;
            sessionStorage.setItem("lastArchiveName", issueName);
            setTimeout(() => window.location.reload(), 1200);
          } catch (_) {
            setProjectStatus("Ошибка восстановления проекта.", "#c62828");
          }
        };

        if (saveProjectBtn) {
          saveProjectBtn.addEventListener("click", window.saveProject);
        }

        if (openProjectBtn) {
          openProjectBtn.addEventListener("click", window.openProject);
        }
        if (deleteProjectBtn) {
          deleteProjectBtn.addEventListener("click", window.deleteProject);
        }
        if (downloadProjectBtn) {
          downloadProjectBtn.addEventListener("click", window.downloadProject);
        }
        if (restoreProjectBtn && restoreProjectArchiveInput) {
          restoreProjectBtn.addEventListener("click", () => {
            restoreProjectArchiveInput.value = "";
            restoreProjectArchiveInput.click();
          });
          restoreProjectArchiveInput.addEventListener("change", async (e) => {
            const file = e.target && e.target.files ? e.target.files[0] : null;
            if (!file) return;
            await window.restoreProjectFromArchive(file);
          });
        }

        window.handleArchiveUpload = async (event) => {
          if (event && event.preventDefault) event.preventDefault();
          const fileInput = document.getElementById("inputArchiveFile");
          const status = document.getElementById("inputArchiveStatus");
          if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
            if (status) {
              status.textContent = "Выберите ZIP файл.";
              status.style.color = "#c62828";
            }
            return false;
          }
          const formData = new FormData();
          formData.append("archive", fileInput.files[0]);
          if (status) {
            status.textContent = "Загрузка архива...";
            status.style.color = "#555";
          }
          try {
            const response = await fetch("/upload-input-archive", {
              method: "POST",
              body: formData
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok || !data.success) {
              if (status) {
                status.textContent = data.error || "Ошибка загрузки архива.";
                status.style.color = "#c62828";
              }
              return false;
            }
            if (status) {
              status.textContent = data.message || "Архив загружен.";
              status.style.color = "#2e7d32";
            }
            const existingNotice = document.getElementById("archiveUploadNotice");
            if (existingNotice) {
              existingNotice.remove();
            }
            const notice = document.createElement("div");
            notice.id = "archiveUploadNotice";
            notice.style.cssText = "margin-top:10px;background:#e8f5e9;border:1px solid #81c784;color:#2e7d32;padding:8px 10px;border-radius:4px;font-size:12px;font-weight:600;";
            notice.textContent = "Архив успешно загружен.";
            inputArchiveForm.appendChild(notice);
            setTimeout(() => {
              window.location.reload();
            }, 4000);
          } catch (error) {
            if (status) {
              status.textContent = "Ошибка загрузки архива.";
              status.style.color = "#c62828";
            }
          }
          return false;
        };

        if (inputArchiveForm) {
          inputArchiveForm.addEventListener("submit", window.handleArchiveUpload);
        }
        const uploadArchiveBtn = document.getElementById("uploadArchiveBtn");
        if (uploadArchiveBtn) {
          uploadArchiveBtn.addEventListener("click", window.handleArchiveUpload);
        }
      </script>
    </div>
  </div>
</body>
</html>
"""

PDF_BBOX_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Поиск блоков в PDF (bbox)</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      padding: 20px;
      min-height: 100vh;
    }
    .container {
      max-width: 1200px;
      margin: 0 auto;
      background: white;
      border-radius: 8px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.2);
      padding: 30px;
    }
    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      border-radius: 8px;
      margin-bottom: 30px;
      text-align: center;
    }
    .header h1 {
      font-size: 24px;
      margin-bottom: 10px;
    }
    .header-actions {
      margin-top: 15px;
    }
    .header-btn {
      background: rgba(255,255,255,0.2);
      color: white;
      border: 1px solid rgba(255,255,255,0.3);
      padding: 8px 16px;
      border-radius: 6px;
      text-decoration: none;
      font-size: 14px;
      display: inline-block;
      margin: 0 5px;
      transition: all 0.2s;
    }
    .header-btn:hover {
      background: rgba(255,255,255,0.3);
    }
    .form-section {
      margin-bottom: 30px;
      padding: 20px;
      background: #f8f9fa;
      border-radius: 6px;
    }
    .form-group {
      margin-bottom: 20px;
    }
    .form-group label {
      display: block;
      font-weight: 600;
      margin-bottom: 8px;
      color: #333;
      font-size: 14px;
    }
    .form-group input,
    .form-group select,
    .form-group textarea {
      width: 100%;
      padding: 10px;
      border: 1px solid #3a3f52;
      border-radius: 4px;
      font-size: 14px;
      font-family: inherit;
      background: #232633;
      color: #e6e8ee;
    }
    .form-group input:focus,
    .form-group select:focus,
    .form-group textarea:focus {
      outline: none;
      border-color: #6c63ff;
      box-shadow: 0 0 0 3px rgba(108, 99, 255, 0.2);
    }
    .checkbox-group {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .checkbox-group input[type="checkbox"] {
      width: auto;
    }
    .btn {
      padding: 12px 24px;
      border: none;
      border-radius: 4px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }
    .btn-primary {
      background: #667eea;
      color: white;
    }
    .btn-primary:hover {
      background: #5568d3;
    }
    .btn-secondary {
      background: #e0e0e0;
      color: #333;
    }
    .btn-secondary:hover {
      background: #d0d0d0;
    }
    .results-section {
      margin-top: 30px;
      display: none;
    }
    .results-section.active {
      display: block;
    }
    .block-item {
      background: white;
      border: 1px solid #e0e0e0;
      border-radius: 6px;
      padding: 20px;
      margin-bottom: 15px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .block-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 15px;
      padding-bottom: 10px;
      border-bottom: 2px solid #667eea;
    }
    .block-title {
      font-size: 18px;
      font-weight: 600;
      color: #667eea;
    }
    .block-meta {
      font-size: 12px;
      color: #666;
    }
    .bbox-info {
      background: #f8f9fa;
      padding: 15px;
      border-radius: 4px;
      margin: 10px 0;
      font-family: 'Courier New', monospace;
      font-size: 13px;
    }
    .bbox-coords {
      display: flex;
      gap: 10px;
      margin-top: 10px;
    }
    .bbox-coord {
      flex: 1;
      background: white;
      padding: 8px;
      border-radius: 4px;
      border: 1px solid #ddd;
    }
    .copy-btn {
      background: #4caf50;
      color: white;
      border: none;
      padding: 6px 12px;
      border-radius: 4px;
      cursor: pointer;
      font-size: 12px;
      margin-left: 10px;
    }
    .copy-btn:hover {
      background: #45a049;
    }
    .block-text {
      margin-top: 15px;
      padding: 15px;
      background: #fff;
      border-left: 4px solid #667eea;
      border-radius: 4px;
      max-height: 200px;
      overflow-y: auto;
      white-space: pre-wrap;
      font-size: 13px;
      line-height: 1.6;
    }
    .loading {
      text-align: center;
      padding: 40px;
      color: #666;
    }
    .error {
      background: #ffebee;
      border: 1px solid #f44336;
      color: #c62828;
      padding: 15px;
      border-radius: 4px;
      margin-top: 20px;
    }
    .success {
      background: #e8f5e9;
      border: 1px solid #4caf50;
      color: #2e7d32;
      padding: 15px;
      border-radius: 4px;
      margin-top: 20px;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🔍 Поиск блоков в PDF (bbox)</h1>
      <p>Найдите текстовые блоки по ключевым словам и получите их координаты</p>
      <div class="header-actions">
        <a href="/" class="header-btn">← К списку</a>
      </div>
    </div>

    <div class="form-section">
      <form id="bboxForm">
        <div class="form-group">
          <label for="pdfFile">Выберите PDF файл из папки input_files:</label>
          <select id="pdfFile" name="pdf_file" required>
            <option value="">-- Выберите файл --</option>
          </select>
        </div>

        <div class="form-group">
          <div class="checkbox-group">
            <input type="checkbox" id="findAnnotation" name="find_annotation">
            <label for="findAnnotation" style="margin: 0;">Автоматически найти аннотацию/резюме</label>
          </div>
        </div>

        <div class="form-group" id="termsGroup">
          <label for="searchTerms">Ключевые слова для поиска (по одному на строку):</label>
          <textarea 
            id="searchTerms" 
            name="search_terms" 
            rows="4" 
            placeholder="Резюме&#10;Аннотация&#10;Abstract&#10;Annotation&#10;Ключевые слова&#10;Keywords"
            style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; font-family: inherit; resize: vertical;"
          ></textarea>
          <small style="color: #666; font-size: 12px; margin-top: 5px; display: block;">
            Оставьте пустым для использования стандартных ключевых слов
          </small>
        </div>

        <div style="display: flex; gap: 10px;">
          <button type="submit" class="btn btn-primary">🔍 Найти блоки</button>
          <button type="button" class="btn btn-secondary" onclick="clearResults()">Очистить</button>
        </div>
      </form>
    </div>

    <div id="loading" class="loading" style="display: none;">
      <p>⏳ Поиск блоков в PDF...</p>
    </div>

    <div id="error" class="error" style="display: none;"></div>

    <div id="results" class="results-section">
      <h2 style="margin-bottom: 20px; color: #333;">Найденные блоки:</h2>
      <div id="blocksContainer"></div>
    </div>
  </div>

  <script>
    // Загружаем список PDF файлов при загрузке страницы

    document.addEventListener('DOMContentLoaded', function() {
      loadPdfFiles();
      
      // Обработчик для чекбокса "найти аннотацию"
      document.getElementById('findAnnotation').addEventListener('change', function() {
        const termsGroup = document.getElementById('termsGroup');
        if (this.checked) {
          termsGroup.style.opacity = '0.5';
          termsGroup.style.pointerEvents = 'none';
        } else {
          termsGroup.style.opacity = '1';
          termsGroup.style.pointerEvents = 'auto';
        }
      });
    });

    // Делаем функцию доступной глобально для onclick
    window.loadPdfFiles = async function loadPdfFiles() {
      const select = document.getElementById('pdfFile');
      if (!select) {
        console.error('Элемент select#pdfFile не найден');
        return;
      }
      
      try {
        console.log('Загрузка списка PDF файлов...');
        const response = await fetch('/api/pdf-files');
        console.log('Ответ получен, статус:', response.status);
        
        if (response.ok) {
          const data = await response.json();
          console.log('Получены данные:', data);
          
          // Проверяем, что data - это массив
          const files = Array.isArray(data) ? data : [];
          
          if (files.length === 0) {
            console.warn('PDF файлы не найдены');
            const option = document.createElement('option');
            option.value = '';
            option.textContent = '-- PDF файлы не найдены --';
            option.disabled = true;
            select.appendChild(option);
            return;
          }
          
          files.forEach(file => {
            // file уже содержит путь с подпапками (например, "1605-7880_2025_84_6")
            const option = document.createElement('option');
            option.value = file;
            // Отображаем полный путь для удобства
            option.textContent = file;
            select.appendChild(option);
          });
          
          console.log(`Загружено ${files.length} PDF файлов`);
        } else {
          const errorData = await response.json().catch(() => ({ error: 'Неизвестная ошибка' }));
          console.error('Ошибка при загрузке файлов:', errorData);
          const option = document.createElement('option');
          option.value = '';
          option.textContent = '-- Ошибка загрузки: ' + (errorData.error || 'Неизвестная ошибка') + ' --';
          option.disabled = true;
          select.appendChild(option);
        }
      } catch (e) {
        console.error('Ошибка при загрузке списка файлов:', e);
        const option = document.createElement('option');
        option.value = '';
        option.textContent = '-- Ошибка: ' + e.message + ' --';
        option.disabled = true;
        select.appendChild(option);
      }
    }

    document.getElementById('bboxForm').addEventListener('submit', async function(e) {
      e.preventDefault();
      
      const pdfFile = document.getElementById('pdfFile').value;
      const findAnnotation = document.getElementById('findAnnotation').checked;
      const searchTermsText = document.getElementById('searchTerms').value;
      
      if (!pdfFile) {
        showError('Выберите PDF файл');
        return;
      }
      
      const searchTerms = searchTermsText
        .split('\\n')
        .map(t => t.trim())
        .filter(t => t);
      
      // Показываем загрузку
      document.getElementById('loading').style.display = 'block';
      document.getElementById('error').style.display = 'none';
      document.getElementById('results').classList.remove('active');
      
      try {
        const response = await fetch('/api/pdf-bbox', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            pdf_file: pdfFile,
            terms: searchTerms,
            annotation: findAnnotation
          })
        });
        
        const data = await response.json();
        
        document.getElementById('loading').style.display = 'none';
        
        if (!response.ok) {
          showError(data.error || 'Ошибка при поиске блоков');
          return;
        }
        
        if (data.success) {
          if (data.blocks && data.blocks.length > 0) {
            displayResults(data.blocks);
          } else {
            showError(data.message || 'Блоки не найдены');
          }
        } else {
          showError(data.message || 'Блоки не найдены');
        }
      } catch (error) {
        document.getElementById('loading').style.display = 'none';
        showError('Ошибка при отправке запроса: ' + error.message);
      }
    });

    function displayResults(blocks) {
      const container = document.getElementById('blocksContainer');
      container.innerHTML = '';
      
      blocks.forEach((block, index) => {
        const blockDiv = document.createElement('div');
        blockDiv.className = 'block-item';
        
        const bbox = block.expanded_bbox || block.bbox;
        const bboxStr = `(${bbox[0].toFixed(2)}, ${bbox[1].toFixed(2)}, ${bbox[2].toFixed(2)}, ${bbox[3].toFixed(2)})`;
        
        const blockTitle = block.term || ('Блок ' + (index + 1));
        const blockTextHtml = block.text ? 
          '<div class="block-text"><strong>Текст блока:</strong><br>' + escapeHtml(block.text) + '</div>' : '';
        
        blockDiv.innerHTML = 
          '<div class="block-header">' +
            '<div>' +
              '<div class="block-title">' + blockTitle + '</div>' +
              '<div class="block-meta">Страница: ' + block.page + '</div>' +
            '</div>' +
          '</div>' +
          '<div class="bbox-info">' +
            '<strong>Координаты bbox (расширенный):</strong>' +
            '<div style="margin-top: 10px; display: flex; align-items: center;">' +
              '<code id="bbox-' + index + '" style="flex: 1; padding: 8px; background: white; border-radius: 4px; border: 1px solid #ddd;">' + bboxStr + '</code>' +
              '<button class="copy-btn" onclick="copyToClipboard(&quot;bbox-' + index + '&quot;)">📋 Копировать</button>' +
            '</div>' +
            '<div class="bbox-coords" style="margin-top: 10px;">' +
              '<div class="bbox-coord"><strong>x0:</strong> ' + bbox[0].toFixed(2) + '</div>' +
              '<div class="bbox-coord"><strong>y0 (top):</strong> ' + bbox[1].toFixed(2) + '</div>' +
              '<div class="bbox-coord"><strong>x1:</strong> ' + bbox[2].toFixed(2) + '</div>' +
              '<div class="bbox-coord"><strong>y1 (bottom):</strong> ' + bbox[3].toFixed(2) + '</div>' +
            '</div>' +
          '</div>' +
          blockTextHtml;
        
        container.appendChild(blockDiv);
      });
      
      document.getElementById('results').classList.add('active');
    }

    function copyToClipboard(elementId) {
      const element = document.getElementById(elementId);
      const text = element.textContent;
      
      navigator.clipboard.writeText(text).then(() => {
        const btn = event.target;
        const originalText = btn.textContent;
        btn.textContent = '✓ Скопировано';
        btn.style.background = '#4caf50';
        setTimeout(() => {
          btn.textContent = originalText;
          btn.style.background = '#4caf50';
        }, 2000);
      }).catch(err => {
        alert('Не удалось скопировать: ' + err);
      });
    }

    function showError(message) {
      const errorDiv = document.getElementById('error');
      errorDiv.textContent = message;
      errorDiv.style.display = 'block';
    }

    function clearResults() {
      document.getElementById('results').classList.remove('active');
      document.getElementById('blocksContainer').innerHTML = '';
      document.getElementById('error').style.display = 'none';
      document.getElementById('bboxForm').reset();
      document.getElementById('termsGroup').style.opacity = '1';
      document.getElementById('termsGroup').style.pointerEvents = 'auto';
    }

    function escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }
  </script>
</body>
</html>
"""

PDF_SELECT_TEMPLATE = ""  # Отключено, страница удалена
"""
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Выделение областей в PDF</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      padding: 20px;
      min-height: 100vh;
    }
    .container {
      max-width: 1400px;
      margin: 0 auto;
      background: white;
      border-radius: 8px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.2);
      padding: 20px;
    }
    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      border-radius: 8px;
      margin-bottom: 20px;
      text-align: center;
    }
    .header h1 {
      font-size: 24px;
      margin-bottom: 10px;
    }
    .header-actions {
      margin-top: 15px;
    }
    .header-btn {
      background: rgba(255,255,255,0.2);
      color: white;
      border: 1px solid rgba(255,255,255,0.3);
      padding: 8px 16px;
      border-radius: 6px;
      text-decoration: none;
      font-size: 14px;
      display: inline-block;
      margin: 0 5px;
      transition: all 0.2s;
    }
    .header-btn:hover {
      background: rgba(255,255,255,0.3);
    }
    .toolbar {
      display: flex;
      gap: 10px;
      margin-bottom: 20px;
      flex-wrap: wrap;
      align-items: center;
    }
    .btn {
      padding: 10px 20px;
      border: none;
      border-radius: 4px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }
    .btn-primary {
      background: #2196f3;
      color: white;
    }
    .btn-primary:hover {
      background: #1976d2;
    }
    .btn-success {
      background: #4caf50;
      color: white;
    }
    .btn-success:hover {
      background: #45a049;
    }
    .btn-warning {
      background: #ff9800;
      color: white;
    }
    .btn-warning:hover {
      background: #f57c00;
    }
    .btn-secondary {
      background: #e0e0e0;
      color: #333;
    }
    .btn-secondary:hover {
      background: #d0d0d0;
    }
    .main-content {
      display: flex;
      gap: 20px;
      min-height: 600px;
    }
    .pdf-panel {
      flex: 1;
      background: #f5f5f5;
      border-radius: 6px;
      padding: 15px;
      position: relative;
    }
    .pdf-viewer-container {
      position: relative;
      border: 2px solid #ddd;
      border-radius: 4px;
      overflow: auto;
      background: #e5e5e5;
      max-height: 95vh;
      min-height: 600px;
    }
    .pdf-bbox-toolbar {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 10px;
      font-size: 12px;
      color: #444;
    }
    .pdf-bbox-toolbar .bbox-active-field {
      font-weight: 600;
      color: #1e88e5;
    }
    .pdf-bbox-toolbar .bbox-btn {
      border: 1px solid #667eea;
      background: #fff;
      color: #667eea;
      border-radius: 4px;
      padding: 6px 10px;
      cursor: pointer;
      font-size: 12px;
    }
    .pdf-bbox-toolbar .bbox-btn:hover {
      background: #667eea;
      color: #fff;
    }
    .bbox-overlay {
      position: absolute;
      /* left, top, width, height устанавливаются в JS */
      z-index: 50;
      pointer-events: auto;
      cursor: crosshair;
      box-sizing: border-box;
    }
    .bbox-rect {
      position: absolute;
      border: 2px solid #1e88e5;
      background: rgba(30, 136, 229, 0.15);
      box-sizing: border-box;
    }
    .bbox-rect.active {
      box-shadow: 0 0 0 2px #000;
      z-index: 1000;
    }
    .bbox-rect .bbox-label {
      position: absolute;
      top: -18px;
      left: 0;
      font-size: 10px;
      padding: 2px 6px;
      border-radius: 4px;
      background: rgba(30, 136, 229, 0.9);
      color: #fff;
      white-space: nowrap;
    }
    .bbox-rect.temp {
      border-style: dashed;
      background: rgba(30, 136, 229, 0.08);
    }
    #pdfViewer {
      width: 100%;
      min-height: 600px;
      display: block;
    }
    .pdf-page {
      margin: 10px auto;
      box-shadow: 0 2px 8px rgba(0,0,0,0.2);
      background: white;
      position: relative;
    }
    .pdf-page canvas {
      display: block;
      cursor: crosshair;
    }
    .selection-overlay {
      position: absolute;
      border: 2px dashed red;
      background: rgba(255, 0, 0, 0.1);
      pointer-events: none;
    }
    .results-panel {
      width: 400px;
      background: #fafafa;
      border-radius: 6px;
      padding: 15px;
      display: flex;
      flex-direction: column;
    }
    .results-panel h3 {
      margin-bottom: 15px;
      color: #333;
      font-size: 16px;
    }
    .text-output {
      flex: 1;
      min-height: 300px;
      padding: 10px;
      border: 1px solid #ddd;
      border-radius: 4px;
      background: white;
      font-family: 'Courier New', monospace;
      font-size: 13px;
      line-height: 1.6;
      overflow-y: auto;
      white-space: pre-wrap;
      word-wrap: break-word;
    }
    .selections-list {
      margin-top: 15px;
      max-height: 200px;
      overflow-y: auto;
      border: 1px solid #ddd;
      border-radius: 4px;
      background: white;
    }
    .selection-item {
      padding: 8px;
      border-bottom: 1px solid #eee;
      font-size: 12px;
      cursor: pointer;
    }
    .selection-item:hover {
      background: #f0f0f0;
    }
    .selection-item:last-child {
      border-bottom: none;
    }
    .instructions {
      background: #fff3cd;
      border: 1px solid #ffc107;
      border-radius: 4px;
      padding: 12px;
      margin-bottom: 12px;
    }
    .instructions h4 {
      margin-bottom: 8px;
      color: #856404;
      font-size: 14px;
    }
    .instructions ul {
      margin-left: 18px;
      color: #856404;
      font-size: 12px;
    }
    .instructions li {
      margin: 4px 0;
    }
    .search-box {
      margin-bottom: 12px;
    }
    .search-box input {
      width: 100%;
      padding: 8px 10px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 12px;
    }
    .field-panel {
      margin-top: 15px;
      border-top: 1px solid #e0e0e0;
      padding-top: 15px;
    }
    .field-buttons {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-bottom: 10px;
    }
    .field-btn {
      padding: 6px 10px;
      border: 1px solid #667eea;
      background: #fff;
      color: #667eea;
      border-radius: 4px;
      cursor: pointer;
      font-size: 12px;
      transition: all 0.2s;
    }
    .field-btn.active {
      background: #667eea;
      color: #fff;
    }
    .field-blocks {
      max-height: 260px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .field-block {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .field-block label {
      font-size: 12px;
      color: #333;
      font-weight: 600;
    }
    .field-block textarea {
      width: 100%;
      min-height: 60px;
      padding: 8px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 12px;
      font-family: inherit;
      resize: vertical;
      background: #fff;
    }
    .status-bar {
      margin-top: 15px;
      padding: 10px;
      background: #e3f2fd;
      border-radius: 4px;
      font-size: 12px;
      color: #1976d2;
    }
    .loading {
      text-align: center;
      padding: 40px;
      color: #666;
    }
    .error {
      background: #ffebee;
      border: 1px solid #f44336;
      color: #c62828;
      padding: 15px;
      border-radius: 4px;
      margin-top: 20px;
    }
    .form-group {
      margin-bottom: 15px;
    }
    .form-group label {
      display: block;
      font-weight: 600;
      margin-bottom: 8px;
      color: #333;
      font-size: 14px;
    }
    .form-group select {
      width: 100%;
      padding: 10px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 14px;
      font-family: inherit;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>📄 Выделение областей в PDF</h1>
      <p>Выделите области мышью и извлеките текст напрямую из PDF</p>
      <div class="header-actions">
        <a href="/" class="header-btn">← К списку</a>
      </div>
    </div>

    <div class="toolbar">
      <div class="form-group" style="margin: 0; min-width: 300px;">
        <label for="pdfFile" style="margin-bottom: 5px;">Выберите PDF файл:</label>
        <div style="display: flex; gap: 5px; align-items: center;">
          <select id="pdfFile" name="pdf_file" style="flex: 1; padding: 5px; font-size: 14px; cursor: pointer;">
            {% if pdf_files %}
              <option value="">-- Выберите PDF файл --</option>
              {% for file in pdf_files %}
                <option value="{{ file|e }}">{{ file }}</option>
              {% endfor %}
            {% else %}
              <option value="" disabled>-- PDF файлы не найдены --</option>
            {% endif %}
          </select>
          <button type="button" id="btnReloadPdfFiles" style="padding: 5px 10px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer; white-space: nowrap;" title="Обновить список файлов">
            🔄
          </button>
        </div>
      </div>
      <button class="btn btn-primary" onclick="window.loadPdf && window.loadPdf()">📁 Загрузить PDF</button>
      <button class="btn btn-secondary" onclick="window.prevPage && window.prevPage()">◀ Предыдущая</button>
      <span id="pageLabel" style="padding: 0 10px; line-height: 38px;">Страница: 0/0</span>
      <button class="btn btn-secondary" onclick="window.nextPage && window.nextPage()">Следующая ▶</button>
      <button class="btn btn-success" onclick="window.extractText && window.extractText()">📝 Извлечь текст</button>
      <button class="btn btn-warning" onclick="window.saveCoordinates && window.saveCoordinates()">💾 Сохранить координаты</button>
      <button class="btn btn-secondary" onclick="window.clearSelections && window.clearSelections()">🗑 Очистить</button>
    </div>

    <div id="loading" class="loading" style="display: none;">
      <p>⏳ Загрузка PDF...</p>
    </div>

    <div id="error" class="error" style="display: none;"></div>

    <div id="mainContent" class="main-content" style="display: none;">
      <div id="pdfPanel" class="pdf-panel{% if view_mode != 'pdf' %} panel-hidden{% endif %}">
        <div class="pdf-viewer-container" id="pdfViewerContainer">
          <div id="pdfViewer"></div>
        </div>
      </div>
      <div class="results-panel">
        <div class="search-box">
          <input id="fieldSearch" type="text" placeholder="Поиск по полям">
        </div>
        
        <h3>Извлеченный текст:</h3>
        <div class="field-panel">
          <h3>Поля</h3>
          <div id="fieldButtons" class="field-buttons"></div>
          <div id="fieldBlocks" class="field-blocks"></div>
        </div>
        <h3 style="margin-top: 15px;">Выделенные области:</h3>
        <div id="selectionsList" class="selections-list"></div>
        <div id="statusBar" class="status-bar">Готов к работе</div>
      </div>
    </div>
  </div>

  <script src="/static/pdf-select.js"></script>
</body>
</html>
"""

VIEWER_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ filename }}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: #f5f5f5;
      padding: 20px;
    }
    .container {
      max-width: 1200px;
      margin: 0 auto;
      background: white;
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.1);
      overflow: hidden;
    }
    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px 30px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .header h1 {
      font-size: 20px;
      font-weight: 500;
    }
    .header-actions {
      display: flex;
      gap: 10px;
    }
    .view-toggle {
      display: flex;
      gap: 8px;
    }
    .toggle-btn {
      background: rgba(255,255,255,0.2);
      color: white;
      border: 1px solid rgba(255,255,255,0.3);
      padding: 8px 12px;
      border-radius: 6px;
      text-decoration: none;
      font-size: 13px;
      transition: all 0.2s;
    }
    .toggle-btn.active {
      background: rgba(255,255,255,0.35);
      border-color: rgba(255,255,255,0.6);
    }
    .back-btn, .markup-btn {
      background: rgba(255,255,255,0.2);
      color: white;
      border: 1px solid rgba(255,255,255,0.3);
      padding: 8px 16px;
      border-radius: 6px;
      text-decoration: none;
      font-size: 14px;
      transition: all 0.2s;
      cursor: pointer;
    }
    .back-btn:hover, .markup-btn:hover {
      background: rgba(255,255,255,0.3);
    }
    .markup-btn {
      background: rgba(76, 175, 80, 0.8);
    }
    .markup-btn:hover {
      background: rgba(76, 175, 80, 1);
    }
    .viewer-content {
      padding: 30px;
      max-width: 900px;
      margin: 0 auto;
      line-height: 1.8;
      color: #333;
    }
    .viewer-content p {
      margin: 1em 0;
      text-align: justify;
    }
    .viewer-content blockquote {
      border-left: 4px solid #3498db;
      margin: 1em 0;
      padding-left: 1em;
      color: #555;
      font-style: italic;
    }
    .viewer-content h1, .viewer-content h2, .viewer-content h3,
    .viewer-content h4, .viewer-content h5, .viewer-content h6 {
      margin-top: 1.5em;
      margin-bottom: 0.5em;
      color: #2c3e50;
    }
    .viewer-content ul,
    .viewer-content ol {
      margin: 0.8em 0 0.8em 1.6em;
    }
    .viewer-content li {
      margin: 0.3em 0;
    }
    .viewer-content .table-wrap {
      overflow-x: auto;
    }
    .viewer-content table {
      width: 100%;
      border-collapse: collapse;
      margin: 1em 0;
      font-size: 0.95em;
    }
    .viewer-content table.docx-table {
      min-width: 100%;
    }
    .viewer-content th,
    .viewer-content td {
      border: 1px solid #d9dbe2;
      padding: 6px 8px;
      vertical-align: top;
    }
    .viewer-content thead th {
      background: #f2f4f8;
      font-weight: 600;
    }
    .viewer-content sup {
      font-size: 0.7em;
      vertical-align: super;
    }
    .viewer-content sub {
      font-size: 0.7em;
      vertical-align: sub;
    }
    .viewer-content em {
      font-style: italic;
    }
    .viewer-content strong {
      font-weight: 600;
    }
    .viewer-content .underline {
      text-decoration: underline;
    }
    .viewer-content .small-caps {
      font-variant: small-caps;
      letter-spacing: 0.02em;
    }
    .viewer-content .caption {
      color: #5c6370;
      font-size: 0.9em;
    }
    .viewer-content .list-paragraph {
      margin-left: 1.2em;
    }
    .viewer-content code {
      font-family: Consolas, Monaco, monospace;
      background: #f4f6f8;
      border: 1px solid #e2e6ee;
      border-radius: 3px;
      padding: 0 4px;
    }
    .viewer-pdf {
      padding: 30px;
    }
    .viewer-iframe {
      width: 100%;
      height: 95vh;
      border: 1px solid #ddd;
      border-radius: 8px;
      background: #fff;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>{{ filename }}</h1>
      <div class="header-actions">
        <div class="view-toggle">
          <a href="{{ html_url }}" class="toggle-btn {% if view_mode == 'html' %}active{% endif %}">HTML</a>
          {% if pdf_url %}
            <a href="{{ pdf_view_url }}" class="toggle-btn {% if view_mode == 'pdf' %}active{% endif %}">PDF</a>
          {% endif %}
        </div>
        <a href="/markup/{{ filename }}" class="markup-btn">📝 Разметить метаданные</a>
        <a href="/" class="back-btn">← Назад к списку</a>
      </div>
    </div>
    {% if view_mode == 'pdf' and pdf_url %}
      <div class="viewer-pdf">
        <iframe class="viewer-iframe" src="{{ pdf_url }}"></iframe>
      </div>
    {% else %}
      <div class="viewer-content">
        {{ content|safe }}
      </div>
    {% endif %}
  </div>
</body>
</html>
"""

MARKUP_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Разметка метаданных - {{ filename }}</title>
  <!-- PDF.js для отображения PDF -->
  <script src="/static/pdf.min.js" 
          onerror="console.error('Ошибка загрузки PDF.js из CDN')"></script>
  <style>
    *{margin:0;padding:0;box-sizing:border-box;}
    body{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:#f5f5f5;padding:20px;}
    .container{max-width:1400px;margin:0 auto;background:white;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1);}
    .header{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;padding:20px;text-align:center;}
    .header h1{font-size:24px;margin-bottom:5px;}
    .header p{opacity:.9;}
    .header-actions{display:flex;gap:10px;justify-content:center;margin-top:10px;}
    .header-btn{background:rgba(255,255,255,0.2);color:white;border:1px solid rgba(255,255,255,0.3);padding:8px 16px;border-radius:6px;text-decoration:none;font-size:14px;transition:all 0.2s;}
    .header-btn:hover{background:rgba(255,255,255,0.3);}
    .header-toggle-btn{cursor:pointer;background:rgba(255,255,255,0.2);}
    .header-toggle-btn.active{background:rgba(255,255,255,0.45);color:#fff;}
    .header-toggle-btn[disabled]{opacity:0.5;cursor:default;}
    .panel-hidden{display:none !important;}
    .content{display:flex;min-height:calc(100vh - 200px);}
    .pdf-panel{flex:1;min-width:0;padding:20px;overflow-y:auto;max-height:calc(100vh - 200px);border-right:1px solid #e0e0e0;background:#f5f5f5;display:flex;flex-direction:column;}
    .pdf-viewer-container{flex:1;border:2px solid #ddd;border-radius:4px;overflow:auto;background:#e5e5e5;min-height:400px;position:relative;}
    .pdf-tabs{display:flex;gap:8px;margin-bottom:10px;}
    .pdf-tab-btn{padding:6px 12px;border:1px solid #667eea;background:#fff;color:#667eea;border-radius:4px;cursor:pointer;font-size:12px;transition:all .2s;}
    .pdf-tab-btn.active{background:#667eea;color:#fff;}
    .pdf-tab-content{display:block;}
    .pdf-tab-content.hidden{display:none;}
    .pdf-iframe{width:100%;height:80vh;border:none;background:#fff;border-radius:4px;}

    #pdfViewerIframe{width:100%;height:95vh;border:none;display:block;}
    .pdf-page-markup{margin:10px auto;box-shadow:0 2px 8px rgba(0,0,0,0.2);background:white;position:relative;overflow:hidden;}
    .pdf-page-markup canvas{display:block;cursor:default;}
    .pdf-page-markup .textLayer{position:absolute;inset:0;opacity:1;pointer-events:auto;color:transparent;}
    .pdf-page-markup .textLayer span{position:absolute;transform-origin:0 0;white-space:pre;}
    .text-panel{flex:1;min-width:0;padding:20px;overflow-y:auto;max-height:calc(100vh - 200px);border-right:1px solid #e0e0e0;}
    .form-panel{width:420px;flex:0 0 420px;padding:20px;overflow-y:auto;max-height:calc(100vh - 200px);background:#fafafa;}

    .search-box{margin-bottom:20px;}
    .search-box input{width:100%;padding:10px;border:1px solid #ddd;border-radius:4px;font-size:14px;}

    .line{padding:8px 12px;margin:2px 0;border-radius:4px;cursor:pointer;transition:all .2s;border-left:3px solid transparent;font-size:14px;line-height:1.5;user-select:none;position:relative;display:flex;align-items:center;gap:10px;}
    .line:hover{background:#f0f0f0;border-left-color:#667eea;}
    .line.selected{background:#e3f2fd !important;border-left-color:#2196f3 !important;font-weight:500;}
    .line-number{display:inline-block;width:50px;color:#999;font-size:12px;flex-shrink:0;}
    .line-text{flex:1;padding-right:20px;}
    .line-copy-btn{position:absolute;right:8px;top:50%;transform:translateY(-50%);opacity:0;transition:opacity .2s,transform .2s;background:rgba(211,47,47,0.1);border:none;padding:2px;margin:0;cursor:pointer;font-size:16px;width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;line-height:1;z-index:10;border-radius:3px;color:#d32f2f;}
    .line:hover .line-copy-btn{opacity:0.9;background:rgba(211,47,47,0.15);}
    .line-copy-btn:hover{opacity:1 !important;background:rgba(211,47,47,0.25);transform:translateY(-50%) scale(1.2);color:#b71c1c;}
    
    .line-editor-modal{display:none;position:fixed;z-index:2000;left:0;top:0;width:100%;height:100%;background:rgba(0,0,0,0.5);overflow:auto;}
    .line-editor-modal.active{display:flex;align-items:center;justify-content:center;}
    .line-editor-content{background:#fff;padding:20px;border-radius:8px;max-width:700px;width:80%;max-height:70vh;box-shadow:0 4px 20px rgba(0,0,0,0.3);}
    .line-editor-content.resizable{resize:both;overflow:auto;min-width:320px;min-height:200px;width:80vw;height:60vh;max-width:95vw;max-height:90vh;}
    .line-editor-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;border-bottom:2px solid #e0e0e0;padding-bottom:10px;}
    .line-editor-header h2{margin:0;color:#333;font-size:18px;}
    .line-editor-textarea{width:100%;min-height:150px;max-height:400px;padding:12px;border:2px solid #ddd;border-radius:4px;font-size:14px;font-family:inherit;line-height:1.6;resize:vertical;background:#f9f9f9;}
    .line-editor-textarea:focus{outline:none;border-color:#667eea;background:#fff;}
    .line-editor-actions{display:flex;justify-content:flex-end;gap:10px;margin-top:15px;padding-top:15px;border-top:1px solid #e0e0e0;}

    .instructions{background:#2f3342;border:1px solid #3a3f52;border-radius:8px;padding:15px;margin-bottom:20px;color:#c6cbe0;}
    .instructions h3{margin-bottom:10px;color:#e6e8ee;}
    .instructions ul{margin-left:20px;color:#c6cbe0;}
    .instructions li{margin:5px 0;}

    .field-group{margin-bottom:20px;}
    .field-group label{display:block;font-weight:600;margin-bottom:8px;color:#333;font-size:14px;}
    .field-group input,.field-group textarea{width:100%;padding:10px;border:1px solid #d6dae3;border-radius:4px;font-size:14px;font-family:inherit;background:#f1f3f8;}
    .field-group textarea{min-height:80px;resize:vertical;}
    .selected-lines{margin-top:5px;font-size:12px;color:#666;}
    .keywords-count{margin-top:5px;font-size:12px;color:#666;font-style:italic;}
    .field-group.active{background:#e3f2fd;border:2px solid #2196f3;border-radius:4px;padding:10px;}

    .buttons{display:flex;gap:10px;margin-top:20px;}
    button{flex:1;padding:12px;border:none;border-radius:4px;font-size:14px;font-weight:600;cursor:pointer;transition:all .2s;}
    .btn-secondary{background:#e0e0e0;color:#333;}
    .btn-secondary:hover{background:#d0d0d0;}
    .btn-success{background:#4caf50;color:#fff;}
    .btn-success:hover{background:#45a049;}

    .selection-panel{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#fff;border:2px solid #667eea;border-radius:8px;padding:15px 20px;box-shadow:0 4px 20px rgba(0,0,0,0.2);z-index:1000;display:none;min-width:400px;max-width:calc(100vw - 24px);cursor:grab;}
    .selection-panel.active{display:block;}
    .selection-panel h4{margin:0 0 10px 0;color:#667eea;font-size:14px;}
    .selection-panel.dragging{cursor:grabbing;user-select:none;}
    .field-buttons{display:flex;flex-wrap:wrap;gap:8px;}
    .field-btn{padding:8px 12px;border:1px solid #667eea;background:#fff;color:#667eea;border-radius:4px;cursor:pointer;font-size:12px;transition:all .2s;}
    .field-btn:hover{background:#667eea;color:#fff;}
    
    .view-refs-btn{background:#2196f3;color:#fff;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;font-size:12px;margin-top:5px;transition:all .2s;}
    .view-refs-btn:hover{background:#1976d2;}
    
    .modal{display:none;position:fixed;z-index:2000;left:0;top:0;width:100%;height:100%;background:transparent;overflow:auto;pointer-events:none;}
    .modal.active{display:flex;align-items:center;justify-content:center;}
    .modal-content{background:#fff;padding:30px;border-radius:8px;max-width:800px;width:90%;max-height:80vh;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.3);pointer-events:auto;display:flex;flex-direction:column;position:relative;}
    .refs-modal-content{overflow-y:auto;}
    .refs-modal-content,
    .refs-modal-content .ref-text,
    .refs-modal-content .ref-text[contenteditable="true"]{font-family:"Segoe UI","Segoe UI Symbol","Arial Unicode MS",Arial,sans-serif;}
    .annotation-modal-content{height:80vh;min-height:0;}
    .modal-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;border-bottom:2px solid #e0e0e0;padding-bottom:15px;cursor:move;}
    .modal-header h2{margin:0;color:#333;font-size:20px;}
    .modal-close{background:none;border:none;font-size:28px;cursor:pointer;color:#999;padding:0;width:30px;height:30px;line-height:30px;text-align:center;}
    .modal-close:hover{color:#333;}
    .modal-resize-handle{position:absolute;z-index:15;user-select:none;touch-action:none;}
    .modal-resize-handle.n{top:-5px;left:10px;right:10px;height:10px;cursor:ns-resize;}
    .modal-resize-handle.s{bottom:-5px;left:10px;right:10px;height:10px;cursor:ns-resize;}
    .modal-resize-handle.e{top:10px;right:-5px;bottom:10px;width:10px;cursor:ew-resize;}
    .modal-resize-handle.w{top:10px;left:-5px;bottom:10px;width:10px;cursor:ew-resize;}
    .modal-resize-handle.ne{top:-6px;right:-6px;width:12px;height:12px;cursor:nesw-resize;}
    .modal-resize-handle.nw{top:-6px;left:-6px;width:12px;height:12px;cursor:nwse-resize;}
    .modal-resize-handle.se{bottom:-6px;right:-6px;width:12px;height:12px;cursor:nwse-resize;}
    .modal-resize-handle.sw{bottom:-6px;left:-6px;width:12px;height:12px;cursor:nesw-resize;}
    .refs-list{margin:0;padding:0;}
    .ref-item{background:#f8f9fa;border-left:4px solid #2196f3;padding:15px;margin-bottom:10px;border-radius:4px;line-height:1.6;position:relative;}
    .ref-number{display:inline-block;width:30px;font-weight:600;color:#2196f3;vertical-align:top;}
    .ref-text{margin-left:35px;color:#333;min-height:24px;line-height:1.7;padding:3px 0;display:block;overflow:visible;}
    .ref-text[contenteditable="true"]{outline:2px solid #2196f3;outline-offset:2px;padding:8px 10px 10px;border-radius:4px;background:#fff;cursor:text;line-height:1.7;overflow:visible;}
    .ref-text[contenteditable="true"]:focus{background:#fff;box-shadow:0 0 0 3px rgba(33,150,243,0.2);}
    .modal-footer{display:flex;justify-content:flex-end;gap:10px;margin-top:20px;padding-top:20px;border-top:2px solid #e0e0e0;}
    .modal-btn{padding:10px 20px;border:none;border-radius:4px;cursor:pointer;font-size:14px;font-weight:600;transition:all .2s;}
    .modal-btn-save{background:#4caf50;color:#fff;}
    .modal-btn-save:hover{background:#45a049;}
    .modal-btn-cancel{background:#e0e0e0;color:#333;}
    .modal-btn-cancel:hover{background:#d0d0d0;}
    .ref-actions{position:absolute;top:5px;right:5px;display:flex;gap:5px;}
    .ref-action-btn{background:#fff;border:1px solid #ddd;padding:4px 8px;border-radius:3px;cursor:pointer;font-size:11px;color:#666;}
    .ref-action-btn:hover{background:#f0f0f0;color:#333;}
    .ref-action-btn.delete{color:#d32f2f;border-color:#d32f2f;}
    .ref-action-btn.delete:hover{background:#ffebee;}
    .ref-action-btn.merge{color:#2196f3;border-color:#2196f3;}
    .ref-action-btn.merge:hover{background:#e3f2fd;}
    
    .author-item{margin-bottom:10px;border:1px solid #ddd;border-radius:4px;overflow:hidden;}
    .author-header{display:flex;justify-content:space-between;align-items:center;padding:12px 15px;background:#f8f9fa;cursor:pointer;transition:background .2s;}
    .author-header:hover{background:#e9ecef;}
    .author-name{font-weight:600;color:#333;font-size:14px;}
    .author-toggle{color:#666;font-size:12px;transition:transform .2s;}
    .author-item.expanded .author-toggle{transform:rotate(180deg);}
    .author-actions{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;gap:10px;}
    .author-field textarea.author-textarea{min-height:54px;resize:vertical;}
    .author-collapse-actions{display:flex;justify-content:flex-end;margin-top:12px;}
    .author-collapse-btn{background:#e0e0e0;color:#333;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;font-size:12px;transition:all .2s;}
    .author-collapse-btn:hover{background:#d0d0d0;}
    .author-actions label{margin:0;flex:1;}
    .add-author-btn{background:#667eea;color:#fff;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;font-size:12px;transition:all .2s;display:inline-flex;align-items:center;gap:4px;white-space:nowrap;}
    .add-author-btn:hover{background:#5568d3;}
    .delete-author-btn{background:#d32f2f;color:#fff;border:none;padding:4px 8px;border-radius:3px;cursor:pointer;font-size:11px;transition:all .2s;min-width:24px;height:24px;display:inline-flex;align-items:center;justify-content:center;}
    .delete-author-btn:hover{background:#b71c1c;}
    .author-details{padding:15px;background:#fff;border-top:1px solid #e0e0e0;}
    .author-section{margin-bottom:20px;}
    .author-section:last-child{margin-bottom:0;}
    .author-section h4{margin:0 0 12px 0;color:#667eea;font-size:14px;font-weight:600;border-bottom:1px solid #e0e0e0;padding-bottom:5px;}
    .author-field{margin-bottom:10px;}
    .author-field label{display:block;font-size:12px;color:#666;margin-bottom:4px;font-weight:500;}
    .author-field input,.author-field textarea{width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;font-size:13px;font-family:inherit;}
    .author-field input:focus,.author-field textarea:focus{outline:2px solid #667eea;outline-offset:2px;border-color:#667eea;}
    .author-field textarea.author-textarea{min-height:54px;resize:vertical;}
    .author-org-toolbar{display:flex;justify-content:flex-end;margin-bottom:8px;}
    .author-org-list{display:flex;flex-direction:column;gap:10px;}
    .author-org-card{border:1px solid #d9dfec;border-radius:8px;background:#f8faff;padding:12px;}
    .author-org-card-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;}
    .author-org-card-title{font-size:14px;font-weight:700;color:#2f3a5a;}
    .author-org-card-actions{display:flex;gap:8px;}
    .author-org-action-btn{
      border:1px solid #c8d2e8;
      background:#fff;
      color:#334;
      min-width:34px;
      height:30px;
      border-radius:8px;
      cursor:pointer;
      font-size:15px;
      font-weight:500;
      line-height:1;
      display:inline-flex;
      align-items:center;
      justify-content:center;
      padding:0;
      font-family:"Segoe UI Symbol","Segoe UI",sans-serif;
    }
    .author-org-action-btn:hover{background:#eef3ff;}
    .author-org-line{display:flex;align-items:flex-start;gap:8px;margin-bottom:8px;}
    .author-org-line:last-child{margin-bottom:0;}
    .author-org-label{min-width:34px;padding-top:7px;font-size:12px;font-weight:700;color:#2f3a5a;}
    .author-org-value{flex:1;min-height:40px;resize:none;background:#fff;line-height:1.35;}
    .author-org-addresses{margin-top:8px;border-top:1px dashed #cfd8ea;padding-top:8px;}
    .author-org-addresses summary{cursor:pointer;font-size:12px;color:#4b5878;font-weight:600;user-select:none;}
    .author-org-addresses summary:hover{color:#2f3a5a;}
    .author-org-address-wrap{margin-top:8px;}
    .correspondence-toggle{margin-top:5px;}
    .toggle-label{display:flex;align-items:center;gap:8px;cursor:pointer;}
    .toggle-label input[type="checkbox"]{width:18px;height:18px;cursor:pointer;}
    .toggle-text{font-size:14px;color:#333;}
  </style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Разметка метаданных</h1>
    <p>{{ filename }}</p>
    {% if is_common_file and common_file_name %}
    <p style="font-size: 12px; opacity: 0.9; margin-top: 5px;">
      ⚠️ Используется общий файл выпуска: <strong>{{ common_file_name }}</strong><br>
      <span style="font-size: 11px;">В тексте показано содержимое всего выпуска. Выделяйте нужные фрагменты для данной статьи.</span>
    </p>
    {% endif %}
    <div class="header-actions">
      <button type="button" class="header-btn header-toggle-btn{% if view_mode == 'html' %} active{% endif %}" data-view="html">HTML</button>
      <button type="button" class="header-btn header-toggle-btn{% if view_mode == 'pdf' %} active{% endif %}" data-view="pdf"{% if not show_pdf_viewer %} disabled{% endif %}>PDF</button>
      <a href="/" class="header-btn">← К списку</a>
    </div>
  </div>

  <div class="content">
    {% if show_pdf_viewer and pdf_path %}
    <div id="pdfPanel" class="pdf-panel{% if view_mode != 'pdf' %} panel-hidden{% endif %}">
      <h3 style="margin-bottom: 10px; color: #333;">PDF просмотр:</h3>
      <div class="pdf-bbox-toolbar">
        <span>Поле для bbox:</span>
        <span id="bboxActiveField" class="bbox-active-field">не выбрано</span>
        <button type="button" id="bboxClearBtn" class="bbox-btn">Очистить bbox на странице</button>
      </div>
      <div class="pdf-viewer-container">
        <iframe
          id="pdfViewerIframe"
          src="/static/pdfjs/web/viewer.html?file=/pdf/{{ pdf_path|urlencode }}#zoom=page-width"
          style="width: 100%; height: 95vh; border: none;"
          title="PDF viewer"
        ></iframe>
      </div>
    </div>
    {% endif %}
    {% if show_text_panel is sameas true %}
    <div id="textPanel" class="text-panel{% if show_pdf_viewer and view_mode == 'pdf' %} panel-hidden{% endif %}">
      <div class="search-box">
        <input type="text" id="searchInput" placeholder="Поиск в тексте...">
      </div>
      <div id="textContent">
        {% for line in lines %}
          <div class="line" data-id="{{ line.id }}" data-line="{{ line.line_number }}">
            <span class="line-number">{{ line.line_number }}</span>
            <span class="line-text">{{ line.text }}</span>
            <button class="line-copy-btn" data-action="open-copy" title="Копировать фрагмент">✏️</button>
          </div>
        {% endfor %}
      </div>
    </div>
    {% endif %}

    <div class="form-panel">

      <form id="metadataForm">
        <div class="field-group">
          <label>УДК</label>
          <input type="text" id="udc" name="udc" value="{% if form_data %}{{ form_data.get('udc', '')|e }}{% endif %}">
          <div class="selected-lines" id="udc-lines"></div>
        </div>

        <div class="field-group">
          <label>Название (русский) *</label>
          <textarea id="title" name="title" required>{% if form_data %}{{ form_data.get('title', '')|e }}{% endif %}</textarea>
          <button type="button" class="view-refs-btn" onclick="viewAnnotation('title', 'Название (русский)')" style="margin-top: 5px;">👁 Просмотреть и редактировать</button>
          <div class="selected-lines" id="title-lines"></div>
        </div>

        <div class="field-group">
          <label>Название (английский)</label>
          <textarea id="title_en" name="title_en">{% if form_data %}{{ form_data.get('title_en', '')|e }}{% endif %}</textarea>
          <button type="button" class="view-refs-btn" onclick="viewAnnotation('title_en', 'Название (английский)')" style="margin-top: 5px;">👁 Просмотреть и редактировать</button>
          <div class="selected-lines" id="title_en-lines"></div>
        </div>

        <div class="field-group">
          <label>DOI</label>
          <input type="text" id="doi" name="doi" value="{% if form_data %}{{ form_data.get('doi', '')|e }}{% endif %}">
          <div class="selected-lines" id="doi-lines"></div>
          <button type="button" class="view-refs-btn" id="crossrefDoiBtn" style="margin-top: 5px;">↻ Подтянуть данные по Crossref DOI</button>
          <div class="selected-lines" id="crossrefStatus"></div>
        </div>

        <div class="field-group">
          <label>EDN</label>
          <input type="text" id="edn" name="edn" value="{% if form_data %}{{ form_data.get('edn', '')|e }}{% endif %}">
        </div>

        <div class="field-group">
          <label>ББК</label>
          <input type="text" id="bbk" name="bbk" value="{% if form_data %}{{ form_data.get('bbk', '')|e }}{% endif %}">
        </div>

        <div class="field-group">
          <label>Тип статьи</label>
          <select id="art_type" name="art_type" style="width:100%;padding:10px;border:1px solid #ddd;border-radius:4px;font-size:14px;font-family:inherit;background:#fff;">
            {% set current_art_type = (form_data.get('art_type') if form_data and form_data.get('art_type') else 'RAR') %}
            <option value="RAR" {% if current_art_type == 'RAR' %}selected{% endif %}>RAR - Исследовательская статья (по умолчанию)</option>
            <option value="REV" {% if current_art_type == 'REV' %}selected{% endif %}>REV - Обзорная статья</option>
            <option value="BRV" {% if current_art_type == 'BRV' %}selected{% endif %}>BRV - Рецензия</option>
            <option value="SCO" {% if current_art_type == 'SCO' %}selected{% endif %}>SCO - Краткое сообщение</option>
            <option value="REP" {% if current_art_type == 'REP' %}selected{% endif %}>REP - Отчет</option>
            <option value="CNF" {% if current_art_type == 'CNF' %}selected{% endif %}>CNF - Конференция</option>
            <option value="EDI" {% if current_art_type == 'EDI' %}selected{% endif %}>EDI - Редакционная статья</option>
            <option value="COR" {% if current_art_type == 'COR' %}selected{% endif %}>COR - Корреспонденция</option>
            <option value="ABS" {% if current_art_type == 'ABS' %}selected{% endif %}>ABS - Аннотация</option>
            <option value="RPR" {% if current_art_type == 'RPR' %}selected{% endif %}>RPR - Отчет о проекте</option>
            <option value="MIS" {% if current_art_type == 'MIS' %}selected{% endif %}>MIS - Разное</option>
            <option value="PER" {% if current_art_type == 'PER' %}selected{% endif %}>PER - Персоналия</option>
            <option value="UNK" {% if current_art_type == 'UNK' %}selected{% endif %}>UNK - Не определён (устаревший)</option>
          </select>
        </div>

        <div class="field-group">
          <label>Язык публикации</label>
          <select id="publ_lang" name="publ_lang" style="width:100%;padding:10px;border:1px solid #ddd;border-radius:4px;font-size:14px;font-family:inherit;background:#fff;">
            {% set current_publ_lang = (form_data.get('publ_lang') if form_data and form_data.get('publ_lang') else 'RUS') %}
            <option value="RUS" {% if current_publ_lang == 'RUS' %}selected{% endif %}>RUS - Русский</option>
            <option value="ENG" {% if current_publ_lang == 'ENG' %}selected{% endif %}>ENG - Английский</option>
          </select>
        </div>

        <div class="field-group">
          <details>
            <summary>Даты публикации</summary>
            <div style="margin-top: 10px;">
              <div class="field-group">
                <label>Дата получения</label>
                <input type="text" id="received_date" name="received_date" value="{% if form_data %}{{ form_data.get('received_date', '')|e }}{% endif %}">
              </div>
              <div class="field-group">
                <label>Дата доработки</label>
                <input type="text" id="reviewed_date" name="reviewed_date" value="{% if form_data %}{{ form_data.get('reviewed_date', '')|e }}{% endif %}">
              </div>
              <div class="field-group">
                <label>Дата принятия</label>
                <input type="text" id="accepted_date" name="accepted_date" value="{% if form_data %}{{ form_data.get('accepted_date', '')|e }}{% endif %}">
              </div>
              <div class="field-group">
                <label>Дата публикации</label>
                <input type="text" id="date_publication" name="date_publication" value="{% if form_data %}{{ form_data.get('date_publication', '')|e }}{% endif %}">
              </div>
            </div>
          </details>
        </div>

        <div class="field-group">
          <label>Страницы</label>
          <input type="text" id="pages" name="pages" value="{% if form_data %}{{ form_data.get('pages', '')|e }}{% endif %}">
        </div>

        <div class="field-group">
          <div class="author-actions">
            <label>Авторы</label>
            <button type="button" class="add-author-btn" onclick="addNewAuthor()">+ Добавить</button>
          </div>
          <div id="authors-list">
            {% if form_data and form_data.get('authors') %}
              {% for author in form_data.get('authors', []) %}
                {% set rus_info = author.get('individInfo', {}).get('RUS', {}) %}
                {% set eng_info = author.get('individInfo', {}).get('ENG', {}) %}
                {% set author_codes = rus_info.get('authorCodes', {}) %}
                <div class="author-item" data-author-index="{{ loop.index0 }}">
                  <div class="author-header" onclick="toggleAuthorDetails({{ loop.index0 }})">
                    <span class="author-name">{{ rus_info.get('surname', '') }} {{ rus_info.get('initials', '') }}</span>
                    <div style="display:flex;align-items:center;gap:10px;">
                      <span class="author-toggle">▼</span>
                      <button type="button" class="delete-author-btn" onclick="event.stopPropagation(); deleteAuthor({{ loop.index0 }})" title="Удалить автора">✕</button>
                    </div>
                  </div>
                  <div class="author-details" id="author-details-{{ loop.index0 }}" style="display:none;">
                    <div class="author-field">
                      <label>Ответственный за переписку:</label>
                      <div class="correspondence-toggle">
                        <label class="toggle-label">
                          <input type="checkbox" class="author-correspondence" data-index="{{ loop.index0 }}" {% if author.get('correspondence', False) %}checked{% endif %}>
                          <span class="toggle-text">Да</span>
                        </label>
                      </div>
                    </div>
                    <div class="author-field">
                      <label>Фамилия (русский):</label>
                      <input type="text" class="author-input" data-field="surname" data-lang="RUS" data-index="{{ loop.index0 }}" value="{{ rus_info.get('surname', '')|e }}">
                    </div>
                    <div class="author-field">
                      <label>Surname (English):</label>
                      <input type="text" class="author-input" data-field="surname" data-lang="ENG" data-index="{{ loop.index0 }}" value="{{ eng_info.get('surname', '')|e }}">
                    </div>
                    <div class="author-field">
                      <label>Инициалы (русский):</label>
                      <input type="text" class="author-input" data-field="initials" data-lang="RUS" data-index="{{ loop.index0 }}" value="{{ rus_info.get('initials', '')|e }}">
                    </div>
                    <div class="author-field">
                      <label>Initials (English):</label>
                      <input type="text" class="author-input" data-field="initials" data-lang="ENG" data-index="{{ loop.index0 }}" value="{{ eng_info.get('initials', '')|e }}">
                    </div>
                    <div class="author-field">
                      <label>Организации и адреса:</label>
                      <div class="author-org-editor"
                           data-index="{{ loop.index0 }}"
                           data-initial-org-rus="{{ rus_info.get('orgName', '')|e }}"
                           data-initial-org-eng="{{ eng_info.get('orgName', '')|e }}"
                           data-initial-address-rus="{{ rus_info.get('address', '')|e }}"
                           data-initial-address-eng="{{ eng_info.get('address', '')|e }}">
                        <div class="author-org-toolbar">
                          <button type="button" class="add-author-btn" onclick="addOrganizationCard({{ loop.index0 }})">+ Добавить организацию</button>
                        </div>
                        <div class="author-org-list" id="author-org-list-{{ loop.index0 }}"></div>
                      </div>
                      <div class="keywords-count" id="org-count-rus-{{ loop.index0 }}">Количество организаций: 0</div>
                      <div class="keywords-count" id="org-count-eng-{{ loop.index0 }}">Количество организаций: 0</div>
                      <textarea class="author-input author-textarea org-hidden" data-field="orgName" data-lang="RUS" data-index="{{ loop.index0 }}" rows="2" style="display:none;">{{ rus_info.get('orgName', '')|e }}</textarea>
                      <textarea class="author-input author-textarea org-hidden" data-field="orgName" data-lang="ENG" data-index="{{ loop.index0 }}" rows="2" style="display:none;">{{ eng_info.get('orgName', '')|e }}</textarea>
                      <input type="text" class="author-input org-hidden" data-field="address" data-lang="RUS" data-index="{{ loop.index0 }}" value="{{ rus_info.get('address', '')|e }}" style="display:none;">
                      <input type="text" class="author-input org-hidden" data-field="address" data-lang="ENG" data-index="{{ loop.index0 }}" value="{{ eng_info.get('address', '')|e }}" style="display:none;">
                    </div>
                    <div class="author-field">
                      <label>Email:</label>
                      <input type="email" class="author-input" data-field="email" data-lang="RUS" data-index="{{ loop.index0 }}" value="{{ rus_info.get('email', '')|e }}">
                    </div>
                    <div class="author-field">
                      <label>Дополнительная информация (русский):</label>
                      <textarea class="author-input" data-field="otherInfo" data-lang="RUS" data-index="{{ loop.index0 }}" rows="2">{{ rus_info.get('otherInfo', '')|e }}</textarea>
                    </div>
                    <div class="author-field">
                      <label>Additional Information (English):</label>
                      <textarea class="author-input" data-field="otherInfo" data-lang="ENG" data-index="{{ loop.index0 }}" rows="2">{{ eng_info.get('otherInfo', '')|e }}</textarea>
                    </div>
                    <div class="author-section">
                      <h4>Коды автора</h4>
                      <div class="author-field">
                        <label>SPIN:</label>
                        <input type="text" class="author-input" data-field="spin" data-lang="CODES" data-index="{{ loop.index0 }}" value="{{ author_codes.get('spin', '')|e }}">
                      </div>
                      <div class="author-field">
                        <label>ORCID:</label>
                        <input type="text" class="author-input" data-field="orcid" data-lang="CODES" data-index="{{ loop.index0 }}" value="{{ author_codes.get('orcid', '')|e }}">
                      </div>
                      <div class="author-field">
                        <label>Scopus ID:</label>
                        <input type="text" class="author-input" data-field="scopusid" data-lang="CODES" data-index="{{ loop.index0 }}" value="{{ author_codes.get('scopusid', '')|e }}">
                      </div>
                      <div class="author-field">
                        <label>Researcher ID:</label>
                        <input type="text" class="author-input" data-field="researcherid" data-lang="CODES" data-index="{{ loop.index0 }}" value="{{ author_codes.get('researcherid', '')|e }}">
                      </div>
                    </div>
                    <div class="author-collapse-actions">
                      <button type="button" class="author-collapse-btn" onclick="event.preventDefault(); event.stopPropagation(); toggleAuthorDetails({{ loop.index0 }}); document.querySelector('.author-item[data-author-index=&quot;{{ loop.index0 }}&quot;]')?.scrollIntoView({ block: 'nearest' });">Свернуть</button>
                    </div>
                  </div>
                </div>
              {% endfor %}
            {% else %}
              <p style="color:#999;font-size:14px;padding:10px;">Авторы не указаны</p>
            {% endif %}
          </div>
        </div>

        <div class="field-group">
          <label>Аннотация (русский)</label>
          <textarea id="annotation" name="annotation">{% if form_data %}{{ form_data.get('annotation', '')|e }}{% endif %}</textarea>
          <div class="selected-lines" id="annotation-lines"></div>
          <button type="button" class="view-refs-btn" onclick="viewAnnotation('annotation', 'Аннотация (русский)')" style="margin-top: 5px;">👁 Просмотреть и редактировать</button>
        </div>

        <div class="field-group">
          <label>Аннотация (английский)</label>
          <textarea id="annotation_en" name="annotation_en">{% if form_data %}{{ form_data.get('annotation_en', '')|e }}{% endif %}</textarea>
          <div class="selected-lines" id="annotation_en-lines"></div>
          <button type="button" class="view-refs-btn" onclick="viewAnnotation('annotation_en', 'Аннотация (английский)')" style="margin-top: 5px;">👁 Просмотреть и редактировать</button>
        </div>

        <div class="field-group">
          <label>Ключевые слова (русский)</label>
          <textarea id="keywords" name="keywords" class="keywords-textarea" rows="3">{% if form_data %}{{ form_data.get('keywords', '')|e }}{% endif %}</textarea>
          <div class="selected-lines" id="keywords-lines"></div>
          <button type="button" class="view-refs-btn" onclick="viewAnnotation('keywords', 'Ключевые слова (русский)')" style="margin-top: 5px;">👁 Просмотреть и редактировать</button>
          <div class="keywords-count" id="keywords-count">Количество: 0</div>
        </div>

        <div class="field-group">
          <label>Ключевые слова (английский)</label>
          <textarea id="keywords_en" name="keywords_en" class="keywords-textarea" rows="3">{% if form_data %}{{ form_data.get('keywords_en', '')|e }}{% endif %}</textarea>
          <div class="selected-lines" id="keywords_en-lines"></div>
          <button type="button" class="view-refs-btn" onclick="viewAnnotation('keywords_en', 'Ключевые слова (английский)')" style="margin-top: 5px;">👁 Просмотреть и редактировать</button>
          <div class="keywords-count" id="keywords_en-count">Количество: 0</div>
        </div>

        <div class="field-group">
          <label>Список литературы (русский)</label>
          <textarea id="references_ru" name="references_ru" rows="5">{% if form_data %}{{ form_data.get('references_ru', '')|e }}{% endif %}</textarea>
          <div class="selected-lines" id="references_ru-lines"></div>
          <div class="keywords-count" id="references_ru-count">Количество источников: 0</div>
          <div style="display: flex; gap: 10px; margin-top: 5px; flex-wrap: wrap;">
            <button type="button" class="view-refs-btn" onclick="viewReferences('references_ru', 'Список литературы (русский)')">👁 Просмотреть список</button>
            <button type="button" class="view-refs-btn" onclick="processReferencesWithAI('references_ru')" id="ai-process-btn-ru" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
              🤖 Обработать с ИИ
            </button>
          </div>
          <small style="color:#666;font-size:12px;">Каждая ссылка с новой строки</small>
        </div>

        <div class="field-group">
          <label>Список литературы (английский)</label>
          <textarea id="references_en" name="references_en" rows="5">{% if form_data %}{{ form_data.get('references_en', '')|e }}{% endif %}</textarea>
          <div class="selected-lines" id="references_en-lines"></div>
          <div class="keywords-count" id="references_en-count">Количество источников: 0</div>
          <div style="display: flex; gap: 10px; margin-top: 5px; flex-wrap: wrap;">
            <button type="button" class="view-refs-btn" onclick="viewReferences('references_en', 'Список литературы (английский)')">👁 Просмотреть список</button>
            <button type="button" class="view-refs-btn" onclick="processReferencesWithAI('references_en')" id="ai-process-btn-en" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
              🤖 Обработать с ИИ
            </button>
          </div>
          <small style="color:#666;font-size:12px;">Каждая ссылка с новой строки</small>
        </div>


        <div class="field-group">
          <label>Финансирование (русский)</label>
          <textarea id="funding" name="funding" rows="3">{% if form_data %}{{ form_data.get('funding', '')|e }}{% endif %}</textarea>
          <div class="selected-lines" id="funding-lines"></div>
        </div>

        <div class="field-group">
          <label>Финансирование (английский)</label>
          <textarea id="funding_en" name="funding_en" rows="3">{% if form_data %}{{ form_data.get('funding_en', '')|e }}{% endif %}</textarea>
          <div class="selected-lines" id="funding_en-lines"></div>
        </div>

        <div class="buttons">
          <button type="button" class="btn-secondary" id="clearBtn">Очистить выделение</button>
          <button type="submit" class="btn-success">Сохранить</button>
        </div>
      </form>
    </div>
  </div>

  <div id="selectionPanel" class="selection-panel">
    <h4>Выделено строк: <span id="selectedCount">0</span>. Выберите поле:</h4>
    <div class="field-buttons">
      <button type="button" class="field-btn" data-assign="title">Название (рус)</button>
      <button type="button" class="field-btn" data-assign="title_en">Название (англ)</button>
      <div style="width: 100%; border-top: 1px solid #ddd; margin: 8px 0; padding-top: 8px;">
        <button type="button" class="field-btn" data-assign="doi">DOI</button>
        <button type="button" class="field-btn" data-assign="udc">УДК</button>
        <button type="button" class="field-btn" data-assign="bbk">ББК</button>
        <button type="button" class="field-btn" data-assign="edn">EDN</button>
      </div>
      <button type="button" class="field-btn" data-assign="annotation">Аннотация (рус)</button>
      <button type="button" class="field-btn" data-assign="annotation_en">Аннотация (англ)</button>
      <button type="button" class="field-btn" data-assign="keywords">Ключевые слова (рус)</button>
      <button type="button" class="field-btn" data-assign="keywords_en">Ключевые слова (англ)</button>
      <button type="button" class="field-btn" data-assign="references_ru">Список литературы (рус)</button>
      <button type="button" class="field-btn" data-assign="references_en">Список литературы (англ)</button>
      <button type="button" class="field-btn" data-assign="pages">Страницы</button>
      <button type="button" class="field-btn" data-assign="received_date">Дата получения</button>
      <button type="button" class="field-btn" data-assign="reviewed_date">Дата доработки</button>
      <button type="button" class="field-btn" data-assign="accepted_date">Дата принятия</button>
      <button type="button" class="field-btn" data-assign="date_publication">Дата публикации</button>
      <button type="button" class="field-btn" data-assign="funding">Финансирование (рус)</button>
      <button type="button" class="field-btn" data-assign="funding_en">Финансирование (англ)</button>
      <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #ddd;">
        <strong style="display: block; margin-bottom: 5px; font-size: 12px; color: #666;">Авторы:</strong>
        <button type="button" class="field-btn" data-assign="author_surname_rus">Автор: Фамилия (рус)</button>
        <button type="button" class="field-btn" data-assign="author_surname_eng">Автор: Фамилия (англ)</button>
        <button type="button" class="field-btn" data-assign="author_initials_rus">Автор: Инициалы (рус)</button>
        <button type="button" class="field-btn" data-assign="author_initials_eng">Автор: Инициалы (англ)</button>
        <button type="button" class="field-btn" data-assign="author_org_rus">Автор: Организация (рус)</button>
        <button type="button" class="field-btn" data-assign="author_org_eng">Автор: Организация (англ)</button>
        <button type="button" class="field-btn" data-assign="author_address_rus">Автор: Адрес (рус)</button>
        <button type="button" class="field-btn" data-assign="author_address_eng">Автор: Адрес (англ)</button>
        <button type="button" class="field-btn" data-assign="author_email">Автор: Email</button>
        <button type="button" class="field-btn" data-assign="author_other_rus">Автор: Доп. инфо (рус)</button>
        <button type="button" class="field-btn" data-assign="author_other_eng">Автор: Доп. инфо (англ)</button>
        <button type="button" class="field-btn" data-assign="author_spin">Автор: SPIN</button>
        <button type="button" class="field-btn" data-assign="author_orcid">Автор: ORCID</button>
        <button type="button" class="field-btn" data-assign="author_scopusid">Автор: Scopus ID</button>
        <button type="button" class="field-btn" data-assign="author_researcherid">Автор: Researcher ID</button>
      </div>
      <button type="button" class="field-btn" data-action="cancel">Отменить</button>
    </div>
  </div>
</div>

<div id="refsModal" class="modal">
  <div class="modal-content resizable refs-modal-content" id="refsModalContent" style="resize:both;overflow:auto;min-width:360px;min-height:240px;">
    <div class="modal-header">
      <h2 id="modalTitle">Список литературы</h2>
      <div class="modal-header-actions">
        <button class="modal-expand-btn" id="refsModalExpandBtn" onclick="toggleRefsModalSize()" title="Увеличить/уменьшить окно">⛶</button>
        <button class="modal-close" onclick="closeRefsModal()">&times;</button>
      </div>
    </div>
    <div id="refsList" class="refs-list"></div>
    <div class="modal-footer">
      <button class="modal-btn modal-btn-cancel" onclick="closeRefsModal()">Отмена</button>
      <button class="modal-btn modal-btn-save" onclick="saveEditedReferences()">Сохранить изменения</button>
    </div>
  </div>
</div>

<div id="annotationModal" class="modal">
  <div class="modal-content resizable annotation-modal-content" id="annotationModalContent" style="resize:both;overflow:auto;min-width:360px;min-height:240px;">
    <div class="modal-header">
      <h2 id="annotationModalTitle">Аннотация</h2>
      <div class="modal-header-actions">
        <button class="modal-expand-btn" id="annotationModalExpandBtn" onclick="toggleAnnotationModalSize()" title="Увеличить/уменьшить окно">⛶</button>
        <button class="modal-close" onclick="closeAnnotationModal()">&times;</button>
      </div>
    </div>
  <div class="annotation-modal-body">
  <div class="annotation-editor-toolbar">
    <div class="annotation-toolbar-row">
      <select id="annotationStyleSelect" class="annotation-select" data-action="format-block" title="Стили абзаца">
        <option value="p">Normal</option>
        <option value="h1">Heading 1</option>
        <option value="h2">Heading 2</option>
        <option value="h3">Heading 3</option>
      </select>
      <select id="annotationFontSelect" class="annotation-select" data-action="font-name" title="Шрифт">
        <option value="">Шрифт</option>
        <option value="Times New Roman">Times New Roman</option>
        <option value="Arial">Arial</option>
        <option value="Calibri">Calibri</option>
        <option value="Georgia">Georgia</option>
        <option value="Cambria">Cambria</option>
      </select>
      <select id="annotationFontSizeSelect" class="annotation-select" data-action="font-size" title="Размер">
        <option value="">Размер</option>
        <option value="2">12</option>
        <option value="3">14</option>
        <option value="4">16</option>
        <option value="5">18</option>
        <option value="6">24</option>
      </select>
      <span class="annotation-divider"></span>
      <button type="button" class="annotation-editor-btn" data-action="bold" tabindex="-1" title="Полужирный"><strong>B</strong></button>
      <button type="button" class="annotation-editor-btn" data-action="italic" tabindex="-1" title="Курсив"><em>I</em></button>
      <button type="button" class="annotation-editor-btn" data-action="strike" tabindex="-1" title="Зачёркнутый"><span style="text-decoration:line-through;">S</span></button>
      <button type="button" class="annotation-editor-btn" data-action="annotation-sup" tabindex="-1" title="Верхний индекс">x<sup>2</sup></button>
      <button type="button" class="annotation-editor-btn" data-action="annotation-sub" tabindex="-1" title="Нижний индекс">x<sub>2</sub></button>
      <input type="color" class="annotation-color-input" data-action="text-color" title="Цвет текста" value="#1f1f1f">
      <input type="color" class="annotation-color-input" data-action="highlight-color" title="Маркер" value="#fff3a3">
      <span class="annotation-divider"></span>
      <button type="button" class="annotation-editor-btn" data-action="align-left" tabindex="-1" title="По левому краю">≡</button>
      <button type="button" class="annotation-editor-btn" data-action="align-center" tabindex="-1" title="По центру">≡</button>
      <button type="button" class="annotation-editor-btn" data-action="align-right" tabindex="-1" title="По правому краю">≡</button>
      <button type="button" class="annotation-editor-btn" data-action="align-justify" tabindex="-1" title="По ширине">≡</button>
      <button type="button" class="annotation-editor-btn" data-action="unordered-list" tabindex="-1" title="Маркированный список">•⋯</button>
      <button type="button" class="annotation-editor-btn" data-action="ordered-list" tabindex="-1" title="Нумерованный список">1.</button>
      <button type="button" class="annotation-editor-btn" data-action="link" tabindex="-1" title="Ссылка">🔗</button>
      <button type="button" class="annotation-editor-btn" data-action="bookmark" tabindex="-1" title="Закладка">🔖</button>
    </div>
    <div class="annotation-toolbar-row">
      <span class="annotation-toolbar-label">Вставка:</span>
      <button type="button" class="annotation-editor-btn" data-action="insert-table" tabindex="-1" title="Таблица">▦</button>
      <button type="button" class="annotation-editor-btn" data-action="insert-image" tabindex="-1" title="Изображение">🖼</button>
      <button type="button" class="annotation-editor-btn" data-action="insert-video" tabindex="-1" title="Видео">▶</button>
      <button type="button" class="annotation-editor-btn" data-action="insert-code" tabindex="-1" title="Вставка кода">&lt;/&gt;</button>
      <button type="button" class="annotation-editor-btn" data-action="toggle-symbols-panel" tabindex="-1" title="Специальные символы" onclick="toggleAnnotationSymbolsPanel()">Ω</button>
      <button type="button" class="annotation-editor-btn" data-action="toggle-preview" tabindex="-1" title="Просмотр">👁</button>
      <button type="button" class="annotation-editor-btn" data-action="toggle-fullscreen" tabindex="-1" title="Полноэкранный режим">⛶</button>
      <button type="button" class="annotation-editor-btn" data-action="toggle-code-view" tabindex="-1" title="HTML / Code View">HTML</button>
      <button type="button" class="annotation-editor-btn" data-action="insert-latex" tabindex="-1" title="LaTeX">LaTeX</button>
      <button type="button" class="annotation-editor-btn" data-action="insert-formula" tabindex="-1" title="Формула">Σ</button>
    </div>
  </div>
  <div id="annotationSymbolsPanel" class="annotation-symbols-panel" role="dialog" aria-label="Специальные символы" aria-hidden="true" style="display:none;">
    <div class="annotation-symbols-header">
      <input id="annotationSymbolsSearch" class="annotation-symbols-search" type="text" placeholder="Поиск: alpha, μ, degree, ≤" autocomplete="off">
      <select id="annotationSymbolsCategory" class="annotation-symbols-category">
        <option value="all">Все</option>
        <option value="greek">Греческий</option>
        <option value="math">Математика</option>
        <option value="arrows">Стрелки</option>
        <option value="indices">Индексы</option>
        <option value="units">Единицы</option>
        <option value="currency">Валюты</option>
        <option value="typography">Типографика</option>
        <option value="latin">Диакритика</option>
        <option value="other">Прочее</option>
      </select>
    </div>
    <div class="annotation-symbols-toggles">
      <label><input id="annotationSymbolsLatex" type="checkbox"> Как LaTeX</label>
      <label><input id="annotationSymbolsAutoClose" type="checkbox" checked> Автозакрытие</label>
    </div>
    <div id="annotationSymbolsGrid" class="annotation-symbols-grid" role="listbox" aria-label="Символы"></div>
    <div class="annotation-symbols-footer">
      <div class="annotation-symbols-section">
        <span class="annotation-symbols-title">Недавние</span>
        <div id="annotationSymbolsRecent" class="annotation-symbols-recent"></div>
      </div>
      <div class="annotation-symbols-section">
        <span class="annotation-symbols-title">Избранное</span>
        <div id="annotationSymbolsFavorites" class="annotation-symbols-favorites"></div>
      </div>
      <div class="annotation-symbols-info">Вставится в позицию курсора.</div>
    </div>
  </div>
  <div id="annotationModalEditor" class="annotation-editor" contenteditable="true" spellcheck="true" autocomplete="off" autocorrect="off" autocapitalize="off" data-ms-editor="false" data-gramm="false" style="padding:24px;box-sizing:border-box;height:32vh;max-height:32vh;overflow-y:scroll;"></div>
  <textarea id="annotationModalTextarea" class="line-editor-textarea annotation-code-view" style="display:none;"></textarea>
  <div class="annotation-editor-footer">
    <div class="annotation-editor-stats">
      <span id="annotationWordCount" class="annotation-word-count">СЛОВ: 0</span>
      <span id="annotationLangIndicator" class="annotation-lang-indicator">RU</span>
    </div>
    <div class="annotation-editor-actions">
      <button class="modal-btn modal-btn-cancel" onclick="closeAnnotationModal()">Отмена</button>
      <button class="modal-btn modal-btn-save" onclick="saveEditedAnnotation()">Сохранить изменения</button>
    </div>
  </div>
  </div>
  </div>
</div>

<div id="lineCopyModal" class="line-editor-modal">
  <div class="line-editor-content resizable" style="resize:both;overflow:auto;min-width:320px;min-height:200px;">
    <div class="line-editor-header">
      <h2>Копирование строки</h2>
      <button class="modal-close" data-action="close-copy">&times;</button>
    </div>
    <textarea id="lineCopyTextarea" class="line-editor-textarea" readonly></textarea>
    <div class="line-editor-actions">
      <button class="modal-btn modal-btn-cancel" data-action="close-copy">Закрыть</button>
      <button class="modal-btn modal-btn-save" data-action="copy-from-modal">Копировать целиком</button>
    </div>
  </div>
</div>

<script src="/static/pdf-bbox.js"></script>
<script>
  function initPdfBbox() {
    if (window.PdfBbox && typeof window.PdfBbox.init === "function") {
      return window.PdfBbox.init.apply(window.PdfBbox, arguments);
    }
    return null;
  }
  const ensureOverlay = () => null;
  const renderBboxes = () => null;
  function convertToPdfPoint() { return null; }
  function convertToViewportPoint() { return null; }
</script>
<script>
// Глобальные функции для работы с модальным окном списка литературы
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function normalizeReferencesText(text) {
  const original = text || "";
  if (!original.trim()) return original;
  let value = original;
  value = value.replace(/(\S)([\u0410-\u042F\u0401][\u0430-\u044F\u0451]+\s+[\u0410-\u042F\u0401]\.[\u0410-\u042F\u0401]\.)/g, "$1\n$2");
  value = value.replace(/(\S)([A-Z][a-z]+\s+[A-Z]\.[A-Z]\.)/g, "$1\n$2");
  value = value.replace(/(https?:\/\/\S+)(?=[\u0410-\u042F\u0401A-Z])/g, "$1\n");
  value = value.replace(/(10\.\d{4,9}\/\S+?)(?=[\u0410-\u042F\u0401A-Z])/g, "$1\n");
  value = value.replace(/(\d\s*\u0441\.)(?=[\u0410-\u042F\u0401A-Z])/g, "$1\n");
  value = value.replace(/(\u0421\.?\s*\d[^\n]*?)(?=[\u0410-\u042F\u0401A-Z])/g, "$1\n");
  return value;
}

function normalizeReferenceWhitespace(text) {
  return (text || "")
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n")
    .replace(/[\u2028\u2029]/g, "\n")
    .replace(/\u00A0/g, " ")
    .replace(/\u200B/g, "");
}

function splitReferences(text) {
  const cleaned = normalizeReferenceWhitespace(text);
  if (!cleaned.trim()) return [];
  const numberedMatches = Array.from(cleaned.matchAll(/(^|\n)\s*(\d{1,3})\s*[).]/g));
  if (numberedMatches.length) {
    const refs = [];
    for (let i = 0; i < numberedMatches.length; i += 1) {
      const match = numberedMatches[i];
      const start = (match.index ?? 0) + match[0].length;
      const end = i + 1 < numberedMatches.length
        ? (numberedMatches[i + 1].index ?? cleaned.length)
        : cleaned.length;
      const entry = cleaned
        .slice(start, end)
        .replace(/\s*\n\s*/g, " ")
        .trim();
      if (entry) refs.push(entry);
    }
    return refs;
  }

  let working = cleaned;
  if (!working.includes("\n")) {
    working = normalizeReferencesText(working);
  }
  const lines = working
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
  if (!lines.length) return [];
  const refs = [];
  let current = lines[0];
  for (let i = 1; i < lines.length; i += 1) {
    const line = lines[i];
    const startsNew = /^[A-ZА-ЯЁ0-9]/.test(line);
    if (!startsNew) {
      current = `${current} ${line}`.trim();
    } else {
      refs.push(current);
      current = line;
    }
  }
  refs.push(current);
  return refs;
}

function splitReferencesStrict(text) {
  const cleaned = normalizeReferenceWhitespace(text);
  if (!cleaned.trim()) return [];
  return cleaned
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

function ensureAnnotationSymbolsData() {
  if (window.__annotationSymbolsData) return;
  window.__annotationSymbolsData = [
    { id: "alpha", char: "α", name_ru: "альфа", name_en: "alpha", codepoint: "U+03B1", category: "greek", aliases: ["alpha", "альфа"], latex: "\\alpha" },
    { id: "beta", char: "β", name_ru: "бета", name_en: "beta", codepoint: "U+03B2", category: "greek", aliases: ["beta", "бета"], latex: "\\beta" },
    { id: "gamma", char: "γ", name_ru: "гамма", name_en: "gamma", codepoint: "U+03B3", category: "greek", aliases: ["gamma", "гамма"], latex: "\\gamma" },
    { id: "delta", char: "δ", name_ru: "дельта", name_en: "delta", codepoint: "U+03B4", category: "greek", aliases: ["delta", "дельта"], latex: "\\delta" },
    { id: "epsilon", char: "ε", name_ru: "эпсилон", name_en: "epsilon", codepoint: "U+03B5", category: "greek", aliases: ["epsilon", "эпсилон"], latex: "\\epsilon" },
    { id: "theta", char: "θ", name_ru: "тета", name_en: "theta", codepoint: "U+03B8", category: "greek", aliases: ["theta", "тета"], latex: "\\theta" },
    { id: "lambda", char: "λ", name_ru: "лямбда", name_en: "lambda", codepoint: "U+03BB", category: "greek", aliases: ["lambda", "лямбда"], latex: "\\lambda" },
    { id: "mu", char: "μ", name_ru: "мю", name_en: "mu", codepoint: "U+03BC", category: "greek", aliases: ["mu", "micro", "мю"], latex: "\\mu" },
    { id: "pi", char: "π", name_ru: "пи", name_en: "pi", codepoint: "U+03C0", category: "greek", aliases: ["pi", "пи"], latex: "\\pi" },
    { id: "sigma", char: "σ", name_ru: "сигма", name_en: "sigma", codepoint: "U+03C3", category: "greek", aliases: ["sigma", "сигма"], latex: "\\sigma" },
    { id: "phi", char: "φ", name_ru: "фи", name_en: "phi", codepoint: "U+03C6", category: "greek", aliases: ["phi", "фи"], latex: "\\phi" },
    { id: "psi", char: "ψ", name_ru: "пси", name_en: "psi", codepoint: "U+03C8", category: "greek", aliases: ["psi", "пси"], latex: "\\psi" },
    { id: "omega", char: "ω", name_ru: "омега", name_en: "omega", codepoint: "U+03C9", category: "greek", aliases: ["omega", "омега"], latex: "\\omega" },
    { id: "Omega", char: "Ω", name_ru: "омега (верхн.)", name_en: "Omega", codepoint: "U+03A9", category: "greek", aliases: ["omega", "омега"], latex: "\\Omega" },
    { id: "plusminus", char: "±", name_ru: "плюс-минус", name_en: "plus-minus", codepoint: "U+00B1", category: "math", aliases: ["plusminus", "+-"], latex: "\\pm" },
    { id: "times", char: "×", name_ru: "умножить", name_en: "times", codepoint: "U+00D7", category: "math", aliases: ["times", "multiply"], latex: "\\times" },
    { id: "divide", char: "÷", name_ru: "деление", name_en: "divide", codepoint: "U+00F7", category: "math", aliases: ["divide"], latex: "\\div" },
    { id: "leq", char: "≤", name_ru: "меньше либо равно", name_en: "leq", codepoint: "U+2264", category: "math", aliases: ["leq", "<="], latex: "\\leq" },
    { id: "geq", char: "≥", name_ru: "больше либо равно", name_en: "geq", codepoint: "U+2265", category: "math", aliases: ["geq", ">="], latex: "\\geq" },
    { id: "neq", char: "≠", name_ru: "не равно", name_en: "not equal", codepoint: "U+2260", category: "math", aliases: ["neq", "!="], latex: "\\neq" },
    { id: "approx", char: "≈", name_ru: "примерно", name_en: "approx", codepoint: "U+2248", category: "math", aliases: ["approx"], latex: "\\approx" },
    { id: "infty", char: "∞", name_ru: "бесконечность", name_en: "infinity", codepoint: "U+221E", category: "math", aliases: ["infty", "infinity"], latex: "\\infty" },
    { id: "sum", char: "∑", name_ru: "сумма", name_en: "sum", codepoint: "U+2211", category: "math", aliases: ["sum"], latex: "\\sum" },
    { id: "prod", char: "∏", name_ru: "произведение", name_en: "prod", codepoint: "U+220F", category: "math", aliases: ["prod"], latex: "\\prod" },
    { id: "sqrt", char: "√", name_ru: "корень", name_en: "sqrt", codepoint: "U+221A", category: "math", aliases: ["sqrt"], latex: "\\sqrt{}" },
    { id: "int", char: "∫", name_ru: "интеграл", name_en: "integral", codepoint: "U+222B", category: "math", aliases: ["integral"], latex: "\\int" },
    { id: "partial", char: "∂", name_ru: "частная производная", name_en: "partial", codepoint: "U+2202", category: "math", aliases: ["partial"], latex: "\\partial" },
    { id: "nabla", char: "∇", name_ru: "набла", name_en: "nabla", codepoint: "U+2207", category: "math", aliases: ["nabla"], latex: "\\nabla" },
    { id: "arrow_left", char: "←", name_ru: "стрелка влево", name_en: "left arrow", codepoint: "U+2190", category: "arrows", aliases: ["left", "arrow"], latex: "\\leftarrow" },
    { id: "arrow_right", char: "→", name_ru: "стрелка вправо", name_en: "right arrow", codepoint: "U+2192", category: "arrows", aliases: ["right", "arrow"], latex: "\\rightarrow" },
    { id: "arrow_up", char: "↑", name_ru: "стрелка вверх", name_en: "up arrow", codepoint: "U+2191", category: "arrows", aliases: ["up", "arrow"], latex: "\\uparrow" },
    { id: "arrow_down", char: "↓", name_ru: "стрелка вниз", name_en: "down arrow", codepoint: "U+2193", category: "arrows", aliases: ["down", "arrow"], latex: "\\downarrow" },
    { id: "arrow_lr", char: "↔", name_ru: "двунаправленная", name_en: "leftright arrow", codepoint: "U+2194", category: "arrows", aliases: ["leftright", "arrow"], latex: "\\leftrightarrow" },
    { id: "sup1", char: "¹", name_ru: "верхний 1", name_en: "superscript 1", codepoint: "U+00B9", category: "indices", aliases: ["superscript", "1"] },
    { id: "sup2", char: "²", name_ru: "верхний 2", name_en: "superscript 2", codepoint: "U+00B2", category: "indices", aliases: ["superscript", "2"] },
    { id: "sup3", char: "³", name_ru: "верхний 3", name_en: "superscript 3", codepoint: "U+00B3", category: "indices", aliases: ["superscript", "3"] },
    { id: "sub1", char: "₁", name_ru: "нижний 1", name_en: "subscript 1", codepoint: "U+2081", category: "indices", aliases: ["subscript", "1"] },
    { id: "sub2", char: "₂", name_ru: "нижний 2", name_en: "subscript 2", codepoint: "U+2082", category: "indices", aliases: ["subscript", "2"] },
    { id: "sub3", char: "₃", name_ru: "нижний 3", name_en: "subscript 3", codepoint: "U+2083", category: "indices", aliases: ["subscript", "3"] },
    { id: "degree", char: "°", name_ru: "градус", name_en: "degree", codepoint: "U+00B0", category: "units", aliases: ["degree"], latex: "^\\circ" },
    { id: "permil", char: "‰", name_ru: "промилле", name_en: "per mille", codepoint: "U+2030", category: "units", aliases: ["permil"], latex: "\\permil" },
    { id: "angstrom", char: "Å", name_ru: "ангстрем", name_en: "angstrom", codepoint: "U+00C5", category: "units", aliases: ["angstrom"], latex: "\\AA" },
    { id: "celsius", char: "℃", name_ru: "цельсий", name_en: "celsius", codepoint: "U+2103", category: "units", aliases: ["celsius"] },
    { id: "euro", char: "€", name_ru: "евро", name_en: "euro", codepoint: "U+20AC", category: "currency", aliases: ["euro"] },
    { id: "ruble", char: "₽", name_ru: "рубль", name_en: "ruble", codepoint: "U+20BD", category: "currency", aliases: ["ruble", "рубль"] },
    { id: "pound", char: "£", name_ru: "фунт", name_en: "pound", codepoint: "U+00A3", category: "currency", aliases: ["pound"] },
    { id: "yen", char: "¥", name_ru: "иена", name_en: "yen", codepoint: "U+00A5", category: "currency", aliases: ["yen"] },
    { id: "emdash", char: "—", name_ru: "длинное тире", name_en: "em dash", codepoint: "U+2014", category: "typography", aliases: ["emdash"] },
    { id: "endash", char: "–", name_ru: "короткое тире", name_en: "en dash", codepoint: "U+2013", category: "typography", aliases: ["endash"] },
    { id: "laquo", char: "«", name_ru: "кавычки елочки", name_en: "guillemets", codepoint: "U+00AB", category: "typography", aliases: ["quotes"] },
    { id: "raquo", char: "»", name_ru: "кавычки елочки", name_en: "guillemets", codepoint: "U+00BB", category: "typography", aliases: ["quotes"] },
    { id: "ellipsis", char: "…", name_ru: "многоточие", name_en: "ellipsis", codepoint: "U+2026", category: "typography", aliases: ["ellipsis"] },
    { id: "sect", char: "§", name_ru: "параграф", name_en: "section", codepoint: "U+00A7", category: "typography", aliases: ["section"] },
    { id: "para", char: "¶", name_ru: "абзац", name_en: "paragraph", codepoint: "U+00B6", category: "typography", aliases: ["paragraph"] },
    { id: "acute_e", char: "é", name_ru: "е с акутом", name_en: "e acute", codepoint: "U+00E9", category: "latin", aliases: ["e", "acute"] },
    { id: "umlaut_u", char: "ü", name_ru: "у с умляутом", name_en: "u umlaut", codepoint: "U+00FC", category: "latin", aliases: ["u", "umlaut"] },
    { id: "ring_a", char: "å", name_ru: "а с кружком", name_en: "a ring", codepoint: "U+00E5", category: "latin", aliases: ["a", "ring"] }
  ];
}

function getAnnotationSymbolsStorage(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch (e) {
    return fallback;
  }
}

function setAnnotationSymbolsStorage(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (e) {}
}

function getAnnotationSymbolsElements() {
  return {
    panel: document.getElementById("annotationSymbolsPanel"),
    search: document.getElementById("annotationSymbolsSearch"),
    category: document.getElementById("annotationSymbolsCategory"),
    grid: document.getElementById("annotationSymbolsGrid"),
    recent: document.getElementById("annotationSymbolsRecent"),
    favorites: document.getElementById("annotationSymbolsFavorites"),
    latexToggle: document.getElementById("annotationSymbolsLatex"),
    autoCloseToggle: document.getElementById("annotationSymbolsAutoClose")
  };
}

function renderAnnotationSymbolsPanel() {
  ensureAnnotationSymbolsData();
  const { search, category, grid } = getAnnotationSymbolsElements();
  if (!search || !category || !grid) return;
  const query = (search.value || "").trim().toLowerCase();
  const selectedCategory = category.value || "all";
  const favorites = new Set(getAnnotationSymbolsStorage("annotation_symbols_favorites", []));
  const symbols = (window.__annotationSymbolsData || []).filter((item) => {
    if (selectedCategory !== "all" && item.category !== selectedCategory) return false;
    if (!query) return true;
    const hay = [
      item.char,
      item.name_ru,
      item.name_en,
      item.codepoint,
      item.category,
      ...(item.aliases || []),
      item.latex || ""
    ].join(" ").toLowerCase();
    return hay.includes(query);
  });
  grid.innerHTML = "";
  symbols.forEach((item, index) => {
    const cell = document.createElement("div");
    cell.className = "annotation-symbol-cell";
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "annotation-symbol-btn";
    btn.dataset.symbolId = item.id;
    btn.dataset.index = String(index);
    btn.textContent = item.char;
    btn.title = `${item.name_ru} (${item.codepoint})`;
    btn.addEventListener("click", () => insertAnnotationSymbol(item));
    const fav = document.createElement("button");
    fav.type = "button";
    fav.className = "annotation-symbol-fav" + (favorites.has(item.id) ? " active" : "");
    fav.textContent = favorites.has(item.id) ? "★" : "☆";
    fav.title = "В избранное";
    fav.tabIndex = -1;
    fav.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      toggleAnnotationSymbolFavorite(item.id);
    });
    cell.appendChild(btn);
    cell.appendChild(fav);
    grid.appendChild(cell);
  });
  renderAnnotationSymbolsLists();
}

function renderAnnotationSymbolsLists() {
  const { recent, favorites } = getAnnotationSymbolsElements();
  if (!recent || !favorites) return;
  const recentIds = getAnnotationSymbolsStorage("annotation_symbols_recent", []);
  const favoriteIds = getAnnotationSymbolsStorage("annotation_symbols_favorites", []);
  recent.innerHTML = "";
  favorites.innerHTML = "";
  const data = window.__annotationSymbolsData || [];
  recentIds.forEach((id) => {
    const item = data.find((symbol) => symbol.id === id);
    if (!item) return;
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "annotation-symbol-chip";
    chip.textContent = item.char;
    chip.title = item.name_ru;
    chip.addEventListener("click", () => insertAnnotationSymbol(item));
    recent.appendChild(chip);
  });
  favoriteIds.forEach((id) => {
    const item = data.find((symbol) => symbol.id === id);
    if (!item) return;
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "annotation-symbol-chip";
    chip.textContent = item.char;
    chip.title = item.name_ru;
    chip.addEventListener("click", () => insertAnnotationSymbol(item));
    favorites.appendChild(chip);
  });
}

function toggleAnnotationSymbolFavorite(id) {
  const current = new Set(getAnnotationSymbolsStorage("annotation_symbols_favorites", []));
  if (current.has(id)) {
    current.delete(id);
  } else {
    current.add(id);
  }
  setAnnotationSymbolsStorage("annotation_symbols_favorites", Array.from(current));
  renderAnnotationSymbolsPanel();
}

function insertAnnotationSymbol(item) {
  const editor = document.getElementById("annotationModalEditor");
  const { latexToggle, autoCloseToggle, panel } = getAnnotationSymbolsElements();
  if (!editor) return;
  restoreAnnotationSelection();
  editor.focus();
  const useLatex = latexToggle && latexToggle.checked && item.latex;
  const text = useLatex ? item.latex : item.char;
  document.execCommand("insertText", false, text);
  const recent = getAnnotationSymbolsStorage("annotation_symbols_recent", []);
  const filtered = recent.filter((id) => id !== item.id);
  filtered.unshift(item.id);
  setAnnotationSymbolsStorage("annotation_symbols_recent", filtered.slice(0, 20));
  renderAnnotationSymbolsLists();
  updateAnnotationStats();
  if (autoCloseToggle && autoCloseToggle.checked && panel) {
    closeAnnotationSymbolsPanel();
  }
  editor.focus();
}

function openAnnotationSymbolsPanel() {
  const { panel, search } = getAnnotationSymbolsElements();
  if (!panel) return;
  saveAnnotationSelection();
  renderAnnotationSymbolsPanel();
  panel.classList.add("active");
  panel.style.display = "block";
  panel.setAttribute("aria-hidden", "false");
  if (search) {
    search.focus();
    search.select();
  }
}

function closeAnnotationSymbolsPanel() {
  const { panel } = getAnnotationSymbolsElements();
  if (!panel) return;
  panel.classList.remove("active");
  panel.style.display = "none";
  panel.setAttribute("aria-hidden", "true");
}

function toggleAnnotationSymbolsPanel() {
  const { panel } = getAnnotationSymbolsElements();
  if (!panel) return;
  if (panel.classList.contains("active")) {
    closeAnnotationSymbolsPanel();
  } else {
    openAnnotationSymbolsPanel();
  }
}

function initAnnotationSymbolsPanel() {
  if (window.__annotationSymbolsHandlersAdded) return;
  window.__annotationSymbolsHandlersAdded = true;
  const { search, category, grid } = getAnnotationSymbolsElements();
  if (search) search.addEventListener("input", renderAnnotationSymbolsPanel);
  if (category) category.addEventListener("change", renderAnnotationSymbolsPanel);
  document.addEventListener("mousedown", (event) => {
    const target = event.target;
    const button = target.closest("[data-action='toggle-symbols-panel']");
    const panelEl = getAnnotationSymbolsElements().panel;
    if (!panelEl || !panelEl.classList.contains("active")) return;
    if (panelEl.contains(target) || button) return;
    closeAnnotationSymbolsPanel();
  });
  document.addEventListener("keydown", (event) => {
    const panelEl = getAnnotationSymbolsElements().panel;
    if (!panelEl || !panelEl.classList.contains("active")) return;
    if (event.key === "Escape") {
      event.preventDefault();
      closeAnnotationSymbolsPanel();
      document.getElementById("annotationModalEditor")?.focus();
    }
  });
  if (grid) {
    grid.addEventListener("keydown", (event) => {
      const buttons = Array.from(grid.querySelectorAll(".annotation-symbol-btn"));
      if (!buttons.length) return;
      const active = document.activeElement;
      const index = buttons.indexOf(active);
      if (index === -1) return;
      const columns = getComputedStyle(grid).gridTemplateColumns.split(" ").length || 8;
      let nextIndex = index;
      if (event.key === "ArrowRight") nextIndex = Math.min(buttons.length - 1, index + 1);
      if (event.key === "ArrowLeft") nextIndex = Math.max(0, index - 1);
      if (event.key === "ArrowDown") nextIndex = Math.min(buttons.length - 1, index + columns);
      if (event.key === "ArrowUp") nextIndex = Math.max(0, index - columns);
      if (nextIndex !== index) {
        event.preventDefault();
        buttons[nextIndex].focus();
      }
      if (event.key === "Enter") {
        event.preventDefault();
        buttons[index].click();
      }
    });
  }
}

let annotationCodeViewEnabled = false;
let annotationPreviewEnabled = false;

function setAnnotationCodeView(enabled) {
  const editor = document.getElementById("annotationModalEditor");
  const textarea = document.getElementById("annotationModalTextarea");
  if (!editor || !textarea) return;
  annotationCodeViewEnabled = enabled;
  annotationPreviewEnabled = false;
  editor.contentEditable = "true";
  editor.classList.remove("preview");
  if (enabled) {
    textarea.value = editor.innerHTML;
    textarea.style.display = "block";
    editor.style.display = "none";
  } else {
    editor.innerHTML = textarea.value;
    textarea.style.display = "none";
    editor.style.display = "block";
  }
  updateAnnotationStats();
}

function toggleAnnotationPreview() {
  const editor = document.getElementById("annotationModalEditor");
  if (!editor) return;
  annotationPreviewEnabled = !annotationPreviewEnabled;
  editor.contentEditable = annotationPreviewEnabled ? "false" : "true";
  editor.classList.toggle("preview", annotationPreviewEnabled);
}

function getAnnotationPlainText() {
  const editor = document.getElementById("annotationModalEditor");
  const textarea = document.getElementById("annotationModalTextarea");
  if (annotationCodeViewEnabled && textarea) {
    return annotationHtmlToText(textarea.value || "");
  }
  if (editor) {
    return annotationHtmlToText(editor.innerHTML || "");
  }
  return "";
}

function updateAnnotationStats() {
  const countEl = document.getElementById("annotationWordCount");
  const langEl = document.getElementById("annotationLangIndicator");
  const modal = document.getElementById("annotationModal");
  const fieldId = modal?.dataset?.fieldId || currentAnnotationFieldId;
  if (langEl) {
    langEl.textContent = fieldId === "annotation_en" ? "EN" : "RU";
  }
  const text = getAnnotationPlainText();
  const words = text.trim() ? text.trim().split(/\s+/).filter(Boolean) : [];
  if (countEl) {
    countEl.textContent = `СЛОВ: ${words.length}`;
  }
}

function getSelectionText() {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) return "";
  return selection.toString();
}

function insertAnnotationHtml(html) {
  document.execCommand("insertHTML", false, html);
}

function applyAnnotationCommand(action, value) {
  if (!action) return;
  if (action === "annotation-sup") {
    applyAnnotationFormat("sup");
    return;
  }
  if (action === "annotation-sub") {
    applyAnnotationFormat("sub");
    return;
  }
  const editor = document.getElementById("annotationModalEditor");
  if (editor && editor.style.display !== "none") {
    editor.focus();
  }
  switch (action) {
    case "bold":
      document.execCommand("bold");
      break;
    case "italic":
      document.execCommand("italic");
      break;
    case "strike":
      document.execCommand("strikeThrough");
      break;
    case "align-left":
      document.execCommand("justifyLeft");
      break;
    case "align-center":
      document.execCommand("justifyCenter");
      break;
    case "align-right":
      document.execCommand("justifyRight");
      break;
    case "align-justify":
      document.execCommand("justifyFull");
      break;
    case "unordered-list":
      document.execCommand("insertUnorderedList");
      break;
    case "ordered-list":
      document.execCommand("insertOrderedList");
      break;
    case "text-color":
      document.execCommand("foreColor", false, value);
      break;
    case "highlight-color":
      document.execCommand("hiliteColor", false, value);
      break;
    case "format-block":
      if (value) document.execCommand("formatBlock", false, value);
      break;
    case "font-name":
      if (value) document.execCommand("fontName", false, value);
      break;
    case "font-size":
      if (value) document.execCommand("fontSize", false, value);
      break;
    case "link": {
      const url = prompt("Введите ссылку:", "https://");
      if (!url) break;
      const selected = getSelectionText();
      if (selected) {
        document.execCommand("createLink", false, url);
      } else {
        insertAnnotationHtml(`<a href="${escapeHtml(url)}" target="_blank" rel="noopener">${escapeHtml(url)}</a>`);
      }
      break;
    }
    case "bookmark": {
      const name = prompt("Название закладки:");
      if (!name) break;
      insertAnnotationHtml(`<span class="annotation-bookmark">🔖 ${escapeHtml(name)}</span>`);
      break;
    }
    case "insert-table": {
      const rows = parseInt(prompt("Количество строк:", "2"), 10);
      const cols = parseInt(prompt("Количество столбцов:", "2"), 10);
      if (!rows || !cols) break;
      let html = '<table class="annotation-table">';
      for (let r = 0; r < rows; r += 1) {
        html += "<tr>";
        for (let c = 0; c < cols; c += 1) {
          html += "<td>&nbsp;</td>";
        }
        html += "</tr>";
      }
      html += "</table>";
      insertAnnotationHtml(html);
      break;
    }
    case "insert-image": {
      const url = prompt("Ссылка на изображение:");
      if (!url) break;
      insertAnnotationHtml(`<img src="${escapeHtml(url)}" alt="image" style="max-width:100%;height:auto;">`);
      break;
    }
    case "insert-video": {
      const url = prompt("Ссылка на видео (iframe/url):");
      if (!url) break;
      insertAnnotationHtml(`<iframe src="${escapeHtml(url)}" frameborder="0" allowfullscreen style="width:100%;height:320px;"></iframe>`);
      break;
    }
    case "insert-code": {
      const selected = getSelectionText() || "код";
      const escaped = escapeHtml(selected);
      insertAnnotationHtml(`<pre class="annotation-code-block"><code>${escaped}</code></pre>`);
      break;
    }
    case "toggle-symbols-panel":
      toggleAnnotationSymbolsPanel();
      break;
    case "insert-latex": {
      const latex = prompt("LaTeX формула:");
      if (!latex) break;
      document.execCommand("insertText", false, `\\(${latex}\\)`);
      break;
    }
    case "insert-formula": {
      const formula = prompt("Формула:");
      if (!formula) break;
      document.execCommand("insertText", false, `∑ ${formula}`);
      break;
    }
    case "toggle-preview":
      toggleAnnotationPreview();
      break;
    case "toggle-fullscreen":
      toggleAnnotationModalSize();
      break;
    case "toggle-code-view":
      setAnnotationCodeView(!annotationCodeViewEnabled);
      break;
    default:
      break;
  }
  updateAnnotationStats();
}

function setViewMode(mode) {
  const pdfPanel = document.getElementById("pdfPanel");
  const textPanel = document.getElementById("textPanel");
  const htmlBtn = document.querySelector("[data-view='html']");
  const pdfBtn = document.querySelector("[data-view='pdf']");
  if (mode === "pdf" && (!pdfPanel || (pdfBtn && pdfBtn.disabled))) {
    mode = "html";
  }
  if (pdfPanel) {
    pdfPanel.classList.toggle("panel-hidden", mode !== "pdf");
  }
  if (textPanel) {
    textPanel.classList.toggle("panel-hidden", mode === "pdf");
  }
  if (htmlBtn) htmlBtn.classList.toggle("active", mode === "html");
  if (pdfBtn) pdfBtn.classList.toggle("active", mode === "pdf");
  try {
    const url = new URL(window.location.href);
    url.searchParams.set("view", mode);
    window.history.replaceState({}, "", url);
  } catch (e) {}
}

document.addEventListener("DOMContentLoaded", () => {
  const htmlBtn = document.querySelector("[data-view='html']");
  const pdfBtn = document.querySelector("[data-view='pdf']");
  if (htmlBtn) htmlBtn.addEventListener("click", () => setViewMode("html"));
  if (pdfBtn) pdfBtn.addEventListener("click", () => setViewMode("pdf"));
  setViewMode("{{ view_mode }}");
});

let currentRefsFieldId = null;

function viewReferences(fieldId, title) {
  const field = document.getElementById(fieldId);
  if (!field) return;
  
  currentRefsFieldId = fieldId;
  
  const useStrictSplit = field.dataset && field.dataset.aiProcessed === "1";
  const refs = useStrictSplit ? splitReferencesStrict(field.value) : splitReferences(field.value);
  if (refs.length === 0) {
    alert("References list is empty");
    return;
  }
  
  const modal = document.getElementById("refsModal");
  const modalTitle = document.getElementById("modalTitle");
  const refsList = document.getElementById("refsList");
  
  if (!modal || !modalTitle || !refsList) return;
  
  modalTitle.textContent = title;
  refsList.innerHTML = "";
  
  if (refs.length === 0) {
    refsList.innerHTML = "<p style='color:#999;text-align:center;padding:20px;'>Список литературы пуст</p>";
  } else {
    refs.forEach((ref, index) => {
      const refItem = document.createElement("div");
      refItem.className = "ref-item";
      refItem.dataset.index = index;
      // Определяем, есть ли следующий источник для объединения
      const hasNext = index < refs.length - 1;
      refItem.innerHTML = `
        <span class="ref-number">${index + 1}.</span>
        <span class="ref-text" contenteditable="true" spellcheck="false">${escapeHtml(ref)}</span>
        <div class="ref-actions">
          ${hasNext ? `<button class="ref-action-btn merge" onclick="mergeWithNext(this)" title="Объединить со следующим">⇅</button>` : ''}
          <button class="ref-action-btn delete" onclick="deleteReference(this)" title="Удалить">✕</button>
        </div>
      `;
      attachRefTextHandlers(refItem);
      refsList.appendChild(refItem);
    });
  }
  
  modal.classList.add("active");
}

function syncReferencesField() {
  if (!currentRefsFieldId) return;
  const field = document.getElementById(currentRefsFieldId);
  if (!field) return;
  const refItems = document.querySelectorAll("#refsList .ref-item");
  const refs = Array.from(refItems)
    .map(item => {
      const textSpan = item.querySelector(".ref-text");
      return textSpan ? textSpan.textContent.trim() : "";
    })
    .filter(ref => ref.length > 0);
  field.value = refs.join("\n");
  field.dispatchEvent(new Event("input", { bubbles: true }));
  if (window.updateReferencesCount) {
    window.updateReferencesCount(currentRefsFieldId);
  }
}

function mergeWithNext(btn) {
  const refItem = btn.closest(".ref-item");
  if (!refItem) return;
  
  const nextItem = refItem.nextElementSibling;
  if (!nextItem || !nextItem.classList.contains("ref-item")) {
    alert("Нет следующего источника для объединения");
    return;
  }
  
  const currentText = refItem.querySelector(".ref-text")?.textContent.trim() || "";
  const nextText = nextItem.querySelector(".ref-text")?.textContent.trim() || "";
  
  if (!currentText || !nextText) {
    alert("Нельзя объединить пустые источники");
    return;
  }
  
  // Объединяем тексты через пробел
  const mergedText = currentText + " " + nextText;
  const currentTextSpan = refItem.querySelector(".ref-text");
  if (currentTextSpan) {
    currentTextSpan.textContent = mergedText;
  }
  
  // Удаляем следующий элемент
  nextItem.remove();
  
  // Перенумеровываем оставшиеся ссылки
  renumberReferences();
  
  // Обновляем кнопки объединения (могут измениться после удаления)
  updateMergeButtons();
  syncReferencesField();
}

function updateMergeButtons() {
  const refItems = document.querySelectorAll("#refsList .ref-item");
  refItems.forEach((item, index) => {
    const actions = item.querySelector(".ref-actions");
    if (!actions) return;
    
    const hasNext = index < refItems.length - 1;
    const existingMergeBtn = actions.querySelector(".ref-action-btn.merge");
    
    if (hasNext && !existingMergeBtn) {
      // Добавляем кнопку объединения, если её нет
      const deleteBtn = actions.querySelector(".ref-action-btn.delete");
      if (deleteBtn) {
        const mergeBtn = document.createElement("button");
        mergeBtn.className = "ref-action-btn merge";
        mergeBtn.onclick = () => mergeWithNext(mergeBtn);
        mergeBtn.title = "Объединить со следующим";
        mergeBtn.textContent = "⇅";
        actions.insertBefore(mergeBtn, deleteBtn);
      }
    } else if (!hasNext && existingMergeBtn) {
      // Удаляем кнопку объединения, если следующего элемента нет
      existingMergeBtn.remove();
    }
  });
}

function deleteReference(btn) {
  const refItem = btn.closest(".ref-item");
  if (refItem && confirm("Удалить эту ссылку из списка?")) {
    refItem.remove();
    // Перенумеровываем оставшиеся ссылки
    renumberReferences();
    // Обновляем кнопки объединения
    updateMergeButtons();
  }
}

function renumberReferences() {
  const refItems = document.querySelectorAll("#refsList .ref-item");
  refItems.forEach((item, index) => {
    const numberSpan = item.querySelector(".ref-number");
    if (numberSpan) {
      numberSpan.textContent = (index + 1) + ".";
    }
  });
  // Обновляем кнопки объединения после перенумерации
  updateMergeButtons();
}

function attachRefTextHandlers(refItem) {
  const refText = refItem.querySelector(".ref-text");
  if (!refText) return;
  refText.addEventListener("keydown", handleRefKeydown);
}

function handleRefKeydown(event) {
  if (event.key !== "Enter") return;
  event.preventDefault();
  const refText = event.currentTarget;
  splitReferenceAtCursor(refText);
}

function splitReferenceAtCursor(refText) {
  const refItem = refText.closest(".ref-item");
  if (!refItem) return;

  const fullText = refText.textContent || "";
  const caretOffset = getCaretOffset(refText);
  const left = fullText.slice(0, caretOffset).trim();
  const right = fullText.slice(caretOffset).trim();

  if (!left && !right) return;

  refText.textContent = left;

  const newItem = document.createElement("div");
  newItem.className = "ref-item";
  newItem.innerHTML = `
    <span class="ref-number"></span>
    <span class="ref-text" contenteditable="true" spellcheck="false">${escapeHtml(right)}</span>
    <div class="ref-actions">
      <button class="ref-action-btn merge" onclick="mergeWithNext(this)" title="Объединить со следующим">⇅</button>
      <button class="ref-action-btn delete" onclick="deleteReference(this)" title="Удалить">✕</button>
    </div>
  `;

  refItem.insertAdjacentElement("afterend", newItem);
  attachRefTextHandlers(newItem);
  renumberReferences();
  updateMergeButtons();
  syncReferencesField();

  const newText = newItem.querySelector(".ref-text");
  if (newText) {
    placeCaretAtStart(newText);
  }
}

function getCaretOffset(element) {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) {
    return (element.textContent || "").length;
  }
  const range = selection.getRangeAt(0);
  if (!element.contains(range.startContainer)) {
    return (element.textContent || "").length;
  }
  const preRange = range.cloneRange();
  preRange.selectNodeContents(element);
  preRange.setEnd(range.startContainer, range.startOffset);
  return preRange.toString().length;
}

function placeCaretAtStart(element) {
  element.focus();
  const range = document.createRange();
  range.selectNodeContents(element);
  range.collapse(true);
  const selection = window.getSelection();
  if (!selection) return;
  selection.removeAllRanges();
  selection.addRange(range);
}

async function processReferencesWithAI(fieldId) {
  const field = document.getElementById(fieldId);
  if (!field) {
    toast("Поле не найдено", "error");
    return;
  }
  
  const rawText = field.value.trim();
  if (!rawText) {
    toast("Поле пусто. Сначала добавьте текст списка литературы.", "error");
    return;
  }
  
  const btnId = fieldId === "references_ru" ? "ai-process-btn-ru" : "ai-process-btn-en";
  const btn = document.getElementById(btnId);
  const originalText = btn ? btn.textContent : "🤖 Обработать с ИИ";
  
  if (btn) {
    btn.disabled = true;
    btn.textContent = "⏳ Обработка ИИ...";
  }
  
  try {
    const response = await fetch("/process-references-ai", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        field_id: fieldId,
        text: rawText,
      }),
    });
    
    const data = await response.json();
    
    if (data.success) {
      field.dataset.aiProcessed = "1";
      field.value = data.text;
      // Обновляем счетчик
      if (window.updateReferencesCount) {
        window.updateReferencesCount(fieldId);
      }
      toast(`✅ Обработано ${data.count} источников с помощью ИИ`, "success");
    } else {
      toast(`❌ Ошибка: ${data.error}`, "error");
    }
  } catch (error) {
    toast(`❌ Ошибка при обработке: ${error.message}`, "error");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = originalText;
    }
  }
}

function saveEditedReferences() {
  if (!currentRefsFieldId) return;
  
  const field = document.getElementById(currentRefsFieldId);
  if (!field) return;
  
  const refItems = document.querySelectorAll("#refsList .ref-item");
  const refs = Array.from(refItems)
    .map(item => {
      const textSpan = item.querySelector(".ref-text");
      return textSpan ? textSpan.textContent.trim() : "";
    })
    .filter(ref => ref.length > 0);
  
  field.value = refs.join("\n");
  field.dispatchEvent(new Event("input", { bubbles: true }));
  // Обновляем счетчик после сохранения
  if (window.updateReferencesCount) {
    window.updateReferencesCount(currentRefsFieldId);
  }
  closeRefsModal();
  
  // Показываем сообщение об успешном сохранении
  const notification = document.createElement("div");
  notification.style.cssText = "position:fixed;top:20px;right:20px;background:#4caf50;color:#fff;padding:15px 20px;border-radius:4px;box-shadow:0 4px 12px rgba(0,0,0,0.2);z-index:3000;font-size:14px;";
  notification.textContent = "Список литературы обновлен";
  document.body.appendChild(notification);
  setTimeout(() => {
    notification.remove();
  }, 2000);
}

function closeRefsModal() {
  const modal = document.getElementById("refsModal");
  const modalContent = document.getElementById("refsModalContent");
  const expandBtn = document.getElementById("refsModalExpandBtn");
  if (modal) {
    modal.classList.remove("active");
    // Сбрасываем размер при закрытии
    if (modalContent) {
      modalContent.classList.remove("expanded");
    }
    if (expandBtn) {
      expandBtn.classList.remove("expanded");
    }
  }
}

function toggleRefsModalSize() {
  const modalContent = document.getElementById("refsModalContent");
  const expandBtn = document.getElementById("refsModalExpandBtn");
  if (modalContent && expandBtn) {
    const isExpanded = modalContent.classList.contains("expanded");
    if (isExpanded) {
      modalContent.classList.remove("expanded");
      expandBtn.classList.remove("expanded");
      expandBtn.title = "Увеличить окно";
    } else {
      modalContent.classList.add("expanded");
      expandBtn.classList.add("expanded");
      expandBtn.title = "Уменьшить окно";
    }
  }
}

let currentAnnotationFieldId = null;

function annotationTextToHtml(text) {
  if (!text) return "";
  const escaped = escapeHtml(text);
  return escaped
    .replace(/&lt;(sup|sub)&gt;/gi, "<$1>")
    .replace(/&lt;\/(sup|sub)&gt;/gi, "</$1>")
    .replace(/&lt;br\s*\/?&gt;/gi, "<br>")
    .replace(/\n/g, "<br>");
}

function annotationHtmlToText(html) {
  const container = document.createElement("div");
  container.innerHTML = html || "";
  let output = "";

  const walk = (node) => {
    if (node.nodeType === Node.TEXT_NODE) {
      output += node.nodeValue;
      return;
    }
    if (node.nodeType !== Node.ELEMENT_NODE) {
      return;
    }

    const tag = node.tagName;
    const verticalAlign = node.style && node.style.verticalAlign;

    if (verticalAlign === "super") {
      output += "<sup>";
      node.childNodes.forEach(walk);
      output += "</sup>";
      return;
    }
    if (verticalAlign === "sub") {
      output += "<sub>";
      node.childNodes.forEach(walk);
      output += "</sub>";
      return;
    }

    if (tag === "BR") {
      output += "\n";
      return;
    }
    if (tag === "DIV" || tag === "P") {
      if (output && !output.endsWith("\n")) {
        output += "\n";
      }
      node.childNodes.forEach(walk);
      if (!output.endsWith("\n")) {
        output += "\n";
      }
      return;
    }
    if (tag === "SUP") {
      output += "<sup>";
      node.childNodes.forEach(walk);
      output += "</sup>";
      return;
    }
    if (tag === "SUB") {
      output += "<sub>";
      node.childNodes.forEach(walk);
      output += "</sub>";
      return;
    }

    node.childNodes.forEach(walk);
  };

  container.childNodes.forEach(walk);
  return output.replace(/\n{3,}/g, "\n\n").trim();
}

function wrapAnnotationRange(range, tag) {
  const editor = document.getElementById("annotationModalEditor");
  if (!editor) return;
  if (!range || !editor.contains(range.commonAncestorContainer)) return;
  if (range.collapsed) return;

  const selection = window.getSelection();
  const wrapper = document.createElement(tag);

  const content = range.extractContents();
  wrapper.appendChild(content);
  range.insertNode(wrapper);

  const newRange = document.createRange();
  newRange.selectNodeContents(wrapper);
  if (selection) {
    selection.removeAllRanges();
    selection.addRange(newRange);
  }
}



let lastAnnotationSelection = null;
let lastAnnotationOffsets = null;

function getNodeTextLength(node) {
  if (!node) return 0;
  if (node.nodeType === Node.TEXT_NODE) {
    return node.nodeValue.length;
  }
  if (node.nodeType === Node.ELEMENT_NODE) {
    if (node.tagName === "BR") return 1;
    let total = 0;
    node.childNodes.forEach((child) => {
      total += getNodeTextLength(child);
    });
    return total;
  }
  return 0;
}

function computeOffset(editor, container, offset) {
  let total = 0;
  let found = false;

  const walk = (node) => {
    if (found) return;
    if (node === container) {
      if (node.nodeType === Node.TEXT_NODE) {
        total += offset;
      } else {
        for (let i = 0; i < offset; i += 1) {
          total += getNodeTextLength(node.childNodes[i]);
        }
      }
      found = true;
      return;
    }

    if (node.nodeType === Node.TEXT_NODE) {
      total += node.nodeValue.length;
      return;
    }
    if (node.nodeType === Node.ELEMENT_NODE) {
      if (node.tagName === "BR") {
        total += 1;
        return;
      }
      node.childNodes.forEach(walk);
    }
  };

  walk(editor);
  return found ? total : null;
}

function resolveOffset(editor, target) {
  let total = 0;
  let result = null;

  const walk = (node) => {
    if (result) return;
    if (node.nodeType === Node.TEXT_NODE) {
      const len = node.nodeValue.length;
      if (total + len >= target) {
        result = { node: node, offset: target - total };
        return;
      }
      total += len;
      return;
    }
    if (node.nodeType === Node.ELEMENT_NODE) {
      if (node.tagName === "BR") {
        if (total + 1 >= target) {
          const parent = node.parentNode || editor;
          const idx = Array.prototype.indexOf.call(parent.childNodes, node);
          result = { node: parent, offset: Math.max(0, idx) + 1 };
          return;
        }
        total += 1;
        return;
      }
      node.childNodes.forEach(walk);
    }
  };

  walk(editor);
  if (!result) {
    result = { node: editor, offset: editor.childNodes.length };
  }
  return result;
}

function saveAnnotationSelection() {
  const editor = document.getElementById("annotationModalEditor");
  if (!editor) return;
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) return;
  const range = selection.getRangeAt(0);
  if (!editor.contains(range.commonAncestorContainer)) return;

  const start = computeOffset(editor, range.startContainer, range.startOffset);
  const end = computeOffset(editor, range.endContainer, range.endOffset);
  if (start === null || end === null) return;

  lastAnnotationOffsets = { start: start, end: end };
  lastAnnotationSelection = range.cloneRange();
}

function restoreAnnotationSelection() {
  const editor = document.getElementById("annotationModalEditor");
  if (!editor) return;
  if (!lastAnnotationOffsets) return;

  const selection = window.getSelection();
  if (!selection) return;
  const startPos = resolveOffset(editor, lastAnnotationOffsets.start);
  const endPos = resolveOffset(editor, lastAnnotationOffsets.end);
  const range = document.createRange();
  range.setStart(startPos.node, startPos.offset);
  range.setEnd(endPos.node, endPos.offset);
  selection.removeAllRanges();
  selection.addRange(range);
  lastAnnotationSelection = range.cloneRange();
}

function getAnnotationRangeFromOffsets() {
  const editor = document.getElementById("annotationModalEditor");
  if (!editor) return null;
  if (!lastAnnotationOffsets) return null;
  const startPos = resolveOffset(editor, lastAnnotationOffsets.start);
  const endPos = resolveOffset(editor, lastAnnotationOffsets.end);
  if (!startPos || !endPos) return null;
  const range = document.createRange();
  range.setStart(startPos.node, startPos.offset);
  range.setEnd(endPos.node, endPos.offset);
  return range;
}



function unwrapTag(node) {
  if (!node || !node.parentNode) return;
  const parent = node.parentNode;
  const first = node.firstChild;
  const last = node.lastChild;
  while (node.firstChild) {
    parent.insertBefore(node.firstChild, node);
  }
  parent.removeChild(node);

  const selection = window.getSelection();
  if (!selection) return;
  const range = document.createRange();
  if (first && last) {
    range.setStartBefore(first);
    range.setEndAfter(last);
  } else {
    range.selectNodeContents(parent);
  }
  selection.removeAllRanges();
  selection.addRange(range);
}

function unwrapTagInPlace(node) {
  if (!node || !node.parentNode) return;
  const parent = node.parentNode;
  while (node.firstChild) {
    parent.insertBefore(node.firstChild, node);
  }
  parent.removeChild(node);
}


function findAncestorTag(node, tag, editor) {
  let current = node;
  const upper = tag.toUpperCase();
  while (current && current !== editor) {
    if (current.nodeType === Node.ELEMENT_NODE && current.tagName === upper) {
      return current;
    }
    current = current.parentNode;
  }
  return null;
}

function applyAnnotationFormat(action, rangeOverride) {
  const editor = document.getElementById("annotationModalEditor");
  if (!editor) return;

  let range = null;
  if (rangeOverride) {
    const node = rangeOverride.commonAncestorContainer;
    if (!rangeOverride.collapsed && node && editor.contains(node)) {
      range = rangeOverride.cloneRange();
    }
  }
  if (!range) {
    range = getAnnotationRangeFromOffsets();
  }
  if (!range) {
    restoreAnnotationSelection();
    const selection = window.getSelection();
    if (selection && selection.rangeCount > 0) {
      const candidate = selection.getRangeAt(0);
      if (!candidate.collapsed && editor.contains(candidate.commonAncestorContainer)) {
        range = candidate.cloneRange();
      }
    }
  }
  if (!range) return;

  const tag = action === "sup" ? "sup" : "sub";
  const startTag = findAncestorTag(range.startContainer, tag, editor);
  const endTag = findAncestorTag(range.endContainer, tag, editor);
  if (startTag && startTag === endTag) {
    saveAnnotationSelection();
    unwrapTagInPlace(startTag);
    restoreAnnotationSelection();
    return;
  }

  const candidates = Array.from(editor.querySelectorAll(tag));
  const toUnwrap = candidates.filter((node) => {
    try {
      return range.intersectsNode(node);
    } catch (e) {
      return node.contains(range.startContainer) || node.contains(range.endContainer);
    }
  });

  if (toUnwrap.length) {
    saveAnnotationSelection();
    toUnwrap.forEach(unwrapTagInPlace);
    restoreAnnotationSelection();
    return;
  }

  wrapAnnotationRange(range, tag);
  saveAnnotationSelection();
}









if (!window.__annotationSelectionHandlerAdded) {
  document.addEventListener("selectionchange", saveAnnotationSelection);
  window.__annotationSelectionHandlerAdded = true;
}
if (!window.__annotationSelectionSyncAdded) {
  document.addEventListener("mouseup", saveAnnotationSelection, true);
  document.addEventListener("keyup", saveAnnotationSelection, true);
  document.addEventListener("touchend", saveAnnotationSelection, true);
  window.__annotationSelectionSyncAdded = true;
}
if (!window.__annotationEditorMouseDownAdded) {
  const handler = (event) => {
    const button = event.target.closest(".annotation-editor-btn");
    if (!button) return;
    event.preventDefault();
    event.stopPropagation();
    const action = button.getAttribute("data-action");
    applyAnnotationCommand(action);
  };
  document.addEventListener("pointerdown", handler, true);
  document.addEventListener("mousedown", handler, true);
  window.__annotationEditorMouseDownAdded = true;
}
if (!window.__annotationEditorHandlersAdded) {
  document.addEventListener("change", (event) => {
    const select = event.target.closest(".annotation-select");
    if (select) {
      applyAnnotationCommand(select.getAttribute("data-action"), select.value);
      return;
    }
    const color = event.target.closest(".annotation-color-input");
    if (color) {
      applyAnnotationCommand(color.getAttribute("data-action"), color.value);
    }
  });
  document.addEventListener("input", (event) => {
    const editor = event.target.closest("#annotationModalEditor");
    const textarea = event.target.closest("#annotationModalTextarea");
    if (editor || textarea) {
      updateAnnotationStats();
    }
  });
  window.__annotationEditorHandlersAdded = true;
}

function viewAnnotation(fieldId, title) {
  const field = document.getElementById(fieldId);
  if (!field) return;

  currentAnnotationFieldId = fieldId;

  const annotationText = field.value.trim();

  const modal = document.getElementById("annotationModal");
  const modalTitle = document.getElementById("annotationModalTitle");
  const modalEditor = document.getElementById("annotationModalEditor");

  if (!modal || !modalTitle || !modalEditor) return;

  modalTitle.textContent = title;
  modalEditor.innerHTML = annotationTextToHtml(annotationText);
  modal.dataset.fieldId = fieldId;
  if (fieldId === "annotation" || fieldId === "annotation_en") {
    const lang = fieldId === "annotation_en" ? "en" : "ru";
    const textarea = document.getElementById("annotationModalTextarea");
    annotationCodeViewEnabled = false;
    annotationPreviewEnabled = false;
    if (textarea) textarea.style.display = "none";
    modalEditor.style.display = "block";
    modalEditor.contentEditable = "true";
    modalEditor.classList.remove("preview");
    modalEditor.lang = lang;
    const normalize = () => {
      const cleaned = window.processAnnotation(annotationHtmlToText(modalEditor.innerHTML), lang);
      modalEditor.innerHTML = annotationTextToHtml(cleaned);
    };
    modalEditor.onpaste = () => {
      setTimeout(normalize, 0);
    };
    modalEditor.onblur = normalize;
  } else {
    modalEditor.onpaste = null;
    modalEditor.onblur = null;
  }
  updateAnnotationStats();

  modal.classList.add("active");
  setTimeout(() => {
    modalEditor.focus();
    const range = document.createRange();
    range.selectNodeContents(modalEditor);
    range.collapse(true);
    const selection = window.getSelection();
    if (selection) {
      selection.removeAllRanges();
      selection.addRange(range);
      saveAnnotationSelection();
    }
  }, 100);
}

function saveEditedAnnotation() {
  const modal = document.getElementById("annotationModal");
  const fallbackFieldId = modal?.dataset?.fieldId || null;
  const targetFieldId = currentAnnotationFieldId || fallbackFieldId;
  if (!targetFieldId) return;

  const field = document.getElementById(targetFieldId);
  const modalEditor = document.getElementById("annotationModalEditor");
  const modalTextarea = document.getElementById("annotationModalTextarea");

  if (!field || !modalEditor) return;

  const lang = targetFieldId === "annotation_en" ? "en" : "ru";
  const html = annotationCodeViewEnabled && modalTextarea ? modalTextarea.value : modalEditor.innerHTML;
  const cleaned = window.processAnnotation(annotationHtmlToText(html), lang);
  field.value = cleaned;
  closeAnnotationModal();

  const notification = document.createElement("div");
  notification.style.cssText = "position:fixed;top:20px;right:20px;background:#4caf50;color:#fff;padding:15px 20px;border-radius:4px;box-shadow:0 4px 12px rgba(0,0,0,0.2);z-index:3000;font-size:14px;";
  notification.textContent = "\u0410\u043d\u043d\u043e\u0442\u0430\u0446\u0438\u044f \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0430";
  document.body.appendChild(notification);
  setTimeout(() => {
    notification.remove();
  }, 2000);
}

function closeAnnotationModal() {
  const modal = document.getElementById("annotationModal");
  const modalContent = document.getElementById("annotationModalContent");
  const expandBtn = document.getElementById("annotationModalExpandBtn");
  if (modal) {
    modal.classList.remove("active");
    // Сбрасываем размер при закрытии
    if (modalContent) {
      modalContent.classList.remove("expanded");
    }
    if (expandBtn) {
      expandBtn.classList.remove("expanded");
    }
  }
  closeAnnotationSymbolsPanel();
  annotationCodeViewEnabled = false;
  annotationPreviewEnabled = false;
  currentAnnotationFieldId = null;
}

function toggleAnnotationModalSize() {
  const modalContent = document.getElementById("annotationModalContent");
  const expandBtn = document.getElementById("annotationModalExpandBtn");
  if (modalContent && expandBtn) {
    const isExpanded = modalContent.classList.contains("expanded");
    if (isExpanded) {
      modalContent.classList.remove("expanded");
      expandBtn.classList.remove("expanded");
      expandBtn.title = "Увеличить окно";
    } else {
      modalContent.classList.add("expanded");
      expandBtn.classList.add("expanded");
      expandBtn.title = "Уменьшить окно";
    }
  }
}

function enableModalDragging(modalId, contentId) {
  const modal = document.getElementById(modalId);
  const content = document.getElementById(contentId);
  if (!modal || !content || content.dataset.modalInteractionReady === "1") return;
  content.dataset.modalInteractionReady = "1";

  // Используем собственные ручки ресайза вместо системного resize: both
  content.style.resize = "none";

  const handleDirs = ["n", "s", "e", "w", "ne", "nw", "se", "sw"];
  handleDirs.forEach((dir) => {
    const handle = document.createElement("div");
    handle.className = `modal-resize-handle ${dir}`;
    handle.dataset.resizeDir = dir;
    content.appendChild(handle);
  });

  let mode = null; // "drag" | "resize"
  let resizeDir = "";
  let startX = 0;
  let startY = 0;
  let startLeft = 0;
  let startTop = 0;
  let startWidth = 0;
  let startHeight = 0;
  let dragOffsetX = 0;
  let dragOffsetY = 0;

  const getMinSize = () => {
    const styles = window.getComputedStyle(content);
    const minW = parseInt(styles.minWidth || "360", 10) || 360;
    const minH = parseInt(styles.minHeight || "240", 10) || 240;
    return { minW, minH };
  };

  const setFixedRect = () => {
    const rect = content.getBoundingClientRect();
    content.style.position = "fixed";
    content.style.margin = "0";
    content.style.left = `${rect.left}px`;
    content.style.top = `${rect.top}px`;
    content.style.width = `${rect.width}px`;
    content.style.height = `${rect.height}px`;
  };

  const isInteractiveTarget = (target) => {
    if (!target) return false;
    return !!target.closest(
      "input, textarea, select, button, a, [contenteditable='true'], .ref-actions, .annotation-editor-toolbar, .modal-btn, .modal-close"
    );
  };

  const onMouseDown = (event) => {
    if (event.button !== 0) return;
    if (!content.contains(event.target)) return;

    const handle = event.target.closest(".modal-resize-handle");
    setFixedRect();
    const rect = content.getBoundingClientRect();
    startX = event.clientX;
    startY = event.clientY;
    startLeft = rect.left;
    startTop = rect.top;
    startWidth = rect.width;
    startHeight = rect.height;

    if (handle) {
      mode = "resize";
      resizeDir = handle.dataset.resizeDir || "";
      event.preventDefault();
      return;
    }

    if (isInteractiveTarget(event.target)) return;
    mode = "drag";
    dragOffsetX = event.clientX - rect.left;
    dragOffsetY = event.clientY - rect.top;
    event.preventDefault();
  };

  const onMouseMove = (event) => {
    if (!mode) return;
    const { minW, minH } = getMinSize();

    if (mode === "drag") {
      const maxX = window.innerWidth - content.offsetWidth;
      const maxY = window.innerHeight - content.offsetHeight;
      const nextX = Math.min(Math.max(0, event.clientX - dragOffsetX), Math.max(0, maxX));
      const nextY = Math.min(Math.max(0, event.clientY - dragOffsetY), Math.max(0, maxY));
      content.style.left = `${nextX}px`;
      content.style.top = `${nextY}px`;
      return;
    }

    if (mode === "resize") {
      const dx = event.clientX - startX;
      const dy = event.clientY - startY;
      let nextLeft = startLeft;
      let nextTop = startTop;
      let nextWidth = startWidth;
      let nextHeight = startHeight;

      if (resizeDir.includes("e")) {
        nextWidth = Math.max(minW, startWidth + dx);
      }
      if (resizeDir.includes("s")) {
        nextHeight = Math.max(minH, startHeight + dy);
      }
      if (resizeDir.includes("w")) {
        nextWidth = Math.max(minW, startWidth - dx);
        nextLeft = startLeft + (startWidth - nextWidth);
      }
      if (resizeDir.includes("n")) {
        nextHeight = Math.max(minH, startHeight - dy);
        nextTop = startTop + (startHeight - nextHeight);
      }

      if (nextLeft < 0) {
        nextWidth += nextLeft;
        nextLeft = 0;
      }
      if (nextTop < 0) {
        nextHeight += nextTop;
        nextTop = 0;
      }
      nextWidth = Math.max(minW, Math.min(nextWidth, window.innerWidth - nextLeft));
      nextHeight = Math.max(minH, Math.min(nextHeight, window.innerHeight - nextTop));

      content.style.left = `${nextLeft}px`;
      content.style.top = `${nextTop}px`;
      content.style.width = `${nextWidth}px`;
      content.style.height = `${nextHeight}px`;
    }
  };

  const onMouseUp = () => {
    mode = null;
    resizeDir = "";
  };

  content.addEventListener("mousedown", onMouseDown);
  document.addEventListener("mousemove", onMouseMove);
  document.addEventListener("mouseup", onMouseUp);
}

enableModalDragging("refsModal", "refsModalContent");
enableModalDragging("annotationModal", "annotationModalContent");

function openCopyModal(text) {
  const modal = document.getElementById("lineCopyModal");
  const ta = document.getElementById("lineCopyTextarea");
  if (!modal || !ta) return;

  ta.value = text;
  modal.classList.add("active");
  setTimeout(() => {
    ta.focus();
    ta.select(); // можно убрать, если чаще копируют фрагмент, а не всё
  }, 0);
}

function closeCopyModal() {
  document.getElementById("lineCopyModal")?.classList.remove("active");
}

function toast(message) {
  const notification = document.createElement("div");
  notification.style.cssText = "position:fixed;top:20px;right:20px;background:#4caf50;color:#fff;padding:15px 20px;border-radius:4px;box-shadow:0 4px 12px rgba(0,0,0,0.2);z-index:3000;font-size:14px;";
  notification.textContent = message;
  document.body.appendChild(notification);
  setTimeout(() => {
    notification.remove();
  }, 2000);
}

// Обработчик кликов для копирования и закрытия модальных окон
document.addEventListener("click", async (e) => {
  // Открытие модального окна копирования
  const openBtn = e.target.closest('[data-action="open-copy"]');
  if (openBtn) {
    const lineEl = openBtn.closest(".line");
    const text = lineEl?.querySelector(".line-text")?.textContent ?? "";
    openCopyModal(text);
    return;
  }

  // Закрытие модального окна копирования
  if (e.target.closest('[data-action="close-copy"]')) {
    closeCopyModal();
    return;
  }

  // Копирование всего текста из модального окна
  if (e.target.closest('[data-action="copy-from-modal"]')) {
    const ta = document.getElementById("lineCopyTextarea");
    const text = ta?.value ?? "";
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      toast("Скопировано");
      closeCopyModal();
    } catch (err) {
      console.error("Ошибка копирования:", err);
      alert("Не удалось скопировать текст. Попробуйте выделить текст и использовать Ctrl+C");
    }
    return;
  }

  // Закрытие модального окна списка литературы при клике вне его
  const refsModal = document.getElementById("refsModal");
  if (e.target === refsModal) {
    closeRefsModal();
  }
  
  // Закрытие модального окна аннотации при клике вне его
  const annotationModal = document.getElementById("annotationModal");
  if (e.target === annotationModal) {
    closeAnnotationModal();
  }
  
  // Закрытие модального окна копирования при клике вне его
  const lineCopyModal = document.getElementById("lineCopyModal");
  if (e.target === lineCopyModal) {
    closeCopyModal();
  }
});

// Закрытие модальных окон по Escape
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeRefsModal();
    closeAnnotationModal();
    closeCopyModal();
  }
});

// Функции для работы с авторами
function toggleAuthorDetails(index) {
  const details = document.getElementById(`author-details-${index}`);
  const item = document.querySelector(`.author-item[data-author-index="${index}"]`);
  if (details && item) {
    const isExpanded = details.style.display !== "none";
    details.style.display = isExpanded ? "none" : "block";
    item.classList.toggle("expanded", !isExpanded);
  }
}

function getNextAuthorIndex() {
  const authorItems = document.querySelectorAll(".author-item");
  let maxIndex = -1;
  authorItems.forEach(item => {
    const index = parseInt(item.dataset.authorIndex, 10);
    if (!isNaN(index) && index > maxIndex) {
      maxIndex = index;
    }
  });
  return maxIndex + 1;
}

function addNewAuthor() {
  const authorsList = document.getElementById("authors-list");
  if (!authorsList) return;
  
  // Удаляем сообщение "Авторы не указаны", если оно есть
  const emptyMessage = authorsList.querySelector("p");
  if (emptyMessage && emptyMessage.textContent.includes("Авторы не указаны")) {
    emptyMessage.remove();
  }
  
  const newIndex = getNextAuthorIndex();
  const authorHtml = createAuthorHTML(newIndex);
  
  // Создаем временный контейнер для вставки HTML
  const tempDiv = document.createElement("div");
  tempDiv.innerHTML = authorHtml;
  const authorElement = tempDiv.firstElementChild;
  
  authorsList.appendChild(authorElement);
  
  // Автоматически открываем нового автора для редактирования
  toggleAuthorDetails(newIndex);
  
  // Прокручиваем к новому автору
  authorElement.scrollIntoView({ behavior: "smooth", block: "nearest" });
  
  // Добавляем обработчики для обновления имени
  attachAuthorNameListeners(newIndex);
  initOrganizationCards(newIndex);
}

function createAuthorHTML(index) {
  return `
    <div class="author-item" data-author-index="${index}">
      <div class="author-header" onclick="toggleAuthorDetails(${index})">
        <span class="author-name">Новый автор</span>
        <div style="display:flex;align-items:center;gap:10px;">
          <span class="author-toggle">▼</span>
          <button type="button" class="delete-author-btn" onclick="event.stopPropagation(); deleteAuthor(${index})" title="Удалить автора">✕</button>
        </div>
      </div>
      <div class="author-details" id="author-details-${index}" style="display:none;">
        <div class="author-field">
          <label>Ответственный за переписку:</label>
          <div class="correspondence-toggle">
            <label class="toggle-label">
              <input type="checkbox" class="author-correspondence" data-index="${index}">
              <span class="toggle-text">Да</span>
            </label>
          </div>
        </div>
        <div class="author-field">
          <label>Фамилия (русский):</label>
          <input type="text" class="author-input" data-field="surname" data-lang="RUS" data-index="${index}" value="">
        </div>
        <div class="author-field">
          <label>Surname (English):</label>
          <input type="text" class="author-input" data-field="surname" data-lang="ENG" data-index="${index}" value="">
        </div>
        <div class="author-field">
          <label>Инициалы (русский):</label>
          <input type="text" class="author-input" data-field="initials" data-lang="RUS" data-index="${index}" value="">
        </div>
        <div class="author-field">
          <label>Initials (English):</label>
          <input type="text" class="author-input" data-field="initials" data-lang="ENG" data-index="${index}" value="">
        </div>
        <div class="author-field">
          <label>Организации и адреса:</label>
          <div class="author-org-editor" data-index="${index}">
            <div class="author-org-toolbar">
              <button type="button" class="add-author-btn" onclick="addOrganizationCard(${index})">+ Добавить организацию</button>
            </div>
            <div class="author-org-list" id="author-org-list-${index}"></div>
          </div>
          <div class="keywords-count" id="org-count-rus-${index}">Количество организаций: 0</div>
          <div class="keywords-count" id="org-count-eng-${index}">Количество организаций: 0</div>
          <textarea class="author-input author-textarea org-hidden" data-field="orgName" data-lang="RUS" data-index="${index}" rows="2" style="display:none;"></textarea>
          <textarea class="author-input author-textarea org-hidden" data-field="orgName" data-lang="ENG" data-index="${index}" rows="2" style="display:none;"></textarea>
          <input type="text" class="author-input org-hidden" data-field="address" data-lang="RUS" data-index="${index}" value="" style="display:none;">
          <input type="text" class="author-input org-hidden" data-field="address" data-lang="ENG" data-index="${index}" value="" style="display:none;">
        </div>
        <div class="author-field">
          <label>Email:</label>
          <input type="email" class="author-input" data-field="email" data-lang="RUS" data-index="${index}" value="">
        </div>
        <div class="author-field">
          <label>Дополнительная информация (русский):</label>
          <textarea class="author-input" data-field="otherInfo" data-lang="RUS" data-index="${index}" rows="2"></textarea>
        </div>
        <div class="author-field">
          <label>Additional Information (English):</label>
          <textarea class="author-input" data-field="otherInfo" data-lang="ENG" data-index="${index}" rows="2"></textarea>
        </div>
        <div class="author-section">
          <h4>Коды автора</h4>
          <div class="author-field">
            <label>SPIN:</label>
            <input type="text" class="author-input" data-field="spin" data-lang="CODES" data-index="${index}" value="">
          </div>
          <div class="author-field">
            <label>ORCID:</label>
            <input type="text" class="author-input" data-field="orcid" data-lang="CODES" data-index="${index}" value="">
          </div>
          <div class="author-field">
            <label>Scopus ID:</label>
            <input type="text" class="author-input" data-field="scopusid" data-lang="CODES" data-index="${index}" value="">
          </div>
          <div class="author-field">
            <label>Researcher ID:</label>
            <input type="text" class="author-input" data-field="researcherid" data-lang="CODES" data-index="${index}" value="">
          </div>
        </div>
        <div class="author-collapse-actions">
          <button type="button" class="author-collapse-btn" onclick="event.preventDefault(); event.stopPropagation(); toggleAuthorDetails(${index}); document.querySelector('.author-item[data-author-index=&quot;${index}&quot;]')?.scrollIntoView({ block: 'nearest' });">Свернуть</button>
        </div>
      </div>
    </div>
  `;
}

function deleteAuthor(index) {
  if (!confirm("Удалить этого автора?")) return;
  
  const authorItem = document.querySelector(`.author-item[data-author-index="${index}"]`);
  if (authorItem) {
    authorItem.remove();
    
    // Если авторов не осталось, показываем сообщение
    const authorsList = document.getElementById("authors-list");
    if (authorsList && authorsList.querySelectorAll(".author-item").length === 0) {
      authorsList.innerHTML = '<p style="color:#999;font-size:14px;padding:10px;">Авторы не указаны</p>';
    }
  }
}

function updateAuthorName(index) {
  const authorItem = document.querySelector(`.author-item[data-author-index="${index}"]`);
  if (!authorItem) return;
  
  const surnameRus = authorItem.querySelector(`.author-input[data-field="surname"][data-lang="RUS"][data-index="${index}"]`)?.value || "";
  const initialsRus = authorItem.querySelector(`.author-input[data-field="initials"][data-lang="RUS"][data-index="${index}"]`)?.value || "";
  const nameElement = authorItem.querySelector(".author-name");
  
  if (nameElement) {
    const fullName = (surnameRus + " " + initialsRus).trim();
    nameElement.textContent = fullName || "Новый автор";
  }
}

function splitMultiValue(raw) {
  if (!raw) return [];
  return String(raw).split(/[;\n]+/).map((s) => s.trim()).filter(Boolean);
}

function joinMultiValue(items) {
  return (items || []).map((s) => String(s || "").trim()).filter(Boolean).join("; ");
}

function collectOrganizationRows(index) {
  const list = document.getElementById(`author-org-list-${index}`);
  if (!list) return [];
  const cards = Array.from(list.querySelectorAll(".author-org-card"));
  return cards.map((card) => ({
    orgRus: card.querySelector(".org-row-org-rus")?.value || "",
    orgEng: card.querySelector(".org-row-org-eng")?.value || "",
    addressRus: card.querySelector(".org-row-address-rus")?.value || "",
    addressEng: card.querySelector(".org-row-address-eng")?.value || "",
  }));
}

function updateOrganizationCardTitles(index) {
  const list = document.getElementById(`author-org-list-${index}`);
  if (!list) return;
  const cards = Array.from(list.querySelectorAll(".author-org-card"));
  cards.forEach((card, rowIndex) => {
    const title = card.querySelector(".author-org-card-title");
    if (title) title.textContent = `#${rowIndex + 1}`;
  });
}

function autoResizeOrganizationTextarea(el) {
  if (!el) return;
  el.style.height = "auto";
  el.style.height = `${Math.max(el.scrollHeight, 40)}px`;
}

function autoResizeOrganizationTextareas(index) {
  const list = document.getElementById(`author-org-list-${index}`);
  if (!list) return;
  list.querySelectorAll("textarea").forEach(autoResizeOrganizationTextarea);
}

function handleOrganizationCardInput(index, textarea) {
  autoResizeOrganizationTextarea(textarea);
  syncOrganizationCards(index);
}

function syncOrganizationCards(index) {
  const authorItem = document.querySelector(`.author-item[data-author-index="${index}"]`);
  if (!authorItem) return;
  const rows = collectOrganizationRows(index);
  const orgRusInput = authorItem.querySelector(`.author-input[data-field="orgName"][data-lang="RUS"][data-index="${index}"]`);
  const orgEngInput = authorItem.querySelector(`.author-input[data-field="orgName"][data-lang="ENG"][data-index="${index}"]`);
  const addrRusInput = authorItem.querySelector(`.author-input[data-field="address"][data-lang="RUS"][data-index="${index}"]`);
  const addrEngInput = authorItem.querySelector(`.author-input[data-field="address"][data-lang="ENG"][data-index="${index}"]`);
  if (!orgRusInput || !orgEngInput || !addrRusInput || !addrEngInput) return;

  orgRusInput.value = joinMultiValue(rows.map((r) => r.orgRus));
  orgEngInput.value = joinMultiValue(rows.map((r) => r.orgEng));
  addrRusInput.value = joinMultiValue(rows.map((r) => r.addressRus));
  addrEngInput.value = joinMultiValue(rows.map((r) => r.addressEng));

  if (window.updateOrgCount) {
    window.updateOrgCount(index, "RUS");
    window.updateOrgCount(index, "ENG");
  }
}

function orgEscapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderOrganizationRows(index, rows) {
  const list = document.getElementById(`author-org-list-${index}`);
  if (!list) return;
  const safeRows = (rows && rows.length) ? rows : [{ orgRus: "", orgEng: "", addressRus: "", addressEng: "" }];
  list.innerHTML = safeRows.map((row, rowIndex) => `
    <div class="author-org-card" data-org-row="${rowIndex}">
      <div class="author-org-card-header">
        <span class="author-org-card-title">#${rowIndex + 1}</span>
        <div class="author-org-card-actions">
          <button type="button" class="author-org-action-btn" title="Вверх" onclick="moveOrganizationCard(${index}, ${rowIndex}, -1)">↑</button>
          <button type="button" class="author-org-action-btn" title="Вниз" onclick="moveOrganizationCard(${index}, ${rowIndex}, 1)">↓</button>
          <button type="button" class="author-org-action-btn" title="Удалить" onclick="deleteOrganizationCard(${index}, ${rowIndex})">✕</button>
        </div>
      </div>
      <div class="author-org-line">
        <div class="author-org-label">RU:</div>
        <textarea class="author-org-value org-row-org-rus" oninput="handleOrganizationCardInput(${index}, this)">${orgEscapeHtml(row.orgRus)}</textarea>
      </div>
      <div class="author-org-line">
        <div class="author-org-label">EN:</div>
        <textarea class="author-org-value org-row-org-eng" oninput="handleOrganizationCardInput(${index}, this)">${orgEscapeHtml(row.orgEng)}</textarea>
      </div>
      <details class="author-org-addresses">
        <summary>Адреса</summary>
        <div class="author-org-address-wrap">
          <div class="author-org-line">
            <div class="author-org-label">RU:</div>
            <textarea class="author-org-value org-row-address-rus" oninput="handleOrganizationCardInput(${index}, this)">${orgEscapeHtml(row.addressRus)}</textarea>
          </div>
        </div>
        <div class="author-org-address-wrap">
          <div class="author-org-line">
            <div class="author-org-label">EN:</div>
            <textarea class="author-org-value org-row-address-eng" oninput="handleOrganizationCardInput(${index}, this)">${orgEscapeHtml(row.addressEng)}</textarea>
          </div>
        </div>
      </details>
    </div>
  `).join("");

  updateOrganizationCardTitles(index);
  autoResizeOrganizationTextareas(index);
  syncOrganizationCards(index);
}

function initOrganizationCards(index) {
  const authorItem = document.querySelector(`.author-item[data-author-index="${index}"]`);
  if (!authorItem) return;
  const editor = authorItem.querySelector(".author-org-editor");
  if (!editor) return;

  const orgRusInput = authorItem.querySelector(`.author-input[data-field="orgName"][data-lang="RUS"][data-index="${index}"]`);
  const orgEngInput = authorItem.querySelector(`.author-input[data-field="orgName"][data-lang="ENG"][data-index="${index}"]`);
  const addrRusInput = authorItem.querySelector(`.author-input[data-field="address"][data-lang="RUS"][data-index="${index}"]`);
  const addrEngInput = authorItem.querySelector(`.author-input[data-field="address"][data-lang="ENG"][data-index="${index}"]`);
  if (!orgRusInput || !orgEngInput || !addrRusInput || !addrEngInput) return;

  const sourceOrgRus = orgRusInput.value || editor.getAttribute("data-initial-org-rus") || "";
  const sourceOrgEng = orgEngInput.value || editor.getAttribute("data-initial-org-eng") || "";
  const sourceAddrRus = addrRusInput.value || editor.getAttribute("data-initial-address-rus") || "";
  const sourceAddrEng = addrEngInput.value || editor.getAttribute("data-initial-address-eng") || "";

  const orgRus = splitMultiValue(sourceOrgRus);
  const orgEng = splitMultiValue(sourceOrgEng);
  const addrRus = splitMultiValue(sourceAddrRus);
  const addrEng = splitMultiValue(sourceAddrEng);
  const maxRows = Math.max(orgRus.length, orgEng.length, addrRus.length, addrEng.length, 1);
  const rows = [];
  for (let i = 0; i < maxRows; i += 1) {
    rows.push({
      orgRus: orgRus[i] || "",
      orgEng: orgEng[i] || "",
      addressRus: addrRus[i] || "",
      addressEng: addrEng[i] || "",
    });
  }
  renderOrganizationRows(index, rows);
}

function addOrganizationCard(index) {
  const rows = collectOrganizationRows(index);
  rows.push({ orgRus: "", orgEng: "", addressRus: "", addressEng: "" });
  renderOrganizationRows(index, rows);
}

function deleteOrganizationCard(index, rowIndex) {
  const rows = collectOrganizationRows(index);
  rows.splice(rowIndex, 1);
  renderOrganizationRows(index, rows);
}

function moveOrganizationCard(index, rowIndex, direction) {
  const rows = collectOrganizationRows(index);
  const to = rowIndex + direction;
  if (to < 0 || to >= rows.length) return;
  const moved = rows[rowIndex];
  rows[rowIndex] = rows[to];
  rows[to] = moved;
  renderOrganizationRows(index, rows);
}

function attachAuthorNameListeners(index) {
  const authorItem = document.querySelector(`.author-item[data-author-index="${index}"]`);
  if (!authorItem) return;
  
  // Добавляем обработчики для полей фамилии и инициалов
  const surnameInput = authorItem.querySelector(`.author-input[data-field="surname"][data-lang="RUS"][data-index="${index}"]`);
  const initialsInput = authorItem.querySelector(`.author-input[data-field="initials"][data-lang="RUS"][data-index="${index}"]`);
  
  if (surnameInput) {
    surnameInput.addEventListener("input", () => updateAuthorName(index));
  }
  if (initialsInput) {
    initialsInput.addEventListener("input", () => updateAuthorName(index));
  }
  
  // Добавляем обработчики для полей организации
  const orgRusInput = authorItem.querySelector(`.author-input[data-field="orgName"][data-lang="RUS"][data-index="${index}"]`);
  const orgEngInput = authorItem.querySelector(`.author-input[data-field="orgName"][data-lang="ENG"][data-index="${index}"]`);
  
  if (orgRusInput) {
    orgRusInput.addEventListener("input", () => {
      if (window.updateOrgCount) {
        window.updateOrgCount(index, "RUS");
      }
    });
    // Инициализируем счетчик при загрузке с небольшой задержкой
    setTimeout(() => {
      if (window.updateOrgCount) {
        window.updateOrgCount(index, "RUS");
      }
    }, 100);
  }
  if (orgEngInput) {
    orgEngInput.addEventListener("input", () => {
      if (window.updateOrgCount) {
        window.updateOrgCount(index, "ENG");
      }
    });
    // Инициализируем счетчик при загрузке с небольшой задержкой
    setTimeout(() => {
      if (window.updateOrgCount) {
        window.updateOrgCount(index, "ENG");
      }
    }, 100);
  }
}

// Сбор данных авторов из формы
function collectAuthorsData() {
  const authors = [];
  const authorItems = document.querySelectorAll(".author-item");
  
  authorItems.forEach((item, index) => {
    const parsedIndex = parseInt(item.dataset.authorIndex, 10);
    const authorIndex = Number.isNaN(parsedIndex) ? index : parsedIndex;
    syncOrganizationCards(authorIndex);
    const inputs = item.querySelectorAll(".author-input");
    
    // Получаем значение чекбокса "ответственный за переписку"
    const correspondenceCheckbox = item.querySelector(`.author-correspondence[data-index="${authorIndex}"]`);
    const correspondence = correspondenceCheckbox ? correspondenceCheckbox.checked : false;
    
    const author = {
      num: String(authorIndex + 1),
      correspondence: correspondence,
      individInfo: {
        RUS: {},
        ENG: {}
      }
    };
    
    // Инициализируем структуру для кодов автора
    if (!author.individInfo.RUS.authorCodes) {
      author.individInfo.RUS.authorCodes = {};
    }
    if (!author.individInfo.ENG.authorCodes) {
      author.individInfo.ENG.authorCodes = {};
    }
    
    inputs.forEach(input => {
      const field = input.dataset.field;
      const lang = input.dataset.lang;
      // Для textarea сохраняем переносы строк, для input - обрезаем пробелы
      const value = input.tagName === "TEXTAREA" ? input.value : input.value.trim();
      
      if (lang === "CODES") {
        // Коды одинаковые для обоих языков
        author.individInfo.RUS.authorCodes[field] = value;
        author.individInfo.ENG.authorCodes[field] = value;
      } else if (lang === "RUS") {
        author.individInfo.RUS[field] = value;
        // Email одинаковый для обоих языков - сразу копируем в ENG (даже если пустой)
        if (field === "email") {
          author.individInfo.ENG.email = value;
        }
      } else if (lang === "ENG") {
        author.individInfo.ENG[field] = value;
        // Email одинаковый для обоих языков - сразу копируем в RUS (даже если пустой)
        if (field === "email") {
          author.individInfo.RUS.email = value;
        }
      }
    });
    
    // Email одинаковый для обоих языков - убеждаемся, что он синхронизирован
    const emailRus = author.individInfo.RUS.email || "";
    const emailEng = author.individInfo.ENG.email || "";
    // Если в одном поле есть email, а в другом нет - копируем
    if (emailRus && !emailEng) {
      author.individInfo.ENG.email = emailRus;
    } else if (emailEng && !emailRus) {
      author.individInfo.RUS.email = emailEng;
    }
    
    authors.push(author);
  });
  
  return authors;
}

(() => {
  const selected = new Set();
  let currentFieldId = null;
  const pdfBbox = window.PdfBbox || null;

  const $ = (sel, root=document) => root.querySelector(sel);
  const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));

  function updatePanel() {
    const panel = $("#selectionPanel");
    const count = $("#selectedCount");
    if (!panel || !count) return;
    if (selected.size > 0) {
      panel.classList.add("active");
      count.textContent = String(selected.size);
    } else {
      panel.classList.remove("active");
      count.textContent = "0";
    }
  }

  function clearSelection() {
    selected.clear();
    $$(".line.selected").forEach(el => el.classList.remove("selected"));
    updatePanel();
  }

  function enableSelectionPanelDragging() {
    const panel = $("#selectionPanel");
    if (!panel || panel.dataset.dragReady === "1") return;
    panel.dataset.dragReady = "1";

    let dragging = false;
    let offsetX = 0;
    let offsetY = 0;

    const isInteractiveTarget = (target) => {
      if (!target) return false;
      return !!target.closest("button, input, textarea, select, a, label, [contenteditable='true']");
    };

    const clampIntoViewport = () => {
      const maxX = Math.max(0, window.innerWidth - panel.offsetWidth);
      const maxY = Math.max(0, window.innerHeight - panel.offsetHeight);
      const currentLeft = parseFloat(panel.style.left || "0") || 0;
      const currentTop = parseFloat(panel.style.top || "0") || 0;
      panel.style.left = `${Math.min(Math.max(0, currentLeft), maxX)}px`;
      panel.style.top = `${Math.min(Math.max(0, currentTop), maxY)}px`;
    };

    const makeFloating = () => {
      const rect = panel.getBoundingClientRect();
      panel.style.left = `${rect.left}px`;
      panel.style.top = `${rect.top}px`;
      panel.style.bottom = "auto";
      panel.style.right = "auto";
      panel.style.transform = "none";
      panel.style.margin = "0";
      clampIntoViewport();
    };

    panel.addEventListener("mousedown", (event) => {
      if (event.button !== 0) return;
      if (!panel.classList.contains("active")) return;
      if (isInteractiveTarget(event.target)) return;
      makeFloating();
      const rect = panel.getBoundingClientRect();
      dragging = true;
      offsetX = event.clientX - rect.left;
      offsetY = event.clientY - rect.top;
      panel.classList.add("dragging");
      event.preventDefault();
    });

    document.addEventListener("mousemove", (event) => {
      if (!dragging) return;
      const maxX = Math.max(0, window.innerWidth - panel.offsetWidth);
      const maxY = Math.max(0, window.innerHeight - panel.offsetHeight);
      const nextLeft = Math.min(Math.max(0, event.clientX - offsetX), maxX);
      const nextTop = Math.min(Math.max(0, event.clientY - offsetY), maxY);
      panel.style.left = `${nextLeft}px`;
      panel.style.top = `${nextTop}px`;
    });

    document.addEventListener("mouseup", () => {
      if (!dragging) return;
      dragging = false;
      panel.classList.remove("dragging");
    });

    window.addEventListener("resize", () => {
      if (panel.style.left || panel.style.top) {
        clampIntoViewport();
      }
    });
  }

  function getSelectedTexts() {
    return Array.from(selected)
      .map(id => $(`.line[data-id="${CSS.escape(id)}"]`))
      .filter(Boolean)
      .map(el => $(".line-text", el)?.textContent || "")
      .map(t => t.trim())
      .filter(Boolean);
  }

  function extractDOI(text) {
    const m = text.match(/10\.\d{4,}\/[^\s\)]+/);
    return m ? m[0] : null;
  }

  function extractEmail(text) {
    // Регулярное выражение для поиска e-mail адресов
    // Поддерживает стандартные форматы: user@domain.com, user.name@domain.co.uk и т.д.
    const emailPattern = /\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b/g;
    const matches = text.match(emailPattern);
    if (matches && matches.length > 0) {
      // Возвращаем первый найденный e-mail
      return matches[0];
    }
    return null;
  }

  function extractORCID(text) {
    // ORCID формат: 0000-0000-0000-0000 (16 цифр, разделенных дефисами)
    // Также может быть в формате https://orcid.org/0000-0000-0000-0000
    const orcidPattern = /(?:orcid\.org\/)?(\d{4}-\d{4}-\d{4}-\d{3}[\dX])/i;
    const match = text.match(orcidPattern);
    return match ? match[1] : null;
  }

  function extractSPIN(text) {
    // SPIN обычно числовой код, может быть указан как "SPIN: 1234-5678", "SPIN-код 264275" или просто число
    // Поддерживаем различные форматы: SPIN-код, SPIN код, SPIN:, AuthorID и т.д.
    // SPIN код обычно состоит из 4-8 цифр, может быть с дефисами или без
    
    // Сначала ищем явные упоминания SPIN или AuthorID
    const explicitPatterns = [
      /(?:SPIN[-]?код|SPIN\s*код|SPIN[:\s-]+|AuthorID[:\s]+)\s*(\d{4,8}(?:[-.\s]\d+)*)/i,
    ];
    
    for (const pattern of explicitPatterns) {
      const match = text.match(pattern);
      if (match) {
        // Убираем дефисы, точки и пробелы, оставляем только цифры
        const spin = match[1].replace(/[-.\s]/g, '');
        // SPIN код обычно от 4 до 8 цифр
        if (spin.length >= 4 && spin.length <= 8) {
          // Проверяем, что это не часть email или другого кода
          const beforeMatch = text.substring(0, match.index);
          const afterMatch = text.substring(match.index + match[0].length);
          // Исключаем числа, которые являются частью email
          if (!beforeMatch.match(/@[\w.-]*$/) && !afterMatch.match(/^[\w.-]*@/)) {
            return spin;
          }
        }
      }
    }
    
    // Если явных упоминаний нет, ищем числа 4-8 цифр, но только если они не являются частью других кодов
    // Исключаем числа, которые являются частью email, DOI, ORCID, Scopus ID и т.д.
    const standaloneNumberPattern = /\b(\d{4,8})\b/g;
    const matches = [...text.matchAll(standaloneNumberPattern)];
    
    for (const match of matches) {
      const number = match[1];
      const matchIndex = match.index;
      const beforeText = text.substring(Math.max(0, matchIndex - 20), matchIndex);
      const afterText = text.substring(matchIndex + number.length, Math.min(text.length, matchIndex + number.length + 20));
      
      // Пропускаем, если это часть email
      if (beforeText.match(/@[\w.-]*$/) || afterText.match(/^[\w.-]*@/)) {
        continue;
      }
      
      // Пропускаем, если это часть DOI (10.xxxx/...)
      if (beforeText.match(/10\.\d{4,}/) || afterText.match(/^\/[^\s\)]+/)) {
        continue;
      }
      
      // Пропускаем, если это часть ORCID (0000-0000-0000-0000)
      if (beforeText.match(/orcid/i) || afterText.match(/^-\d{4}-\d{4}-\d{3}/)) {
        continue;
      }
      
      // Пропускаем, если это часть Scopus ID (обычно 8+ цифр)
      if (beforeText.match(/scopus/i) || number.length >= 8) {
        continue;
      }
      
      // Пропускаем, если это часть Researcher ID (A-1234-5678)
      if (beforeText.match(/researcher\s*id/i) || afterText.match(/^-\d{4}-\d{4}/)) {
        continue;
      }
      
      // Если число не является частью других кодов, возвращаем его как SPIN
      return number;
    }
    
    return null;
  }

  function extractScopusID(text) {
    // Scopus ID - числовой код, может быть указан как "Scopus ID: 123456789" или просто число
    const scopusPattern = /(?:Scopus\s*ID[:\s]*)?(\d{8,})/i;
    const match = text.match(scopusPattern);
    return match ? match[1] : null;
  }

  function extractResearcherID(text) {
    // Researcher ID может быть в формате A-XXXX-XXXX или просто числовой код
    const researcherPattern = /(?:Researcher\s*ID[:\s]*)?([A-Z]-\d{4}-\d{4}|\d{8,})/i;
    const match = text.match(researcherPattern);
    return match ? match[1] : null;
  }

  const AUTO_EXTRACT_AUTHOR_CODES = false;

function autoExtractAuthorDataFromLine(text, authorIndex, skipField = null) {
    if (!AUTO_EXTRACT_AUTHOR_CODES) {
      return;
    }

    // Автоматически извлекает все доступные данные автора из строки и заполняет соответствующие поля
    // Это полезно, когда в одной строке содержится несколько данных (SPIN, email, AuthorID и т.д.)
    // skipField - поле, которое уже заполнено и не нужно извлекать повторно
    
    // Небольшая задержка, чтобы убедиться, что основное поле уже заполнено
    setTimeout(() => {
      // Извлекаем email, если он еще не заполнен и это не то поле, которое мы только что заполнили
      if (!skip.has("email")) {
        const emailField = $(`.author-input[data-field="email"][data-lang="RUS"][data-index="${authorIndex}"]`);
        if (emailField) {
          const currentValue = emailField.value.trim();
          if (!currentValue) {
            const email = extractEmail(text);
            if (email) {
              emailField.value = email;
              emailField.dispatchEvent(new Event('input', { bubbles: true }));
              const emailEngField = $(`.author-input[data-field="email"][data-lang="ENG"][data-index="${authorIndex}"]`);
              if (emailEngField) {
                emailEngField.value = email;
                emailEngField.dispatchEvent(new Event('input', { bubbles: true }));
              }
            }
          }
        }
      }
      
      // Извлекаем SPIN, если он еще не заполнен и это не то поле, которое мы только что заполнили
      if (!skip.has("spin")) {
        const spinField = $(`.author-input[data-field="spin"][data-lang="CODES"][data-index="${authorIndex}"]`);
        if (spinField) {
          const currentValue = spinField.value.trim();
          if (!currentValue) {
            const spin = extractSPIN(text);
            if (spin) {
              spinField.value = spin;
              spinField.dispatchEvent(new Event('input', { bubbles: true }));
            }
          }
        }
      }
      
      // Извлекаем ORCID, если он еще не заполнен и это не то поле, которое мы только что заполнили
      if (!skip.has("orcid")) {
        const orcidField = $(`.author-input[data-field="orcid"][data-lang="CODES"][data-index="${authorIndex}"]`);
        if (orcidField) {
          const currentValue = orcidField.value.trim();
          if (!currentValue) {
            const orcid = extractORCID(text);
            if (orcid) {
              orcidField.value = orcid;
              orcidField.dispatchEvent(new Event('input', { bubbles: true }));
            }
          }
        }
      }
      
      // Извлекаем Scopus ID, если он еще не заполнен и это не то поле, которое мы только что заполнили
      if (!skip.has("scopusid")) {
        const scopusField = $(`.author-input[data-field="scopusid"][data-lang="CODES"][data-index="${authorIndex}"]`);
        if (scopusField) {
          const currentValue = scopusField.value.trim();
          if (!currentValue) {
            const scopusId = extractScopusID(text);
            if (scopusId) {
              scopusField.value = scopusId;
              scopusField.dispatchEvent(new Event('input', { bubbles: true }));
            }
          }
        }
      }
      
      // Извлекаем Researcher ID, если он еще не заполнен и это не то поле, которое мы только что заполнили
      if (!skip.has("researcherid")) {
        const researcherField = $(`.author-input[data-field="researcherid"][data-lang="CODES"][data-index="${authorIndex}"]`);
        if (researcherField) {
          const currentValue = researcherField.value.trim();
          if (!currentValue) {
            const researcherId = extractResearcherID(text);
            if (researcherId) {
              researcherField.value = researcherId;
              researcherField.dispatchEvent(new Event('input', { bubbles: true }));
            }
          }
        }
      }
    }, 10); // Небольшая задержка 10мс для гарантии, что основное поле заполнено
  }

  function removeCountryFromAddress(text) {
    // Список названий стран на русском и английском языках
    const countries = [
      // Русские названия
      'Россия', 'Российская Федерация', 'РФ',
      'Украина', 'Беларусь', 'Белоруссия', 'Казахстан',
      'Германия', 'Франция', 'Италия', 'Испания', 'Польша',
      'США', 'Соединенные Штаты', 'Соединённые Штаты', 'Соединенные Штаты Америки', 'Соединённые Штаты Америки',
      'Великобритания', 'Соединенное Королевство', 'Соединённое Королевство',
      'Китай', 'Япония', 'Индия', 'Бразилия',
      // Английские названия
      'Russia', 'Russian Federation', 'RF',
      'Ukraine', 'Belarus', 'Kazakhstan',
      'Germany', 'France', 'Italy', 'Spain', 'Poland',
      'USA', 'United States', 'United States of America', 'US', 'U.S.', 'U.S.A.',
      'United Kingdom', 'UK', 'U.K.',
      'China', 'Japan', 'India', 'Brazil',
      // Общие паттерны
      'Российская', 'Российской', 'Российскому',
      'Russian', 'Russians'
    ];
    
    let cleanedText = text.trim();
    
    // Удаляем названия стран из текста
    for (const country of countries) {
      // Создаем регулярное выражение для поиска названия страны
      // Ищем как отдельное слово (с границами слов) и в конце строки
      const pattern = new RegExp(`\\b${country.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'gi');
      cleanedText = cleanedText.replace(pattern, '').trim();
    }
    
    // Удаляем лишние запятые и пробелы
    cleanedText = cleanedText.replace(/^[,.\s]+|[,.\s]+$/g, '').trim();
    cleanedText = cleanedText.replace(/\s*,\s*,/g, ','); // Убираем двойные запятые
    cleanedText = cleanedText.replace(/\s{2,}/g, ' '); // Убираем множественные пробелы
    
    return cleanedText;
  }

  function removeNameFromText(text) {
    // Паттерны для удаления ФИО из текста
    // Русские имена: Фамилия Имя Отчество, Имя Отчество Фамилия, Фамилия И.О., И.О. Фамилия
    // Английские имена: First Last, Last, First, First M. Last, Last, First M.
    
    let cleanedText = text.trim();
    
    // Паттерны для русских имен
    const russianPatterns = [
      // Фамилия Имя Отчество (полное)
      /\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\b/g,
      // Имя Отчество Фамилия
      /\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\b/g,
      // Фамилия И.О.
      /\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.\s*[А-ЯЁ]\./g,
      // И.О. Фамилия
      /\b[А-ЯЁ]\.\s*[А-ЯЁ]\.\s+[А-ЯЁ][а-яё]+\b/g,
      // Фамилия И.
      /\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\./g,
      // И. Фамилия
      /\b[А-ЯЁ]\.\s+[А-ЯЁ][а-яё]+\b/g,
    ];
    
    // Паттерны для английских имен
    const englishPatterns = [
      // First Last
      /\b[A-Z][a-z]+\s+[A-Z][a-z]+\b/g,
      // Last, First
      /\b[A-Z][a-z]+,\s*[A-Z][a-z]+\b/g,
      // First M. Last
      /\b[A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+\b/g,
      // Last, First M.
      /\b[A-Z][a-z]+,\s*[A-Z][a-z]+\s+[A-Z]\./g,
      // First Last, Jr./Sr.
      /\b[A-Z][a-z]+\s+[A-Z][a-z]+,\s*(?:Jr\.?|Sr\.?|III|II|IV)\b/gi,
    ];
    
    // Удаляем русские имена
    for (const pattern of russianPatterns) {
      cleanedText = cleanedText.replace(pattern, '').trim();
    }
    
    // Удаляем английские имена
    for (const pattern of englishPatterns) {
      cleanedText = cleanedText.replace(pattern, '').trim();
    }
    
    // Удаляем лишние запятые, точки и пробелы
    cleanedText = cleanedText.replace(/^[,.\s]+|[,.\s]+$/g, '').trim();
    cleanedText = cleanedText.replace(/\s*,\s*,/g, ','); // Убираем двойные запятые
    cleanedText = cleanedText.replace(/\s{2,}/g, ' '); // Убираем множественные пробелы
    
    return cleanedText;
  }

  function extractDate(text) {
    if (!text) return null;
    const datePatterns = [
      /\b(\d{1,2}[./]\d{1,2}[./]\d{4})\b/,
      /\b(\d{4}[-./]\d{1,2}[-./]\d{1,2})\b/,
      /\b(\d{1,2}[-]\d{1,2}[-]\d{4})\b/,
    ];
    for (const pattern of datePatterns) {
      const match = text.match(pattern);
      if (match) {
        let date = match[1].replace(/[\/-]/g, '.');
        if (/^\d{4}\.\d{1,2}\.\d{1,2}$/.test(date)) {
          const parts = date.split('.');
          date = `${parts[2]}.${parts[1]}.${parts[0]}`;
        }
        return date;
      }
    }
    return null;
  }

  function extractUDC(text) {
    if (!text) return null;
    // ????? ??? ????? ???/UDC ?? ????? ?????? (????? ????? ????????????)
    const prefixRe = new RegExp("(?:\\u0423\\u0414\\u041a|UDC)\\s*:?\\s*([^\\n]+)", "i");
    const match = text.match(prefixRe);
    if (match) {
      return match[1]
        .replace(/\s+/g, " ")
        .replace(/\s*[.;,]\s*$/g, "")
        .trim();
    }
    return null;
  }




  function extractYear(text) {
    if (!text) return null;
    const yearPattern = /\b(19\d{2}|20\d{2})\b/;
    const match = text.match(yearPattern);
    if (match) {
      const year = parseInt(match[1], 10);
      if (year >= 1900 && year <= 2100) return String(year);
    }
    return null;
  }

  function processKeywords(text) {
    if (!text) return "";
    let cleaned = text.replace(/^(Keywords|Ключевые слова)\s*:?\s*/i, "").trim();
    if (cleaned.includes(";")) {
      return cleaned.split(";").map(s => s.trim()).filter(Boolean).join("; ");
    }
    if (cleaned.includes(",")) {
      return cleaned.split(",").map(s => s.trim()).filter(Boolean).join("; ");
    }
    return cleaned;
  }

  function countKeywords(text) {
    if (!text || !text.trim()) return 0;
    const cleaned = text.trim();
    // Подсчитываем количество ключевых слов, разделенных точкой с запятой или запятой
    if (cleaned.includes(";")) {
      return cleaned.split(";").map(s => s.trim()).filter(Boolean).length;
    }
    // Если нет разделителей, считаем как одно слово
    return cleaned ? 1 : 0;
  }

  function updateKeywordsCount(fieldId) {
    const field = document.getElementById(fieldId);
    const countEl = document.getElementById(fieldId + "-count");
    if (!field || !countEl) return;
    
    const count = countKeywords(field.value);
    countEl.textContent = `Количество: ${count}`;
  }

  function autoResizeKeywordsField(fieldId) {
    const field = document.getElementById(fieldId);
    if (!field || field.tagName !== "TEXTAREA") return;
    field.style.height = "auto";
    field.style.height = `${Math.max(field.scrollHeight, 72)}px`;
  }

  window.countOrganizations = function(text, lang) {
    if (!text || !text.trim()) return 0;
    const cleaned = text.trim();
    const langNorm = (lang || "").toLowerCase();
    // В англоязычных организациях разделитель - ";" (такой формат чаще для англ. организаций)
    if (langNorm.startsWith("en")) {
      return cleaned.includes(";")
        ? cleaned.split(";").map(s => s.trim()).filter(Boolean).length
        : 1;
    }
    if (cleaned.includes(";")) {
      return cleaned.split(";").map(s => s.trim()).filter(Boolean).length;
    }
    return cleaned ? 1 : 0;
  };

  window.updateOrgCount = function(authorIndex, lang) {
    const field = document.querySelector(`.author-input[data-field="orgName"][data-lang="${lang}"][data-index="${authorIndex}"]`);
    const countEl = document.getElementById(`org-count-${lang.toLowerCase()}-${authorIndex}`);
    if (!field || !countEl) return;
    
    const count = window.countOrganizations(field.value, lang);
    countEl.textContent = `Количество организаций: ${count}`;
  };

  window.countReferences = function(text, strict) {
    if (!text || !text.trim()) return 0;
    if (strict && typeof splitReferencesStrict === "function") {
      return splitReferencesStrict(text).length;
    }
    if (typeof splitReferences === "function") {
      return splitReferences(text).length;
    }
    const lines = text.split("\n")
      .map(line => line.trim())
      .filter(line => line.length > 0);
    return lines.length;
  };

  window.updateReferencesCount = function(fieldId) {
    const field = document.getElementById(fieldId);
    const countEl = document.getElementById(fieldId + "-count");
    if (!field || !countEl) return;
    
    const useStrict = field.dataset && field.dataset.aiProcessed === "1";
    const count = window.countReferences(field.value, useStrict);
    countEl.textContent = `Количество источников: ${count}`;
  };

  function processFunding(text, lang) {
    if (!text) return "";
    const hasCyr = /[А-Яа-яЁё]/.test(text);
    const detected = hasCyr ? "ru" : "en";
    const langToUse = lang || detected;
    const prefixRe = /^(Финансирование|Funding)\s*[.:]?\s*/i;
    let cleaned = String(text).replace(prefixRe, "");
    cleaned = cleaned.replace(/\r\n?/g, "\n");
    cleaned = cleaned.replace(/\u00ad/g, "");
    cleaned = cleaned.replace(/([A-Za-zА-Яа-яЁё'])[-‑–—]\s*\n\s*([A-Za-zА-Яа-яЁё'])/g, "$1$2");
    cleaned = cleaned.replace(/[ \t]*\n[ \t]*/g, " ");
    cleaned = cleaned.replace(/[ \t]+/g, " ");
    cleaned = repairBrokenWords(cleaned, langToUse);
    return cleaned.trim();
  }

  function repairBrokenWords(text, lang) {
    const stopRu = new Set([
      "и","в","во","на","к","с","со","у","о","об","от","до","по","за","из",
      "не","ни","но","ли","же","бы","мы","вы","я","он","она","они","это","то",
      "как","при","для","без","над","под","про","так","или","а"
    ]);
    const suffixesRu = new Set([
      "го","ому","ыми","ый","ая","ое","ые","ого","овой","овке","овки","овка",
      "ении","ение","ения","ению","ением","ность","ности","ностью",
      "ский","ского","ская","ские","ских","ческим","ческой","ческих","ческого",
      "тельный","тельного","тельная","тельные","тельным","тельными",
      "дательный","дательного","дательной","дательным","дательными"
    ]);
    const stopEn = new Set([
      "a","an","the","and","or","but","if","then","of","to","in","on","at","by","for",
      "with","as","is","are","was","were","be","been","being","this","that","these",
      "those","it","its","from","into","not","no","so"
    ]);
    const suffixesEn = new Set([
      "tion","tions","ing","ed","ly","al","ment","ence","ance","ous","able","ible",
      "ity","ize","izes","ized","ization","ative","ness","less","ful","ical","ically",
      "sion","sions","ious","ably","ist","ists","ism","isms"
    ]);
    const prefixesEn = new Set([
      "inter","multi","micro","macro","post","pre","sub","super","trans","poly",
      "mono","neo","auto","meta","socio","eco"
    ]);
    const stop = lang === "en" ? stopEn : stopRu;
    const suffixes = lang === "en" ? suffixesEn : suffixesRu;
    const prefixes = lang === "en" ? prefixesEn : null;
    return text.replace(/\b([A-Za-zА-Яа-яЁё]+)\s+([A-Za-zА-Яа-яЁё]+)\b/g, (m, a, b) => {
      const aLower = a.toLowerCase();
      const bLower = b.toLowerCase();
      const aIsLower = a === aLower;
      const bIsLower = b === bLower;
      if (aLower.length <= 2 && !stop.has(aLower) && aIsLower) return a + b;
      if (bLower.length <= 2 && !stop.has(bLower) && bIsLower) return a + b;
      if (prefixes && prefixes.has(aLower)) return a + b;
      if (bLower.startsWith("дователь")) return a + b;
      if (suffixes.has(bLower)) return a + b;
      return m;
    });
  }

  window.processAnnotation = function processAnnotation(text, lang) {
    if (!text) return "";
    const hasCyr = /[А-Яа-яЁё]/.test(text);
    const detected = hasCyr ? "ru" : "en";
    const langToUse = lang || detected;
    // Удаляем префикс и чистим переносы/разрывы слов из PDF
    const prefixRe = langToUse === "en"
      ? /^(Annotation|Abstract|Summary|Resume|Résumé)\s*[.:]?\s*/i
      : /^(Аннотация|Резюме|Аннот\.|Рез\.|Annotation|Abstract|Summary)\s*[.:]?\s*/i;
    let cleaned = String(text).replace(prefixRe, "");
    cleaned = cleaned.replace(/\r\n?/g, "\n");
    cleaned = cleaned.replace(/\u00ad/g, "");
    cleaned = cleaned.replace(/([A-Za-zА-Яа-яЁё])[-‑–—]\s*\n\s*([A-Za-zА-Яа-яЁё])/g, "$1$2");
    cleaned = cleaned.replace(/[ \t]*\n[ \t]*/g, " ");
    cleaned = cleaned.replace(/[ \t]+/g, " ");
    cleaned = repairBrokenWords(cleaned, langToUse);
    return cleaned.trim();
  };

  function processReferences(texts) {
    const processed = [];
    texts.forEach(text => {
      // Удаляем нумерацию в начале строки (например, "1. ", "2. "), но сохраняем остальной текст
      let cleaned = String(text).replace(/^\d+\.\s*/, "").replace(/\t/g, " ").replace(/\s+/g, " ").trim();
      if (!cleaned) return;
      const isUrl = /^(https?:\/\/|doi\.org\/|doi:\s*|http:\/\/dx\.doi\.org\/)/i.test(cleaned);
      if (isUrl && processed.length > 0) {
        processed[processed.length - 1] += " " + cleaned;
      } else {
        processed.push(cleaned);
      }
    });
    return processed.filter(Boolean);
  }

  window.extractUDC = extractUDC;
  window.processKeywords = processKeywords;
  window.processFunding = processFunding;
  window.processReferences = processReferences;
  
  function mergeDoiUrlWithReferences(refs) {
    if (!refs || refs.length === 0) return refs;
    const result = [];
    const doiUrlPattern = /^(https?:\/\/|doi\.org\/|doi:\s*|http:\/\/dx\.doi\.org\/)/i;
    refs.forEach(ref => {
      const cleaned = String(ref).trim();
      if (!cleaned) return;
      if (doiUrlPattern.test(cleaned) && result.length > 0) {
        result[result.length - 1] += " " + cleaned;
      } else {
        result.push(cleaned);
      }
    });
    return result;
  }

  function markField(fieldId) {
    const field = document.getElementById(fieldId);
    if (!field) return;
    const group = field.closest(".field-group");
    if (!group) return;
    group.classList.add("active");
    setTimeout(() => group.classList.remove("active"), 1200);
  }

  function setLinesInfo(fieldId, n) {
    const el = document.getElementById(fieldId + "-lines");
    if (el) el.textContent = n ? `Выбрано строк: ${n}` : "";
  }

  function getActiveAuthorIndex() {
    // Находим первого открытого (expanded) автора
    const authorItems = $$(".author-item");
    for (const item of authorItems) {
      const index = item.dataset.authorIndex;
      if (index !== undefined) {
        const details = $(`#author-details-${index}`);
        if (details && details.style.display !== "none") {
          return parseInt(index, 10);
        }
      }
    }
    // Если ни один не открыт, возвращаем первого автора
    if (authorItems.length > 0) {
      const firstIndex = authorItems[0].dataset.authorIndex;
      if (firstIndex !== undefined) {
        return parseInt(firstIndex, 10);
      }
    }
    return 0;
  }

  function extractSurnameFromText(text) {
    const raw = String(text || "").replace(/\s+/g, " ").trim();
    if (!raw) return "";
    const cleaned = raw
      .replace(/^\d+[)\.]?\s+/, "")
      .replace(/[,:;]+/g, " ")
      .trim();
    if (!cleaned) return "";
    const parts = cleaned.split(" ").filter(Boolean);
    if (!parts.length) return "";

    const LETTER = "[A-Za-z\\u0410-\\u042F\\u0401\\u0430-\\u044F\\u0451]";
    const DASH_RE = new RegExp("[\\u2013\\u2014-]", "g");
    const RE_INITIAL_1 = new RegExp("^" + LETTER + "\\\\.$");
    const RE_INITIAL_2 = new RegExp("^" + LETTER + "\\\\." + LETTER + "\\\\.?$");
    const RE_INITIAL_H = new RegExp("^" + LETTER + "\\\\.-" + LETTER + "\\\\.?$");
    const RE_INITIAL_3 = new RegExp("^" + LETTER + "\\\\." + LETTER + "\\\\.-" + LETTER + "\\\\.?$");

    const isInitial = (token) => {
      const t = String(token || "").replace(DASH_RE, "-");
      return RE_INITIAL_1.test(t)
        || RE_INITIAL_2.test(t)
        || RE_INITIAL_H.test(t)
        || RE_INITIAL_3.test(t);
    };

    const particles = new Set([
      "da","de","del","della","di","du","des","la","le",
      "van","von","der","den","ter","ten","zu","zur","zum",
      "al","el","bin","ibn","dos","das","do","d'","o'",
      "st.","st","saint","san","sant"
    ]);

    const nonInitials = parts.filter(p => !isInitial(p));
    if (nonInitials.length) {
      let idx = nonInitials.length - 1;
      let surnameParts = [nonInitials[idx].replace(/[\.]+$/g, "")];

      while (idx - 1 >= 0) {
        const prev = nonInitials[idx - 1];
        const prevNorm = prev.toLowerCase().replace(/[\.]+$/g, "");
        if (particles.has(prevNorm)) {
          surnameParts.unshift(prev.replace(/[\.]+$/g, ""));
          idx -= 1;
        } else {
          break;
        }
      }

      return surnameParts.join(" ");
    }

    return parts[parts.length - 1].replace(/[\.]+$/g, "");
  }


function extractInitialsFromText(text) {
    const raw = String(text || "");
    if (!raw.trim()) return "";

    const LETTER = "[A-Za-z\\u0410-\\u042F\\u0401\\u0430-\\u044F\\u0451]";
    const DASH_RE = new RegExp("[\\u2013\\u2014-]", "g");
    const RE_INITIAL_1 = new RegExp("^" + LETTER + "\\\\.$");
    const RE_INITIAL_2 = new RegExp("^" + LETTER + "\\\\." + LETTER + "\\\\.?$");
    const RE_INITIAL_H = new RegExp("^" + LETTER + "\\\\.-" + LETTER + "\\\\.?$");
    const RE_INITIAL_3 = new RegExp("^" + LETTER + "\\\\." + LETTER + "\\\\.-" + LETTER + "\\\\.?$");

    const compactRe = new RegExp(LETTER + "\\\\.?\\\\s*" + LETTER + "?\\\\.?", "g");
    const compactMatches = raw.match(compactRe) || [];
    for (const m of compactMatches) {
      const cleaned = m.replace(/\s+/g, "");
      if (RE_INITIAL_2.test(cleaned)) {
        return cleaned[0] + "." + " " + cleaned[2] + ".";
      }
    }

    const cleaned = raw
      .replace(/\s+/g, " ")
      .replace(/^\d+[)\.]?\s+/, "")
      .replace(/[,:;]+/g, " ")
      .trim();
    if (!cleaned) return "";
    const parts = cleaned.split(" ").filter(Boolean);
    if (!parts.length) return "";

    const spaced = parts.filter(p => {
      const t = String(p || "").replace(DASH_RE, "-");
      return RE_INITIAL_1.test(t) || RE_INITIAL_2.test(t) || RE_INITIAL_H.test(t) || RE_INITIAL_3.test(t);
    });
    if (spaced.length) {
      return spaced.join(" ");
    }

    const letters = parts.slice(0, 2).map(p => p[0]).filter(Boolean);
    if (letters.length) {
      return letters.map(ch => ch + ".").join(" ");
    }

    return "";
  }









function applySelectionToField(fieldId) {
    const texts = getSelectedTexts();
    if (!texts.length) return;
    const fullText = texts.join(" ");
    let value = "";
    
    // Обработка полей авторов
    if (fieldId.startsWith("author_")) {
      const authorIndex = getActiveAuthorIndex();
      const parts = fieldId.split("_");
      if (parts.length < 2) return;
      
      const fieldName = parts[1]; // surname, initials, org, address, email, other
      const lang = parts.length >= 3 ? parts[2] : null; // rus, eng, или null для email
      
      // Находим соответствующее поле автора
      let targetField = null;
      if (fieldName === "surname") {
        if (!lang) return;
        targetField = $(`.author-input[data-field="surname"][data-lang="${lang.toUpperCase()}"][data-index="${authorIndex}"]`);
        value = extractSurnameFromText(fullText);
      } else if (fieldName === "initials") {
        if (!lang) return;
        targetField = $(`.author-input[data-field="initials"][data-lang="${lang.toUpperCase()}"][data-index="${authorIndex}"]`);
        value = extractInitialsFromText(fullText);
      } else if (fieldName === "org") {
        if (!lang) return;
        targetField = $(`.author-input[data-field="orgName"][data-lang="${lang.toUpperCase()}"][data-index="${authorIndex}"]`);
        value = fullText.trim();
      } else if (fieldName === "address") {
        if (!lang) return;
        targetField = $(`.author-input[data-field="address"][data-lang="${lang.toUpperCase()}"][data-index="${authorIndex}"]`);
        // Удаляем названия стран из адреса
        value = removeCountryFromAddress(fullText);
      } else if (fieldName === "email") {
        targetField = $(`.author-input[data-field="email"][data-lang="RUS"][data-index="${authorIndex}"]`);
        // Извлекаем только e-mail адрес из выделенного текста
        const email = extractEmail(fullText);
        if (!email) {
          alert("E-mail адрес не найден в выделенном тексте. Убедитесь, что выделен текст, содержащий e-mail (например: user@domain.com)");
          return;
        }
        value = email;
        // E-mail одинаковый для обоих языков - всегда копируем в ENG поле
        const emailEngField = $(`.author-input[data-field="email"][data-lang="ENG"][data-index="${authorIndex}"]`);
        if (emailEngField) {
          emailEngField.value = email;
        }
        // Автоматически извлекаем и заполняем другие поля из той же строки (пропускаем email, т.к. он уже заполнен)
        autoExtractAuthorDataFromLine(fullText, authorIndex, "email");
      } else if (fieldName === "spin") {
        targetField = $(`.author-input[data-field="spin"][data-lang="CODES"][data-index="${authorIndex}"]`);
        if (!targetField) {
          alert(`Поле SPIN не найдено. Убедитесь, что форма автора открыта.`);
          return;
        }
        const spin = extractSPIN(fullText);
        if (!spin) {
          alert("SPIN код не найден в выделенном тексте. Убедитесь, что выделен текст, содержащий SPIN (например: SPIN: 1234-5678)");
          return;
        }
        value = spin;
        // Автоматически извлекаем и заполняем другие поля из той же строки (пропускаем spin, т.к. он уже заполнен)
        autoExtractAuthorDataFromLine(fullText, authorIndex, "spin");
      } else if (fieldName === "orcid") {
        targetField = $(`.author-input[data-field="orcid"][data-lang="CODES"][data-index="${authorIndex}"]`);
        if (!targetField) {
          alert(`Поле ORCID не найдено. Убедитесь, что форма автора открыта.`);
          return;
        }
        const orcid = extractORCID(fullText);
        if (!orcid) {
          alert("ORCID не найден в выделенном тексте. Убедитесь, что выделен текст, содержащий ORCID (например: 0000-0000-0000-0000)");
          return;
        }
        value = orcid;
        // Автоматически извлекаем и заполняем другие поля из той же строки (пропускаем orcid, т.к. он уже заполнен)
        autoExtractAuthorDataFromLine(fullText, authorIndex, ["orcid", "spin"]);
      } else if (fieldName === "scopusid") {
        targetField = $(`.author-input[data-field="scopusid"][data-lang="CODES"][data-index="${authorIndex}"]`);
        if (!targetField) {
          alert(`Поле Scopus ID не найдено. Убедитесь, что форма автора открыта.`);
          return;
        }
        const scopusId = extractScopusID(fullText);
        if (!scopusId) {
          alert("Scopus ID не найден в выделенном тексте. Убедитесь, что выделен текст, содержащий Scopus ID (например: 123456789)");
          return;
        }
        value = scopusId;
        // Автоматически извлекаем и заполняем другие поля из той же строки (пропускаем scopusid, т.к. он уже заполнен)
        autoExtractAuthorDataFromLine(fullText, authorIndex, "scopusid");
      } else if (fieldName === "researcherid") {
        targetField = $(`.author-input[data-field="researcherid"][data-lang="CODES"][data-index="${authorIndex}"]`);
        if (!targetField) {
          alert(`Поле Researcher ID не найдено. Убедитесь, что форма автора открыта.`);
          return;
        }
        const researcherId = extractResearcherID(fullText);
        if (!researcherId) {
          alert("Researcher ID не найден в выделенном тексте. Убедитесь, что выделен текст, содержащий Researcher ID (например: A-1234-5678)");
          return;
        }
        value = researcherId;
        // Автоматически извлекаем и заполняем другие поля из той же строки (пропускаем researcherid, т.к. он уже заполнен)
        autoExtractAuthorDataFromLine(fullText, authorIndex, "researcherid");
      } else if (fieldName === "other") {
        if (!lang) return;
        targetField = $(`.author-input[data-field="otherInfo"][data-lang="${lang.toUpperCase()}"][data-index="${authorIndex}"]`);
        // Вставляем текст как есть, без удаления ФИО
        value = fullText.trim();
      } else {
        // Неизвестное поле
        return;
      }
      
      if (!targetField) {
        alert(`Поле автора не найдено. Убедитесь, что форма автора открыта.`);
        return;
      }
      
      targetField.value = value;
      if (fieldName === "org" || fieldName === "address") {
        initOrganizationCards(authorIndex);
      }
      // Триггерим событие input для обновления всех обработчиков
      targetField.dispatchEvent(new Event('input', { bubbles: true }));
      targetField.focus();
      
      // Обновляем имя автора в заголовке, если изменились фамилия или инициалы
      if (fieldName === "surname" || fieldName === "initials") {
        updateAuthorName(authorIndex);
      }
      
      // Открываем форму автора, если она закрыта
      const authorDetails = $(`#author-details-${authorIndex}`);
      if (authorDetails && authorDetails.style.display === "none") {
        toggleAuthorDetails(authorIndex);
      }
      
      // Подсвечиваем поле
      const authorItem = $(`.author-item[data-author-index="${authorIndex}"]`);
      if (authorItem) {
        authorItem.classList.add("active");
        setTimeout(() => authorItem.classList.remove("active"), 1200);
      }
      
      clearSelection();
      return;
    }
    
    // Обработка обычных полей
    const field = document.getElementById(fieldId);
    if (!field) return;
    
    if (fieldId === "doi") {
      const doi = extractDOI(fullText);
      if (!doi) {
        alert("DOI не найден в выделенном тексте. Нужен формат 10.xxxx/xxxxx");
        return;
      }
      value = doi;
    } else if (fieldId === "keywords" || fieldId === "keywords_en") {
      const kw = processKeywords(fullText);
      value = kw;
      // Обновляем счетчик после установки значения
      setTimeout(() => {
        updateKeywordsCount(fieldId);
        autoResizeKeywordsField(fieldId);
      }, 100);
    } else if (fieldId === "references_ru" || fieldId === "references_en") {
      const refs = processReferences(texts);
      value = refs.join("\n");
      // Обновляем счетчик после установки значения
      setTimeout(() => {
        if (window.updateReferencesCount) {
          window.updateReferencesCount(fieldId);
        }
      }, 100);
    } else if (fieldId === "received_date" || fieldId === "reviewed_date" || fieldId === "accepted_date" || fieldId === "date_publication") {
      const date = extractDate(fullText);
      if (date) {
        value = date;
      } else {
        alert("Дата не найдена в выделенном тексте. Ожидается формат: DD.MM.YYYY, DD/MM/YYYY или YYYY-MM-DD");
        return;
      }
    } else if (fieldId === "udc") {
      const udc = extractUDC(fullText);
      if (udc) {
        value = udc;
      } else {
        const udcRe = new RegExp("^\\s*(?:\u0423\u0414\u041a|UDC)\\s*", "i");
        value = fullText.replace(udcRe, "").trim();
      }
    } else if (fieldId === "funding" || fieldId === "funding_en") {
      const funding = processFunding(fullText, fieldId === "funding_en" ? "en" : "ru");
      value = funding;
    } else if (fieldId === "annotation" || fieldId === "annotation_en") {
      // Обрабатываем аннотацию: удаляем префикс "Аннотация" или "Annotation" если он есть
      const annotation = window.processAnnotation(fullText, fieldId === "annotation_en" ? "en" : "ru");
      // Заменяем содержимое поля, не добавляя к предыдущему
      value = annotation;
    } else if (fieldId === "year") {
      const year = extractYear(fullText);
      if (year) {
        value = year;
      } else {
        alert("Год не найден в выделенном тексте. Ожидается 4-значный год (например, 2025)");
        return;
      }
    } else {
      value = fullText.trim();
    }
    field.value = value;
    field.focus();
    setLinesInfo(fieldId, selected.size);
    markField(fieldId);
    clearSelection();
  }

  document.addEventListener("DOMContentLoaded", () => {
    // Очищаем префикс "Аннотация" из полей аннотации при загрузке страницы
    const annotationField = document.getElementById("annotation");
    if (annotationField && annotationField.value) {
      const cleaned = window.processAnnotation(annotationField.value, "ru");
      if (cleaned !== annotationField.value) {
        annotationField.value = cleaned;
      }
    }
    if (annotationField) {
      annotationField.addEventListener("paste", () => {
        setTimeout(() => {
          annotationField.value = window.processAnnotation(annotationField.value, "ru");
        }, 0);
      });
      annotationField.addEventListener("blur", () => {
        annotationField.value = window.processAnnotation(annotationField.value, "ru");
      });
    }
    
    const annotationEnField = document.getElementById("annotation_en");
    if (annotationEnField && annotationEnField.value) {
      const cleaned = window.processAnnotation(annotationEnField.value, "en");
      if (cleaned !== annotationEnField.value) {
        annotationEnField.value = cleaned;
      }
    }
    if (annotationEnField) {
      annotationEnField.addEventListener("paste", () => {
        setTimeout(() => {
          annotationEnField.value = window.processAnnotation(annotationEnField.value, "en");
        }, 0);
      });
      annotationEnField.addEventListener("blur", () => {
        annotationEnField.value = window.processAnnotation(annotationEnField.value, "en");
      });
    }

    const fundingField = document.getElementById("funding");
    if (fundingField && fundingField.value) {
      const cleaned = processFunding(fundingField.value, "ru");
      if (cleaned !== fundingField.value) {
        fundingField.value = cleaned;
      }
    }
    if (fundingField) {
      fundingField.addEventListener("paste", () => {
        setTimeout(() => {
          fundingField.value = processFunding(fundingField.value, "ru");
        }, 0);
      });
      fundingField.addEventListener("blur", () => {
        fundingField.value = processFunding(fundingField.value, "ru");
      });
    }

    const fundingEnField = document.getElementById("funding_en");
    if (fundingEnField && fundingEnField.value) {
      const cleaned = processFunding(fundingEnField.value, "en");
      if (cleaned !== fundingEnField.value) {
        fundingEnField.value = cleaned;
      }
    }
    if (fundingEnField) {
      fundingEnField.addEventListener("paste", () => {
        setTimeout(() => {
          fundingEnField.value = processFunding(fundingEnField.value, "en");
        }, 0);
      });
      fundingEnField.addEventListener("blur", () => {
        fundingEnField.value = processFunding(fundingEnField.value, "en");
      });
    }
    
    // Автоматическая прокрутка к началу статьи, если используется общий файл
    {% if is_common_file and article_start_line %}
    const articleLine = $(`.line[data-line="{{ article_start_line }}"]`);
    if (articleLine) {
      // Выделяем строку визуально
      articleLine.style.background = "#fff9c4";
      articleLine.style.borderLeft = "4px solid #ff9800";
      articleLine.style.fontWeight = "600";
      
      // Прокручиваем к строке с небольшим отступом сверху
      setTimeout(() => {
        articleLine.scrollIntoView({ behavior: "smooth", block: "center" });
        
        // Показываем уведомление
        const notification = document.createElement("div");
        notification.style.cssText = "position:fixed;top:20px;right:20px;background:#ff9800;color:#fff;padding:15px 20px;border-radius:4px;box-shadow:0 4px 12px rgba(0,0,0,0.2);z-index:3000;font-size:14px;max-width:400px;";
        notification.textContent = `📍 Найдено начало статьи на строке {{ article_start_line }}`;
        document.body.appendChild(notification);
        setTimeout(() => {
          notification.remove();
        }, 4000);
      }, 300);
    }
    {% endif %}
    
    const textContent = $("#textContent");
    if (textContent) {
      textContent.addEventListener("click", (e) => {
        const line = e.target.closest(".line");
        if (!line) return;
        const id = line.dataset.id;
        if (!id) return;
        
        const lineNumber = parseInt(line.dataset.line, 10);
        const isShiftPressed = e.shiftKey;
        
        if (isShiftPressed && selected.size > 0) {
          // Выделение диапазона при Shift+клик
          const selectedNumbers = Array.from(selected)
            .map(sid => {
              const selLine = $(`.line[data-id="${CSS.escape(sid)}"]`);
              return selLine ? parseInt(selLine.dataset.line, 10) : null;
            })
            .filter(n => n !== null)
            .sort((a, b) => a - b);
          
          if (selectedNumbers.length > 0) {
            const minLine = Math.min(...selectedNumbers, lineNumber);
            const maxLine = Math.max(...selectedNumbers, lineNumber);
            
            // Выделяем все строки в диапазоне
            $$(".line").forEach(l => {
              const lNum = parseInt(l.dataset.line, 10);
              if (lNum >= minLine && lNum <= maxLine) {
                const lid = l.dataset.id;
                selected.add(lid);
                l.classList.add("selected");
              }
            });
          }
        } else if (selected.size > 0 && !selected.has(id)) {
          // Если уже есть выделенные строки и кликнули на другую, выделяем диапазон
          const selectedNumbers = Array.from(selected)
            .map(sid => {
              const selLine = $(`.line[data-id="${CSS.escape(sid)}"]`);
              return selLine ? parseInt(selLine.dataset.line, 10) : null;
            })
            .filter(n => n !== null);
          
          if (selectedNumbers.length > 0) {
            const minLine = Math.min(...selectedNumbers, lineNumber);
            const maxLine = Math.max(...selectedNumbers, lineNumber);
            
            // Выделяем все строки в диапазоне
            $$(".line").forEach(l => {
              const lNum = parseInt(l.dataset.line, 10);
              if (lNum >= minLine && lNum <= maxLine) {
                const lid = l.dataset.id;
                selected.add(lid);
                l.classList.add("selected");
              }
            });
          } else {
            // Обычное выделение/снятие выделения
            if (selected.has(id)) {
              selected.delete(id);
              line.classList.remove("selected");
            } else {
              selected.add(id);
              line.classList.add("selected");
            }
          }
        } else {
          // Обычное выделение/снятие выделения
          if (selected.has(id)) {
            selected.delete(id);
            line.classList.remove("selected");
          } else {
            selected.add(id);
            line.classList.add("selected");
          }
        }
        
        updatePanel();
      });
    }

    document.addEventListener("focusin", (e) => {
      const el = e.target;
      if (!el) return;
      if ((el.tagName === "INPUT" || el.tagName === "TEXTAREA") && el.id) {
        currentFieldId = el.id;
        if (pdfBbox) pdfBbox.setActiveField(el.id);
      }
    });

    const clearBtn = $("#clearBtn");
    if (clearBtn) clearBtn.addEventListener("click", clearSelection);

    const panel = $("#selectionPanel");
    enableSelectionPanelDragging();
    if (panel) {
      panel.addEventListener("click", (e) => {
        const btn = e.target.closest("button");
        if (!btn) return;
        const action = btn.dataset.action;
        if (action === "cancel") {
          clearSelection();
          return;
        }
        const assign = btn.dataset.assign;
        if (assign) {
          if (pdfBbox) pdfBbox.setActiveField(assign);
          applySelectionToField(assign);
        }
      });
    }

    const searchInput = $("#searchInput");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        const q = (e.target.value || "").toLowerCase();
        const lines = $$(".line");
        if (q.length < 2) {
          lines.forEach(l => { l.style.display = ""; l.style.background = ""; });
          return;
        }
        lines.forEach(l => {
          const t = l.textContent.toLowerCase();
          if (t.includes(q)) {
            l.style.display = "";
            l.style.background = "#fff9c4";
          } else {
            l.style.display = "none";
          }
        });
      });
    }

    // Инициализация счетчиков ключевых слов при загрузке
    const keywordsField = $("#keywords");
    const keywordsEnField = $("#keywords_en");
    if (keywordsField) {
      updateKeywordsCount("keywords");
      autoResizeKeywordsField("keywords");
      keywordsField.addEventListener("input", () => {
        updateKeywordsCount("keywords");
        autoResizeKeywordsField("keywords");
      });
    }
    if (keywordsEnField) {
      updateKeywordsCount("keywords_en");
      autoResizeKeywordsField("keywords_en");
      keywordsEnField.addEventListener("input", () => {
        updateKeywordsCount("keywords_en");
        autoResizeKeywordsField("keywords_en");
      });
    }

    const crossrefBtn = $("#crossrefDoiBtn");
    const crossrefStatus = $("#crossrefStatus");
    const doiField = $("#doi");
    const crossrefAnnotationEnField = $("#annotation_en");
    const crossrefReferencesEnField = $("#references_en");
    const setCrossrefStatus = (text, color) => {
      if (!crossrefStatus) return;
      crossrefStatus.textContent = text || "";
      crossrefStatus.style.color = color || "#666";
    };
    if (crossrefBtn) {
      crossrefBtn.addEventListener("click", async () => {
        const doi = (doiField?.value || "").trim();
        if (!doi) {
          setCrossrefStatus("Укажите DOI перед обновлением.", "#c62828");
          return;
        }
        crossrefBtn.disabled = true;
        setCrossrefStatus("Запрос к Crossref...", "#555");
        try {
          const resp = await fetch("/crossref-update", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ doi }),
          });
          const data = await resp.json().catch(() => ({}));
          if (!resp.ok || !data.success) {
            setCrossrefStatus(data.error || "Не удалось получить данные из Crossref.", "#c62828");
            return;
          }

          if (doiField && data.doi) {
            doiField.value = String(data.doi);
          }

          const abstractText = (data.abstract || "").trim();
          if (crossrefAnnotationEnField && abstractText) {
            if (!crossrefAnnotationEnField.value.trim() || confirm("Заменить текущую Annotation (English) данными из Crossref?")) {
              crossrefAnnotationEnField.value = abstractText;
              crossrefAnnotationEnField.dispatchEvent(new Event("input", { bubbles: true }));
            }
          }

          const refs = Array.isArray(data.references) ? data.references.map((s) => String(s || "").trim()).filter(Boolean) : [];
          if (crossrefReferencesEnField && refs.length) {
            const nextRefs = refs.join("\n");
            if (!crossrefReferencesEnField.value.trim() || confirm("Заменить текущий список литературы (английский) данными из Crossref?")) {
              crossrefReferencesEnField.value = nextRefs;
              crossrefReferencesEnField.dispatchEvent(new Event("input", { bubbles: true }));
              if (window.updateReferencesCount) {
                window.updateReferencesCount("references_en");
              }
            }
          }

          const parts = [];
          if (abstractText) parts.push("аннотация");
          if (refs.length) parts.push(`ссылки: ${refs.length}`);
          setCrossrefStatus(
            parts.length ? `Данные обновлены (${parts.join(", ")}).` : "Данные получены, но обновлять было нечего.",
            "#2e7d32"
          );
        } catch (err) {
          setCrossrefStatus(`Ошибка Crossref: ${err.message || err}`, "#c62828");
        } finally {
          crossrefBtn.disabled = false;
        }
      });
    }
    
    // Инициализация счетчиков литературы при загрузке
    const referencesRuField = $("#references_ru");
    const referencesEnField = $("#references_en");
    if (referencesRuField) {
      if (window.updateReferencesCount) {
        window.updateReferencesCount("references_ru");
        referencesRuField.addEventListener("input", () => {
          referencesRuField.dataset.aiProcessed = "";
          window.updateReferencesCount("references_ru");
        });
      }
    }
    if (referencesEnField) {
      if (window.updateReferencesCount) {
        window.updateReferencesCount("references_en");
        referencesEnField.addEventListener("input", () => {
          referencesEnField.dataset.aiProcessed = "";
          window.updateReferencesCount("references_en");
        });
      }
    }
    
    // Инициализация обработчиков для обновления имен авторов
    const existingAuthors = $$(".author-item");
    existingAuthors.forEach(item => {
      const index = parseInt(item.dataset.authorIndex, 10);
      if (!isNaN(index)) {
        attachAuthorNameListeners(index);
        initOrganizationCards(index);
      }
    });

    const form = $("#metadataForm");
    if (form) {
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(form);
        const data = {};
        for (const [k, v] of fd.entries()) data[k] = v;
        
        // Собираем данные авторов из раскрывающегося меню
        data.authors = collectAuthorsData();
        
        ["references_ru", "references_en"].forEach((k) => {
          if (data[k]) {
            const refs = String(data[k]).split("\n").map(s => s.trim()).filter(Boolean);
            data[k] = mergeDoiUrlWithReferences(refs);
          }
        });
        try {
          const resp = await fetch("/markup/{{ filename|e }}/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
          });
          const result = await resp.json();
          if (result.success) {
            if (pdfBbox) await pdfBbox.saveSelections();
            // Сохраняем информацию о том, что файл был только что сохранен
            // Это позволит сразу подсветить его на главной странице
            const savedFiles = JSON.parse(localStorage.getItem("recently_saved_files") || "[]");
            const currentFile = "{{ filename|e }}";
            if (!savedFiles.includes(currentFile)) {
              savedFiles.push(currentFile);
              localStorage.setItem("recently_saved_files", JSON.stringify(savedFiles));
            }
            
            // Показываем красивое уведомление
            toast("Метаданные успешно сохранены! Статья помечена как обработанная.");
            // Перенаправляем на главную страницу с небольшой задержкой, чтобы увидеть уведомление
            // На главной странице файл автоматически будет показан как обработанный (зеленый цвет и галочка)
            setTimeout(() => {
              window.location.href = "/";
            }, 1500);
          } else {
            alert("Ошибка при сохранении: " + result.error);
          }
        } catch (err) {
          alert("Ошибка: " + err.message);
        }
      });
    }

    if (pdfBbox) {
      pdfBbox.init({
        iframeSelector: "#pdfViewerIframe",
        pdfFile: "{{ pdf_path|e }}",
        activeFieldLabelSelector: "#bboxActiveField",
        clearButtonSelector: "#bboxClearBtn",
        extractEndpoint: "/api/pdf-extract-text",
        saveEndpoint: "/api/pdf-save-coordinates",
      });
      
      // Устанавливаем ISSN журнала для шаблонов bbox
      const journalIssn = "{{ journal_issn|default('', true)|e }}";
      const journalName = "{{ journal_name|default('', true)|e }}";
      if (journalIssn) {
        pdfBbox.setIssn(journalIssn, journalName);
        
        // Загружаем шаблоны и показываем уведомление если есть предложения
        pdfBbox.loadTemplateSuggestions(journalIssn).then(data => {
          if (data && data.suggestions && Object.keys(data.suggestions).length > 0) {
            const count = Object.keys(data.suggestions).length;
            const toast = window.toast || ((msg) => console.log(msg));
            toast(`Доступно ${count} шаблонов bbox для этого журнала. Нажмите "Применить шаблоны" для автозаполнения.`, "info");
            
            // Добавляем кнопку применения шаблонов в toolbar
            const toolbar = document.querySelector('.pdf-bbox-toolbar');
            if (toolbar && !document.getElementById('applyTemplatesBtn')) {
              const btn = document.createElement('button');
              btn.id = 'applyTemplatesBtn';
              btn.className = 'bbox-btn';
              btn.style.cssText = 'background: #4caf50; color: white; margin-left: 10px;';
              btn.innerHTML = '📋 Применить шаблоны (' + count + ')';
              btn.onclick = () => pdfBbox.showSuggestionsPanel();
              toolbar.appendChild(btn);
            }
          }
        });
      }
    }
  });
})();
</script>
</body>
</html>
"""
