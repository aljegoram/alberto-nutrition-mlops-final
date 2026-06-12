from pydantic import BaseModel, Field
from typing import Optional


class NutritionInput(BaseModel):
    item_name: Optional[str] = Field(default="producto_sin_nombre")
    energy_kcal_100g: float = Field(..., ge=0, description="Energía en kcal por 100g")
    saturated_fat_100g: float = Field(..., ge=0, description="Grasas saturadas por 100g")
    sodium_100g: float = Field(..., ge=0, description="Sodio por 100g")
    sugars_100g: float = Field(..., ge=0, description="Azúcares por 100g")


class PredictionResponse(BaseModel):
    ambiente: str
    item_name: str
    recomendable: bool
    label: int
    probabilidad_recomendable: float
    interpretacion: str
    modelo: str
