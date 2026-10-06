from datetime import date, datetime
from decimal import Decimal
from enum import Enum, IntEnum
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

def parsedate(val: date | str) -> date:
    if isinstance(val, date):
        return val
    for df in ("%Y-%m-%d", "%d.%m.%y"):
        try:
            return datetime.strptime(val, df).date()
        except ValueError:
            pass
    raise ValueError(f"Invalid date format: {val}. Use YYYY-MM-DD or DD.MM.YY")

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
    sweets = "sweets"
    baking = "baking"
    sauces = "sauces"
    milk = "milk"
    beverages = "beverages"
    dairy = "dairy"
    grains = "grains"
    other = "other"

class healcreate(BaseModel):
    gender: Gend = Field(description="Пол: m или f")
    age: int = Field(ge=12, le=125, description="Возраст, лет")
    weight: Decimal = Field(ge=0, le=400, description="Вес, кг")
    height: Decimal = Field(ge=0, le=2.5, description="Рост, м")
    activity_level: ActLvl = Field(description="Уровень активности от 1 до 5")
    target_goal: Goal = Field(description="Цель: 1 (похудение), 2 (набор массы), 3 (рекомпозиция), 4 (удержание)")
    target_steps: int = Field(default=0, ge=0, description="Цель шагов в день (0 — рассчитать автоматически)")
    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "gender": "m", "age": 25, "weight": 80, "height": 1.8,
                "activity_level": 1, "target_goal": 1, "target_steps": 0}})

class healresp(healcreate):
    id: int
    min_target_calories: Decimal = Field(description="Мин. граница калорий")
    max_target_calories: Decimal = Field(description="Макс. граница калорий")
    target_proteins: Decimal = Field(description="Рассчитанная норма белков (г)")
    target_fats: Decimal = Field(description="Рассчитанная норма жиров (г)")
    target_carbs: Decimal = Field(description="Рассчитанная норма углеводов (г)")
    target_water: Decimal = Field(description="Рассчитанная норма воды (л)")
    model_config = ConfigDict(from_attributes=True, json_encoders={Decimal: float})

class healupd(BaseModel):
    gender: Gend | None = Field(default=None, description="Пол: m или f")
    age: int | None = Field(default=None, ge=12, le=125, description="Возраст, лет")
    weight: Decimal | None = Field(default=None, ge=0, le=400, description="Вес, кг")
    height: Decimal | None = Field(default=None, ge=0, le=2.5, description="Рост, м")
    activity_level: ActLvl | None = Field(default=None, description="Уровень активности от 1 до 5")
    target_goal: Goal | None = Field(default=None, description="Цель: 1 (похудение), 2 (набор массы), 3 (рекомпозиция), 4 (удержание)")
    target_steps: int | None = Field(default=None, ge=0, description="Цель шагов в день")
    model_config = ConfigDict(use_enum_values=True)

class entrycreate(BaseModel):
    base_product_id: int | None = Field(default=None, description="ID базового продукта (если из каталога)")
    user_product_id: int | None = Field(default=None, description="ID пользовательского продукта (если из своих)")
    title: str | None = Field(default=None, min_length=1, max_length=255, description="Название (для разовой записи без продукта)")
    description: str | None = Field(default=None, description="Описание или заметка к записи")
    quantity_grams: Decimal | None = Field(default=None, gt=0, description="Количество продукта, граммы (обязательно при выборе продукта)")
    calories: Decimal | None = Field(default=None, ge=0, description="Калории (для разовой записи)")
    proteins: Decimal | None = Field(default=None, ge=0, description="Белки, г (для разовой записи)")
    fats: Decimal | None = Field(default=None, ge=0, description="Жиры, г (для разовой записи)")
    carbs: Decimal | None = Field(default=None, ge=0, description="Углеводы, г (для разовой записи)")
    product_type: ProdType | None = Field(default=None, description="Категория продукта")

    @model_validator(mode="after")
    def validate_entry(self):
        has_base = self.base_product_id is not None
        has_user = self.user_product_id is not None
        if has_base and has_user:
            raise ValueError("Укажите либо base_product_id, либо user_product_id, но не оба одновременно")
        if has_base or has_user:
            if self.quantity_grams is None:
                raise ValueError("quantity_grams обязателен при указании продукта")
        else:
            if self.calories is None:
                raise ValueError("Для разовой записи необходимо указать calories")
            if not self.title:
                self.title = "Перекус"
            if self.proteins is None:
                self.proteins = Decimal(0)
            if self.fats is None:
                self.fats = Decimal(0)
            if self.carbs is None:
                self.carbs = Decimal(0)
        return self

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "examples": [
                {"summary": "Продукт из каталога", "value": {"base_product_id": 1, "quantity_grams": 100}},
                {"summary": "Разовый перекус (быстрое добавление)", "value": {"title": "Перекус в кофейне", "calories": 250, "proteins": 5.0, "fats": 10.0, "carbs": 35.0, "product_type": "baking"}}]})

class entryupd(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255, description="Название")
    description: str | None = Field(default=None, description="Описание")
    quantity_grams: Decimal | None = Field(default=None, gt=0, description="Количество продукта, граммы")
    calories: Decimal | None = Field(default=None, ge=0, description="Калории")
    proteins: Decimal | None = Field(default=None, ge=0, description="Белки, г")
    fats: Decimal | None = Field(default=None, ge=0, description="Жиры, г")
    carbs: Decimal | None = Field(default=None, ge=0, description="Углеводы, г")
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
    created_at: datetime
    model_config = ConfigDict(from_attributes=True, json_encoders={Decimal: float})

class sheetcreate(BaseModel):
    sheet_date: date = Field(description="Дата: YYYY-MM-DD или DD.MM.YY")
    weight: Decimal | None = Field(default=None, ge=0, le=500, description="Вес в этот день, кг")
    @field_validator("sheet_date", mode="before")
    @classmethod
    def validate_sheet_date(cls, value: date | str) -> date:
        return parsedate(value)
    model_config = ConfigDict(json_schema_extra={"example": {"sheet_date": "2026-10-02", "weight": 80.5}})

class sheetupd(BaseModel):
    weight: Decimal | None = Field(default=None, ge=0, le=500, description="Вес в этот день, кг")

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
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    product_type: ProdType = Field(description="Категории: meatfish, garnish, vegetables, fruits, nuts, sweets, baking, sauces, milk, beverages, dairy, grains, other")
    calories: Decimal = Field(ge=0, description="Ккал на 100 г")
    fats: Decimal = Field(ge=0, description="Жиры на 100 г")
    proteins: Decimal = Field(ge=0, description="Белки на 100 г")
    carbs: Decimal = Field(ge=0, description="Углеводы на 100 г")

class produpd(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    product_type: ProdType | None = None
    calories: Decimal | None = Field(default=None, ge=0)
    fats: Decimal | None = Field(default=None, ge=0)
    proteins: Decimal | None = Field(default=None, ge=0)
    carbs: Decimal | None = Field(default=None, ge=0)

class prodresp(prodcreate):
    id: int
    model_config = ConfigDict(from_attributes=True, json_encoders={Decimal: float})

class favcreate(BaseModel):
    base_product_id: int | None = None
    user_product_id: int | None = None

class favresp(favcreate):
    id: int
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
    target_calories: Decimal | None = None
    days: list[daydyn] = []
    model_config = ConfigDict(json_encoders={Decimal: float})

