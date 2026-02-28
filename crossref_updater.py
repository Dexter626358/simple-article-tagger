from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
try:
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover - fallback when bs4 is unavailable
    BeautifulSoup = None

LOGGER = logging.getLogger(__name__)
API_URL = "https://api.crossref.org/works/{}"
RATE_LIMIT_SECONDS = 1
RETRY_COUNT = 3
RETRY_DELAY_SECONDS = 1


def _get_user_agent() -> str:
    email = os.getenv("CROSSREF_MAILTO") or os.getenv("CROSSREF_EMAIL")
    if not email:
        email = "unknown@example.com"
    return f"word_parser_metadata/1.0 (mailto:{email})"


def _get_message(data: Dict[str, Any]) -> Dict[str, Any]:
    if "message" in data and isinstance(data["message"], dict):
        return data["message"]
    return data


def _first_non_empty(*values: Any) -> Optional[str]:
    for value in values:
        if isinstance(value, str):
            candidate = value.strip()
            if candidate:
                return candidate
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    candidate = item.strip()
                    if candidate:
                        return candidate
    return None


def _extract_author_affiliation(author: Dict[str, Any]) -> str:
    raw_aff = author.get("affiliation")
    if isinstance(raw_aff, list):
        names = []
        for item in raw_aff:
            if isinstance(item, dict):
                name = str(item.get("name") or "").strip()
                if name:
                    names.append(name)
            elif isinstance(item, str):
                name = item.strip()
                if name:
                    names.append(name)
        return "; ".join(names)
    if isinstance(raw_aff, str):
        return raw_aff.strip()
    return ""


def fetch_crossref_data(doi: str) -> Optional[Dict[str, Any]]:
    """
    Fetch Crossref metadata by DOI.
    """
    headers = {"User-Agent": _get_user_agent()}
    url = API_URL.format(doi)

    for attempt in range(1, RETRY_COUNT + 1):
        if attempt > 1:
            time.sleep(RETRY_DELAY_SECONDS)
        time.sleep(RATE_LIMIT_SECONDS)
        try:
            response = requests.get(url, headers=headers, timeout=20)
            if response.status_code != 200:
                LOGGER.error("Crossref error status=%s doi=%s", response.status_code, doi)
                continue
            try:
                payload = response.json()
            except ValueError as exc:
                LOGGER.error("Crossref invalid JSON doi=%s error=%s", doi, exc)
                continue
            return _get_message(payload)
        except requests.RequestException as exc:
            LOGGER.error("Crossref request failed doi=%s error=%s", doi, exc)
            continue
    return None


def extract_abstract(crossref_data: Dict[str, Any]) -> Optional[str]:
    """
    Extract and clean abstract from Crossref response.
    """
    message = _get_message(crossref_data)
    abstract = message.get("abstract")
    if not abstract:
        return None
    try:
        if BeautifulSoup is not None:
            soup = BeautifulSoup(abstract, "html.parser")
            text = soup.get_text(separator="")
        else:
            text = _strip_jats_tags(abstract)
    except Exception:
        text = _strip_jats_tags(abstract)
    return text.strip() or None


def _strip_jats_tags(text: str) -> str:
    import re

    cleaned = re.sub(r"<[^>]+>", " ", text)
    return " ".join(cleaned.replace("\n", " ").split())


def extract_references(crossref_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract references from Crossref response.
    """
    message = _get_message(crossref_data)
    refs = message.get("reference", [])
    if not isinstance(refs, list):
        return []
    result: List[Dict[str, Any]] = []
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        result.append(
            {
                "doi": ref.get("DOI") or ref.get("doi"),
                "author": ref.get("author"),
                "year": ref.get("year"),
                "title": _first_non_empty(ref.get("article-title"), ref.get("article_title"), ref.get("title")),
                "journal": _first_non_empty(ref.get("journal-title"), ref.get("journal_title"), ref.get("journal")),
                "volume": ref.get("volume"),
                "issue": ref.get("issue"),
                "first_page": ref.get("first-page") or ref.get("first_page"),
                "publisher": ref.get("publisher"),
                "isbn": ref.get("ISBN") or ref.get("isbn"),
                "issn": ref.get("ISSN") or ref.get("issn"),
                "series_title": ref.get("series-title") or ref.get("series_title"),
                "volume_title": ref.get("volume-title") or ref.get("volume_title"),
                "edition": ref.get("edition"),
                "key": ref.get("key"),
                "unstructured": ref.get("unstructured"),
            }
        )
    return result


def update_article_by_doi(doi: str) -> Dict[str, Any]:
    """
    Fetch and normalize metadata by DOI.
    """
    data = fetch_crossref_data(doi)
    now = datetime.now(timezone.utc).isoformat()
    if not data:
        return {
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

    title = _first_non_empty(data.get("title"))
    original_title = _first_non_empty(data.get("original-title"))

    journal = None
    if isinstance(data.get("container-title"), list) and data.get("container-title"):
        journal = data["container-title"][0]
    elif isinstance(data.get("container-title"), str):
        journal = data.get("container-title")

    year = None
    for key in ("issued", "published-print", "published-online"):
        date_parts = data.get(key, {}).get("date-parts")
        if isinstance(date_parts, list) and date_parts:
            year = date_parts[0][0]
            break

    authors: List[Dict[str, str]] = []
    raw_authors = data.get("author", [])
    if isinstance(raw_authors, list):
        for author in raw_authors:
            if not isinstance(author, dict):
                continue
            family = str(author.get("family") or "").strip()
            given = str(author.get("given") or "").strip()
            name = " ".join(p for p in [given, family] if p).strip()
            orcid = str(author.get("ORCID") or author.get("orcid") or "").strip()
            affiliation = _extract_author_affiliation(author)
            authors.append(
                {
                    "family": family,
                    "given": given,
                    "name": name,
                    "orcid": orcid,
                    "affiliation": affiliation,
                    "sequence": str(author.get("sequence") or "").strip(),
                }
            )

    return {
        "doi": doi,
        "abstract": extract_abstract(data),
        "references": extract_references(data),
        "title": title,
        "original_title": original_title,
        "authors": authors,
        "year": year,
        "journal": journal,
        "updated_at": now,
        "raw": data,
    }
