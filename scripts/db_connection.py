"""
db_connection.py - Module de connexion PostgreSQL
==================================================
Fournit une connexion PostgreSQL réutilisable basée sur les variables d'environnement.
"""

import os
from contextlib import contextmanager
from typing import Generator, Optional

import psycopg2
from psycopg2.extensions import connection as PgConnection
from dotenv import load_dotenv


def load_env() -> None:
    """Charge les variables d'environnement depuis .env"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(env_path)


def get_connection_params() -> dict:
    """Récupère les paramètres de connexion depuis l'environnement."""
    load_env()
    return {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', '5432')),
        'dbname': os.getenv('POSTGRES_DB', 'tunnel_db'),
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD'),
        'sslmode': os.getenv('POSTGRES_SSLMODE', 'prefer'),
    }


def get_connection() -> PgConnection:
    """Crée et retourne une connexion PostgreSQL."""
    params = get_connection_params()
    return psycopg2.connect(**params)


@contextmanager
def get_cursor(autocommit: bool = False) -> Generator:
    """
    Context manager pour obtenir un curseur avec gestion automatique 
    de la connexion et des transactions.

    Args:
        autocommit: Si True, chaque requête est commitée immédiatement

    Yields:
        cursor: Curseur PostgreSQL
    """
    conn = get_connection()
    conn.autocommit = autocommit
    cursor = conn.cursor()
    try:
        yield cursor
        if not autocommit:
            conn.commit()
    except Exception as e:
        if not autocommit:
            conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


@contextmanager
def get_dict_cursor(autocommit: bool = False) -> Generator:
    """
    Context manager pour obtenir un curseur dict avec gestion automatique.
    Retourne les résultats sous forme de dictionnaires.
    """
    from psycopg2.extras import RealDictCursor

    conn = get_connection()
    conn.autocommit = autocommit
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        yield cursor
        if not autocommit:
            conn.commit()
    except Exception as e:
        if not autocommit:
            conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def test_connection() -> bool:
    """Teste la connexion à la base de données."""
    try:
        with get_cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            return result[0] == 1
    except Exception as e:
        print(f"Erreur de connexion: {e}")
        return False


if __name__ == "__main__":
    if test_connection():
        print("✓ Connexion réussie à PostgreSQL")
    else:
        print("✗ Échec de connexion à PostgreSQL")
