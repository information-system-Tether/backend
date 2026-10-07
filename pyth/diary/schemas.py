from datetime import date, datetime
from decimal import Decimal
from enum import Enum, IntEnum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

def parsedate(val: date | str, allow_future: bool = True) -> date:
    if isinstance(val, date):
        d = val
    elif isinstance(val, str) and val.strip().lower() in ("today", "сегодня"):
        d = date.today()
    elif isinstance(val, str):
        d = None
        for df in ("%Y-%m-%d", "%d.%m.%y"):
            try:
                d = datetime.strptime(val.strip(), df).date()
                break
            except ValueError:
                pass
        if d is None:
            raise ValueError(f"Неверный формат даты или несуществующая календарная дата: {val}. Требуется использовать формат YYYY-MM-DD или 'today'")
    else:
        raise ValueError(f"Неверный формат даты: {val}. Требуется использовать формат YYYY-MM-DD или 'today'")
    if not allow_future and d > date.today():
        raise ValueError(f"Дата {d} ещё не наступила. Нельзя создать лист для даты из будущего")
    return d

class ActLvl(IntEnum):
    sedentary = 1
    light = 2
    moderate = 3
    high = 4
    extreme = 5

class Goal(IntEnum):
    losew = 1
    morem = 2
    recom = 3
    maint = 4

class Gend(str, Enum):
    m = "m"
    f = "f"

class ProdType(str, Enum):
    meatfish = "meatfish"
    garnish = "garnish"
    vegetables = "vegetables"
    fruits = "fruits"
    nuts = "nuts"
    sweets_candies = "sweets&candies"
    sweets = "sweets"
    baking = "baking"
    sauces_spices = "sauces&spices"
    sauces = "sauces"
    sauses_spices = "sauses&spices"
    sausesandspices = "sausesandspices"
    milk = "milk"
    beverages = "beverages"
    dairy = "dairy"
    grains = "grains"
    oils = "oils"
    soups = "soups"
    fastfood = "fastfood"
    supplements = "supplements"
    other = "other"

class healcreate(BaseModel):
    gender: Gend = Field(description="Пол: m (мужской) или f (женский)")
    age: int = Field(ge=12, le=125, description="Возраст, полных лет")
    weight: Decimal = Field(gt=0, le=400, description="Текущий вес, кг")
    height: Decimal = Field(gt=0, le=2.5, description="Рост, метры (например 1.80)")
    activity_level: ActLvl = Field(description="Уровень активности: 1 - сидячий, 2 - лёгкая, 3 - умеренная, 4 - высокая, 5 - экстремальная")
    target_goal: Goal = Field(description="Цель: 1 - похудение, 2 - набор массы, 3 - рекомпозиция, 4 - удержание веса")
    target_steps: int = Field(default=0, ge=0, description="Цель шагов в день (0 - рассчитать автоматически математическим модулем)")
    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "gender": "m", "age": 25, "weight": 80, "height": 1.8,
                "activity_level": 1, "target_goal": 1, "target_steps": 0}})

class healresp(healcreate):
    id: int
    min_target_calories: Decimal = Field(description="Нижняя граница нормы калорий (рассчитано мат. модулем)")
    max_target_calories: Decimal = Field(description="Верхняя граница нормы калорий (рассчитано мат. модулем)")
    target_proteins: Decimal = Field(description="Суточная норма белков, г (рассчитано мат. модулем)")
    target_fats: Decimal = Field(description="Суточная норма жиров, г (рассчитано мат. модулем)")
    target_carbs: Decimal = Field(description="Суточная норма углеводов, г (рассчитано мат. модулем)")
    target_water: Decimal = Field(description="Суточная норма воды, л (рассчитано мат. модулем)")
    model_config = ConfigDict(from_attributes=True, json_encoders={Decimal: float})

class healupd(BaseModel):
    gender: Gend | None = Field(default=None, description="Пол: m (мужской) или f (женский)")
    age: int | None = Field(default=None, ge=12, le=125, description="Возраст, полных лет")
    weight: Decimal | None = Field(default=None, gt=0, le=400, description="Текущий вес, кг")
    height: Decimal | None = Field(default=None, gt=0, le=2.5, description="Рост, метры (например 1.80)")
    activity_level: ActLvl | None = Field(default=None, description="Уровень активности: 1 - сидячий, 2 - лёгкая, 3 - умеренная, 4 - высокая, 5 - экстремальная")
    target_goal: Goal | None = Field(default=None, description="Цель: 1 - похудение, 2 - набор массы, 3 - рекомпозиция, 4 - удержание веса")
    target_steps: int | None = Field(default=None, ge=0, description="Цель шагов в день (0 - рассчитать автоматически математическим модулем)")
    model_config = ConfigDict(use_enum_values=True)

class entrycreate(BaseModel):
    base_product_id: int | None = Field(default=None, gt=0, description="ID базового продукта (если из каталога)")
    user_product_id: int | None = Field(default=None, gt=0, description="ID пользовательского продукта (если из своих)")
    name: str | None = Field(default=None, min_length=1, max_length=100, description="Название (для разовой записи без ID продукта, до 100 символов)")
    title: str | None = Field(default=None, min_length=1, max_length=100, description="Название (альтернативное поле, до 100 символов)")
    description: str | None = Field(default=None, max_length=200, description="Описание или заметка к записи (до 200 символов)")
    quantity_grams: Decimal | None = Field(default=None, gt=0, description="Количество продукта, граммы (строго больше 0)")
    calories: Decimal | None = Field(default=None, ge=0, description="Калории (для разовой записи без ID, не менее 0)")
    fats: Decimal | None = Field(default=None, ge=0, description="Жиры, г (для разовой записи без ID, не менее 0)")
    proteins: Decimal | None = Field(default=None, ge=0, description="Белки, г (для разовой записи без ID, не менее 0)")
    carbs: Decimal | None = Field(default=None, ge=0, description="Углеводы, г (для разовой записи без ID, не менее 0)")
    product_type: ProdType | None = Field(default=None, description="Категория продукта")

    @model_validator(mode="before")
    @classmethod
    def sync_name_and_title(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "name" in data and not data.get("title"):
                data["title"] = data["name"]
            elif "title" in data and not data.get("name"):
                data["name"] = data["title"]
        return data

    @model_validator(mode="after")
    def validate_entry(self):
        has_base = self.base_product_id is not None
        has_user = self.user_product_id is not None
        if has_base and has_user:
            raise ValueError("Требуется указать либо base_product_id, либо user_product_id, но не оба одновременно")
        if has_base or has_user:
            if self.quantity_grams is None:
                raise ValueError("Поле quantity_grams обязательно при указании продукта")
            if self.quantity_grams <= 0:
                raise ValueError("Количество продукта в граммах должно быть строго больше 0 (не может быть равным 0 или отрицательным)")
        else:
            if self.quantity_grams is not None and self.quantity_grams <= 0:
                raise ValueError("Количество продукта в граммах должно быть строго больше 0 (не может быть равным 0 или отрицательным)")
            if self.calories is None:
                raise ValueError("Для разовой записи (без ID) необходимо указать calories")
            if self.calories < 0:
                raise ValueError("Калории не могут быть отрицательными")
            if not self.title and not self.name:
                self.title = "Перекус"
                self.name = "Перекус"
            elif self.name and not self.title:
                self.title = self.name
            elif self.title and not self.name:
                self.name = self.title
            if self.proteins is None:
                self.proteins = Decimal(0)
            elif self.proteins < 0:
                raise ValueError("Белки не могут быть отрицательными")
            if self.fats is None:
                self.fats = Decimal(0)
            elif self.fats < 0:
                raise ValueError("Жиры не могут быть отрицательными")
            if self.carbs is None:
                self.carbs = Decimal(0)
            elif self.carbs < 0:
                raise ValueError("Углеводы не могут быть отрицательными")
        return self

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "name": "Филе минтая в панировке Экспродов",
                "description": "Рыбные котлетки в кляре, ",
                "product_type": "meatfish",
                "calories": 130,
                "fats": 16,
                "proteins": 6.5,
                "carbs": 5,
                "quantity_grams": 100
            }
        }
    )

class entryupd(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100, description="Название (до 100 символов)")
    description: str | None = Field(default=None, max_length=200, description="Описание (до 200 символов)")
    quantity_grams: Decimal | None = Field(default=None, gt=0, description="Количество продукта, граммы (строго больше 0)")
    calories: Decimal | None = Field(default=None, ge=0, description="Калории (не менее 0)")
    proteins: Decimal | None = Field(default=None, ge=0, description="Белки, г (не менее 0)")
    fats: Decimal | None = Field(default=None, ge=0, description="Жиры, г (не менее 0)")
    carbs: Decimal | None = Field(default=None, ge=0, description="Углеводы, г (не менее 0)")
    water: Decimal | None = Field(default=None, ge=0, description="Вода, л (не менее 0)")
    product_type: ProdType | None = Field(default=None, description="Категория продукта")
    model_config = ConfigDict(use_enum_values=True)

class entryresp(BaseModel):
    id: int
    sheet_id: int
    base_product_id: int | None
    user_product_id: int | None
    title: str
    description: str | None = None
    product_type: ProdType | None = None
    quantity_grams: Decimal | None
    calories: Decimal | None
    fats: Decimal | None
    proteins: Decimal | None
    carbs: Decimal | None
    water: Decimal | None = Decimal("0")
    created_at: datetime
    model_config = ConfigDict(from_attributes=True, json_encoders={Decimal: float})

class sheetcreate(BaseModel):
    sheet_date: date = Field(description="Дата: YYYY-MM-DD или DD.MM.YY")
    weight: Decimal | None = Field(default=None, gt=0, le=500, description="Вес в этот день, кг (строго больше 0, до 500.0)")
    @field_validator("sheet_date", mode="before")
    @classmethod
    def validate_sheet_date(cls, value: date | str) -> date:
        return parsedate(value, allow_future=False)
    model_config = ConfigDict(json_schema_extra={"example": {"sheet_date": "2026-10-02", "weight": 80.5}})

class sheetupd(BaseModel):
    weight: Decimal | None = Field(default=None, gt=0, le=500, description="Вес в этот день, кг (строго больше 0, до 500.0)")

class sheetresp(BaseModel):
    id: int
    user_id: int
    sheet_date: date
    weight: Decimal | None
    total_calories: Decimal
    total_fats: Decimal
    total_proteins: Decimal
    total_carbs: Decimal
    total_water: Decimal
    entries: list[entryresp] = []
    model_config = ConfigDict(from_attributes=True, json_encoders={Decimal: float})

class prodcreate(BaseModel):
    name: str = Field(min_length=1, max_length=100, description="Название продукта (от 1 до 100 символов)")
    description: str | None = Field(default=None, max_length=200, description="Описание продукта (до 200 символов)")
    product_type: ProdType = Field(description="Категории: meatfish (мясо/рыба), garnish (гарниры), vegetables (овощи), fruits (фрукты/ягоды), nuts (орехи), sweets&candies (сладости/конфеты), baking (выпечка), sauces&spices (соусы/специи), beverages (напитки), dairy (молочные продукты), grains (крупы/каши), oils (масла/жиры), soups (супы), fastfood (фастфуд), supplements (добавки/спортпит), other (прочее)")
    calories: Decimal = Field(ge=0, description="Ккал на 100 г (не менее 0)")
    fats: Decimal = Field(ge=0, description="Жиры на 100 г (не менее 0)")
    proteins: Decimal = Field(ge=0, description="Белки на 100 г (не менее 0)")
    carbs: Decimal = Field(ge=0, description="Углеводы на 100 г (не менее 0)")
    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "name": "Филе минтая в панировке Экспродов",
                "description": "Рыбные котлетки в кляре, ",
                "product_type": "meatfish",
                "calories": 130,
                "fats": 15,
                "proteins": 6.5,
                "carbs": 5
            }
        }
    )

class produpd(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100, description="Название продукта (от 1 до 100 символов)")
    description: str | None = Field(default=None, max_length=200, description="Описание продукта (до 200 символов)")
    product_type: ProdType | None = None
    calories: Decimal | None = Field(default=None, ge=0, description="Ккал на 100 г (не менее 0)")
    fats: Decimal | None = Field(default=None, ge=0, description="Жиры на 100 г (не менее 0)")
    proteins: Decimal | None = Field(default=None, ge=0, description="Белки на 100 г (не менее 0)")
    carbs: Decimal | None = Field(default=None, ge=0, description="Углеводы на 100 г (не менее 0)")

class prodresp(prodcreate):
    id: int
    model_config = ConfigDict(from_attributes=True, json_encoders={Decimal: float})

class favcreate(BaseModel):
    base_product_id: int | None = Field(default=None, description="ID базового продукта из каталога", gt=0)
    user_product_id: int | None = Field(default=None, description="ID своего (пользовательского) продукта", gt=0)

    @model_validator(mode="after")
    def validate_fav(self):
        has_base = self.base_product_id is not None
        has_user = self.user_product_id is not None
        if has_base == has_user:
            raise ValueError("Необходимо указать ровно один идентификатор продукта: base_product_id или user_product_id")
        return self

class favresp(BaseModel):
    id: int
    base_product_id: int | None = None
    user_product_id: int | None = None
    model_config = ConfigDict(from_attributes=True)

class syncdata(BaseModel):
    health: healupd | None = None
    products: list[prodcreate] | None = None
    favorites: list[favcreate] | None = None
    sheets: list[sheetcreate] | None = None
    entries: list[entrycreate] | None = None

class syncresp(BaseModel):
    health: healresp | None = None
    products: list[prodresp] = []
    favorites: list[favresp] = []
    sheets: list[sheetresp] = []

class daydyn(BaseModel):
    sheet_date: date
    weight: Decimal | None = None
    total_calories: Decimal
    total_proteins: Decimal
    total_fats: Decimal
    total_carbs: Decimal
    total_water: Decimal
    entries_count: int
    model_config = ConfigDict(json_encoders={Decimal: float})

class dynresp(BaseModel):
    start_date: date
    end_date: date
    days_count: int
    average_calories: Decimal
    average_proteins: Decimal
    average_fats: Decimal
    average_carbs: Decimal
    average_water: Decimal
    average_weight: Decimal | None = None
    target_calories: Decimal | None = None
    days: list[daydyn] = []
    model_config = ConfigDict(json_encoders={Decimal: float})

