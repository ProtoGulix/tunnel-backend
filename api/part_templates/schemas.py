from pydantic import BaseModel, validator
from typing import Optional, List, Literal


class TemplateFieldEnumIn(BaseModel):
    """Schéma d'entrée pour créer une valeur enum"""
    value: str
    label: str


class TemplateFieldIn(BaseModel):
    """Schéma d'entrée pour créer un champ template"""
    key: str
    label: str
    field_type: Literal["text", "number", "enum"]
    required: bool
    unit: str = None
    order: int = 0
    enum_values: List[TemplateFieldEnumIn] = None

    @validator('enum_values')
    def validate_enum_values(cls, v, values):
        """Vérifie que enum_values est fourni si field_type='enum'"""
        field_type = values.get('field_type')
        if field_type == 'enum' and not v:
            raise ValueError(
                "enum_values est obligatoire pour un champ de type enum")
        if field_type != 'enum' and v:
            raise ValueError(
                "enum_values ne peut être fourni que pour un champ de type enum")
        return v


class PartTemplateIn(BaseModel):
    """Schéma d'entrée pour créer un template"""
    code: str
    pattern: str
    fields: List[TemplateFieldIn]
    label: str = None
    active: bool = True

    @validator('pattern')
    def validate_pattern(cls, v):
        """Vérifie que le pattern contient au moins un placeholder"""
        if '{' not in v or '}' not in v:
            raise ValueError(
                "Le pattern doit contenir au moins un placeholder {KEY}")
        return v


class PartTemplateUpdate(BaseModel):
    """Schéma d'entrée pour créer une nouvelle version d'un template"""
    pattern: str = None
    fields: List[TemplateFieldIn] = None

    @validator('pattern')
    def validate_pattern(cls, v):
        """Vérifie que le pattern contient au moins un placeholder"""
        if v and ('{' not in v or '}' not in v):
            raise ValueError(
                "Le pattern doit contenir au moins un placeholder {KEY}")
        return v
