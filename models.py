from __future__ import annotations # To have the forward refrencing

from datetime import UTC, datetime, date as d # For date

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, TIMESTAMP, func, Text, Float # Some column types and relation keys
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Our class from base
from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String(15), nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    height_cm: Mapped[int] = mapped_column(Integer, nullable=False)
    goal: Mapped[str] = mapped_column(String(50), default='balanced')
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC))
    food_logs: Mapped[list[Food]] = relationship(back_populates="user")
    exercise_logs: Mapped[list[Exercise]] = relationship(back_populates="user")
    sleep_logs: Mapped[list[Sleep]] = relationship(back_populates="user")
    weight_logs: Mapped[list[Weight]] = relationship(back_populates="user")
    custom_foods: Mapped[list[Custom_Food]] = relationship(back_populates="user")


class Food(Base):
    __tablename__ = "food_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    date: Mapped[d] = mapped_column(Date, nullable=False)
    food_name: Mapped[str] = mapped_column(String, nullable=False)
    quantity_g: Mapped[float] = mapped_column(Float, default=100)
    calories: Mapped[float] = mapped_column(Float, nullable=False)
    carbohydrate: Mapped[float] = mapped_column(Float, nullable=False)
    protein: Mapped[float] = mapped_column(Float, nullable=False)
    fat: Mapped[float] = mapped_column(Float, nullable=False)
    logged_at: Mapped[datetime] = mapped_column(
            TIMESTAMP,
            server_default=func.now()
        )
    user: Mapped[User] = relationship(back_populates="food_logs")


class Exercise(Base):
    __tablename__ = "exercise_logs"
    

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    date: Mapped[d] = mapped_column(Date, nullable=False)
    exercise_name: Mapped[str] = mapped_column(String, nullable=False)
    duration_min: Mapped[float] = mapped_column(Float, nullable=False)
    MET: Mapped[float] = mapped_column(Float, nullable=False)  
    calories_burned: Mapped[float] = mapped_column(Float, nullable=False)
    logged_at: Mapped[datetime] = mapped_column(
            TIMESTAMP,
            server_default=func.now()
        )
    user: Mapped[User] = relationship(back_populates="exercise_logs")


class Sleep(Base):
    __tablename__ = "sleep_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    date: Mapped[d] = mapped_column(Date, nullable=False)
    quality: Mapped[str] = mapped_column(String, default="good")
    hours: Mapped[float] = mapped_column(Float, nullable=False)
    logged_at: Mapped[datetime] = mapped_column(
            TIMESTAMP,
            server_default=func.now()
        )
    user: Mapped[User] = relationship(back_populates="sleep_logs")


class Weight(Base):
    __tablename__ = "weight_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    date: Mapped[d] = mapped_column(Date, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    logged_at: Mapped[datetime] = mapped_column(
            TIMESTAMP,
            server_default=func.now()
        )
    user: Mapped[User] = relationship(back_populates="weight_logs")


class Custom_Food(Base):
    __tablename__ = "custom_foods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    food_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    calories: Mapped[float] = mapped_column(Float, nullable=False)
    protein: Mapped[float] = mapped_column(Float, nullable=False)
    carbohydrate: Mapped[float] = mapped_column(Float, nullable=False)
    fat: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
            TIMESTAMP,
            server_default=func.now()
        )
    user: Mapped[User] = relationship(back_populates="custom_foods")


class Stored_Food(Base):
    __tablename__ = "stored_food"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )
    food_name: Mapped[str] = mapped_column(String, nullable=False)
    calories: Mapped[float] = mapped_column(Float, nullable=False)
    carbohydrate: Mapped[float] = mapped_column(Float, nullable=False)
    protein: Mapped[float] = mapped_column(Float, nullable=False)
    fat: Mapped[float] = mapped_column(Float, nullable=False)


class Stored_Exercise(Base):
    __tablename__ = "stored_exercise"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )
    exercise_name: Mapped[str] = mapped_column(String, nullable=False)
    MET: Mapped[float] = mapped_column(Float, nullable=False)  
