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
        extract_text_from_html,
    )
    METADATA_MARKUP_AVAILABLE = True
except ImportError:
    METADATA_MARKUP_AVAILABLE = False
    print("⚠ Ошибка: не удалось импортировать metadata_markup. Убедитесь, что metadata_markup.py доступен.")

# Импортируем функции для работы с JSON метаданными
try:
    from json_metadata import (
        load_json_metadata,
        save_json_metadata,
        form_data_to_json_structure,
        json_structure_to_form_data,
        find_docx_for_json,
    )
    JSON_METADATA_AVAILABLE = True
except ImportError:
    JSON_METADATA_AVAILABLE = False
    print("⚠ Ошибка: не удалось импортировать json_metadata. Убедитесь, что json_metadata.py доступен.")

# ----------------------------
# Константы
# ----------------------------

SUPPORTED_EXTENSIONS = {".docx", ".rtf"}
SUPPORTED_JSON_EXTENSIONS = {".json"}

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
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      padding: 10px;
      margin: 0;
    }
    .container {
      max-width: 1400px;
      margin: 0 auto;
      background: white;
      border-radius: 8px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.2);
      min-height: auto;
      height: auto;
      padding-bottom: 20px;
    }
    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 15px 20px;
      text-align: center;
    }
    .header h1 {
      font-size: 22px;
      margin-bottom: 5px;
    }
    .header p {
      opacity: 0.9;
      font-size: 12px;
    }
    .content {
      padding: 15px 20px;
      min-height: auto;
      height: auto;
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
      color: #333;
      font-size: 13px;
    }
    .form-field-group input,
    .form-field-group textarea,
    .form-field-group select {
      width: 100%;
      padding: 10px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 14px;
      font-family: inherit;
      transition: border-color 0.2s;
    }
    .form-field-group input:focus,
    .form-field-group textarea:focus,
    .form-field-group select:focus {
      outline: none;
      border-color: #2196f3;
      box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
    }
    .form-field-group textarea {
      min-height: 60px;
      resize: vertical;
    }
    .form-instructions {
      background: #fff3cd;
      border: 1px solid #ffc107;
      border-radius: 4px;
      padding: 12px;
      margin-bottom: 20px;
      font-size: 12px;
    }
    .form-instructions h3 {
      margin: 0 0 8px 0;
      color: #856404;
      font-size: 14px;
    }
    .form-instructions ul {
      margin: 0;
      padding-left: 20px;
      color: #856404;
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
    .instructions{background:#fff3cd;border:1px solid #ffc107;border-radius:4px;padding:15px;margin-bottom:20px;}
    .instructions h3{margin-bottom:10px;color:#856404;font-size:14px;}
    .instructions ul{margin-left:20px;color:#856404;}
    .instructions li{margin:5px 0;}
    .field-group{margin-bottom:20px;}
    .field-group label{display:block;font-weight:600;margin-bottom:8px;color:#333;font-size:14px;}
    .field-group input,.field-group textarea,.field-group select{width:100%;padding:10px;border:1px solid #ddd;border-radius:4px;font-size:14px;font-family:inherit;}
    .field-group textarea{min-height:80px;resize:vertical;}
    .selected-lines{margin-top:5px;font-size:12px;color:#666;}
    .keywords-count{margin-top:5px;font-size:12px;color:#666;font-style:italic;}
    .field-group.active{background:#e3f2fd;border:2px solid #2196f3;border-radius:4px;padding:10px;}
    .buttons{display:flex;gap:10px;margin-top:20px;}
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
    .author-item{margin-bottom:10px;border:1px solid #ddd;border-radius:4px;overflow:hidden;}
    .author-header{display:flex;justify-content:space-between;align-items:center;padding:12px 15px;background:#f8f9fa;cursor:pointer;transition:background .2s;}
    .author-header:hover{background:#e9ecef;}
    .author-name{font-weight:600;color:#333;font-size:14px;}
    .author-toggle{color:#666;font-size:12px;transition:transform .2s;}
    .author-item.expanded .author-toggle{transform:rotate(180deg);}
    .author-actions{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;gap:10px;}
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
    .ref-action-btn.merge{color:#2196f3;border-color:#2196f3;}
    .ref-action-btn.merge:hover{background:#e3f2fd;}
    .line-editor-modal{display:none;position:fixed;z-index:2000;left:0;top:0;width:100%;height:100%;background:rgba(0,0,0,0.5);overflow:auto;}
    .line-editor-modal.active{display:flex;align-items:center;justify-content:center;}
    .line-editor-content{background:#fff;padding:20px;border-radius:8px;max-width:700px;width:80%;max-height:70vh;box-shadow:0 4px 20px rgba(0,0,0,0.3);}
    .line-editor-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;border-bottom:2px solid #e0e0e0;padding-bottom:10px;}
    .line-editor-header h2{margin:0;color:#333;font-size:18px;}
    .line-editor-textarea{width:100%;min-height:150px;max-height:400px;padding:12px;border:2px solid #ddd;border-radius:4px;font-size:14px;font-family:inherit;line-height:1.6;resize:vertical;background:#f9f9f9;}
    .line-editor-textarea:focus{outline:none;border-color:#667eea;background:#fff;}
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
      <h1>📄 Работа с метаданными статей</h1>
      <p>Выберите JSON файл для разметки</p>
      <div style="margin-top: 20px;">
        <button id="generateXmlBtn" class="btn-primary" style="padding: 12px 24px; font-size: 16px; font-weight: 600; border-radius: 6px; cursor: pointer; border: none; background: #4caf50; color: white; transition: background 0.2s;">
          📄 Сгенерировать XML
        </button>
      </div>
    </div>
    <div class="content">
      {% if files %}
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
          document.getElementById("generateXmlBtn")?.addEventListener("click", async function() {
            const btn = this;
            const originalText = btn.textContent;
            
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
                
                // Показываем уведомление
                const notification = document.createElement("div");
                notification.style.cssText = "position:fixed;top:20px;right:20px;background:#4caf50;color:#fff;padding:15px 20px;border-radius:4px;box-shadow:0 4px 12px rgba(0,0,0,0.2);z-index:3000;font-size:14px;max-width:400px;";
                notification.innerHTML = `<strong>Успешно!</strong><br>${data.message}<br><small>Создано файлов: ${data.files?.length || 0}</small>`;
                document.body.appendChild(notification);
                
                setTimeout(() => {
                  notification.remove();
                  btn.textContent = originalText;
                  btn.style.background = "#4caf50";
                  btn.disabled = false;
                }, 5000);
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
          
          // Теперь используем прямые ссылки на /markup/<filename> вместо AJAX загрузки
          
          // Проверяем localStorage для файлов, которые были только что сохранены
          // и подсвечиваем их как обработанные
          (function() {
            try {
              const savedFiles = JSON.parse(localStorage.getItem("recently_saved_files") || "[]");
              if (savedFiles.length > 0) {
                savedFiles.forEach(function(filename) {
                  const fileItem = document.querySelector(`.file-item[data-filename="${filename}"]`);
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
        
        <div id="lineCopyModal" class="line-editor-modal">
          <div class="line-editor-content">
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
              const hasNext = index < refs.length - 1;
              refItem.innerHTML = `
                <span class="ref-number">${index + 1}.</span>
                <span class="ref-text" contenteditable="true" spellcheck="false">${escapeHtml(ref)}</span>
                <div class="ref-actions">
                  ${hasNext ? `<button class="ref-action-btn merge" onclick="mergeWithNext(this)" title="Объединить со следующим">⇅</button>` : ''}
                  <button class="ref-action-btn delete" onclick="deleteReference(this)" title="Удалить">✕</button>
                </div>
              `;
              refsList.appendChild(refItem);
            });
          }
          
          modal.classList.add("active");
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
          
          if (confirm(`Объединить источник ${refItem.querySelector(".ref-number")?.textContent.trim()} со следующим?\\n\\nТекущий: ${currentText.substring(0, 50)}...\\nСледующий: ${nextText.substring(0, 50)}...`)) {
            const mergedText = currentText + " " + nextText;
            const currentTextSpan = refItem.querySelector(".ref-text");
            if (currentTextSpan) {
              currentTextSpan.textContent = mergedText;
            }
            nextItem.remove();
            renumberReferences();
            updateMergeButtons();
          }
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
          
          const lineCopyModal = document.getElementById("lineCopyModal");
          if (e.target === lineCopyModal) {
            closeCopyModal();
          }
        });
        
        // Закрытие модальных окон по Escape
        document.addEventListener("keydown", (e) => {
          if (e.key === "Escape") {
            closeRefsModal();
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
        <div class="empty-state">
          <h3>📁 Папка пуста</h3>
          <p>В папке json_input не найдено JSON файлов.</p>
          <p style="margin-top: 20px; font-size: 14px;">
            Поместите JSON файлы в подпапки вида: <code>issn_год_том_номер</code> или <code>issn_год_номер</code>
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
    .container{max-width:1400px;margin:0 auto;background:white;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1);}
    .header{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;padding:20px;text-align:center;}
    .header h1{font-size:24px;margin-bottom:5px;}
    .header p{opacity:.9;}
    .header-actions{display:flex;gap:10px;justify-content:center;margin-top:10px;}
    .header-btn{background:rgba(255,255,255,0.2);color:white;border:1px solid rgba(255,255,255,0.3);padding:8px 16px;border-radius:6px;text-decoration:none;font-size:14px;transition:all 0.2s;}
    .header-btn:hover{background:rgba(255,255,255,0.3);}
    .content{display:flex;min-height:calc(100vh - 200px);}
    .text-panel{flex:1;padding:20px;overflow-y:auto;max-height:calc(100vh - 200px);border-right:1px solid #e0e0e0;}
    .form-panel{width:400px;padding:20px;overflow-y:auto;max-height:calc(100vh - 200px);background:#fafafa;}

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
    .line-editor-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;border-bottom:2px solid #e0e0e0;padding-bottom:10px;}
    .line-editor-header h2{margin:0;color:#333;font-size:18px;}
    .line-editor-textarea{width:100%;min-height:150px;max-height:400px;padding:12px;border:2px solid #ddd;border-radius:4px;font-size:14px;font-family:inherit;line-height:1.6;resize:vertical;background:#f9f9f9;}
    .line-editor-textarea:focus{outline:none;border-color:#667eea;background:#fff;}
    .line-editor-actions{display:flex;justify-content:flex-end;gap:10px;margin-top:15px;padding-top:15px;border-top:1px solid #e0e0e0;}

    .instructions{background:#fff3cd;border:1px solid #ffc107;border-radius:4px;padding:15px;margin-bottom:20px;}
    .instructions h3{margin-bottom:10px;color:#856404;}
    .instructions ul{margin-left:20px;color:#856404;}
    .instructions li{margin:5px 0;}

    .field-group{margin-bottom:20px;}
    .field-group label{display:block;font-weight:600;margin-bottom:8px;color:#333;font-size:14px;}
    .field-group input,.field-group textarea{width:100%;padding:10px;border:1px solid #ddd;border-radius:4px;font-size:14px;font-family:inherit;}
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
    .ref-action-btn.merge{color:#2196f3;border-color:#2196f3;}
    .ref-action-btn.merge:hover{background:#e3f2fd;}
    
    .author-item{margin-bottom:10px;border:1px solid #ddd;border-radius:4px;overflow:hidden;}
    .author-header{display:flex;justify-content:space-between;align-items:center;padding:12px 15px;background:#f8f9fa;cursor:pointer;transition:background .2s;}
    .author-header:hover{background:#e9ecef;}
    .author-name{font-weight:600;color:#333;font-size:14px;}
    .author-toggle{color:#666;font-size:12px;transition:transform .2s;}
    .author-item.expanded .author-toggle{transform:rotate(180deg);}
    .author-actions{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;gap:10px;}
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
    .author-field input{width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;font-size:13px;font-family:inherit;}
    .author-field input:focus{outline:2px solid #667eea;outline-offset:2px;border-color:#667eea;}
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
            <button class="line-copy-btn" data-action="open-copy" title="Копировать фрагмент">✏️</button>
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
          <textarea id="title" name="title" required>{% if form_data %}{{ form_data.get('title', '')|e }}{% endif %}</textarea>
          <div class="selected-lines" id="title-lines"></div>
        </div>

        <div class="field-group">
          <label>Название (английский)</label>
          <textarea id="title_en" name="title_en">{% if form_data %}{{ form_data.get('title_en', '')|e }}{% endif %}</textarea>
          <div class="selected-lines" id="title_en-lines"></div>
        </div>

        <div class="field-group">
          <label>УДК</label>
          <input type="text" id="udc" name="udc" value="{% if form_data %}{{ form_data.get('udc', '')|e }}{% endif %}">
          <div class="selected-lines" id="udc-lines"></div>
        </div>

        <div class="field-group">
          <label>ББК</label>
          <input type="text" id="bbk" name="bbk" value="{% if form_data %}{{ form_data.get('bbk', '')|e }}{% endif %}">
        </div>

        <div class="field-group">
          <label>EDN</label>
          <input type="text" id="edn" name="edn" value="{% if form_data %}{{ form_data.get('edn', '')|e }}{% endif %}">
        </div>

        <div class="field-group">
          <label>DOI</label>
          <input type="text" id="doi" name="doi" value="{% if form_data %}{{ form_data.get('doi', '')|e }}{% endif %}">
          <div class="selected-lines" id="doi-lines"></div>
        </div>

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
                      <label>Организация (русский):</label>
                      <input type="text" class="author-input" data-field="orgName" data-lang="RUS" data-index="{{ loop.index0 }}" value="{{ rus_info.get('orgName', '')|e }}">
                      <div class="selected-lines" style="display:none;"></div>
                      <div class="keywords-count" id="org-count-rus-{{ loop.index0 }}">Количество организаций: 0</div>
                    </div>
                    <div class="author-field">
                      <label>Organization (English):</label>
                      <input type="text" class="author-input" data-field="orgName" data-lang="ENG" data-index="{{ loop.index0 }}" value="{{ eng_info.get('orgName', '')|e }}">
                      <div class="selected-lines" style="display:none;"></div>
                      <div class="keywords-count" id="org-count-eng-{{ loop.index0 }}">Количество организаций: 0</div>
                    </div>
                    <div class="author-field">
                      <label>Адрес (русский):</label>
                      <input type="text" class="author-input" data-field="address" data-lang="RUS" data-index="{{ loop.index0 }}" value="{{ rus_info.get('address', '')|e }}">
                    </div>
                    <div class="author-field">
                      <label>Address (English):</label>
                      <input type="text" class="author-input" data-field="address" data-lang="ENG" data-index="{{ loop.index0 }}" value="{{ eng_info.get('address', '')|e }}">
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
        </div>

        <div class="field-group">
          <label>Аннотация (английский)</label>
          <textarea id="annotation_en" name="annotation_en">{% if form_data %}{{ form_data.get('annotation_en', '')|e }}{% endif %}</textarea>
          <div class="selected-lines" id="annotation_en-lines"></div>
        </div>

        <div class="field-group">
          <label>Ключевые слова (русский)</label>
          <input type="text" id="keywords" name="keywords" value="{% if form_data %}{{ form_data.get('keywords', '')|e }}{% endif %}">
          <div class="selected-lines" id="keywords-lines"></div>
          <div class="keywords-count" id="keywords-count">Количество: 0</div>
        </div>

        <div class="field-group">
          <label>Ключевые слова (английский)</label>
          <input type="text" id="keywords_en" name="keywords_en" value="{% if form_data %}{{ form_data.get('keywords_en', '')|e }}{% endif %}">
          <div class="selected-lines" id="keywords_en-lines"></div>
          <div class="keywords-count" id="keywords_en-count">Количество: 0</div>
        </div>

        <div class="field-group">
          <label>Список литературы (русский)</label>
          <textarea id="references_ru" name="references_ru" rows="5">{% if form_data %}{{ form_data.get('references_ru', '')|e }}{% endif %}</textarea>
          <div class="selected-lines" id="references_ru-lines"></div>
          <div class="keywords-count" id="references_ru-count">Количество источников: 0</div>
          <button type="button" class="view-refs-btn" onclick="viewReferences('references_ru', 'Список литературы (русский)')">👁 Просмотреть список</button>
          <small style="color:#666;font-size:12px;">Каждая ссылка с новой строки</small>
        </div>

        <div class="field-group">
          <label>Список литературы (английский)</label>
          <textarea id="references_en" name="references_en" rows="5">{% if form_data %}{{ form_data.get('references_en', '')|e }}{% endif %}</textarea>
          <div class="selected-lines" id="references_en-lines"></div>
          <div class="keywords-count" id="references_en-count">Количество источников: 0</div>
          <button type="button" class="view-refs-btn" onclick="viewReferences('references_en', 'Список литературы (английский)')">👁 Просмотреть список</button>
          <small style="color:#666;font-size:12px;">Каждая ссылка с новой строки</small>
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

<div id="lineCopyModal" class="line-editor-modal">
  <div class="line-editor-content">
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
      refsList.appendChild(refItem);
    });
  }
  
  modal.classList.add("active");
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
  
  if (confirm(`Объединить источник ${refItem.querySelector(".ref-number")?.textContent.trim()} со следующим?\n\nТекущий: ${currentText.substring(0, 50)}...\nСледующий: ${nextText.substring(0, 50)}...`)) {
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
  }
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
  if (modal) {
    modal.classList.remove("active");
  }
}


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
          <label>Организация (русский):</label>
          <input type="text" class="author-input" data-field="orgName" data-lang="RUS" data-index="${index}" value="">
          <div class="selected-lines" style="display:none;"></div>
          <div class="keywords-count" id="org-count-rus-${index}">Количество организаций: 0</div>
        </div>
        <div class="author-field">
          <label>Organization (English):</label>
          <input type="text" class="author-input" data-field="orgName" data-lang="ENG" data-index="${index}" value="">
          <div class="selected-lines" style="display:none;"></div>
          <div class="keywords-count" id="org-count-eng-${index}">Количество организаций: 0</div>
        </div>
        <div class="author-field">
          <label>Адрес (русский):</label>
          <input type="text" class="author-input" data-field="address" data-lang="RUS" data-index="${index}" value="">
        </div>
        <div class="author-field">
          <label>Address (English):</label>
          <input type="text" class="author-input" data-field="address" data-lang="ENG" data-index="${index}" value="">
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
    const authorIndex = item.dataset.authorIndex || index;
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

  function autoExtractAuthorDataFromLine(text, authorIndex, skipField = null) {
    // Автоматически извлекает все доступные данные автора из строки и заполняет соответствующие поля
    // Это полезно, когда в одной строке содержится несколько данных (SPIN, email, AuthorID и т.д.)
    // skipField - поле, которое уже заполнено и не нужно извлекать повторно
    
    // Небольшая задержка, чтобы убедиться, что основное поле уже заполнено
    setTimeout(() => {
      // Извлекаем email, если он еще не заполнен и это не то поле, которое мы только что заполнили
      if (skipField !== "email") {
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
      if (skipField !== "spin") {
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
      if (skipField !== "orcid") {
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
      if (skipField !== "scopusid") {
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
      if (skipField !== "researcherid") {
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

  function countKeywords(text) {
    if (!text || !text.trim()) return 0;
    const cleaned = text.trim();
    // Подсчитываем количество ключевых слов, разделенных точкой с запятой или запятой
    if (cleaned.includes(";")) {
      return cleaned.split(";").map(s => s.trim()).filter(Boolean).length;
    }
    if (cleaned.includes(",")) {
      return cleaned.split(",").map(s => s.trim()).filter(Boolean).length;
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

  window.countOrganizations = function(text) {
    if (!text || !text.trim()) return 0;
    const cleaned = text.trim();
    // Подсчитываем количество организаций, разделенных точкой с запятой или запятой
    if (cleaned.includes(";")) {
      return cleaned.split(";").map(s => s.trim()).filter(Boolean).length;
    }
    if (cleaned.includes(",")) {
      return cleaned.split(",").map(s => s.trim()).filter(Boolean).length;
    }
    // Если нет разделителей, считаем как одну организацию
    return cleaned ? 1 : 0;
  };

  window.updateOrgCount = function(authorIndex, lang) {
    const field = document.querySelector(`.author-input[data-field="orgName"][data-lang="${lang}"][data-index="${authorIndex}"]`);
    const countEl = document.getElementById(`org-count-${lang.toLowerCase()}-${authorIndex}`);
    if (!field || !countEl) return;
    
    const count = window.countOrganizations(field.value);
    countEl.textContent = `Количество организаций: ${count}`;
  };

  window.countReferences = function(text) {
    if (!text || !text.trim()) return 0;
    // Подсчитываем количество источников - каждая непустая строка = один источник
    const lines = text.split("\n")
      .map(line => line.trim())
      .filter(line => line.length > 0);
    return lines.length;
  };

  window.updateReferencesCount = function(fieldId) {
    const field = document.getElementById(fieldId);
    const countEl = document.getElementById(fieldId + "-count");
    if (!field || !countEl) return;
    
    const count = window.countReferences(field.value);
    countEl.textContent = `Количество источников: ${count}`;
  };

  function processFunding(text) {
    if (!text) return "";
    return text.replace(/^(Финансирование|Funding)\s*[.:]?\s*/i, "").replace(/^(Финансирование|Funding)\s*/i, "").trim();
  }

  function processAnnotation(text) {
    if (!text) return "";
    // Удаляем префикс "Аннотация", "Annotation" или "Abstract" в начале текста (с возможными двоеточиями и пробелами)
    return text.replace(/^(Аннотация|Annotation|Abstract)\s*[.:]?\s*/i, "").trim();
  }

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
        value = fullText.trim();
      } else if (fieldName === "initials") {
        if (!lang) return;
        targetField = $(`.author-input[data-field="initials"][data-lang="${lang.toUpperCase()}"][data-index="${authorIndex}"]`);
        value = fullText.trim();
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
        autoExtractAuthorDataFromLine(fullText, authorIndex, "orcid");
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
      setTimeout(() => updateKeywordsCount(fieldId), 100);
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
      value = udc ? udc : fullText.trim();
    } else if (fieldId === "funding" || fieldId === "funding_en") {
      const funding = processFunding(fullText);
      value = funding;
    } else if (fieldId === "annotation" || fieldId === "annotation_en") {
      // Обрабатываем аннотацию: удаляем префикс "Аннотация" или "Annotation" если он есть
      const annotation = processAnnotation(fullText);
      // Если поле уже содержит текст, добавляем через пробел
      value = field.value.trim() ? (field.value.trim() + " " + annotation) : annotation;
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
    // Очищаем префикс "Аннотация" из полей аннотации при загрузке страницы
    const annotationField = document.getElementById("annotation");
    if (annotationField && annotationField.value) {
      const cleaned = processAnnotation(annotationField.value);
      if (cleaned !== annotationField.value) {
        annotationField.value = cleaned;
      }
    }
    
    const annotationEnField = document.getElementById("annotation_en");
    if (annotationEnField && annotationEnField.value) {
      const cleaned = processAnnotation(annotationEnField.value);
      if (cleaned !== annotationEnField.value) {
        annotationEnField.value = cleaned;
      }
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

    // Инициализация счетчиков ключевых слов при загрузке
    const keywordsField = $("#keywords");
    const keywordsEnField = $("#keywords_en");
    if (keywordsField) {
      updateKeywordsCount("keywords");
      keywordsField.addEventListener("input", () => updateKeywordsCount("keywords"));
    }
    if (keywordsEnField) {
      updateKeywordsCount("keywords_en");
      keywordsEnField.addEventListener("input", () => updateKeywordsCount("keywords_en"));
    }
    
    // Инициализация счетчиков литературы при загрузке
    const referencesRuField = $("#references_ru");
    const referencesEnField = $("#references_en");
    if (referencesRuField) {
      if (window.updateReferencesCount) {
        window.updateReferencesCount("references_ru");
        referencesRuField.addEventListener("input", () => window.updateReferencesCount("references_ru"));
      }
    }
    if (referencesEnField) {
      if (window.updateReferencesCount) {
        window.updateReferencesCount("references_en");
        referencesEnField.addEventListener("input", () => window.updateReferencesCount("references_en"));
      }
    }
    
    // Инициализация обработчиков для обновления имен авторов
    const existingAuthors = $$(".author-item");
    existingAuthors.forEach(item => {
      const index = parseInt(item.dataset.authorIndex, 10);
      if (!isNaN(index)) {
        attachAuthorNameListeners(index);
        // Дополнительная инициализация счетчиков организаций
        setTimeout(() => {
          if (window.updateOrgCount) {
            window.updateOrgCount(index, "RUS");
            window.updateOrgCount(index, "ENG");
          }
        }, 200);
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
  });
})();
</script>
</body>
</html>
"""


# ----------------------------
# Вспомогательные функции
# ----------------------------

def is_json_processed(json_path: Path) -> bool:
    """
    Проверяет, обработан ли JSON файл через веб-интерфейс.
    Файл считается обработанным только если он был сохранен через кнопку "Сохранить"
    (отслеживается через специальное поле в JSON).
    
    Args:
        json_path: Путь к JSON файлу
        
    Returns:
        True, если файл обработан через веб-интерфейс
    """
    if not json_path.exists():
        return False
    
    try:
        if not JSON_METADATA_AVAILABLE:
            return False
        
        json_data = load_json_metadata(json_path)
        
        # Проверяем наличие специального флага, который устанавливается при сохранении через веб-интерфейс
        # Это гарантирует, что файл был обработан именно через веб-форму, а не просто содержит данные
        # Файл считается обработанным ТОЛЬКО если есть этот флаг
        is_processed_flag = json_data.get("_processed_via_web", False)
        
        return is_processed_flag
        
    except Exception:
        # В случае ошибки считаем файл необработанным
        return False


def get_json_files(json_input_dir: Path) -> list[dict]:
    """
    Получает список JSON файлов из указанной директории и всех подпапок.
    JSON файлы могут находиться в подпапках вида issn_год_том_номер или issn_год_номер.
    
    Args:
        json_input_dir: Путь к директории с JSON файлами
        
    Returns:
        Список словарей с информацией о файлах (включая относительный путь)
    """
    if not json_input_dir.exists() or not json_input_dir.is_dir():
        return []
    
    files = []
    # Рекурсивный поиск всех JSON файлов
    for file_path in sorted(json_input_dir.rglob("*.json"), key=lambda x: (x.parent.name, x.name)):
        try:
            # Пропускаем файлы в корне json_input (если они там есть)
            # Работаем только с файлами в подпапках
            if file_path.parent == json_input_dir:
                continue
            
            stat = file_path.stat()
            size_kb = stat.st_size / 1024
            modified = time.strftime("%d.%m.%Y %H:%M", time.localtime(stat.st_mtime))
            
            # Относительный путь от json_input_dir
            relative_path = file_path.relative_to(json_input_dir)
            
            # Проверяем, обработан ли файл
            is_processed = is_json_processed(file_path)
            
            # Извлекаем номера страниц для сортировки
            pages_start = None
            pages_str = ""
            if JSON_METADATA_AVAILABLE:
                try:
                    json_data = load_json_metadata(file_path)
                    pages_str = str(json_data.get("pages", "")).strip()
                    if pages_str:
                        # Парсим формат "5-20" или "21-34" и т.д.
                        match = re.match(r'^(\d+)(?:-(\d+))?', pages_str)
                        if match:
                            pages_start = int(match.group(1))
                except Exception:
                    pass
            
            files.append({
                "name": str(relative_path).replace("\\", "/"),  # Относительный путь для маршрутов Flask (с прямыми слэшами)
                "display_name": file_path.name,  # Только имя файла для отображения
                "path": file_path,  # Полный путь
                "size_kb": f"{size_kb:.1f}",
                "modified": modified,
                "extension": ".json",
                "is_processed": is_processed,  # Флаг обработки
                "pages_start": pages_start,  # Начальная страница для сортировки (None если нет)
                "pages": pages_str,  # Строка с номерами страниц
            })
        except Exception:
            continue
    
    # Сортируем файлы: сначала по подпапке, затем по номерам страниц (если есть)
    # Файлы без страниц идут в конец
    files.sort(key=lambda x: (
        x["path"].parent.name,  # Сначала по подпапке
        (x["pages_start"] if x["pages_start"] is not None else float('inf')),  # Затем по начальной странице
        x["display_name"]  # В конце по имени файла
    ))
    
    return files


def get_source_files(input_dir: Path) -> list[dict]:
    """
    Получает список DOCX/RTF файлов из указанной директории и всех подпапок.
    Файлы могут находиться в подпапках вида issn_год_том_номер или issn_год_номер.
    
    Args:
        input_dir: Путь к директории с исходными файлами
        
    Returns:
        Список словарей с информацией о файлах (включая относительный путь)
    """
    if not input_dir.exists() or not input_dir.is_dir():
        return []
    
    files = []
    # Рекурсивный поиск всех DOCX/RTF файлов
    for ext in SUPPORTED_EXTENSIONS:
        for file_path in sorted(input_dir.rglob(f"*{ext}"), key=lambda x: (x.parent.name, x.name)):
            try:
                # Пропускаем файлы в корне words_input (если они там есть)
                # Работаем только с файлами в подпапках
                if file_path.parent == input_dir:
                    continue
                
                stat = file_path.stat()
                size_kb = stat.st_size / 1024
                modified = time.strftime("%d.%m.%Y %H:%M", time.localtime(stat.st_mtime))
                
                # Относительный путь от input_dir
                relative_path = file_path.relative_to(input_dir)
                
                files.append({
                    "name": str(relative_path),  # Путь вида "подпапка/файл.docx"
                    "path": file_path,  # Полный путь
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

def create_app(json_input_dir: Path, words_input_dir: Path, use_word_reader: bool = False, xml_output_dir: Path = None, list_of_journals_path: Path = None) -> Flask:
    """
    Создает Flask приложение для работы с JSON метаданными.
    
    Args:
        json_input_dir: Путь к директории с JSON файлами
        words_input_dir: Путь к директории с DOCX/RTF файлами
        use_word_reader: Использовать ли word_reader для конвертации
        xml_output_dir: Путь к директории для сохранения XML файлов
        list_of_journals_path: Путь к файлу list_of_journals.json
        
    Returns:
        Flask приложение
    """
    app = Flask(__name__)
    
    # Определяем пути по умолчанию, если не указаны
    if xml_output_dir is None:
        script_dir = Path(__file__).parent.absolute()
        xml_output_dir = script_dir / "xml_output"
    
    if list_of_journals_path is None:
        script_dir = Path(__file__).parent.absolute()
        list_of_journals_path = script_dir / "list_of_journals.json"
    
    @app.route("/")
    def index():
        """Главная страница со списком JSON файлов."""
        files = get_json_files(json_input_dir)
        return render_template_string(HTML_TEMPLATE, files=files)
    
    @app.route("/generate-xml", methods=["POST"])
    def generate_xml():
        """Генерация XML файлов для всех выпусков."""
        try:
            from xml_generator_helper import generate_xml_for_all_folders
            
            if not list_of_journals_path.exists():
                return jsonify({
                    "success": False,
                    "error": f"Файл list_of_journals.json не найден: {list_of_journals_path}"
                }), 400
            
            # Генерируем XML для всех папок
            results = generate_xml_for_all_folders(
                json_input_dir=json_input_dir,
                xml_output_dir=xml_output_dir,
                list_of_journals_path=list_of_journals_path
            )
            
            if results:
                return jsonify({
                    "success": True,
                    "message": f"Успешно сгенерировано XML файлов: {len(results)}",
                    "files": [str(r) for r in results]
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Не удалось сгенерировать XML файлы. Проверьте наличие JSON файлов в подпапках."
                }), 400
                
        except ImportError as e:
            return jsonify({
                "success": False,
                "error": f"Модуль xml_generator_helper недоступен: {e}"
            }), 500
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Ошибка при генерации XML: {str(e)}"
            }), 500
    
    @app.route("/view/<path:filename>")
    def view_file(filename: str):
        """Конвертация и отображение выбранного файла."""
        # Безопасность: проверяем, что путь не содержит опасные символы
        if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
            abort(404)
        
        file_path = words_input_dir / filename
        
        if not file_path.exists() or not file_path.is_file():
            abort(404)
        
        # Проверяем расширение
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            abort(404)
        
        # Проверяем, что файл находится внутри words_input_dir
        try:
            file_path.resolve().relative_to(words_input_dir.resolve())
        except ValueError:
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
    
    @app.route("/markup/<path:json_filename>")
    def markup_file(json_filename: str):
        """Страница разметки метаданных для выбранного JSON файла."""
        if not METADATA_MARKUP_AVAILABLE or not JSON_METADATA_AVAILABLE:
            return "Ошибка: необходимые модули недоступны", 500
        
        # Безопасность: проверяем, что путь не содержит опасные символы
        if ".." in json_filename or json_filename.startswith("/") or json_filename.startswith("\\"):
            abort(404)
        
        json_path = json_input_dir / json_filename
        
        if not json_path.exists() or not json_path.is_file():
            abort(404)
        
        # Проверяем расширение
        if json_path.suffix.lower() != ".json":
            abort(404)
        
        # Проверяем, что файл находится внутри json_input_dir
        try:
            json_path.resolve().relative_to(json_input_dir.resolve())
        except ValueError:
            abort(404)
        
        try:
            # Загружаем существующий JSON
            json_data = load_json_metadata(json_path)
            
            # Преобразуем JSON в данные для формы
            form_data = json_structure_to_form_data(json_data)
            
            # Находим соответствующий DOCX файл
            # Передаем json_input_dir для поиска в той же подпапке
            docx_path = find_docx_for_json(json_path, words_input_dir, json_input_dir)
            
            if not docx_path:
                # Определяем подпапку для более информативного сообщения
                try:
                    relative_path = json_path.relative_to(json_input_dir)
                    if len(relative_path.parts) > 1:
                        subdir_name = relative_path.parts[0]
                        error_msg = (
                            f"Ошибка: не найден DOCX/RTF файл для статьи {json_filename}<br><br>"
                            f"Искали:<br>"
                            f"1. Отдельный файл: {json_path.stem}.docx или {json_path.stem}.rtf<br>"
                            f"2. Общий файл выпуска в папке '{subdir_name}':<br>"
                            f"   - {subdir_name}.docx<br>"
                            f"   - issue.docx<br>"
                            f"   - выпуск.docx<br><br>"
                            f"Поместите файл в папку: words_input/{subdir_name}/"
                        )
                    else:
                        error_msg = f"Ошибка: не найден соответствующий DOCX/RTF файл для {json_filename}"
                except ValueError:
                    error_msg = f"Ошибка: не найден соответствующий DOCX/RTF файл для {json_filename}"
                return error_msg, 404
            
            # Проверяем, является ли найденный файл общим файлом выпуска
            # (не совпадает с именем JSON файла)
            is_common_file = docx_path.stem != json_path.stem
            
            # Конвертируем DOCX в HTML
            html_body, warnings = convert_file_to_html(docx_path, use_word_reader=use_word_reader)
            
            # Извлекаем текст из HTML для разметки
            lines = extract_text_from_html(html_body)
            
            # Опциональный отладочный вывод (можно включить через переменную окружения DEBUG_LITERATURE=1)
            import os
            if os.getenv("DEBUG_LITERATURE") == "1" and ("Литература" in html_body or "литература" in html_body.lower()):
                lit_pos = html_body.lower().find("литература")
                if lit_pos != -1:
                    debug_html = html_body[max(0, lit_pos-100):lit_pos+2000]
                    print("=" * 80)
                    print("DEBUG: HTML вокруг слова 'Литература':")
                    print("=" * 80)
                    print(debug_html)
                    print("=" * 80)
                
                print("=" * 80)
                print(f"DEBUG: Всего извлечено строк: {len(lines)}")
                lit_lines = [line for line in lines if "литература" in line.get("text", "").lower() or 
                             (line.get("text", "").strip() and 
                              re.match(r'^\d+\.', line.get("text", "").strip()))]
                print(f"DEBUG: Найдено строк, связанных с литературой: {len(lit_lines)}")
                if lit_lines:
                    print("DEBUG: Примеры строк литературы:")
                    for i, line in enumerate(lit_lines[:5], 1):
                        print(f"  {i}. Строка {line.get('line_number')}: {line.get('text', '')[:100]}...")
                print("=" * 80)
            
            if warnings:
                print(f"Предупреждения для {json_filename}: {warnings}")
            
            # Если используется общий файл, пытаемся найти начало статьи по названию и/или фамилии автора
            article_start_line = None
            if is_common_file:
                # Получаем название статьи из JSON (приоритет: RUS, затем ENG)
                art_titles = json_data.get("artTitles", {})
                title_rus = str(art_titles.get("RUS", "")).strip()
                title_eng = str(art_titles.get("ENG", "")).strip()
                search_title = title_rus if title_rus else title_eng
                
                # Получаем фамилию первого автора из JSON (приоритет: RUS, затем ENG)
                author_surname = None
                authors = json_data.get("authors", [])
                if authors and isinstance(authors, list) and len(authors) > 0:
                    first_author = authors[0]
                    if isinstance(first_author, dict):
                        individ_info = first_author.get("individInfo", {})
                        rus_info = individ_info.get("RUS", {})
                        eng_info = individ_info.get("ENG", {})
                        surname_rus = str(rus_info.get("surname", "")).strip()
                        surname_eng = str(eng_info.get("surname", "")).strip()
                        author_surname = surname_rus if surname_rus else surname_eng
                
                # Используем название или фамилию автора для поиска
                search_terms = []
                if search_title:
                    search_terms.append(("title", search_title))
                if author_surname and len(author_surname) >= 2:
                    search_terms.append(("author", author_surname))
                
                if search_terms:
                    # Определяем конец содержания (оглавления)
                    # Ищем маркеры содержания: "Содержание", "Оглавление", "Contents", "Table of Contents"
                    content_end_line = 0
                    content_markers = [
                        r'содержание',
                        r'оглавление',
                        r'contents',
                        r'table of contents',
                        r'содержание\s*$',
                        r'оглавление\s*$',
                    ]
                    
                    # Ищем последнее вхождение маркера содержания
                    for idx, line in enumerate(lines):
                        line_text = line.get("text", "").lower().strip()
                        for marker in content_markers:
                            if re.search(marker, line_text, re.IGNORECASE):
                                # Найдено содержание, запоминаем строку
                                # Обычно содержание занимает несколько страниц, пропускаем еще 20-30 строк
                                content_end_line = idx + 30
                                break
                        if content_end_line > 0:
                            break
                    
                    # Если не нашли маркеры, пропускаем первые 50 строк (где обычно находится содержание)
                    if content_end_line == 0:
                        content_end_line = min(50, len(lines))
                    
                    print(f"Поиск статьи начинается со строки {content_end_line + 1} (пропущено содержание)")
                    if search_title:
                        print(f"  Ищем по названию: '{search_title[:50]}...'")
                    if author_surname:
                        print(f"  Ищем по фамилии автора: '{author_surname}'")
                    
                    # Функция для проверки, не является ли строка частью содержания
                    def is_content_line(line_text):
                        """Проверяет, не является ли строка частью содержания"""
                        text = line_text.strip()
                        # Исключаем очень короткие строки
                        if len(text) < 5:
                            return True
                        # Исключаем строки, заканчивающиеся только числом (номер страницы)
                        if re.search(r'^\s*\S+.*\d+\s*$', text) and len(re.findall(r'\d+', text)) <= 2:
                            return True
                        return False
                    
                    # Ищем по всем доступным терминам (сначала фамилия автора, затем название)
                    # Фамилия автора обычно более надежный маркер
                    search_order = sorted(search_terms, key=lambda x: 0 if x[0] == "author" else 1)
                    
                    for search_type, search_term in search_order:
                        if article_start_line:
                            break
                        
                        # Нормализуем термин для поиска
                        search_term_normalized = re.sub(r'\s+', ' ', search_term.lower().strip())
                        
                        # Ищем точное совпадение или частичное
                        for idx in range(content_end_line, len(lines)):
                            line = lines[idx]
                            line_text = line.get("text", "")
                            line_text_normalized = re.sub(r'\s+', ' ', line_text.lower().strip())
                            
                            # Для фамилии автора ищем точное совпадение или начало строки
                            if search_type == "author":
                                # Фамилия должна быть отдельным словом или в начале строки
                                if (search_term_normalized == line_text_normalized or
                                    line_text_normalized.startswith(search_term_normalized + " ") or
                                    re.search(r'\b' + re.escape(search_term_normalized) + r'\b', line_text_normalized)):
                                    if not is_content_line(line_text):
                                        article_start_line = idx + 1
                                        print(f"✓ Найдено начало статьи по фамилии автора '{search_term[:30]}...' на строке {article_start_line}")
                                        break
                            
                            # Для названия ищем точное совпадение или частичное (минимум 10 символов)
                            elif search_type == "title":
                                if (search_term_normalized == line_text_normalized or 
                                    (len(search_term_normalized) >= 10 and search_term_normalized in line_text_normalized)):
                                    if not is_content_line(line_text):
                                        article_start_line = idx + 1
                                        print(f"✓ Найдено начало статьи по названию '{search_term[:50]}...' на строке {article_start_line}")
                                        break
                        
                        # Если не нашли точное совпадение для названия, ищем по первым словам
                        if not article_start_line and search_type == "title" and len(search_term.split()) >= 3:
                            title_words = search_term.split()
                            # Берем первые 3-5 слов для поиска
                            search_phrase = " ".join(title_words[:min(5, len(title_words))])
                            search_phrase_normalized = re.sub(r'\s+', ' ', search_phrase.lower().strip())
                            
                            for idx in range(content_end_line, len(lines)):
                                line = lines[idx]
                                line_text = line.get("text", "")
                                line_text_normalized = re.sub(r'\s+', ' ', line_text.lower().strip())
                                
                                if search_phrase_normalized in line_text_normalized:
                                    if not is_content_line(line_text):
                                        article_start_line = idx + 1
                                        print(f"✓ Найдено начало статьи по первым словам названия '{search_phrase[:50]}...' на строке {article_start_line}")
                                        break
            
            # Передаем данные формы в шаблон для предзаполнения
            # Добавляем информацию о том, используется ли общий файл
            return render_template_string(
                MARKUP_TEMPLATE, 
                filename=json_filename, 
                lines=lines,
                form_data=form_data or {},
                is_common_file=is_common_file,
                common_file_name=docx_path.name if is_common_file else None,
                article_start_line=article_start_line
            )
        except Exception as e:
            error_msg = f"Ошибка при подготовке разметки: {e}"
            print(error_msg)
            return error_msg, 500
    
    @app.route("/api/article/<path:json_filename>")
    def api_get_article(json_filename: str):
        """API endpoint для получения данных статьи через AJAX."""
        # Явно указываем, что используем глобальный модуль re
        global re
        if not METADATA_MARKUP_AVAILABLE or not JSON_METADATA_AVAILABLE:
            return jsonify(error="Необходимые модули недоступны"), 500
        
        # Безопасность: проверяем, что путь не содержит опасные символы
        if ".." in json_filename or json_filename.startswith("/") or json_filename.startswith("\\"):
            abort(404)
        
        json_path = json_input_dir / json_filename
        
        if not json_path.exists() or not json_path.is_file():
            abort(404)
        
        # Проверяем расширение
        if json_path.suffix.lower() != ".json":
            abort(404)
        
        # Проверяем, что файл находится внутри json_input_dir
        try:
            json_path.resolve().relative_to(json_input_dir.resolve())
        except ValueError:
            abort(404)
        
        try:
            # Загружаем существующий JSON
            json_data = load_json_metadata(json_path)
            
            # Преобразуем JSON в данные для формы
            form_data = json_structure_to_form_data(json_data)
            
            # Находим соответствующий DOCX файл
            docx_path = find_docx_for_json(json_path, words_input_dir, json_input_dir)
            
            if not docx_path:
                return jsonify(error="DOCX файл не найден"), 404
            
            # Проверяем, является ли найденный файл общим файлом выпуска
            is_common_file = docx_path.stem != json_path.stem
            
            # Конвертируем DOCX в HTML
            html_body, warnings = convert_file_to_html(docx_path, use_word_reader=use_word_reader)
            
            # Извлекаем текст из HTML для разметки
            lines = extract_text_from_html(html_body)
            
            # Если используется общий файл, пытаемся найти начало статьи
            article_start_line = None
            if is_common_file:
                art_titles = json_data.get("artTitles", {})
                title_rus = str(art_titles.get("RUS", "")).strip()
                title_eng = str(art_titles.get("ENG", "")).strip()
                search_title = title_rus if title_rus else title_eng
                
                author_surname = None
                authors = json_data.get("authors", [])
                if authors and isinstance(authors, list) and len(authors) > 0:
                    first_author = authors[0]
                    if isinstance(first_author, dict):
                        individ_info = first_author.get("individInfo", {})
                        rus_info = individ_info.get("RUS", {})
                        eng_info = individ_info.get("ENG", {})
                        surname_rus = str(rus_info.get("surname", "")).strip()
                        surname_eng = str(eng_info.get("surname", "")).strip()
                        author_surname = surname_rus if surname_rus else surname_eng
                
                search_terms = []
                if search_title:
                    search_terms.append(("title", search_title))
                if author_surname and len(author_surname) >= 2:
                    search_terms.append(("author", author_surname))
                
                if search_terms:
                    content_end_line = 0
                    content_markers = [
                        r'содержание',
                        r'оглавление',
                        r'contents',
                        r'table of contents',
                    ]
                    
                    for idx, line in enumerate(lines):
                        line_text = line.get("text", "").lower().strip()
                        for marker in content_markers:
                            if re.search(marker, line_text, re.IGNORECASE):
                                content_end_line = idx + 30
                                break
                        if content_end_line > 0:
                            break
                    
                    if content_end_line == 0:
                        content_end_line = min(50, len(lines))
                    
                    def is_content_line(line_text):
                        text = line_text.strip()
                        if len(text) < 5:
                            return True
                        if re.search(r'^\s*\S+.*\d+\s*$', text) and len(re.findall(r'\d+', text)) <= 2:
                            return True
                        return False
                    
                    search_order = sorted(search_terms, key=lambda x: 0 if x[0] == "author" else 1)
                    
                    for search_type, search_term in search_order:
                        if article_start_line:
                            break
                        
                        search_term_normalized = re.sub(r'\s+', ' ', search_term.lower().strip())
                        
                        for idx in range(content_end_line, len(lines)):
                            line = lines[idx]
                            line_text = line.get("text", "")
                            line_text_normalized = re.sub(r'\s+', ' ', line_text.lower().strip())
                            
                            if search_type == "author":
                                if (search_term_normalized == line_text_normalized or
                                    line_text_normalized.startswith(search_term_normalized + " ") or
                                    re.search(r'\b' + re.escape(search_term_normalized) + r'\b', line_text_normalized)):
                                    if not is_content_line(line_text):
                                        article_start_line = idx + 1
                                        break
                            
                            elif search_type == "title":
                                if (search_term_normalized == line_text_normalized or 
                                    (len(search_term_normalized) >= 10 and search_term_normalized in line_text_normalized)):
                                    if not is_content_line(line_text):
                                        article_start_line = idx + 1
                                        break
            
            # Генерируем HTML для текста статьи (только строки для выделения)
            from html import escape
            text_html = '<div class="search-box" style="margin-bottom: 15px; position: sticky; top: 0; background: white; padding: 10px 0; z-index: 100; border-bottom: 1px solid #e0e0e0;"><input type="text" id="searchInput" placeholder="🔍 Поиск в тексте..." style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"></div><div id="textContent">'
            for line in lines:
                line_text = escape(str(line.get("text", "")))
                line_id = escape(str(line.get("id", "")))
                line_number = escape(str(line.get("line_number", "")))
                # Добавляем класс для начала статьи, если это нужная строка
                start_class = ' article-start-marker' if article_start_line and line.get("line_number") == article_start_line else ''
                text_html += f'<div class="line{start_class}" data-id="{line_id}" data-line="{line_number}"><span class="line-number">{line_number}</span><span class="line-text">{line_text}</span><button class="line-copy-btn" data-action="open-copy" title="Копировать фрагмент">✏️</button></div>'
            text_html += '</div>'
            
            # Генерируем HTML для формы (используем упрощенную версию MARKUP_TEMPLATE)
            # Извлекаем только форму из MARKUP_TEMPLATE
            from jinja2 import Template
            form_template = Template(MARKUP_TEMPLATE)
            form_html = form_template.render(
                filename=json_filename,
                form_data=form_data,
                lines=lines,
                is_common_file=is_common_file,
                article_start_line=article_start_line,
                common_file_name=docx_path.name if is_common_file else None
            )
            
            # Извлекаем только часть формы (без всего шаблона)
            # Находим начало формы
            form_start = form_html.find('<form id="metadataForm">')
            form_end = form_html.find('</form>') + 7
            
            if form_start != -1 and form_end > form_start:
                # Извлекаем форму и инструкции
                instructions_start = form_html.find('<div class="instructions">')
                instructions_end = form_html.find('</div>', instructions_start) + 6 if instructions_start != -1 else -1
                
                form_section = ''
                if instructions_start != -1 and instructions_end > instructions_start:
                    form_section += form_html[instructions_start:instructions_end]
                form_section += form_html[form_start:form_end]
                
                # Добавляем панель выбора полей
                selection_panel_start = form_html.find('<div id="selectionPanel"')
                if selection_panel_start != -1:
                    # Находим закрывающий тег для selectionPanel (может быть вложен)
                    depth = 0
                    pos = selection_panel_start
                    selection_panel_end = len(form_html)
                    while pos < len(form_html):
                        if form_html[pos:pos+4] == '<div':
                            depth += 1
                        elif form_html[pos:pos+6] == '</div>':
                            depth -= 1
                            if depth == 0:
                                selection_panel_end = pos + 6
                                break
                        pos += 1
                    form_section += form_html[selection_panel_start:selection_panel_end]
                
                # НЕ извлекаем JavaScript из MARKUP_TEMPLATE, чтобы избежать синтаксических ошибок
                # Все необходимые функции уже определены в главном шаблоне HTML_TEMPLATE
                # JavaScript из MARKUP_TEMPLATE может содержать сложные конструкции, которые ломаются при извлечении
            else:
                form_section = '<p>Ошибка генерации формы</p>'
            
            return jsonify({
                "html_content": text_html,
                "form_html": form_section,
                "filename": json_filename,
                "article_start_line": article_start_line
            })
            
        except Exception as e:
            error_msg = f"Ошибка при загрузке статьи: {e}"
            print(error_msg)
            import traceback
            error_details = traceback.format_exc()
            print(error_details)
            return jsonify(error=error_msg, details=error_details), 500
    
    @app.route("/markup/<path:json_filename>/save", methods=["POST"])
    def save_metadata(json_filename: str):
        """Сохранение метаданных обратно в JSON файл."""
        if not JSON_METADATA_AVAILABLE:
            return jsonify(success=False, error="Модуль json_metadata недоступен"), 500
        
        # Безопасность: проверяем, что путь не содержит опасные символы
        if ".." in json_filename or json_filename.startswith("/") or json_filename.startswith("\\"):
            abort(404)
        
        json_path = json_input_dir / json_filename
        
        if not json_path.exists() or not json_path.is_file():
            abort(404)
        
        # Проверяем, что файл находится внутри json_input_dir
        try:
            json_path.resolve().relative_to(json_input_dir.resolve())
        except ValueError:
            abort(404)
        
        try:
            payload = request.get_json(force=True, silent=False)
            if not isinstance(payload, dict):
                return jsonify(success=False, error="Ожидался JSON-объект."), 400
            
            # Загружаем существующий JSON
            existing_json = load_json_metadata(json_path)
            
            # Преобразуем данные формы в структуру JSON и обновляем существующий JSON
            updated_json = form_data_to_json_structure(payload, existing_json)
            
            # Устанавливаем флаг, что файл был обработан через веб-интерфейс
            updated_json["_processed_via_web"] = True
            
            # Сохраняем обновленный JSON обратно в исходный файл в json_input
            save_json_metadata(updated_json, json_path)
            
            return jsonify(success=True, filename=str(json_path))
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
        "--json-input-dir",
        default=None,
        help="Путь к папке с JSON файлами (по умолчанию: json_input)"
    )
    parser.add_argument(
        "--words-input-dir",
        default=None,
        help="Путь к папке с DOCX/RTF файлами (по умолчанию: words_input)"
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
        "--use-word-reader",
        action="store_true",
        help="Использовать word_reader для конвертации"
    )
    parser.add_argument(
        "--no-debug",
        action="store_true",
        help="Отключить режим отладки (по умолчанию включен для разработки)"
    )
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent.resolve()
    
    # Определяем директорию с JSON файлами
    if args.json_input_dir:
        json_input_dir = Path(args.json_input_dir)
        if not json_input_dir.is_absolute():
            json_input_dir = script_dir / json_input_dir
    else:
        json_input_dir = script_dir / "json_input"
    
    if not json_input_dir.exists():
        json_input_dir.mkdir(parents=True, exist_ok=True)
        print(f"⚠ Создана папка: {json_input_dir}")
        print("   Поместите JSON файлы в подпапки вида: issn_год_том_номер или issn_год_номер")
    
    # Определяем директорию с DOCX/RTF файлами
    if args.words_input_dir:
        words_input_dir = Path(args.words_input_dir)
        if not words_input_dir.is_absolute():
            words_input_dir = script_dir / words_input_dir
    else:
        words_input_dir = script_dir / "words_input"
    
    if not words_input_dir.exists():
        words_input_dir.mkdir(parents=True, exist_ok=True)
        print(f"⚠ Создана папка: {words_input_dir}")
        print("   Поместите DOCX или RTF файлы в подпапки вида: issn_год_том_номер или issn_год_номер")
    
    # Определяем пути для генерации XML
    xml_output_dir = script_dir / "xml_output"
    list_of_journals_path = script_dir / "list_of_journals.json"
    
    app = create_app(
        json_input_dir, 
        words_input_dir, 
        use_word_reader=args.use_word_reader,
        xml_output_dir=xml_output_dir,
        list_of_journals_path=list_of_journals_path
    )
    
    # Формируем URL главной страницы
    url = f"http://127.0.0.1:{args.port}/"
    
    if not args.no_browser:
        open_browser_later(url)
    
    print("\n" + "=" * 80)
    print("🌐 Веб-приложение для работы с метаданными")
    print("=" * 80)
    print(f"📁 Папка с JSON файлами: {json_input_dir}")
    print(f"📁 Папка с DOCX/RTF файлами: {words_input_dir}")
    if args.use_word_reader:
        print("🔧 Используется word_reader для конвертации")
    print(f"🔗 URL: {url}")
    print("Для остановки: Ctrl+C")
    # По умолчанию debug=True для удобства разработки
    # Можно отключить через --no-debug для продакшена
    debug_mode = not args.no_debug
    if debug_mode:
        print("⚠️  Режим отладки включен (автоперезагрузка при изменении кода)")
    print("=" * 80 + "\n")
    
    try:
        app.run(host="127.0.0.1", port=args.port, debug=debug_mode)
    except KeyboardInterrupt:
        print("\n\nПриложение остановлено.")
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

