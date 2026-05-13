from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import ExerciseCreate, ExerciseResponse, ExerciseUpdate

router = APIRouter()

# add exercise
@router.post("/exercise_logs", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
async def add_exercise(user_id: int, exercise: ExerciseCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    results = await db.execute(
        select(models.User)
        .where(models.User.id == user_id)
    )

    user = results.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="User not found")   
    
    results = await db.execute(
        select(models.Stored_Exercise)
        .where(models.Stored_Exercise.exercise_name == exercise.exercise_name.strip().lower())
    )

    stored_exercise = results.scalars().first()

    if not stored_exercise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="No exercise with given detail is found")


    
    new_exercise = models.Exercise(
        exercise_name = exercise.exercise_name,
        duration_min = exercise.duration_min,
        user_id = user_id,
        MET = stored_exercise.MET,
        calories_burned = (stored_exercise.MET * 3.5 * user.weight_kg * exercise.duration_min) / 200
    )

    db.add(new_exercise)
    await db.commit()
    await db.refresh(new_exercise)

    return new_exercise

# Show added exercises of a user
@router.get("/exercise_logs", response_model=list[ExerciseResponse])
async def get_exercises_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    results = await db.execute(select(models.User).where(models.User.id == user_id))
    user = results.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User doesn't Exist")
    
    results = await db.execute(select(models.Exercise).where(models.Exercise.user_id == user_id))
    exercises = results.scalars().all()

    if exercises:
        return exercises
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, 
        detail="User has no exercise logged yet."
        )


# Delete Food of the user
@router.delete("/exercise_logs/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exercise(user_id: int, exercise_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    # we check if the user exists
    results = await db.execute(select(models.User).where(models.User.id == user_id))
    user = results.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User doesn't exist.")
    
    # After a valid user, we check for exercise log in the exercise log
    # Here in future we need to check for the exercise of the current user only.
    results = await db.execute(select(models.Exercise).where(models.Exercise.id == exercise_id))
    exercise = results.scalars().first()

    if not exercise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="exercise log with given entry not found")

    await db.delete(exercise)
    await db.commit()

# Search For exercises
@router.get("/exercises/search")
async def search_exercise(q: str, db: Annotated[AsyncSession, Depends(get_db)]):
    # Search for the exercise types in database and match the pattern with q or query
    results = await db.execute(
        select(models.Stored_Exercise)
        .where(models.Stored_Exercise.exercise_name.ilike(f"%{q}%"))
        .limit(10)
    )

    exercises = results.scalars().all()

    return [{"id": exercise.id, "exercise_name": exercise.exercise_name} for exercise in exercises]

