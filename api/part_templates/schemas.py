from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Literal


class TemplateFieldEnumIn(BaseModel):
    """Schéma d'entrée pour créer une valeur enum"""
    value: str = Field(..., max_length=50, description="Valeur de l'enum")
    label: str = Field(..., max_length=100, description="Libellé affiché")


class TemplateFieldIn(BaseModel):
    """Schéma d'entrée pour créer un champ template"""
    field_key: str = Field(..., max_length=50, validation_alias="key",
                           description="Clé du champ (ex: DIAM)")
    label: str = Field(..., max_length=100, description="Libellé du champ")
    type: Literal["text", "number", "enum"] = Field(..., validation_alias="field_type",
                                                    description="Type de champ")
    unit: Optional[str] = Field(
        default=None, max_length=20, description="Unité (si applicable)")
    required: bool = Field(default=False, description="Champ obligatoire")
    order: Optional[int] = Field(default=0, description="Ordre d'affichage")
    enum_values: Optional[List[TemplateFieldEnumIn]] = Field(
        default=None,
        description="Valeurs possibles si type enum (obligatoire si type='enum')"
    )

    # Accepte aussi field_key et type
    model_config = ConfigDict(populate_by_name=True)

    @field_validator('enum_values')
    @classmethod
    def validate_enum_values(cls, v, info):
        """Vérifie que enum_values est fourni si type='enum'"""
        data = info.data
        if data.get('type') == 'enum' and not v:
            raise ValueError(
                "enum_values est obligatoire pour un champ de type enum")
        if data.get('type') != 'enum' and v:
            raise ValueError(
                "enum_values ne peut être fourni que pour un champ de type enum")
        return v


class PartTemplateIn(BaseModel):
    """Schéma d'entrée pour créer un template"""
    code: str = Field(..., max_length=50, description="Code du template")
    label: Optional[str] = Field(
        default=None, max_length=100, description="Libellé du template")
    pattern: str = Field(..., max_length=255,
                         description="Pattern (ex: {DIAM}x{LONG}-{MAT})")
    active: Optional[bool] = Field(default=True, description="Template actif")
    fields: List[TemplateFieldIn] = Field(...,
                                          min_length=1, description="Champs du template")

    @field_validator('pattern')
    @classmethod
    def validate_pattern(cls, v):
        """Vérifie que le pattern contient au moins un placeholder"""
        if '{' not in v or '}' not in v:
            raise ValueError(
                "Le pattern doit contenir au moins un placeholder {KEY}")
        return v


class PartTemplateUpdate(BaseModel):
    """Schéma d'entrée pour créer une nouvelle version d'un template"""
    pattern: Optional[str] = Field(
        default=None, max_length=255, description="Pattern modifié")
    fields: Optional[List[TemplateFieldIn]] = Field(
        default=None, description="Champs modifiés")

    @field_validator('pattern')
    @classmethod
    def validate_pattern(cls, v):
        """Vérifie que le pattern contient au moins un placeholder"""
        if v and ('{' not in v or '}' not in v):
            raise ValueError(
                "Le pattern doit contenir au moins un placeholder {KEY}")
        return v
