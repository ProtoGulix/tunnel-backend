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

import logging
from contextlib import contextmanager
from urllib.parse import urlparse

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from api.errors.exceptions import DatabaseError

logger = logging.getLogger(__name__)

_pool: pool.ThreadedConnectionPool | None = None


def init_pool(database_url: str, minconn: int = 2, maxconn: int = 10) -> None:
    """Initialise le pool au démarrage de l'application."""
    global _pool
    parsed = urlparse(database_url)
    try:
        _pool = pool.ThreadedConnectionPool(
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
        logger.info("Pool DB initialisé (%d-%d connexions)", minconn, maxconn)
    except psycopg2.OperationalError as e:
        logger.error("Impossible d'initialiser le pool DB : %s", e)
        raise DatabaseError(f"Connexion PostgreSQL impossible : {e}") from e


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
