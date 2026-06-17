import csv
import io
import logging
from fastapi import APIRouter, File, Form, HTTPException, Query, Depends, UploadFile
from typing import Any, Dict, List, Optional, Literal, Union
from datetime import date
from api.purchase_requests.repo import PurchaseRequestRepository
from api.purchase_requests.schemas import (
    PurchaseRequestIn,
    PurchaseRequestListItem,
    PurchaseRequestDetail,
    PurchaseRequestStats,
    DispatchResult,
    ImportResult,
)
from api.errors.exceptions import ValidationError
from api.constants import DERIVED_STATUS_CONFIG
from api.utils.response import single, referentiel

logger = logging.getLogger(__name__)

VALID_STATUSES = tuple(DERIVED_STATUS_CONFIG.keys())

from api.auth.permissions import require_authenticated

router = APIRouter(prefix="/purchase-requests", tags=["purchase-requests"], dependencies=[Depends(require_authenticated)])


# ─── Helper CSV partagé ───────────────────────────────────────────────────────

def _parse_csv_bytes(content_bytes: bytes) -> tuple[list[dict], str, int]:
    """
    Décode, détecte le séparateur et parse un fichier CSV.
    Retourne (rows, separator, header_line_index).
    Utilisé par /import/headers ET /import pour garantir un parsing identique.
    """
    try:
        content = content_bytes.decode('utf-8-sig')
    except UnicodeDecodeError:
        content = content_bytes.decode('latin-1')

    sample = content[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=',;')
        sep = dialect.delimiter
    except csv.Error:
        sep = ','

    all_lines = [l for l in content.splitlines() if l.strip()]
    header_line_idx = 0
    for i, line in enumerate(all_lines[:10]):
        cells = [c.strip().strip('"').strip("'") for c in line.split(sep)]
        if sum(1 for c in cells if c) >= 2:
            header_line_idx = i
            break
    effective_content = '\n'.join(all_lines[header_line_idx:])

    reader = csv.DictReader(io.StringIO(effective_content), delimiter=sep)
    try:
        rows = list(reader)
    except Exception as e:
        raise ValidationError(f"Impossible de lire le CSV : {e}")

    return rows, sep, header_line_idx


# ========== Endpoints optimisés v1.2.0 ==========

@router.get("/statuses")
def list_purchase_request_statuses():
    """Retourne tous les statuts dérivés possibles avec leur label et couleur."""
    return referentiel([
        {"code": code, "label": cfg["label"], "color": cfg["color"]}
        for code, cfg in DERIVED_STATUS_CONFIG.items()
    ])


@router.get("/stats")
def get_purchase_requests_stats(
    start_date: Optional[date] = Query(
        None, description="Date début (default: -3 mois)"),
    end_date: Optional[date] = Query(
        None, description="Date fin (default: aujourd'hui)"),
    group_by: str = Query(
        "status", description="Grouper par (status, urgency)")
):
    """
    [v1.2.0] Statistiques agrégées pour dashboards.
    Retourne compteurs totaux, par statut, par urgence, top articles.
    """
    repo = PurchaseRequestRepository()
    return single(repo.get_stats(
        start_date=start_date,
        end_date=end_date,
        group_by=group_by
    ))


@router.get("/list")
def list_purchase_requests_optimized(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Nombre max d'éléments"),
    status: Optional[str] = Query(
        None, description="Filtrer par statut dérivé (TO_QUALIFY, NO_SUPPLIER_REF, PENDING_DISPATCH, OPEN, QUOTED, ORDERED, PARTIAL, RECEIVED, REJECTED)"),
    exclude_statuses: Optional[str] = Query(
        None, description="Statuts à exclure, séparés par virgule. Ex: RECEIVED,REJECTED"),
    intervention_id: Optional[str] = Query(
        None, description="Filtrer par intervention"),
    urgency: Optional[str] = Query(None, description="Filtrer par urgence")
) -> Dict[str, Any]:
    """
    [v1.2.0] Liste optimisée légère pour tableaux.
    - Statut dérivé calculé en SQL
    - Compteurs agrégés (quotes_count, selected_count, suppliers_count)
    - Pas d'objets imbriqués (références directes)
    - Payload ~95% plus léger que version legacy
    """
    exclude_list = [s.strip() for s in exclude_statuses.split(",") if s.strip()] if exclude_statuses else None
    repo = PurchaseRequestRepository()
    data = repo.get_list(
        limit=limit,
        offset=skip,
        status=status,
        intervention_id=intervention_id,
        urgency=urgency,
        exclude_statuses=exclude_list
    )
    return single(data, audit_entity="purchase_request")


@router.get("/detail/{request_id}")
def get_purchase_request_detail(request_id: str) -> Dict[str, Any]:
    """
    [v1.2.0] Détail complet avec contexte enrichi.
    - Intervention complète avec équipement
    - Stock item complet
    - Order lines avec fournisseurs enrichis
    - Statut dérivé avec règles appliquées
    """
    repo = PurchaseRequestRepository()
    data = repo.get_detail(request_id)
    return single(data, audit_entity="purchase_request")


@router.get("/status/{status}", response_model=List[PurchaseRequestListItem])
def list_purchase_requests_by_status(
    status: str,
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre max d'éléments"),
    urgency: Optional[str] = Query(None, description="Filtrer par urgence : normal, high, critical")
):
    """
    Liste les demandes d'achat filtrées par statut dérivé.

    Statuts valides : TO_QUALIFY, NO_SUPPLIER_REF, PENDING_DISPATCH, OPEN, QUOTED, ORDERED, PARTIAL, RECEIVED, REJECTED
    """
    if status not in VALID_STATUSES:
        raise ValidationError(f"Statut invalide '{status}'. Valeurs acceptées : {', '.join(VALID_STATUSES)}")
    repo = PurchaseRequestRepository()
    return repo.get_list(limit=limit, offset=skip, status=status, urgency=urgency)


@router.get("/intervention/{intervention_id}/optimized")
def get_purchase_requests_by_intervention_optimized(
    intervention_id: str,
    view: Literal['list', 'full'] = Query(
        'list', description="Niveau de détail (list=léger, full=complet)")
) -> Union[List[PurchaseRequestListItem], List[PurchaseRequestDetail]]:
    """
    [v1.2.0] Filtre par intervention avec choix de granularité.
    - view=list : retourne PurchaseRequestListItem (rapide)
    - view=full : retourne PurchaseRequestDetail (complet avec contexte)
    """
    repo = PurchaseRequestRepository()
    return repo.get_by_intervention_optimized(intervention_id, view=view)


@router.get("/facets")
def get_purchase_request_facets():
    """Compteurs par statut dérivé en temps réel, sans filtre de date."""
    repo = PurchaseRequestRepository()
    return single(repo.get_facets())


@router.post("/dispatch")
def dispatch_pending_requests():
    """
    [v1.2.12] Dispatch automatique des demandes PENDING_DISPATCH.

    Pour chaque demande prête à dispatcher:
    - Récupère les fournisseurs liés au stock_item
    - Trouve ou crée un supplier_order ouvert par fournisseur
    - Crée une supplier_order_line liée à la demande

    Les demandes passent automatiquement de PENDING_DISPATCH à OPEN.
    """
    repo = PurchaseRequestRepository()
    return single(repo.dispatch_all())


@router.post("/import/headers", status_code=200)
async def get_csv_import_headers(
    file: UploadFile = File(..., description="Fichier CSV"),
):
    """
    Retourne les colonnes détectées par le backend pour un fichier CSV.
    À appeler avant /import pour construire les sélecteurs de colonnes côté client.
    Utilise le même parseur que /import pour garantir la cohérence des noms de colonnes.
    """
    if not file.filename or not file.filename.lower().endswith('.csv'):
        raise ValidationError("Le fichier doit être un CSV (.csv)")

    rows, sep, header_line_idx = _parse_csv_bytes(await file.read())

    if not rows:
        raise ValidationError("Le fichier CSV est vide")

    headers = [h for h in rows[0].keys() if h and h != 'None']
    return {"headers": headers, "separator": sep, "header_row_index": header_line_idx}


@router.post("/import", response_model=ImportResult, status_code=201)
async def import_purchase_requests_from_csv(
    file: UploadFile = File(..., description="Fichier CSV"),
    intervention_id: str = Form(..., description="UUID de l'intervention cible"),
    col_ref: str = Form(..., description="Nom de la colonne référence"),
    col_qty: str = Form(..., description="Nom de la colonne quantité"),
    urgency: str = Form("normal", description="Urgence globale (normal, high, critical)"),
    dry_run: bool = Form(False, description="Mode aperçu : analyse sans créer les DA"),
    excluded_rows: str = Form("", description="Numéros de lignes à ignorer, séparés par virgule (ex: 2,5,7)"),
):
    """
    Importe des demandes d'achat en masse depuis un fichier CSV.

    Détecte automatiquement le séparateur (`,` ou `;`).
    Pour chaque ligne : tente de résoudre la référence dans le catalogue part,
    crée la DA via la logique existante, retourne un rapport ligne par ligne.

    En mode dry_run=True, retourne une analyse sans créer de DA (status='preview').
    Les lignes listées dans excluded_rows sont ignorées lors de l'import réel.
    """
    if not file.filename or not file.filename.lower().endswith('.csv'):
        raise ValidationError("Le fichier doit être un CSV (.csv)")

    rows, _sep, _header_idx = _parse_csv_bytes(await file.read())

    if not rows:
        raise ValidationError("Le fichier CSV est vide")

    headers = list(rows[0].keys()) if rows else []
    if col_ref not in headers:
        raise ValidationError(f"Colonne '{col_ref}' introuvable. Colonnes disponibles : {', '.join(headers)}")
    if col_qty not in headers:
        raise ValidationError(f"Colonne '{col_qty}' introuvable. Colonnes disponibles : {', '.join(headers)}")

    excluded_list = [
        int(r.strip()) for r in excluded_rows.split(',')
        if r.strip().isdigit()
    ] if excluded_rows.strip() else []

    repo = PurchaseRequestRepository()
    result = repo.import_from_csv(
        rows=rows,
        intervention_id=intervention_id,
        col_ref=col_ref,
        col_qty=col_qty,
        urgency=urgency,
        dry_run=dry_run,
        excluded_rows=excluded_list,
    )
    logger.info(
        "Import CSV (%s) : %d créées, %d ignorées, %d erreurs sur %d lignes (intervention=%s)",
        "aperçu" if dry_run else "réel",
        result['created'], result.get('skipped', 0), result['errors'], result['total'], intervention_id
    )
    return result


# ========== Endpoints CRUD ==========

@router.get("")
def list_purchase_requests(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre max d'éléments"),
    status: Optional[str] = Query(None, description="Filtrer par statut dérivé"),
    exclude_statuses: Optional[str] = Query(
        None, description="Statuts à exclure, séparés par virgule. Ex: RECEIVED,REJECTED"),
    intervention_id: Optional[str] = Query(None, description="Filtrer par intervention"),
    urgency: Optional[str] = Query(None, description="Filtrer par urgence")
) -> Dict[str, Any]:
    """Liste toutes les demandes d'achat. Alias de /list."""
    exclude_list = [s.strip() for s in exclude_statuses.split(",") if s.strip()] if exclude_statuses else None
    repo = PurchaseRequestRepository()
    data = repo.get_list(
        limit=limit,
        offset=skip,
        status=status,
        intervention_id=intervention_id,
        urgency=urgency,
        exclude_statuses=exclude_list
    )
    return single(data, audit_entity="purchase_request")


@router.get("/intervention/{intervention_id}", response_model=List[PurchaseRequestListItem])
def get_purchase_requests_by_intervention(intervention_id: str):
    """Demandes liées à une intervention. Alias de /intervention/{id}/optimized?view=list."""
    repo = PurchaseRequestRepository()
    return repo.get_list(limit=1000, offset=0, intervention_id=intervention_id)


@router.get("/{request_id}")
def get_purchase_request(request_id: str) -> Dict[str, Any]:
    """Détail d'une demande d'achat. Alias de /detail/{id}."""
    repo = PurchaseRequestRepository()
    data = repo.get_detail(request_id)
    return single(data, audit_entity="purchase_request")


@router.post("")
def create_purchase_request(purchase_request: PurchaseRequestIn):
    """
    Crée une nouvelle demande d'achat.

    **Audit obligatoire** : le champ `reason_code` est requis (voir `GET /audit/reasons`).
    `reason_text` est obligatoire si `reason_code=OTHER`.
    """
    repo = PurchaseRequestRepository()
    return single(repo.add(purchase_request.model_dump()))


EDITABLE_STATUSES = {'TO_QUALIFY', 'NO_SUPPLIER_REF', 'PENDING_DISPATCH'}

@router.put("/{request_id}")
def update_purchase_request(request_id: str, purchase_request: PurchaseRequestIn):
    """
    Met à jour une demande d'achat existante.

    Modification autorisée uniquement pour les statuts : TO_QUALIFY, NO_SUPPLIER_REF, PENDING_DISPATCH.

    **Audit obligatoire** : le champ `reason_code` est requis (voir `GET /audit/reasons`).
    `reason_text` est obligatoire si `reason_code=OTHER`.
    """
    repo = PurchaseRequestRepository()
    current = repo.get_detail(request_id)
    derived = current['derived_status']
    if derived['code'] not in EDITABLE_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Cette demande ne peut plus être modifiée (statut : {derived['label']})"
        )
    return single(repo.update(request_id, purchase_request.model_dump(exclude_unset=True)))


@router.delete("/{request_id}")
def delete_purchase_request(request_id: str):
    """Supprime une demande d'achat"""
    repo = PurchaseRequestRepository()
    repo.delete(request_id)
    return {"message": f"Demande d'achat {request_id} supprimée"}
