from typing import Optional

from api.db import get_connection, release_connection
from api.errors.exceptions import raise_db_error


def _version_tuple(version: str) -> tuple:
    return tuple(int(p) for p in version.split("."))


class ChangelogRepository:
    """Accès à la position de lecture du changelog de l'utilisateur (tunnel_user)."""

    def get_last_seen_version(self, user_id: str) -> Optional[str]:
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT last_seen_changelog_version FROM tunnel_user WHERE id = %s::uuid",
                    (user_id,),
                )
                row = cur.fetchone()
            return row[0] if row else None
        except Exception as e:
            raise_db_error(e, "lecture dernière version du changelog vue")
        finally:
            if conn:
                release_connection(conn)

    def mark_seen(self, user_id: str, version: str) -> None:
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE tunnel_user
                    SET last_seen_changelog_version = %s, updated_at = now()
                    WHERE id = %s::uuid
                    """,
                    (version, user_id),
                )
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise_db_error(e, "mise à jour dernière version du changelog vue")
        finally:
            if conn:
                release_connection(conn)


def entries_since(entries: list, last_seen_version: Optional[str]) -> list:
    """Filtre les entrées de changelog postérieures à `last_seen_version`.

    Si `last_seen_version` est None (utilisateur jamais vu) ou ne se parse pas
    en triplet numérique, retourne toutes les entrées disponibles (bornées en
    amont par MAX_VERSIONS côté parser).
    """
    if last_seen_version is None:
        return entries

    try:
        last_seen_tuple = _version_tuple(last_seen_version)
    except ValueError:
        return entries

    result = []
    for entry in entries:
        try:
            if _version_tuple(entry.version) > last_seen_tuple:
                result.append(entry)
        except ValueError:
            continue
    return result
