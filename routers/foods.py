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

    results = await db.execute(
        select(models.Custom_Food)
        .where(models.Custom_Food.food_name == food.food_name.strip().lower())
    )

    custom_stored_food = results.scalars().first()

    selected_food = stored_food or custom_stored_food

    if not selected_food:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="No food with given detail is found")

    
    new_food = models.Food(
        food_name = food.food_name,
        date = food.date,
        user_id = user_id,
        quantity_g = food.quantity_g,
        calories = (selected_food.calories * food.quantity_g) / 100,
        carbohydrate = (selected_food.carbohydrate * food.quantity_g) / 100,
        fat = (selected_food.fat * food.quantity_g) / 100,
        protein = (selected_food.protein * food.quantity_g) / 100
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


@router.get("/foods/search")
async def search_food(q: str, db: Annotated[AsyncSession, Depends(get_db)]):
    results = await db.execute(
        select(models.Stored_Food)
        .where(models.Stored_Food.food_name.ilike(f"%{q}%"))
        .limit(10)
    )

    foods = results.scalars().all()

    results = await db.execute(
        select(models.Custom_Food)
        .where(models.Custom_Food.food_name.ilike(f"%{q}%"))
        .limit(10)
    )

    custom_foods = results.scalars().all()

    list_foods = [{"id": food.id, "food_name": food.food_name} for food in foods]
    list_custom_foods = [{"id": food.id, "food_name": food.food_name} for food in custom_foods]

    list_foods.extend(list_custom_foods)

    return list_foods
