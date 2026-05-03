import asyncio
import hashlib
import logging
import random
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr, field_validator

from api.auth.antiflood import (
    check_ip_blocklist, check_email_flood, check_ip_flood, record_attempt,
)
from api.auth.jwt_handler import create_access_token, create_refresh_token
from api.auth.permissions import require_authenticated, permission_cache
from api.db import get_connection, release_connection
from api.errors.exceptions import UnauthorizedError
from api.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


class LoginPayload(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_max_length(cls, v: str) -> str:
        if len(v) > 256:
            raise ValueError("Mot de passe trop long")
        return v


class RefreshPayload(BaseModel):
    refresh_token: str


class LogoutPayload(BaseModel):
    refresh_token: str


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def _login_delay() -> None:
    """Délai constant 50-200 ms appliqué avant TOUTE réponse login (succès ou échec)."""
    await asyncio.sleep(random.uniform(0.05, 0.20))


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _log_security_event(conn, event_type: str, user_id: Optional[str],
                        ip: str, detail: dict) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO security_log (event_type, user_id, ip_address, detail)
            VALUES (%s, %s::uuid, %s, %s::jsonb)
            """,
            (event_type, user_id, ip,
             __import__("json").dumps(detail, default=str)),
        )


@router.post("/login")
async def login(request: Request, payload: LoginPayload):
    """
    Authentification native Tunnel.
    Délai aléatoire appliqué avant toute réponse pour contrer le timing attack.
    """
    await _login_delay()
    ip = _get_client_ip(request)

    conn = None
    try:
        conn = get_connection()

        check_ip_blocklist(ip, conn)
        check_email_flood(payload.email, conn)
        check_ip_flood(ip, conn)

        # Vérification whitelist domaine email (si des règles existent)
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM email_domain_rule")
            has_rules = cur.fetchone()[0] > 0
        if has_rules:
            domain = payload.email.split("@")[-1].lower()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT allowed FROM email_domain_rule WHERE domain = %s",
                    (domain,),
                )
                row = cur.fetchone()
            if row is None or not row[0]:
                record_attempt(payload.email, ip, False, conn)
                conn.commit()
                # Même message que les autres erreurs
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                    detail="Email ou mot de passe incorrect")

        # Récupération utilisateur (timing constant même si inexistant via bcrypt)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT tu.id, tu.password_hash, tu.is_active,
                       tr.code AS role_code,
                       tu.first_name, tu.last_name, tu.initial, tu.email
                FROM tunnel_user tu
                JOIN tunnel_role tr ON tr.id = tu.role_id
                WHERE tu.email = %s
                """,
                (payload.email,),
            )
            user = cur.fetchone()

        # Vérification du mot de passe (timing constant : on vérifie même si user absent)
        # Supporte bcrypt ($2b$/$2y$) et argon2id (héritage Directus).
        # Au premier login argon2id réussi, re-hash automatique en bcrypt.
        import bcrypt
        from argon2 import PasswordHasher
        from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

        raw_hash = user[1] if user else "$2b$12$dummyhashfordummycheckingpurposes000000000000"
        password_ok = False

        if raw_hash.startswith("$argon2"):
            try:
                PasswordHasher().verify(raw_hash, payload.password)
                password_ok = True
            except (VerifyMismatchError, VerificationError, InvalidHashError):
                password_ok = False
        else:
            normalized = raw_hash.replace("$2y$", "$2b$").encode()
            try:
                password_ok = bcrypt.checkpw(payload.password.encode(), normalized)
            except ValueError:
                password_ok = False

        if not user or not password_ok or not user[2]:
            record_attempt(payload.email, ip, False, conn)
            _log_security_event(conn, "LOGIN_FAIL", None, ip,
                                 {"email": payload.email, "reason": "invalid_credentials"})
            conn.commit()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                 detail="Email ou mot de passe incorrect")

        user_id, _, _, role_code, first_name, last_name, initial, email = user
        user_id = str(user_id)

        # Re-hash argon2id → bcrypt au premier login réussi (migration transparente)
        if raw_hash.startswith("$argon2"):
            new_hash = bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode()
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE tunnel_user SET password_hash = %s WHERE id = %s::uuid",
                    (new_hash, user_id),
                )

        permissions = permission_cache.permissions_for_role(role_code)
        access_token = create_access_token(user_id, role_code, permissions)
        token_clair, token_hash = create_refresh_token()

        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=settings.REFRESH_TOKEN_EXPIRE_HOURS)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO refresh_token (user_id, token_hash, expires_at, ip_address)
                VALUES (%s::uuid, %s, %s, %s)
                """,
                (user_id, token_hash, expires_at, ip),
            )

        record_attempt(payload.email, ip, True, conn)
        _log_security_event(conn, "LOGIN_SUCCESS", user_id, ip, {"email": email})
        conn.commit()

        return {
            "access_token": access_token,
            "refresh_token": token_clair,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user_id,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "initial": initial,
                "role": role_code,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur login : %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Erreur interne") from e
    finally:
        if conn:
            release_connection(conn)


@router.post("/refresh")
async def refresh_token(payload: RefreshPayload, request: Request):
    """
    Rotation du refresh token.
    Détection de vol : si le token est déjà révoqué, tous les tokens du user sont révoqués.
    """
    ip = _get_client_ip(request)
    token_hash = _hash_token(payload.refresh_token)

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT rt.id, rt.user_id, rt.revoked, rt.expires_at,
                       tu.is_active, tr.code AS role_code
                FROM refresh_token rt
                JOIN tunnel_user tu ON tu.id = rt.user_id
                JOIN tunnel_role tr ON tr.id = tu.role_id
                WHERE rt.token_hash = %s
                """,
                (token_hash,),
            )
            row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                 detail="Token invalide")

        rt_id, user_id, revoked, expires_at, is_active, role_code = row
        user_id = str(user_id)

        # Détection de vol : token déjà révoqué → révoquer tous les tokens du user
        if revoked:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE refresh_token SET revoked = true WHERE user_id = %s::uuid",
                    (user_id,),
                )
            _log_security_event(conn, "TOKEN_REVOKED", user_id, ip,
                                 {"reason": "reuse_detected", "all_tokens_revoked": True})
            conn.commit()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                 detail="Token invalide")

        now = datetime.now(timezone.utc)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now or not is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                 detail="Token invalide")

        # Rotation : révoquer l'ancien, émettre un nouveau
        with conn.cursor() as cur:
            cur.execute("UPDATE refresh_token SET revoked = true WHERE id = %s", (rt_id,))

        permissions = permission_cache.permissions_for_role(role_code)
        new_access = create_access_token(user_id, role_code, permissions)
        new_clair, new_hash = create_refresh_token()
        new_expires = now + timedelta(hours=settings.REFRESH_TOKEN_EXPIRE_HOURS)

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO refresh_token (user_id, token_hash, expires_at, ip_address)
                VALUES (%s::uuid, %s, %s, %s)
                """,
                (user_id, new_hash, new_expires, ip),
            )
        conn.commit()

        return {
            "access_token": new_access,
            "refresh_token": new_clair,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur refresh : %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Erreur interne") from e
    finally:
        if conn:
            release_connection(conn)


@router.post("/logout")
async def logout(payload: LogoutPayload, request: Request,
                 user_id: str = Depends(require_authenticated)):
    """Révoque le refresh token présenté."""
    ip = _get_client_ip(request)
    token_hash = _hash_token(payload.refresh_token)

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE refresh_token SET revoked = true WHERE token_hash = %s",
                (token_hash,),
            )
        _log_security_event(conn, "TOKEN_REVOKED", user_id, ip, {})
        conn.commit()
        return {"message": "Déconnecté"}
    except Exception as e:
        logger.error("Erreur logout : %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Erreur interne") from e
    finally:
        if conn:
            release_connection(conn)


@router.get("/me")
async def get_me(request: Request, user_id: str = Depends(require_authenticated)):
    """Retourne le profil complet de l'utilisateur connecté."""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT tu.id, tu.email, tu.first_name, tu.last_name,
                       tu.initial, tr.code AS role_code
                FROM tunnel_user tu
                JOIN tunnel_role tr ON tr.id = tu.role_id
                WHERE tu.id = %s::uuid AND tu.is_active = true
                """,
                (user_id,),
            )
            row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                 detail="Utilisateur non trouvé")
        uid, email, first_name, last_name, initial, role_code = row
        permissions = permission_cache.permissions_for_role(role_code)
        return {
            "id": str(uid),
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "initial": initial,
            "role": role_code,
            "permissions": permissions,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur /auth/me : %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Erreur interne") from e
    finally:
        if conn:
            release_connection(conn)
