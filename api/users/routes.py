from typing import List, Optional

from fastapi import APIRouter, Query, Request, HTTPException, Depends

from api.users.repo import UserRepository
from api.users.schemas import UserListItem, UserOut

from api.auth.permissions import require_authenticated

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_authenticated)])


@router.get("/me", response_model=UserOut)
def get_current_user(request: Request):
    """Retourne l'utilisateur courant (extrait du JWT)"""
    user_id = getattr(request.state, 'user_id', None)

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authentification requise. Connectez-vous d'abord via POST /auth/login"
        )

    repo = UserRepository()
    return repo.get_by_id(str(user_id))


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


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: str):
    """Détail d'un utilisateur par ID"""
    repo = UserRepository()
    return repo.get_by_id(user_id)
