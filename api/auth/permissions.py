from fastapi import Depends, Request
from api.errors.exceptions import UnauthorizedError


def require_authenticated(request: Request) -> str:
    """
    Dépendance FastAPI : vérifie que l'utilisateur est authentifié.
    Retourne le user_id extrait du JWT par le middleware.

    Gestion des rôles prévue en V4.
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise UnauthorizedError("Authentification requise")
    return user_id
