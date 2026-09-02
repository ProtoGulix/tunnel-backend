import logging
from fastapi import APIRouter, Depends, Request
from typing import Any, Dict, List

from api.home_view.repo import HomeViewRepository, RoleHomeViewRepository
from api.home_view.schemas import HomeViewRef, CurrentHomeViewOut, RoleHomeViewOut, RoleHomeViewUpsert
from api.errors.exceptions import ValidationError
from api.auth.permissions import require_authenticated, require_role
from api.utils.response import single, referentiel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/home-view",
    tags=["home-view"],
    dependencies=[Depends(require_authenticated)],
)

home_view_repo = HomeViewRepository()
role_home_view_repo = RoleHomeViewRepository()

_resp_admin = Depends(require_role("RESP", "ADMIN"))


@router.get("", response_model=List[HomeViewRef])
def list_home_views():
    """Référentiel des vues d'accueil disponibles (technicien, acheteur, direction_technique)."""
    return referentiel(home_view_repo.get_all())


@router.get("/me", response_model=CurrentHomeViewOut)
def get_my_home_view(request: Request) -> Dict[str, Any]:
    """
    Vue d'accueil assignée à l'utilisateur courant, résolue depuis son rôle.

    Comportement par défaut garanti : si le rôle de l'utilisateur n'a pas de
    configuration explicite, retourne 'technicien' (comportement actuel,
    aucune régression).
    """
    role_code = getattr(request.state, "role", None)
    return role_home_view_repo.get_for_role_code(role_code)


# ------------------------------------------------------------------ #
# Admin — assignation rôle → vue d'accueil                            #
# ------------------------------------------------------------------ #

@router.get("/admin/assignments", response_model=List[RoleHomeViewOut], dependencies=[_resp_admin])
def list_assignments():
    """
    Liste les assignations rôle → vue d'accueil explicitement configurées.

    Un rôle absent de cette liste est sur la vue par défaut ('technicien') —
    ce n'est pas une anomalie, c'est le comportement garanti pour tout rôle
    non configuré (le technicien notamment n'a jamais besoin d'apparaître ici).
    """
    return role_home_view_repo.list_all()


@router.put("/admin/assignments/{role_id}", response_model=RoleHomeViewOut, dependencies=[_resp_admin])
def upsert_assignment(role_id: str, body: RoleHomeViewUpsert, request: Request) -> Dict[str, Any]:
    """Assigne (ou remplace) la vue d'accueil d'un rôle."""
    updated_by = getattr(request.state, "user_id", None)
    return role_home_view_repo.upsert(role_id, body.home_view, updated_by)


@router.delete("/admin/assignments/{role_id}", status_code=204, dependencies=[_resp_admin])
def delete_assignment(role_id: str):
    """
    Retire la configuration explicite d'un rôle : il retombe sur la vue par
    défaut ('technicien'), sans qu'il soit nécessaire de le réassigner
    explicitement.
    """
    role_home_view_repo.delete(role_id)
