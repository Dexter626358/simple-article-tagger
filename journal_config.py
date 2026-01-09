#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Минимальный модуль конфигурации журнала для xml_generator.
"""

from typing import Dict, Any, Optional


def get_journal_config() -> Dict[str, Any]:
    """
    Возвращает конфигурацию журнала по умолчанию.
    
    Returns:
        Словарь с конфигурацией журнала
    """
    return {
        "titleid": 0,
        "issn": "",
        "journal_titles": {
            "ru": "",
            "en": "",
        },
        "issue": {
            "year": "",
            "volume": "",
            "number": "",
            "pages": "",
        },
    }


def load_config() -> Dict[str, Any]:
    """
    Загружает конфигурацию журнала.
    В данном случае просто возвращает конфигурацию по умолчанию.
    
    Returns:
        Словарь с конфигурацией журнала
    """
    return get_journal_config()

