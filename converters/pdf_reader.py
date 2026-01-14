#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdf_reader.py

Модуль для чтения PDF файлов статей и извлечения текста.
Поддерживает настройку количества первых и последних страниц для обработки.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union
import re

# Попытка импорта библиотек для работы с PDF
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


# =========================
# Exceptions
# =========================

class PDFReaderError(Exception):
    """Базовый класс ошибок чтения PDF документов."""


class DependencyError(PDFReaderError):
    """Отсутствует зависимость для работы с PDF."""


class FormatError(PDFReaderError):
    """Неподдерживаемый формат файла."""


# =========================
# Data Structures
# =========================

@dataclass(frozen=True)
class PDFTextBlock:
    """Блок текста из PDF с информацией о странице."""
    text: str
    page_number: int
    block_type: str = "text"  # text, header, footer, etc.
    order: int = 0


@dataclass(frozen=True)
class PDFReaderConfig:
    """Конфигурация для чтения PDF."""
    first_pages: int = 3
    last_pages: int = 3
    extract_all_pages: bool = False
    clean_text: bool = True


# =========================
# Helper Functions
# =========================

def _require_pypdf2():
    """Проверяет наличие PyPDF2."""
    if not PYPDF2_AVAILABLE:
        raise DependencyError("PyPDF2 не установлен. Установите: pip install PyPDF2")


def _require_pdfplumber():
    """Проверяет наличие pdfplumber."""
    if not PDFPLUMBER_AVAILABLE:
        raise DependencyError("pdfplumber не установлен. Установите: pip install pdfplumber")


def _ensure_file(path: Union[str, Path]) -> Path:
    """Проверяет существование файла и возвращает Path."""
    p = Path(path)
    if not p.exists():
        raise PDFReaderError(f"Файл не найден: {p}")
    if not p.is_file():
        raise PDFReaderError(f"Путь не является файлом: {p}")
    return p


def _clean_text(text: str) -> str:
    """Очищает текст от лишних пробелов и символов."""
    if not text:
        return ""
    
    # Заменяем множественные пробелы на один
    text = re.sub(r'\s+', ' ', text)
    
    # Убираем пробелы в начале и конце строк
    text = text.strip()
    
    return text


def _normalize_block_text(text: str, clean: bool = True) -> str:
    """Нормализует текст блока."""
    if not text:
        return ""
    
    if clean:
        text = _clean_text(text)
    
    return text


# =========================
# PDF Reading with PyPDF2
# =========================

def read_pdf_with_pypdf2(
    path: Union[str, Path],
    config: PDFReaderConfig = PDFReaderConfig()
) -> List[PDFTextBlock]:
    """
    Читает PDF используя PyPDF2.
    
    Args:
        path: Путь к PDF файлу
        config: Конфигурация чтения
        
    Returns:
        Список блоков текста из PDF
    """
    _require_pypdf2()
    p = _ensure_file(path)
    
    blocks: List[PDFTextBlock] = []
    order = 0
    
    try:
        with open(p, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            if total_pages == 0:
                raise PDFReaderError(f"PDF файл не содержит страниц: {p}")
            
            # Определяем диапазон страниц для обработки
            if config.extract_all_pages:
                pages_to_process = list(range(total_pages))
            else:
                pages_to_process = []
                
                # Первые страницы
                first_end = min(config.first_pages, total_pages)
                pages_to_process.extend(range(first_end))
                
                # Последние страницы (если они не пересекаются с первыми)
                if config.last_pages > 0:
                    last_start = max(config.first_pages, total_pages - config.last_pages)
                    # Добавляем последние страницы, исключая те, что уже добавлены
                    for page_num in range(last_start, total_pages):
                        if page_num not in pages_to_process:
                            pages_to_process.append(page_num)
                
                # Сортируем для правильного порядка обработки
                pages_to_process = sorted(set(pages_to_process))
            
            # Извлекаем текст со страниц
            for page_num in pages_to_process:
                try:
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    
                    if text:
                        text = _normalize_block_text(text, clean=config.clean_text)
                        if text:
                            blocks.append(PDFTextBlock(
                                text=text,
                                page_number=page_num + 1,  # Нумерация с 1
                                block_type="text",
                                order=order
                            ))
                            order += 1
                except Exception as e:
                    # Пропускаем страницы с ошибками, но продолжаем обработку
                    continue
            
            return blocks
            
    except PDFReaderError:
        raise
    except Exception as e:
        raise PDFReaderError(f"Ошибка чтения PDF: {e}") from e


# =========================
# PDF Reading with pdfplumber
# =========================

def read_pdf_with_pdfplumber(
    path: Union[str, Path],
    config: PDFReaderConfig = PDFReaderConfig()
) -> List[PDFTextBlock]:
    """
    Читает PDF используя pdfplumber (более точное извлечение текста).
    
    Args:
        path: Путь к PDF файлу
        config: Конфигурация чтения
        
    Returns:
        Список блоков текста из PDF
    """
    _require_pdfplumber()
    p = _ensure_file(path)
    
    blocks: List[PDFTextBlock] = []
    order = 0
    
    try:
        with pdfplumber.open(p) as pdf:
            total_pages = len(pdf.pages)
            
            if total_pages == 0:
                raise PDFReaderError(f"PDF файл не содержит страниц: {p}")
            
            # Определяем диапазон страниц для обработки
            if config.extract_all_pages:
                pages_to_process = list(range(total_pages))
            else:
                pages_to_process = []
                
                # Первые страницы
                first_end = min(config.first_pages, total_pages)
                pages_to_process.extend(range(first_end))
                
                # Последние страницы (если они не пересекаются с первыми)
                if config.last_pages > 0:
                    last_start = max(config.first_pages, total_pages - config.last_pages)
                    # Добавляем последние страницы, исключая те, что уже добавлены
                    for page_num in range(last_start, total_pages):
                        if page_num not in pages_to_process:
                            pages_to_process.append(page_num)
                
                # Сортируем для правильного порядка обработки
                pages_to_process = sorted(set(pages_to_process))
            
            # Извлекаем текст со страниц
            for page_num in pages_to_process:
                try:
                    page = pdf.pages[page_num]
                    text = page.extract_text()
                    
                    if text:
                        text = _normalize_block_text(text, clean=config.clean_text)
                        if text:
                            blocks.append(PDFTextBlock(
                                text=text,
                                page_number=page_num + 1,  # Нумерация с 1
                                block_type="text",
                                order=order
                            ))
                            order += 1
                except Exception as e:
                    # Пропускаем страницы с ошибками, но продолжаем обработку
                    continue
            
            return blocks
            
    except PDFReaderError:
        raise
    except Exception as e:
        raise PDFReaderError(f"Ошибка чтения PDF: {e}") from e


# =========================
# Unified API
# =========================

def read_pdf_blocks(
    path: Union[str, Path],
    config: Optional[PDFReaderConfig] = None,
    prefer_pdfplumber: bool = True
) -> List[PDFTextBlock]:
    """
    Универсальное чтение PDF -> PDFTextBlock[].
    
    Args:
        path: Путь к PDF файлу
        config: Конфигурация чтения. Если None, используется конфигурация из config.py или по умолчанию.
        prefer_pdfplumber: Предпочитать pdfplumber над PyPDF2 (более точное извлечение)
        
    Returns:
        Список блоков текста из PDF
    """
    if config is None:
        # Пытаемся загрузить конфигурацию из config.py
        try:
            from config import get_config
            cfg = get_config()
            config = PDFReaderConfig(
                first_pages=cfg.get("pdf_reader.first_pages", 3),
                last_pages=cfg.get("pdf_reader.last_pages", 3),
                extract_all_pages=cfg.get("pdf_reader.extract_all_pages", False),
                clean_text=cfg.get("pdf_reader.clean_text", True),
            )
        except ImportError:
            # Если config.py недоступен, используем значения по умолчанию
            config = PDFReaderConfig()
    
    p = _ensure_file(path)
    
    # Проверяем расширение файла
    if p.suffix.lower() != ".pdf":
        raise FormatError(f"Ожидается PDF файл, получен: {p.suffix}")
    
    # Пробуем использовать pdfplumber, если доступен и предпочтителен
    if prefer_pdfplumber and PDFPLUMBER_AVAILABLE:
        try:
            return read_pdf_with_pdfplumber(p, config)
        except Exception as e:
            # Если pdfplumber не сработал, пробуем PyPDF2
            if PYPDF2_AVAILABLE:
                return read_pdf_with_pypdf2(p, config)
            raise PDFReaderError(f"Ошибка чтения PDF с pdfplumber: {e}") from e
    
    # Используем PyPDF2, если доступен
    if PYPDF2_AVAILABLE:
        return read_pdf_with_pypdf2(p, config)
    
    # Если ни одна библиотека не доступна
    raise DependencyError(
        "Не установлена ни одна библиотека для работы с PDF. "
        "Установите одну из: pip install PyPDF2 или pip install pdfplumber"
    )


def read_pdf_text(
    path: Union[str, Path],
    config: Optional[PDFReaderConfig] = None,
    prefer_pdfplumber: bool = True
) -> str:
    """
    Читает PDF и возвращает весь текст как одну строку.
    
    Args:
        path: Путь к PDF файлу
        config: Конфигурация чтения
        prefer_pdfplumber: Предпочитать pdfplumber над PyPDF2
        
    Returns:
        Текст из PDF как строка
    """
    blocks = read_pdf_blocks(path, config, prefer_pdfplumber)
    return "\n\n".join(block.text for block in blocks)


def read_pdf_lines(
    path: Union[str, Path],
    config: Optional[PDFReaderConfig] = None,
    prefer_pdfplumber: bool = True
) -> List[str]:
    """
    Читает PDF и возвращает список строк.
    
    Args:
        path: Путь к PDF файлу
        config: Конфигурация чтения
        prefer_pdfplumber: Предпочитать pdfplumber над PyPDF2
        
    Returns:
        Список строк из PDF
    """
    blocks = read_pdf_blocks(path, config, prefer_pdfplumber)
    lines = []
    for block in blocks:
        # Разбиваем блок на строки
        block_lines = block.text.split('\n')
        lines.extend(line.strip() for line in block_lines if line.strip())
    return lines


# =========================
# CLI / Testing
# =========================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Использование: python converters/pdf_reader.py <путь_к_pdf> [first_pages] [last_pages]")
        print("Пример: python converters/pdf_reader.py article.pdf 3 3")
        sys.exit(1)
    
    pdf_path = Path(sys.argv[1])
    first_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    last_pages = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    
    config = PDFReaderConfig(
        first_pages=first_pages,
        last_pages=last_pages,
        extract_all_pages=False,
        clean_text=True
    )
    
    try:
        print(f"Чтение PDF: {pdf_path}")
        print(f"Первые страницы: {first_pages}, Последние страницы: {last_pages}\n")
        
        blocks = read_pdf_blocks(pdf_path, config)
        
        print(f"Извлечено блоков: {len(blocks)}\n")
        print("=" * 80)
        
        for block in blocks:
            print(f"\n[Страница {block.page_number}]")
            print("-" * 80)
            print(block.text[:500])  # Показываем первые 500 символов
            if len(block.text) > 500:
                print("...")
        
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)

