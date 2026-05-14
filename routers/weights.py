from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import WeightCreate, WeightResponse

from auth import CurrentUser

router = APIRouter()

# add weight
@router.post("/weight_logs", response_model=WeightResponse, status_code=status.HTTP_201_CREATED)
async def add_weight(current_user: CurrentUser, weight: WeightCreate, db: Annotated[AsyncSession, Depends(get_db)]):

    new_weight = models.Weight(
        weight_kg = weight.weight_kg,
        date = weight.date,
        user_id = current_user.id
    )

    db.add(new_weight)
    await db.commit()
    await db.refresh(new_weight)

    return new_weight

# Show added weights of a user
@router.get("/weight_logs", response_model=list[WeightResponse])
async def get_weights_user(current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):

    results = await db.execute(select(models.Weight).where(models.Weight.user_id == current_user.id))
    weights = results.scalars().all()

    if weights:
        return weights
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, 
        detail="User has no weight logged yet."
        )


# Delete weight log of the user
@router.delete("/weight_logs/{weight_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_weight(current_user: CurrentUser, weight_id: int, db: Annotated[AsyncSession, Depends(get_db)]):

    results = await db.execute(
        select(models.Weight)
        .where(models.Weight.id == weight_id)
        )
    weight = results.scalars().first()

    if not weight:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="weight log with given entry not found")

    if weight.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this weight log."
        )

    await db.delete(weight)
    await db.commit()