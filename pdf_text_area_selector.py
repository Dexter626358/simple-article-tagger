#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF Area Selector for Text PDFs (InDesign)
Скрипт для выделения областей в текстовых PDF и извлечения текста напрямую.
"""

from __future__ import annotations

import json
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from PIL import Image, ImageTk

# Попытка импорта необходимых библиотек
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    print("⚠ pdf2image не установлен. Установите: pip install pdf2image")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("⚠ pdfplumber не установлен. Установите: pip install pdfplumber")


class PDFTextAreaSelector:
    """Класс для выделения областей в текстовых PDF и извлечения текста напрямую."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PDF Text Area Selector (InDesign)")
        self.root.geometry("1200x800")
        
        # Переменные
        self.pdf_path: Optional[Path] = None
        self.pdf_images: List[Image.Image] = []  # Для отображения
        self.pdf_pages: List[Any] = []  # pdfplumber страницы
        self.current_page = 0
        self.scale_factor = 1.0
        self.page_width = 0
        self.page_height = 0
        self.selection_start: Optional[Tuple[int, int]] = None
        self.selection_end: Optional[Tuple[int, int]] = None
        self.selection_rect: Optional[int] = None
        self.selections: List[Dict[str, Any]] = []
        self.is_selecting = False
        
        # Создаем интерфейс
        self.create_ui()
        
    def create_ui(self):
        """Создает пользовательский интерфейс."""
        # Верхняя панель с кнопками
        toolbar = tk.Frame(self.root, bg="#f0f0f0", pady=5)
        toolbar.pack(fill=tk.X)
        
        tk.Button(toolbar, text="📁 Открыть PDF", command=self.open_pdf, 
                 bg="#4caf50", fg="white", padx=10, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(toolbar, text="◀ Предыдущая", command=self.prev_page,
                 padx=10, pady=5).pack(side=tk.LEFT, padx=5)
        
        self.page_label = tk.Label(toolbar, text="Страница: 0/0", padx=10)
        self.page_label.pack(side=tk.LEFT, padx=5)
        
        tk.Button(toolbar, text="Следующая ▶", command=self.next_page,
                 padx=10, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(toolbar, text="📝 Извлечь текст", command=self.extract_text,
                 bg="#2196f3", fg="white", padx=10, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(toolbar, text="💾 Сохранить координаты", command=self.save_coordinates,
                 bg="#ff9800", fg="white", padx=10, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(toolbar, text="🗑 Очистить выделения", command=self.clear_selections,
                 padx=10, pady=5).pack(side=tk.LEFT, padx=5)
        
        # Основная область с Canvas и текстовым полем
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Левая панель - Canvas для PDF
        left_panel = tk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        canvas_frame = tk.Frame(left_panel)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar для Canvas
        v_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.canvas = tk.Canvas(canvas_frame, bg="gray",
                               yscrollcommand=v_scrollbar.set,
                               xscrollcommand=h_scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        v_scrollbar.config(command=self.canvas.yview)
        h_scrollbar.config(command=self.canvas.xview)
        
        # Привязываем события мыши
        self.canvas.bind("<Button-1>", self.on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        
        # Правая панель - результаты
        right_panel = tk.Frame(main_frame, width=400)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        
        tk.Label(right_panel, text="Извлеченный текст:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=5)
        
        self.text_output = scrolledtext.ScrolledText(right_panel, wrap=tk.WORD, height=20)
        self.text_output.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Список выделений
        tk.Label(right_panel, text="Выделенные области:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        self.selections_listbox = tk.Listbox(right_panel, height=8)
        self.selections_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.selections_listbox.bind("<Double-Button-1>", self.on_selection_double_click)
        
        # Статусная строка
        self.status_label = tk.Label(self.root, text="Готов к работе", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        
    def open_pdf(self):
        """Открывает PDF файл."""
        if not PDFPLUMBER_AVAILABLE:
            messagebox.showerror("Ошибка", 
                               "pdfplumber не установлен.\n"
                               "Установите: pip install pdfplumber")
            return
        
        file_path = filedialog.askopenfilename(
            title="Выберите PDF файл",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        self.pdf_path = Path(file_path)
        self.status_label.config(text=f"Загрузка PDF: {self.pdf_path.name}...")
        self.root.update()
        
        try:
            # Открываем PDF через pdfplumber
            pdf = pdfplumber.open(str(self.pdf_path))
            self.pdf_pages = list(pdf.pages)
            pdf.close()
            
            if not self.pdf_pages:
                messagebox.showerror("Ошибка", "Не удалось загрузить PDF файл")
                return
            
            # Конвертируем в изображения для отображения (если доступно)
            if PDF2IMAGE_AVAILABLE:
                try:
                    self.pdf_images = convert_from_path(
                        str(self.pdf_path),
                        dpi=150,  # Меньше DPI для быстрой загрузки
                        fmt='png'
                    )
                except Exception as e:
                    print(f"Предупреждение: не удалось конвертировать в изображения: {e}")
                    self.pdf_images = []
            else:
                self.pdf_images = []
            
            self.current_page = 0
            self.selections = []
            self.display_page()
            self.status_label.config(text=f"Загружено страниц: {len(self.pdf_pages)}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке PDF:\n{str(e)}")
            self.status_label.config(text="Ошибка загрузки")
    
    def display_page(self):
        """Отображает текущую страницу PDF."""
        if not self.pdf_pages or self.current_page >= len(self.pdf_pages):
            return
        
        # Очищаем canvas
        self.canvas.delete("all")
        
        # Получаем страницу из pdfplumber
        page = self.pdf_pages[self.current_page]
        self.page_width = page.width
        self.page_height = page.height
        
        # Пытаемся отобразить изображение, если доступно
        if self.pdf_images and self.current_page < len(self.pdf_pages):
            page_image = self.pdf_images[self.current_page]
            
            # Масштабируем для отображения (максимальная ширина 800px)
            max_width = 800
            if page_image.width > max_width:
                scale = max_width / page_image.width
                new_width = int(page_image.width * scale)
                new_height = int(page_image.height * scale)
                page_image = page_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                self.scale_factor = scale
            else:
                self.scale_factor = 1.0
            
            # Конвертируем в PhotoImage
            self.photo = ImageTk.PhotoImage(page_image)
            
            # Отображаем на canvas
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        else:
            # Если нет изображения, рисуем рамку с информацией
            display_width = 800
            display_height = int(self.page_height * (display_width / self.page_width))
            self.scale_factor = display_width / self.page_width
            
            self.canvas.create_rectangle(0, 0, display_width, display_height, 
                                       outline="black", fill="white", width=2)
            self.canvas.create_text(display_width/2, display_height/2, 
                                  text=f"Страница {self.current_page + 1}\n"
                                       f"Размер: {int(self.page_width)}x{int(self.page_height)}",
                                  font=("Arial", 16))
        
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        
        # Обновляем метку страницы
        self.page_label.config(text=f"Страница: {self.current_page + 1}/{len(self.pdf_pages)}")
        
        # Отображаем сохраненные выделения для этой страницы
        self.redraw_selections()
    
    def prev_page(self):
        """Переход на предыдущую страницу."""
        if self.pdf_pages and self.current_page > 0:
            self.current_page -= 1
            self.display_page()
    
    def next_page(self):
        """Переход на следующую страницу."""
        if self.pdf_pages and self.current_page < len(self.pdf_pages) - 1:
            self.current_page += 1
            self.display_page()
    
    def on_mouse_press(self, event):
        """Обработчик нажатия мыши - начало выделения."""
        if not self.pdf_pages:
            return
        
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        self.selection_start = (int(x), int(y))
        self.is_selecting = True
    
    def on_mouse_drag(self, event):
        """Обработчик перетаскивания мыши - обновление выделения."""
        if not self.is_selecting or not self.selection_start:
            return
        
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        self.selection_end = (int(x), int(y))
        
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
        
        x1, y1 = self.selection_start
        x2, y2 = self.selection_end
        
        self.selection_rect = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline="red", width=2, dash=(5, 5)
        )
    
    def on_mouse_release(self, event):
        """Обработчик отпускания мыши - завершение выделения."""
        if not self.is_selecting or not self.selection_start:
            return
        
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        self.selection_end = (int(x), int(y))
        self.is_selecting = False
        
        x1, y1 = self.selection_start
        x2, y2 = self.selection_end
        
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        
        if abs(x2 - x1) < 10 or abs(y2 - y1) < 10:
            if self.selection_rect:
                self.canvas.delete(self.selection_rect)
                self.selection_rect = None
            return
        
        # Конвертируем координаты экрана в координаты PDF
        pdf_x1 = x1 / self.scale_factor
        pdf_y1 = y1 / self.scale_factor
        pdf_x2 = x2 / self.scale_factor
        pdf_y2 = y2 / self.scale_factor
        
        # В PDF координаты идут снизу вверх, нужно инвертировать Y
        pdf_y1_inv = self.page_height - pdf_y2
        pdf_y2_inv = self.page_height - pdf_y1
        
        selection = {
            "page": self.current_page,
            "screen_x1": x1,
            "screen_y1": y1,
            "screen_x2": x2,
            "screen_y2": y2,
            "pdf_x1": pdf_x1,
            "pdf_y1": pdf_y1_inv,
            "pdf_x2": pdf_x2,
            "pdf_y2": pdf_y2_inv,
            "text": ""
        }
        
        self.selections.append(selection)
        
        rect_id = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline="blue", width=2
        )
        selection["rect_id"] = rect_id
        
        self.update_selections_list()
        
        self.status_label.config(text=f"Выделена область: ({int(x1)}, {int(y1)}) - ({int(x2)}, {int(y2)})")
    
    def redraw_selections(self):
        """Перерисовывает сохраненные выделения для текущей страницы."""
        for selection in self.selections:
            if selection["page"] == self.current_page:
                rect_id = self.canvas.create_rectangle(
                    selection["screen_x1"], selection["screen_y1"],
                    selection["screen_x2"], selection["screen_y2"],
                    outline="blue", width=2
                )
                selection["rect_id"] = rect_id
    
    def update_selections_list(self):
        """Обновляет список выделений."""
        self.selections_listbox.delete(0, tk.END)
        for i, sel in enumerate(self.selections):
            if sel["page"] == self.current_page:
                text_preview = sel["text"][:30] + "..." if sel["text"] else "Не обработано"
                self.selections_listbox.insert(tk.END, f"Область {i+1}: {text_preview}")
    
    def on_selection_double_click(self, event):
        """Обработчик двойного клика на выделении."""
        selection = self.selections_listbox.curselection()
        if selection:
            idx = selection[0]
            page_selections = [s for s in self.selections if s["page"] == self.current_page]
            if idx < len(page_selections):
                sel = page_selections[idx]
                if sel["text"]:
                    messagebox.showinfo("Текст выделения", sel["text"])
    
    def extract_text(self):
        """Извлекает текст из выделенных областей напрямую из PDF."""
        if not PDFPLUMBER_AVAILABLE:
            messagebox.showerror("Ошибка",
                               "pdfplumber не установлен.\n"
                               "Установите: pip install pdfplumber")
            return
        
        if not self.pdf_pages:
            messagebox.showwarning("Предупреждение", "Сначала откройте PDF файл")
            return
        
        if not self.selections:
            messagebox.showwarning("Предупреждение", "Нет выделенных областей")
            return
        
        self.status_label.config(text="Извлечение текста...")
        self.root.update()
        
        extracted_texts = []
        
        for selection in self.selections:
            if selection["page"] != self.current_page:
                continue
            
            try:
                # Получаем страницу из pdfplumber
                page = self.pdf_pages[selection["page"]]
                
                # Используем crop для извлечения текста из области
                # Координаты в pdfplumber: (x0, top, x1, bottom)
                # top и bottom идут сверху вниз
                cropped = page.crop((
                    selection["pdf_x1"],
                    self.page_height - selection["pdf_y2"],  # top
                    selection["pdf_x2"],
                    self.page_height - selection["pdf_y1"]   # bottom
                ))
                
                # Извлекаем текст
                text = cropped.extract_text()
                if text:
                    text = text.strip()
                else:
                    text = "(Текст не найден)"
                
                selection["text"] = text
                extracted_texts.append(f"Область {len(extracted_texts) + 1}:\n{text}\n{'='*50}\n")
                
            except Exception as e:
                selection["text"] = f"Ошибка: {str(e)}"
                extracted_texts.append(f"Ошибка в области {len(extracted_texts) + 1}: {str(e)}\n")
        
        self.update_selections_list()
        
        self.text_output.delete(1.0, tk.END)
        self.text_output.insert(1.0, "\n".join(extracted_texts))
        
        self.status_label.config(text=f"Извлечено текста из {len(extracted_texts)} областей")
    
    def clear_selections(self):
        """Очищает все выделения на текущей странице."""
        if messagebox.askyesno("Подтверждение", "Очистить все выделения на текущей странице?"):
            for selection in self.selections:
                if selection["page"] == self.current_page and "rect_id" in selection:
                    self.canvas.delete(selection["rect_id"])
            
            self.selections = [s for s in self.selections if s["page"] != self.current_page]
            
            self.update_selections_list()
            self.text_output.delete(1.0, tk.END)
            self.status_label.config(text="Выделения очищены")
    
    def save_coordinates(self):
        """Сохраняет координаты выделенных областей в JSON файл."""
        if not self.selections:
            messagebox.showwarning("Предупреждение", "Нет выделенных областей для сохранения")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Сохранить координаты",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        output_data = {
            "pdf_file": str(self.pdf_path) if self.pdf_path else None,
            "total_pages": len(self.pdf_pages),
            "selections": []
        }
        
        for selection in self.selections:
            output_data["selections"].append({
                "page": selection["page"],
                "bbox": {
                    "x1": round(selection["pdf_x1"], 2),
                    "y1": round(selection["pdf_y1"], 2),
                    "x2": round(selection["pdf_x2"], 2),
                    "y2": round(selection["pdf_y2"], 2)
                },
                "text": selection.get("text", "")
            })
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("Успех", f"Координаты сохранены в:\n{file_path}")
            self.status_label.config(text=f"Координаты сохранены: {Path(file_path).name}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}")


def main():
    """Главная функция."""
    root = tk.Tk()
    app = PDFTextAreaSelector(root)
    root.mainloop()


if __name__ == "__main__":
    main()
