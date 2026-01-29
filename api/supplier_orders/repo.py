from typing import Dict, Any, List, Optional
from uuid import uuid4
from datetime import datetime
from decimal import Decimal

from api.settings import settings
from api.errors.exceptions import DatabaseError, NotFoundError


class SupplierOrderRepository:
    """Requêtes pour le domaine supplier_order"""

    def _get_connection(self):
        """Ouvre une connexion à la base de données via settings"""
        try:
            return settings.get_db_connection()
        except Exception as e:
            raise DatabaseError(
                f"Erreur de connexion base de données: {str(e)}") from e

    def _convert_decimals(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convertit les Decimal en float pour la sérialisation JSON"""
        for key, value in data.items():
            if isinstance(value, Decimal):
                data[key] = float(value)
        return data

    def _get_order_lines(self, order_id: str, conn) -> List[Dict[str, Any]]:
        """Récupère les lignes d'une commande"""
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    sol.id, sol.supplier_order_id, sol.stock_item_id,
                    sol.quantity, sol.unit_price, sol.total_price,
                    sol.quantity_received, sol.is_selected,
                    si.name as stock_item_name, si.ref as stock_item_ref,
                    (SELECT COUNT(*) FROM supplier_order_line_purchase_request
                     WHERE supplier_order_line_id = sol.id) as purchase_request_count
                FROM supplier_order_line sol
                LEFT JOIN stock_item si ON sol.stock_item_id = si.id
                WHERE sol.supplier_order_id = %s
                ORDER BY sol.created_at ASC
                """,
                (order_id,)
            )
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            return [self._convert_decimals(dict(zip(cols, row))) for row in rows]
        except Exception:
            return []

    def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        supplier_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Récupère toutes les commandes avec filtres optionnels"""
        limit = min(limit, 1000)

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            where_clauses = []
            params: List[Any] = []

            if status:
                where_clauses.append("so.status = %s")
                params.append(status)

            if supplier_id:
                where_clauses.append("so.supplier_id = %s")
                params.append(supplier_id)

            where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

            query = f"""
                SELECT
                    so.id, so.order_number, so.supplier_id, so.status,
                    so.total_amount, so.ordered_at, so.expected_delivery_date,
                    (SELECT COUNT(*) FROM supplier_order_line WHERE supplier_order_id = so.id) as line_count
                FROM supplier_order so
                {where_sql}
                ORDER BY so.created_at DESC
                LIMIT %s OFFSET %s
            """

            cur.execute(query, (*params, limit, offset))
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]

            return [self._convert_decimals(dict(zip(cols, row))) for row in rows]
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def get_by_id(self, order_id: str) -> Dict[str, Any]:
        """Récupère une commande par ID avec ses lignes"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM supplier_order WHERE id = %s",
                (order_id,)
            )
            row = cur.fetchone()

            if not row:
                raise NotFoundError(f"Commande {order_id} non trouvée")

            cols = [desc[0] for desc in cur.description]
            result = self._convert_decimals(dict(zip(cols, row)))
            result['lines'] = self._get_order_lines(order_id, conn)

            return result
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def get_by_order_number(self, order_number: str) -> Dict[str, Any]:
        """Récupère une commande par numéro"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM supplier_order WHERE order_number = %s",
                (order_number,)
            )
            row = cur.fetchone()

            if not row:
                raise NotFoundError(f"Commande {order_number} non trouvée")

            cols = [desc[0] for desc in cur.description]
            result = self._convert_decimals(dict(zip(cols, row)))
            result['lines'] = self._get_order_lines(str(result['id']), conn)

            return result
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def add(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une nouvelle commande fournisseur"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            order_id = str(uuid4())

            # Note: order_number est généré automatiquement par trigger
            cur.execute(
                """
                INSERT INTO supplier_order
                (id, supplier_id, status, ordered_at, expected_delivery_date, notes, currency)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    order_id,
                    data['supplier_id'],
                    data.get('status', 'OPEN'),
                    data.get('ordered_at'),
                    data.get('expected_delivery_date'),
                    data.get('notes'),
                    data.get('currency')
                )
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la création de la commande: {str(e)}") from e
        finally:
            conn.close()

        return self.get_by_id(order_id)

    def update(self, order_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour une commande existante"""
        # Vérifie que la commande existe
        self.get_by_id(order_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Champs modifiables (order_number est généré, non modifiable)
            updatable_fields = [
                'supplier_id', 'status', 'ordered_at', 'expected_delivery_date',
                'received_at', 'notes', 'currency'
            ]

            set_clauses = []
            params = []

            for field in updatable_fields:
                if field in data:
                    set_clauses.append(f"{field} = %s")
                    params.append(data[field])

            if not set_clauses:
                return self.get_by_id(order_id)

            params.append(order_id)

            query = f"""
                UPDATE supplier_order
                SET {', '.join(set_clauses)}
                WHERE id = %s
            """

            cur.execute(query, params)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la mise à jour: {str(e)}") from e
        finally:
            conn.close()

        return self.get_by_id(order_id)

    def delete(self, order_id: str) -> bool:
        """Supprime une commande (cascade sur les lignes)"""
        # Vérifie que la commande existe
        self.get_by_id(order_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM supplier_order WHERE id = %s", (order_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la suppression: {str(e)}") from e
        finally:
            conn.close()
