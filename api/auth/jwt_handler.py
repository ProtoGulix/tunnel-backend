import jwt
import logging
from typing import Dict, Any
from api.settings import settings
from api.errors.exceptions import UnauthorizedError

logger = logging.getLogger(__name__)


def decode_directus_token(token: str) -> Dict[str, Any]:
    """
    Décode et vérifie un JWT Directus.

    Si DIRECTUS_SECRET est configuré : vérifie la signature HS256 (recommandé).
    Sinon : décode sans vérification (fallback dev uniquement, log warning).
    """
    try:
        if settings.DIRECTUS_SECRET:
            payload = jwt.decode(
                token,
                settings.DIRECTUS_SECRET,
                algorithms=["HS256"],
                options={"verify_exp": True},
            )
        else:
            logger.warning(
                "DIRECTUS_SECRET non configuré — JWT décodé sans vérification de signature. "
                "Configurer DIRECTUS_SECRET en production."
            )
            payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Token expiré")
    except jwt.InvalidSignatureError:
        raise UnauthorizedError("Signature JWT invalide")
    except jwt.DecodeError:
        raise UnauthorizedError("Token invalide")


def extract_user_from_token(token: str) -> Dict[str, Any]:
    """
    Extrait les infos utilisateur du token JWT.
    Retourne: {user_id, role, iat, exp}
    """
    payload = decode_directus_token(token)

    user_id = payload.get("id") or payload.get("sub")
    role = payload.get("role")

    logger.debug(f"Token payload: id={user_id}, role={role}")

    if not user_id:
        logger.error(f"user_id manquant dans le token. Payload: {payload}")
        raise UnauthorizedError("user_id manquant dans le token")

    return {
        "user_id": user_id,
        "role": role,
        "iat": payload.get("iat"),
        "exp": payload.get("exp")
    }
