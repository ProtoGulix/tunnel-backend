from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from uuid import UUID


class TemplateFieldEnum(BaseModel):
    """Valeur d'énumération pour un champ template"""
    value: str = Field(..., description="Valeur de l'enum")
    label: str = Field(..., description="Libellé affiché")

    class Config:
        from_attributes = True


class TemplateField(BaseModel):
    """Champ d'un template de pièce"""
    key: str = Field(..., max_length=50, description="Clé du champ (ex: DIAM)")
    label: str = Field(..., max_length=100, description="Libellé du champ")
    field_type: Literal["text", "number",
                        "enum"] = Field(..., description="Type de champ")
    unit: Optional[str] = Field(
        default=None, max_length=20, description="Unité (si applicable)")
    required: bool = Field(default=False, description="Champ obligatoire")
    enum_values: Optional[List[TemplateFieldEnum]] = Field(
        default=None, description="Valeurs possibles si type enum")

    class Config:
        from_attributes = True


class PartTemplate(BaseModel):
    """Template de pièce avec ses champs"""
    id: UUID
    code: str = Field(..., max_length=50, description="Code du template")
    version: int = Field(..., ge=1, description="Version du template")
    pattern: str = Field(..., max_length=255,
                         description="Pattern de génération de dimension (ex: {DIAM}x{LONG})")
    fields: List[TemplateField] = Field(
        default_factory=list, description="Champs du template")

    class Config:
        from_attributes = True


class StockSubFamily(BaseModel):
    """Sous-famille de stock avec template associé"""
    family_code: str = Field(..., max_length=20)
    code: str = Field(..., max_length=20)
    label: str = Field(..., max_length=100)
    template: Optional[PartTemplate] = Field(
        default=None, description="Template associé si existant")

    class Config:
        from_attributes = True


class CharacteristicValue(BaseModel):
    """Valeur d'une caractéristique pour un stock_item"""
    key: str = Field(..., max_length=50,
                     description="Clé du champ (doit correspondre au template)")
    text_value: Optional[str] = Field(default=None, description="Valeur texte")
    number_value: Optional[float] = Field(
        default=None, description="Valeur numérique")
    enum_value: Optional[str] = Field(
        default=None, description="Valeur énumération")

    @field_validator('text_value', 'number_value', 'enum_value')
    @classmethod
    def validate_single_value(cls, v):
        """Vérifie qu'un seul type de valeur est renseigné (validation de base)"""
        # Cette validation sera complétée par le service qui connaît le type attendu
        return v

    class Config:
        from_attributes = True


class StockItemWithCharacteristics(BaseModel):
    """Stock item avec ses caractéristiques"""
    id: UUID
    name: str
    family_code: str
    sub_family_code: str
    spec: Optional[str] = None
    dimension: str
    ref: Optional[str] = None
    quantity: Optional[int] = 0
    unit: Optional[str] = None
    location: Optional[str] = None
    template_id: Optional[UUID] = Field(
        default=None, description="ID du template (null = legacy)")
    template_version: Optional[int] = Field(
        default=None, description="Version du template utilisée")
    characteristics: List[CharacteristicValue] = Field(
        default_factory=list, description="Caractéristiques de la pièce")

    class Config:
        from_attributes = True
