from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import FoodCreate, FoodResponse, FoodUpdate

router = APIRouter()

# add food
@router.post("/food_logs", response_model=FoodResponse, status_code=status.HTTP_201_CREATED)
async def add_food(user_id: int, food: FoodCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    results = await db.execute(
        select(models.Stored_Food)
        .where(models.Stored_Food.food_name == food.food_name.strip().lower())
    )

    stored_food = results.scalars().first()

    if not stored_food:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="No food with given detail is found")


    
    new_food = models.Food(
        food_name = food.food_name,
        user_id = user_id,
        quantity_g = food.quantity_g,
        calories = stored_food.calories * food.quantity_g,
        carbohydrate = stored_food.carbohydrate * food.quantity_g,
        fat = stored_food.fat * food.quantity_g,
        protein = stored_food.protein * food.quantity_g
    )

    db.add(new_food)
    await db.commit()
    await db.refresh(new_food)

    return new_food

# Show added foods of a user
@router.get("/food_logs", response_model=list[FoodResponse])
async def get_foods_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    results = await db.execute(select(models.User).where(models.User.id == user_id))
    user = results.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User doesn't Exist")
    
    results = await db.execute(select(models.Food).where(models.Food.user_id == user_id))
    foods = results.scalars().all()

    if foods:
        return foods
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, 
        detail="User has no food logged yet."
        )


# Delete Food of the user
@router.delete("/food_logs/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_food(user_id: int, food_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    # we check if the user exists
    results = await db.execute(select(models.User).where(models.User.id == user_id))
    user = results.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User doesn't exist.")
    
    # After a valid user, we check for food log in the food log
    # Here in future we need to check for the food of the current user only.
    results = await db.execute(select(models.Food).where(models.Food.id == food_id))
    food = results.scalars().first()

    if not food:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food log with given entry not found")

    await db.delete(food)
    await db.commit()

