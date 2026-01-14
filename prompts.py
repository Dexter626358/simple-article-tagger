"""
Модуль для хранения промптов для анализа PDF документов
"""

class Prompts:
    """Класс для хранения различных промптов"""
       
    # Промпт для детального анализа научных статей (с метаданными)
    SCIENTIFIC_DETAILED = """
You are an expert in extracting metadata from scientific articles. Analyze the provided text and extract structured information in JSON format.

## Core Principles

1. **Accuracy**: Extract only information present in the text. Do not generate or invent data.
2. **Completeness**: Aim for maximum completeness of extracted information.
3. **Format Preservation**: Do not modify original structure, spelling, or formatting of source data. **IMPORTANT**: Convert UPPERCASE titles to normal case formatting.
4. **Handling Missing Data**: Use empty strings ("") for text fields or empty arrays ([]) for lists if information is absent.
5. **JSON Compatibility**: Ensure all text values are properly escaped for JSON format:
   - Use standard ASCII quotes (") instead of typographic quotes ("")
   - Escape internal quotes with backslash (\")
   - Use standard hyphens (-) instead of em-dashes (—)
   - Replace special characters like № with "No"
   - Convert UPPERCASE titles to proper title case
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
- **Addresses**: Do not include organization name in address. For multiple organizations, separate addresses with semicolons. Address maybe just city.
- **Important**: Do NOT include address information in the main author data fields (surname, initials, orgName). Address should be placed in the separate "address" field only.
- **Email**: 
  - Use author's email if explicitly stated
  - If not stated - use email of other authors or organization
  - Apply same email to all authors if individual emails not specified
  - **Special rule for single email in contacts**: If only ONE email address is provided in the article's contact information:
    - **Mark the FIRST author as corresponding** (set "correspondence": true for the first author)
    - **Apply this email to ALL authors** (add the same email address to all authors' email fields)
    - This ensures all authors have contact information while clearly identifying the corresponding author
- **Identifiers**: Extract SPIN, ORCID, Scopus ID, ResearcherID if present.
  - **ORCID format**: Extract only the identifier (e.g., "0000-0001-6816-0260"). Do not include full URLs like "http://orcid.org/0000-0001-6816-0260".
- **Corresponding Author**: Determine if author is the corresponding author using the following criteria:
  - **Explicit markers** (set "correspondence": true if any of these are found):
    - English: "corresponding author", "author for correspondence", "correspondence to", "correspondence:", "for correspondence", "corresponding", "correspondence should be addressed to"
    - Russian: "автор для переписки", "для переписки", "корреспондирующий автор", "корреспонденция", "для корреспонденции", "переписка", "автор-корреспондент"
  - **Symbol markers**: If author name is marked with asterisk (*), dagger (†), double dagger (‡), or other special symbols that typically indicate corresponding author
  - **Email indicators**: If author has an email address explicitly listed and other authors don't, or if text states "correspondence to [email]" or "для переписки [email]"
  - **Position indicators**: If author is listed first and has contact information (email, address) while others don't, they may be the corresponding author
  - **Single email rule**: If only ONE email address is provided in the article's contact information, mark the FIRST author as corresponding (set "correspondence": true) and apply this email to ALL authors
  - **Default rule**: If none of the above explicit criteria are met, mark as corresponding author the author who has an email address. If multiple authors have emails, prefer the first author with email. If no authors have emails, set "correspondence": false for all.
  - **Important**: Only mark as corresponding author if there is clear evidence. When using default rule, ensure email is explicitly present for that author.
- **Editorial Articles**: If the article is an editorial article (artType: "EDI") or has no individual authors (e.g., editorial notes, anonymous articles, institutional publications), use the following default author:
  - **RUS**: surname: "Редакция", initials: "Журнала", orgName: "" (or organization name if explicitly mentioned in the text)
  - **ENG**: surname: "Editorial", initials: "Team", orgName: "" (or organization name if explicitly mentioned in the text)
  - **Important**: Do NOT use "Редакция журнала" or "Editorial Team" in orgName. Only use the actual organization name if it is explicitly mentioned in the article text. If no organization is mentioned, leave orgName empty.

### Titles and Abstracts
- Extract titles completely, without modifications or abbreviations
- Preserve original punctuation and special characters
- **IMPORTANT**: Convert UPPERCASE (CAPS LOCK) titles to normal case formatting
- Provide titles in both Russian (RUS) and English (ENG) languages
- **IMPORTANT**: Do NOT extract abstracts. Leave abstracts fields empty: `"abstracts": {"RUS": "", "ENG": ""}`

### Keywords
- Extract all keywords/phrases
- Preserve original order
- Provide in both Russian (RUS) and English (ENG) languages

### References
- **IMPORTANT**: Do NOT extract references/literature lists. Leave references fields empty: `"references": {"RUS": [], "ENG": []}`

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

## Output Format

Return only valid JSON without additional comments or explanations. """

    # Промпт для форматирования списка литературы (исправление ошибок OCR)
    REFERENCES_FORMATTING_RUS = """
Задание:

Перед тобой — список литературы, полученный с помощью распознавания текста (OCR). В нем уже выверено содержание и порядок источников, но есть технические ошибки форматирования: разрывы слов и инициалов пробелами, лишние пробелы, ошибки переноса, а также нарушение единообразия в оформлении.
Твоя задача — привести список к аккуратному, читабельному виду для публикации на сайте, не внося никаких изменений в библиографическую информацию, а только исправив форматирование.

Правила:

1. Убери лишние пробелы внутри слов, фамилий, инициалов и между ними (например, "Ве с е л о в а И . С ." → "Веселова И. С.").

2. Убери разрывы строк внутри одной записи (одна публикация — одна строка).

3. Исправь переносы внутри слов (например, "му- зыкальной" → "музыкальной").

4. Приведи оформление к единообразному стилю (например, кавычки, тире, точки и запятые, если они отличаются).

5. Не изменяй суть и порядок библиографических описаний.

6. Не добавляй и не убирай элементы описания.

7. В конце каждого описания ставь точку, если это соответствует принятому стандарту.

8. Выводи результат как аккуратно отформатированный, удобочитаемый список для сайта.

9. **ВАЖНО: Удали строки, которые НЕ являются библиографическими источниками:**
   - Заголовки журналов (например, "IZVESTIYA RAN. ENERGETIKA / BULLETIN OF THE RAS. ENERGETICS")
   - Номера выпусков и страниц без авторов (например, "no. 6 2025 52")
   - Служебные строки с фамилиями без полного описания (например, "ВОРОНИН и др. / VORONIN et al.")
   - Строки, содержащие только название журнала, номер, год или страницы без автора и названия публикации
   - Строки, которые явно являются частью оглавления или служебной информации, а не библиографической записью

10. Верни результат в формате JSON: {"references": ["запись 1", "запись 2", ...]}

Пример входных данных (с примерами строк, которые нужно удалить):

IZVESTIYA RAN. ENERGETIKA / BULLETIN OF THE RAS. ENERGETICS no. 6 2025 52 ВОРОНИН и др. / VORONIN et al.
1. Ве с е л о в а И . С . Жесты публичной лаудации: доступы к благу // Комплекс Чебурашки, или Общество послушания: Сб. статей. СПб.: Пропповский центр, 2012. C. 11–49.
2. До р о хо в а Е . А . Фольклорная комиссия Союза композиторов России и изучение традиционной му- зыкальной культуры Русского Севера // Рябининские чтения. Петрозаводск: Музей-заповедник «Кижи», 2007. С. 290–292.

Пример ожидаемого результата (служебные строки удалены):

1. Веселова И. С. Жесты публичной лаудации: доступы к благу // Комплекс Чебурашки, или Общество послушания: Сб. статей. СПб.: Пропповский центр, 2012. С. 11–49.
2. Дорохова Е. А. Фольклорная комиссия Союза композиторов России и изучение традиционной музыкальной культуры Русского Севера // Рябининские чтения. Петрозаводск: Музей-заповедник «Кижи», 2007. С. 290–292.

Выполни форматирование для всего приведенного ниже списка литературы:

{references_text}

Верни только валидный JSON без дополнительных комментариев.
"""

    REFERENCES_FORMATTING_ENG = """
Task:

You are given a bibliography list generated via OCR. The content is already checked for accuracy, but there are technical formatting issues: words and initials are split by spaces, there are extra spaces, line breaks, hyphenated word splits, and inconsistencies in punctuation.
Your task is to correct only the formatting and output a clean, consistent, web-friendly bibliography list.

Instructions:

1. Remove extra spaces inside words, surnames, and initials.

2. Merge any split lines belonging to the same reference.

3. Restore hyphenated words to their correct form.

4. Standardize punctuation, quotation marks, dashes, and dots according to standard bibliographic style.

5. Do not change the actual content or order of the references.

6. Do not add or remove any bibliographic elements.

7. Output each reference as a single clean line, with proper punctuation at the end (as appropriate).

8. **IMPORTANT: Remove lines that are NOT bibliographic references:**
   - Journal titles/headers (e.g., "IZVESTIYA RAN. ENERGETIKA / BULLETIN OF THE RAS. ENERGETICS")
   - Issue numbers and pages without authors (e.g., "no. 6 2025 52")
   - Service lines with surnames without full description (e.g., "VORONIN et al.")
   - Lines containing only journal name, issue number, year, or pages without author and publication title
   - Lines that are clearly part of table of contents or service information, not bibliographic entries

9. Return result in JSON format: {"references": ["entry 1", "entry 2", ...]}

Example input (with lines to be removed):

IZVESTIYA RAN. ENERGETIKA / BULLETIN OF THE RAS. ENERGETICS no. 6 2025 52 VORONIN et al.
1. V e s e l o v a , I . S . Gestures of public laudation: access to the good. The Cheburashka complex, or the Obedience Society: Collection of articles. St. Petersburg, 2012. P. 11–49. (In Russ.)

Expected output (service lines removed):

1. Veselova, I. S. Gestures of public laudation: access to the good. The Cheburashka complex, or the Obedience Society: Collection of articles. St. Petersburg, 2012. P. 11–49. (In Russ.)

Format the following bibliography list:

{references_text}

Return only valid JSON without additional comments.
"""

    @classmethod
    def get_prompt(cls, prompt_type: str = "scientific") -> str:
        """
        Получить промпт по типу
        
        Args:
            prompt_type (str): Тип промпта ("scientific_detailed")
        
        Returns:
            str: Промпт для анализа
        """
        prompts = {
            "scientific_detailed": cls.SCIENTIFIC_DETAILED,
            "references_formatting_rus": cls.REFERENCES_FORMATTING_RUS,
            "references_formatting_eng": cls.REFERENCES_FORMATTING_ENG,
        }
        
        return prompts.get(prompt_type, cls.SCIENTIFIC_DETAILED)
    
    @classmethod
    def list_available_prompts(cls) -> list:
        """
        Получить список доступных типов промптов
        
        Returns:
            list: Список доступных типов промптов
        """
        return ["scientific_detailed", "references_formatting_rus", "references_formatting_eng"] 
