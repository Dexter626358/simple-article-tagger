#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для извлечения метаданных из текста статей с помощью GPT.
"""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    try:
        import openai
        OPENAI_AVAILABLE = True
        OPENAI_LEGACY = True
    except ImportError:
        OPENAI_AVAILABLE = False
        OPENAI_LEGACY = False


class GPTExtractionError(Exception):
    """Ошибки при извлечении метаданных с помощью GPT."""
    pass


def hash_prompt(prompt: str) -> str:
    """
    Создает хэш промпта для идентификации и кэширования.
    
    Args:
        prompt: Текст промпта
        
    Returns:
        SHA256 хэш промпта в виде строки
    """
    return hashlib.sha256(prompt.encode('utf-8')).hexdigest()


def create_extraction_prompt(text: str, use_prompts_module: bool = True) -> str:
    """
    Создает промпт для извлечения метаданных из текста статьи.
    
    Args:
        text: Текст статьи для обработки
        use_prompts_module: Использовать ли промпт из модуля prompts.py (если доступен)
        
    Returns:
        Промпт для GPT
    """
    # Пробуем использовать промпт из prompts.py
    if use_prompts_module:
        try:
            from prompts import Prompts
            base_prompt = Prompts.SCIENTIFIC_DETAILED
            # Добавляем текст статьи к промпту
            prompt = f"{base_prompt}\n\nТекст статьи для анализа:\n\n{text}"
            return prompt
        except (ImportError, AttributeError):
            pass
    
    # Если промпт из prompts.py недоступен, используем базовый промпт
    prompt = f"""Извлеки метаданные из следующего текста научной статьи и верни результат в формате JSON.

Текст статьи:
{text}

Извлеки следующие поля:
- title (название статьи на русском языке)
- title_en (название статьи на английском языке, если есть)
- IMPORTANT: Extract full information for all authors listed in the article. Do not omit any author under any circumstances.
- authors (список авторов, каждый автор как объект с полями: surname, initials, organization, address, email, otherInfo - для русского и английского языков)
- doi (DOI статьи, если есть)
- udc (УДК, если есть)
- bbk (ББК, если есть)
- edn (EDN, если есть)
- annotation (аннотация на русском языке)
- annotation_en (аннотация на английском языке, если есть)
- keywords (ключевые слова на русском языке, список)
- keywords_en (ключевые слова на английском языке, список, если есть)
- pages (страницы статьи в формате "начало-конец", например "9-18")
- artType (тип статьи: "Научная статья", "Обзорная статья" и т.д.)
- PublLang (язык публикации: "RUS", "ENG" или "BOTH")
- datePublication (дата публикации в формате YYYY-MM-DD)
- received_date (дата поступления в редакцию в формате YYYY-MM-DD, если есть)
- reviewed_date (дата рецензирования в формате YYYY-MM-DD, если есть)
- accepted_date (дата принятия к публикации в формате YYYY-MM-DD, если есть)
- funding (финансирование на русском языке, если есть)
- funding_en (финансирование на английском языке, если есть)
- references_ru (список литературы на русском языке)
- references_en (список литературы на английском языке, если есть)

Верни только валидный JSON объект без дополнительных комментариев и форматирования.
Если какое-то поле отсутствует в тексте, верни null для этого поля.
"""
    return prompt


def extract_metadata_with_gpt(
    text: str,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    api_key: Optional[str] = None,
    cache_dir: Optional[Path] = None,
    use_prompts_module: Optional[bool] = None,
    use_cache: Optional[bool] = None,
    raw_prompt: bool = False,
    config: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Извлекает метаданные из текста статьи с помощью GPT.
    
    Args:
        text: Текст статьи для обработки
        model: Модель GPT для использования (по умолчанию: gpt-4o-mini)
        temperature: Температура для генерации (по умолчанию: 0.3)
        api_key: API ключ OpenAI (если не указан, используется переменная окружения OPENAI_API_KEY)
        cache_dir: Директория для кэширования результатов (опционально)
        
    Returns:
        Словарь с извлеченными метаданными
        
    Raises:
        GPTExtractionError: Если произошла ошибка при извлечении
    """
    if not OPENAI_AVAILABLE:
        raise GPTExtractionError(
            "Библиотека openai не установлена. "
            "Установите её: pip install openai"
        )
    
    # Загружаем настройки из конфига, если он передан
    if config is not None:
        if model is None:
            model = config.get("gpt_extraction.model", "gpt-4o-mini")
        if temperature is None:
            temperature = config.get("gpt_extraction.temperature", 0.3)
        if cache_dir is None:
            cache_dir_str = config.get("gpt_extraction.cache_dir")
            if cache_dir_str:
                try:
                    cache_dir = config.get_path("gpt_extraction.cache_dir")
                except Exception:
                    cache_dir = Path(cache_dir_str)
        if use_prompts_module is None:
            use_prompts_module = config.get("gpt_extraction.use_prompts_module", True)
        if use_cache is None:
            use_cache = config.get("gpt_extraction.use_cache", True)
    else:
        # Значения по умолчанию, если конфиг не передан
        if model is None:
            model = "gpt-4o-mini"
        if temperature is None:
            temperature = 0.3
        if use_prompts_module is None:
            use_prompts_module = True
        if use_cache is None:
            use_cache = True
    
    # API ключ: приоритет - переменная окружения > параметр функции > config
    import os
    if not api_key:
        # Сначала пробуем переменную окружения (высший приоритет)
        api_key = os.getenv('OPENAI_API_KEY')
        
        # Отладочный вывод
        if api_key:
            print(f"✅ API ключ найден в переменной окружения (длина: {len(api_key)} символов)")
        else:
            print("⚠️  API ключ не найден в переменной окружения OPENAI_API_KEY")
        
        # Если не найдена в переменной окружения, пробуем config
        if not api_key and config is not None:
            api_key_from_config = config.get("gpt_extraction.api_key", "")
            if api_key_from_config and api_key_from_config.strip():
                api_key = api_key_from_config.strip()
                print("✅ API ключ найден в config.json")
    
    if not api_key:
        raise GPTExtractionError(
            "API ключ OpenAI не указан. "
            "Установите переменную окружения OPENAI_API_KEY или укажите ключ в config.json (gpt_extraction.api_key)"
        )
    
    # Создаем промпт (если raw_prompt=True, используем текст как есть)
    if raw_prompt:
        prompt = text
    else:
        prompt = create_extraction_prompt(text, use_prompts_module=use_prompts_module)
    
    # Хэшируем промпт для кэширования
    prompt_hash = hash_prompt(prompt)
    
    # Проверяем кэш, если указана директория для кэширования и кэш включен
    if cache_dir and use_cache:
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{prompt_hash}.json"
        
        if cache_file.exists():
            try:
                cached_data = json.loads(cache_file.read_text(encoding='utf-8'))
                print(f"✅ Использован кэш для промпта (хэш: {prompt_hash[:16]}...)")
                return cached_data
            except Exception as e:
                print(f"⚠️  Ошибка при чтении кэша: {e}")
    
    try:
        # Отправляем запрос к GPT
        print(f"📤 Отправка запроса к GPT (модель: {model}, хэш промпта: {prompt_hash[:16]}...)")
        
        # Используем современный API или старый в зависимости от версии библиотеки
        if OPENAI_AVAILABLE and not getattr(globals(), 'OPENAI_LEGACY', False):
            # Современный API (openai >= 1.0.0)
            try:
                import httpx
                http_client = httpx.Client(
                    timeout=httpx.Timeout(60.0, connect=10.0),
                )
                client = OpenAI(api_key=api_key, http_client=http_client, max_retries=2)
            except Exception:
                client = OpenAI(api_key=api_key, timeout=60)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Ты помощник для извлечения метаданных из научных статей. Всегда возвращай валидный JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                response_format={"type": "json_object"}  # Требуем JSON ответ
            )
            # Извлекаем JSON из ответа
            response_text = response.choices[0].message.content.strip()
        else:
            # Старый API (openai < 1.0.0)
            import openai
            openai.api_key = api_key
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Ты помощник для извлечения метаданных из научных статей. Всегда возвращай валидный JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                response_format={"type": "json_object"}  # Требуем JSON ответ
            )
            # Извлекаем JSON из ответа
            response_text = response.choices[0].message.content.strip()
        
        # Парсим JSON
        try:
            metadata = json.loads(response_text)
        except json.JSONDecodeError as e:
            # Пытаемся извлечь JSON из текста, если он обернут в markdown
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                metadata = json.loads(json_match.group(0))
            else:
                raise GPTExtractionError(f"Не удалось распарсить JSON из ответа GPT: {e}")
        
        # Сохраняем в кэш, если указана директория и кэш включен
        if cache_dir and use_cache:
            try:
                cache_file.write_text(
                    json.dumps(metadata, ensure_ascii=False, indent=2),
                    encoding='utf-8'
                )
                print(f"💾 Результат сохранен в кэш: {cache_file.name}")
            except Exception as e:
                print(f"⚠️  Ошибка при сохранении в кэш: {e}")
        
        print(f"✅ Метаданные успешно извлечены")
        return metadata
        
    except Exception as e:
        # Проверяем, является ли это ошибкой OpenAI API
        error_msg = str(e)
        if "OpenAI" in error_msg or "API" in error_msg or "rate limit" in error_msg.lower():
            raise GPTExtractionError(f"Ошибка API OpenAI: {e}")
        raise
    except Exception as e:
        raise GPTExtractionError(f"Неожиданная ошибка при извлечении метаданных: {e}")


def extract_metadata_from_pdf(
    pdf_path: Path,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    api_key: Optional[str] = None,
    cache_dir: Optional[Path] = None,
    use_word_reader: bool = False,
    config: Optional[Any] = None,
    json_output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Извлекает метаданные из PDF файла: читает текст и отправляет его в GPT.
    
    Автоматически сохраняет JSON файл в папку архива:
    - Если PDF находится в input_files/<архив>/raw/article.pdf,
      то JSON будет сохранен в input_files/<архив>/json/article.json
    
    Args:
        pdf_path: Путь к PDF файлу
        model: Модель GPT для использования (если None, берется из конфига)
        temperature: Температура для генерации (если None, берется из конфига)
        api_key: API ключ OpenAI (если None, берется из конфига или переменной окружения)
        cache_dir: Директория для кэширования результатов (если None, берется из конфига)
        use_word_reader: Использовать ли word_reader для извлечения текста (не используется для PDF)
        config: Объект конфигурации (опционально)
        json_output_dir: Директория для сохранения JSON (если None, используется input_files/<архив>/json)
        
    Returns:
        Словарь с извлеченными метаданными
    """
    # Импортируем модули для чтения PDF
    try:
        from converters.pdf_reader import read_pdf_text, PDFReaderConfig
        from config import get_config
        from text_utils import clean_pdf_text_for_llm
    except ImportError as e:
        raise GPTExtractionError(f"Не удалось импортировать необходимые модули: {e}")
    
    # Загружаем конфигурацию, если не передан
    if config is None:
        try:
            config = get_config()
        except Exception:
            config = None
    
    # Загружаем настройки GPT из конфига, если они не указаны явно
    if config is not None:
        if model is None:
            model = config.get("gpt_extraction.model", "gpt-4o-mini")
        if temperature is None:
            temperature = config.get("gpt_extraction.temperature", 0.3)
        if cache_dir is None:
            cache_dir_str = config.get("gpt_extraction.cache_dir")
            if cache_dir_str:
                try:
                    cache_dir = config.get_path("gpt_extraction.cache_dir")
                except Exception:
                    cache_dir = Path(cache_dir_str)
    
    # API ключ: приоритет - переменная окружения > параметр функции > config
    import os
    if not api_key:
        # Сначала пробуем переменную окружения (высший приоритет)
        api_key = os.getenv('OPENAI_API_KEY')
        
        # Отладочный вывод
        if api_key:
            print(f"✅ API ключ найден в переменной окружения (длина: {len(api_key)} символов)")
        else:
            print("⚠️  API ключ не найден в переменной окружения OPENAI_API_KEY")
        
        # Если не найдена в переменной окружения, пробуем config
        if not api_key and config is not None:
            api_key_from_config = config.get("gpt_extraction.api_key", "")
            if api_key_from_config and api_key_from_config.strip():
                api_key = api_key_from_config.strip()
                print("✅ API ключ найден в config.json")
    
    # Загружаем настройки PDF reader из конфига
    try:
        if config:
            pdf_config = PDFReaderConfig(
                first_pages=config.get("pdf_reader.first_pages", 3),
                last_pages=config.get("pdf_reader.last_pages", 3),
                extract_all_pages=config.get("pdf_reader.extract_all_pages", False),
                clean_text=config.get("pdf_reader.clean_text", True),
            )
        else:
            pdf_config = PDFReaderConfig()
    except Exception:
        pdf_config = PDFReaderConfig()
    
    # Шаг 1: Читаем текст из PDF с помощью pdf_reader
    print(f"📖 Шаг 1: Чтение текста из PDF через pdf_reader: {pdf_path.name}")
    print(f"   Настройки: первые {pdf_config.first_pages} страниц, последние {pdf_config.last_pages} страниц")
    if pdf_config.extract_all_pages:
        print("   Режим: извлечение всех страниц")
    try:
        raw_text = read_pdf_text(pdf_path, pdf_config)
        print(f"✅ Извлечено {len(raw_text)} символов из PDF")
    except Exception as e:
        raise GPTExtractionError(f"Ошибка при чтении PDF через pdf_reader: {e}")
    
    # Шаг 2: Очищаем текст для LLM
    print("\n🧹 Шаг 2: Очистка текста для LLM...")
    cleaned_text = clean_pdf_text_for_llm(raw_text, min_repeats=3)
    print(f"✅ Очищенный текст: {len(cleaned_text)} символов (было {len(raw_text)})")
    
    # Проверяем, включено ли использование GPT
    if config and not config.get("gpt_extraction.enabled", True):
        raise GPTExtractionError(
            "Использование GPT для извлечения метаданных отключено в конфигурации. "
            "Установите gpt_extraction.enabled = true для включения."
        )
    
    # Шаг 3: Извлекаем метаданные с помощью GPT
    print("\n🤖 Шаг 3: Извлечение метаданных с помощью GPT...")
    metadata = extract_metadata_with_gpt(
        cleaned_text,
        model=model,
        temperature=temperature,
        api_key=api_key,
        cache_dir=cache_dir,
        config=config
    )
    
    # Добавляем имя исходного PDF файла в метаданные
    if metadata is not None:
        # Инициализируем поле file, если его нет
        if "file" not in metadata:
            metadata["file"] = ""
        # Устанавливаем имя PDF файла (с расширением)
        metadata["file"] = pdf_path.name
        print(f"📄 Имя исходного файла добавлено в метаданные: {pdf_path.name}")
    
    # Определяем путь для сохранения JSON
    if json_output_dir is None:
        # Если не указана директория, используем input_files/<архив>/json
        if config:
            try:
                pdf_input_dir = config.get_path("directories.input_files")
            except Exception:
                pdf_input_dir = Path("input_files")
        else:
            pdf_input_dir = Path("input_files")

        pdf_path_abs = pdf_path.resolve()
        pdf_input_dir_abs = pdf_input_dir.resolve()

        try:
            pdf_relative = pdf_path_abs.relative_to(pdf_input_dir_abs)
            # Ожидаем структуру input_files/<архив>/raw/<file>.pdf
            parts = list(pdf_relative.parts)
            archive_name = parts[0] if parts else ""
            if archive_name:
                output_folder = pdf_input_dir_abs / archive_name / "json"
            else:
                output_folder = pdf_input_dir_abs / "json"
            output_folder.mkdir(parents=True, exist_ok=True)
            json_filename = pdf_path.stem + ".json"
            json_output_path = output_folder / json_filename
        except ValueError:
            # Если PDF не находится внутри input_files, сохраняем рядом с PDF
            output_folder = pdf_path_abs.parent
            json_filename = pdf_path.stem + ".json"
            json_output_path = output_folder / json_filename
    else:
        # Используем указанную директорию
        json_output_dir = Path(json_output_dir)
        json_output_dir.mkdir(parents=True, exist_ok=True)
        json_filename = pdf_path.stem + ".json"
        json_output_path = json_output_dir / json_filename
    
    # Сохраняем метаданные в JSON файл
    json_output_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    print(f"💾 Метаданные сохранены: {json_output_path}")
    
    return metadata


if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description="Извлечение метаданных из PDF статей с помощью GPT",
        epilog="""
Примеры использования:
  # Обработка всех PDF файлов из input_files (по умолчанию):
  python services/gpt_extraction.py
  
  # Обработка одного файла:
  python services/gpt_extraction.py article.pdf
  
  # Обработка всех PDF файлов из указанной подпапки:
  python services/gpt_extraction.py --folder 2619-1601_2024_4
  
  # С указанием API ключа:
  python services/gpt_extraction.py --api-key sk-your-key-here
  
  # С указанием модели и температуры:
  python services/gpt_extraction.py --model gpt-4o --temperature 0.5

Примечание: 
  - По умолчанию обрабатываются все PDF файлы из input_files (включая подпапки)
  - API ключ можно установить через переменную окружения OPENAI_API_KEY
    или указать в config.json (gpt_extraction.api_key). Переменная окружения имеет приоритет.
  - JSON файлы сохраняются в json_input с сохранением структуры папок.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Аргументы для выбора источника файлов
    parser.add_argument(
        "pdf_path",
        type=Path,
        nargs="?",
        default=None,
        help="Путь к PDF файлу (если не указан, обрабатываются все PDF из input_files и подпапок)"
    )
    parser.add_argument(
        "--folder",
        type=str,
        help="Обработать все PDF файлы из указанной подпапки (например: 2619-1601_2024_4)"
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="Модель GPT для использования (по умолчанию: gpt-4o-mini)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.3,
        help="Температура для генерации (по умолчанию: 0.3)"
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="API ключ OpenAI (или используйте переменную окружения OPENAI_API_KEY)"
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Директория для кэширования результатов (опционально)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Путь для сохранения JSON файла с метаданными (по умолчанию: {pdf_name}_metadata.json)"
    )
    
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Путь к файлу конфигурации (по умолчанию: config.json)"
    )
    
    args = parser.parse_args()
    
    # Загружаем конфигурацию
    try:
        from config import get_config, Config
        if args.config:
            config = Config(args.config)
        else:
            config = get_config()
    except Exception as e:
        print(f"⚠️  Предупреждение: не удалось загрузить конфигурацию: {e}")
        config = None
    
    # Проверяем, включено ли использование GPT
    if config and not config.get("gpt_extraction.enabled", True):
        print("❌ Использование GPT для извлечения метаданных отключено в конфигурации.")
        print("   Установите gpt_extraction.enabled = true для включения.")
        sys.exit(1)
    
    # Определяем список PDF файлов для обработки
    pdf_files_to_process = []
    
    # Определяем базовую папку input_files
    if config:
        try:
            pdf_input_dir = config.get_path("directories.input_files")
        except Exception:
            pdf_input_dir = Path("input_files")
    else:
        pdf_input_dir = Path("input_files")
    
    if args.folder:
        # Обрабатываем все PDF файлы из указанной подпапки
        folder_path = pdf_input_dir / args.folder
        
        if not folder_path.exists():
            print(f"❌ Папка не найдена: {folder_path}")
            sys.exit(1)
        
        # Находим все PDF файлы в указанной подпапке
        pdf_files_to_process = list(folder_path.glob("*.pdf"))
        
        if not pdf_files_to_process:
            print(f"⚠️  PDF файлы не найдены в папке: {folder_path}")
            sys.exit(0)
        
        print(f"📁 Найдено {len(pdf_files_to_process)} PDF файлов в папке: {args.folder}")
        
    elif args.pdf_path:
        # Обрабатываем один файл
        if not args.pdf_path.exists():
            print(f"❌ Файл не найден: {args.pdf_path}")
            sys.exit(1)
        
        pdf_files_to_process = [args.pdf_path]
        
    else:
        # По умолчанию: обрабатываем все PDF файлы из input_files (включая подпапки)
        if not pdf_input_dir.exists():
            print(f"❌ Папка не найдена: {pdf_input_dir}")
            print("   Создайте папку input_files и поместите туда PDF файлы в подпапках")
            sys.exit(1)
        
        # Рекурсивно находим все PDF файлы во всех подпапках
        pdf_files_to_process = list(pdf_input_dir.rglob("*.pdf"))
        
        if not pdf_files_to_process:
            print(f"⚠️  PDF файлы не найдены в папке: {pdf_input_dir}")
            print("   Поместите PDF файлы в подпапки внутри input_files")
            sys.exit(0)
        
        print(f"📁 Найдено {len(pdf_files_to_process)} PDF файлов для обработки")
        print(f"   Папка: {pdf_input_dir}")
    
    # Обрабатываем файлы
    successful = 0
    failed = 0
    
    try:
        print("=" * 80)
        print("🤖 Извлечение метаданных с помощью GPT")
        print("=" * 80)
        
        for i, pdf_path in enumerate(pdf_files_to_process, 1):
            print(f"\n[{i}/{len(pdf_files_to_process)}] Обработка: {pdf_path.name}")
            print("-" * 80)
            
            try:
                # Определяем директорию для сохранения JSON
                json_output_dir = None
                if args.output and len(pdf_files_to_process) == 1:
                    # Если указан --output и обрабатывается один файл, используем его
                    output_path = args.output
                    json_output_dir = output_path.parent
                else:
                    # Иначе используем автоматическое определение пути
                    json_output_dir = None  # Будет определено внутри функции
                
                metadata = extract_metadata_from_pdf(
                    pdf_path,
                    model=args.model,
                    temperature=args.temperature,
                    api_key=args.api_key,
                    cache_dir=args.cache_dir,
                    config=config,
                    json_output_dir=json_output_dir
                )
                
                # Если был указан --output и обрабатывается один файл, сохраняем по указанному пути
                if args.output and len(pdf_files_to_process) == 1:
                    output_path = args.output
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_text(
                        json.dumps(metadata, ensure_ascii=False, indent=2),
                        encoding='utf-8'
                    )
                    print(f"\n✅ Метаданные также сохранены по указанному пути: {output_path}")
                
                # Показываем краткую информацию об извлеченных метаданных
                if len(pdf_files_to_process) == 1:
                    print("\n📋 Извлеченные метаданные:")
                    print("-" * 80)
                    for key, value in metadata.items():
                        if value:
                            if isinstance(value, list):
                                print(f"{key}: [{len(value)} элементов]")
                            elif isinstance(value, dict):
                                print(f"{key}: {{ {len(value)} полей }}")
                            else:
                                preview = str(value)[:100]
                                if len(str(value)) > 100:
                                    preview += "..."
                                print(f"{key}: {preview}")
                
                successful += 1
                
            except GPTExtractionError as e:
                print(f"❌ Ошибка при обработке {pdf_path.name}: {e}")
                failed += 1
            except Exception as e:
                print(f"❌ Неожиданная ошибка при обработке {pdf_path.name}: {e}")
                import traceback
                traceback.print_exc()
                failed += 1
        
        # Итоговая статистика
        print("\n" + "=" * 80)
        print("📊 Итоговая статистика:")
        print(f"   ✅ Успешно обработано: {successful}")
        print(f"   ❌ Ошибок: {failed}")
        print(f"   📄 Всего файлов: {len(pdf_files_to_process)}")
        print("=" * 80)
        
        if failed > 0:
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Обработка прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

