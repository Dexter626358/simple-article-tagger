#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Утилита для работы с bbox (bounding box) в PDF файлах.
Позволяет находить текстовые блоки по ключевым словам и получать их координаты.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

try:
    from converters.pdf_to_html import find_text_blocks_with_bbox, print_bbox_info, find_annotation_bbox_auto
except ImportError:
    print("Ошибка: не удалось импортировать функции из pdf_to_html.py")
    print("Убедитесь, что файл pdf_to_html.py доступен.")
    exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Находит текстовые блоки в PDF по ключевым словам и выводит их координаты (bbox)"
    )
    parser.add_argument("pdf_file", type=str, help="Путь к PDF файлу")
    parser.add_argument(
        "--terms",
        type=str,
        nargs="+",
        default=None,
        help="Ключевые слова для поиска (по умолчанию: Резюме, Аннотация, Abstract, Annotation)"
    )
    parser.add_argument(
        "--annotation",
        action="store_true",
        help="Автоматически найти аннотацию/резюме"
    )
    
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf_file)
    
    if not pdf_path.exists():
        print(f"Ошибка: файл не найден: {pdf_path}")
        return 1
    
    if args.annotation:
        # Автоматический поиск аннотации
        print(f"Поиск аннотации/резюме в файле: {pdf_path}\n")
        result = find_annotation_bbox_auto(pdf_path)
        
        if result:
            print(f"{'='*80}")
            print("Найдена аннотация:")
            print(f"{'='*80}\n")
            print(f"Ключевое слово: {result['term']}")
            print(f"Страница: {result['page']}")
            print(f"Bbox (оригинал): {result['bbox']}")
            print(f"Bbox (расширенный): {result['expanded_bbox']}")
            print(f"\nТекст блока:\n{result['text']}\n")
            
            bbox = result['expanded_bbox']
            print(f"{'='*80}")
            print("Координаты для использования:")
            print(f"{'='*80}")
            print(f"bbox = ({bbox[0]:.2f}, {bbox[1]:.2f}, {bbox[2]:.2f}, {bbox[3]:.2f})")
        else:
            print("Аннотация не найдена.")
    else:
        # Поиск по ключевым словам
        print(f"Поиск блоков в файле: {pdf_path}\n")
        print_bbox_info(pdf_path, search_terms=args.terms)
    
    return 0


if __name__ == "__main__":
    exit(main())
