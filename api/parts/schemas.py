from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class PartSupplierRefOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    part_manufacturer_ref_id: UUID
    supplier_id: UUID
    supplier_name: Optional[str] = None
    supplier_ref: str
    unit_price: Optional[float] = None
    min_order_quantity: int = 1
    delivery_time_days: Optional[int] = None
    is_preferred: bool = False
    product_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PartManufacturerRefOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    part_id: UUID
    manufacturer_name: str
    manufacturer_ref: str
    label: Optional[str] = None
    is_preferred: bool = False
    supplier_refs: List[PartSupplierRefOut] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PartListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    internal_ref: str
    family_code: str
    sub_family_code: str
    unit: Optional[str] = None
    location: Optional[str] = None
    qty_in_stock: int = 0
    preferred_manufacturer_name: Optional[str] = None
    preferred_manufacturer_ref: Optional[str] = None
    preferred_label: Optional[str] = None


class PartDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    internal_ref: str
    family_code: str
    sub_family_code: str
    unit: Optional[str] = None
    location: Optional[str] = None
    qty_in_stock: int = 0
    manufacturer_refs: List[PartManufacturerRefOut] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PartCreate(BaseModel):
    family_code: str = Field(..., description="Code famille")
    sub_family_code: str = Field(..., description="Code sous-famille")
    unit: Optional[str] = Field(default=None, description="Unité")
    location: Optional[str] = Field(default=None, description="Emplacement")
    qty_in_stock: int = Field(default=0, ge=0, description="Quantité en stock")


class PartUpdate(BaseModel):
    family_code: Optional[str] = None
    sub_family_code: Optional[str] = None
    unit: Optional[str] = None
    location: Optional[str] = None
    qty_in_stock: Optional[int] = Field(default=None, ge=0)


class PartManufacturerRefCreate(BaseModel):
    manufacturer_name: str = Field(..., description="Nom fabricant")
    manufacturer_ref: str = Field(..., description="Référence fabricant")
    label: Optional[str] = Field(default=None, description="Désignation")
    is_preferred: bool = Field(default=False)


class PartSupplierRefCreate(BaseModel):
    supplier_id: UUID = Field(..., description="ID fournisseur")
    supplier_ref: str = Field(..., description="Référence fournisseur")
    unit_price: Optional[float] = Field(default=None, ge=0)
    min_order_quantity: int = Field(default=1, ge=1)
    delivery_time_days: Optional[int] = Field(default=None, ge=0)
    is_preferred: bool = Field(default=False)
    product_url: Optional[str] = Field(default=None)
