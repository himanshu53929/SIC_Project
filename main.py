from typing import Annotated
from datetime import date
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
from auth import CookieUser

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
app.include_router(foods.router, prefix="/api/foods", tags=["Food APIs"])
app.include_router(exercises.router, prefix="/api/exercises", tags=["Exercise APIs"])
app.include_router(sleeps.router, prefix="/api/sleeps", tags=["Sleep APIs"])
app.include_router(weights.router, prefix="/api/weights", tags=["Weight APIs"])
app.include_router(custom_food.router, prefix="/api/custom_foods", tags=["Custom Food APIs"])
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
@app.get("/profile", include_in_schema=False)
async def user_profile(request: Request, cookie_user: CookieUser, db: Annotated[AsyncSession, Depends(get_db)]):

    return templates.TemplateResponse(
        request,
        "profile.html",
        {
            "user": cookie_user
        }
    )


# Exercise Page
@app.get("/exercises/exercise_logs", include_in_schema=False)
async def exercise(request: Request, cookie_user: CookieUser, db: Annotated[AsyncSession, Depends(get_db)]):

    results = await db.execute(
        select(models.Exercise)
        .where(
            models.Exercise.user_id == cookie_user.id
            ,models.Exercise.date == date.today()
        )
    )
    exercises = results.scalars().all()

    return templates.TemplateResponse(
        request,
        "exercise.html",
        {
            "exercises": exercises
        }
    )


# Sleep Page
@app.get("/sleeps/sleep_logs", include_in_schema=False)
async def sleep(request: Request, cookie_user: CookieUser, db: Annotated[AsyncSession, Depends(get_db)]):
    
    results = await db.execute(
        select(models.Sleep)
        .where(
            models.Sleep.user_id == cookie_user.id,
            models.Sleep.date == date.today()
            ))
    sleeps = results.scalars().all()

    return templates.TemplateResponse(
        request,
        "sleep.html",
        {
            "sleeps": sleeps
        }
    )

# Food Page
@app.get("/foods/food_logs", include_in_schema=False)
async def food_templates(request: Request, cookie_user: CookieUser, db: Annotated[AsyncSession, Depends(get_db)]):

    
    results = await db.execute(
        select(models.Food)
        .where(
            models.Food.user_id == cookie_user.id,
            models.Food.date == date.today()
            )
        )
    foods = results.scalars().all()

    return templates.TemplateResponse(
        request,
        "food.html",
        {
            "foods": foods
        }
    )


# Weight Page
@app.get("/weights/weight_logs", include_in_schema=False)
async def weight(request: Request, cookie_user: CookieUser, db: Annotated[AsyncSession, Depends(get_db)]):
    
    results = await db.execute(
        select(models.Weight)
        .where(
            models.Weight.user_id == cookie_user.id
            )
        )
    weights = results.scalars().all()


    return templates.TemplateResponse(
        request,
        "weight.html",
        {
            "weights": weights
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




@app.get("/login", include_in_schema=False)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        {"title": "Login"}
    )


@app.get("/register", include_in_schema=False)
async def register_page(request: Request):
    return templates.TemplateResponse(
        request,
        "register.html",
        {"title": "Register"}
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