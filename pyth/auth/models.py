from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from auth.database import Base

class User(Base):
    __tablename__ = "auth"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    login: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    bio: Mapped["Bio | None"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)

class Bio(Base):
    __tablename__ = "bio"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("auth.id", ondelete="CASCADE"), unique=True)
    gender: Mapped[str | None] = mapped_column(String(1))
    age: Mapped[int | None] = mapped_column(Integer)
    weight: Mapped[float | None] = mapped_column(Numeric(6, 2))
    height: Mapped[float | None] = mapped_column(Numeric(6, 2))
    target_calories: Mapped[float | None] = mapped_column(Numeric(8, 2))
    target_proteins: Mapped[float | None] = mapped_column(Numeric(8, 2))
    target_fats: Mapped[float | None] = mapped_column(Numeric(8, 2))
    target_carbs: Mapped[float | None] = mapped_column(Numeric(8, 2))
    target_water: Mapped[float | None] = mapped_column(Numeric(8, 2))
    target_steps: Mapped[int | None] = mapped_column(Integer)
    activity_level: Mapped[str | None] = mapped_column(String(32))
    user: Mapped[User] = relationship(back_populates="bio")
