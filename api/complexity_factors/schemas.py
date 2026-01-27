from pydantic import BaseModel
from typing import Optional


class ComplexityFactorOut(BaseModel):
    """Schéma de sortie pour un facteur de complexité"""
    code: str
    label: Optional[str] = None
    category: Optional[str] = None

    class Config:
        from_attributes = True
