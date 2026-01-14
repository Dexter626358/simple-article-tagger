function processAnnotation(text) {
    if (!text) return "";
    // Удаляем префикс и чистим переносы/разрывы слов из PDF
    let cleaned = String(text).replace(/^(Аннотация|Annotation|Abstract|Резюме|Summary)\s*[.:]?\s*/i, "");
    cleaned = cleaned.replace(/\r\n?/g, "\n");
    cleaned = cleaned.replace(/\u00ad/g, "");
    cleaned = cleaned.replace(/([A-Za-zА-Яа-яЁё])[-‑–—]\s*\n\s*([A-Za-zА-Яа-яЁ