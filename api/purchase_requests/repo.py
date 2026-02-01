from typing import Dict, Any, List, Optional
from uuid import uuid4
from datetime import datetime
from decimal import Decimal

from api.settings import settings
from api.errors.exceptions import DatabaseError, NotFoundError


class PurchaseRequestRepository:
    """Requêtes pour le domaine purchase_request"""

    def _get_connection(self):
        """Ouvre une connexion à la base de données via settings"""
        try:
            return settings.get_db_connection()
        except Exception as e:
            raise DatabaseError(
                f"Erreur de connexion base de données: {str(e)}") from e

    def _enrich_with_stock_item(self, request_dict: Dict[str, Any], conn) -> Dict[str, Any]:
        """Enrichit une demande avec les détails du stock_item si présent"""
        stock_item_id = request_dict.get('stock_item_id')
        if stock_item_id:
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT id, name, ref, family_code, sub_family_code,
                           quantity, unit, location
                    FROM stock_item WHERE id = %s
                    """,
                    (str(stock_item_id),)
                )
                row = cur.fetchone()
                if row:
                    cols = [desc[0] for desc in cur.description]
                    request_dict['stock_item'] = dict(zip(cols, row))
                else:
                    request_dict['stock_item'] = None
            except Exception:
                request_dict['stock_item'] = None
        else:
            request_dict['stock_item'] = None
        return request_dict

    def _map_with_stock_item(self, row_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Mappe une row avec stock_item imbriqué depuis les colonnes JOIN"""
        if row_dict.get('si_id') is not None:
            row_dict['stock_item'] = {
                'id': row_dict['si_id'],
                'name': row_dict['si_name'],
                'ref': row_dict['si_ref'],
                'family_code': row_dict['si_family_code'],
                'sub_family_code': row_dict['si_sub_family_code'],
                'quantity': row_dict['si_quantity'],
                'unit': row_dict['si_unit'],
                'location': row_dict['si_location']
            }
        else:
            row_dict['stock_item'] = None

        # Nettoie les colonnes intermédiaires
        for key in ['si_id', 'si_name', 'si_ref', 'si_family_code',
                    'si_sub_family_code', 'si_quantity', 'si_unit', 'si_location']:
            row_dict.pop(key, None)

        return row_dict

    def _get_linked_order_lines(self, purchase_request_id: str, conn) -> List[Dict[str, Any]]:
        """Récupère les lignes de commande liées à une demande d'achat"""
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    solpr.id, solpr.supplier_order_line_id, solpr.quantity as quantity_allocated,
                    solpr.created_at,
                    sol.supplier_order_id, sol.stock_item_id, sol.quantity,
                    sol.unit_price, sol.total_price, sol.quantity_received, sol.is_selected,
                    sol.quote_received, sol.quote_price,
                    si.name as stock_item_name, si.ref as stock_item_ref,
                    so.status as supplier_order_status, so.order_number as supplier_order_number
                FROM supplier_order_line_purchase_request solpr
                JOIN supplier_order_line sol ON solpr.supplier_order_line_id = sol.id
                LEFT JOIN stock_item si ON sol.stock_item_id = si.id
                LEFT JOIN supplier_order so ON sol.supplier_order_id = so.id
                WHERE solpr.purchase_request_id = %s
                ORDER BY solpr.created_at ASC
                """,
                (purchase_request_id,)
            )
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            results = []
            for row in rows:
                line = dict(zip(cols, row))
                # Convertit Decimal en float
                for key in ['unit_price', 'total_price', 'quote_price']:
                    if line.get(key) is not None and isinstance(line[key], Decimal):
                        line[key] = float(line[key])
                results.append(line)
            return results
        except Exception:
            return []

    def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        intervention_id: Optional[str] = None,
        urgency: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Récupère toutes les demandes d'achat avec filtres optionnels"""
        limit = min(limit, 1000)

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            where_clauses = []
            params: List[Any] = []

            if status:
                where_clauses.append("pr.status = %s")
                params.append(status)

            if intervention_id:
                where_clauses.append("pr.intervention_id = %s")
                params.append(intervention_id)

            if urgency:
                where_clauses.append("pr.urgency = %s")
                params.append(urgency)

            where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

            query = f"""
                SELECT pr.*,
                       si.id as si_id, si.name as si_name, si.ref as si_ref,
                       si.family_code as si_family_code, si.sub_family_code as si_sub_family_code,
                       si.quantity as si_quantity, si.unit as si_unit, si.location as si_location
                FROM purchase_request pr
                LEFT JOIN stock_item si ON pr.stock_item_id = si.id
                {where_sql}
                ORDER BY pr.created_at DESC
                LIMIT %s OFFSET %s
            """

            cur.execute(query, (*params, limit, offset))
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]

            results = []
            for row in rows:
                pr = self._map_with_stock_item(dict(zip(cols, row)))
                pr['order_lines'] = self._get_linked_order_lines(str(pr['id']), conn)
                results.append(pr)
            return results
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def get_by_id(self, request_id: str) -> Dict[str, Any]:
        """Récupère une demande d'achat par ID avec stock_item"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT pr.*,
                       si.id as si_id, si.name as si_name, si.ref as si_ref,
                       si.family_code as si_family_code, si.sub_family_code as si_sub_family_code,
                       si.quantity as si_quantity, si.unit as si_unit, si.location as si_location
                FROM purchase_request pr
                LEFT JOIN stock_item si ON pr.stock_item_id = si.id
                WHERE pr.id = %s
                """,
                (request_id,)
            )
            row = cur.fetchone()

            if not row:
                raise NotFoundError(f"Demande d'achat {request_id} non trouvée")

            cols = [desc[0] for desc in cur.description]
            result = self._map_with_stock_item(dict(zip(cols, row)))
            result['order_lines'] = self._get_linked_order_lines(request_id, conn)
            return result
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def get_by_intervention(self, intervention_id: str) -> List[Dict[str, Any]]:
        """Récupère toutes les demandes d'achat liées à une intervention avec stock_item"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT pr.*,
                       si.id as si_id, si.name as si_name, si.ref as si_ref,
                       si.family_code as si_family_code, si.sub_family_code as si_sub_family_code,
                       si.quantity as si_quantity, si.unit as si_unit, si.location as si_location
                FROM purchase_request pr
                LEFT JOIN stock_item si ON pr.stock_item_id = si.id
                WHERE pr.intervention_id = %s
                ORDER BY pr.created_at DESC
                """,
                (intervention_id,)
            )
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]

            results = []
            for row in rows:
                pr = self._map_with_stock_item(dict(zip(cols, row)))
                pr['order_lines'] = self._get_linked_order_lines(str(pr['id']), conn)
                results.append(pr)
            return results
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def add(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une nouvelle demande d'achat"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            request_id = str(uuid4())
            now = datetime.now()

            cur.execute(
                """
                INSERT INTO purchase_request
                (id, status, stock_item_id, item_label, quantity, unit,
                 requested_by, urgency, reason, notes, workshop,
                 intervention_id, quantity_requested, urgent, requester_name,
                 created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    request_id,
                    data.get('status', 'open'),
                    data.get('stock_item_id'),
                    data['item_label'],
                    data['quantity'],
                    data.get('unit'),
                    data.get('requested_by'),
                    data.get('urgency', 'normal'),
                    data.get('reason'),
                    data.get('notes'),
                    data.get('workshop'),
                    data.get('intervention_id'),
                    data.get('quantity_requested'),
                    data.get('urgent', False),
                    data.get('requester_name'),
                    now,
                    now
                )
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la création de la demande d'achat: {str(e)}") from e
        finally:
            conn.close()

        # Retourne avec stock_item enrichi
        return self.get_by_id(request_id)

    def update(self, request_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour une demande d'achat existante"""
        # Vérifie que la demande existe
        self.get_by_id(request_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            now = datetime.now()

            # Champs modifiables
            updatable_fields = [
                'status', 'stock_item_id', 'item_label', 'quantity', 'unit',
                'requested_by', 'urgency', 'reason', 'notes', 'workshop',
                'intervention_id', 'quantity_requested', 'quantity_approved',
                'urgent', 'requester_name', 'approver_name', 'approved_at'
            ]

            set_clauses = []
            params = []

            for field in updatable_fields:
                if field in data:
                    set_clauses.append(f"{field} = %s")
                    params.append(data[field])

            if not set_clauses:
                return self.get_by_id(request_id)

            set_clauses.append("updated_at = %s")
            params.append(now)
            params.append(request_id)

            query = f"""
                UPDATE purchase_request
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

        # Retourne avec stock_item enrichi
        return self.get_by_id(request_id)

    def delete(self, request_id: str) -> bool:
        """Supprime une demande d'achat"""
        # Vérifie que la demande existe
        self.get_by_id(request_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM purchase_request WHERE id = %s", (request_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la suppression: {str(e)}") from e
        finally:
            conn.close()
