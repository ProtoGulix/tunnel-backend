"""
Pool de connexions PostgreSQL (psycopg2 ThreadedConnectionPool).

Usage dans les repos :
    from api.db import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(...)
    finally:
        release_connection(conn)
"""

from api.errors.exceptions import DatabaseError
import logging
import time
from contextlib import contextmanager
from urllib.parse import urlparse

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor, register_uuid

# Enable native UUID adaptation for all connections
register_uuid()


logger = logging.getLogger(__name__)

_pool: pool.ThreadedConnectionPool | None = None


def init_pool(
    database_url: str,
    minconn: int = 2,
    maxconn: int = 10,
    retries: int = 10,
    retry_delay: float = 3.0,
) -> None:
    """Initialise le pool au démarrage de l'application.

    Réessaie jusqu'à `retries` fois avec un délai de `retry_delay` secondes
    entre chaque tentative, afin de tolérer un démarrage tardif de PostgreSQL.
    """
    global _pool
    parsed = urlparse(database_url)
    conn_kwargs = dict(
        minconn=minconn,
        maxconn=maxconn,
        host=parsed.hostname,
        port=parsed.port or 5432,
        user=parsed.username,
        password=parsed.password,
        dbname=parsed.path.lstrip("/"),
        connect_timeout=5,
        options="-c statement_timeout=30000",  # 30s max par requête
    )
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            _pool = pool.ThreadedConnectionPool(**conn_kwargs)
            logger.info("Pool DB initialisé (%d-%d connexions)", minconn, maxconn)
            return
        except psycopg2.OperationalError as e:
            last_error = e
            logger.warning(
                "Tentative %d/%d : PostgreSQL indisponible, nouvel essai dans %.0fs — %s",
                attempt, retries, retry_delay, e,
            )
            if attempt < retries:
                time.sleep(retry_delay)
    logger.error("Impossible d'initialiser le pool DB après %d tentatives", retries)
    raise DatabaseError(f"Connexion PostgreSQL impossible : {last_error}") from last_error


def get_connection() -> psycopg2.extensions.connection:
    """Emprunte une connexion du pool."""
    if _pool is None:
        raise DatabaseError("Pool DB non initialisé")
    try:
        conn = _pool.getconn()
        conn.autocommit = False
        return conn
    except pool.PoolError as e:
        raise DatabaseError(f"Pool saturé ou indisponible : {e}") from e


def release_connection(conn: psycopg2.extensions.connection) -> None:
    """Restitue la connexion au pool (même en cas d'erreur)."""
    if _pool is None or conn is None:
        return
    try:
        if conn.status == psycopg2.extensions.STATUS_IN_TRANSACTION:
            conn.rollback()
        _pool.putconn(conn)
    except Exception:
        # En dernier recours, ferme la connexion
        try:
            conn.close()
        except Exception:
            pass


@contextmanager
def db_connection():
    """
    Context manager pour utilisation avec `with` :

        with db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(...)
            conn.commit()
    """
    conn = get_connection()
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        release_connection(conn)


def close_pool() -> None:
    """Ferme toutes les connexions du pool (arrêt de l'application)."""
    global _pool
    if _pool:
        _pool.closeall()
        _pool = None
        logger.info("Pool DB fermé")


def check_connection() -> str:
    """Vérifie que le pool fonctionne. Retourne 'connected' ou message d'erreur."""
    try:
        with db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1")
        return "connected"
    except Exception as e:
        return f"error: {type(e).__name__}"
