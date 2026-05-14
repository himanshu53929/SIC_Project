from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import ExerciseCreate, ExerciseResponse, ExerciseUpdate

from auth import CurrentUser

router = APIRouter()

# add exercise
@router.post("/exercise_logs", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
async def add_exercise(current_user: CurrentUser, exercise: ExerciseCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    
    results = await db.execute(
        select(models.Stored_Exercise)
        .where(func.lower(models.Stored_Exercise.exercise_name) == exercise.exercise_name.lower())
    )

    stored_exercise = results.scalars().first()

    if not stored_exercise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="No exercise with given detail is found")


    
    new_exercise = models.Exercise(
        exercise_name = exercise.exercise_name,
        date = exercise.date,
        duration_min = exercise.duration_min,
        user_id = current_user.id,
        MET = stored_exercise.MET,
        calories_burned = (stored_exercise.MET * 3.5 * current_user.weight_kg * exercise.duration_min) / 200
    )

    db.add(new_exercise)
    await db.commit()
    await db.refresh(new_exercise)

    return new_exercise

# Show added exercises of a user
@router.get("/exercise_logs", response_model=list[ExerciseResponse])
async def get_exercises_user(current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):

    results = await db.execute(
        select(models.Exercise)
        .where(models.Exercise.user_id == current_user.id)
        )
    exercises = results.scalars().all()

    if exercises:
        return exercises
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, 
        detail="User has no exercise logged yet."
        )


# Delete Excersie log of the user
@router.delete("/exercise_logs/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exercise(current_user: CurrentUser, exercise_id: int, db: Annotated[AsyncSession, Depends(get_db)]):

    results = await db.execute(
        select(models.Exercise)
        .where(models.Exercise.id == exercise_id)
        )

    exercise = results.scalars().first()

    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="exercise log with given entry not found")

    if exercise.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this exercise log."
        )


    await db.delete(exercise)
    await db.commit()

# Search For exercises
@router.get("/search")
async def search_exercise(q: str, db: Annotated[AsyncSession, Depends(get_db)]):
    # Search for the exercise types in database and match the pattern with q or query
    results = await db.execute(
        select(models.Stored_Exercise)
        .where(models.Stored_Exercise.exercise_name.ilike(f"%{q}%"))
        .limit(10)
    )

    exercises = results.scalars().all()

    return [{"id": exercise.id, "exercise_name": exercise.exercise_name} for exercise in exercises]

