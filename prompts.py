"""
Модуль для хранения промптов для анализа PDF документов
"""

from typing import Optional

class Prompts:
    """Класс для хранения различных промптов"""
       
    # Базовый промпт для детального анализа научных статей (без опциональных секций)
    SCIENTIFIC_BASE_TEMPLATE = """
You are an expert in extracting metadata from scientific articles. Analyze the provided text and extract structured information in JSON format.

## Core Principles

1. **Accuracy**: Extract only information present in the text. Do not generate or invent data.
2. **Completeness**: Aim for maximum completeness of extracted information.
3. **Format Preservation**: Do not modify original structure, spelling, or formatting of source data. **IMPORTANT**: Convert UPPERCASE titles to normal case formatting.
4. **Formatting**: Use <sup>/<sub> for superscripts/subscripts.
5. **Handling Missing Data**: Use empty strings ("") for text fields or empty arrays ([]) for lists if information is absent.
6. **JSON Compatibility**: Ensure all text values are properly escaped for JSON format:
   - Use standard ASCII quotes (") instead of typographic quotes ("")
   - Escape internal quotes with backslash (\")
   - Use standard hyphens (-) instead of em-dashes (—)
   - Replace special characters like № with "No"
   - Avoid non-ASCII characters that may cause JSON parsing errors

## Article Types

Determine the article type according to the following list (use "RAR" by default):

artType: RAR (default), REV, BRV, SCO, REP, CNF, EDI, COR, ABS, RPR, MIS, PER, UNK

## Data Extraction Rules

### Authors
- **STRICT REQUIREMENT**: Extract full information for **all** authors listed in the article. Do not omit any author under any circumstances.
- **Full Name and Patronymic (Полное имя и отчество)**: 
  - **IMPORTANT**: If the full first name and patronymic (middle name) are available in the source text, use them completely (e.g., "Иван Петрович", "Ivan Petrovich").
  - **If full names are NOT available**, only then use initials (e.g., "И. П.", "I. P.").
  - **Priority rule**: Full names > Initials. Always prefer full names when they are present in the source.
- **Initials**: When using initials (only when full names are not available), separate with space (e.g., "G. M." not "G.M.", "И. П." not "И.П.").
- **Organizations**: If author is affiliated with multiple organizations, list them separated by semicolons.
- **Shared affiliation rule**: If multiple authors share the same organization, and it is provided once for the group, apply this organization to ALL those authors. Copy both organization names (RUS/ENG) and addresses (RUS/ENG) for each author.
- **Affiliation markers**: Superscript/inline numbers next to author names (e.g., "Юрова1,2", "Kordys 1") indicate the affiliation numbers listed below. Use these numbers to map each author to the correct organization(s). If an author has multiple numbers, include all corresponding organizations and addresses.
- **Addresses**: Do not include organization name in address. For multiple organizations, separate addresses with semicolons. Address maybe just city.
- **Important**: Do NOT include address information in the main author data fields (surname, initials, orgName). Address should be placed in the separate "address" field only.
- **Email**:
  - Use each author's individual email if explicitly stated
  - If only ONE email exists in the article, apply it to all authors (see **Single email rule** in Corresponding Author)
  - If no emails are present, leave email fields empty
- **Identifiers**: Extract SPIN, ORCID, Scopus ID, ResearcherID if present.
  - **ORCID format**: Extract only the identifier (e.g., "0000-0001-6816-0260"). Do not include full URLs like "http://orcid.org/0000-0001-6816-0260".
- **Corresponding Author**: Determine corresponding author by priority (stop at first match):
  1. **Explicit text markers** → correspondence: true
     - English: "corresponding author", "author for correspondence", "correspondence to", "correspondence:", "for correspondence", "corresponding", "correspondence should be addressed to"
     - Russian: "автор для переписки", "для переписки", "корреспондирующий автор", "корреспонденция", "для корреспонденции", "переписка", "автор-корреспондент"
  2. **Symbol markers** → correspondence: true
     - Asterisk (*), dagger (†), double dagger (‡) next to author name
  3. **Single email rule** → correspondence: true for FIRST author, email applied to ALL
     - Triggers when exactly ONE email exists in the entire article
     - If the only email belongs to the corresponding author, still apply it to ALL co-authors
  4. **Sole email holder** → correspondence: true
     - Only one author has an email, others don't
  5. **No criteria met** → correspondence: false for ALL authors
- **Editorial Articles**: If the article is an editorial article (artType: "EDI") or has no individual authors (e.g., editorial notes, anonymous articles, institutional publications), use the following default author:
  - **RUS**: surname: "Редакция", initials: "Журнала", orgName: "" (or organization name if explicitly mentioned in the text)
  - **ENG**: surname: "Editorial", initials: "Team", orgName: "" (or organization name if explicitly mentioned in the text)
  - **Important**: Do NOT use "Редакция журнала" or "Editorial Team" in orgName. Only use the actual organization name if it is explicitly mentioned in the article text. If no organization is mentioned, leave orgName empty.

### Titles
- Extract titles completely, without modifications or abbreviations
- Preserve original punctuation and special characters
- Provide titles in both Russian (RUS) and English (ENG) languages

### Keywords
- Extract all keywords/phrases
- Preserve original order
- Provide in both Russian (RUS) and English (ENG) languages

### Metadata
- **Pages**: Format "start-end" (e.g., "7-26")
- **Codes**: UDC (УДК), BBK (ББК), DOI, EDN
- **Dates**: Format YYYY-MM-DD (e.g., "2023-05-15")
- **Funding**: Information about grants and funding sources
- **Publication Language (PublLang)**: Determine the main language of the article publication:
  - Use "RUS" if the article is primarily in Russian
  - Use "ENG" if the article is primarily in English
  - For bilingual articles, determine the primary language based on the main content

## JSON Structure

```json
{
  "pages": "",
  "artType": "",
  "PublLang": "",
  "authors": [
    {
      "num": "",
      "correspondence": false,
      "individInfo": {
        "RUS": {
          "surname": "",
          "initials": "",
          "address": "",
          "orgName": "",
          "email": "",
          "otherInfo": "",
          "authorCodes": {
            "spin": "",
            "orcid": "",
            "scopusid": "",
            "researcherid": ""
          }
        },
        "ENG": {
          "surname": "",
          "initials": "",
          "address": "",
          "orgName": "",
          "email": "",
          "otherInfo": "",
          "authorCodes": {
            "spin": "",
            "orcid": "",
            "scopusid": "",
            "researcherid": ""
          }
        }
      }
    }
  ],
  "artTitles": {
    "RUS": "",
    "ENG": ""
  },
  "abstracts": {
    "RUS": "",
    "ENG": ""
  },
  "codes": {
    "udk": "",
    "bbk": "",
    "doi": "",
    "edn": ""
  },
  "keywords": {
    "RUS": [],
    "ENG": []
  },
  "references": {
    "RUS": [],
    "ENG": []
  },
  "dates": {
    "dateReceived": "",
    "dateAccepted": "",
    "datePublication": ""
  },
  "fundings": {
    "RUS": "",
    "ENG": ""
  },
  "file": "",
  "article_url": "",
  "pdf_url": ""
}
```

**Notes for file/article_url/pdf_url**:
- Fill only if explicitly present in the source text
- If absent, leave empty strings

## Example: Converting UPPERCASE Titles to Normal Case

If the source title is in UPPERCASE, convert it to proper title case:

**Source (UPPERCASE):**
```
ДЛИННЫЕ НЕКОДИРУЮЩИЕ РНК ТРЕМАТОДЫ HIMASTHLA ELONGATA (MEHLIS, 1831) (TREMATODA, HIMASTHLIDAE)
```

**Correct JSON output:**
```json
{
  "artTitles": {
    "RUS": "Длинные некодирующие РНК трематоды Himasthla elongata (Mehlis, 1831) (Trematoda, Himasthlidae)",
    "ENG": "Long non-coding RNAs of the trematode Himasthla elongata (Mehlis, 1831) (Trematoda, Himasthlidae)"
  }
}
```

## Example for Articles Without Individual Authors

```json
{
  "pages": "1-2",
  "artType": "EDI",
  "PublLang": "RUS",
  "authors": [
    {
      "num": "1",
      "correspondence": false,
      "individInfo": {
        "RUS": {
          "surname": "Редакция",
          "initials": "Журнала",
          "address": "",
          "orgName": "",
          "email": "",
          "otherInfo": "",
          "authorCodes": {
            "spin": "",
            "orcid": "",
            "scopusid": "",
            "researcherid": ""
          }
        },
        "ENG": {
          "surname": "Editorial",
          "initials": "Team",
          "address": "",
          "orgName": "",
          "email": "",
          "otherInfo": "",
          "authorCodes": {
            "spin": "",
            "orcid": "",
            "scopusid": "",
            "researcherid": ""
          }
        }
      }
    }
  ],
  "artTitles": {
    "RUS": "Редакционная заметка",
    "ENG": "Editorial Note"
  }
}
```

## Important Notes

- **Source Language**: The article text may be in Russian, English, or bilingual. Extract content exactly as it appears in the source.
- **Language Handling**:
  - If article is **in Russian only**: Extract Russian content to RUS fields, leave ENG fields empty
  - If article is **in English only**: Extract English content to ENG fields, leave RUS fields empty
  - If article is **bilingual**: Extract content to corresponding RUS and ENG fields
  - **Never translate** content yourself - only extract what is present in the source
- **Character Encoding**: Preserve all Cyrillic characters, Latin characters, special symbols, and formatting.
- **Case Formatting**: Convert UPPERCASE titles to normal case formatting. Apply proper title case rules (capitalize first letter of each major word).
- **Validation**: Ensure the output is valid JSON before returning.

"""

    # Опциональный блок: аннотации
    SCIENTIFIC_ABSTRACTS_BLOCK = """
### Abstracts
- CRITICAL: Copy abstract text EXACTLY as it appears in the source. Do NOT paraphrase, summarize, or shorten.
- FORMATTING:
  - Superscripts: wrap in <sup>...</sup> (e.g., m² → m<sup>2</sup>)
  - Subscripts: wrap in <sub>...</sub> (e.g., H2O → H<sub>2</sub>O)
  - Bold text: wrap in <b>...</b>
  - Italic/cursive text: wrap in <i>...</i>
  - New paragraph: insert \\n\\n between paragraphs
  - Single line break within paragraph: insert \\n
- COMPLETENESS:
  - Extract the FULL abstract from first word to last word.
  - Do NOT cut off mid-sentence or skip sentences.
  - If abstract is long, extract it entirely regardless of length.
  - BEFORE returning JSON, verify last sentence matches the source; if not, append missing part.
- LANGUAGE:
  - Extract RUS abstract to "RUS" field.
  - Extract ENG abstract to "ENG" field.
  - Never translate — only extract what is present in source.
  - If abstract exists in one language only, leave the other field empty.
"""

    # Футер промпта
    SCIENTIFIC_FOOTER = """
## Output Format
Return only valid JSON without additional comments or explanations.

## Input Text

Текст статьи для анализа:

{article_text}
"""

    # Опциональный блок: список литературы
    SCIENTIFIC_REFERENCES_BLOCK = """
### References
- Extract ALL references from the literature list.
- Preserve original formatting and punctuation.
- Return as array of strings, one entry per element.
- Use RUS and ENG arrays if both versions are present.
### References Structure Rules
- If ONLY section titled "Список литературы" exists: put ALL entries in RUS array, ENG empty.
- If a COMBINED list is present: put ALL entries in RUS array, ENG empty.
- If TWO SEPARATE sections exist:
  - "Список литературы" -> RUS array
  - "References" -> ENG array
- If ONLY section titled "References" exists: put ALL entries in ENG array, RUS empty.
- If structure is unclear: put all entries in RUS array by default.
"""

    # Промпт-шаблон для форматирования списка литературы (исправление ошибок OCR)
    REFERENCES_FORMATTING_TEMPLATE = """
You are a mechanical text processor for bibliographic references extracted from PDF files. You are not an editor, translator, or proofreader.

LANGUAGE: {language_label}
This indicates the language of the references. Do NOT translate.

TASK:
Normalize the formatting of bibliographic entries while preserving ALL bibliographic data exactly.

STRICT RULES:

1. DO NOT:
- add any characters or data;
- remove any characters or data;
- change spelling of names, titles, journals, years, volumes, issues, pages;
- translate text;
- reorder elements inside a reference;
- interpret or correct content;
- produce summaries, explanations, comments, metadata, or headings.

2. YOU MAY ONLY:
- remove line breaks inside a single reference;
- remove extra spaces;
- remove hyphenation caused by line breaks;
- merge fragmented parts of one reference into one line.
- preserve DOI exactly as in the source; do NOT truncate or alter it.

3. OUTPUT FORMAT:
- each bibliographic entry must be on ONE line;
- NO numbering (remove "1.", "2.", etc.);
- preserve original punctuation and separators (//, ., :, №, V., P., etc.);
- return ONLY valid JSON: {"references": ["entry 1", "entry 2", ...]};
- no additional comments or text;
- EXCEPTION: wrap superscripts/subscripts in <sup>/<sub>.
  Example: CO2 -> CO<sub>2</sub>, note№ -> note<sup>1</sup>.

COLUMN ARTIFACTS:
- Input may contain mixed fragments from a two-column layout.
- If an entry looks corrupted by column mixing, keep it as-is.
- Never merge fragments from different entries.
- Never reconstruct or guess missing parts.

4. DATA INTEGRITY:
- all characters from the input must be present in the output, except:
  * line break characters,
  * extra spaces,
  * hyphenation caused by line breaks,
  * numbering markers (1., 2., [1], [2], etc.).

5. RECORD BOUNDARIES:
- Determine boundaries by numbering (1., 2., [1], [2], etc.).
- Keep the original source order exactly as it appears in INPUT.
- If numbering is missing, split conservatively by entry-start patterns.
- If boundary is ambiguous, keep more text inside the current entry.
- Do NOT reorder entries and do NOT infer a "correct" bibliography order.

6. COMPLETENESS (MANDATORY):
- Extract ABSOLUTELY ALL references from the input.
- NEVER skip entries, even if damaged, unreadable, or incomplete.
- DAMAGED ENTRIES: include as-is; do not repair or delete OCR noise.
- BEFORE returning JSON, perform an internal check:
  * Count entries in input: N_input.
  * If there is no numbering, estimate N_input by counting distinct reference-start patterns.
  * Count entries in output: N_output.
  * If N_input != N_output, find missing entries and add them.
  * Do not include N_input/N_output in final JSON.
- If an entry has no number but is clearly a reference, include it.

INPUT:
{references_text}

OUTPUT:
Return valid JSON only.

If INPUT is empty or contains no recognizable references, return:
{"references": []}
"""

    # System message for metadata extraction
    SYSTEM_METADATA_EXTRACTION = "Ты помощник для извлечения метаданных из научных статей. Всегда возвращай валидный JSON."

    # Fallback prompt for metadata extraction (note: schema differs from SCIENTIFIC_BASE_TEMPLATE)
    SCIENTIFIC_FALLBACK_TEMPLATE = """Извлеки метаданные из следующего текста научной статьи и верни результат в формате JSON.

Текст статьи:
{article_text}

Извлеки следующие поля:
- title (название статьи на русском языке)
- title_en (название статьи на английском языке, если есть)
- IMPORTANT: Extract full information for all authors listed in the article. Do not omit any author under any circumstances.
- authors (список авторов, каждый автор как объект с полями: surname, initials, organization, address, email, otherInfo - для русского и английского языков)
- doi (DOI статьи, если есть)
- udc (УДК, если есть)
- bbk (ББК, если есть)
- edn (EDN, если есть)
- annotation (аннотация на русском языке){annotation_suffix}
- annotation_en (аннотация на английском языке, если есть){annotation_suffix}
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
- references_ru (список литературы на русском языке){references_suffix}
- references_en (список литературы на английском языке, если есть){references_suffix}

Верни только валидный JSON объект без дополнительных комментариев и форматирования.
Если какое-то поле отсутствует в тексте, верни null для этого поля.
"""

    # System message for PDF->HTML conversion
    SYSTEM_PDF_TO_HTML = "Ты помощник для конвертации текста научных статей в HTML. Всегда возвращай валидный HTML код."

    # Prompt template for PDF->HTML conversion
    PDF_TO_HTML_PROMPT_TEMPLATE = """Преобразуй текст научной статьи в HTML. Правила:
1. Сохрани всё содержимое без изменений
2. Исправь форматирование: убери лишние пробелы в словах, объедини разорванные строки
3. Каждый абзац в теге <p>
4. Верни только HTML код без комментариев

Текст:
{article_text}

HTML:"""

    @classmethod
    def get_prompt(
        cls,
        prompt_type: str = "scientific_detailed",
        article_text: Optional[str] = None,
        language: Optional[str] = None,
        extract_abstracts: bool = False,
        extract_references: bool = False,
    ) -> str:
        """
        Получить промпт по типу
        
        Args:
            prompt_type (str): Тип промпта ("scientific_detailed")
        
        Returns:
            str: Промпт для анализа
        """
        if prompt_type in ("references_formatting_rus", "references_formatting_eng"):
            inferred = "RUS" if prompt_type.endswith("_rus") else "ENG"
            if language and language.upper() != inferred:
                raise ValueError("language conflicts with prompt_type suffix")
            return cls.get_references_prompt(inferred)

        if prompt_type == "references_formatting":
            if not language:
                raise ValueError("language is required for references_formatting")
            return cls.get_references_prompt(language)

        if prompt_type == "pdf_to_html":
            if not article_text:
                raise ValueError("article_text is required for pdf_to_html")
            return cls.get_pdf_to_html_prompt(article_text)

        if prompt_type == "scientific_detailed":
            if not article_text:
                raise ValueError("article_text is required for scientific_detailed")
            return cls.get_scientific_prompt(
                article_text=article_text,
                extract_abstracts=extract_abstracts,
                extract_references=extract_references,
            )

        raise ValueError(f"Unknown prompt_type: {prompt_type}")

    @classmethod
    def get_references_prompt(cls, language: str, references_text: Optional[str] = None) -> str:
        language_label = "Русский" if (language or "").upper() == "RUS" else "English"
        if references_text is None:
            references_text = "{references_text}"
        prompt = cls.REFERENCES_FORMATTING_TEMPLATE
        prompt = prompt.replace("{language_label}", language_label)
        prompt = prompt.replace("{references_text}", references_text)
        return prompt

    @classmethod
    def get_scientific_fallback_prompt(
        cls,
        article_text: str,
        extract_abstracts: bool = False,
        extract_references: bool = False,
    ) -> str:
        annotation_suffix = "" if extract_abstracts else " — оставь пустой строкой"
        references_suffix = "" if extract_references else " — оставь пустым массивом"
        return cls.SCIENTIFIC_FALLBACK_TEMPLATE.format(
            article_text=article_text,
            annotation_suffix=annotation_suffix,
            references_suffix=references_suffix,
        )

    @classmethod
    def get_pdf_to_html_prompt(cls, article_text: str) -> str:
        return cls.PDF_TO_HTML_PROMPT_TEMPLATE.format(article_text=article_text)

    @classmethod
    def get_scientific_prompt(
        cls,
        article_text: str,
        extract_abstracts: bool = False,
        extract_references: bool = False,
    ) -> str:
        blocks = [cls.SCIENTIFIC_BASE_TEMPLATE]
        if extract_abstracts:
            blocks.append(cls.SCIENTIFIC_ABSTRACTS_BLOCK)
        if extract_references:
            blocks.append(cls.SCIENTIFIC_REFERENCES_BLOCK)
        blocks.append(cls.SCIENTIFIC_FOOTER)
        prompt = "\n".join(blocks)
        return prompt.replace("{article_text}", article_text)
    
    @classmethod
    def list_available_prompts(cls) -> list:
        """
        Получить список доступных типов промптов
        
        Returns:
            list: Список доступных типов промптов
        """
        return [
            "scientific_detailed",
            "references_formatting",
            "references_formatting_rus",
            "references_formatting_eng",
            "pdf_to_html",
        ]

