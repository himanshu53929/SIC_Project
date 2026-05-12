from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import UserResponse, UserCreate

router = APIRouter()


@router.post("/{user_id}/profile", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def profile(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    new_user = models.User(
        name = user.name,
        age = user.age,
        gender = user.gender,
        height_cm = user.height_cm,
        weight_kg = user.weight_kg,
        goal = user.goal
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user

# View Users
@router.get("", response_model=list[UserResponse])
async def get_users(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User))
    users = result.scalars().all()

    if not users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Users Found")

    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Users Found")

    return user
