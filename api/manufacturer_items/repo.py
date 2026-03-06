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

    def get_all(self, limit: int = 100, offset: int = 0, search: str = None) -> List[Dict[str, Any]]:
        """Liste les références fabricants avec recherche optionnelle"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            params = []
            where = ""
            if search:
                where = "WHERE manufacturer_name ILIKE %s OR manufacturer_ref ILIKE %s"
                params = [f"%{search}%", f"%{search}%"]
            params += [limit, offset]
            cur.execute(
                f"""
                SELECT id, manufacturer_name, manufacturer_ref
                FROM manufacturer_item
                {where}
                ORDER BY manufacturer_name ASC
                LIMIT %s OFFSET %s
                """,
                params
            )
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def count_all(self, search: str = None) -> int:
        """Compte les références fabricants avec filtre optionnel"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            if search:
                cur.execute(
                    "SELECT COUNT(*) FROM manufacturer_item WHERE manufacturer_name ILIKE %s OR manufacturer_ref ILIKE %s",
                    (f"%{search}%", f"%{search}%")
                )
            else:
                cur.execute("SELECT COUNT(*) FROM manufacturer_item")
            return cur.fetchone()[0]
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

    def get_by_id_with_suppliers(self, item_id: str) -> Dict[str, Any]:
        """Récupère une référence fabricant avec ses références fournisseurs liées"""
        item = self.get_by_id(item_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    sis.id, sis.supplier_ref, sis.unit_price,
                    sis.min_order_quantity, sis.delivery_time_days, sis.is_preferred,
                    si.name as stock_item_name, si.ref as stock_item_ref,
                    s.name as supplier_name, s.code as supplier_code
                FROM stock_item_supplier sis
                LEFT JOIN stock_item si ON sis.stock_item_id = si.id
                LEFT JOIN supplier s ON sis.supplier_id = s.id
                WHERE sis.manufacturer_item_id = %s
                ORDER BY s.name ASC, sis.supplier_ref ASC
                """,
                (item_id,)
            )
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            item['supplier_items'] = [dict(zip(cols, row)) for row in rows]
            return item
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
