import logging
from typing import Dict, Any, List
from uuid import uuid4

from api.settings import settings
from api.errors.exceptions import DatabaseError, NotFoundError

logger = logging.getLogger(__name__)


class ManufacturerItemRepository:
    """Requêtes pour le domaine manufacturer_item"""

    def _get_connection(self):
        try:
            return settings.get_db_connection()
        except Exception as e:
            raise DatabaseError(
                f"Erreur de connexion base de données: {str(e)}") from e

    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Liste toutes les références fabricants"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, manufacturer_name, manufacturer_ref
                FROM manufacturer_item
                ORDER BY manufacturer_name ASC
                LIMIT %s OFFSET %s
                """,
                (limit, offset)
            )
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def get_by_id(self, item_id: str) -> Dict[str, Any]:
        """Récupère une référence fabricant par ID"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, manufacturer_name, manufacturer_ref FROM manufacturer_item WHERE id = %s",
                (item_id,)
            )
            row = cur.fetchone()
            if not row:
                raise NotFoundError(
                    f"Référence fabricant {item_id} non trouvée")
            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def add(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une nouvelle référence fabricant"""
        manufacturer_name = (data.get('manufacturer_name') or '').strip()
        if not manufacturer_name:
            raise ValueError("manufacturer_name est obligatoire")

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            item_id = str(uuid4())
            cur.execute(
                """
                INSERT INTO manufacturer_item (id, manufacturer_name, manufacturer_ref)
                VALUES (%s, %s, %s)
                """,
                (item_id, manufacturer_name, data.get('manufacturer_ref'))
            )
            conn.commit()
            logger.info("Référence fabricant créée: %s", item_id)
        except Exception as e:
            conn.rollback()
            raise DatabaseError(f"Erreur lors de la création: {str(e)}") from e
        finally:
            conn.close()

        return self.get_by_id(item_id)

    def update(self, item_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour partiellement une référence fabricant"""
        self.get_by_id(item_id)

        updatable = ['manufacturer_name', 'manufacturer_ref']
        updates = {k: v for k, v in data.items() if k in updatable}

        if not updates:
            return self.get_by_id(item_id)

        if 'manufacturer_name' in updates:
            updates['manufacturer_name'] = (
                updates['manufacturer_name'] or '').strip()
            if not updates['manufacturer_name']:
                raise ValueError("manufacturer_name ne peut pas être vide")

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            set_clauses = [f"{k} = %s" for k in updates]
            params = list(updates.values()) + [item_id]
            cur.execute(
                f"UPDATE manufacturer_item SET {', '.join(set_clauses)} WHERE id = %s",
                params
            )
            conn.commit()
            logger.info("Référence fabricant %s mise à jour", item_id)
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la mise à jour: {str(e)}") from e
        finally:
            conn.close()

        return self.get_by_id(item_id)

    def delete(self, item_id: str) -> None:
        """Supprime une référence fabricant"""
        self.get_by_id(item_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM manufacturer_item WHERE id = %s", (item_id,))
            conn.commit()
            logger.info("Référence fabricant %s supprimée", item_id)
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la suppression: {str(e)}") from e
        finally:
            conn.close()
