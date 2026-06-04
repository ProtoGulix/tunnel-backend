from typing import List, Optional

from fastapi import APIRouter, Query, Request, HTTPException, Depends

from api.users.repo import UserRepository
from api.users.schemas import UserListItem, UserOut, ProfileUpdate, PasswordChange

from api.auth.permissions import require_authenticated
from api.utils.response import single

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_authenticated)])


@router.get("/me")
def get_current_user(request: Request):
    """Retourne l'utilisateur courant (extrait du JWT)"""
    user_id = getattr(request.state, 'user_id', None)

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authentification requise. Connectez-vous d'abord via POST /auth/login"
        )

    repo = UserRepository()
    return single(repo.get_by_id(str(user_id)))


@router.get("", response_model=List[UserListItem])
def list_users(
    skip: int = Query(0, ge=0, description="Offset de pagination"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Nombre max de résultats"),
    status: Optional[str] = Query(
        None, description="Filtrer par statut (active, suspended, etc.)"),
    search: Optional[str] = Query(
        None, description="Recherche sur nom, prénom, email"),
):
    """Liste les utilisateurs avec filtres optionnels"""
    repo = UserRepository()
    return repo.get_all(limit=limit, offset=skip, status=status, search=search)


@router.get("/{user_id}")
def get_user(user_id: str):
    """Détail d'un utilisateur par ID"""
    repo = UserRepository()
    return single(repo.get_by_id(user_id))


@router.patch("/me/profile", response_model=UserOut)
def update_my_profile(body: ProfileUpdate, request: Request):
    """Met à jour le prénom, nom et/ou initiales de l'utilisateur connecté."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentification requise")

    repo = UserRepository()
    return repo.update_profile(str(user_id), body.model_dump(exclude_none=True))


@router.post("/me/password", status_code=200)
def change_my_password(body: PasswordChange, request: Request):
    """Change le mot de passe de l'utilisateur connecté (vérifie l'ancien avant)."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentification requise")

    repo = UserRepository()
    repo.change_password(str(user_id), body.current_password, body.new_password)
    return {"message": "Mot de passe modifié avec succès"}
