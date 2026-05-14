from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import SleepCreate, SleepResponse

router = APIRouter()

# add sleep
@router.post("/sleep_logs", response_model=SleepResponse, status_code=status.HTTP_201_CREATED)
async def add_sleep(user_id: int, sleep: SleepCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    results = await db.execute(
        select(models.User)
        .where(models.User.id == user_id)
    )

    user = results.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="User not found")   
    

    new_sleep = models.Sleep(
        hours = sleep.hours,
        quality = sleep.quality,
        date = sleep.date,
        user_id = user_id,

    )

    db.add(new_sleep)
    await db.commit()
    await db.refresh(new_sleep)

    return new_sleep

# Show added sleeps of a user
@router.get("/sleep_logs", response_model=list[SleepResponse])
async def get_sleeps_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    results = await db.execute(select(models.User).where(models.User.id == user_id))
    user = results.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User doesn't Exist")
    
    results = await db.execute(select(models.Sleep).where(models.Sleep.user_id == user_id))
    sleeps = results.scalars().all()

    if sleeps:
        return sleeps
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, 
        detail="User has no sleep logged yet."
        )


# Delete Sleep log of the user
@router.delete("/sleep_logs/{sleep_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sleep(user_id: int, sleep_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    # we check if the user exists
    results = await db.execute(select(models.User).where(models.User.id == user_id))
    user = results.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User doesn't exist.")
    
    # After a valid user, we check for sleep log in the sleep log
    # Here in future we need to check for the sleep of the current user only.
    results = await db.execute(select(models.Sleep).where(models.Sleep.id == sleep_id))
    sleep = results.scalars().first()

    if not sleep:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="sleep log with given entry not found")

    await db.delete(sleep)
    await db.commit()