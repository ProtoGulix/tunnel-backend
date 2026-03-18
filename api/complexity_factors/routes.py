from fastapi import APIRouter, Depends
from typing import List
from api.complexity_factors.repo import ComplexityFactorRepository
from api.complexity_factors.schemas import ComplexityFactorOut

from api.auth.permissions import require_authenticated

router = APIRouter(prefix="/complexity-factors", tags=["complexity-factors"], dependencies=[Depends(require_authenticated)])


@router.get("/", response_model=List[ComplexityFactorOut])
def list_factors():
    """Liste tous les facteurs de complexité"""
    repo = ComplexityFactorRepository()
    return repo.get_all()


@router.get("/{code}", response_model=ComplexityFactorOut)
def get_factor(code: str):
    """Récupère un facteur de complexité par code"""
    repo = ComplexityFactorRepository()
    return repo.get_by_code(code)
