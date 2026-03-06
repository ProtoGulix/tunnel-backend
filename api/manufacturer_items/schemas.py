from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


class ManufacturerItemIn(BaseModel):
    """Schéma d'entrée pour créer/modifier une référence fabricant"""
    manufacturer_name: str = Field(...,
                                   description="Nom du fabricant/constructeur")
    manufacturer_ref: Optional[str] = Field(
        default=None, description="Référence catalogue fabricant")

    class Config:
        from_attributes = True


class ManufacturerItemOut(BaseModel):
    """Schéma de sortie pour une référence fabricant"""
    id: UUID
    manufacturer_name: str
    manufacturer_ref: Optional[str] = Field(default=None)

    class Config:
        from_attributes = True
