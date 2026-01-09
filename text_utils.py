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


def clean_pdf_text_for_llm(text: str, min_repeats: int = 3, custom_patterns: list[str] | None = None) -> str:
    """
    Очищает и структурирует текст, извлеченный из PDF, для отправки в LLM.
    
    Автоматически определяет и удаляет повторяющиеся колонтитулы (любые строки,
    которые встречаются более min_repeats раз).
    
    Также удаляет:
    - Лишние пробелы и переносы строк
    - Артефакты PDF
    
    Args:
        text: Исходный текст из PDF
        min_repeats: Минимальное количество повторений строки для определения её как колонтитула (по умолчанию: 3)
        custom_patterns: Дополнительные паттерны для удаления (опционально)
        
    Returns:
        Очищенный и структурированный текст
        
    Examples:
        >>> text = "Заголовок\\nТекст статьи\\nЗаголовок\\nПродолжение\\nЗаголовок"
        >>> clean_pdf_text_for_llm(text, min_repeats=2)
        'Текст статьи\\nПродолжение'
    """
    if not text:
        return ""
    
    import re
    from collections import Counter
    
    # Разбиваем текст на строки
    lines = text.split('\n')
    
    # Подсчитываем частоту появления каждой строки (без учета пробелов в начале/конце)
    line_counts = Counter(line.strip() for line in lines if line.strip())
    
    # Определяем колонтитулы: строки, которые встречаются min_repeats или более раз
    # Исключаем очень короткие строки (менее 3 символов) - это могут быть просто знаки препинания
    headers_to_remove = {
        line for line, count in line_counts.items() 
        if count >= min_repeats and len(line) >= 3
    }
    
    # Если указаны дополнительные паттерны, добавляем их
    if custom_patterns:
        for pattern in custom_patterns:
            # Находим все строки, соответствующие паттерну
            for line in line_counts.keys():
                if re.match(pattern, line, re.IGNORECASE):
                    headers_to_remove.add(line)
    
    # Удаляем колонтитулы из текста
    filtered_lines = []
    for line in lines:
        line_stripped = line.strip()
        # Пропускаем строки, которые являются колонтитулами
        if line_stripped not in headers_to_remove:
            filtered_lines.append(line)
    
    text = '\n'.join(filtered_lines)
    
    # Удаляем колонтитулы, которые могут быть встроены в строки
    # Паттерны для поиска колонтитулов внутри текста
    header_patterns_inline = [
        r'Вестник ВНИИДАД № \d+ \| \d{4}',
        r'Herald of VNIIDAD № \d+ \| \d{4}',
        r'Archival science and document science \d+',
        r'Архивоведение и документоведение \d+',
    ]
    
    for pattern in header_patterns_inline:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Удаляем переносы слов с дефисом (например: "иссле- дования" -> "исследования")
    # Более точный паттерн: минимум 3 буквы перед дефисом, чтобы избежать ложных срабатываний
    # И проверяем, что после дефиса идет строчная буква (не начало нового слова)
    def fix_hyphenated_words(match):
        """Исправляет переносы слов с дефисом."""
        before = match.group(1)  # Часть до дефиса
        after = match.group(2)    # Часть после дефиса
        
        # Если часть до дефиса слишком короткая (менее 4 символов), это скорее всего не перенос слова
        # Примеры: "ар-", "Рос-", "Пенз-" - это не переносы, а разрывы слов
        if len(before) < 4:
            return match.group(0)  # Возвращаем как было
        
        # Если после дефиса идет заглавная буква, это скорее всего начало нового слова, а не перенос
        # Примеры: "видео- Участие", "ар- Конференцсвязи" - не склеиваем
        if after and after[0].isupper():
            return match.group(0)  # Возвращаем как было
        
        # Объединяем части слова только если обе части в нижнем регистре
        # или первая часть заканчивается на строчную, а вторая начинается со строчной
        return before + after
    
    # Паттерн: минимум 4 буквы + дефис + пробел(ы) + буква
    # Это обрабатывает случаи типа "иссле- дования", "документове- дения"
    # Но НЕ обрабатывает "ар- конференцсвязи", "Рос- сийского", "Пенз- енской"
    text = re.sub(r'([а-яА-Яa-zA-Z]{4,})-\s+([а-яА-Яa-zA-Z])', fix_hyphenated_words, text)
    
    # Также обрабатываем случаи, когда дефис стоит в конце строки
    # (минимум 4 буквы + дефис + перенос строки + пробелы + буква)
    text = re.sub(r'([а-яА-Яa-zA-Z]{4,})-\n\s+([а-яА-Яa-zA-Z])', fix_hyphenated_words, text)
    
    # Удаляем множественные пустые строки (более 2 подряд)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Нормализуем пробелы (множественные пробелы -> один)
    text = re.sub(r' +', ' ', text)
    
    # Удаляем пробелы в начале и конце строк
    lines = text.split('\n')
    lines = [line.strip() for line in lines]
    text = '\n'.join(lines)
    
    # Удаляем пустые строки в начале и конце
    text = text.strip()
    
    return text


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

