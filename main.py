from typing import Annotated
from contextlib import asynccontextmanager
import pandas as pd
# Fastapi
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException

# Sqlalchemy
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


import models
from database import Base, engine, get_db

# Routers
from routers import (foods, 
                     users, 
                     load_data, 
                     exercises,
                     sleeps,
                     weights,
                     custom_food
                     )

# Creating Database Tables
# For async we need to use life span function
# Life span is a modern way in fastapi to handle startup and shutdown operations.
# It replaces the older deprecated onstartup and onshutdown decorators
# Code below is just a asynchronous way of creating tables if they don't exist
@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield # Here, our application actually runs
    # Shutdown
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")

app.include_router(users.router, prefix="/api/users", tags=["User APIs"])
app.include_router(foods.router, prefix="/api/users/{user_id}", tags=["Food APIs"])
app.include_router(exercises.router, prefix="/api/users/{user_id}", tags=["Exercise APIs"])
app.include_router(sleeps.router, prefix="/api/users/{user_id}", tags=["Sleep APIs"])
app.include_router(weights.router, prefix="/api/users/{user_id}", tags=["Weight APIs"])
app.include_router(custom_food.router, prefix="/api/users/{user_id}", tags=["Custom Food APIs"])
app.include_router(load_data.router, prefix="/api/data", tags=["Load Data APIs"])



# ------Template Routes--------

# Food Page
@app.get("/", include_in_schema=False)
def home(request: Request):
    return templates.TemplateResponse(
        request,
        "home.html",
        {

        }
    )

# Dashboard Page
@app.get("/dashboard", include_in_schema=False)
def dashboard(request: Request):
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {

        }
    )


# Profile Page
@app.get("/profile/{user_id}", include_in_schema=False)
async def user_profile(request: Request, user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User doesn't exist")
    

    return templates.TemplateResponse(
        request,
        "profile.html",
        {
            "user": user
        }
    )


# Exercise Page
@app.get("/users/{user_id}/exercise_logs", include_in_schema=False)
async def exercise(request: Request, user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    results = await db.execute(
        select(models.User)
        .where(models.User.id == user_id)
    )
    user = results.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="User doesn't exist.")
    
    results = await db.execute(select(models.Exercise).where(models.Exercise.user_id == user_id))
    exercises = results.scalars().all()

    return templates.TemplateResponse(
        request,
        "exercise.html",
        {
            "exercises": exercises
        }
    )


# Sleep Page
@app.get("/users/{user_id}/sleep_logs", include_in_schema=False)
async def sleep(request: Request, user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    results = await db.execute(
        select(models.User)
        .where(models.User.id == user_id)
    )
    user = results.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="User doesn't exist.")
    
    results = await db.execute(select(models.Sleep).where(models.Sleep.user_id == user_id))
    sleeps = results.scalars().all()

    return templates.TemplateResponse(
        request,
        "sleep.html",
        {
            "sleeps": sleeps
        }
    )

# Food Page
@app.get("/users/{user_id}/food_logs", include_in_schema=False)
async def food_templates(request: Request, user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    results = await db.execute(
        select(models.User)
        .where(models.User.id == user_id)
    )
    user = results.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="User doesn't exist.")
    
    results = await db.execute(select(models.Food).where(models.Food.user_id == user_id))
    foods = results.scalars().all()

    return templates.TemplateResponse(
        request,
        "food.html",
        {
            "foods": foods
        }
    )

# Analytics Page
@app.get("/analytics", include_in_schema=False)
def analytics(request: Request):
    return templates.TemplateResponse(
        request,
        "analytics.html",
        {

        }
    )           

# Weight Page
@app.get("/users/{user_id}/weight_logs", include_in_schema=False)
async def weight(request: Request, user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    results = await db.execute(
        select(models.User)
        .where(models.User.id == user_id)
    )
    user = results.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="User doesn't exist.")
    
    results = await db.execute(select(models.Weight).where(models.Weight.user_id == user_id))
    weights = results.scalars().all()


    return templates.TemplateResponse(
        request,
        "weight.html",
        {
            "weights": weights
        }
    )

# About Page
@app.get("/about", include_in_schema=False)
def about(request: Request):
    return templates.TemplateResponse(
        request,
        "about.html",
        {

        }
    )



@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    
    if request.url.path.startswith("/api"):
        return await http_exception_handler(request, exception)
    
    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return await request_validation_exception_handler(request, exception)
    
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )