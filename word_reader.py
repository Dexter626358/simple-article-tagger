#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
word_reader.py

Низкоуровневый Reader для DOCX/RTF.

Цель:
- извлечь текст максимально полно (как он хранится),
- сохранить границы абзацев/строк,
- не применять "умных" склеек заголовков и т.п.

Поддержка:
- .docx (через чтение XML частей DOCX как zip)
  - document.xml
  - header*.xml, footer*.xml
  - footnotes.xml, endnotes.xml
- .rtf (striprtf)

Возвращает:
- List[TextBlock] — структурированные блоки (абзацы/строки) с источником.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Union, Literal
import zipfile
import xml.etree.ElementTree as ET
import re


# =========================
# Exceptions
# =========================

class WordReaderError(Exception):
    """Базовый класс ошибок чтения документов."""


class DependencyError(WordReaderError):
    """Отсутствует зависимость."""


class FormatError(WordReaderError):
    """Неподдерживаемый формат."""


class FileAccessError(WordReaderError):
    """Ошибка доступа к файлу."""


# =========================
# Types / Models
# =========================

BlockType = Literal["paragraph", "line"]

@dataclass(frozen=True)
class TextBlock:
    """
    Единица текста "как хранится":
    - для DOCX: абзац (paragraph) из XML
    - для RTF: строка (line) из plain text
    """
    text: str
    source: str              # например: word/document.xml, rtf
    block_type: BlockType    # paragraph / line
    order: int               # порядок извлечения


@dataclass(frozen=True)
class ReaderConfig:
    clean: bool = True
    rtf_encodings: Sequence[str] = ("utf-8", "cp1251", "windows-1251", "latin-1")


SUPPORTED_EXTENSIONS = (".docx", ".rtf")

W_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


# =========================
# External utils
# =========================
try:
    from text_utils import clean_text  # ваш утилитный модуль
except Exception:  # pragma: no cover
    def clean_text(s: str) -> str:
        # запасной вариант, чтобы модуль не падал при импорте
        return re.sub(r"\s+", " ", s).strip()


# =========================
# Helpers
# =========================

def _ensure_file(path: Union[str, Path]) -> Path:
    p = Path(path)
    if not p.exists():
        raise FileAccessError(f"Файл не найден: {p}")
    if not p.is_file():
        raise FileAccessError(f"Указанный путь не является файлом: {p}")
    return p


def _ensure_supported_extension(p: Path) -> str:
    ext = p.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise FormatError(
            f"Неподдерживаемый формат: {ext}. Поддерживаются: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    return ext


def is_supported_format(path: Union[str, Path]) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS


def check_dependencies() -> dict:
    docx_ok = True
    rtf_ok = True
    # docx — zip+xml, без внешних зависимостей
    # rtf — striprtf
    try:
        _require_striprtf()
    except DependencyError:
        rtf_ok = False
    return {"docx": docx_ok, "rtf": rtf_ok, "all_available": docx_ok and rtf_ok}


def _normalize_text(s: str) -> str:
    """Нормализация невидимых символов, общая для RTF/DOCX."""
    if not s:
        return ""
    s = s.replace("\ufeff", "")   # BOM
    s = s.replace("\u00ad", "")   # soft hyphen
    s = s.replace("\u00a0", " ")  # NBSP
    # Не схлопываем все пробелы намертво — это делает clean_text (если включен).
    return s


def _normalize_block_text(s: str, clean: bool) -> str:
    s = _normalize_text(s)
    s = s.strip()
    if not s:
        return ""
    if clean:
        s = clean_text(s).strip()
    return s


def _is_service_block(block: TextBlock) -> bool:
    """
    Проверяет, является ли блок служебным.
    """
    try:
        from text_utils import is_service_line
        return is_service_line(block.text)
    except ImportError:
        # Простая проверка без text_utils
        text = block.text.strip()
        if not text or len(text) < 3:
            return True
        text_lower = text.lower()
        service_keywords = ['удк', 'udc', 'doi', 'e-mail', 'email', '@', '©', 'copyright']
        return any(keyword in text_lower for keyword in service_keywords)


# =========================
# DOCX reading via XML
# =========================

def _iter_docx_xml_parts(z: zipfile.ZipFile) -> List[str]:
    """
    Выбираем набор частей, где обычно бывает значимый текст.
    """
    names = z.namelist()
    parts = [
        n for n in names
        if n.startswith("word/")
        and n.endswith(".xml")
        and (
            n == "word/document.xml"
            or n.startswith("word/header")
            or n.startswith("word/footer")
            or n == "word/footnotes.xml"
            or n == "word/endnotes.xml"
        )
    ]
    # Сортировка даёт стабильность; приоритет можно корректировать при желании.
    return sorted(parts)


def _extract_paragraphs_from_word_xml(xml_bytes: bytes) -> List[str]:
    """
    Возвращает список абзацев из xml (w:p), собирая весь текст w:t внутри абзаца.

    Важно:
    - сохраняем границу абзаца как отдельный блок
    - не пытаемся реконструировать "страничный" порядок
    """
    root = ET.fromstring(xml_bytes)
    out: List[str] = []
    for p in root.findall(".//w:p", W_NS):
        texts = [t.text for t in p.findall(".//w:t", W_NS) if t.text]
        if not texts:
            continue
        paragraph = "".join(texts)
        out.append(paragraph)
    return out


def read_docx_blocks(path: Union[str, Path], config: ReaderConfig = ReaderConfig()) -> List[TextBlock]:
    """
    Читает DOCX и возвращает список TextBlock (paragraph).
    """
    p = _ensure_file(path)
    ext = _ensure_supported_extension(p)
    if ext != ".docx":
        raise FormatError(f"read_docx_blocks ожидает .docx, получен: {ext}")

    blocks: List[TextBlock] = []
    order = 0

    try:
        with zipfile.ZipFile(p, "r") as z:
            parts = _iter_docx_xml_parts(z)
            for part in parts:
                xml_bytes = z.read(part)
                paragraphs = _extract_paragraphs_from_word_xml(xml_bytes)
                for para in paragraphs:
                    text = _normalize_block_text(para, clean=config.clean)
                    if not text:
                        continue
                    blocks.append(TextBlock(text=text, source=part, block_type="paragraph", order=order))
                    order += 1
        return blocks
    except WordReaderError:
        raise
    except zipfile.BadZipFile as e:
        raise WordReaderError(f"Файл не является корректным DOCX (zip): {p}") from e
    except Exception as e:
        raise WordReaderError(f"Ошибка чтения DOCX: {e}") from e


# =========================
# RTF reading
# =========================

def _require_striprtf():
    try:
        import striprtf.striprtf as rtf  # type: ignore
    except ImportError as e:
        raise DependencyError("Библиотека striprtf не установлена. Установите: pip install striprtf") from e
    return rtf


def _read_text_with_fallback_encodings(p: Path, encodings: Sequence[str]) -> str:
    last_exc: Optional[Exception] = None
    for enc in encodings:
        try:
            content = p.read_text(encoding=enc, errors="ignore")
            if content:
                return content
        except Exception as e:
            last_exc = e
            continue
    if last_exc:
        raise FileAccessError(
            f"Не удалось прочитать RTF {p} с доступными кодировками. Последняя ошибка: {last_exc}"
        ) from last_exc
    raise FileAccessError(f"Не удалось прочитать RTF {p} с доступными кодировками.")


def read_rtf_blocks(path: Union[str, Path], config: ReaderConfig = ReaderConfig()) -> List[TextBlock]:
    """
    Читает RTF и возвращает список TextBlock (line).
    """
    p = _ensure_file(path)
    ext = _ensure_supported_extension(p)
    if ext != ".rtf":
        raise FormatError(f"read_rtf_blocks ожидает .rtf, получен: {ext}")

    rtf = _require_striprtf()
    content = _read_text_with_fallback_encodings(p, config.rtf_encodings)

    try:
        plain = rtf.rtf_to_text(content) or ""
    except Exception as e:
        raise WordReaderError(f"Ошибка разбора RTF: {e}") from e

    # нормализуем переносы
    plain = plain.replace("\r\n", "\n").replace("\r", "\n")
    lines = plain.split("\n")

    blocks: List[TextBlock] = []
    order = 0
    for line in lines:
        text = _normalize_block_text(line, clean=config.clean)
        if not text:
            continue
        blocks.append(TextBlock(text=text, source="rtf", block_type="line", order=order))
        order += 1

    return blocks


# =========================
# Unified API
# =========================

def read_blocks(path: Union[str, Path], *, clean: bool = True) -> List[TextBlock]:
    """
    Универсальное чтение DOCX/RTF -> TextBlock[].
    """
    cfg = ReaderConfig(clean=clean)
    p = _ensure_file(path)
    ext = _ensure_supported_extension(p)

    if ext == ".docx":
        return read_docx_blocks(p, cfg)
    return read_rtf_blocks(p, cfg)


def filter_service_blocks(blocks: List[TextBlock]) -> List[TextBlock]:
    """
    Фильтрует служебные блоки из списка.
    
    Args:
        blocks: Список блоков для фильтрации
        
    Returns:
        Отфильтрованный список блоков без служебных
    """
    return [b for b in blocks if not _is_service_block(b)]


def merge_doi_url_lines(lines: List[str]) -> List[str]:
    """
    Объединяет строки с DOI/URL с предыдущими строками.
    
    Если строка начинается с http и содержит doi.org, она объединяется
    с предыдущей строкой через пробел.
    
    Args:
        lines: Список строк
        
    Returns:
        Обработанный список, где DOI/URL прикреплены к предыдущим строкам
        
    Examples:
        >>> lines = [
        ...     "Polyanin A.D., Manzhirov A.V. Handbook...",
        ...     "https://doi.org/10.1201/9781420010558"
        ... ]
        >>> merge_doi_url_lines(lines)
        ['Polyanin A.D., Manzhirov A.V. Handbook... https://doi.org/10.1201/9781420010558']
    """
    if not lines:
        return []
    
    result = []
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
        
        # Проверяем, является ли строка DOI/URL
        # Варианты: https://doi.org/, http://doi.org/, http://dx.doi.org/
        line_lower = line_stripped.lower()
        is_doi_url = (
            line_stripped.startswith("http") and 
            ("doi.org" in line_lower or "dx.doi.org" in line_lower)
        )
        
        # Если это DOI/URL и есть предыдущая строка, объединяем
        if is_doi_url and result:
            result[-1] = result[-1] + " " + line_stripped
        else:
            result.append(line_stripped)
    
    return result


def blocks_to_lines(blocks: List[TextBlock], filter_service: bool = False, merge_doi_url: bool = True) -> List[str]:
    """
    Удобный конвертер: TextBlock[] -> list[str]
    (без склейки, просто извлекаем text).
    
    Args:
        blocks: Список блоков текста
        filter_service: Фильтровать ли служебные строки (УДК, email, DOI и т.д.)
        merge_doi_url: Объединять ли строки с DOI/URL с предыдущими строками
    """
    if filter_service:
        blocks = filter_service_blocks(blocks)
    lines = [b.text for b in sorted(blocks, key=lambda x: x.order)]
    
    # Объединяем строки с DOI/URL с предыдущими
    if merge_doi_url:
        lines = merge_doi_url_lines(lines)
    
    return lines


def read_lines(path: Union[str, Path], *, clean: bool = True, filter_service: bool = False, merge_doi_url: bool = True) -> List[str]:
    """
    Читает документ и возвращает список строк.
    
    Args:
        path: Путь к файлу
        clean: Очищать ли текст от табуляций и разрывов строк
        filter_service: Фильтровать ли служебные строки (УДК, email, DOI и т.д.)
        merge_doi_url: Объединять ли строки с DOI/URL с предыдущими строками
    """
    blocks = read_blocks(path, clean=clean)
    return blocks_to_lines(blocks, filter_service=filter_service, merge_doi_url=merge_doi_url)


def read_text(path: Union[str, Path], *, clean: bool = True, filter_service: bool = False, merge_doi_url: bool = True) -> str:
    """
    Читает документ и возвращает весь текст как одну строку.
    
    Args:
        path: Путь к файлу
        clean: Очищать ли текст от табуляций и разрывов строк
        filter_service: Фильтровать ли служебные строки (УДК, email, DOI и т.д.)
        merge_doi_url: Объединять ли строки с DOI/URL с предыдущими строками
    """
    return "\n".join(read_lines(path, clean=clean, filter_service=filter_service, merge_doi_url=merge_doi_url))


# =========================
# Backward compatibility / Convenience aliases
# =========================

def get_lines(path: Union[str, Path], clean: bool = True, filter_service: bool = False, merge_doi_url: bool = True) -> List[str]:
    """
    Получает текст из Word документа как список строк.
    (Алиас для read_lines для обратной совместимости)
    
    Args:
        path: Путь к файлу
        clean: Очищать ли текст от табуляций и разрывов строк
        filter_service: Фильтровать ли служебные строки (УДК, email, DOI и т.д.)
        merge_doi_url: Объединять ли строки с DOI/URL с предыдущими строками
    """
    return read_lines(path, clean=clean, filter_service=filter_service, merge_doi_url=merge_doi_url)


def get_full_text(path: Union[str, Path], clean: bool = True, filter_service: bool = False, merge_doi_url: bool = True) -> str:
    """
    Получает весь текст из Word документа как одну строку.
    (Алиас для read_text для обратной совместимости)
    
    Args:
        path: Путь к файлу
        clean: Очищать ли текст от табуляций и разрывов строк
        filter_service: Фильтровать ли служебные строки (УДК, email, DOI и т.д.)
        merge_doi_url: Объединять ли строки с DOI/URL с предыдущими строками
    """
    return read_text(path, clean=clean, filter_service=filter_service, merge_doi_url=merge_doi_url)


def read_word_file(
    path: Union[str, Path],
    clean: bool = True,
    return_format: str = 'lines'
) -> Union[List[str], str]:
    """
    Универсальная функция для чтения Word документов (DOCX или RTF).
    (Для обратной совместимости)
    
    Args:
        path: Путь к файлу (DOCX или RTF)
        clean: Очищать ли текст от табуляций и разрывов строк
        return_format: 'lines' (список строк) или 'text' (одна строка)
    """
    if return_format == 'text':
        return read_text(path, clean=clean)
    else:
        return read_lines(path, clean=clean)


def extract_text_from_file(path: Union[str, Path]) -> List[str]:
    """
    Извлекает текст из файла построчно.
    (Для обратной совместимости)
    """
    return read_lines(path, clean=True)


def read_docx(path: Union[str, Path], clean: bool = True) -> List[str]:
    """
    Читает DOCX файл и возвращает список строк текста.
    (Для обратной совместимости)
    """
    blocks = read_docx_blocks(path, ReaderConfig(clean=clean))
    return blocks_to_lines(blocks)


def read_rtf(path: Union[str, Path], clean: bool = True) -> List[str]:
    """
    Читает RTF файл и возвращает список строк текста.
    (Для обратной совместимости)
    """
    blocks = read_rtf_blocks(path, ReaderConfig(clean=clean))
    return blocks_to_lines(blocks)


# =========================
# Interactive file selection
# =========================

def get_files_from_words_input(input_dir: Optional[Union[str, Path]] = None) -> List[Path]:
    """
    Получает список поддерживаемых файлов из папки words_input.
    """
    if input_dir is None:
        script_dir = Path(__file__).parent.absolute()
        input_dir = script_dir / 'words_input'
    else:
        input_dir = Path(input_dir)
    
    if not input_dir.exists() or not input_dir.is_dir():
        return []
    
    files = [
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    
    return sorted(files, key=lambda x: x.name)


def pick_file_interactive(input_dir: Optional[Union[str, Path]] = None) -> Optional[Path]:
    """
    Интерактивно предлагает выбрать файл из папки words_input.
    """
    if input_dir is None:
        script_dir = Path(__file__).parent.absolute()
        input_dir = script_dir / 'words_input'
    else:
        input_dir = Path(input_dir)
    
    if not input_dir.exists() or not input_dir.is_dir():
        raise WordReaderError(
            f"Папка не найдена: {input_dir}\n"
            f"Создайте папку words_input и поместите в неё DOCX или RTF файлы."
        )
    
    files = get_files_from_words_input(input_dir)
    
    if not files:
        raise WordReaderError(
            f"В папке {input_dir.name}/ не найдено поддерживаемых файлов (DOCX, RTF)."
        )
    
    print(f"\nНайдено файлов в {input_dir.name}/:")
    print("-" * 60)
    for i, file in enumerate(files, 1):
        file_size = file.stat().st_size
        size_kb = file_size / 1024
        print(f"  {i:2d}. {file.name:<40} ({size_kb:.1f} KB)")
    print("-" * 60)
    
    while True:
        try:
            choice = input(f"\nВыберите файл (1-{len(files)}) или введите имя файла (или 'q' для выхода): ").strip()
            
            if choice.lower() in ['q', 'quit', 'exit', 'выход']:
                return None
            
            if not choice:
                continue
            
            try:
                file_num = int(choice)
                if 1 <= file_num <= len(files):
                    return files[file_num - 1]
                else:
                    print(f"Неверный номер. Выберите от 1 до {len(files)}")
                    continue
            except ValueError:
                selected_file = input_dir / choice
                if selected_file.exists() and selected_file.is_file():
                    if is_supported_format(selected_file):
                        return selected_file
                    else:
                        print(f"Файл {choice} не поддерживается. Поддерживаются: .docx, .rtf")
                        continue
                else:
                    print(f"Файл не найден: {choice}")
                    continue
                    
        except KeyboardInterrupt:
            print("\n\nПрервано пользователем.")
            return None
        except EOFError:
            print("\n\nВвод завершен.")
            return None


# =========================
# CLI / Main
# =========================

if __name__ == '__main__':
    """
    Пример использования модуля.
    """
    import sys
    
    # Проверяем зависимости
    deps = check_dependencies()
    print("=" * 80)
    print("Word Reader - Чтение Word документов (DOCX, RTF)")
    print("=" * 80)
    print("\nПроверка зависимостей:")
    print(f"  DOCX (zip+xml): {'✓' if deps['docx'] else '✗'}")
    print(f"  striprtf: {'✓' if deps['rtf'] else '✗ (установите: pip install striprtf)'}")
    
    if not deps['all_available']:
        print("\n⚠ Предупреждение: не все библиотеки установлены.")
        print("  Некоторые форматы могут быть недоступны.")
    print()
    
    # Проверяем, нужно ли фильтровать служебные строки
    filter_service = '--filter-service' in sys.argv or '-f' in sys.argv
    
    # Определяем файл для чтения (исключаем флаги из аргументов)
    file_path = None
    file_args = [arg for arg in sys.argv[1:] if not arg.startswith('-')]
    
    if file_args:
        # Файл указан в аргументах командной строки
        file_path = Path(file_args[0])
        if not file_path.is_absolute():
            script_dir = Path(__file__).parent.absolute()
            file_path = script_dir / file_path
    else:
        # Предлагаем выбрать файл из words_input
        try:
            file_path = pick_file_interactive()
            if file_path is None:
                print("\nВыбор файла отменен.")
                sys.exit(0)
        except WordReaderError as e:
            print(f"\nОшибка: {e}")
            print("\nИспользование:")
            print("  python word_reader.py                    # Выбор файла из words_input/")
            print("  python word_reader.py <путь_к_файлу>     # Указать файл напрямую")
            print("  python word_reader.py <путь> --filter-service  # С фильтрацией служебных строк")
            print("  python word_reader.py <путь> -f         # Короткий вариант фильтрации")
            print("  Пример: python word_reader.py words_input/ПММ-6_1.rtf -f")
            sys.exit(1)
    
    if not file_path.exists():
        print(f"Ошибка: файл не найден: {file_path}")
        sys.exit(1)
    
    if not file_path.is_file():
        print(f"Ошибка: указанный путь не является файлом: {file_path}")
        sys.exit(1)
    
    if not is_supported_format(file_path):
        print(f"Ошибка: неподдерживаемый формат файла: {file_path.suffix}")
        print("Поддерживаются форматы: .docx, .rtf")
        sys.exit(1)
    
    try:
        print("\n" + "=" * 80)
        print(f"Чтение файла: {file_path.name}")
        print(f"Формат: {file_path.suffix}")
        print(f"Размер: {file_path.stat().st_size / 1024:.1f} KB")
        print("=" * 80)
        print()
        
        # Проверяем, нужно ли фильтровать служебные строки
        filter_service = '--filter-service' in sys.argv or '-f' in sys.argv
        
        # Читаем файл как блоки
        blocks = read_blocks(file_path)
        total_blocks = len(blocks)
        
        print(f"✓ Извлечено блоков: {total_blocks}")
        if filter_service:
            blocks = filter_service_blocks(blocks)
            filtered_count = len(blocks)
            print(f"✓ После фильтрации служебных строк: {filtered_count} (удалено: {total_blocks - filtered_count})")
        print()
        
        if blocks:
            # Показываем информацию о блоках (только текст, без служебной информации)
            print("Первые 10 блоков:")
            print("-" * 80)
            for i, block in enumerate(blocks[:10], 1):
                # Показываем только текст, без [paragraph] word/document.xml
                print(f"{i:3d}. {block.text[:70]}{'...' if len(block.text) > 70 else ''}")
            
            if len(blocks) > 10:
                print(f"\n... и еще {len(blocks) - 10} блоков")
            
            # Показываем статистику
            total_chars = sum(len(b.text) for b in blocks)
            avg_block_length = total_chars / len(blocks) if blocks else 0
            sources = {}
            for b in blocks:
                sources[b.source] = sources.get(b.source, 0) + 1
            
            print("\n" + "-" * 80)
            print("Статистика:")
            print(f"  Всего блоков: {len(blocks)}")
            print(f"  Всего символов: {total_chars:,}")
            print(f"  Средняя длина блока: {avg_block_length:.1f} символов")
            print(f"  Источники:")
            for source, count in sorted(sources.items()):
                print(f"    - {source}: {count} блоков")
            print("-" * 80)
        else:
            print("⚠ Файл не содержит текста или текст не удалось извлечь.")
        
    except WordReaderError as e:
        print(f"\n✗ Ошибка чтения: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
