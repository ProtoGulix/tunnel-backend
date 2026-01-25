import jwt
from typing import Optional, Dict, Any
from api.settings import settings
from api.errors.exceptions import UnauthorizedError


def decode_directus_token(token: str) -> Dict[str, Any]:
    """
    Décode un JWT Directus sans vérification de signature.

    En production, vérifier la signature avec la clé publique de Directus.
    Pour le MVP : extraction du payload uniquement.
    """
    try:
        # Decode sans vérification pour le MVP
        # TODO: Implémenter la vérification de signature en production
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except jwt.DecodeError:
        raise UnauthorizedError("Token invalide")
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Token expiré")


def extract_user_from_token(token: str) -> Dict[str, Any]:
    """
    Extrait les infos utilisateur du token JWT.
    Retourne: {user_id, role, iat, exp}
    """
    payload = decode_directus_token(token)

    user_id = payload.get("sub")
    role = payload.get("role")

    if not user_id:
        raise UnauthorizedError("user_id manquant dans le token")

    return {
        "user_id": user_id,
        "role": role,
        "iat": payload.get("iat"),
        "exp": payload.get("exp")
    }
