from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import UserCreate, UserPublic, UserPrivate, Token, UserUpdate

from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm

from auth import (
    CurrentUser,
    create_access_token, 
    hash_password,
    verify_password
    )
from config import settings

router = APIRouter()


@router.post("", response_model=UserPrivate, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User)
        .where(func.lower(models.User.username) == user.username.lower())
        )

    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                             detail="User with same username already exists")
    
    result = await db.execute(select(models.User)
                              .where(func.lower(models.User.email) == user.email.lower()))

    existing_email = result.scalars().first()

    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                             detail="User with same email already exists")

    new_user = models.User(
        username = user.username,
        email = user.email.lower(),
        password_hash = hash_password(user.password),

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


@router.post("/token", response_model=Token)
async def login_for_access_token(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # Look up user by email (case-insensitive)
    # Note: OAuth2PasswordRequestForm uses "username" field, but we treat it as email
    result = await db.execute(
        select(models.User)
        .where(func.lower(models.User.email) == form_data.username.lower())
    )

    user = result.scalars().first()

    # Verify user exists and password is correct
    # Don't reveal which one failed (security best practice)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Create acces token with user id as subject
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60
    )

    return {"access_token": access_token, "token_type": "bearer"}


## get_current_user
@router.get("/me", response_model=UserPrivate)
async def get_current_user(current_user: CurrentUser):
    # Return explicit dict to avoid serialization edge-cases
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "age": getattr(current_user, "age", None),
        "gender": getattr(current_user, "gender", None),
        "weight_kg": getattr(current_user, "weight_kg", None),
        "height_cm": getattr(current_user, "height_cm", None),
        "goal": getattr(current_user, "goal", None),
    }


# View Users
@router.get("", response_model=list[UserPublic])
async def get_users(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User))
    users = result.scalars().all()

    if not users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Users Found")

    return users

# Update User
@router.patch("", response_model=UserPrivate)
async def update_user(
    update_user_data: UserUpdate, 
    current_user: CurrentUser, 
    db: Annotated[AsyncSession, Depends(get_db)]
    ):

    result = await db.execute(
        select(models.User)
        .where(models.User.id == current_user.id)
    )
    user = result.scalars().first()

    # this just means that the user has set some new username
    if (update_user_data.username is not None 
        and update_user_data.username.lower() != user.username.lower()): 
        result = await db.execute(
            select(models.User)
            .where(func.lower(models.User.username) == update_user_data.username.lower())
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with given username already exists."
            )
        
    if (update_user_data.email is not None
        and update_user_data.email.lower() != user.email):
        result = await db.execute(
            select(models.User)
            .where(models.User.email == update_user_data.email.lower())
        )
        existing_email = result.scalars().first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with given email already exists."
            )
        
    if update_user_data.username is not None:
        user.username = update_user_data.username
    if update_user_data.email is not None:
        user.email = update_user_data.email
    if update_user_data.age is not None:
        user.age = update_user_data.age
    if update_user_data.gender is not None:
        user.gender = update_user_data.gender
    if update_user_data.weight_kg is not None:
        user.weight_kg = update_user_data.weight_kg
    if update_user_data.height_cm is not None:
        user.height_cm = update_user_data.height_cm
    if update_user_data.goal is not None:
        user.goal = update_user_data.goal

    await db.commit()
    await db.refresh(user)

    return user



# Delete User
@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(models.User)
        .where(models.User.id == current_user.id)
    )
    user = result.scalars().first()

    await db.delete(user)
    await db.commit()   
        

    






# Logout
@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged Out"}





