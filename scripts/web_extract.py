"""
Веб-интерфейс для интерактивного извлечения метаданных из Word/RTF документов.
Открывает файл в браузере; пользователь кликом выделяет строки и назначает их полям.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import webbrowser
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from flask import Flask, jsonify, render_template_string, request

try:
    from text_utils import merge_doi_url_with_references
except ImportError:
    # Запасной вариант, если text_utils недоступен
    def merge_doi_url_with_references(references: List[str]) -> List[str]:
        return references

# ----------------------------
# Константы и структуры данных
# ----------------------------

SUPPORTED_EXTENSIONS = {".docx", ".rtf"}

METADATA_FIELDS: Sequence[str] = (
    "title",
    "title_en",
    "doi",
    "annotation",
    "annotation_en",
    "keywords",
    "keywords_en",
    "references_ru",
    "references_en",
    "year",
    "issue",
    "article_number",
    "url",
    "url_en",
    "pages",
    "udc",
    "received_date",
    "reviewed_date",
    "accepted_date",
    "funding",
)

LIST_FIELDS = {"references_ru", "references_en"}  # список строк
INT_FIELDS = {"year"}  # целые числа


@dataclass(frozen=True)
class TextLine:
    id: int
    text: str
    line_number: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class UserError(RuntimeError):
    """Ошибки, которые стоит показывать пользователю/в консоль кратко."""


# ----------------------------
# Чтение файлов
# ----------------------------

def clean_text(text: str) -> str:
    """
    Очищает текст от табуляций и разрывов строк.
    Заменяет табуляции и множественные пробелы на один пробел.
    """
    if not text:
        return ""
    # Заменяем табуляции на пробелы
    cleaned = text.replace("\t", " ")
    # Заменяем разрывы строк на пробелы
    cleaned = cleaned.replace("\n", " ").replace("\r", " ")
    # Заменяем множественные пробелы на один
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    return cleaned.strip()


def _require_module(module_name: str, pip_hint: str) -> Any:
    try:
        return __import__(module_name, fromlist=["*"])
    except Exception as e:
        raise UserError(f"Не найден модуль '{module_name}'. Установите: {pip_hint}") from e


def read_docx_lines(file_path: Path) -> List[TextLine]:
    docx = _require_module("docx", "pip install python-docx")
    Document = docx.Document

    try:
        doc = Document(str(file_path))
    except Exception as e:
        raise UserError(f"Ошибка при чтении DOCX: {e}") from e

    lines: List[TextLine] = []
    idx = 1
    for i, p in enumerate(doc.paragraphs):
        # Получаем исходный текст
        txt = p.text or ""
        # Убираем только начальные и конечные пробелы
        txt = txt.strip()
        if not txt:
            # Отладочный вывод для пустых строк
            if i < 3:
                print(f"DEBUG DOCX: Строка {i+1} пустая после strip")
            continue
        # Отладочный вывод для первых строк
        if i < 3:
            print(f"DEBUG DOCX: Строка {i+1} до очистки: '{txt[:50]}...'")
        # Очищаем текст от табуляций и разрывов строк
        cleaned_txt = clean_text(txt)
        # Если после очистки текст стал пустым, но исходный был не пустым, используем исходный
        if not cleaned_txt and txt:
            cleaned_txt = txt
        # Проверяем, что после очистки остался текст (не только пробелы)
        if cleaned_txt and cleaned_txt.strip():
            if i < 3:
                print(f"DEBUG DOCX: Строка {i+1} после очистки: '{cleaned_txt[:50]}...'")
            lines.append(TextLine(id=idx, text=cleaned_txt, line_number=idx))
            idx += 1
        elif i < 3:
            print(f"DEBUG DOCX: Строка {i+1} отфильтрована после очистки")

    print(f"DEBUG DOCX: Всего строк добавлено: {len(lines)}")
    return lines


def read_rtf_lines(file_path: Path) -> List[TextLine]:
    striprtf = _require_module("striprtf.striprtf", "pip install striprtf")

    encodings = ("utf-8", "cp1251", "windows-1251", "latin-1")
    content: Optional[str] = None

    for enc in encodings:
        try:
            content = file_path.read_text(encoding=enc, errors="ignore")
            if content:
                print(f"DEBUG RTF: Файл прочитан с кодировкой {enc}, размер: {len(content)} байт")
                break
        except Exception:
            continue

    if not content:
        raise UserError("Не удалось прочитать RTF (пустой или неизвестная кодировка).")

    # Отладочный вывод: ищем название в исходном RTF
    if "ТОПОЛОГИЧЕСКАЯ" in content or "ОПТИМИЗАЦИЯ" in content:
        print("DEBUG RTF: Название найдено в исходном RTF контенте!")
        # Ищем контекст вокруг названия
        idx = content.find("ТОПОЛОГИЧЕСКАЯ")
        if idx == -1:
            idx = content.find("ОПТИМИЗАЦИЯ")
        if idx != -1:
            print(f"DEBUG RTF: Контекст вокруг названия (позиция {idx}): {content[max(0, idx-50):idx+200]}")
    else:
        print("DEBUG RTF: Название НЕ найдено в исходном RTF контенте!")

    try:
        plain = striprtf.rtf_to_text(content)
        print(f"DEBUG RTF: После rtf_to_text размер: {len(plain)} символов")
    except Exception as e:
        raise UserError(f"Ошибка при разборе RTF: {e}") from e

    # Отладочный вывод: проверяем, есть ли название в plain тексте
    if "ТОПОЛОГИЧЕСКАЯ" in plain or "ОПТИМИЗАЦИЯ" in plain:
        print("DEBUG RTF: Название найдено в plain тексте после rtf_to_text!")
        idx = plain.find("ТОПОЛОГИЧЕСКАЯ")
        if idx == -1:
            idx = plain.find("ОПТИМИЗАЦИЯ")
        if idx != -1:
            print(f"DEBUG RTF: Контекст в plain тексте (позиция {idx}): {plain[max(0, idx-50):idx+200]}")
    else:
        print("DEBUG RTF: Название НЕ найдено в plain тексте после rtf_to_text!")

    # Отладочный вывод: первые 500 символов исходного текста
    print(f"DEBUG RTF: Первые 500 символов plain текста:\n{plain[:500]}")
    
    # Разбиваем на строки, сохраняя первую строку даже если она пустая после strip
    raw_lines = plain.splitlines()
    print(f"DEBUG RTF: Всего raw_lines после splitlines: {len(raw_lines)}")
    print(f"DEBUG RTF: Первые 15 raw_lines:")
    for i, raw_line in enumerate(raw_lines[:15], 1):
        print(f"  Raw {i}: '{raw_line[:100]}...' (len={len(raw_line)}, strip_len={len(raw_line.strip())})")
    
    lines: List[TextLine] = []
    idx = 1
    for i, txt in enumerate(raw_lines):
        # Убираем только начальные и конечные пробелы
        original_raw = txt
        txt = txt.strip()
        if not txt:
            if i < 15:
                print(f"DEBUG RTF: Строка {i+1} пропущена (пустая после strip): '{original_raw[:50]}...'")
            continue
        # Очищаем текст от табуляций и разрывов строк
        cleaned_txt = clean_text(txt)
        # Если после очистки текст стал пустым, но исходный был не пустым, используем исходный
        if not cleaned_txt and txt:
            cleaned_txt = txt
        # Проверяем, что после очистки остался текст (не только пробелы)
        if cleaned_txt and cleaned_txt.strip():
            # Отладочный вывод для строк, содержащих название
            if "ТОПОЛОГИЧЕСКАЯ" in cleaned_txt or "ОПТИМИЗАЦИЯ" in cleaned_txt:
                print(f"DEBUG RTF: НАЙДЕНО! Строка {idx} содержит название: '{cleaned_txt}'")
            if i < 15:
                print(f"DEBUG RTF: Строка {i+1} -> добавлена как строка {idx}: '{cleaned_txt[:80]}...'")
            lines.append(TextLine(id=idx, text=cleaned_txt, line_number=idx))
            idx += 1
        elif i < 15:
            print(f"DEBUG RTF: Строка {i+1} отфильтрована: '{txt[:80]}...' -> '{cleaned_txt[:80]}...'")
    
    print(f"DEBUG RTF: Итого строк добавлено: {len(lines)}")
    return lines


def merge_doi_url_in_lines(lines: List[TextLine]) -> List[TextLine]:
    """
    Объединяет строки с DOI/URL с предыдущими строками в списке TextLine.
    
    Если строка начинается с http и содержит doi.org, она объединяется
    с предыдущей строкой через пробел.
    """
    if not lines:
        return lines
    
    result: List[TextLine] = []
    
    for line in lines:
        line_text = line.text.strip()
        if not line_text:
            continue
        
        # Проверяем, является ли строка DOI/URL
        line_lower = line_text.lower()
        is_doi_url = (
            line_text.startswith("http") and 
            ("doi.org" in line_lower or "dx.doi.org" in line_lower)
        )
        
        # Если это DOI/URL и есть предыдущая строка, объединяем
        if is_doi_url and result:
            # Объединяем текст с предыдущей строкой
            result[-1] = TextLine(
                id=result[-1].id,
                text=result[-1].text + " " + line_text,
                line_number=result[-1].line_number
            )
        else:
            # Добавляем как новую строку
            result.append(line)
    
    return result


def extract_text_lines(file_path: Path) -> List[TextLine]:
    suffix = file_path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise UserError(f"Неподдерживаемый формат: {suffix}. Поддерживаются: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")

    if suffix == ".docx":
        lines = read_docx_lines(file_path)
    elif suffix == ".rtf":
        lines = read_rtf_lines(file_path)
    else:
        # на будущее
        raise UserError(f"Неподдерживаемый формат: {suffix}")
    
    # Объединяем строки с DOI/URL с предыдущими строками
    lines = merge_doi_url_in_lines(lines)
    
    return lines


# ----------------------------
# Нормализация/валидация метаданных
# ----------------------------

def build_metadata(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Приводит JSON из браузера к ожидаемой структуре:
    - гарантирует наличие всех ключей;
    - list-поля всегда список строк;
    - int-поля старается привести к int.
    """
    out: Dict[str, Any] = {}

    for key in METADATA_FIELDS:
        if key in LIST_FIELDS:
            v = payload.get(key, [])
            if v is None:
                out[key] = []
            elif isinstance(v, list):
                refs = [str(x).strip() for x in v if str(x).strip()]
            elif isinstance(v, str):
                refs = [s.strip() for s in v.splitlines() if s.strip()]
            else:
                refs = [str(v).strip()] if str(v).strip() else []
            
            # Объединяем DOI/URL с предыдущими источниками для списка литературы
            if key in {"references_ru", "references_en"}:
                out[key] = merge_doi_url_with_references(refs)
            else:
                out[key] = refs
            continue

        if key in INT_FIELDS:
            v = payload.get(key)
            if v in (None, "", []):
                out[key] = None
            else:
                try:
                    out[key] = int(v)
                except Exception:
                    out[key] = v  # оставим как есть
            continue

        # обычные строки/nullable
        v = payload.get(key)
        if v is None or v == "":
            out[key] = None
        else:
            out[key] = str(v)

    return out


# ----------------------------
# Веб-приложение
# ----------------------------

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Извлечение метаданных - {{ filename }}</title>
  <style>
    *{margin:0;padding:0;box-sizing:border-box;}
    body{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:#f5f5f5;padding:20px;}
    .container{max-width:1400px;margin:0 auto;background:white;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1);overflow:hidden;}
    .header{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;padding:20px;text-align:center;}
    .header h1{font-size:24px;margin-bottom:5px;}
    .header p{opacity:.9;}
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
  </style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Извлечение метаданных</h1>
    <p>{{ filename }}</p>
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
          <small style="color:#666;font-size:12px;">Каждая ссылка с новой строки</small>
        </div>

        <div class="field-group">
          <label>Список литературы (английский)</label>
          <textarea id="references_en" name="references_en" rows="5"></textarea>
          <div class="selected-lines" id="references_en-lines"></div>
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

<script>
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
    
    // Различные форматы дат: DD.MM.YYYY, DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY
    const datePatterns = [
      /\b(\d{1,2}[./]\d{1,2}[./]\d{4})\b/,           // DD.MM.YYYY или DD/MM/YYYY
      /\b(\d{4}[-./]\d{1,2}[-./]\d{1,2})\b/,         // YYYY-MM-DD или YYYY.MM.DD
      /\b(\d{1,2}[-]\d{1,2}[-]\d{4})\b/,             // DD-MM-YYYY
    ];
    
    for (const pattern of datePatterns) {
      const match = text.match(pattern);
      if (match) {
        // Нормализуем формат: заменяем / и - на .
        let date = match[1].replace(/[\/-]/g, '.');
        // Если формат YYYY.MM.DD, переводим в DD.MM.YYYY
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
    
    // УДК обычно имеет формат: "УДК 621.3" или "621.3" или "УДК: 621.3"
    // Паттерн для поиска кода УДК (числа с точками, возможно с дефисами)
    const udcPatterns = [
      /(?:УДК|UDC)\s*:?\s*([0-9.]+(?:[-–—][0-9.]+)?)/i,  // "УДК 621.3" или "УДК: 621.3"
      /\b([0-9]{1,3}(?:\.[0-9]+)*(?:[-–—][0-9.]+)?)\b/,   // Просто код "621.3" или "621.3-5"
    ];
    
    for (const pattern of udcPatterns) {
      const match = text.match(pattern);
      if (match) {
        return match[1].trim();
      }
    }
    
    return null;
  }

  function extractYear(text) {
    if (!text) return null;
    
    // Ищем 4-значный год в диапазоне 1900-2100
    const yearPattern = /\b(19\d{2}|20\d{2})\b/;
    const match = text.match(yearPattern);
    
    if (match) {
      const year = parseInt(match[1], 10);
      // Проверяем, что год в разумном диапазоне
      if (year >= 1900 && year <= 2100) {
        return String(year);
      }
    }
    
    return null;
  }

  function processKeywords(text) {
    if (!text) return "";
    let cleaned = text
      .replace(/^(Keywords|Ключевые слова)\s*:?\s*/i, "")
      .trim();
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
    // Удаляем префиксы "Финансирование", "Funding" и их варианты с двоеточием и точкой
    let cleaned = text
      .replace(/^(Финансирование|Funding)\s*[.:]?\s*/i, "")
      .replace(/^(Финансирование|Funding)\s*/i, "")
      .trim();
    return cleaned;
  }

  function processReferences(texts) {
    // Каждая выделенная строка становится отдельным элементом массива
    const processed = [];
    
    texts.forEach(text => {
      // Очищаем строку: убираем номера в начале, табуляции, лишние пробелы
      let cleaned = String(text)
        .replace(/^\d+\s+/, "")  // Убираем номер в начале строки (123 ...)
        .replace(/\t/g, " ")      // Заменяем табуляции на пробелы
        .replace(/\s+/g, " ")     // Множественные пробелы в один
        .trim();
      
      if (!cleaned) return;
      
      // Если строка содержит URL или DOI, добавляем её к предыдущей (если есть)
      // Паттерны: https://, http://, doi.org/, doi:, http://dx.doi.org/
      const isUrl = /^(https?:\/\/|doi\.org\/|doi:\s*|http:\/\/dx\.doi\.org\/)/i.test(cleaned);
      if (isUrl && processed.length > 0) {
        // Добавляем URL к последней ссылке
        processed[processed.length - 1] += " " + cleaned;
      } else {
        // Каждая строка - отдельный источник
        processed.push(cleaned);
      }
    });
    
    return processed.filter(Boolean);
  }
  
  function mergeDoiUrlWithReferences(refs) {
    // Объединяет строки с DOI/URL с предыдущими источниками
    if (!refs || refs.length === 0) return refs;
    
    const result = [];
    const doiUrlPattern = /^(https?:\/\/|doi\.org\/|doi:\s*|http:\/\/dx\.doi\.org\/)/i;
    
    refs.forEach(ref => {
      const cleaned = String(ref).trim();
      if (!cleaned) return;
      
      // Если строка начинается с DOI/URL и есть предыдущая строка
      if (doiUrlPattern.test(cleaned) && result.length > 0) {
        // Объединяем с предыдущей строкой
        result[result.length - 1] += " " + cleaned;
      } else {
        // Добавляем как новую строку
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
      value = field.value.trim() ? (processKeywords(field.value) + "; " + kw) : kw;
    } else if (fieldId === "references_ru" || fieldId === "references_en") {
      const refs = processReferences(texts);
      if (field.value.trim()) {
        const existing = field.value.split("\n").map(s => s.trim()).filter(Boolean);
        value = existing.concat(refs).join("\n");
      } else {
        value = refs.join("\n");
      }
    } else if (fieldId === "received_date" || fieldId === "reviewed_date" || fieldId === "accepted_date") {
      // Для полей дат извлекаем только дату без дополнительного текста
      const date = extractDate(fullText);
      if (date) {
        value = date;
      } else {
        alert("Дата не найдена в выделенном тексте. Ожидается формат: DD.MM.YYYY, DD/MM/YYYY или YYYY-MM-DD");
        return;
      }
    } else if (fieldId === "udc") {
      // Для поля УДК извлекаем только код УДК
      const udc = extractUDC(fullText);
      if (udc) {
        value = udc;
      } else {
        // Если не найден код, используем весь текст (может быть пользователь хочет ввести вручную)
        value = fullText.trim();
      }
    } else if (fieldId === "funding") {
      // Для поля финансирования удаляем префиксы "Финансирование", "Funding"
      const funding = processFunding(fullText);
      if (field.value.trim()) {
        // Если поле уже содержит текст, добавляем через пробел
        value = field.value.trim() + " " + funding;
      } else {
        value = funding;
      }
    } else if (fieldId === "year") {
      // Для поля года извлекаем только год (4-значное число)
      const year = extractYear(fullText);
      if (year) {
        value = year;
      } else {
        alert("Год не найден в выделенном тексте. Ожидается 4-значный год (например, 2025)");
        return;
      }
    } else {
      value = field.value.trim() ? (field.value.trim() + " " + fullText) : fullText;
    }

    field.value = value;
    field.focus();

    setLinesInfo(fieldId, selected.size);
    markField(fieldId);
    clearSelection();
  }

  // Делегирование кликов по строкам
  document.addEventListener("DOMContentLoaded", () => {
    const textContent = $("#textContent");
    if (textContent) {
      textContent.addEventListener("click", (e) => {
        const line = e.target.closest(".line");
        if (!line) return;

        const id = line.dataset.id;
        if (!id) return;

        if (selected.has(id)) {
          selected.delete(id);
          line.classList.remove("selected");
        } else {
          selected.add(id);
          line.classList.add("selected");
        }
        updatePanel();
      });
    }

    // Активное поле — по фокусу
    document.addEventListener("focusin", (e) => {
      const el = e.target;
      if (!el) return;
      if ((el.tagName === "INPUT" || el.tagName === "TEXTAREA") && el.id) {
        currentFieldId = el.id;
      }
    });

    // Кнопка очистки
    const clearBtn = $("#clearBtn");
    if (clearBtn) clearBtn.addEventListener("click", clearSelection);

    // Кнопки панели назначения
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

    // Поиск
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

    // Submit формы
    const form = $("#metadataForm");
    if (form) {
      form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const fd = new FormData(form);
        const data = {};
        for (const [k, v] of fd.entries()) data[k] = v;

        // Списки литературы - объединяем DOI/URL с предыдущими источниками
        ["references_ru", "references_en"].forEach((k) => {
          if (data[k]) {
            const refs = String(data[k]).split("\n").map(s => s.trim()).filter(Boolean);
            data[k] = mergeDoiUrlWithReferences(refs);
          }
        });

        try {
          const resp = await fetch("/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
          });
          const result = await resp.json();
          if (result.success) {
            alert("Метаданные успешно сохранены!\nФайл: " + result.filename);
            window.close();
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


def create_app(file_path: Path, output_path: Path) -> Flask:
    lines = extract_text_lines(file_path)
    if not lines:
        raise UserError("Не удалось извлечь текст: документ пуст или не распознан.")

    app = Flask(__name__)

    @app.get("/")
    def index():
        # Отладочный вывод: проверяем количество строк и первые строки
        lines_dict = [ln.to_dict() for ln in lines]
        print(f"DEBUG: Всего строк извлечено: {len(lines_dict)}")
        if lines_dict:
            print(f"DEBUG: Первая строка: {lines_dict[0]}")
            print(f"DEBUG: Первые 3 строки: {lines_dict[:3]}")
            # Выводим строки с 4 по 10, чтобы найти название
            if len(lines_dict) >= 10:
                print(f"DEBUG: Строки 4-10:")
                for i, line in enumerate(lines_dict[3:10], start=4):
                    print(f"  Строка {i}: {line['text'][:80]}...")
            elif len(lines_dict) > 3:
                print(f"DEBUG: Строки 4-{len(lines_dict)}:")
                for i, line in enumerate(lines_dict[3:], start=4):
                    print(f"  Строка {i}: {line['text'][:80]}...")
        else:
            print("DEBUG: ВНИМАНИЕ! Строки не извлечены!")
        
        return render_template_string(
            HTML_TEMPLATE,
            filename=file_path.name,
            lines=lines_dict,
        )

    @app.post("/save")
    def save():
        try:
            payload = request.get_json(force=True, silent=False)
            if not isinstance(payload, dict):
                return jsonify(success=False, error="Ожидался JSON-объект."), 400

            metadata = build_metadata(payload)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

            return jsonify(success=True, filename=str(output_path))
        except Exception as e:
            return jsonify(success=False, error=str(e)), 500

    return app


# ----------------------------
# CLI / запуск
# ----------------------------

def pick_file_from_dir(dir_path: Path) -> Path:
    files = [p for p in dir_path.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS]
    if not files:
        raise UserError(f"В папке {dir_path.name}/ не найдено файлов ({', '.join(sorted(SUPPORTED_EXTENSIONS))}).")

    print(f"\nНайдено файлов в {dir_path.name}/:")
    for i, p in enumerate(files, 1):
        print(f"  {i}. {p.name}")

    try:
        choice = input(f"\nВыберите файл (1-{len(files)}): ").strip()
        n = int(choice)
        if not (1 <= n <= len(files)):
            raise UserError("Неверный номер.")
        return files[n - 1]
    except KeyboardInterrupt:
        raise UserError("Прервано пользователем.")
    except ValueError:
        raise UserError("Неверный ввод (ожидалось число).")


def open_browser_later(url: str, delay_sec: float = 1.2) -> None:
    def _open():
        time.sleep(delay_sec)
        webbrowser.open(url)

    threading.Thread(target=_open, daemon=True).start()


def main() -> int:
    parser = argparse.ArgumentParser(description="Веб-интерфейс для извлечения метаданных из Word/RTF документов")
    parser.add_argument("input_file", nargs="?", default=None, help="Путь к .docx/.rtf файлу")
    parser.add_argument("-o", "--output", default=None, help="Путь к выходному JSON файлу")
    parser.add_argument("--port", type=int, default=5000, help="Порт (по умолчанию: 5000)")
    args = parser.parse_args()

    script_dir = Path(__file__).parent.resolve()
    default_input_dir = script_dir / "words_input"

    # Входной файл
    if args.input_file is None:
        if not default_input_dir.exists():
            raise UserError("Не указан файл и не найдена папка words_input рядом со скриптом.")
        input_path = pick_file_from_dir(default_input_dir)
    else:
        input_path = Path(args.input_file)
        if not input_path.is_absolute():
            input_path = script_dir / input_path

    if not input_path.exists():
        raise UserError(f"Файл не существует: {input_path}")

    # Выходной файл
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = script_dir / output_path
    else:
        output_path = script_dir / "output" / f"{input_path.stem}_metadata.json"

    app = create_app(input_path, output_path)

    url = f"http://127.0.0.1:{args.port}/"
    open_browser_later(url)

    print("\n" + "=" * 80)
    print("Веб-интерфейс запущен!")
    print(f"Файл: {input_path.name}")
    print(f"Откройте в браузере: {url}")
    print("Для остановки: Ctrl+C")
    print("=" * 80 + "\n")

    app.run(host="127.0.0.1", port=args.port, debug=False)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except UserError as e:
        print(f"Ошибка: {e}")
        raise SystemExit(1)
