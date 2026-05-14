from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import WeightCreate, WeightResponse

router = APIRouter()

# add weight
@router.post("/weight_logs", response_model=WeightResponse, status_code=status.HTTP_201_CREATED)
async def add_weight(user_id: int, weight: WeightCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    results = await db.execute(
        select(models.User)
        .where(models.User.id == user_id)
    )

    user = results.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="User not found")   
    

    new_weight = models.Weight(
        weight_kg = weight.weight_kg,
        date = weight.date,
        user_id = user_id
    )

    db.add(new_weight)
    await db.commit()
    await db.refresh(new_weight)

    return new_weight

# Show added weights of a user
@router.get("/weight_logs", response_model=list[WeightResponse])
async def get_weights_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    results = await db.execute(select(models.User).where(models.User.id == user_id))
    user = results.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User doesn't Exist")
    
    results = await db.execute(select(models.Weight).where(models.Weight.user_id == user_id))
    weights = results.scalars().all()

    if weights:
        return weights
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, 
        detail="User has no weight logged yet."
        )


# Delete weight log of the user
@router.delete("/weight_logs/{weight_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_weight(user_id: int, weight_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    # we check if the user exists
    results = await db.execute(select(models.User).where(models.User.id == user_id))
    user = results.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User doesn't exist.")
    
    # After a valid user, we check for weight log in the weight log
    # Here in future we need to check for the weight of the current user only.
    results = await db.execute(select(models.Weight).where(models.Weight.id == weight_id))
    weight = results.scalars().first()

    if not weight:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="weight log with given entry not found")

    await db.delete(weight)
    await db.commit()