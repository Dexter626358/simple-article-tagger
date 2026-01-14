from __future__ import annotations

# Optional imports grouped to keep app.py smaller and avoid repetition.
try:
    from converters.word_to_html import convert_to_html, create_full_html_page
    WORD_TO_HTML_AVAILABLE = True
except ImportError:
    WORD_TO_HTML_AVAILABLE = False
    convert_to_html = None
    create_full_html_page = None
    print("WARNING: word_to_html not available. Please add converters/word_to_html.py.")

try:
    from converters.pdf_to_html import convert_pdf_to_html
    PDF_TO_HTML_AVAILABLE = True
except ImportError:
    PDF_TO_HTML_AVAILABLE = False
    convert_pdf_to_html = None
    print("WARNING: pdf_to_html not available. Install pdfplumber and pymupdf.")

try:
    from converters.convert_rtf_to_docx import convert_rtf_to_docx, ConversionError
    RTF_CONVERT_AVAILABLE = True
except ImportError:
    RTF_CONVERT_AVAILABLE = False
    convert_rtf_to_docx = None
    ConversionError = Exception

try:
    from metadata_markup import (
        extract_text_from_html,
        extract_text_from_pdf,
    )
    METADATA_MARKUP_AVAILABLE = True
except ImportError:
    METADATA_MARKUP_AVAILABLE = False
    extract_text_from_html = None
    extract_text_from_pdf = None
    print("WARNING: metadata_markup not available. Please add metadata_markup.py.")

try:
    from json_metadata import (
        load_json_metadata,
        save_json_metadata,
        form_data_to_json_structure,
        json_structure_to_form_data,
        find_docx_for_json,
    )
    JSON_METADATA_AVAILABLE = True
except ImportError:
    JSON_METADATA_AVAILABLE = False
    load_json_metadata = None
    save_json_metadata = None
    form_data_to_json_structure = None
    json_structure_to_form_data = None
    find_docx_for_json = None
    print("WARNING: json_metadata not available. Please add json_metadata.py.")
