
// Глобальные функции для работы с модальным окном списка литературы
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

let currentRefsFieldId = null;

function viewReferences(fieldId, title) {
  const field = document.getElementById(fieldId);
  if (!field) return;
  
  currentRefsFieldId = fieldId;
  
  const refsText = field.value.trim();
  if (!refsText) {
    alert("Список литературы пуст");
    return;
  }
  
  const refs = refsText.split("\n")
    .map(s => s.trim())
    .filter(Boolean);
  
  const modal = document.getElementById("refsModal");
  const modalTitle = document.getElementById("modalTitle");
  const refsList = document.getElementById("refsList");
  
  if (!modal || !modalTitle || !refsList) return;
  
  modalTitle.textContent = title;
  refsList.innerHTML = "";
  
  if (refs.length === 0) {
    refsList.innerHTML = "<p style='color:#999;text-align:center;padding:20px;'>Список литературы пуст</p>";
  } else {
    refs.forEach((ref, index) => {
      const refItem = document.createElement("div");
      refItem.className = "ref-item";
      refItem.dataset.index = index;
      // Определяем, есть ли следующий источник для объединения
      const hasNext = index < refs.length - 1;
      refItem.innerHTML = `
        <span class="ref-number">${index + 1}.</span>
        <span class="ref-text" contenteditable="true" spellcheck="false">${escapeHtml(ref)}</span>
        <div class="ref-actions">
          ${hasNext ? `<button class="ref-action-btn merge" onclick="mergeWithNext(this)" title="Объединить со следующим">⇅</button>` : ''}
          <button class="ref-action-btn delete" onclick="deleteReference(this)" title="Удалить">✕</button>
        </div>
      `;
      refsList.appendChild(refItem);
    });
  }
  
  modal.classList.add("active");
}

function mergeWithNext(btn) {
  const refItem = btn.closest(".ref-item");
  if (!refItem) return;
  
  const nextItem = refItem.nextElementSibling;
  if (!nextItem || !nextItem.classList.contains("ref-item")) {
    alert("Нет следующего источника для объединения");
    return;
  }
  
  const currentText = refItem.querySelector(".ref-text")?.textContent.trim() || "";
  const nextText = nextItem.querySelector(".ref-text")?.textContent.trim() || "";
  
  if (!currentText || !nextText) {
    alert("Нельзя объединить пустые источники");
    return;
  }
  
  if (confirm(`Объединить источник ${refItem.querySelector(".ref-number")?.textContent.trim()} со следующим?\n\nТекущий: ${currentText.substring(0, 50)}...\nСледующий: ${nextText.substring(0, 50)}...`)) {
    // Объединяем тексты через пробел
    const mergedText = currentText + " " + nextText;
    const currentTextSpan = refItem.querySelector(".ref-text");
    if (currentTextSpan) {
      currentTextSpan.textContent = mergedText;
    }
    
    // Удаляем следующий элемент
    nextItem.remove();
    
    // Перенумеровываем оставшиеся ссылки
    renumberReferences();
    
    // Обновляем кнопки объединения (могут измениться после удаления)
    updateMergeButtons();
  }
}

function updateMergeButtons() {
  const refItems = document.querySelectorAll("#refsList .ref-item");
  refItems.forEach((item, index) => {
    const actions = item.querySelector(".ref-actions");
    if (!actions) return;
    
    const hasNext = index < refItems.length - 1;
    const existingMergeBtn = actions.querySelector(".ref-action-btn.merge");
    
    if (hasNext && !existingMergeBtn) {
      // Добавляем кнопку объединения, если её нет
      const deleteBtn = actions.querySelector(".ref-action-btn.delete");
      if (deleteBtn) {
        const mergeBtn = document.createElement("button");
        mergeBtn.className = "ref-action-btn merge";
        mergeBtn.onclick = () => mergeWithNext(mergeBtn);
        mergeBtn.title = "Объединить со следующим";
        mergeBtn.textContent = "⇅";
        actions.insertBefore(mergeBtn, deleteBtn);
      }
    } else if (!hasNext && existingMergeBtn) {
      // Удаляем кнопку объединения, если следующего элемента нет
      existingMergeBtn.remove();
    }
  });
}

function deleteReference(btn) {
  const refItem = btn.closest(".ref-item");
  if (refItem && confirm("Удалить эту ссылку из списка?")) {
    refItem.remove();
    // Перенумеровываем оставшиеся ссылки
    renumberReferences();
    // Обновляем кнопки объединения
    updateMergeButtons();
  }
}

function renumberReferences() {
  const refItems = document.querySelectorAll("#refsList .ref-item");
  refItems.forEach((item, index) => {
    const numberSpan = item.querySelector(".ref-number");
    if (numberSpan) {
      numberSpan.textContent = (index + 1) + ".";
    }
  });
  // Обновляем кнопки объединения после перенумерации
  updateMergeButtons();
}

async function processReferencesWithAI(fieldId) {
  const field = document.getElementById(fieldId);
  if (!field) {
    toast("Поле не найдено", "error");
    return;
  }
  
  const rawText = field.value.trim();
  if (!rawText) {
    toast("Поле пусто. Сначала добавьте текст списка литературы.", "error");
    return;
  }
  
  const btnId = fieldId === "references_ru" ? "ai-process-btn-ru" : "ai-process-btn-en";
  const btn = document.getElementById(btnId);
  const originalText = btn ? btn.textContent : "🤖 Обработать с ИИ";
  
  if (btn) {
    btn.disabled = true;
    btn.textContent = "⏳ Обработка ИИ...";
  }
  
  try {
    const response = await fetch("/process-references-ai", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        field_id: fieldId,
        text: rawText,
      }),
    });
    
    const data = await response.json();
    
    if (data.success) {
      field.value = data.text;
      // Обновляем счетчик
      if (window.updateReferencesCount) {
        window.updateReferencesCount(fieldId);
      }
      toast(`✅ Обработано ${data.count} источников с помощью ИИ`, "success");
    } else {
      toast(`❌ Ошибка: ${data.error}`, "error");
    }
  } catch (error) {
    toast(`❌ Ошибка при обработке: ${error.message}`, "error");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = originalText;
    }
  }
}

function saveEditedReferences() {
  if (!currentRefsFieldId) return;
  
  const field = document.getElementById(currentRefsFieldId);
  if (!field) return;
  
  const refItems = document.querySelectorAll("#refsList .ref-item");
  const refs = Array.from(refItems)
    .map(item => {
      const textSpan = item.querySelector(".ref-text");
      return textSpan ? textSpan.textContent.trim() : "";
    })
    .filter(ref => ref.length > 0);
  
  field.value = refs.join("\n");
  // Обновляем счетчик после сохранения
  if (window.updateReferencesCount) {
    window.updateReferencesCount(currentRefsFieldId);
  }
  closeRefsModal();
  
  // Показываем сообщение об успешном сохранении
  const notification = document.createElement("div");
  notification.style.cssText = "position:fixed;top:20px;right:20px;background:#4caf50;color:#fff;padding:15px 20px;border-radius:4px;box-shadow:0 4px 12px rgba(0,0,0,0.2);z-index:3000;font-size:14px;";
  notification.textContent = "Список литературы обновлен";
  document.body.appendChild(notification);
  setTimeout(() => {
    notification.remove();
  }, 2000);
}

function closeRefsModal() {
  const modal = document.getElementById("refsModal");
  const modalContent = document.getElementById("refsModalContent");
  const expandBtn = document.getElementById("refsModalExpandBtn");
  if (modal) {
    modal.classList.remove("active");
    // Сбрасываем размер при закрытии
    if (modalContent) {
      modalContent.classList.remove("expanded");
    }
    if (expandBtn) {
      expandBtn.classList.remove("expanded");
    }
  }
}

function toggleRefsModalSize() {
  const modalContent = document.getElementById("refsModalContent");
  const expandBtn = document.getElementById("refsModalExpandBtn");
  if (modalContent && expandBtn) {
    const isExpanded = modalContent.classList.contains("expanded");
    if (isExpanded) {
      modalContent.classList.remove("expanded");
      expandBtn.classList.remove("expanded");
      expandBtn.title = "Увеличить окно";
    } else {
      modalContent.classList.add("expanded");
      expandBtn.classList.add("expanded");
      expandBtn.title = "Уменьшить окно";
    }
  }
}

let currentAnnotationFieldId = null;

function viewAnnotation(fieldId, title) {
  const field = document.getElementById(fieldId);
  if (!field) return;
  
  currentAnnotationFieldId = fieldId;
  
  const annotationText = field.value.trim();
  
  const modal = document.getElementById("annotationModal");
  const modalTitle = document.getElementById("annotationModalTitle");
  const modalTextarea = document.getElementById("annotationModalTextarea");
  
  if (!modal || !modalTitle || !modalTextarea) return;
  
  modalTitle.textContent = title;
  modalTextarea.value = annotationText;
  
  modal.classList.add("active");
  setTimeout(() => {
    modalTextarea.focus();
    modalTextarea.setSelectionRange(0, 0);
  }, 100);
}

function saveEditedAnnotation() {
  if (!currentAnnotationFieldId) return;
  
  const field = document.getElementById(currentAnnotationFieldId);
  const modalTextarea = document.getElementById("annotationModalTextarea");
  
  if (!field || !modalTextarea) return;
  
  field.value = modalTextarea.value.trim();
  closeAnnotationModal();
  
  const notification = document.createElement("div");
  notification.style.cssText = "position:fixed;top:20px;right:20px;background:#4caf50;color:#fff;padding:15px 20px;border-radius:4px;box-shadow:0 4px 12px rgba(0,0,0,0.2);z-index:3000;font-size:14px;";
  notification.textContent = "Аннотация обновлена";
  document.body.appendChild(notification);
  setTimeout(() => {
    notification.remove();
  }, 2000);
}

function closeAnnotationModal() {
  const modal = document.getElementById("annotationModal");
  const modalContent = document.getElementById("annotationModalContent");
  const expandBtn = document.getElementById("annotationModalExpandBtn");
  if (modal) {
    modal.classList.remove("active");
    // Сбрасываем размер при закрытии
    if (modalContent) {
      modalContent.classList.remove("expanded");
    }
    if (expandBtn) {
      expandBtn.classList.remove("expanded");
    }
  }
  currentAnnotationFieldId = null;
}

function toggleAnnotationModalSize() {
  const modalContent = document.getElementById("annotationModalContent");
  const expandBtn = document.getElementById("annotationModalExpandBtn");
  if (modalContent && expandBtn) {
    const isExpanded = modalContent.classList.contains("expanded");
    if (isExpanded) {
      modalContent.classList.remove("expanded");
      expandBtn.classList.remove("expanded");
      expandBtn.title = "Увеличить окно";
    } else {
      modalContent.classList.add("expanded");
      expandBtn.classList.add("expanded");
      expandBtn.title = "Уменьшить окно";
    }
  }
}

function openCopyModal(text) {
  const modal = document.getElementById("lineCopyModal");
  const ta = document.getElementById("lineCopyTextarea");
  if (!modal || !ta) return;

  ta.value = text;
  modal.classList.add("active");
  setTimeout(() => {
    ta.focus();
    ta.select(); // можно убрать, если чаще копируют фрагмент, а не всё
  }, 0);
}

function closeCopyModal() {
  document.getElementById("lineCopyModal")?.classList.remove("active");
}

function toast(message) {
  const notification = document.createElement("div");
  notification.style.cssText = "position:fixed;top:20px;right:20px;background:#4caf50;color:#fff;padding:15px 20px;border-radius:4px;box-shadow:0 4px 12px rgba(0,0,0,0.2);z-index:3000;font-size:14px;";
  notification.textContent = message;
  document.body.appendChild(notification);
  setTimeout(() => {
    notification.remove();
  }, 2000);
}

// Обработчик кликов для копирования и закрытия модальных окон
document.addEventListener("click", async (e) => {
  // Открытие модального окна копирования
  const openBtn = e.target.closest('[data-action="open-copy"]');
  if (openBtn) {
    const lineEl = openBtn.closest(".line");
    const text = lineEl?.querySelector(".line-text")?.textContent ?? "";
    openCopyModal(text);
    return;
  }

  // Закрытие модального окна копирования
  if (e.target.closest('[data-action="close-copy"]')) {
    closeCopyModal();
    return;
  }

  // Копирование всего текста из модального окна
  if (e.target.closest('[data-action="copy-from-modal"]')) {
    const ta = document.getElementById("lineCopyTextarea");
    const text = ta?.value ?? "";
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      toast("Скопировано");
      closeCopyModal();
    } catch (err) {
      console.error("Ошибка копирования:", err);
      alert("Не удалось скопировать текст. Попробуйте выделить текст и использовать Ctrl+C");
    }
    return;
  }

  // Закрытие модального окна списка литературы при клике вне его
  const refsModal = document.getElementById("refsModal");
  if (e.target === refsModal) {
    closeRefsModal();
  }
  
  // Закрытие модального окна аннотации при клике вне его
  const annotationModal = document.getElementById("annotationModal");
  if (e.target === annotationModal) {
    closeAnnotationModal();
  }
  
  // Закрытие модального окна копирования при клике вне его
  const lineCopyModal = document.getElementById("lineCopyModal");
  if (e.target === lineCopyModal) {
    closeCopyModal();
  }
});

// Закрытие модальных окон по Escape
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeRefsModal();
    closeAnnotationModal();
    closeCopyModal();
  }
});

// Функции для работы с авторами
function toggleAuthorDetails(index) {
  const details = document.getElementById(`author-details-${index}`);
  const item = document.querySelector(`.author-item[data-author-index="${index}"]`);
  if (details && item) {
    const isExpanded = details.style.display !== "none";
    details.style.display = isExpanded ? "none" : "block";
    item.classList.toggle("expanded", !isExpanded);
  }
}

function getNextAuthorIndex() {
  const authorItems = document.querySelectorAll(".author-item");
  let maxIndex = -1;
  authorItems.forEach(item => {
    const index = parseInt(item.dataset.authorIndex, 10);
    if (!isNaN(index) && index > maxIndex) {
      maxIndex = index;
    }
  });
  return maxIndex + 1;
}

function addNewAuthor() {
  const authorsList = document.getElementById("authors-list");
  if (!authorsList) return;
  
  // Удаляем сообщение "Авторы не указаны", если оно есть
  const emptyMessage = authorsList.querySelector("p");
  if (emptyMessage && emptyMessage.textContent.includes("Авторы не указаны")) {
    emptyMessage.remove();
  }
  
  const newIndex = getNextAuthorIndex();
  const authorHtml = createAuthorHTML(newIndex);
  
  // Создаем временный контейнер для вставки HTML
  const tempDiv = document.createElement("div");
  tempDiv.innerHTML = authorHtml;
  const authorElement = tempDiv.firstElementChild;
  
  authorsList.appendChild(authorElement);
  
  // Автоматически открываем нового автора для редактирования
  toggleAuthorDetails(newIndex);
  
  // Прокручиваем к новому автору
  authorElement.scrollIntoView({ behavior: "smooth", block: "nearest" });
  
  // Добавляем обработчики для обновления имени
  attachAuthorNameListeners(newIndex);
}

function createAuthorHTML(index) {
  return `
    <div class="author-item" data-author-index="${index}">
      <div class="author-header" onclick="toggleAuthorDetails(${index})">
        <span class="author-name">Новый автор</span>
        <div style="display:flex;align-items:center;gap:10px;">
          <span class="author-toggle">▼</span>
          <button type="button" class="delete-author-btn" onclick="event.stopPropagation(); deleteAuthor(${index})" title="Удалить автора">✕</button>
        </div>
      </div>
      <div class="author-details" id="author-details-${index}" style="display:none;">
        <div class="author-field">
          <label>Ответственный за переписку:</label>
          <div class="correspondence-toggle">
            <label class="toggle-label">
              <input type="checkbox" class="author-correspondence" data-index="${index}">
              <span class="toggle-text">Да</span>
            </label>
          </div>
        </div>
        <div class="author-field">
          <label>Фамилия (русский):</label>
          <input type="text" class="author-input" data-field="surname" data-lang="RUS" data-index="${index}" value="">
        </div>
        <div class="author-field">
          <label>Surname (English):</label>
          <input type="text" class="author-input" data-field="surname" data-lang="ENG" data-index="${index}" value="">
        </div>
        <div class="author-field">
          <label>Инициалы (русский):</label>
          <input type="text" class="author-input" data-field="initials" data-lang="RUS" data-index="${index}" value="">
        </div>
        <div class="author-field">
          <label>Initials (English):</label>
          <input type="text" class="author-input" data-field="initials" data-lang="ENG" data-index="${index}" value="">
        </div>
        <div class="author-field">
          <label>Организация (русский):</label>
          <input type="text" class="author-input" data-field="orgName" data-lang="RUS" data-index="${index}" value="">
          <div class="selected-lines" style="display:none;"></div>
          <div class="keywords-count" id="org-count-rus-${index}">Количество организаций: 0</div>
        </div>
        <div class="author-field">
          <label>Organization (English):</label>
          <input type="text" class="author-input" data-field="orgName" data-lang="ENG" data-index="${index}" value="">
          <div class="selected-lines" style="display:none;"></div>
          <div class="keywords-count" id="org-count-eng-${index}">Количество организаций: 0</div>
        </div>
        <div class="author-field">
          <label>Адрес (русский):</label>
          <input type="text" class="author-input" data-field="address" data-lang="RUS" data-index="${index}" value="">
        </div>
        <div class="author-field">
          <label>Address (English):</label>
          <input type="text" class="author-input" data-field="address" data-lang="ENG" data-index="${index}" value="">
        </div>
        <div class="author-field">
          <label>Email:</label>
          <input type="email" class="author-input" data-field="email" data-lang="RUS" data-index="${index}" value="">
        </div>
        <div class="author-field">
          <label>Дополнительная информация (русский):</label>
          <textarea class="author-input" data-field="otherInfo" data-lang="RUS" data-index="${index}" rows="2"></textarea>
        </div>
        <div class="author-field">
          <label>Additional Information (English):</label>
          <textarea class="author-input" data-field="otherInfo" data-lang="ENG" data-index="${index}" rows="2"></textarea>
        </div>
        <div class="author-section">
          <h4>Коды автора</h4>
          <div class="author-field">
            <label>SPIN:</label>
            <input type="text" class="author-input" data-field="spin" data-lang="CODES" data-index="${index}" value="">
          </div>
          <div class="author-field">
            <label>ORCID:</label>
            <input type="text" class="author-input" data-field="orcid" data-lang="CODES" data-index="${index}" value="">
          </div>
          <div class="author-field">
            <label>Scopus ID:</label>
            <input type="text" class="author-input" data-field="scopusid" data-lang="CODES" data-index="${index}" value="">
          </div>
          <div class="author-field">
            <label>Researcher ID:</label>
            <input type="text" class="author-input" data-field="researcherid" data-lang="CODES" data-index="${index}" value="">
          </div>
        </div>
      </div>
    </div>
  `;
}

function deleteAuthor(index) {
  if (!confirm("Удалить этого автора?")) return;
  
  const authorItem = document.querySelector(`.author-item[data-author-index="${index}"]`);
  if (authorItem) {
    authorItem.remove();
    
    // Если авторов не осталось, показываем сообщение
    const authorsList = document.getElementById("authors-list");
    if (authorsList && authorsList.querySelectorAll(".author-item").length === 0) {
      authorsList.innerHTML = '<p style="color:#999;font-size:14px;padding:10px;">Авторы не указаны</p>';
    }
  }
}

function updateAuthorName(index) {
  const authorItem = document.querySelector(`.author-item[data-author-index="${index}"]`);
  if (!authorItem) return;
  
  const surnameRus = authorItem.querySelector(`.author-input[data-field="surname"][data-lang="RUS"][data-index="${index}"]`)?.value || "";
  const initialsRus = authorItem.querySelector(`.author-input[data-field="initials"][data-lang="RUS"][data-index="${index}"]`)?.value || "";
  const nameElement = authorItem.querySelector(".author-name");
  
  if (nameElement) {
    const fullName = (surnameRus + " " + initialsRus).trim();
    nameElement.textContent = fullName || "Новый автор";
  }
}

function attachAuthorNameListeners(index) {
  const authorItem = document.querySelector(`.author-item[data-author-index="${index}"]`);
  if (!authorItem) return;
  
  // Добавляем обработчики для полей фамилии и инициалов
  const surnameInput = authorItem.querySelector(`.author-input[data-field="surname"][data-lang="RUS"][data-index="${index}"]`);
  const initialsInput = authorItem.querySelector(`.author-input[data-field="initials"][data-lang="RUS"][data-index="${index}"]`);
  
  if (surnameInput) {
    surnameInput.addEventListener("input", () => updateAuthorName(index));
  }
  if (initialsInput) {
    initialsInput.addEventListener("input", () => updateAuthorName(index));
  }
  
  // Добавляем обработчики для полей организации
  const orgRusInput = authorItem.querySelector(`.author-input[data-field="orgName"][data-lang="RUS"][data-index="${index}"]`);
  const orgEngInput = authorItem.querySelector(`.author-input[data-field="orgName"][data-lang="ENG"][data-index="${index}"]`);
  
  if (orgRusInput) {
    orgRusInput.addEventListener("input", () => {
      if (window.updateOrgCount) {
        window.updateOrgCount(index, "RUS");
      }
    });
    // Инициализируем счетчик при загрузке с небольшой задержкой
    setTimeout(() => {
      if (window.updateOrgCount) {
        window.updateOrgCount(index, "RUS");
      }
    }, 100);
  }
  if (orgEngInput) {
    orgEngInput.addEventListener("input", () => {
      if (window.updateOrgCount) {
        window.updateOrgCount(index, "ENG");
      }
    });
    // Инициализируем счетчик при загрузке с небольшой задержкой
    setTimeout(() => {
      if (window.updateOrgCount) {
        window.updateOrgCount(index, "ENG");
      }
    }, 100);
  }
}

// Сбор данных авторов из формы
function collectAuthorsData() {
  const authors = [];
  const authorItems = document.querySelectorAll(".author-item");
  
  authorItems.forEach((item, index) => {
    const authorIndex = item.dataset.authorIndex || index;
    const inputs = item.querySelectorAll(".author-input");
    
    // Получаем значение чекбокса "ответственный за переписку"
    const correspondenceCheckbox = item.querySelector(`.author-correspondence[data-index="${authorIndex}"]`);
    const correspondence = correspondenceCheckbox ? correspondenceCheckbox.checked : false;
    
    const author = {
      num: String(authorIndex + 1),
      correspondence: correspondence,
      individInfo: {
        RUS: {},
        ENG: {}
      }
    };
    
    // Инициализируем структуру для кодов автора
    if (!author.individInfo.RUS.authorCodes) {
      author.individInfo.RUS.authorCodes = {};
    }
    if (!author.individInfo.ENG.authorCodes) {
      author.individInfo.ENG.authorCodes = {};
    }
    
    inputs.forEach(input => {
      const field = input.dataset.field;
      const lang = input.dataset.lang;
      // Для textarea сохраняем переносы строк, для input - обрезаем пробелы
      const value = input.tagName === "TEXTAREA" ? input.value : input.value.trim();
      
      if (lang === "CODES") {
        // Коды одинаковые для обоих языков
        author.individInfo.RUS.authorCodes[field] = value;
        author.individInfo.ENG.authorCodes[field] = value;
      } else if (lang === "RUS") {
        author.individInfo.RUS[field] = value;
        // Email одинаковый для обоих языков - сразу копируем в ENG (даже если пустой)
        if (field === "email") {
          author.individInfo.ENG.email = value;
        }
      } else if (lang === "ENG") {
        author.individInfo.ENG[field] = value;
        // Email одинаковый для обоих языков - сразу копируем в RUS (даже если пустой)
        if (field === "email") {
          author.individInfo.RUS.email = value;
        }
      }
    });
    
    // Email одинаковый для обоих языков - убеждаемся, что он синхронизирован
    const emailRus = author.individInfo.RUS.email || "";
    const emailEng = author.individInfo.ENG.email || "";
    // Если в одном поле есть email, а в другом нет - копируем
    if (emailRus && !emailEng) {
      author.individInfo.ENG.email = emailRus;
    } else if (emailEng && !emailRus) {
      author.individInfo.RUS.email = emailEng;
    }
    
    authors.push(author);
  });
  
  return authors;
}

(() => {
  const selected = new Set();
  let currentFieldId = null;

  const $ = (sel, root=document) => root.querySelector(sel);
  const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));

  function updatePanel() {
    const panel = $("#selectionPanel");
    const count = $("#selectedCount");
    if (!panel || !count) return;
    if (selected.size > 0) {
      panel.classList.add("active");
      count.textContent = String(selected.size);
    } else {
      panel.classList.remove("active");
      count.textContent = "0";
    }
  }

  function clearSelection() {
    selected.clear();
    $$(".line.selected").forEach(el => el.classList.remove("selected"));
    updatePanel();
  }

  function getSelectedTexts() {
    return Array.from(selected)
      .map(id => $(`.line[data-id="${CSS.escape(id)}"]`))
      .filter(Boolean)
      .map(el => $(".line-text", el)?.textContent || "")
      .map(t => t.trim())
      .filter(Boolean);
  }

  function extractDOI(text) {
    const m = text.match(/10\.\d{4,}\/[^\s\)]+/);
    return m ? m[0] : null;
  }

  function extractEmail(text) {
    // Регулярное выражение для поиска e-mail адресов
    // Поддерживает стандартные форматы: user@domain.com, user.name@domain.co.uk и т.д.
    const emailPattern = /\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b/g;
    const matches = text.match(emailPattern);
    if (matches && matches.length > 0) {
      // Возвращаем первый найденный e-mail
      return matches[0];
    }
    return null;
  }

  function extractORCID(text) {
    // ORCID формат: 0000-0000-0000-0000 (16 цифр, разделенных дефисами)
    // Также может быть в формате https://orcid.org/0000-0000-0000-0000
    const orcidPattern = /(?:orcid\.org\/)?(\d{4}-\d{4}-\d{4}-\d{3}[\dX])/i;
    const match = text.match(orcidPattern);
    return match ? match[1] : null;
  }

  function extractSPIN(text) {
    // SPIN обычно числовой код, может быть указан как "SPIN: 1234-5678", "SPIN-код 264275" или просто число
    // Поддерживаем различные форматы: SPIN-код, SPIN код, SPIN:, AuthorID и т.д.
    // SPIN код обычно состоит из 4-8 цифр, может быть с дефисами или без
    
    // Сначала ищем явные упоминания SPIN или AuthorID
    const explicitPatterns = [
      /(?:SPIN[-]?код|SPIN\s*код|SPIN[:\s-]+|AuthorID[:\s]+)\s*(\d{4,8}(?:[-.\s]\d+)*)/i,
    ];
    
    for (const pattern of explicitPatterns) {
      const match = text.match(pattern);
      if (match) {
        // Убираем дефисы, точки и пробелы, оставляем только цифры
        const spin = match[1].replace(/[-.\s]/g, '');
        // SPIN код обычно от 4 до 8 цифр
        if (spin.length >= 4 && spin.length <= 8) {
          // Проверяем, что это не часть email или другого кода
          const beforeMatch = text.substring(0, match.index);
          const afterMatch = text.substring(match.index + match[0].length);
          // Исключаем числа, которые являются частью email
          if (!beforeMatch.match(/@[\w.-]*$/) && !afterMatch.match(/^[\w.-]*@/)) {
            return spin;
          }
        }
      }
    }
    
    // Если явных упоминаний нет, ищем числа 4-8 цифр, но только если они не являются частью других кодов
    // Исключаем числа, которые являются частью email, DOI, ORCID, Scopus ID и т.д.
    const standaloneNumberPattern = /\b(\d{4,8})\b/g;
    const matches = [...text.matchAll(standaloneNumberPattern)];
    
    for (const match of matches) {
      const number = match[1];
      const matchIndex = match.index;
      const beforeText = text.substring(Math.max(0, matchIndex - 20), matchIndex);
      const afterText = text.substring(matchIndex + number.length, Math.min(text.length, matchIndex + number.length + 20));
      
      // Пропускаем, если это часть email
      if (beforeText.match(/@[\w.-]*$/) || afterText.match(/^[\w.-]*@/)) {
        continue;
      }
      
      // Пропускаем, если это часть DOI (10.xxxx/...)
      if (beforeText.match(/10\.\d{4,}/) || afterText.match(/^\/[^\s\)]+/)) {
        continue;
      }
      
      // Пропускаем, если это часть ORCID (0000-0000-0000-0000)
      if (beforeText.match(/orcid/i) || afterText.match(/^-\d{4}-\d{4}-\d{3}/)) {
        continue;
      }
      
      // Пропускаем, если это часть Scopus ID (обычно 8+ цифр)
      if (beforeText.match(/scopus/i) || number.length >= 8) {
        continue;
      }
      
      // Пропускаем, если это часть Researcher ID (A-1234-5678)
      if (beforeText.match(/researcher\s*id/i) || afterText.match(/^-\d{4}-\d{4}/)) {
        continue;
      }
      
      // Если число не является частью других кодов, возвращаем его как SPIN
      return number;
    }
    
    return null;
  }

  function extractScopusID(text) {
    // Scopus ID - числовой код, может быть указан как "Scopus ID: 123456789" или просто число
    const scopusPattern = /(?:Scopus\s*ID[:\s]*)?(\d{8,})/i;
    const match = text.match(scopusPattern);
    return match ? match[1] : null;
  }

  function extractResearcherID(text) {
    // Researcher ID может быть в формате A-XXXX-XXXX или просто числовой код
    const researcherPattern = /(?:Researcher\s*ID[:\s]*)?([A-Z]-\d{4}-\d{4}|\d{8,})/i;
    const match = text.match(researcherPattern);
    return match ? match[1] : null;
  }

  function autoExtractAuthorDataFromLine(text, authorIndex, skipField = null) {
    // Автоматически извлекает все доступные данные автора из строки и заполняет соответствующие поля
    // Это полезно, когда в одной строке содержится несколько данных (SPIN, email, AuthorID и т.д.)
    // skipField - поле, которое уже заполнено и не нужно извлекать повторно
    
    // Небольшая задержка, чтобы убедиться, что основное поле уже заполнено
    setTimeout(() => {
      // Извлекаем email, если он еще не заполнен и это не то поле, которое мы только что заполнили
      if (skipField !== "email") {
        const emailField = $(`.author-input[data-field="email"][data-lang="RUS"][data-index="${authorIndex}"]`);
        if (emailField) {
          const currentValue = emailField.value.trim();
          if (!currentValue) {
            const email = extractEmail(text);
            if (email) {
              emailField.value = email;
              emailField.dispatchEvent(new Event('input', { bubbles: true }));
              const emailEngField = $(`.author-input[data-field="email"][data-lang="ENG"][data-index="${authorIndex}"]`);
              if (emailEngField) {
                emailEngField.value = email;
                emailEngField.dispatchEvent(new Event('input', { bubbles: true }));
              }
            }
          }
        }
      }
      
      // Извлекаем SPIN, если он еще не заполнен и это не то поле, которое мы только что заполнили
      if (skipField !== "spin") {
        const spinField = $(`.author-input[data-field="spin"][data-lang="CODES"][data-index="${authorIndex}"]`);
        if (spinField) {
          const currentValue = spinField.value.trim();
          if (!currentValue) {
            const spin = extractSPIN(text);
            if (spin) {
              spinField.value = spin;
              spinField.dispatchEvent(new Event('input', { bubbles: true }));
            }
          }
        }
      }
      
      // Извлекаем ORCID, если он еще не заполнен и это не то поле, которое мы только что заполнили
      if (skipField !== "orcid") {
        const orcidField = $(`.author-input[data-field="orcid"][data-lang="CODES"][data-index="${authorIndex}"]`);
        if (orcidField) {
          const currentValue = orcidField.value.trim();
          if (!currentValue) {
            const orcid = extractORCID(text);
            if (orcid) {
              orcidField.value = orcid;
              orcidField.dispatchEvent(new Event('input', { bubbles: true }));
            }
          }
        }
      }
      
      // Извлекаем Scopus ID, если он еще не заполнен и это не то поле, которое мы только что заполнили
      if (skipField !== "scopusid") {
        const scopusField = $(`.author-input[data-field="scopusid"][data-lang="CODES"][data-index="${authorIndex}"]`);
        if (scopusField) {
          const currentValue = scopusField.value.trim();
          if (!currentValue) {
            const scopusId = extractScopusID(text);
            if (scopusId) {
              scopusField.value = scopusId;
              scopusField.dispatchEvent(new Event('input', { bubbles: true }));
            }
          }
        }
      }
      
      // Извлекаем Researcher ID, если он еще не заполнен и это не то поле, которое мы только что заполнили
      if (skipField !== "researcherid") {
        const researcherField = $(`.author-input[data-field="researcherid"][data-lang="CODES"][data-index="${authorIndex}"]`);
        if (researcherField) {
          const currentValue = researcherField.value.trim();
          if (!currentValue) {
            const researcherId = extractResearcherID(text);
            if (researcherId) {
              researcherField.value = researcherId;
              researcherField.dispatchEvent(new Event('input', { bubbles: true }));
            }
          }
        }
      }
    }, 10); // Небольшая задержка 10мс для гарантии, что основное поле заполнено
  }

  function removeCountryFromAddress(text) {
    // Список названий стран на русском и английском языках
    const countries = [
      // Русские названия
      'Россия', 'Российская Федерация', 'РФ',
      'Украина', 'Беларусь', 'Белоруссия', 'Казахстан',
      'Германия', 'Франция', 'Италия', 'Испания', 'Польша',
      'США', 'Соединенные Штаты', 'Соединённые Штаты', 'Соединенные Штаты Америки', 'Соединённые Штаты Америки',
      'Великобритания', 'Соединенное Королевство', 'Соединённое Королевство',
      'Китай', 'Япония', 'Индия', 'Бразилия',
      // Английские названия
      'Russia', 'Russian Federation', 'RF',
      'Ukraine', 'Belarus', 'Kazakhstan',
      'Germany', 'France', 'Italy', 'Spain', 'Poland',
      'USA', 'United States', 'United States of America', 'US', 'U.S.', 'U.S.A.',
      'United Kingdom', 'UK', 'U.K.',
      'China', 'Japan', 'India', 'Brazil',
      // Общие паттерны
      'Российская', 'Российской', 'Российскому',
      'Russian', 'Russians'
    ];
    
    let cleanedText = text.trim();
    
    // Удаляем названия стран из текста
    for (const country of countries) {
      // Создаем регулярное выражение для поиска названия страны
      // Ищем как отдельное слово (с границами слов) и в конце строки
      const pattern = new RegExp(`\\b${country.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'gi');
      cleanedText = cleanedText.replace(pattern, '').trim();
    }
    
    // Удаляем лишние запятые и пробелы
    cleanedText = cleanedText.replace(/^[,.\s]+|[,.\s]+$/g, '').trim();
    cleanedText = cleanedText.replace(/\s*,\s*,/g, ','); // Убираем двойные запятые
    cleanedText = cleanedText.replace(/\s{2,}/g, ' '); // Убираем множественные пробелы
    
    return cleanedText;
  }

  function removeNameFromText(text) {
    // Паттерны для удаления ФИО из текста
    // Русские имена: Фамилия Имя Отчество, Имя Отчество Фамилия, Фамилия И.О., И.О. Фамилия
    // Английские имена: First Last, Last, First, First M. Last, Last, First M.
    
    let cleanedText = text.trim();
    
    // Паттерны для русских имен
    const russianPatterns = [
      // Фамилия Имя Отчество (полное)
      /\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\b/g,
      // Имя Отчество Фамилия
      /\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\b/g,
      // Фамилия И.О.
      /\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.\s*[А-ЯЁ]\./g,
      // И.О. Фамилия
      /\b[А-ЯЁ]\.\s*[А-ЯЁ]\.\s+[А-ЯЁ][а-яё]+\b/g,
      // Фамилия И.
      /\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\./g,
      // И. Фамилия
      /\b[А-ЯЁ]\.\s+[А-ЯЁ][а-яё]+\b/g,
    ];
    
    // Паттерны для английских имен
    const englishPatterns = [
      // First Last
      /\b[A-Z][a-z]+\s+[A-Z][a-z]+\b/g,
      // Last, First
      /\b[A-Z][a-z]+,\s*[A-Z][a-z]+\b/g,
      // First M. Last
      /\b[A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+\b/g,
      // Last, First M.
      /\b[A-Z][a-z]+,\s*[A-Z][a-z]+\s+[A-Z]\./g,
      // First Last, Jr./Sr.
      /\b[A-Z][a-z]+\s+[A-Z][a-z]+,\s*(?:Jr\.?|Sr\.?|III|II|IV)\b/gi,
    ];
    
    // Удаляем русские имена
    for (const pattern of russianPatterns) {
      cleanedText = cleanedText.replace(pattern, '').trim();
    }
    
    // Удаляем английские имена
    for (const pattern of englishPatterns) {
      cleanedText = cleanedText.replace(pattern, '').trim();
    }
    
    // Удаляем лишние запятые, точки и пробелы
    cleanedText = cleanedText.replace(/^[,.\s]+|[,.\s]+$/g, '').trim();
    cleanedText = cleanedText.replace(/\s*,\s*,/g, ','); // Убираем двойные запятые
    cleanedText = cleanedText.replace(/\s{2,}/g, ' '); // Убираем множественные пробелы
    
    return cleanedText;
  }

  function extractDate(text) {
    if (!text) return null;
    const datePatterns = [
      /\b(\d{1,2}[./]\d{1,2}[./]\d{4})\b/,
      /\b(\d{4}[-./]\d{1,2}[-./]\d{1,2})\b/,
      /\b(\d{1,2}[-]\d{1,2}[-]\d{4})\b/,
    ];
    for (const pattern of datePatterns) {
      const match = text.match(pattern);
      if (match) {
        let date = match[1].replace(/[\/-]/g, '.');
        if (/^\d{4}\.\d{1,2}\.\d{1,2}$/.test(date)) {
          const parts = date.split('.');
          date = `${parts[2]}.${parts[1]}.${parts[0]}`;
        }
        return date;
      }
    }
    return null;
  }

  function extractUDC(text) {
    if (!text) return null;
    const udcPatterns = [
      /(?:УДК|UDC)\s*:?\s*([0-9.]+(?:[-–—][0-9.]+)?)/i,
      /\b([0-9]{1,3}(?:\.[0-9]+)*(?:[-–—][0-9.]+)?)\b/,
    ];
    for (const pattern of udcPatterns) {
      const match = text.match(pattern);
      if (match) return match[1].trim();
    }
    return null;
  }

  function extractYear(text) {
    if (!text) return null;
    const yearPattern = /\b(19\d{2}|20\d{2})\b/;
    const match = text.match(yearPattern);
    if (match) {
      const year = parseInt(match[1], 10);
      if (year >= 1900 && year <= 2100) return String(year);
    }
    return null;
  }

  function processKeywords(text) {
    if (!text) return "";
    let cleaned = text.replace(/^(Keywords|Ключевые слова)\s*:?\s*/i, "").trim();
    if (cleaned.includes(";")) {
      return cleaned.split(";").map(s => s.trim()).filter(Boolean).join("; ");
    }
    if (cleaned.includes(",")) {
      return cleaned.split(",").map(s => s.trim()).filter(Boolean).join("; ");
    }
    return cleaned;
  }

  function countKeywords(text) {
    if (!text || !text.trim()) return 0;
    const cleaned = text.trim();
    // Подсчитываем количество ключевых слов, разделенных точкой с запятой или запятой
    if (cleaned.includes(";")) {
      return cleaned.split(";").map(s => s.trim()).filter(Boolean).length;
    }
    if (cleaned.includes(",")) {
      return cleaned.split(",").map(s => s.trim()).filter(Boolean).length;
    }
    // Если нет разделителей, считаем как одно слово
    return cleaned ? 1 : 0;
  }

  function updateKeywordsCount(fieldId) {
    const field = document.getElementById(fieldId);
    const countEl = document.getElementById(fieldId + "-count");
    if (!field || !countEl) return;
    
    const count = countKeywords(field.value);
    countEl.textContent = `Количество: ${count}`;
  }

  window.countOrganizations = function(text) {
    if (!text || !text.trim()) return 0;
    const cleaned = text.trim();
    // Подсчитываем количество организаций, разделенных точкой с запятой или запятой
    if (cleaned.includes(";")) {
      return cleaned.split(";").map(s => s.trim()).filter(Boolean).length;
    }
    if (cleaned.includes(",")) {
      return cleaned.split(",").map(s => s.trim()).filter(Boolean).length;
    }
    // Если нет разделителей, считаем как одну организацию
    return cleaned ? 1 : 0;
  };

  window.updateOrgCount = function(authorIndex, lang) {
    const field = document.querySelector(`.author-input[data-field="orgName"][data-lang="${lang}"][data-index="${authorIndex}"]`);
    const countEl = document.getElementById(`org-count-${lang.toLowerCase()}-${authorIndex}`);
    if (!field || !countEl) return;
    
    const count = window.countOrganizations(field.value);
    countEl.textContent = `Количество организаций: ${count}`;
  };

  window.countReferences = function(text) {
    if (!text || !text.trim()) return 0;
    // Подсчитываем количество источников - каждая непустая строка = один источник
    const lines = text.split("\n")
      .map(line => line.trim())
      .filter(line => line.length > 0);
    return lines.length;
  };

  window.updateReferencesCount = function(fieldId) {
    const field = document.getElementById(fieldId);
    const countEl = document.getElementById(fieldId + "-count");
    if (!field || !countEl) return;
    
    const count = window.countReferences(field.value);
    countEl.textContent = `Количество источников: ${count}`;
  };

  function processFunding(text) {
    if (!text) return "";
    return text.replace(/^(Финансирование|Funding)\s*[.:]?\s*/i, "").replace(/^(Финансирование|Funding)\s*/i, "").trim();
  }

  function processAnnotation(text) {
    if (!text) return "";
    // Удаляем префикс "Аннотация", "Annotation" или "Abstract" в начале текста (с возможными двоеточиями и пробелами)
    return text.replace(/^(Аннотация|Annotation|Abstract)\s*[.:]?\s*/i, "").trim();
  }

  function processReferences(texts) {
    const processed = [];
    texts.forEach(text => {
      // Удаляем нумерацию в начале строки (например, "1. ", "2. "), но сохраняем остальной текст
      let cleaned = String(text).replace(/^\d+\.\s*/, "").replace(/\t/g, " ").replace(/\s+/g, " ").trim();
      if (!cleaned) return;
      const isUrl = /^(https?:\/\/|doi\.org\/|doi:\s*|http:\/\/dx\.doi\.org\/)/i.test(cleaned);
      if (isUrl && processed.length > 0) {
        processed[processed.length - 1] += " " + cleaned;
      } else {
        processed.push(cleaned);
      }
    });
    return processed.filter(Boolean);
  }
  
  function mergeDoiUrlWithReferences(refs) {
    if (!refs || refs.length === 0) return refs;
    const result = [];
    const doiUrlPattern = /^(https?:\/\/|doi\.org\/|doi:\s*|http:\/\/dx\.doi\.org\/)/i;
    refs.forEach(ref => {
      const cleaned = String(ref).trim();
      if (!cleaned) return;
      if (doiUrlPattern.test(cleaned) && result.length > 0) {
        result[result.length - 1] += " " + cleaned;
      } else {
        result.push(cleaned);
      }
    });
    return result;
  }

  function markField(fieldId) {
    const field = document.getElementById(fieldId);
    if (!field) return;
    const group = field.closest(".field-group");
    if (!group) return;
    group.classList.add("active");
    setTimeout(() => group.classList.remove("active"), 1200);
  }

  function setLinesInfo(fieldId, n) {
    const el = document.getElementById(fieldId + "-lines");
    if (el) el.textContent = n ? `Выбрано строк: ${n}` : "";
  }

  function getActiveAuthorIndex() {
    // Находим первого открытого (expanded) автора
    const authorItems = $$(".author-item");
    for (const item of authorItems) {
      const index = item.dataset.authorIndex;
      if (index !== undefined) {
        const details = $(`#author-details-${index}`);
        if (details && details.style.display !== "none") {
          return parseInt(index, 10);
        }
      }
    }
    // Если ни один не открыт, возвращаем первого автора
    if (authorItems.length > 0) {
      const firstIndex = authorItems[0].dataset.authorIndex;
      if (firstIndex !== undefined) {
        return parseInt(firstIndex, 10);
      }
    }
    return 0;
  }

  function applySelectionToField(fieldId) {
    const texts = getSelectedTexts();
    if (!texts.length) return;
    const fullText = texts.join(" ");
    let value = "";
    
    // Обработка полей авторов
    if (fieldId.startsWith("author_")) {
      const authorIndex = getActiveAuthorIndex();
      const parts = fieldId.split("_");
      if (parts.length < 2) return;
      
      const fieldName = parts[1]; // surname, initials, org, address, email, other
      const lang = parts.length >= 3 ? parts[2] : null; // rus, eng, или null для email
      
      // Находим соответствующее поле автора
      let targetField = null;
      if (fieldName === "surname") {
        if (!lang) return;
        targetField = $(`.author-input[data-field="surname"][data-lang="${lang.toUpperCase()}"][data-index="${authorIndex}"]`);
        value = fullText.trim();
      } else if (fieldName === "initials") {
        if (!lang) return;
        targetField = $(`.author-input[data-field="initials"][data-lang="${lang.toUpperCase()}"][data-index="${authorIndex}"]`);
        value = fullText.trim();
      } else if (fieldName === "org") {
        if (!lang) return;
        targetField = $(`.author-input[data-field="orgName"][data-lang="${lang.toUpperCase()}"][data-index="${authorIndex}"]`);
        value = fullText.trim();
      } else if (fieldName === "address") {
        if (!lang) return;
        targetField = $(`.author-input[data-field="address"][data-lang="${lang.toUpperCase()}"][data-index="${authorIndex}"]`);
        // Удаляем названия стран из адреса
        value = removeCountryFromAddress(fullText);
      } else if (fieldName === "email") {
        targetField = $(`.author-input[data-field="email"][data-lang="RUS"][data-index="${authorIndex}"]`);
        // Извлекаем только e-mail адрес из выделенного текста
        const email = extractEmail(fullText);
        if (!email) {
          alert("E-mail адрес не найден в выделенном тексте. Убедитесь, что выделен текст, содержащий e-mail (например: user@domain.com)");
          return;
        }
        value = email;
        // E-mail одинаковый для обоих языков - всегда копируем в ENG поле
        const emailEngField = $(`.author-input[data-field="email"][data-lang="ENG"][data-index="${authorIndex}"]`);
        if (emailEngField) {
          emailEngField.value = email;
        }
        // Автоматически извлекаем и заполняем другие поля из той же строки (пропускаем email, т.к. он уже заполнен)
        autoExtractAuthorDataFromLine(fullText, authorIndex, "email");
      } else if (fieldName === "spin") {
        targetField = $(`.author-input[data-field="spin"][data-lang="CODES"][data-index="${authorIndex}"]`);
        if (!targetField) {
          alert(`Поле SPIN не найдено. Убедитесь, что форма автора открыта.`);
          return;
        }
        const spin = extractSPIN(fullText);
        if (!spin) {
          alert("SPIN код не найден в выделенном тексте. Убедитесь, что выделен текст, содержащий SPIN (например: SPIN: 1234-5678)");
          return;
        }
        value = spin;
        // Автоматически извлекаем и заполняем другие поля из той же строки (пропускаем spin, т.к. он уже заполнен)
        autoExtractAuthorDataFromLine(fullText, authorIndex, "spin");
      } else if (fieldName === "orcid") {
        targetField = $(`.author-input[data-field="orcid"][data-lang="CODES"][data-index="${authorIndex}"]`);
        if (!targetField) {
          alert(`Поле ORCID не найдено. Убедитесь, что форма автора открыта.`);
          return;
        }
        const orcid = extractORCID(fullText);
        if (!orcid) {
          alert("ORCID не найден в выделенном тексте. Убедитесь, что выделен текст, содержащий ORCID (например: 0000-0000-0000-0000)");
          return;
        }
        value = orcid;
        // Автоматически извлекаем и заполняем другие поля из той же строки (пропускаем orcid, т.к. он уже заполнен)
        autoExtractAuthorDataFromLine(fullText, authorIndex, "orcid");
      } else if (fieldName === "scopusid") {
        targetField = $(`.author-input[data-field="scopusid"][data-lang="CODES"][data-index="${authorIndex}"]`);
        if (!targetField) {
          alert(`Поле Scopus ID не найдено. Убедитесь, что форма автора открыта.`);
          return;
        }
        const scopusId = extractScopusID(fullText);
        if (!scopusId) {
          alert("Scopus ID не найден в выделенном тексте. Убедитесь, что выделен текст, содержащий Scopus ID (например: 123456789)");
          return;
        }
        value = scopusId;
        // Автоматически извлекаем и заполняем другие поля из той же строки (пропускаем scopusid, т.к. он уже заполнен)
        autoExtractAuthorDataFromLine(fullText, authorIndex, "scopusid");
      } else if (fieldName === "researcherid") {
        targetField = $(`.author-input[data-field="researcherid"][data-lang="CODES"][data-index="${authorIndex}"]`);
        if (!targetField) {
          alert(`Поле Researcher ID не найдено. Убедитесь, что форма автора открыта.`);
          return;
        }
        const researcherId = extractResearcherID(fullText);
        if (!researcherId) {
          alert("Researcher ID не найден в выделенном тексте. Убедитесь, что выделен текст, содержащий Researcher ID (например: A-1234-5678)");
          return;
        }
        value = researcherId;
        // Автоматически извлекаем и заполняем другие поля из той же строки (пропускаем researcherid, т.к. он уже заполнен)
        autoExtractAuthorDataFromLine(fullText, authorIndex, "researcherid");
      } else if (fieldName === "other") {
        if (!lang) return;
        targetField = $(`.author-input[data-field="otherInfo"][data-lang="${lang.toUpperCase()}"][data-index="${authorIndex}"]`);
        // Вставляем текст как есть, без удаления ФИО
        value = fullText.trim();
      } else {
        // Неизвестное поле
        return;
      }
      
      if (!targetField) {
        alert(`Поле автора не найдено. Убедитесь, что форма автора открыта.`);
        return;
      }
      
      targetField.value = value;
      // Триггерим событие input для обновления всех обработчиков
      targetField.dispatchEvent(new Event('input', { bubbles: true }));
      targetField.focus();
      
      // Обновляем имя автора в заголовке, если изменились фамилия или инициалы
      if (fieldName === "surname" || fieldName === "initials") {
        updateAuthorName(authorIndex);
      }
      
      // Открываем форму автора, если она закрыта
      const authorDetails = $(`#author-details-${authorIndex}`);
      if (authorDetails && authorDetails.style.display === "none") {
        toggleAuthorDetails(authorIndex);
      }
      
      // Подсвечиваем поле
      const authorItem = $(`.author-item[data-author-index="${authorIndex}"]`);
      if (authorItem) {
        authorItem.classList.add("active");
        setTimeout(() => authorItem.classList.remove("active"), 1200);
      }
      
      clearSelection();
      return;
    }
    
    // Обработка обычных полей
    const field = document.getElementById(fieldId);
    if (!field) return;
    
    if (fieldId === "doi") {
      const doi = extractDOI(fullText);
      if (!doi) {
        alert("DOI не найден в выделенном тексте. Нужен формат 10.xxxx/xxxxx");
        return;
      }
      value = doi;
    } else if (fieldId === "keywords" || fieldId === "keywords_en") {
      const kw = processKeywords(fullText);
      value = kw;
      // Обновляем счетчик после установки значения
      setTimeout(() => updateKeywordsCount(fieldId), 100);
    } else if (fieldId === "references_ru" || fieldId === "references_en") {
      const refs = processReferences(texts);
      value = refs.join("\n");
      // Обновляем счетчик после установки значения
      setTimeout(() => {
        if (window.updateReferencesCount) {
          window.updateReferencesCount(fieldId);
        }
      }, 100);
    } else if (fieldId === "received_date" || fieldId === "reviewed_date" || fieldId === "accepted_date" || fieldId === "date_publication") {
      const date = extractDate(fullText);
      if (date) {
        value = date;
      } else {
        alert("Дата не найдена в выделенном тексте. Ожидается формат: DD.MM.YYYY, DD/MM/YYYY или YYYY-MM-DD");
        return;
      }
    } else if (fieldId === "udc") {
      const udc = extractUDC(fullText);
      value = udc ? udc : fullText.trim();
    } else if (fieldId === "funding" || fieldId === "funding_en") {
      const funding = processFunding(fullText);
      value = funding;
    } else if (fieldId === "annotation" || fieldId === "annotation_en") {
      // Обрабатываем аннотацию: удаляем префикс "Аннотация" или "Annotation" если он есть
      const annotation = processAnnotation(fullText);
      // Если поле уже содержит текст, добавляем через пробел
      value = field.value.trim() ? (field.value.trim() + " " + annotation) : annotation;
    } else if (fieldId === "year") {
      const year = extractYear(fullText);
      if (year) {
        value = year;
      } else {
        alert("Год не найден в выделенном тексте. Ожидается 4-значный год (например, 2025)");
        return;
      }
    } else {
      value = fullText;
    }
    field.value = value;
    field.focus();
    setLinesInfo(fieldId, selected.size);
    markField(fieldId);
    clearSelection();
  }

  document.addEventListener("DOMContentLoaded", () => {
    // Очищаем префикс "Аннотация" из полей аннотации при загрузке страницы
    const annotationField = document.getElementById("annotation");
    if (annotationField && annotationField.value) {
      const cleaned = processAnnotation(annotationField.value);
      if (cleaned !== annotationField.value) {
        annotationField.value = cleaned;
      }
    }
    
    const annotationEnField = document.getElementById("annotation_en");
    if (annotationEnField && annotationEnField.value) {
      const cleaned = processAnnotation(annotationEnField.value);
      if (cleaned !== annotationEnField.value) {
        annotationEnField.value = cleaned;
      }
    }
    
    // Автоматическая прокрутка к началу статьи, если используется общий файл
    
    
    const textContent = $("#textContent");
    if (textContent) {
      textContent.addEventListener("click", (e) => {
        const line = e.target.closest(".line");
        if (!line) return;
        const id = line.dataset.id;
        if (!id) return;
        
        const lineNumber = parseInt(line.dataset.line, 10);
        const isShiftPressed = e.shiftKey;
        
        if (isShiftPressed && selected.size > 0) {
          // Выделение диапазона при Shift+клик
          const selectedNumbers = Array.from(selected)
            .map(sid => {
              const selLine = $(`.line[data-id="${CSS.escape(sid)}"]`);
              return selLine ? parseInt(selLine.dataset.line, 10) : null;
            })
            .filter(n => n !== null)
            .sort((a, b) => a - b);
          
          if (selectedNumbers.length > 0) {
            const minLine = Math.min(...selectedNumbers, lineNumber);
            const maxLine = Math.max(...selectedNumbers, lineNumber);
            
            // Выделяем все строки в диапазоне
            $$(".line").forEach(l => {
              const lNum = parseInt(l.dataset.line, 10);
              if (lNum >= minLine && lNum <= maxLine) {
                const lid = l.dataset.id;
                selected.add(lid);
                l.classList.add("selected");
              }
            });
          }
        } else if (selected.size > 0 && !selected.has(id)) {
          // Если уже есть выделенные строки и кликнули на другую, выделяем диапазон
          const selectedNumbers = Array.from(selected)
            .map(sid => {
              const selLine = $(`.line[data-id="${CSS.escape(sid)}"]`);
              return selLine ? parseInt(selLine.dataset.line, 10) : null;
            })
            .filter(n => n !== null);
          
          if (selectedNumbers.length > 0) {
            const minLine = Math.min(...selectedNumbers, lineNumber);
            const maxLine = Math.max(...selectedNumbers, lineNumber);
            
            // Выделяем все строки в диапазоне
            $$(".line").forEach(l => {
              const lNum = parseInt(l.dataset.line, 10);
              if (lNum >= minLine && lNum <= maxLine) {
                const lid = l.dataset.id;
                selected.add(lid);
                l.classList.add("selected");
              }
            });
          } else {
            // Обычное выделение/снятие выделения
            if (selected.has(id)) {
              selected.delete(id);
              line.classList.remove("selected");
            } else {
              selected.add(id);
              line.classList.add("selected");
            }
          }
        } else {
          // Обычное выделение/снятие выделения
          if (selected.has(id)) {
            selected.delete(id);
            line.classList.remove("selected");
          } else {
            selected.add(id);
            line.classList.add("selected");
          }
        }
        
        updatePanel();
      });
    }

    document.addEventListener("focusin", (e) => {
      const el = e.target;
      if (!el) return;
      if ((el.tagName === "INPUT" || el.tagName === "TEXTAREA") && el.id) {
        currentFieldId = el.id;
      }
    });

    const clearBtn = $("#clearBtn");
    if (clearBtn) clearBtn.addEventListener("click", clearSelection);

    const panel = $("#selectionPanel");
    if (panel) {
      panel.addEventListener("click", (e) => {
        const btn = e.target.closest("button");
        if (!btn) return;
        const action = btn.dataset.action;
        if (action === "cancel") {
          clearSelection();
          return;
        }
        const assign = btn.dataset.assign;
        if (assign) applySelectionToField(assign);
      });
    }

    const searchInput = $("#searchInput");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        const q = (e.target.value || "").toLowerCase();
        const lines = $$(".line");
        if (q.length < 2) {
          lines.forEach(l => { l.style.display = ""; l.style.background = ""; });
          return;
        }
        lines.forEach(l => {
          const t = l.textContent.toLowerCase();
          if (t.includes(q)) {
            l.style.display = "";
            l.style.background = "#fff9c4";
          } else {
            l.style.display = "none";
          }
        });
      });

    // Инициализация счетчиков ключевых слов при загрузке
    const keywordsField = $("#keywords");
    const keywordsEnField = $("#keywords_en");
    if (keywordsField) {
      updateKeywordsCount("keywords");
      keywordsField.addEventListener("input", () => updateKeywordsCount("keywords"));
    }
    if (keywordsEnField) {
      updateKeywordsCount("keywords_en");
      keywordsEnField.addEventListener("input", () => updateKeywordsCount("keywords_en"));
    }
    
    // Инициализация счетчиков литературы при загрузке
    const referencesRuField = $("#references_ru");
    const referencesEnField = $("#references_en");
    if (referencesRuField) {
      if (window.updateReferencesCount) {
        window.updateReferencesCount("references_ru");
        referencesRuField.addEventListener("input", () => window.updateReferencesCount("references_ru"));
      }
    }
    if (referencesEnField) {
      if (window.updateReferencesCount) {
        window.updateReferencesCount("references_en");
        referencesEnField.addEventListener("input", () => window.updateReferencesCount("references_en"));
      }
    }
    
    // Инициализация обработчиков для обновления имен авторов
    const existingAuthors = $$(".author-item");
    existingAuthors.forEach(item => {
      const index = parseInt(item.dataset.authorIndex, 10);
      if (!isNaN(index)) {
        attachAuthorNameListeners(index);
        // Дополнительная инициализация счетчиков организаций
        setTimeout(() => {
          if (window.updateOrgCount) {
            window.updateOrgCount(index, "RUS");
            window.updateOrgCount(index, "ENG");
          }
        }, 200);
      }
    });

    const form = $("#metadataForm");
    if (form) {
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(form);
        const data = {};
        for (const [k, v] of fd.entries()) data[k] = v;
        
        // Собираем данные авторов из раскрывающегося меню
        data.authors = collectAuthorsData();
        
        ["references_ru", "references_en"].forEach((k) => {
          if (data[k]) {
            const refs = String(data[k]).split("\n").map(s => s.trim()).filter(Boolean);
            data[k] = mergeDoiUrlWithReferences(refs);
          }
        });
        try {
          const resp = await fetch("/markup/4 ???????? 6.json/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
          });
          const result = await resp.json();
          if (result.success) {
            // Сохраняем информацию о том, что файл был только что сохранен
            // Это позволит сразу подсветить его на главной странице
            const savedFiles = JSON.parse(localStorage.getItem("recently_saved_files") || "[]");
            const currentFile = "4 ???????? 6.json";
            if (!savedFiles.includes(currentFile)) {
              savedFiles.push(currentFile);
              localStorage.setItem("recently_saved_files", JSON.stringify(savedFiles));
            }
            
            // Показываем красивое уведомление
            toast("Метаданные успешно сохранены! Статья помечена как обработанная.");
            // Перенаправляем на главную страницу с небольшой задержкой, чтобы увидеть уведомление
            // На главной странице файл автоматически будет показан как обработанный (зеленый цвет и галочка)
            setTimeout(() => {
              window.location.href = "/";
            }, 1500);
          } else {
            alert("Ошибка при сохранении: " + result.error);
          }
        } catch (err) {
          alert("Ошибка: " + err.message);
        }
      });
    }
  });
})();
