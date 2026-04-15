from typing import List

from fastapi import APIRouter, Depends, Response

from api.auth.permissions import require_authenticated
from api.preventive_plans.repo import PreventivePlanRepository
from api.preventive_plans.schemas import (
    GammeStepIn,
    GammeStepOut,
    PreventivePlanIn,
    PreventivePlanOut,
    PreventivePlanUpdate,
)

router = APIRouter(
    prefix="/preventive-plans",
    tags=["Preventive Plans"],
    dependencies=[Depends(require_authenticated)],
)


@router.get("", response_model=List[PreventivePlanOut])
def list_preventive_plans(active_only: bool = True):
    """Liste tous les plans de maintenance préventive"""
    repo = PreventivePlanRepository()
    return repo.get_list(active_only=active_only)


@router.get("/{plan_id}", response_model=PreventivePlanOut)
def get_preventive_plan(plan_id: str):
    """Récupère un plan de maintenance préventive par ID"""
    repo = PreventivePlanRepository()
    return repo.get_by_id(plan_id)


@router.post("", response_model=PreventivePlanOut, status_code=201)
def create_preventive_plan(data: PreventivePlanIn):
    """Crée un nouveau plan de maintenance préventive"""
    repo = PreventivePlanRepository()
    return repo.create(data)


@router.put("/{plan_id}", response_model=PreventivePlanOut)
def update_preventive_plan(plan_id: str, data: PreventivePlanUpdate):
    """Met à jour un plan de maintenance préventive (PATCH sémantique, code immuable)"""
    repo = PreventivePlanRepository()
    return repo.update(plan_id, data)


@router.patch("/{plan_id}/steps", response_model=List[GammeStepOut])
def replace_plan_steps(plan_id: str, steps: List[GammeStepIn]):
    """Remplace entièrement les étapes de gamme d'un plan"""
    repo = PreventivePlanRepository()
    return repo.replace_steps(plan_id, steps)


@router.delete("/{plan_id}", status_code=204)
def delete_preventive_plan(plan_id: str):
    """Désactive un plan de maintenance préventive (soft delete)"""
    repo = PreventivePlanRepository()
    repo.soft_delete(plan_id)
    return Response(status_code=204)
