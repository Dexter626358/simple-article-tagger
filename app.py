#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Веб-приложение для просмотра HTML страниц, сгенерированных word_to_html.
Позволяет выбрать DOCX/RTF файл из папки words_input, конвертировать его в HTML
и отобразить в браузере без сохранения в файл.
"""

from __future__ import annotations

import argparse
import re
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Optional

from flask import Flask, render_template_string, abort, jsonify, request

# Импортируем функции конвертации из word_to_html
try:
    from word_to_html import convert_to_html, create_full_html_page
    WORD_TO_HTML_AVAILABLE = True
except ImportError:
    WORD_TO_HTML_AVAILABLE = False
    print("⚠ Ошибка: не удалось импортировать word_to_html. Убедитесь, что word_to_html.py доступен.")

# Импортируем функции для работы с метаданными
try:
    from metadata_markup import (
        build_metadata,
        save_metadata as save_metadata_to_file,
        extract_text_from_html,
        get_default_output_path,
        METADATA_FIELDS,
        LIST_FIELDS,
        INT_FIELDS,
    )
    METADATA_MARKUP_AVAILABLE = True
except ImportError:
    METADATA_MARKUP_AVAILABLE = False
    print("⚠ Ошибка: не удалось импортировать metadata_markup. Убедитесь, что metadata_markup.py доступен.")

# ----------------------------
# Константы
# ----------------------------

SUPPORTED_EXTENSIONS = {".docx", ".rtf"}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Просмотр HTML документов</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      padding: 20px;
    }
    .container {
      max-width: 1200px;
      margin: 0 auto;
      background: white;
      border-radius: 12px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.2);
      overflow: hidden;
    }
    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 30px;
      text-align: center;
    }
    .header h1 {
      font-size: 28px;
      margin-bottom: 10px;
    }
    .header p {
      opacity: 0.9;
      font-size: 14px;
    }
    .content {
      padding: 30px;
    }
    .file-list {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 15px;
      margin-top: 20px;
    }
    .file-item {
      background: #f8f9fa;
      border: 2px solid #e0e0e0;
      border-radius: 8px;
      padding: 20px;
      cursor: pointer;
      transition: all 0.3s;
      text-decoration: none;
      color: #333;
      display: block;
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
    .file-name {
      font-weight: 600;
      font-size: 16px;
      margin-bottom: 8px;
      color: #2196f3;
    }
    .file-info {
      font-size: 12px;
      color: #666;
    }
    .empty-state {
      text-align: center;
      padding: 60px 20px;
      color: #999;
    }
    .empty-state h3 {
      margin-bottom: 10px;
      color: #666;
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
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>📄 Просмотр документов</h1>
      <p>Выберите DOCX/RTF файл для просмотра</p>
    </div>
    <div class="content">
      {% if files %}
        <div class="file-list">
          {% for file in files %}
            <a href="/markup/{{ file.name }}" class="file-item">
              <div class="file-name">{{ file.name }}</div>
              <div class="file-info">
                Размер: {{ file.size_kb }} KB<br>
                Изменен: {{ file.modified }}
              </div>
            </a>
          {% endfor %}
        </div>
      {% else %}
        <div class="empty-state">
          <h3>📁 Папка пуста</h3>
          <p>В папке words_input не найдено DOCX/RTF файлов.</p>
          <p style="margin-top: 20px; font-size: 14px;">
            Поместите DOCX или RTF файлы в папку <code>words_input</code>.
          </p>
        </div>
      {% endif %}
    </div>
  </div>
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
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>{{ filename }}</h1>
      <div class="header-actions">
        <a href="/markup/{{ filename }}" class="markup-btn">📝 Разметить метаданные</a>
        <a href="/" class="back-btn">← Назад к списку</a>
      </div>
    </div>
    <div class="viewer-content">
      {{ content|safe }}
    </div>
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
  <style>
    *{margin:0;padding:0;box-sizing:border-box;}
    body{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:#f5f5f5;padding:20px;}
    .container{max-width:1400px;margin:0 auto;background:white;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1);overflow:hidden;}
    .header{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;padding:20px;text-align:center;}
    .header h1{font-size:24px;margin-bottom:5px;}
    .header p{opacity:.9;}
    .header-actions{display:flex;gap:10px;justify-content:center;margin-top:10px;}
    .header-btn{background:rgba(255,255,255,0.2);color:white;border:1px solid rgba(255,255,255,0.3);padding:8px 16px;border-radius:6px;text-decoration:none;font-size:14px;transition:all 0.2s;}
    .header-btn:hover{background:rgba(255,255,255,0.3);}
    .content{display:flex;height:calc(100vh - 200px);}
    .text-panel{flex:1;padding:20px;overflow-y:auto;border-right:1px solid #e0e0e0;}
    .form-panel{width:400px;padding:20px;overflow-y:auto;background:#fafafa;}

    .search-box{margin-bottom:20px;}
    .search-box input{width:100%;padding:10px;border:1px solid #ddd;border-radius:4px;font-size:14px;}

    .line{padding:8px 12px;margin:2px 0;border-radius:4px;cursor:pointer;transition:all .2s;border-left:3px solid transparent;font-size:14px;line-height:1.5;user-select:none;}
    .line:hover{background:#f0f0f0;border-left-color:#667eea;}
    .line.selected{background:#e3f2fd !important;border-left-color:#2196f3 !important;font-weight:500;}
    .line-number{display:inline-block;width:50px;color:#999;font-size:12px;margin-right:10px;}

    .instructions{background:#fff3cd;border:1px solid #ffc107;border-radius:4px;padding:15px;margin-bottom:20px;}
    .instructions h3{margin-bottom:10px;color:#856404;}
    .instructions ul{margin-left:20px;color:#856404;}
    .instructions li{margin:5px 0;}

    .field-group{margin-bottom:20px;}
    .field-group label{display:block;font-weight:600;margin-bottom:8px;color:#333;font-size:14px;}
    .field-group input,.field-group textarea{width:100%;padding:10px;border:1px solid #ddd;border-radius:4px;font-size:14px;font-family:inherit;}
    .field-group textarea{min-height:80px;resize:vertical;}
    .selected-lines{margin-top:5px;font-size:12px;color:#666;}
    .field-group.active{background:#e3f2fd;border:2px solid #2196f3;border-radius:4px;padding:10px;}

    .buttons{display:flex;gap:10px;margin-top:20px;}
    button{flex:1;padding:12px;border:none;border-radius:4px;font-size:14px;font-weight:600;cursor:pointer;transition:all .2s;}
    .btn-secondary{background:#e0e0e0;color:#333;}
    .btn-secondary:hover{background:#d0d0d0;}
    .btn-success{background:#4caf50;color:#fff;}
    .btn-success:hover{background:#45a049;}

    .selection-panel{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#fff;border:2px solid #667eea;border-radius:8px;padding:15px 20px;box-shadow:0 4px 20px rgba(0,0,0,0.2);z-index:1000;display:none;min-width:400px;}
    .selection-panel.active{display:block;}
    .selection-panel h4{margin:0 0 10px 0;color:#667eea;font-size:14px;}
    .field-buttons{display:flex;flex-wrap:wrap;gap:8px;}
    .field-btn{padding:8px 12px;border:1px solid #667eea;background:#fff;color:#667eea;border-radius:4px;cursor:pointer;font-size:12px;transition:all .2s;}
    .field-btn:hover{background:#667eea;color:#fff;}
    
    .view-refs-btn{background:#2196f3;color:#fff;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;font-size:12px;margin-top:5px;transition:all .2s;}
    .view-refs-btn:hover{background:#1976d2;}
    
    .modal{display:none;position:fixed;z-index:2000;left:0;top:0;width:100%;height:100%;background:rgba(0,0,0,0.5);overflow:auto;}
    .modal.active{display:flex;align-items:center;justify-content:center;}
    .modal-content{background:#fff;padding:30px;border-radius:8px;max-width:800px;width:90%;max-height:80vh;overflow-y:auto;box-shadow:0 4px 20px rgba(0,0,0,0.3);}
    .modal-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;border-bottom:2px solid #e0e0e0;padding-bottom:15px;}
    .modal-header h2{margin:0;color:#333;font-size:20px;}
    .modal-close{background:none;border:none;font-size:28px;cursor:pointer;color:#999;padding:0;width:30px;height:30px;line-height:30px;text-align:center;}
    .modal-close:hover{color:#333;}
    .refs-list{margin:0;padding:0;}
    .ref-item{background:#f8f9fa;border-left:4px solid #2196f3;padding:15px;margin-bottom:10px;border-radius:4px;line-height:1.6;position:relative;}
    .ref-number{display:inline-block;width:30px;font-weight:600;color:#2196f3;vertical-align:top;}
    .ref-text{margin-left:35px;color:#333;min-height:20px;}
    .ref-text[contenteditable="true"]{outline:2px solid #2196f3;outline-offset:2px;padding:8px;border-radius:4px;background:#fff;cursor:text;}
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
  </style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Разметка метаданных</h1>
    <p>{{ filename }}</p>
    <div class="header-actions">
      <a href="/view/{{ filename }}" class="header-btn">← Просмотр</a>
      <a href="/" class="header-btn">← К списку</a>
    </div>
  </div>

  <div class="content">
    <div class="text-panel">
      <div class="search-box">
        <input type="text" id="searchInput" placeholder="Поиск в тексте...">
      </div>
      <div id="textContent">
        {% for line in lines %}
          <div class="line" data-id="{{ line.id }}" data-line="{{ line.line_number }}">
            <span class="line-number">{{ line.line_number }}</span>
            <span class="line-text">{{ line.text }}</span>
          </div>
        {% endfor %}
      </div>
    </div>

    <div class="form-panel">
      <div class="instructions">
        <h3>Инструкция:</h3>
        <ul>
          <li><strong>Способ 1:</strong> Кликните на поле → выделите строки в тексте</li>
          <li><strong>Способ 2:</strong> Выделите строки → выберите поле из панели внизу</li>
          <li>Можно редактировать текст в полях вручную</li>
          <li>Используйте поиск для быстрого нахождения текста</li>
        </ul>
      </div>

      <form id="metadataForm">
        <div class="field-group">
          <label>Название (русский) *</label>
          <textarea id="title" name="title" required></textarea>
          <div class="selected-lines" id="title-lines"></div>
        </div>

        <div class="field-group">
          <label>Название (английский)</label>
          <textarea id="title_en" name="title_en"></textarea>
          <div class="selected-lines" id="title_en-lines"></div>
        </div>

        <div class="field-group">
          <label>DOI</label>
          <input type="text" id="doi" name="doi">
          <div class="selected-lines" id="doi-lines"></div>
        </div>

        <div class="field-group">
          <label>Аннотация (русский)</label>
          <textarea id="annotation" name="annotation"></textarea>
          <div class="selected-lines" id="annotation-lines"></div>
        </div>

        <div class="field-group">
          <label>Аннотация (английский)</label>
          <textarea id="annotation_en" name="annotation_en"></textarea>
          <div class="selected-lines" id="annotation_en-lines"></div>
        </div>

        <div class="field-group">
          <label>Ключевые слова (русский)</label>
          <input type="text" id="keywords" name="keywords">
          <div class="selected-lines" id="keywords-lines"></div>
        </div>

        <div class="field-group">
          <label>Ключевые слова (английский)</label>
          <input type="text" id="keywords_en" name="keywords_en">
          <div class="selected-lines" id="keywords_en-lines"></div>
        </div>

        <div class="field-group">
          <label>Список литературы (русский)</label>
          <textarea id="references_ru" name="references_ru" rows="5"></textarea>
          <div class="selected-lines" id="references_ru-lines"></div>
          <button type="button" class="view-refs-btn" onclick="viewReferences('references_ru', 'Список литературы (русский)')">👁 Просмотреть список</button>
          <small style="color:#666;font-size:12px;">Каждая ссылка с новой строки</small>
        </div>

        <div class="field-group">
          <label>Список литературы (английский)</label>
          <textarea id="references_en" name="references_en" rows="5"></textarea>
          <div class="selected-lines" id="references_en-lines"></div>
          <button type="button" class="view-refs-btn" onclick="viewReferences('references_en', 'Список литературы (английский)')">👁 Просмотреть список</button>
          <small style="color:#666;font-size:12px;">Каждая ссылка с новой строки</small>
        </div>

        <div class="field-group">
          <label>Год</label>
          <input type="number" id="year" name="year">
        </div>

        <div class="field-group">
          <label>Страницы</label>
          <input type="text" id="pages" name="pages">
        </div>

        <div class="field-group">
          <label>УДК</label>
          <input type="text" id="udc" name="udc">
          <div class="selected-lines" id="udc-lines"></div>
        </div>

        <div class="field-group">
          <label>Дата получения</label>
          <input type="text" id="received_date" name="received_date">
        </div>

        <div class="field-group">
          <label>Дата доработки</label>
          <input type="text" id="reviewed_date" name="reviewed_date">
        </div>

        <div class="field-group">
          <label>Дата принятия</label>
          <input type="text" id="accepted_date" name="accepted_date">
        </div>

        <div class="field-group">
          <label>Финансирование</label>
          <textarea id="funding" name="funding" rows="3"></textarea>
          <div class="selected-lines" id="funding-lines"></div>
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
      <button type="button" class="field-btn" data-assign="doi">DOI</button>
      <button type="button" class="field-btn" data-assign="annotation">Аннотация (рус)</button>
      <button type="button" class="field-btn" data-assign="annotation_en">Аннотация (англ)</button>
      <button type="button" class="field-btn" data-assign="keywords">Ключевые слова (рус)</button>
      <button type="button" class="field-btn" data-assign="keywords_en">Ключевые слова (англ)</button>
      <button type="button" class="field-btn" data-assign="references_ru">Список литературы (рус)</button>
      <button type="button" class="field-btn" data-assign="references_en">Список литературы (англ)</button>
      <button type="button" class="field-btn" data-assign="pages">Страницы</button>
      <button type="button" class="field-btn" data-assign="udc">УДК</button>
      <button type="button" class="field-btn" data-assign="received_date">Дата получения</button>
      <button type="button" class="field-btn" data-assign="reviewed_date">Дата доработки</button>
      <button type="button" class="field-btn" data-assign="accepted_date">Дата принятия</button>
      <button type="button" class="field-btn" data-assign="year">Год</button>
      <button type="button" class="field-btn" data-assign="funding">Финансирование</button>
      <button type="button" class="field-btn" data-action="cancel">Отменить</button>
    </div>
  </div>
</div>

<div id="refsModal" class="modal">
  <div class="modal-content">
    <div class="modal-header">
      <h2 id="modalTitle">Список литературы</h2>
      <button class="modal-close" onclick="closeRefsModal()">&times;</button>
    </div>
    <div id="refsList" class="refs-list"></div>
    <div class="modal-footer">
      <button class="modal-btn modal-btn-cancel" onclick="closeRefsModal()">Отмена</button>
      <button class="modal-btn modal-btn-save" onclick="saveEditedReferences()">Сохранить изменения</button>
    </div>
  </div>
</div>

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
  
  const refs = refsText.split("\n")
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
      refItem.innerHTML = `
        <span class="ref-number">${index + 1}.</span>
        <span class="ref-text" contenteditable="true" spellcheck="false">${escapeHtml(ref)}</span>
        <div class="ref-actions">
          <button class="ref-action-btn delete" onclick="deleteReference(this)" title="Удалить">✕</button>
        </div>
      `;
      refsList.appendChild(refItem);
    });
  }
  
  modal.classList.add("active");
}

function deleteReference(btn) {
  const refItem = btn.closest(".ref-item");
  if (refItem && confirm("Удалить эту ссылку из списка?")) {
    refItem.remove();
    // Перенумеровываем оставшиеся ссылки
    renumberReferences();
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
  if (modal) {
    modal.classList.remove("active");
  }
}

// Закрытие модального окна при клике вне его
document.addEventListener("click", (e) => {
  const modal = document.getElementById("refsModal");
  if (e.target === modal) {
    closeRefsModal();
  }
});

// Закрытие модального окна по Escape
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeRefsModal();
  }
});

(() => {
  const selected = new Set();
  let currentFieldId = null;

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
    const udcPatterns = [
      /(?:УДК|UDC)\s*:?\s*([0-9.]+(?:[-–—][0-9.]+)?)/i,
      /\b([0-9]{1,3}(?:\.[0-9]+)*(?:[-–—][0-9.]+)?)\b/,
    ];
    for (const pattern of udcPatterns) {
      const match = text.match(pattern);
      if (match) return match[1].trim();
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

  function processFunding(text) {
    if (!text) return "";
    return text.replace(/^(Финансирование|Funding)\s*[.:]?\s*/i, "").replace(/^(Финансирование|Funding)\s*/i, "").trim();
  }

  function processReferences(texts) {
    const processed = [];
    texts.forEach(text => {
      let cleaned = String(text).replace(/^\d+\s+/, "").replace(/\t/g, " ").replace(/\s+/g, " ").trim();
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

  function applySelectionToField(fieldId) {
    const texts = getSelectedTexts();
    if (!texts.length) return;
    const field = document.getElementById(fieldId);
    if (!field) return;
    const fullText = texts.join(" ");
    let value = "";
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
    } else if (fieldId === "references_ru" || fieldId === "references_en") {
      const refs = processReferences(texts);
      value = refs.join("\n");
    } else if (fieldId === "received_date" || fieldId === "reviewed_date" || fieldId === "accepted_date") {
      const date = extractDate(fullText);
      if (date) {
        value = date;
      } else {
        alert("Дата не найдена в выделенном тексте. Ожидается формат: DD.MM.YYYY, DD/MM/YYYY или YYYY-MM-DD");
        return;
      }
    } else if (fieldId === "udc") {
      const udc = extractUDC(fullText);
      value = udc ? udc : fullText.trim();
    } else if (fieldId === "funding") {
      const funding = processFunding(fullText);
      value = funding;
    } else if (fieldId === "year") {
      const year = extractYear(fullText);
      if (year) {
        value = year;
      } else {
        alert("Год не найден в выделенном тексте. Ожидается 4-значный год (например, 2025)");
        return;
      }
    } else {
      value = fullText;
    }
    field.value = value;
    field.focus();
    setLinesInfo(fieldId, selected.size);
    markField(fieldId);
    clearSelection();
  }

  document.addEventListener("DOMContentLoaded", () => {
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
      }
    });

    const clearBtn = $("#clearBtn");
    if (clearBtn) clearBtn.addEventListener("click", clearSelection);

    const panel = $("#selectionPanel");
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
        if (assign) applySelectionToField(assign);
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

    const form = $("#metadataForm");
    if (form) {
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(form);
        const data = {};
        for (const [k, v] of fd.entries()) data[k] = v;
        ["references_ru", "references_en"].forEach((k) => {
          if (data[k]) {
            const refs = String(data[k]).split("\n").map(s => s.trim()).filter(Boolean);
            data[k] = mergeDoiUrlWithReferences(refs);
          }
        });
        try {
          const resp = await fetch("/markup/{{ filename }}/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
          });
          const result = await resp.json();
          if (result.success) {
            alert("Метаданные успешно сохранены!\nФайл: " + result.filename);
            window.location.href = "/view/{{ filename }}";
          } else {
            alert("Ошибка при сохранении: " + result.error);
          }
        } catch (err) {
          alert("Ошибка: " + err.message);
        }
      });
    }
  });
})();
</script>
</body>
</html>
"""


# ----------------------------
# Вспомогательные функции
# ----------------------------

def get_source_files(input_dir: Path) -> list[dict]:
    """
    Получает список DOCX/RTF файлов из указанной директории.
    
    Args:
        input_dir: Путь к директории с исходными файлами
        
    Returns:
        Список словарей с информацией о файлах
    """
    if not input_dir.exists() or not input_dir.is_dir():
        return []
    
    files = []
    for ext in SUPPORTED_EXTENSIONS:
        for file_path in sorted(input_dir.glob(f"*{ext}"), key=lambda x: x.name):
            try:
                stat = file_path.stat()
                size_kb = stat.st_size / 1024
                modified = time.strftime("%d.%m.%Y %H:%M", time.localtime(stat.st_mtime))
                
                files.append({
                    "name": file_path.name,
                    "path": file_path,
                    "size_kb": f"{size_kb:.1f}",
                    "modified": modified,
                    "extension": ext,
                })
            except Exception:
                continue
    
    return files


def merge_doi_url_in_html(html_content: str) -> str:
    """
    Объединяет параграфы с DOI/URL с предыдущими параграфами в HTML.
    
    Если параграф содержит только DOI/URL (начинается с http и содержит doi.org),
    он объединяется с предыдущим параграфом.
    
    Args:
        html_content: HTML содержимое
        
    Returns:
        Обработанный HTML с объединенными параграфами
    """
    def is_doi_url_paragraph(text: str) -> bool:
        """Проверяет, является ли текст параграфа DOI/URL."""
        # Убираем HTML теги для проверки
        text_clean = re.sub(r'<[^>]+>', '', text).strip()
        if not text_clean:
            return False
        
        # Проверяем, начинается ли с http и содержит doi.org
        line_lower = text_clean.lower()
        return (
            text_clean.startswith("http") and 
            ("doi.org" in line_lower or "dx.doi.org" in line_lower)
        )
    
    # Паттерн для поиска параграфов <p>...</p> с возможными атрибутами
    pattern = r'(<p[^>]*>)(.*?)(</p>)'
    
    # Находим все параграфы
    matches = list(re.finditer(pattern, html_content, re.DOTALL))
    
    if not matches:
        return html_content
    
    # Собираем результат
    result_parts = []
    last_end = 0
    
    for i, match in enumerate(matches):
        # Текст до текущего параграфа
        if match.start() > last_end:
            result_parts.append(html_content[last_end:match.start()])
        
        open_tag = match.group(1)  # <p> или <p attr="...">
        content = match.group(2)    # содержимое параграфа
        close_tag = match.group(3)  # </p>
        
        # Проверяем, является ли это DOI/URL параграфом
        if is_doi_url_paragraph(content) and result_parts:
            # Объединяем с предыдущим параграфом
            # Ищем последний добавленный параграф
            last_part = result_parts[-1]
            
            # Если последняя часть заканчивается на </p>, объединяем
            if last_part.rstrip().endswith('</p>'):
                # Находим последний </p> в последней части
                last_p_end = last_part.rfind('</p>')
                if last_p_end != -1:
                    # Берем всё до </p>, добавляем пробел, DOI/URL и закрывающий тег
                    before_close = last_part[:last_p_end]
                    result_parts[-1] = before_close + " " + content + close_tag
                else:
                    result_parts.append(match.group(0))
            else:
                result_parts.append(match.group(0))
        else:
            # Обычный параграф, добавляем как есть
            result_parts.append(match.group(0))
        
        last_end = match.end()
    
    # Добавляем остаток после последнего параграфа
    if last_end < len(html_content):
        result_parts.append(html_content[last_end:])
    
    return ''.join(result_parts)


def convert_file_to_html(file_path: Path, use_word_reader: bool = False) -> tuple[str, list[str]]:
    """
    Конвертирует DOCX/RTF файл в HTML используя word_to_html.
    
    Args:
        file_path: Путь к исходному файлу
        use_word_reader: Использовать ли word_reader для конвертации
        
    Returns:
        Кортеж (HTML содержимое, список предупреждений)
    """
    if not WORD_TO_HTML_AVAILABLE:
        raise RuntimeError("word_to_html недоступен")
    
    if not file_path.exists():
        raise FileNotFoundError(f"Файл не найден: {file_path}")
    
    try:
        html_body, warnings = convert_to_html(
            file_path,
            style_map_text=None,
            include_default_style_map=True,
            use_word_reader=use_word_reader,
            include_metadata=False,
        )
        
        # Объединяем параграфы с DOI/URL с предыдущими
        html_body = merge_doi_url_in_html(html_body)
        
        return html_body, warnings
    except Exception as e:
        raise RuntimeError(f"Ошибка конвертации: {e}") from e


# ----------------------------
# Flask приложение
# ----------------------------

def create_app(input_dir: Path, use_word_reader: bool = False) -> Flask:
    """
    Создает Flask приложение для просмотра HTML документов.
    
    Args:
        input_dir: Путь к директории с исходными DOCX/RTF файлами
        use_word_reader: Использовать ли word_reader для конвертации
        
    Returns:
        Flask приложение
    """
    app = Flask(__name__)
    
    @app.route("/")
    def index():
        """Главная страница со списком файлов."""
        files = get_source_files(input_dir)
        return render_template_string(HTML_TEMPLATE, files=files)
    
    @app.route("/view/<filename>")
    def view_file(filename: str):
        """Конвертация и отображение выбранного файла."""
        # Безопасность: проверяем, что filename не содержит путь
        if "/" in filename or "\\" in filename or ".." in filename:
            abort(404)
        
        file_path = input_dir / filename
        
        if not file_path.exists() or not file_path.is_file():
            abort(404)
        
        # Проверяем расширение
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            abort(404)
        
        try:
            html_body, warnings = convert_file_to_html(file_path, use_word_reader=use_word_reader)
            
            # Если есть предупреждения, можно их отобразить (опционально)
            if warnings:
                print(f"Предупреждения для {filename}: {warnings}")
            
            return render_template_string(VIEWER_TEMPLATE, filename=filename, content=html_body)
        except Exception as e:
            error_msg = f"Ошибка при конвертации файла: {e}"
            print(error_msg)
            return error_msg, 500
    
    @app.route("/markup/<filename>")
    def markup_file(filename: str):
        """Страница разметки метаданных для выбранного файла."""
        if not METADATA_MARKUP_AVAILABLE:
            return "Ошибка: модуль metadata_markup недоступен", 500
        
        # Безопасность: проверяем, что filename не содержит путь
        if "/" in filename or "\\" in filename or ".." in filename:
            abort(404)
        
        file_path = input_dir / filename
        
        if not file_path.exists() or not file_path.is_file():
            abort(404)
        
        # Проверяем расширение
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            abort(404)
        
        try:
            # Конвертируем файл в HTML
            html_body, warnings = convert_file_to_html(file_path, use_word_reader=use_word_reader)
            
            # Извлекаем текст из HTML для разметки
            lines = extract_text_from_html(html_body)
            
            if warnings:
                print(f"Предупреждения для {filename}: {warnings}")
            
            return render_template_string(MARKUP_TEMPLATE, filename=filename, lines=lines)
        except Exception as e:
            error_msg = f"Ошибка при подготовке разметки: {e}"
            print(error_msg)
            return error_msg, 500
    
    @app.route("/markup/<filename>/save", methods=["POST"])
    def save_metadata(filename: str):
        """Сохранение метаданных в JSON файл."""
        if not METADATA_MARKUP_AVAILABLE:
            return jsonify(success=False, error="Модуль metadata_markup недоступен"), 500
        
        # Безопасность: проверяем, что filename не содержит путь
        if "/" in filename or "\\" in filename or ".." in filename:
            abort(404)
        
        file_path = input_dir / filename
        
        if not file_path.exists() or not file_path.is_file():
            abort(404)
        
        try:
            payload = request.get_json(force=True, silent=False)
            if not isinstance(payload, dict):
                return jsonify(success=False, error="Ожидался JSON-объект."), 400
            
            # Нормализуем метаданные
            metadata = build_metadata(payload)
            
            # Определяем путь для сохранения в папку output в корне проекта
            script_dir = Path(__file__).parent.resolve()
            output_dir = script_dir / "output"
            output_path = get_default_output_path(file_path, output_dir=output_dir)
            
            # Сохраняем метаданные
            save_metadata_to_file(metadata, output_path)
            
            return jsonify(success=True, filename=str(output_path))
        except Exception as e:
            error_msg = f"Ошибка при сохранении метаданных: {e}"
            print(error_msg)
            return jsonify(success=False, error=error_msg), 500
    
    return app


# ----------------------------
# CLI / Запуск
# ----------------------------

def open_browser_later(url: str, delay_sec: float = 1.2) -> None:
    """Открывает браузер с задержкой."""
    def _open():
        time.sleep(delay_sec)
        webbrowser.open(url)
    
    threading.Thread(target=_open, daemon=True).start()


def pick_file_interactive(input_dir: Path) -> Optional[str]:
    """
    Интерактивный выбор файла в терминале.
    
    Args:
        input_dir: Путь к директории с исходными DOCX/RTF файлами
        
    Returns:
        Имя выбранного файла или None, если выбор отменен
    """
    files = get_source_files(input_dir)
    
    if not files:
        print("⚠ В папке не найдено DOCX/RTF файлов.")
        print(f"   Папка: {input_dir}")
        print("   Поместите DOCX или RTF файлы в эту папку.")
        return None
    
    print("\n" + "=" * 80)
    print("📄 Доступные файлы (DOCX/RTF):")
    print("=" * 80)
    
    for i, file_info in enumerate(files, 1):
        print(f"  {i:2d}. {file_info['name']:<50} ({file_info['size_kb']} KB, {file_info['modified']})")
    
    print("=" * 80)
    print(f"  0. Показать все файлы (главная страница)")
    print("=" * 80)
    
    while True:
        try:
            choice = input(f"\nВыберите файл (1-{len(files)}) или 0 для списка, 'q' для выхода: ").strip()
            
            if choice.lower() in ['q', 'quit', 'exit', 'выход']:
                return None
            
            if not choice:
                continue
            
            try:
                file_num = int(choice)
                if file_num == 0:
                    return None  # Вернем None, чтобы показать главную страницу
                elif 1 <= file_num <= len(files):
                    return files[file_num - 1]['name']
                else:
                    print(f"❌ Неверный номер. Выберите от 1 до {len(files)} или 0")
                    continue
            except ValueError:
                print("❌ Неверный ввод. Введите число или 'q' для выхода.")
                continue
                
        except KeyboardInterrupt:
            print("\n\nПрервано пользователем.")
            return None
        except EOFError:
            print("\n\nВвод завершен.")
            return None


def main() -> int:
    """Главная функция для запуска приложения."""
    if not WORD_TO_HTML_AVAILABLE:
        print("❌ Ошибка: word_to_html недоступен.")
        print("   Убедитесь, что word_to_html.py находится в той же папке.")
        return 1
    
    parser = argparse.ArgumentParser(
        description="Веб-приложение для просмотра DOCX/RTF документов через word_to_html"
    )
    parser.add_argument(
        "--input-dir",
        default=None,
        help="Путь к папке с исходными DOCX/RTF файлами (по умолчанию: words_input)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5001,
        help="Порт для веб-сервера (по умолчанию: 5001)"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Не открывать браузер автоматически"
    )
    parser.add_argument(
        "--no-pick",
        action="store_true",
        help="Не показывать интерактивный выбор файла, открыть главную страницу"
    )
    parser.add_argument(
        "--use-word-reader",
        action="store_true",
        help="Использовать word_reader для конвертации"
    )
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent.resolve()
    
    # Определяем директорию с исходными файлами
    if args.input_dir:
        input_dir = Path(args.input_dir)
        if not input_dir.is_absolute():
            input_dir = script_dir / input_dir
    else:
        input_dir = script_dir / "words_input"
    
    if not input_dir.exists():
        input_dir.mkdir(parents=True, exist_ok=True)
        print(f"⚠ Создана папка: {input_dir}")
        print("   Поместите DOCX или RTF файлы в эту папку.")
    
    app = create_app(input_dir, use_word_reader=args.use_word_reader)
    
    # Интерактивный выбор файла
    selected_file = None
    if not args.no_pick:
        selected_file = pick_file_interactive(input_dir)
    
    # Формируем URL
    if selected_file:
        url = f"http://127.0.0.1:{args.port}/markup/{selected_file}"
    else:
        url = f"http://127.0.0.1:{args.port}/"
    
    if not args.no_browser:
        open_browser_later(url)
    
    print("\n" + "=" * 80)
    print("🌐 Веб-приложение для просмотра документов")
    print("=" * 80)
    print(f"📁 Папка с исходными файлами: {input_dir}")
    if selected_file:
        print(f"📄 Выбранный файл: {selected_file}")
    if args.use_word_reader:
        print("🔧 Используется word_reader для конвертации")
    print(f"🔗 URL: {url}")
    print("Для остановки: Ctrl+C")
    print("=" * 80 + "\n")
    
    try:
        app.run(host="127.0.0.1", port=args.port, debug=False)
    except KeyboardInterrupt:
        print("\n\nПриложение остановлено.")
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

