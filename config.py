#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Централизованный конфигурационный файл для управления настройками всех модулей проекта.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Sequence


class Config:
    """
    Класс для управления конфигурацией всех модулей проекта.
    """
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Инициализирует конфигурацию.
        
        Args:
            config_file: Путь к JSON файлу с конфигурацией. Если None, используются значения по умолчанию.
        """
        self._config: Dict[str, Any] = {}
        self._config_file = config_file
        
        # Загружаем конфигурацию по умолчанию
        self._load_defaults()
        
        # Если указан файл конфигурации, загружаем из него
        if config_file and config_file.exists():
            self.load_from_file(config_file)
    
    def _load_defaults(self) -> None:
        """Загружает значения конфигурации по умолчанию."""
        script_dir = Path(__file__).parent.resolve()
        
        self._config = {
            # ----------------------------
            # Общие настройки
            # ----------------------------
            "general": {
                "project_root": str(script_dir),
                "encoding": "utf-8",
            },
            
            # ----------------------------
            # Настройки директорий
            # ----------------------------
            "directories": {
                "json_input": "json_input",
                "words_input": "words_input",
                "input_files": "input_files",
                "output": "output",
                "xml_output": "xml_output",
                "html_output": "html_output",
                "docx_output": "docx_output",
                "pdf_articles_input": "pdf_articles_input",
            },
            
            # ----------------------------
            # Настройки веб-приложения (app.py)
            # ----------------------------
            "app": {
                "host": "127.0.0.1",
                "port": 5001,
                "debug": False,
                "auto_open_browser": True,
                "use_word_reader": False,
                "browser_delay_sec": 1.2,
            },
            
            # ----------------------------
            # Настройки word_reader
            # ----------------------------
            "word_reader": {
                "clean_text": True,
                "merge_doi_url": True,
                "rtf_encodings": ["utf-8", "cp1251", "windows-1251", "latin-1"],
            },
            
            # ----------------------------
            # Настройки word_to_html
            # ----------------------------
            "word_to_html": {
                "use_word_reader": False,
                "include_metadata": False,
                "include_default_style_map": True,
                "style_map": None,  # Можно указать путь к файлу со style_map
            },
            
            # ----------------------------
            # Настройки метаданных
            # ----------------------------
            "metadata": {
                "merge_doi_url_with_references": True,
                "processed_suffix": "_processed",
            },
            
            # ----------------------------
            # Настройки XML генератора
            # ----------------------------
            "xml_generator": {
                "list_of_journals_file": "data/list_of_journals.json",
                "xml_schema_file": "data/xml_schema.xsd",
                "validate_xml": True,
                "ignore_validation_errors": {
                    "empty_volume": True,
                    "empty_references": True,
                },
            },
            
            # ----------------------------
            # Настройки валидации XML
            # ----------------------------
            "xml_validation": {
                "preferred_library": "xmlschema",  # "xmlschema" или "lxml"
                "fallback_to_basic_check": True,
            },
            
            # ----------------------------
            # Настройки разметки метаданных
            # ----------------------------
            "markup": {
                "auto_select_range": True,
                "show_line_numbers": True,
                "enable_search": True,
            },
            
            # ----------------------------
            # Настройки PDF reader
            # ----------------------------
            "pdf_reader": {
                "first_pages": 3,  # Количество первых страниц для обработки
                "last_pages": 3,   # Количество последних страниц для обработки
                "extract_all_pages": True,  # Если True, обрабатывать все страницы
                "clean_text": True,  # Очищать текст от лишних пробелов
                "smart_columns": True,  # Автоопределение 1/2 колонок при извлечении
                "two_column_min_words": 10,  # Мин. слов в каждой половине для 2-колоночной страницы
                "two_column_gutter_ratio": 0.1,  # Центральный зазор (доля ширины) для детекта колонок
            },
            
            # ----------------------------
            # Настройки GPT extraction
            # ----------------------------
            "gpt_extraction": {
                "enabled": True,  # Включить/выключить использование GPT для извлечения метаданных
                "model": "gpt-4.1-mini",  # Модель GPT для использования gpt-4o-mini
                "temperature": 0.3,  # Температура для генерации (0.0-2.0)
                "api_key": "",  # API ключ OpenAI (если пусто, используется переменная окружения OPENAI_API_KEY)
                "cache_dir": "gpt_cache",  # Директория для кэширования результатов (относительно project_root)
                "use_prompts_module": True,  # Использовать ли промпт из prompts.py
                "use_cache": True,  # Использовать ли кэширование результатов
                "extract_abstracts": True,  # Извлекать аннотации
                "extract_references": True,  # Извлекать списки литературы
            },
        }
    
    def load_from_file(self, config_file: Path) -> None:
        """
        Загружает конфигурацию из JSON файла.
        
        Args:
            config_file: Путь к JSON файлу с конфигурацией.
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            
            # Рекурсивно обновляем конфигурацию
            self._update_dict(self._config, file_config)
            self._config_file = config_file
        except Exception as e:
            raise ValueError(f"Ошибка при загрузке конфигурации из {config_file}: {e}")
    
    def save_to_file(self, config_file: Optional[Path] = None) -> None:
        """
        Сохраняет текущую конфигурацию в JSON файл.
        
        Args:
            config_file: Путь к файлу для сохранения. Если None, используется файл загрузки.
        """
        if config_file is None:
            config_file = self._config_file
        
        if config_file is None:
            raise ValueError("Не указан файл для сохранения конфигурации")
        
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)
    
    def _update_dict(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """Рекурсивно обновляет словарь base значениями из update."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._update_dict(base[key], value)
            else:
                base[key] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Получает значение конфигурации по пути (например, "app.port").
        
        Args:
            key_path: Путь к значению через точку (например, "app.port")
            default: Значение по умолчанию, если ключ не найден
            
        Returns:
            Значение конфигурации или default
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Устанавливает значение конфигурации по пути.
        
        Args:
            key_path: Путь к значению через точку (например, "app.port")
            value: Значение для установки
        """
        keys = key_path.split('.')
        config = self._config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def get_path(self, key_path: str, relative_to: Optional[Path] = None) -> Path:
        """
        Получает путь из конфигурации и преобразует его в Path.
        Если путь относительный, он будет разрешен относительно project_root или relative_to.
        
        Args:
            key_path: Путь к значению через точку (например, "directories.output")
            relative_to: Базовая директория для относительных путей. Если None, используется project_root.
            
        Returns:
            Path объект
        """
        path_str = self.get(key_path)
        if path_str is None:
            raise KeyError(f"Ключ конфигурации не найден: {key_path}")
        
        path = Path(path_str)
        
        if not path.is_absolute():
            if relative_to is None:
                project_root = Path(self.get("general.project_root", "."))
                path = project_root / path
            else:
                path = relative_to / path
        
        return path
    
    # ----------------------------
    # Удобные методы для доступа к настройкам
    # ----------------------------
    
    @property
    def json_input_dir(self) -> Path:
        """Путь к директории с JSON файлами."""
        return self.get_path("directories.json_input")
    
    @property
    def words_input_dir(self) -> Path:
        """Путь к директории с DOCX/RTF файлами."""
        return self.get_path("directories.words_input")
    
    @property
    def output_dir(self) -> Path:
        """Путь к директории для сохранения обработанных файлов."""
        return self.get_path("directories.output")
    
    @property
    def xml_output_dir(self) -> Path:
        """Путь к директории для сохранения XML файлов."""
        return self.get_path("directories.xml_output")
    
    @property
    def html_output_dir(self) -> Path:
        """Путь к директории для сохранения HTML файлов."""
        return self.get_path("directories.html_output")
    
    @property
    def docx_output_dir(self) -> Path:
        """Путь к директории для сохранения DOCX файлов."""
        return self.get_path("directories.docx_output")
    
    @property
    def pdf_articles_input_dir(self) -> Path:
        """Путь к директории с PDF файлами статей."""
        return self.get_path("directories.pdf_articles_input")
    
    @property
    def list_of_journals_path(self) -> Path:
        """Путь к файлу list_of_journals.json."""
        return self.get_path("xml_generator.list_of_journals_file")
    
    @property
    def xml_schema_path(self) -> Path:
        """Путь к файлу xml_schema.xsd."""
        return self.get_path("xml_generator.xml_schema_file")
    
    @property
    def app_port(self) -> int:
        """Порт веб-приложения."""
        return self.get("app.port", 5001)
    
    @property
    def app_host(self) -> str:
        """Хост веб-приложения."""
        return self.get("app.host", "127.0.0.1")
    
    @property
    def use_word_reader(self) -> bool:
        """Использовать ли word_reader для конвертации."""
        return self.get("app.use_word_reader", False) or self.get("word_to_html.use_word_reader", False)


# Глобальный экземпляр конфигурации
_config_instance: Optional[Config] = None


def get_config(config_file: Optional[Path] = None) -> Config:
    """
    Получает глобальный экземпляр конфигурации.
    
    Args:
        config_file: Путь к файлу конфигурации. Используется только при первом вызове.
        
    Returns:
        Экземпляр Config
    """
    global _config_instance
    
    if _config_instance is None:
        if config_file is None:
            # Пытаемся найти config.json в корне проекта
            script_dir = Path(__file__).parent.resolve()
            config_file = script_dir / "config.json"
            if not config_file.exists():
                config_file = None
        
        _config_instance = Config(config_file)
    
    return _config_instance


def reload_config(config_file: Optional[Path] = None) -> Config:
    """
    Перезагружает конфигурацию из файла.
    
    Args:
        config_file: Путь к файлу конфигурации. Если None, используется текущий файл.
        
    Returns:
        Экземпляр Config
    """
    global _config_instance
    _config_instance = Config(config_file)
    return _config_instance


if __name__ == "__main__":
    """
    Создает файл config.json с настройками по умолчанию.
    """
    import sys
    
    config = Config()
    
    if len(sys.argv) > 1:
        output_file = Path(sys.argv[1])
    else:
        script_dir = Path(__file__).parent.resolve()
        output_file = script_dir / "config.json"
    
    config.save_to_file(output_file)
    print(f"✅ Конфигурационный файл создан: {output_file}")
    print("   Отредактируйте его для настройки параметров работы модулей.")
