from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import CustomFoodCreate, CustomFoodResponse

from auth import CurrentUser

router = APIRouter()

# add food
@router.post("", response_model=CustomFoodResponse, status_code=status.HTTP_201_CREATED)
async def add_custom_food(current_user: CurrentUser, food: CustomFoodCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    results = await db.execute(
        select(models.Stored_Food)
        .where(func.lower(models.Stored_Food.food_name) == food.food_name.lower())
    )

    stored_food = results.scalars().first()

    if stored_food:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, 
                            detail="Food with same name is alreday registered in standard foods.")


    results = await db.execute(
        select(models.Custom_Food)
        .where(func.lower(models.Custom_Food.food_name) == food.food_name.lower())
    )

    custom_stored_food = results.scalars().first()

    if custom_stored_food:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, 
                            detail="Food with same name is alreday registered in custom foods.")


    
    new_food = models.Custom_Food(
        food_name = food.food_name,
        user_id = current_user.id,
        calories = food.calories,
        carbohydrate = food.carbohydrate,
        fat = food.fat,
        protein = food.protein
    )

    db.add(new_food)
    await db.commit()
    await db.refresh(new_food)

    return new_food