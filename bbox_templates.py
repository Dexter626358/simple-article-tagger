"""
Модуль для управления шаблонами bbox для автоматического извлечения данных из PDF.

Шаблоны сохраняются по ISSN журнала и содержат координаты областей для каждого поля.
При накоплении достаточного количества примеров система предлагает использовать шаблон.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class BboxCoords:
    """Координаты области в PDF."""
    page: int  # номер страницы (0-based), -1 = последняя страница
    pdf_x1: float
    pdf_y1: float
    pdf_x2: float
    pdf_y2: float
    page_width: float = 595.0  # A4 width
    page_height: float = 842.0  # A4 height
    
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BboxCoords":
        return cls(**data)
    
    def normalize(self) -> "BboxCoords":
        """Нормализует координаты относительно размера страницы (0-1)."""
        return BboxCoords(
            page=self.page,
            pdf_x1=self.pdf_x1 / self.page_width,
            pdf_y1=self.pdf_y1 / self.page_height,
            pdf_x2=self.pdf_x2 / self.page_width,
            pdf_y2=self.pdf_y2 / self.page_height,
            page_width=1.0,
            page_height=1.0,
        )
    
    def denormalize(self, page_width: float, page_height: float) -> "BboxCoords":
        """Денормализует координаты для конкретного размера страницы."""
        return BboxCoords(
            page=self.page,
            pdf_x1=self.pdf_x1 * page_width,
            pdf_y1=self.pdf_y1 * page_height,
            pdf_x2=self.pdf_x2 * page_width,
            pdf_y2=self.pdf_y2 * page_height,
            page_width=page_width,
            page_height=page_height,
        )


@dataclass
class FieldTemplate:
    """Шаблон для одного поля метаданных."""
    field_id: str
    samples: list[BboxCoords] = field(default_factory=list)
    
    def add_sample(self, coords: BboxCoords) -> None:
        """Добавляет новый образец координат."""
        # Нормализуем перед сохранением
        normalized = coords.normalize()
        self.samples.append(normalized)
        # Ограничиваем количество образцов
        if len(self.samples) > 20:
            self.samples = self.samples[-20:]
    
    def get_average_coords(self) -> BboxCoords | None:
        """Возвращает усреднённые координаты из всех образцов."""
        if not self.samples:
            return None
        
        # Группируем по номеру страницы
        by_page: dict[int, list[BboxCoords]] = {}
        for s in self.samples:
            by_page.setdefault(s.page, []).append(s)
        
        # Берём самую частую страницу
        most_common_page = max(by_page.keys(), key=lambda p: len(by_page[p]))
        page_samples = by_page[most_common_page]
        
        if len(page_samples) < 2:
            # Недостаточно данных — возвращаем единственный образец
            return page_samples[0] if page_samples else None
        
        # Усредняем координаты
        return BboxCoords(
            page=most_common_page,
            pdf_x1=statistics.mean(s.pdf_x1 for s in page_samples),
            pdf_y1=statistics.mean(s.pdf_y1 for s in page_samples),
            pdf_x2=statistics.mean(s.pdf_x2 for s in page_samples),
            pdf_y2=statistics.mean(s.pdf_y2 for s in page_samples),
            page_width=1.0,
            page_height=1.0,
        )
    
    def get_confidence(self) -> float:
        """
        Возвращает уровень уверенности в шаблоне (0-1).
        Зависит от количества образцов и их согласованности.
        """
        if len(self.samples) < 2:
            return 0.0
        
        # Базовая уверенность от количества образцов
        count_confidence = min(len(self.samples) / 5, 1.0)  # 5+ образцов = 100%
        
        # Проверяем согласованность координат (низкая дисперсия = высокая уверенность)
        try:
            x1_std = statistics.stdev(s.pdf_x1 for s in self.samples)
            y1_std = statistics.stdev(s.pdf_y1 for s in self.samples)
            x2_std = statistics.stdev(s.pdf_x2 for s in self.samples)
            y2_std = statistics.stdev(s.pdf_y2 for s in self.samples)
            
            # Средняя стандартная ошибка (нормализованные координаты 0-1)
            avg_std = (x1_std + y1_std + x2_std + y2_std) / 4
            # Низкая ошибка (<0.05) = высокая согласованность
            consistency = max(0, 1 - avg_std * 10)
        except statistics.StatisticsError:
            consistency = 0.5
        
        return count_confidence * consistency
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "field_id": self.field_id,
            "samples": [s.to_dict() for s in self.samples],
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FieldTemplate":
        return cls(
            field_id=data["field_id"],
            samples=[BboxCoords.from_dict(s) for s in data.get("samples", [])],
        )


@dataclass
class JournalTemplate:
    """Шаблон для журнала (по ISSN)."""
    issn: str
    journal_name: str = ""
    fields: dict[str, FieldTemplate] = field(default_factory=dict)
    total_articles_processed: int = 0
    
    def add_bbox(self, field_id: str, coords: BboxCoords) -> None:
        """Добавляет bbox для поля."""
        if field_id not in self.fields:
            self.fields[field_id] = FieldTemplate(field_id=field_id)
        self.fields[field_id].add_sample(coords)
    
    def get_suggestions(self, page_width: float = 595.0, page_height: float = 842.0, 
                        min_confidence: float = 0.3) -> dict[str, dict[str, Any]]:
        """
        Возвращает предложения bbox для всех полей с достаточной уверенностью.
        
        Returns:
            {field_id: {"coords": BboxCoords, "confidence": float, "sample_count": int}}
        """
        suggestions = {}
        for field_id, template in self.fields.items():
            confidence = template.get_confidence()
            if confidence >= min_confidence:
                avg_coords = template.get_average_coords()
                if avg_coords:
                    # Денормализуем для конкретного размера страницы
                    denormalized = avg_coords.denormalize(page_width, page_height)
                    suggestions[field_id] = {
                        "coords": denormalized.to_dict(),
                        "confidence": round(confidence, 2),
                        "sample_count": len(template.samples),
                    }
        return suggestions
    
    def increment_processed(self) -> None:
        """Увеличивает счётчик обработанных статей."""
        self.total_articles_processed += 1
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "issn": self.issn,
            "journal_name": self.journal_name,
            "fields": {k: v.to_dict() for k, v in self.fields.items()},
            "total_articles_processed": self.total_articles_processed,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JournalTemplate":
        return cls(
            issn=data["issn"],
            journal_name=data.get("journal_name", ""),
            fields={k: FieldTemplate.from_dict(v) for k, v in data.get("fields", {}).items()},
            total_articles_processed=data.get("total_articles_processed", 0),
        )


class BboxTemplateManager:
    """Менеджер шаблонов bbox."""
    
    def __init__(self, templates_dir: Path | None = None):
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "bbox_templates"
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, JournalTemplate] = {}
    
    def _get_template_path(self, issn: str) -> Path:
        """Возвращает путь к файлу шаблона."""
        safe_issn = issn.replace("-", "_").replace("/", "_")
        return self.templates_dir / f"{safe_issn}.json"
    
    def get_template(self, issn: str) -> JournalTemplate | None:
        """Загружает шаблон для журнала."""
        if issn in self._cache:
            return self._cache[issn]
        
        path = self._get_template_path(issn)
        if not path.exists():
            return None
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            template = JournalTemplate.from_dict(data)
            self._cache[issn] = template
            return template
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Error loading template for {issn}: {e}")
            return None
    
    def get_or_create_template(self, issn: str, journal_name: str = "") -> JournalTemplate:
        """Загружает или создаёт шаблон для журнала."""
        template = self.get_template(issn)
        if template is None:
            template = JournalTemplate(issn=issn, journal_name=journal_name)
            self._cache[issn] = template
        elif journal_name and not template.journal_name:
            template.journal_name = journal_name
        return template
    
    def save_template(self, template: JournalTemplate) -> None:
        """Сохраняет шаблон в файл."""
        path = self._get_template_path(template.issn)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)
        self._cache[template.issn] = template
    
    def add_bbox_sample(self, issn: str, field_id: str, coords: BboxCoords, 
                        journal_name: str = "") -> None:
        """Добавляет образец bbox и сохраняет шаблон."""
        template = self.get_or_create_template(issn, journal_name)
        template.add_bbox(field_id, coords)
        self.save_template(template)
    
    def get_suggestions_for_journal(self, issn: str, page_width: float = 595.0, 
                                     page_height: float = 842.0) -> dict[str, Any]:
        """
        Возвращает предложения bbox для журнала.
        
        Returns:
            {
                "issn": str,
                "journal_name": str,
                "total_processed": int,
                "suggestions": {field_id: {...}}
            }
        """
        template = self.get_template(issn)
        if template is None:
            return {
                "issn": issn,
                "journal_name": "",
                "total_processed": 0,
                "suggestions": {},
            }
        
        return {
            "issn": issn,
            "journal_name": template.journal_name,
            "total_processed": template.total_articles_processed,
            "suggestions": template.get_suggestions(page_width, page_height),
        }
    
    def list_templates(self) -> list[dict[str, Any]]:
        """Возвращает список всех доступных шаблонов."""
        templates = []
        for path in self.templates_dir.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                templates.append({
                    "issn": data.get("issn", path.stem),
                    "journal_name": data.get("journal_name", ""),
                    "total_processed": data.get("total_articles_processed", 0),
                    "fields_count": len(data.get("fields", {})),
                })
            except (json.JSONDecodeError, KeyError):
                continue
        return sorted(templates, key=lambda t: t.get("total_processed", 0), reverse=True)
    
    def delete_template(self, issn: str) -> bool:
        """Удаляет шаблон."""
        path = self._get_template_path(issn)
        if path.exists():
            path.unlink()
            self._cache.pop(issn, None)
            return True
        return False


# Глобальный экземпляр менеджера
_manager: BboxTemplateManager | None = None


def get_template_manager(templates_dir: Path | None = None) -> BboxTemplateManager:
    """Возвращает глобальный экземпляр менеджера шаблонов."""
    global _manager
    if _manager is None:
        _manager = BboxTemplateManager(templates_dir)
    return _manager
