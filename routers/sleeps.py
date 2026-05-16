from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import SleepCreate, SleepResponse

from auth import CurrentUser
from validation import date_validation

router = APIRouter()

# add sleep
@router.post("/sleep_logs", response_model=SleepResponse, status_code=status.HTTP_201_CREATED)
async def add_sleep(current_user: CurrentUser, sleep: SleepCreate, db: Annotated[AsyncSession, Depends(get_db)]):

    date_validation(sleep.date)

    new_sleep = models.Sleep(
        hours = sleep.hours,
        quality = sleep.quality,
        date = sleep.date,
        user_id = current_user.id,

    )

    db.add(new_sleep)
    await db.commit()
    await db.refresh(new_sleep)

    return new_sleep

# Show added sleeps of a user
@router.get("/sleep_logs", response_model=list[SleepResponse])
async def get_sleeps_user(current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):

    results = await db.execute(
        select(models.Sleep)
        .where(models.Sleep.user_id == current_user.id)
        .order_by(
            models.Sleep.date.desc(),
            models.Sleep.id.desc()
        )
        )
    
    sleeps = results.scalars().all()

    if sleeps:
        return sleeps
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, 
        detail="User has no sleep logged yet."
        )


# Delete Sleep log of the user
@router.delete("/sleep_logs/{sleep_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sleep(current_user: CurrentUser, sleep_id: int, db: Annotated[AsyncSession, Depends(get_db)]):

    results = await db.execute(
        select(models.Sleep)
        .where(models.Sleep.id == sleep_id)
        )
    
    sleep = results.scalars().first()

    if not sleep:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="sleep log with given entry not found")

    if sleep.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this sleep log."
        )

    await db.delete(sleep)
    await db.commit()