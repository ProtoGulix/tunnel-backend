import logging
from fastapi import HTTPException, status
from api.db import get_connection, release_connection

logger = logging.getLogger(__name__)

_MSG_BLOCKED = "Trop de tentatives. Réessayez plus tard."


def check_ip_blocklist(ip: str, conn) -> None:
    """Lève 429 si l'IP est dans ip_blocklist (permanente ou non expirée)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id FROM ip_blocklist
            WHERE ip_address = %s
              AND (blocked_until IS NULL OR blocked_until > now())
            LIMIT 1
            """,
            (ip,),
        )
        if cur.fetchone():
            logger.warning("IP bloquée : %s", ip)
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                                detail=_MSG_BLOCKED)


def check_email_flood(email: str, conn) -> None:
    """Lève 429 si ≥ 5 échecs pour cet email dans les 15 dernières minutes."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) FROM auth_attempt
            WHERE email = %s
              AND success = false
              AND created_at > now() - INTERVAL '15 minutes'
            """,
            (email,),
        )
        count = cur.fetchone()[0]
    if count >= 5:
        logger.warning("Flood email détecté : %s (%d tentatives)", email, count)
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail=_MSG_BLOCKED)


def check_ip_flood(ip: str, conn) -> None:
    """Lève 429 si ≥ 20 tentatives depuis cette IP dans la dernière heure."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) FROM auth_attempt
            WHERE ip_address = %s
              AND created_at > now() - INTERVAL '1 hour'
            """,
            (ip,),
        )
        count = cur.fetchone()[0]
    if count >= 20:
        logger.warning("Flood IP détecté : %s (%d tentatives)", ip, count)
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail=_MSG_BLOCKED)


def record_attempt(email: str | None, ip: str, success: bool, conn) -> None:
    """Enregistre une tentative de connexion."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO auth_attempt (email, ip_address, success) VALUES (%s, %s, %s)",
            (email, ip, success),
        )
