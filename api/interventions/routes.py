from fastapi import APIRouter, Request, Query, Depends
from typing import List, Dict, Any, Optional
from api.interventions.repo import InterventionRepository
from api.intervention_actions.repo import InterventionActionRepository
from api.interventions.schemas import InterventionOut, InterventionIn, InterventionCreate, InterventionStats
from api.interventions.validators import InterventionValidator
from api.intervention_actions.schemas import InterventionActionOut
from api.intervention_status_log.schemas import InterventionStatusLogOut
from api.intervention_tasks.schemas import TaskProgressOut, InterventionTaskOut
from api.equipements.schemas import EquipementDetail
from api.constants import INTERVENTION_TYPES
from api.errors.exceptions import ValidationError
from api.auth.permissions import require_authenticated
from api.utils.response import single, referentiel, paginated

# Résolution des références circulaires : InterventionOut.request référence
# InterventionRequestListItem (intervention_requests.schemas → interventions.schemas)
from api.intervention_requests.schemas import InterventionRequestListItem
InterventionOut.model_rebuild(_types_namespace={
    "Optional": Optional,
    "List": List,
    "InterventionRequestListItem": InterventionRequestListItem,
    "InterventionActionOut": InterventionActionOut,
    "InterventionStatusLogOut": InterventionStatusLogOut,
    "TaskProgressOut": TaskProgressOut,
    "InterventionTaskOut": InterventionTaskOut,
    "EquipementDetail": EquipementDetail,
    "InterventionStats": InterventionStats,
})

router = APIRouter(prefix="/interventions",
                   tags=["interventions"], dependencies=[Depends(require_authenticated)])


def add_stats_to_intervention(intervention: Dict[str, Any], actions: List[Dict[str, Any]]) -> None:
    """Ajoute les stats calculées à une intervention"""
    intervention["actions"] = actions
    intervention["total_time"] = sum(a.get("time_spent") or 0 for a in actions)
    intervention["action_count"] = len(actions)
    complexities = [a.get("complexity_score")
                    for a in actions if a.get("complexity_score")]
    intervention["avg_complexity"] = round(
        sum(complexities) / len(complexities), 2) if complexities else None


@router.get("/types")
def list_intervention_types():
    """Liste tous les types d'intervention disponibles (id, title, color)"""
    return referentiel(INTERVENTION_TYPES)


@router.get("")
def list_interventions(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str | None = Query(
        None, description="Recherche insensible à la casse sur code, titre, code équipement ou nom équipement"),
    equipement_id: str | None = Query(
        None, description="Filtre intervention.machine_id"),
    status: str | None = Query(
        None, description="CSV de codes statut (ex: open,in_progress,ferme)"),
    priority: str | None = Query(
        None, description="CSV de priorités (faible,normale,important,urgent)"),
    sort: str | None = Query(
        None, description="Ex: -priority,-reported_date ou -reported_date"),
    include: str | None = Query(None, description="Ex: stats"),
    printed: bool | None = Query(
        False, description="Filtre par statut d'impression/archivage. false=actives (défaut), true=archivées, null=toutes"),
    tech_id: str | None = Query(
        None, description="Filtrer par UUID technicien pilote"),
) -> Dict[str, Any]:
    """Liste interventions avec filtres/sort et stats optionnelles (sans actions)"""
    intervention_repo = InterventionRepository()

    statuses = [s.strip() for s in status.split(',')] if status else None
    priorities = [p.strip() for p in priority.split(',')] if priority else None
    include_list = [i.strip() for i in include.split(',')] if include else []
    include_stats = (include is None) or ("stats" in include_list)
    include_tasks = "tasks" in include_list

    items = intervention_repo.get_all(
        limit=limit,
        offset=skip,
        search=search,
        equipement_id=equipement_id,
        statuses=statuses,
        priorities=priorities,
        sort=sort,
        include_stats=include_stats,
        include_tasks=include_tasks,
        printed=printed,
        tech_id=tech_id,
    )
    total = intervention_repo.count_all(
        search=search,
        equipement_id=equipement_id,
        statuses=statuses,
        priorities=priorities,
        printed=printed,
        tech_id=tech_id,
    )
    return paginated(items, total=total, offset=skip, limit=limit, audit_entity="intervention")


@router.get("/{intervention_id}")
def get_intervention(intervention_id: str, request: Request) -> Dict[str, Any]:
    """Récupère une intervention par ID avec ses actions et stats (calculées en SQL)"""
    intervention_repo = InterventionRepository()
    data = intervention_repo.get_by_id(intervention_id)
    return single(data, audit_entity="intervention")


@router.get("/{intervention_id}/actions")
def get_intervention_actions(intervention_id: str, request: Request):
    """Récupère les actions d'une intervention"""
    repo = InterventionActionRepository()
    return single(repo.get_by_intervention(intervention_id))


@router.post("", status_code=201)
def create_intervention(data: InterventionCreate, request: Request):
    """
    Crée une nouvelle intervention.

    **Audit obligatoire** : le champ `reason_code` est requis (voir `GET /audit/reasons`).
    `reason_text` est obligatoire si `reason_code=OTHER`.
    """
    payload = data.model_dump(exclude_none=True)
    InterventionValidator.validate_request_required(payload)
    repo = InterventionRepository()
    return single(repo.add(payload))


@router.put("/{intervention_id}")
def update_intervention(intervention_id: str, data: InterventionIn, request: Request):
    """
    Met à jour une intervention existante.

    **Audit obligatoire** : le champ `reason_code` est requis (voir `GET /audit/reasons`).
    `reason_text` est obligatoire si `reason_code=OTHER`.
    """
    repo = InterventionRepository()
    return single(repo.update(intervention_id, data.model_dump(exclude_none=True)))


@router.post("/{intervention_id}/force-close-request")
def force_close_linked_request(intervention_id: str, request: Request):
    """
    Force la clôture de la demande d'intervention liée quand la cascade automatique a échoué.

    Conditions requises :
    - L'intervention doit être au statut `ferme`
    - Une demande liée doit être encore en statut `acceptee`

    Retourne l'intervention mise à jour avec la demande désormais `cloturee`.
    """
    repo = InterventionRepository()
    return single(repo.force_close_request(intervention_id))


@router.delete("/{intervention_id}")
def delete_intervention(intervention_id: str, request: Request):
    """Supprime une intervention"""
    repo = InterventionRepository()
    repo.delete(intervention_id)
    return {"detail": "Intervention supprimée"}
