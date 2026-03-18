# -*- coding: utf-8 -*-
"""
Подтягивание метаданных статей из ИС «Метафора» (metafora.rcsi.science) по DOI.
Использует metafora_client (вход по логину/паролю) и логику поиска/парсинга из search_publications.
Формат ответа совместим с crossref_updater для кнопки «Подтянуть данные из MTFR» в форме разметки.

Настройка в config.json:
  "mtfr": {
    "base_url": "https://metafora.rcsi.science",
    "login": "",
    "password": ""
  }
Переменные окружения: METAFORA_LOGIN, METAFORA_PASSWORD; опционально METAFORA_BASE_URL.

Если заданы api_url (и опционально api_key) — используется запрос к внешнему API (GET api_url/DOI).
"""

from __future__ import annotations

import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

LOGGER = logging.getLogger(__name__)

# Нормализация названия для поиска: убираем лишние пробелы, типы кавычек/тире для лучшего совпадения на сайте
def _normalize_search_title(title: str) -> str:
    if not title or not isinstance(title, str):
        return ""
    s = title.strip()
    s = re.sub(r"[\u00ad\u200b-\u200f\u2060\ufeff]", "", s)  # невидимые символы
    s = re.sub(r"\s+", " ", s)  # склеить пробелы
    s = s.replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'").replace("\u2019", "'")
    s = s.replace("\u2013", "-").replace("\u2014", "-")  # en-dash, em-dash → дефис
    return s.strip()
RETRY_COUNT = 2
RETRY_DELAY_SECONDS = 1


def _get_config(config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if config is None:
        return {}
    return config.get("mtfr") if isinstance(config.get("mtfr"), dict) else {}


def _get_base_url(config: Optional[Dict[str, Any]]) -> str:
    cfg = _get_config(config)
    url = (cfg.get("base_url") or os.getenv("METAFORA_BASE_URL") or "").strip()
    if url:
        return url.rstrip("/")
    return "https://metafora.rcsi.science"


def _get_metafora_credentials(config: Optional[Dict[str, Any]]) -> Optional[tuple]:
    """Возвращает (login, password) для входа в Метафору или None."""
    cfg = _get_config(config)
    login = (cfg.get("login") or os.getenv("METAFORA_LOGIN") or "").strip()
    password = (cfg.get("password") or os.getenv("METAFORA_PASSWORD") or "").strip()
    if login and password:
        return (login, password)
    return None


def _get_api_url(config: Optional[Dict[str, Any]]) -> Optional[str]:
    url = _get_config(config).get("api_url", "").strip()
    if url:
        return url
    return (os.getenv("MTFR_API_URL") or "").strip() or None


def _get_api_key(config: Optional[Dict[str, Any]]) -> Optional[str]:
    key = _get_config(config).get("api_key", "").strip()
    if key:
        return key
    return (os.getenv("MTFR_API_KEY") or "").strip() or None


def _references_text_to_list(text: str) -> List[str]:
    """Разбивает блок «список литературы» на список строк (по строкам)."""
    if not text or not isinstance(text, str):
        return []
    return [line.strip() for line in text.splitlines() if line.strip()]


def _error_result(error: str, error_message: str) -> Dict[str, Any]:
    """Возвращает словарь-ошибку для передачи в update_article_by_doi и маршрут."""
    return {"error": error, "error_message": error_message}


def _fetch_via_metafora_site(
    doi: str,
    config: Optional[Dict[str, Any]],
    title: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Подтягивает данные через сайт Метафоры: вход по логину/паролю,
    поиск публикации по DOI и/или по названию, парсинг страницы публикации.
    Возвращает словарь с данными (title_ru, title_en, ...) или словарь с ключами error, error_message.
    """
    creds = _get_metafora_credentials(config)
    if not creds:
        LOGGER.warning("Для подтягивания из Метафоры задайте login и password в config.mtfr или METAFORA_LOGIN, METAFORA_PASSWORD")
        return _error_result(
            "no_credentials",
            "Не заданы логин и пароль Метафоры. Укажите mtfr.login и mtfr.password в config.json или переменные METAFORA_LOGIN, METAFORA_PASSWORD.",
        )

    try:
        from metafora_client import MetaforaClient
        from search_publications import (
            search_publications_page,
            parse_publication_links,
            fetch_publication_detail,
            parse_publication_detail,
        )
    except ImportError as e:
        LOGGER.warning("Модули Метафоры недоступны: %s", e)
        return _error_result(
            "import_error",
            "Модули Метафоры недоступны. Убедитесь, что metafora_client.py и search_publications.py находятся в корне проекта (рядом с mtfr_updater.py).",
        )

    base_url = _get_base_url(config)
    client = MetaforaClient(base_url=base_url)
    login, password = creds
    if not client.login(login=login, password=password):
        LOGGER.warning("Не удалось войти в ИС Метафора (проверьте логин/пароль и доступность сайта)")
        return _error_result(
            "login_failed",
            "Не удалось войти в Метафору. Проверьте логин и пароль в config.json (mtfr.login, mtfr.password) и доступность сайта metafora.rcsi.science.",
        )

    filter_doi = (doi or "").strip()
    filter_title = _normalize_search_title(title or "")
    if not filter_doi and not filter_title:
        return _error_result(
            "no_identifier",
            "Укажите DOI или название статьи для поиска в Метафоре.",
        )
    try:
        # Важно: фильтры на странице /publications комбинируются.
        # Если DOI в Метафоре отсутствует/отличается от ожидаемого, поиск по (DOI + title)
        # может дать пустой результат даже при наличии публикации. Поэтому делаем fallback.
        links: List[Dict[str, str]] = []

        # 1) Пробуем самый строгий вариант, если заданы оба параметра.
        if filter_doi or filter_title:
            html = search_publications_page(client, filter_doi=filter_doi, filter_title=filter_title)
            links = parse_publication_links(html, base_url)

        # 2) Если не нашли по (DOI + title), пробуем только DOI (частый случай: title в форме обрезан).
        if not links and filter_doi and filter_title:
            html = search_publications_page(client, filter_doi=filter_doi, filter_title="")
            links = parse_publication_links(html, base_url)

        # 3) Если не нашли по DOI, пробуем только title (частый случай: DOI в Метафоре отсутствует/иной).
        if not links and filter_title and filter_doi:
            html = search_publications_page(client, filter_doi="", filter_title=filter_title)
            links = parse_publication_links(html, base_url)
    except Exception as e:
        LOGGER.warning("Ошибка поиска по DOI=%s title=%s: %s", filter_doi, filter_title[:50] if filter_title else "", e)
        return _error_result(
            "request_error",
            f"Ошибка при запросе к Метафоре: {e}. Проверьте доступность сайта и DOI/название.",
        )

    # Если по полному названию не нашли — пробуем по началу названия (первые слова), часто опечатки в конце
    if not links and filter_title:
        short_title = " ".join(filter_title.split()[:12]).strip()  # первые 12 слов
        if len(short_title) > 20 and short_title != filter_title:
            try:
                html2 = search_publications_page(client, filter_doi="", filter_title=short_title)
                links = parse_publication_links(html2, base_url)
                if links:
                    LOGGER.info("Публикация найдена по укороченному названию (первые слова)")
            except Exception:
                pass
    if not links and filter_title:
        # Ещё попытка: по первым 70 символам (на случай обрезанного заголовка в форме)
        short_title = filter_title[:70].strip()
        if len(short_title) > 25 and short_title != filter_title:
            try:
                html2 = search_publications_page(client, filter_doi="", filter_title=short_title)
                links = parse_publication_links(html2, base_url)
                if links:
                    LOGGER.info("Публикация найдена по началу названия (70 символов)")
            except Exception:
                pass

    if not links:
        LOGGER.info("Публикация по DOI=%s title=%s не найдена в Метафоре", filter_doi, filter_title[:50] if filter_title else "")
        return _error_result(
            "not_found",
            "Публикация не найдена в Метафоре. Проверьте DOI или название (попробуйте скопировать точное название со страницы Метафоры).",
        )

    pub = links[0]
    title_from_list = (pub.get("title") or "").strip()  # заголовок со страницы списка публикаций
    try:
        detail_html = fetch_publication_detail(client, pub["url"])
        detail = parse_publication_detail(detail_html)
    except Exception as e:
        LOGGER.warning("Ошибка загрузки страницы публикации: %s", e)
        return _error_result(
            "request_error",
            f"Ошибка при загрузке страницы публикации: {e}.",
        )

    return {
        "title_ru": detail.get("title_ru") or "",
        "title_en": detail.get("title_en") or "",
        "abstract_ru": detail.get("abstract_ru") or "",
        "abstract_en": detail.get("abstract_en") or "",
        "references_ru": detail.get("references_ru") or "",
        "references_en": detail.get("references_en") or "",
        "title_from_list": title_from_list,  # подстановка, если парсер карточки ничего не нашёл
    }


def _fetch_via_api(doi: str, config: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Запрос к внешнему MTFR API (GET api_url/DOI). Используется при заданном mtfr.api_url."""
    api_url = _get_api_url(config)
    if not api_url:
        return None

    api_key = _get_api_key(config)
    cfg = _get_config(config)
    login = (cfg.get("login") or os.getenv("METAFORA_LOGIN") or "").strip()
    password = (cfg.get("password") or os.getenv("METAFORA_PASSWORD") or "").strip()
    auth = (login, password) if login and password else None
    headers = {"Accept": "application/json", "User-Agent": "word_parser_metadata/1.0"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    url = api_url.rstrip("/") + "/" + requests.utils.quote(doi, safe="")

    for attempt in range(1, RETRY_COUNT + 1):
        if attempt > 1:
            time.sleep(RETRY_DELAY_SECONDS)
        try:
            response = requests.get(url, headers=headers, auth=auth, timeout=20)
            if response.status_code != 200:
                LOGGER.warning("MTFR API HTTP %s doi=%s", response.status_code, doi)
                return None
            return response.json()
        except requests.RequestException as exc:
            LOGGER.warning("MTFR API request failed doi=%s error=%s", doi, exc)
        except ValueError:
            LOGGER.warning("MTFR API invalid JSON doi=%s", doi)
    return None


def fetch_mtfr_data(
    doi: str,
    config: Optional[Dict[str, Any]] = None,
    title: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Запрашивает метаданные по DOI и/или по названию статьи.
    Сначала пробует подтянуть через сайт Метафоры (если заданы login/password),
    иначе — через mtfr.api_url, если задан (только по DOI).
    Возвращает нормализованный словарь с данными или словарь с ключами error, error_message.
    """
    doi = (doi or "").strip()
    title = (title or "").strip()
    if not doi and not title:
        return _error_result(
            "no_identifier",
            "Укажите DOI или название статьи для поиска в Метафоре.",
        )

    # 1) Метафора: вход по логину/паролю и парсинг страниц (по DOI и/или по названию)
    metafora_result = _fetch_via_metafora_site(doi, config, title=title)
    if metafora_result is not None:
        if metafora_result.get("error"):
            return metafora_result
        return metafora_result

    # 2) Внешний API по api_url (только по DOI)
    if doi:
        raw = _fetch_via_api(doi, config)
        if raw is not None:
            return raw

    return _error_result(
        "unavailable",
        "Не удалось получить данные из MTFR. Публикация не найдена по DOI/названию или нет доступа к Метафоре (проверьте логин и пароль в config.json).",
    )


def _normalize_author(raw: Any) -> Dict[str, str]:
    if not isinstance(raw, dict):
        return {"family": "", "given": "", "name": "", "orcid": "", "affiliation": ""}
    family = str(raw.get("family") or raw.get("surname") or "").strip()
    given = str(raw.get("given") or raw.get("initials") or "").strip()
    name = str(raw.get("name") or "").strip() or " ".join(p for p in [given, family] if p).strip()
    orcid = str(raw.get("orcid") or raw.get("ORCID") or "").strip()
    aff = raw.get("affiliation")
    if isinstance(aff, list):
        affiliation = "; ".join(str(x.get("name", x) if isinstance(x, dict) else x).strip() for x in aff).strip()
    else:
        affiliation = str(aff or "").strip()
    return {
        "family": family,
        "given": given,
        "name": name,
        "orcid": orcid,
        "affiliation": affiliation,
        "sequence": str(raw.get("sequence", "")).strip(),
    }


def _extract_references_list(data: Dict[str, Any]) -> List[str]:
    refs = data.get("references") or data.get("reference") or data.get("references_list")
    if not isinstance(refs, list):
        return []
    result = []
    for ref in refs:
        if isinstance(ref, str):
            result.append(ref.strip())
        elif isinstance(ref, dict):
            unstructured = (ref.get("unstructured") or ref.get("text") or "").strip()
            if unstructured:
                result.append(unstructured)
            else:
                parts = [
                    ref.get("author"),
                    ref.get("title"),
                    ref.get("journal"),
                    ref.get("year"),
                    ref.get("volume"),
                    ref.get("first_page"),
                    ref.get("doi"),
                ]
                line = ". ".join(str(p).strip() for p in parts if p).strip()
                if line:
                    result.append(line)
    return result


def update_article_by_doi(
    doi: str,
    config: Optional[Dict[str, Any]] = None,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Загружает метаданные по DOI и/или по названию статьи из Метафоры (или внешнего MTFR API)
    и приводит к формату, совместимому с формой разметки (как crossref_updater).
    При отсутствии DOI используется название статьи для поиска на сайте Метафоры.
    Возвращает словарь: doi, title, original_title, abstract, authors, references, raw.
    """
    doi = (doi or "").strip()
    title = (title or "").strip()
    if not doi and not title:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "doi": "",
            "abstract": None,
            "references": [],
            "title": None,
            "original_title": None,
            "authors": [],
            "year": None,
            "journal": None,
            "updated_at": now,
            "raw": None,
            "error": "no_identifier",
            "error_message": "Укажите DOI или название статьи для поиска в Метафоре.",
        }

    now = datetime.now(timezone.utc).isoformat()
    empty = {
        "doi": doi,
        "abstract": None,
        "references": [],
        "title": None,
        "original_title": None,
        "authors": [],
        "year": None,
        "journal": None,
        "updated_at": now,
        "raw": None,
    }

    data = fetch_mtfr_data(doi, config, title=title)
    if not data:
        return empty
    if data.get("error"):
        return {
            **empty,
            "error": data["error"],
            "error_message": data.get("error_message", "Не удалось получить данные из MTFR."),
        }

    # Ответ от сайта Метафоры (parse_publication_detail) — сохраняем RU/EN раздельно для полей формы
    abstract_ru: Optional[str] = None
    abstract_en: Optional[str] = None
    references_ru_list: Optional[List[str]] = None
    references_en_list: Optional[List[str]] = None

    if "title_ru" in data or "title_en" in data or "abstract_ru" in data or "references_ru" in data:
        title_ru = (data.get("title_ru") or "").strip()
        title_en = (data.get("title_en") or "").strip()
        abstract_ru = (data.get("abstract_ru") or "").strip() or None
        abstract_en = (data.get("abstract_en") or "").strip() or None
        refs_ru = _references_text_to_list(data.get("references_ru") or "")
        refs_en = _references_text_to_list(data.get("references_en") or "")
        references_ru_list = refs_ru if refs_ru else None
        references_en_list = refs_en if refs_en else None
        title_from_list = (data.get("title_from_list") or "").strip()
        if not title_ru and not title_en and title_from_list:
            title_ru = title_from_list
        title = title_en or None
        original_title = title_ru or None
        abstract = abstract_ru or abstract_en or None
        references = refs_ru if refs_ru else refs_en
        authors = []
        raw_for_state = data
    else:
        # Ответ от внешнего API (JSON)
        title = (data.get("title") or data.get("title_en") or "").strip() or None
        original_title = (data.get("original_title") or data.get("title_ru") or data.get("title")) or None
        if isinstance(original_title, str):
            original_title = original_title.strip() or None
        abstract = (data.get("abstract") or data.get("annotation") or data.get("description") or "").strip() or None
        authors = []
        raw_authors = data.get("authors") or data.get("author") or []
        if isinstance(raw_authors, list):
            for a in raw_authors:
                authors.append(_normalize_author(a))
        references = _extract_references_list(data)
        raw_for_state = data

    return {
        "doi": data.get("doi") if isinstance(data.get("doi"), str) else doi,
        "abstract": abstract,
        "references": references,
        "title": title,
        "original_title": original_title,
        "authors": authors,
        "year": data.get("year") if "year" in data else None,
        "journal": data.get("journal") or data.get("container_title"),
        "updated_at": now,
        "raw": raw_for_state,
        "abstract_ru": abstract_ru,
        "abstract_en": abstract_en,
        "references_ru": references_ru_list,
        "references_en": references_en_list,
    }
