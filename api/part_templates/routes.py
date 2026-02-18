from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from api.part_templates.repo import PartTemplateRepository
from api.part_templates.schemas import PartTemplateIn, PartTemplateUpdate
from api.stock_items.template_service import TemplateService
from api.stock_items.template_schemas import PartTemplate
from api.errors.exceptions import DatabaseError, NotFoundError, ValidationError

router = APIRouter(prefix="/part-templates", tags=["part-templates"])


@router.get("/", response_model=List[PartTemplate])
async def list_templates():
    """
    Liste tous les templates (dernière version de chaque) avec leurs champs
    Retourne les données complètes (optimisé pour pages de gestion)
    """
    repo = PartTemplateRepository()
    try:
        return repo.get_all()
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/code/{code}", response_model=List[dict])
async def get_template_versions_by_code(code: str):
    """
    Récupère toutes les versions d'un template par code
    """
    repo = PartTemplateRepository()
    try:
        versions = repo.get_by_code(code)
        if not versions:
            raise HTTPException(
                status_code=404, detail="Template %s non trouvé" % code)
        return versions
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{template_id}", response_model=PartTemplate)
async def get_template(
    template_id: str,
    version: Optional[int] = Query(
        None, description="Version spécifique (dernière si omis)")
):
    """
    Récupère un template complet avec ses champs et enum_values
    Si version est omise, retourne la version la plus récente
    """
    service = TemplateService()
    try:
        return service.load_template(template_id, version)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/", response_model=dict, status_code=201)
async def create_template(data: PartTemplateIn):
    """
    Crée un nouveau template (version 1)

    Le template inclut :
    - code unique
    - pattern de génération
    - liste des champs avec leurs types
    - valeurs enum si applicable
    """
    repo = PartTemplateRepository()
    try:
        return repo.create(data)
    except (ValidationError, DatabaseError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/{template_id}/versions", response_model=dict, status_code=201)
async def create_template_version(template_id: str, data: PartTemplateUpdate):
    """
    Crée une nouvelle version d'un template existant

    Permet de faire évoluer un template sans casser les pièces existantes
    Le numéro de version est incrémenté automatiquement
    """
    repo = PartTemplateRepository()
    try:
        return repo.create_new_version(template_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except (ValidationError, DatabaseError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    version: Optional[int] = Query(
        None, description="Version à supprimer (toutes si omis)")
):
    """
    Supprime un template ou une version spécifique

    Si version est omise, supprime toutes les versions du template
    Refuse la suppression si des pièces utilisent ce template
    """
    repo = PartTemplateRepository()
    try:
        repo.delete(template_id, version)
        if version:
            return {"message": "Template %s version %s supprimé" % (template_id, version)}
        return {"message": "Template %s supprimé (toutes versions)" % template_id}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
