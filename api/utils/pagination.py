"""Schémas standards pour la pagination"""
from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field
from math import ceil


T = TypeVar('T')


class PaginationMeta(BaseModel):
    """Métadonnées de pagination"""
    total: int = Field(..., description="Nombre total d'éléments")
    page: int = Field(...,
                      description="Numéro de la page actuelle (commence à 1)")
    page_size: int = Field(..., description="Nombre d'éléments par page")
    total_pages: int = Field(..., description="Nombre total de pages")
    offset: int = Field(...,
                        description="Position de début dans la liste globale")
    count: int = Field(...,
                       description="Nombre d'éléments retournés dans cette page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Réponse paginée standard"""
    items: List[T] = Field(..., description="Liste des éléments de la page")
    pagination: PaginationMeta = Field(...,
                                       description="Métadonnées de pagination")


def create_pagination_meta(
    total: int,
    offset: int,
    limit: int,
    count: int
) -> PaginationMeta:
    """Crée les métadonnées de pagination"""
    page = (offset // limit) + 1 if limit > 0 else 1
    total_pages = ceil(total / limit) if limit > 0 else 1

    return PaginationMeta(
        total=total,
        page=page,
        page_size=limit,
        total_pages=total_pages,
        offset=offset,
        count=count
    )
