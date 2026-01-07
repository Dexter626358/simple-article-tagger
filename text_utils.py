#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Утилиты для работы с текстом.
Функции для очистки и обработки текстовых данных.
"""


def clean_text(text: str) -> str:
    """
    Очищает текст от табуляций и разрывов строк.
    Заменяет табуляции и множественные пробелы на один пробел.
    
    Args:
        text: Исходный текст
        
    Returns:
        Очищенный текст
        
    Examples:
        >>> clean_text("Текст\\n\\tс\\n\\nпробелами")
        'Текст с пробелами'
        >>> clean_text("Много    пробелов")
        'Много пробелов'
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


def merge_doi_url_with_references(references: list[str]) -> list[str]:
    """
    Объединяет строки с DOI/URL с предыдущим источником в списке литературы.
    
    Если строка начинается с DOI или URL (https://, http://, doi.org, doi:),
    она объединяется с предыдущей строкой через пробел.
    
    Args:
        references: Список строк литературы
        
    Returns:
        Обработанный список, где DOI/URL прикреплены к предыдущим источникам
        
    Examples:
        >>> refs = [
        ...     "Krechetnikov R., Lipatov I. Hidden invariances...",
        ...     "https://doi.org/10.1137/S0036139900378906"
        ... ]
        >>> merge_doi_url_with_references(refs)
        ['Krechetnikov R., Lipatov I. Hidden invariances... https://doi.org/10.1137/S0036139900378906']
    """
    if not references:
        return []
    
    import re
    
    # Паттерны для определения DOI/URL
    # Проверяем, начинается ли строка с URL или DOI
    def is_doi_url_line(text: str) -> bool:
        """Проверяет, является ли строка DOI/URL."""
        if not text or not text.strip():
            return False
        text_stripped = text.strip()
        
        # Проверяем различные паттерны DOI/URL
        patterns = [
            r'^https?://',           # http:// или https://
            r'^doi\.org/',           # doi.org/ (без протокола)
            r'^doi:\s*',             # doi: или doi: с пробелом
            r'^http://dx\.doi\.org/', # http://dx.doi.org/
        ]
        
        for pattern in patterns:
            if re.match(pattern, text_stripped, re.IGNORECASE):
                return True
        
        # Дополнительная проверка: если строка содержит только URL/DOI
        # (начинается с https:// или http:// и содержит doi.org)
        if re.match(r'^https?://.*doi\.org', text_stripped, re.IGNORECASE):
            return True
            
        return False
    
    
    result = []
    i = 0
    
    while i < len(references):
        current = references[i].strip()
        
        # Если текущая строка - DOI/URL и есть предыдущая строка
        if is_doi_url_line(current) and result:
            # Объединяем с предыдущей строкой
            result[-1] = result[-1] + " " + current
        else:
            # Добавляем как новую строку
            if current:  # Пропускаем пустые строки
                result.append(current)
        
        i += 1
    
    return result


if __name__ == '__main__':
    # Тестирование функции
    test_cases = [
        ("Текст\n\tс\n\nпробелами", "Текст с пробелами"),
        ("Много    пробелов", "Много пробелов"),
        ("Обычный текст", "Обычный текст"),
        ("", ""),
        ("   Пробелы в начале и конце   ", "Пробелы в начале и конце"),
    ]
    
    print("Тестирование функции clean_text:")
    print("-" * 60)
    
    all_passed = True
    for input_text, expected in test_cases:
        result = clean_text(input_text)
        passed = result == expected
        all_passed = all_passed and passed
        
        status = "✓" if passed else "✗"
        print(f"{status} Вход: {repr(input_text)}")
        print(f"  Ожидалось: {repr(expected)}")
        print(f"  Получено:  {repr(result)}")
        if not passed:
            print(f"  ❌ ОШИБКА!")
        print()
    
    if all_passed:
        print("Все тесты пройдены успешно! ✓")
    else:
        print("Некоторые тесты не пройдены! ✗")

