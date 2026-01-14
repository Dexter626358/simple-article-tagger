#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для массовой конвертации всех RTF файлов в DOCX формат.
Конвертирует файлы в той же директории, заменяя расширение .rtf на .docx.
"""

import sys
from pathlib import Path
from typing import List

try:
    from converters.convert_rtf_to_docx import convert_rtf_to_docx, ConversionError
except ImportError:
    print("Ошибка: модуль convert_rtf_to_docx не найден")
    sys.exit(1)


def find_all_rtf_files(input_dir: Path) -> List[Path]:
    """
    Находит все RTF файлы рекурсивно в указанной директории.
    
    Args:
        input_dir: Директория для поиска
        
    Returns:
        Список путей к RTF файлам
    """
    if not input_dir.exists() or not input_dir.is_dir():
        return []
    
    # Рекурсивный поиск всех RTF файлов
    rtf_files = list(input_dir.rglob('*.rtf')) + list(input_dir.rglob('*.RTF'))
    
    # Фильтруем только файлы (не директории)
    rtf_files = [f for f in rtf_files if f.is_file()]
    
    return sorted(rtf_files, key=lambda x: x.name)


def convert_all_rtf_to_docx(input_dir: Path, preserve_formatting: bool = True) -> dict:
    """
    Конвертирует все RTF файлы в DOCX в той же директории.
    
    Args:
        input_dir: Директория с RTF файлами
        preserve_formatting: Сохранять ли форматирование
        
    Returns:
        Словарь с результатами: {'converted': [...], 'errors': [...], 'skipped': [...]}
    """
    rtf_files = find_all_rtf_files(input_dir)
    
    if not rtf_files:
        print(f"В директории {input_dir} не найдено RTF файлов")
        return {'converted': [], 'errors': [], 'skipped': []}
    
    print(f"Найдено RTF файлов: {len(rtf_files)}")
    print("=" * 80)
    
    converted = []
    errors = []
    skipped = []
    
    for i, rtf_file in enumerate(rtf_files, 1):
        # Определяем выходной файл в той же директории
        output_file = rtf_file.with_suffix('.docx')
        
        # Проверяем, существует ли уже DOCX файл
        if output_file.exists():
            print(f"{i:3d}/{len(rtf_files)} ⚠ Пропущен (DOCX уже существует): {rtf_file.name}")
            skipped.append(rtf_file)
            continue
        
        try:
            print(f"{i:3d}/{len(rtf_files)} Обработка: {rtf_file.name}...", end=' ', flush=True)
            
            # Конвертируем
            result = convert_rtf_to_docx(rtf_file, output_file, preserve_formatting)
            converted.append(result)
            print(f"✓ Успешно")
            
        except ConversionError as e:
            error_msg = f"✗ Ошибка: {e}"
            print(error_msg)
            errors.append((rtf_file, str(e)))
        except Exception as e:
            error_msg = f"✗ Неожиданная ошибка: {e}"
            print(error_msg)
            errors.append((rtf_file, str(e)))
    
    print("=" * 80)
    print(f"\nРезультаты:")
    print(f"  ✓ Успешно конвертировано: {len(converted)}")
    print(f"  ⚠ Пропущено (DOCX уже существует): {len(skipped)}")
    print(f"  ✗ Ошибок: {len(errors)}")
    
    if errors:
        print(f"\nОшибки:")
        for rtf_file, error_msg in errors:
            print(f"  - {rtf_file.name}: {error_msg}")
    
    return {
        'converted': converted,
        'errors': errors,
        'skipped': skipped
    }


def main():
    """Основная функция."""
    script_dir = Path(__file__).parent.absolute()
    default_input_dir = script_dir / 'words_input'
    
    # Определяем входную директорию
    if len(sys.argv) > 1:
        input_dir = Path(sys.argv[1])
        if not input_dir.is_absolute():
            input_dir = script_dir / input_dir
    else:
        input_dir = default_input_dir
    
    if not input_dir.exists():
        print(f"Ошибка: директория не найдена: {input_dir}")
        print(f"\nИспользование:")
        print(f"  python convert_all_rtf_to_docx.py [путь_к_директории]")
        print(f"  Пример: python convert_all_rtf_to_docx.py words_input/")
        sys.exit(1)
    
    if not input_dir.is_dir():
        print(f"Ошибка: указанный путь не является директорией: {input_dir}")
        sys.exit(1)
    
    print("=" * 80)
    print("Массовая конвертация RTF -> DOCX")
    print("=" * 80)
    print(f"Директория: {input_dir}")
    print(f"Файлы будут сохранены в тех же папках с расширением .docx")
    print()
    
    # Подтверждение
    rtf_files = find_all_rtf_files(input_dir)
    if not rtf_files:
        print(f"В директории {input_dir} не найдено RTF файлов")
        sys.exit(0)
    
    print(f"Будет обработано файлов: {len(rtf_files)}")
    response = input("\nПродолжить? (y/n): ").strip().lower()
    
    if response not in ['y', 'yes', 'да', 'д']:
        print("Отменено пользователем")
        sys.exit(0)
    
    print()
    
    # Конвертируем
    try:
        results = convert_all_rtf_to_docx(input_dir, preserve_formatting=True)
        
        if results['converted']:
            print(f"\n✓ Конвертация завершена успешно!")
        elif results['errors']:
            print(f"\n⚠ Конвертация завершена с ошибками")
        else:
            print(f"\n⚠ Все файлы уже были конвертированы ранее")
            
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
