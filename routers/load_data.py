from typing import Annotated
import pandas as pd

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db

router = APIRouter()

@router.post("/load-exercises")
async def load_exercises_from_csv(
    db: Annotated[AsyncSession, Depends(get_db)],
    csv_file: str = "./data/met_exercises.csv"
):

    # Read CSV
    df = pd.read_csv(csv_file)

    exercises = []

    for _, row in df.iterrows():

        exercise = models.Stored_Exercise(
            exercise_name=row["Exercise"],
            MET=row["MET"]
        )

        exercises.append(exercise)

    # Add all foods
    db.add_all(exercises)

    # Commit changes
    await db.commit()

    return {
        "message": "Exercises inserted successfully",
        "foods_inserted": len(exercises)
    }

@router.post("/load-foods")
async def load_foods_from_csv(
    db: Annotated[AsyncSession, Depends(get_db)],
    csv_file: str = "./data/food_nutrition.csv"
):

    # Read CSV
    df = pd.read_csv(csv_file)


    foods = []

    for _, row in df.iterrows():

        food = models.Stored_Food(
            food_name=row["food_name"],
            calories=float(row["calories"]),
            carbohydrate=float(row["carbohydrates"]),
            protein=float(row["protein"]),
            fat=float(row["fat"]),
        )

        foods.append(food)

    # Add all foods
    db.add_all(foods)

    # Commit changes
    await db.commit()

    return {
        "message": "Foods inserted successfully",
        "foods_inserted": len(foods)
    }