from __future__ import annotations

import json
import logging
import re
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import quote, urljoin, urlparse

import requests

try:
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover
    BeautifulSoup = None

LOGGER = logging.getLogger(__name__)
REQUEST_TIMEOUT = 20
MAX_SEARCH_CANDIDATES = 5
ARTICLE_TYPES = {"article", "scholarlyarticle", "creativework", "newsarticle"}


def _norm_space(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _looks_cyrillic(value: str) -> bool:
    return bool(re.search(r"[А-Яа-яЁё]", value or ""))


def _first_non_empty(*values: Any) -> str:
    for value in values:
        if isinstance(value, list):
            for item in value:
                text = _norm_space(item)
                if text:
                    return text
        else:
            text = _norm_space(value)
            if text:
                return text
    return ""


def _meta_values(soup, *names: str) -> list[str]:
    if soup is None:
        return []
    wanted = {name.lower() for name in names if name}
    result: list[str] = []
    for tag in soup.find_all("meta"):
        key = _norm_space(
            tag.get("name")
            or tag.get("property")
            or tag.get("itemprop")
            or tag.get("http-equiv")
        ).lower()
        if key not in wanted:
            continue
        content = _norm_space(tag.get("content"))
        if content:
            result.append(content)
    return result


def _strip_tags(value: str) -> str:
    if not value:
        return ""
    if BeautifulSoup is not None:
        try:
            return _norm_space(BeautifulSoup(value, "html.parser").get_text(" ", strip=True))
        except Exception:
            pass
    return _norm_space(re.sub(r"<[^>]+>", " ", value))


def _safe_json_loads(value: str) -> Any:
    try:
        return json.loads(value)
    except Exception:
        return None


def _iter_json_ld_nodes(node: Any):
    if isinstance(node, dict):
        yield node
        graph = node.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                yield from _iter_json_ld_nodes(item)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_json_ld_nodes(item)


def _extract_json_ld_article(soup):
    if soup is None:
        return None
    for script in soup.find_all("script", attrs={"type": re.compile("ld\\+json", re.I)}):
        raw = script.string or script.get_text() or ""
        data = _safe_json_loads(raw.strip())
        if data is None:
            continue
        for node in _iter_json_ld_nodes(data):
            raw_type = node.get("@type")
            types = raw_type if isinstance(raw_type, list) else [raw_type]
            normalized = {_norm_space(item).lower() for item in types if item}
            if normalized & ARTICLE_TYPES:
                return node
    return None


def _find_jats_url_from_html(html: str, base_url: str) -> str:
    if BeautifulSoup is None:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    # Common patterns: explicit "jats" download action, or alternate link.
    for tag in soup.find_all("a", href=True):
        href = tag.get("href", "")
        text = _norm_space(tag.get_text(" ", strip=True)).lower()
        if "jats" in href.lower() or "jats" in text:
            return urljoin(base_url, href)
    for link in soup.find_all("link", href=True):
        link_type = _norm_space(link.get("type")).lower()
        if "xml" in link_type and "jats" in _norm_space(link.get("title")).lower():
            return urljoin(base_url, link.get("href", ""))
    meta_jats = None
    for meta in soup.find_all("meta", attrs={"name": re.compile("citation_xml_url", re.I)}):
        meta_jats = meta.get("content")
        if meta_jats:
            return urljoin(base_url, meta_jats)
    return ""


def _strip_xml_ns(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _iter_text(node: ET.Element) -> str:
    parts = []
    if node.text:
        parts.append(node.text)
    for child in node:
        parts.append(_iter_text(child))
        if child.tail:
            parts.append(child.tail)
    return _norm_space(" ".join(p for p in parts if p))


def _normalize_reference_text(value: str) -> str:
    # Collapse line breaks and excessive whitespace inside a single reference.
    return _norm_space(value)


def _normalize_reference_list(values: list[str]) -> list[str]:
    out: list[str] = []
    for item in values or []:
        cleaned = _normalize_reference_text(item)
        if cleaned:
            out.append(cleaned)
    return out


def _xml_lang(node: ET.Element) -> str:
    return _norm_space(node.attrib.get("{http://www.w3.org/XML/1998/namespace}lang"))


def _extract_metadata_from_jats(xml_text: str) -> dict[str, Any]:
    root = ET.fromstring(xml_text)
    # Titles
    title = ""
    original_title = ""
    for elem in root.iter():
        tag = _strip_xml_ns(elem.tag)
        if tag == "article-title":
            text = _iter_text(elem)
            if not text:
                continue
            lang = _xml_lang(elem).lower()
            if lang.startswith("ru"):
                if not original_title:
                    original_title = text
            elif lang.startswith("en"):
                if not title:
                    title = text
            else:
                if not original_title and _looks_cyrillic(text):
                    original_title = text
                elif not title:
                    title = text
        elif tag == "trans-title":
            text = _iter_text(elem)
            if not text:
                continue
            lang = _xml_lang(elem).lower()
            if lang.startswith("en") and not title:
                title = text
            elif lang.startswith("ru") and not original_title:
                original_title = text

    # Abstracts
    abstract_ru = ""
    abstract_en = ""
    for elem in root.iter():
        tag = _strip_xml_ns(elem.tag)
        if tag in ("abstract", "trans-abstract"):
            text = _iter_text(elem)
            if not text:
                continue
            lang = _xml_lang(elem).lower()
            if lang.startswith("ru") and not abstract_ru:
                abstract_ru = text
            elif lang.startswith("en") and not abstract_en:
                abstract_en = text
            elif not lang and not abstract_en and not _looks_cyrillic(text):
                abstract_en = text
            elif not lang and not abstract_ru and _looks_cyrillic(text):
                abstract_ru = text

    # References
    references_ru: list[str] = []
    references_en: list[str] = []
    refs_fallback: list[str] = []
    for elem in root.iter():
        if _strip_xml_ns(elem.tag) != "ref-list":
            continue
        for ref in elem.iter():
            if _strip_xml_ns(ref.tag) != "ref":
                continue
            # JATS often uses citation-alternatives with lang-specific mixed-citation.
            found_langged = False
            for child in ref.iter():
                if _strip_xml_ns(child.tag) != "mixed-citation":
                    continue
                text = _iter_text(child)
                if not text:
                    continue
                lang = _xml_lang(child).lower()
                if lang.startswith("ru"):
                    references_ru.append(_normalize_reference_text(text))
                    found_langged = True
                elif lang.startswith("en"):
                    references_en.append(_normalize_reference_text(text))
                    found_langged = True
            if found_langged:
                continue
            # Fallback to element-citation or mixed-citation without lang
            text = ""
            for child in ref.iter():
                if _strip_xml_ns(child.tag) in ("mixed-citation", "element-citation"):
                    text = _iter_text(child)
                    if text:
                        break
            if not text:
                text = _iter_text(ref)
            if text:
                refs_fallback.append(_normalize_reference_text(text))
        break

    references: list[str] = []
    if references_ru or references_en:
        references = references_en or references_ru
    elif refs_fallback:
        references = refs_fallback

    return {
        "title": title,
        "original_title": original_title,
        "abstract": _first_non_empty(abstract_en, abstract_ru),
        "abstract_ru": abstract_ru,
        "abstract_en": abstract_en,
        "references": references,
        "references_ru": references_ru,
        "references_en": references_en,
    }


def _extract_section_text(soup, headings: list[str], multiline: bool = False) -> str:
    if soup is None:
        return ""
    target_names = {"h1", "h2", "h3", "h4", "h5", "h6", "strong", "b", "dt"}
    wanted = [h.lower() for h in headings]
    for tag in soup.find_all(list(target_names)):
        tag_text = _norm_space(tag.get_text(" ", strip=True)).rstrip(":").lower()
        if not any(h in tag_text for h in wanted):
            continue
        parts: list[str] = []
        for sibling in tag.find_next_siblings():
            sibling_text = _norm_space(sibling.get_text(" ", strip=True))
            if not sibling_text:
                continue
            if sibling.name in target_names:
                next_head = sibling_text.rstrip(":").lower()
                if any(h in next_head for h in wanted):
                    continue
                if len(parts) > 0:
                    break
            parts.append(sibling_text)
        if parts:
            return "\n".join(parts) if multiline else " ".join(parts)
    return ""


def _split_keywords(value: str) -> str:
    text = _norm_space(value).strip(" ,;.")
    if not text:
        return ""
    text = re.sub(r"^(keywords|key words|ключевые слова)\s*[:\-]\s*", "", text, flags=re.I)
    parts = [item.strip(" ,;.") for item in re.split(r"[;,]\s*|\s{2,}", text) if item.strip(" ,;.")]
    if len(parts) <= 1:
        return text
    return "; ".join(parts)


def _split_references(value: str) -> list[str]:
    text = str(value or "").replace("\r", "\n")
    lines = [_norm_space(line) for line in text.split("\n")]
    lines = [line for line in lines if line]
    if not lines:
        return []
    if len(lines) == 1:
        parts = re.split(r"\s(?=\[\d+\]|\d+\.)", lines[0])
        split_lines = [_norm_space(item) for item in parts if _norm_space(item)]
        if len(split_lines) > 1:
            lines = split_lines
    cleaned = [re.sub(r"^\s*(\[\d+\]|\d+\.)\s*", "", line).strip() for line in lines]
    return [line for line in cleaned if line]


def _parse_pages(first_page: str, last_page: str, pages: str) -> str:
    first_clean = _norm_space(first_page)
    last_clean = _norm_space(last_page)
    pages_clean = _norm_space(pages)
    if first_clean and last_clean:
        return f"{first_clean}-{last_clean}"
    if pages_clean:
        match = re.search(r"\b(\d+)\s*[-–—]\s*(\d+)\b", pages_clean)
        if match:
            return f"{match.group(1)}-{match.group(2)}"
        if re.fullmatch(r"\d+", pages_clean):
            return pages_clean
    return ""


def _split_person_name(name: str) -> tuple[str, str]:
    clean = _norm_space(name)
    if not clean:
        return "", ""
    if "," in clean:
        left, right = [part.strip() for part in clean.split(",", 1)]
        return left, right
    parts = clean.split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[-1], " ".join(parts[:-1])


def _authors_from_meta(soup) -> list[dict[str, str]]:
    names = _meta_values(soup, "citation_author", "dc.creator", "author")
    affiliations = _meta_values(soup, "citation_author_institution", "citation_author_affiliation")
    orcids = _meta_values(soup, "citation_author_orcid")
    if not names:
        return []
    authors = []
    for index, name in enumerate(names):
        family, given = _split_person_name(name)
        authors.append(
            {
                "family": family,
                "given": given,
                "name": _norm_space(name),
                "affiliation": affiliations[index] if index < len(affiliations) else "",
                "orcid": re.sub(r"^https?://orcid\.org/", "", orcids[index], flags=re.I) if index < len(orcids) else "",
            }
        )
    return authors


def _authors_from_json_ld(article: dict[str, Any] | None) -> list[dict[str, str]]:
    if not isinstance(article, dict):
        return []
    raw_authors = article.get("author")
    if isinstance(raw_authors, dict):
        raw_authors = [raw_authors]
    if not isinstance(raw_authors, list):
        return []
    authors = []
    for item in raw_authors:
        if isinstance(item, str):
            family, given = _split_person_name(item)
            authors.append({"family": family, "given": given, "name": _norm_space(item), "affiliation": "", "orcid": ""})
            continue
        if not isinstance(item, dict):
            continue
        name = _first_non_empty(item.get("name"))
        family = _first_non_empty(item.get("familyName"))
        given = _first_non_empty(item.get("givenName"))
        if not family and name:
            family, given = _split_person_name(name)
        affiliation = item.get("affiliation")
        if isinstance(affiliation, list):
            aff_text = "; ".join(_first_non_empty(v.get("name") if isinstance(v, dict) else v) for v in affiliation).strip("; ")
        elif isinstance(affiliation, dict):
            aff_text = _first_non_empty(affiliation.get("name"))
        else:
            aff_text = _norm_space(affiliation)
        authors.append(
            {
                "family": family,
                "given": given,
                "name": name or " ".join(part for part in (given, family) if part),
                "affiliation": aff_text,
                "orcid": re.sub(r"^https?://orcid\.org/", "", _first_non_empty(item.get("identifier"), item.get("orcid")), flags=re.I),
            }
        )
    return authors


def _extract_metadata_from_html(html: str, source_url: str) -> dict[str, Any]:
    if BeautifulSoup is None:
        raise RuntimeError("BeautifulSoup is required for RAS site parsing.")

    soup = BeautifulSoup(html, "html.parser")
    article_ld = _extract_json_ld_article(soup)

    def _find_text_by_class(patterns: list[str], lang: str = "") -> str:
        for pat in patterns:
            for tag in soup.find_all(class_=re.compile(pat, re.I)):
                if lang:
                    tag_lang = _norm_space(tag.get("lang") or tag.get("xml:lang") or "").lower()
                    if tag_lang and not tag_lang.startswith(lang.lower()):
                        continue
                text = _norm_space(tag.get_text(" ", strip=True))
                if text:
                    return text
        return ""

    # Bibliography lists are often clean in HTML; prefer explicit list items when present.
    references_ru = []
    references_en = []
    bibliography_used = False
    bibliography_block = soup.find(id="articleBibliography") or soup.find(class_="article-bibliography")
    if bibliography_block:
        list_items = bibliography_block.find_all("li")
        if list_items:
            items = [
                _normalize_reference_text(li.get_text(separator=" ", strip=True))
                for li in list_items
                if _normalize_reference_text(li.get_text(separator=" ", strip=True))
            ]
            heading = _norm_space(
                (bibliography_block.find(["h1", "h2", "h3", "h4"]) or "").get_text(" ", strip=True)
                if bibliography_block.find(["h1", "h2", "h3", "h4"]) else ""
            ).lower()
            is_en_page = "sl=en" in (urlparse(source_url).query or "").lower()
            if "references" in heading or is_en_page:
                references_en = items
            else:
                references_ru = items
            bibliography_used = True

    raw_title = _first_non_empty(
        _meta_values(soup, "citation_title"),
        article_ld.get("headline") if isinstance(article_ld, dict) else "",
        article_ld.get("name") if isinstance(article_ld, dict) else "",
        _meta_values(soup, "og:title", "twitter:title", "dc.title"),
        soup.title.get_text(" ", strip=True) if soup.title else "",
        soup.find("h1").get_text(" ", strip=True) if soup.find("h1") else "",
    )
    raw_title = re.sub(r"\s*[|¦]\s*[^|¦]+$", "", raw_title).strip()

    title_en_html = _first_non_empty(
        _meta_values(soup, "citation_title_en"),
        _find_text_by_class(["title.*en", "article-title.*en", "trans-title", "title-translate"], lang="en"),
    )

    raw_abstract = _first_non_empty(
        _meta_values(soup, "citation_abstract", "description", "og:description", "dc.description"),
        article_ld.get("description") if isinstance(article_ld, dict) else "",
    )
    abstract_ru = _extract_section_text(soup, ["аннотация", "резюме"])
    abstract_en = _first_non_empty(
        _extract_section_text(soup, ["abstract", "summary"]),
        _find_text_by_class(["abstract.*en", "article-abstract.*en", "trans-abstract"], lang="en"),
    )
    if not abstract_ru and raw_abstract and _looks_cyrillic(raw_abstract):
        abstract_ru = _strip_tags(raw_abstract)
    if not abstract_en and raw_abstract and not _looks_cyrillic(raw_abstract):
        abstract_en = _strip_tags(raw_abstract)
    abstract = _first_non_empty(abstract_en, abstract_ru, _strip_tags(raw_abstract))

    keywords_meta = _first_non_empty(_meta_values(soup, "citation_keywords", "keywords", "news_keywords"))
    keywords_ru = _split_keywords(_extract_section_text(soup, ["ключевые слова", "ключевые слова и словосочетания"]) or (keywords_meta if _looks_cyrillic(keywords_meta) else ""))
    keywords_en = _split_keywords(_extract_section_text(soup, ["keywords", "key words"]) or (keywords_meta if keywords_meta and not _looks_cyrillic(keywords_meta) else ""))

    # RU bibliography should not match the separate English "References" section.
    if not references_ru and not bibliography_used:
        references_ru = _split_references(_extract_section_text(soup, ["список литературы", "литература", "библиография", "источники"], multiline=True))
        references_ru = _normalize_reference_list(references_ru)
    if not references_en and not bibliography_used:
        references_en = _split_references(_extract_section_text(soup, ["references", "bibliography"], multiline=True))
        references_en = _normalize_reference_list(references_en)
    meta_refs = _meta_values(soup, "citation_reference")
    references = references_en or references_ru or [_normalize_reference_text(_strip_tags(item)) for item in meta_refs if _normalize_reference_text(_strip_tags(item))]

    first_page = _first_non_empty(_meta_values(soup, "citation_firstpage"))
    last_page = _first_non_empty(_meta_values(soup, "citation_lastpage"))
    pages = _parse_pages(first_page, last_page, _first_non_empty(_meta_values(soup, "citation_pages")))

    doi = _first_non_empty(
        _meta_values(soup, "citation_doi"),
        _meta_values(soup, "dc.identifier"),
        article_ld.get("identifier") if isinstance(article_ld, dict) else "",
    )
    doi = re.sub(r"^(doi:\s*|https?://doi\.org/)", "", doi, flags=re.I).strip()
    doi_match = re.search(r"10\.\d{4,9}/\S+", doi, re.I)
    if doi_match:
        doi = doi_match.group(0).rstrip(").,;")

    authors = _authors_from_meta(soup) or _authors_from_json_ld(article_ld)

    title = ""
    original_title = ""
    if raw_title:
        if _looks_cyrillic(raw_title):
            original_title = raw_title
        else:
            title = raw_title
    if title_en_html and not title:
        title = title_en_html

    return {
        "doi": doi,
        "title": title,
        "original_title": original_title,
        "abstract": abstract,
        "abstract_ru": abstract_ru,
        "abstract_en": abstract_en,
        "keywords": keywords_ru,
        "keywords_en": keywords_en,
        "references": references,
        "references_ru": references_ru,
        "references_en": references_en,
        "pages": pages,
        "authors": authors,
        "source_url": source_url,
    }


def _fetch_html(session: requests.Session, url: str, params: dict[str, str] | None = None) -> tuple[str, str]:
    response = session.get(url, params=params, timeout=REQUEST_TIMEOUT, allow_redirects=True)
    response.raise_for_status()
    response.encoding = response.encoding or response.apparent_encoding or "utf-8"
    return response.text, response.url


def _with_lang_param(url: str, lang: str = "en") -> str:
    parsed = urlparse(url)
    query = parsed.query
    if "sl=" in query:
        query = re.sub(r"(?:^|&)(sl=)[^&]*", f"\\1{lang}", query)
    else:
        query = f"{query}&sl={lang}" if query else f"sl={lang}"
    return parsed._replace(query=query).geturl()


def _resolve_doi(session: requests.Session, doi: str) -> tuple[str, str]:
    doi_url = f"https://doi.org/{quote(doi, safe='/')}"
    return _fetch_html(session, doi_url)


def _normalize_doi_value(doi: str) -> str:
    value = _norm_space(doi)
    value = re.sub(r"^(doi:\s*|https?://doi\.org/)", "", value, flags=re.I).strip()
    value = value.rstrip(").,;")
    return value


def _candidate_article_urls_from_doi(journal_url: str, doi: str) -> list[str]:
    """
    RAS journal sites sometimes use article URLs derived from DOI suffix.

    Example:
      DOI: 10.1134/S2949179725040058
      URL: https://geopaleoras.ru/s2949179725040058-1/
    """
    normalized = _normalize_doi_value(doi)
    if "/" not in normalized:
        return []
    _prefix, suffix = normalized.split("/", 1)
    suffix = suffix.strip()
    if not suffix:
        return []
    token = suffix.lower()
    if re.search(r"-\d+$", token):
        # DOI already contains a site-like suffix such as "...-1"
        candidates = [
            urljoin(journal_url.rstrip("/") + "/", f"{token}/"),
        ]
    else:
        candidates = [
            urljoin(journal_url.rstrip("/") + "/", f"{token}-1/"),
            urljoin(journal_url.rstrip("/") + "/", f"{token}/"),
        ]
    out: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


# Override to avoid source/console encoding issues in older definition above.
def _looks_cyrillic(value: str) -> bool:  # type: ignore[no-redef]
    return bool(re.search(r"[\u0400-\u04FF]", value or ""))


def _parse_search_results(search_html: str, base_url: str, title: str) -> list[str]:
    if BeautifulSoup is None:
        return []
    soup = BeautifulSoup(search_html, "html.parser")
    base_host = urlparse(base_url).netloc.lower()
    title_norm = _norm_space(title).lower()
    ranked: list[tuple[int, str]] = []
    seen: set[str] = set()
    for link in soup.find_all("a", href=True):
        href = link.get("href", "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        candidate = urljoin(base_url, href)
        parsed = urlparse(candidate)
        if parsed.netloc.lower() != base_host:
            continue
        if candidate in seen:
            continue
        path = parsed.path.lower()
        if any(skip in path for skip in ("/wp-content/", "/tag/", "/category/", "/author/", "/feed")):
            continue
        anchor_text = _norm_space(link.get_text(" ", strip=True))
        if len(anchor_text) < 12:
            continue
        score = 0
        anchor_norm = anchor_text.lower()
        if title_norm and title_norm == anchor_norm:
            score += 5
        if title_norm and title_norm in anchor_norm:
            score += 4
        if title_norm and anchor_norm in title_norm and len(anchor_norm) > 24:
            score += 2
        if re.search(r"/20\d{2}/", path):
            score += 1
        if score <= 0:
            continue
        seen.add(candidate)
        ranked.append((score, candidate))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [url for _, url in ranked[:MAX_SEARCH_CANDIDATES]]


def _score_metadata(metadata: dict[str, Any], requested_title: str, requested_doi: str) -> int:
    score = 0
    title_norm = _norm_space(requested_title).lower()
    doi_norm = _norm_space(requested_doi).lower()
    extracted_title = _norm_space(metadata.get("title") or metadata.get("original_title")).lower()
    extracted_doi = _norm_space(metadata.get("doi")).lower()
    if doi_norm and extracted_doi == doi_norm:
        score += 10
    if title_norm and extracted_title == title_norm:
        score += 8
    if title_norm and title_norm in extracted_title:
        score += 5
    if metadata.get("abstract_ru") or metadata.get("abstract_en") or metadata.get("abstract"):
        score += 2
    if metadata.get("references") or metadata.get("references_ru") or metadata.get("references_en"):
        score += 2
    if metadata.get("pages"):
        score += 1
    return score


def update_article_from_ras_site(
    doi: str,
    journal_url: str,
    title: str = "",
    journal_issn: str = "",
    journal_name: str = "",
) -> dict[str, Any]:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "word_parser_metadata/1.0 (+RAS-site-updater)",
            "Accept-Language": "ru,en;q=0.9",
        }
    )
    raw: dict[str, Any] = {
        "journal_url": journal_url,
        "journal_issn": journal_issn,
        "journal_name": journal_name,
        "doi": doi,
        "requested_title": title,
    }

    try:
        best_metadata: dict[str, Any] | None = None
        best_score = -1
        best_source = ""

        if doi:
            # 0) Try journal-site URL derived from DOI suffix (fast path).
            direct_candidates = _candidate_article_urls_from_doi(journal_url, doi)
            if direct_candidates:
                raw["direct_url_candidates"] = direct_candidates
            for candidate_url in direct_candidates:
                try:
                    html, resolved_url = _fetch_html(session, candidate_url)
                    en_html = ""
                    try:
                        en_html, _en_url = _fetch_html(session, _with_lang_param(resolved_url, "en"))
                    except Exception as en_exc:
                        raw.setdefault("en_page_errors", []).append({"url": resolved_url, "error": str(en_exc)})
                    jats_url = _find_jats_url_from_html(html, resolved_url)
                    if jats_url:
                        try:
                            jats_xml, _jats_final = _fetch_html(session, jats_url)
                            jats_metadata = _extract_metadata_from_jats(jats_xml)
                            jats_metadata["source_url"] = jats_url
                            score = _score_metadata(jats_metadata, title, doi) + 3
                            if score > best_score:
                                best_metadata = jats_metadata
                                best_score = score
                                best_source = "jats"
                                raw["jats_url"] = jats_url
                        except Exception as jats_exc:
                            raw.setdefault("jats_errors", []).append({"url": jats_url, "error": str(jats_exc)})
                    metadata = _extract_metadata_from_html(html, resolved_url)
                    if en_html:
                        en_metadata = _extract_metadata_from_html(en_html, _with_lang_param(resolved_url, "en"))
                        if not _norm_space(metadata.get("title")) and _norm_space(en_metadata.get("title")):
                            metadata["title"] = en_metadata.get("title")
                        if not _norm_space(metadata.get("abstract_en")) and _norm_space(en_metadata.get("abstract_en")):
                            metadata["abstract_en"] = en_metadata.get("abstract_en")
                        if not _norm_space(metadata.get("abstract")) and _norm_space(en_metadata.get("abstract_en")):
                            metadata["abstract"] = en_metadata.get("abstract_en")
                        if not metadata.get("references_en") and en_metadata.get("references_en"):
                            metadata["references_en"] = en_metadata.get("references_en")
                    score = _score_metadata(metadata, title, doi)
                    if score > best_score:
                        best_metadata = metadata
                        best_score = score
                        if best_source != "jats":
                            best_source = "html"
                except Exception as exc:
                    raw.setdefault("direct_url_errors", []).append({"url": candidate_url, "error": str(exc)})

        if doi and best_score < 10:
            try:
                html, final_url = _resolve_doi(session, doi)
                raw["doi_resolved_url"] = final_url
                en_html = ""
                try:
                    en_html, _en_url = _fetch_html(session, _with_lang_param(final_url, "en"))
                except Exception as en_exc:
                    raw.setdefault("en_page_errors", []).append({"url": final_url, "error": str(en_exc)})
                jats_url = _find_jats_url_from_html(html, final_url)
                if jats_url:
                    try:
                        jats_xml, _jats_final = _fetch_html(session, jats_url)
                        jats_metadata = _extract_metadata_from_jats(jats_xml)
                        jats_metadata["source_url"] = jats_url
                        score = _score_metadata(jats_metadata, title, doi) + 3
                        if score > best_score:
                            best_metadata = jats_metadata
                            best_score = score
                            best_source = "jats"
                            raw["jats_url"] = jats_url
                    except Exception as jats_exc:
                        raw.setdefault("jats_errors", []).append({"url": jats_url, "error": str(jats_exc)})
                metadata = _extract_metadata_from_html(html, final_url)
                if en_html:
                    en_metadata = _extract_metadata_from_html(en_html, _with_lang_param(final_url, "en"))
                    if not _norm_space(metadata.get("title")) and _norm_space(en_metadata.get("title")):
                        metadata["title"] = en_metadata.get("title")
                    if not _norm_space(metadata.get("abstract_en")) and _norm_space(en_metadata.get("abstract_en")):
                        metadata["abstract_en"] = en_metadata.get("abstract_en")
                    if not _norm_space(metadata.get("abstract")) and _norm_space(en_metadata.get("abstract_en")):
                        metadata["abstract"] = en_metadata.get("abstract_en")
                    if not metadata.get("references_en") and en_metadata.get("references_en"):
                        metadata["references_en"] = en_metadata.get("references_en")
                score = _score_metadata(metadata, title, doi)
                if score > best_score:
                    best_metadata = metadata
                    best_score = score
                    if best_source != "jats":
                        best_source = "html"
            except Exception as exc:
                raw["doi_error"] = str(exc)
                LOGGER.warning("RAS DOI resolve failed doi=%s error=%s", doi, exc)

        if title and best_score < 10:
            search_candidates: list[str] = []
            try:
                search_html, search_url = _fetch_html(session, journal_url, params={"s": title})
                raw["search_url"] = search_url
                search_candidates = _parse_search_results(search_html, journal_url, title)
                raw["search_candidates"] = search_candidates
            except Exception as exc:
                raw["search_error"] = str(exc)
                LOGGER.warning("RAS site search failed url=%s title=%s error=%s", journal_url, title, exc)

            for candidate_url in search_candidates:
                try:
                    html, resolved_url = _fetch_html(session, candidate_url)
                    en_html = ""
                    try:
                        en_html, _en_url = _fetch_html(session, _with_lang_param(resolved_url, "en"))
                    except Exception as en_exc:
                        raw.setdefault("en_page_errors", []).append({"url": resolved_url, "error": str(en_exc)})
                    jats_url = _find_jats_url_from_html(html, resolved_url)
                    if jats_url:
                        try:
                            jats_xml, _jats_final = _fetch_html(session, jats_url)
                            jats_metadata = _extract_metadata_from_jats(jats_xml)
                            jats_metadata["source_url"] = jats_url
                            score = _score_metadata(jats_metadata, title, doi) + 3
                            if score > best_score:
                                best_metadata = jats_metadata
                                best_score = score
                                best_source = "jats"
                                raw["jats_url"] = jats_url
                        except Exception as jats_exc:
                            raw.setdefault("jats_errors", []).append({"url": jats_url, "error": str(jats_exc)})
                    metadata = _extract_metadata_from_html(html, resolved_url)
                    if en_html:
                        en_metadata = _extract_metadata_from_html(en_html, _with_lang_param(resolved_url, "en"))
                        if not _norm_space(metadata.get("title")) and _norm_space(en_metadata.get("title")):
                            metadata["title"] = en_metadata.get("title")
                        if not _norm_space(metadata.get("abstract_en")) and _norm_space(en_metadata.get("abstract_en")):
                            metadata["abstract_en"] = en_metadata.get("abstract_en")
                        if not _norm_space(metadata.get("abstract")) and _norm_space(en_metadata.get("abstract_en")):
                            metadata["abstract"] = en_metadata.get("abstract_en")
                        if not metadata.get("references_en") and en_metadata.get("references_en"):
                            metadata["references_en"] = en_metadata.get("references_en")
                    score = _score_metadata(metadata, title, doi)
                    if score > best_score:
                        best_metadata = metadata
                        best_score = score
                        if best_source != "jats":
                            best_source = "html"
                except Exception as exc:
                    LOGGER.warning("RAS candidate parse failed url=%s error=%s", candidate_url, exc)

        if not best_metadata:
            return {
                "error": True,
                "error_message": "Не удалось найти публикацию по DOI или заголовку на сайте журнала РАН.",
                "raw": raw,
            }

        # If JATS was used, keep its references even if HTML scores higher.
        if best_metadata and best_source == "jats":
            for field in ("title", "original_title", "abstract", "abstract_ru", "abstract_en"):
                if not _norm_space(best_metadata.get(field)):
                    candidate = _norm_space(best_metadata.get(field))
                    if candidate:
                        best_metadata[field] = candidate

        result = {
            "doi": _first_non_empty(best_metadata.get("doi"), doi),
            "title": _norm_space(best_metadata.get("title")),
            "original_title": _norm_space(best_metadata.get("original_title")),
            "abstract": _norm_space(best_metadata.get("abstract")),
            "abstract_ru": _norm_space(best_metadata.get("abstract_ru")),
            "abstract_en": _norm_space(best_metadata.get("abstract_en")),
            "keywords": _norm_space(best_metadata.get("keywords")),
            "keywords_en": _norm_space(best_metadata.get("keywords_en")),
            "references": _normalize_reference_list(best_metadata.get("references") or []),
            "references_ru": _normalize_reference_list(best_metadata.get("references_ru") or []),
            "references_en": _normalize_reference_list(best_metadata.get("references_en") or []),
            "pages": _norm_space(best_metadata.get("pages")),
            "authors": best_metadata.get("authors") or [],
            "source_url": _norm_space(best_metadata.get("source_url")),
            "raw": {**raw, "best_score": best_score, "selected_source_url": _norm_space(best_metadata.get("source_url")), "best_source": best_source},
        }
        if not result["title"] and result["original_title"] and not _looks_cyrillic(result["original_title"]):
            result["title"] = result["original_title"]
            result["original_title"] = ""
        return result
    finally:
        session.close()
