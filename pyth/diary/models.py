from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from diary.database import Base

class diarylist(Base):
    __tablename__ = "diary_sheets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    sheet_date: Mapped[date] = mapped_column("date", Date, index=True)
    weight: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    entries: Mapped[list["entry"]] = relationship("entry", back_populates="sheet", cascade="all, delete-orphan", order_by="entry.id")
    __table_args__ = (UniqueConstraint("user_id", "date", name="uix_user_date"),)

class entry(Base):
    __tablename__ = "entries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sheet_id: Mapped[int] = mapped_column(ForeignKey("diary_sheets.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column("desc", Text, nullable=True)
    calories: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    fats: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    proteins: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    carbs: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    water: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True, default=Decimal("0"))
    product_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    base_product_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_product_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quantity_grams: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sheet: Mapped["diarylist"] = relationship("diarylist", back_populates="entries")

class bio(Base):
    __tablename__ = "bio"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    gender: Mapped[str] = mapped_column(String(1))
    age: Mapped[int] = mapped_column(Integer)
    weight: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    height: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    target_goal: Mapped[int] = mapped_column(Integer)
    activity_level: Mapped[int] = mapped_column(Integer)
    target_steps: Mapped[int] = mapped_column(Integer, default=0)
    min_target_calories: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    max_target_calories: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    target_proteins: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    target_fats: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    target_carbs: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    target_water: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)

class baseprod(Base):
    __tablename__ = "base_products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)
    product_type: Mapped[str] = mapped_column(String(32))
    calories: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    fats: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    proteins: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    carbs: Mapped[Decimal] = mapped_column(Numeric(8, 2))

class userprod(Base):
    __tablename__ = "user_products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    product_type: Mapped[str] = mapped_column(String(32))
    calories: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    fats: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    proteins: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    carbs: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    __table_args__ = (UniqueConstraint("user_id", "idempotency_key", name="uix_user_product_idempotency"),)

class fav(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "base_product_id", "user_product_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    base_product_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_product_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

