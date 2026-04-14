from typing import Optional

from fastapi import APIRouter, Depends, Query

from api.auth.permissions import require_authenticated
from api.errors.exceptions import ValidationError
from api.gamme_step_validations.repo import GammeStepValidationRepository
from api.gamme_step_validations.schemas import (
    GammeProgressOut,
    GammeStepValidationOut,
    GammeStepValidationPatch,
)

router = APIRouter(
    prefix="/gamme-step-validations",
    tags=["Gamme Step Validations"],
    dependencies=[Depends(require_authenticated)],
)


@router.get("", response_model=list[GammeStepValidationOut])
def list_validations(
    intervention_id: Optional[str] = Query(None, description="ID de l'intervention"),
    occurrence_id: Optional[str] = Query(None, description="ID de l'occurrence"),
):
    """Liste les validations d'étapes de gamme pour une intervention ou une occurrence"""
    repo = GammeStepValidationRepository()
    if intervention_id:
        return repo.get_by_intervention(intervention_id)
    if occurrence_id:
        return repo.get_by_occurrence(occurrence_id)
    raise ValidationError("intervention_id ou occurrence_id requis")


@router.get("/by-occurrence", response_model=list[GammeStepValidationOut])
def list_validations_by_occurrence(
    occurrence_id: str = Query(..., description="ID de l'occurrence"),
):
    """Liste les validations d'étapes de gamme pour une occurrence"""
    repo = GammeStepValidationRepository()
    return repo.get_by_occurrence(occurrence_id)


@router.get("/progress", response_model=GammeProgressOut)
def get_progress(
    intervention_id: Optional[str] = Query(None, description="ID de l'intervention"),
    occurrence_id: Optional[str] = Query(None, description="ID de l'occurrence"),
):
    """Calcule la progression de la gamme pour une intervention ou une occurrence"""
    repo = GammeStepValidationRepository()
    if intervention_id:
        return repo.get_progress(intervention_id)
    if occurrence_id:
        return repo.get_progress_by_occurrence(occurrence_id)
    raise ValidationError("intervention_id ou occurrence_id requis")


@router.patch("/{validation_id}", response_model=GammeStepValidationOut)
def patch_validation(validation_id: str, data: GammeStepValidationPatch):
    """Met à jour le statut d'une étape de gamme (validated ou skipped)"""
    repo = GammeStepValidationRepository()
    return repo.patch_validation(validation_id, data)
