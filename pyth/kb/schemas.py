from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class kbcreate(BaseModel):
    question: str = Field(min_length=3, max_length=1000, description="Вопрос")
    answer: str = Field(min_length=1, max_length=5000, description="Ответ")
    category: str = Field(default="general", max_length=64, description="Категория (general, calories, nutrients, methods, standards, hydration)")
    block: str | None = Field(default=None, max_length=128, description="Тематический блок (например, 'Калории, энергетический баланс и метаболизм')")
    tags: str | None = Field(default=None, max_length=512, description="Ключевые слова через запятую")
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "Как рассчитать калорийность блюда из нескольких ингредиентов?",
                "answer": "Взвесьте каждый ингредиент отдельно, найдите КБЖУ на 100 г каждого, пересчитайте пропорционально фактическому весу и сложите все значения.",
                "category": "methods",
                "block": "Методы взвешивания, расчёта и учёта",
                "tags": "калорийность,расчёт,ингредиенты,блюдо"
            }
        }
    )

class kbupd(BaseModel):
    question: str | None = Field(default=None, min_length=3, max_length=1000, description="Вопрос")
    answer: str | None = Field(default=None, min_length=1, max_length=5000, description="Ответ")
    category: str | None = Field(default=None, max_length=64, description="Категория")
    block: str | None = Field(default=None, max_length=128, description="Тематический блок")
    tags: str | None = Field(default=None, max_length=512, description="Ключевые слова через запятую")

class kbresp(BaseModel):
    id: int
    question: str
    answer: str
    category: str
    block: str | None = None
    tags: str | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class kbpaginated(BaseModel):
    items: list[kbresp] = Field(description="Список статей базы знаний на текущей странице")
    total: int = Field(description="Общее количество статей по заданным фильтрам")
    page: int = Field(description="Текущий номер страницы")
    page_size: int = Field(description="Количество статей на страницу")
    total_pages: int = Field(description="Общее количество страниц")
    has_next: bool = Field(description="Есть ли следующая страница")
    has_prev: bool = Field(description="Есть ли предыдущая страница")
