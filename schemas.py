from datetime import datetime
from datetime import date as d
from pydantic import BaseModel, ConfigDict, Field

class UserBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    age: int = Field(gt=1, lt=120)
    gender: str = Field(min_length=1, max_length=50)
    weight_kg: float = Field(gt=5, lt=150)
    height_cm: float = Field(gt=30, lt=280)
    goal: str = Field(min_length=1, max_length=50)

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int

# Food Schemas
class FoodBase(BaseModel):
    food_name: str = Field(min_length=1, max_length=50)
    quantity_g: float
    date: d
    

class FoodCreate(FoodBase):
    pass

class FoodResponse(FoodBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    calories: float
    carbohydrate: float
    protein: float
    fat: float

class FoodUpdate(BaseModel):
    food_name: str | None = Field(default=None, min_length=1, max_length=50)
    quantity_g: float | None = Field(default=None)


# Exercise Schemas
class ExerciseBase(BaseModel):
    exercise_name: str = Field(min_length=1, max_length=50)
    duration_min: float
    date: d
    

class ExerciseCreate(ExerciseBase):
    pass

class ExerciseResponse(ExerciseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    MET: float
    calories_burned: float

class ExerciseUpdate(BaseModel):
    exercise_name: str | None = Field(default=None, min_length=1, max_length=50)
    duration_min: float | None = Field(default=None)


# Sleep Shcemas

class SleepBase(BaseModel):
    quality: str = Field(min_length=1, max_length=50)
    hours: float
    date: d
    

class SleepCreate(SleepBase):
    pass

class SleepResponse(SleepBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int



# Weight Schemas
class WeightBase(BaseModel):
    weight_kg: float = Field(gt=5, lt=200)
    date: d
    

class WeightCreate(WeightBase):
    pass

class WeightResponse(WeightBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int


class WeightUpdate(BaseModel):
    weight_kg: float | None = Field(default=None, gt=5, lt=200)



# Custom Food Schemas

class CustomFoodBase(BaseModel):
    food_name: str = Field(min_length=1, max_length=50)
    calories: float = Field(gt=0)
    carbohydrate: float = Field(ge=0)
    protein: float = Field(ge=0)
    fat: float = Field(ge=0)
    

class CustomFoodCreate(CustomFoodBase):
    pass

class CustomFoodResponse(CustomFoodBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int

# This needs to be updated later
class CustomFoodUpdate(BaseModel):
    food_name: str | None = Field(default=None, min_length=1, max_length=50)
    quantity_g: float | None = Field(default=None)
