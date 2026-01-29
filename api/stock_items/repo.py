from typing import Dict, Any, List, Optional
from uuid import uuid4

from api.settings import settings
from api.errors.exceptions import DatabaseError, NotFoundError


class StockItemRepository:
    """Requêtes pour le domaine stock_item"""

    def _get_connection(self):
        """Ouvre une connexion à la base de données via settings"""
        try:
            return settings.get_db_connection()
        except Exception as e:
            raise DatabaseError(
                f"Erreur de connexion base de données: {str(e)}") from e

    def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        family_code: Optional[str] = None,
        sub_family_code: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Récupère tous les articles en stock avec filtres optionnels"""
        limit = min(limit, 1000)

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            where_clauses = []
            params: List[Any] = []

            if family_code:
                where_clauses.append("family_code = %s")
                params.append(family_code)

            if sub_family_code:
                where_clauses.append("sub_family_code = %s")
                params.append(sub_family_code)

            if search:
                where_clauses.append("(name ILIKE %s OR ref ILIKE %s)")
                search_pattern = f"%{search}%"
                params.extend([search_pattern, search_pattern])

            where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

            query = f"""
                SELECT * FROM stock_item
                {where_sql}
                ORDER BY name ASC
                LIMIT %s OFFSET %s
            """

            cur.execute(query, (*params, limit, offset))
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]

            return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def get_by_id(self, item_id: str) -> Dict[str, Any]:
        """Récupère un article par ID"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM stock_item WHERE id = %s", (item_id,))
            row = cur.fetchone()

            if not row:
                raise NotFoundError(f"Article {item_id} non trouvé")

            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def get_by_ref(self, ref: str) -> Dict[str, Any]:
        """Récupère un article par référence"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM stock_item WHERE ref = %s", (ref,))
            row = cur.fetchone()

            if not row:
                raise NotFoundError(f"Article avec référence {ref} non trouvé")

            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def add(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée un nouvel article en stock"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            item_id = str(uuid4())

            # Note: ref est généré automatiquement par trigger
            cur.execute(
                """
                INSERT INTO stock_item
                (id, name, family_code, sub_family_code, spec, dimension,
                 quantity, unit, location, standars_spec, manufacturer_item_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    item_id,
                    data['name'],
                    data['family_code'],
                    data['sub_family_code'],
                    data.get('spec'),
                    data['dimension'],
                    data.get('quantity', 0),
                    data.get('unit'),
                    data.get('location'),
                    data.get('standars_spec'),
                    data.get('manufacturer_item_id')
                )
            )
            conn.commit()
            row = cur.fetchone()
            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la création de l'article: {str(e)}") from e
        finally:
            conn.close()

    def update(self, item_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour un article existant"""
        # Vérifie que l'article existe
        self.get_by_id(item_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Champs modifiables (ref est généré par trigger si family/sub_family/spec/dimension changent)
            updatable_fields = [
                'name', 'family_code', 'sub_family_code', 'spec', 'dimension',
                'quantity', 'unit', 'location', 'standars_spec', 'manufacturer_item_id'
            ]

            set_clauses = []
            params = []

            for field in updatable_fields:
                if field in data:
                    set_clauses.append(f"{field} = %s")
                    params.append(data[field])

            if not set_clauses:
                return self.get_by_id(item_id)

            params.append(item_id)

            query = f"""
                UPDATE stock_item
                SET {', '.join(set_clauses)}
                WHERE id = %s
                RETURNING *
            """

            cur.execute(query, params)
            conn.commit()
            row = cur.fetchone()
            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la mise à jour: {str(e)}") from e
        finally:
            conn.close()

    def delete(self, item_id: str) -> bool:
        """Supprime un article"""
        # Vérifie que l'article existe
        self.get_by_id(item_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM stock_item WHERE id = %s", (item_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la suppression: {str(e)}") from e
        finally:
            conn.close()

    def update_quantity(self, item_id: str, quantity: int) -> Dict[str, Any]:
        """Met à jour uniquement la quantité d'un article"""
        # Vérifie que l'article existe
        self.get_by_id(item_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE stock_item
                SET quantity = %s
                WHERE id = %s
                RETURNING *
                """,
                (quantity, item_id)
            )
            conn.commit()
            row = cur.fetchone()
            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la mise à jour de la quantité: {str(e)}") from e
        finally:
            conn.close()
