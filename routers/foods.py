from typing import Annotated

import httpx

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import FoodCreate, FoodResponse, FoodUpdate

from config import settings
from auth import CurrentUser

router = APIRouter()


def _extract_usda_nutrients(usda: dict) -> dict[str, float]:
    calories_100 = 0.0
    protein_100 = 0.0
    fat_100 = 0.0
    carb_100 = 0.0

    for n in usda.get("foodNutrients", []):
        nutrient_number = None
        name = None
        value = None

        if isinstance(n, dict):
            nutrient = n.get("nutrient") or {}
            nutrient_number = nutrient.get("number") or n.get("nutrientNumber") or n.get("nutrientId")
            name = (nutrient.get("name") or n.get("nutrientName") or "").lower()
            value = n.get("amount") or n.get("value")

        if value is None:
            continue

        try:
            value = float(value)
        except (TypeError, ValueError):
            continue

        if str(nutrient_number) in ("1008", "208") or "energy" in (name or "") or "kcal" in (name or ""):
            calories_100 = value
        elif str(nutrient_number) == "1003" or "protein" in (name or ""):
            protein_100 = value
        elif str(nutrient_number) == "1004" or "total lipid" in (name or "") or name == "fat":
            fat_100 = value
        elif str(nutrient_number) == "1005" or "carbohydrate" in (name or ""):
            carb_100 = value

    return {
        "calories": calories_100,
        "protein": protein_100,
        "fat": fat_100,
        "carbohydrate": carb_100,
    }


async def _fetch_usda_food_by_id(fdc_id: int) -> dict:
    if settings.usda_api_key is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="USDA API key not configured on server")

    async with httpx.AsyncClient(timeout=10.0) as client:
        url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}"
        params = {"api_key": settings.usda_api_key.get_secret_value()}
        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Failed to fetch USDA food data")
        return resp.json()


async def _search_usda_foods(query: str) -> list[dict]:
    if settings.usda_api_key is None:
        return []

    async with httpx.AsyncClient(timeout=10.0) as client:
        url = "https://api.nal.usda.gov/fdc/v1/foods/search"
        params = {"api_key": settings.usda_api_key.get_secret_value()}
        json_body = {"query": query, "pageSize": 10}
        resp = await client.post(url, params=params, json=json_body)
        if resp.status_code != 200:
            return []

        data = resp.json()
        return data.get("foods", [])


async def _resolve_usda_food(query: str | None = None, fdc_id: int | None = None) -> dict | None:
    if fdc_id is not None:
        usda = await _fetch_usda_food_by_id(fdc_id)
        nutrients = _extract_usda_nutrients(usda)
        return {"fdc_id": fdc_id, "name": usda.get("description") or query or "USDA food", **nutrients}

    if not query:
        return None

    foods = await _search_usda_foods(query)
    if not foods:
        return None

    normalized_query = query.strip().lower()
    chosen = None

    for item in foods:
        description = (item.get("description") or "").strip().lower()
        if description == normalized_query:
            chosen = item
            break

    if chosen is None:
        chosen = foods[0]

    chosen_fdc_id = chosen.get("fdcId")
    if chosen_fdc_id is None:
        return None

    usda = await _fetch_usda_food_by_id(int(chosen_fdc_id))
    nutrients = _extract_usda_nutrients(usda)
    return {
        "fdc_id": int(chosen_fdc_id),
        "name": usda.get("description") or chosen.get("description") or query,
        **nutrients,
    }

# add food
@router.post("/food_logs", response_model=FoodResponse, status_code=status.HTTP_201_CREATED)
async def add_food(
    current_user: CurrentUser, 
    food: FoodCreate, 
    db: Annotated[AsyncSession, Depends(get_db)]
    ):
    results = await db.execute(
        select(models.Stored_Food)
        .where(func.lower(models.Stored_Food.food_name) == food.food_name.lower())
    )

    stored_food = results.scalars().first()

    results = await db.execute(
        select(models.Custom_Food)
        .where(
            func.lower(models.Custom_Food.food_name) == food.food_name.lower(),
            models.Custom_Food.user_id == current_user.id
            )
    )

    custom_stored_food = results.scalars().first()

    selected_food = stored_food or custom_stored_food

    # Allow client to send food_name as "usda:<fdcId>" (from search id); extract fdc_id
    if not selected_food and food.fdc_id is None and isinstance(food.food_name, str) and food.food_name.startswith("usda:"):
        try:
            food.fdc_id = int(food.food_name.split("usda:", 1)[1])
        except (ValueError, IndexError):
            pass

    # If not found locally, try USDA by FDC id or by food name
    if not selected_food:
        usda_food = await _resolve_usda_food(query=food.food_name, fdc_id=food.fdc_id)
        if usda_food is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No food with given detail is found")

        selected_food = type("USDA", (), {
            "calories": usda_food["calories"],
            "carbohydrate": usda_food["carbohydrate"],
            "fat": usda_food["fat"],
            "protein": usda_food["protein"],
        })

        food.food_name = usda_food["name"]

    
    new_food = models.Food(
        food_name = food.food_name,
        date = food.date,
        user_id = current_user.id,
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
async def get_foods_user(current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    results = await db.execute(select(models.Food).where(models.Food.user_id == current_user.id))
    foods = results.scalars().all()

    if foods:
        return foods
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, 
        detail="User has no food logged yet."
        )


# Delete Food of the user
@router.delete("/food_logs/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_food(current_user: CurrentUser, food_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    results = await db.execute(select(models.Food).where(models.Food.id == food_id))
    food = results.scalars().first()

    if not food:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food log with given entry not found")

    if food.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this food log."
        )

    await db.delete(food)
    await db.commit()


@router.get("/search")
async def search_food(q: str, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    results = await db.execute(
        select(models.Stored_Food)
        .where(models.Stored_Food.food_name.ilike(f"%{q}%"))
        .limit(10)
    )

    foods = results.scalars().all()

    results = await db.execute(
        select(models.Custom_Food)
        .where(
            and_(models.Custom_Food.food_name.ilike(f"%{q}%"),
            models.Custom_Food.user_id == current_user.id)
            )
        .limit(10)
    )

    custom_foods = results.scalars().all()

    list_foods = [{"id": food.id, "food_name": food.food_name} for food in foods]
    list_custom_foods = [{"id": food.id, "food_name": food.food_name} for food in custom_foods]

    list_foods.extend(list_custom_foods)

    # Append USDA search results if available
    if settings.usda_api_key is not None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = "https://api.nal.usda.gov/fdc/v1/foods/search"
            params = {"api_key": settings.usda_api_key.get_secret_value()}
            json_body = {"query": q, "pageSize": 10}
            try:
                resp = await client.post(url, params=params, json=json_body)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("foods", []):
                        list_foods.append({
                            "id": f"usda:{item.get('fdcId')}",
                            "food_name": item.get("description"),
                            "fdc_id": item.get("fdcId"),
                            "source": "usda"
                        })
            except httpx.HTTPError:
                # ignore external API failures for search
                pass

    return list_foods
