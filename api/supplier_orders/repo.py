from typing import Dict, Any, List, Optional
from uuid import uuid4
from datetime import datetime, timezone
from decimal import Decimal
import logging

from api.settings import settings
from api.errors.exceptions import DatabaseError, NotFoundError

logger = logging.getLogger(__name__)


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

    def _map_supplier(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mappe les colonnes supplier en objet imbriqué"""
        if data.get('s_id'):
            data['supplier'] = {
                'id': data['s_id'],
                'name': data['s_name'],
                'code': data['s_code'],
                'contact_name': data['s_contact_name'],
                'email': data['s_email'],
                'phone': data['s_phone']
            }
        else:
            data['supplier'] = None

        # Nettoie les colonnes intermédiaires
        for key in ['s_id', 's_name', 's_code', 's_contact_name', 's_email', 's_phone']:
            data.pop(key, None)

        return data

    def _compute_age_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcule age_days, age_color et is_blocking"""
        created_at = data.get('created_at')
        status = data.get('status', 'OPEN')

        # Calcul de l'âge en jours
        if created_at and isinstance(created_at, datetime):
            # Gère les datetimes avec ou sans timezone
            now = datetime.now(timezone.utc)
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            age_days = (now - created_at).days
        else:
            age_days = 0

        data['age_days'] = age_days

        # Couleur basée sur l'âge (seuils: 7 jours orange, 14 jours rouge)
        if age_days >= 14:
            data['age_color'] = 'red'
        elif age_days >= 7:
            data['age_color'] = 'orange'
        else:
            data['age_color'] = 'gray'

        # Commande bloquante si en attente depuis trop longtemps
        blocking_statuses = ['OPEN', 'SENT', 'ACK']
        data['is_blocking'] = status in blocking_statuses and age_days >= 7

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

            where_sql = ("WHERE " + " AND ".join(where_clauses)
                         ) if where_clauses else ""

            query = f"""
                SELECT
                    so.id, so.order_number, so.supplier_id, so.status,
                    so.total_amount, so.ordered_at, so.expected_delivery_date,
                    so.created_at, so.updated_at,
                    (SELECT COUNT(*) FROM supplier_order_line WHERE supplier_order_id = so.id) as line_count,
                    -- Supplier info
                    s.id as s_id, s.name as s_name, s.code as s_code,
                    s.contact_name as s_contact_name, s.email as s_email, s.phone as s_phone
                FROM supplier_order so
                LEFT JOIN supplier s ON so.supplier_id = s.id
                {where_sql}
                ORDER BY so.created_at DESC
                LIMIT %s OFFSET %s
            """

            cur.execute(query, (*params, limit, offset))
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]

            results = []
            for row in rows:
                order = self._convert_decimals(dict(zip(cols, row)))
                order = self._map_supplier(order)
                order = self._compute_age_fields(order)
                results.append(order)
            return results
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def get_by_id(self, order_id: str) -> Dict[str, Any]:
        """Récupère une commande par ID avec ses lignes et fournisseur"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT so.*,
                       s.id as s_id, s.name as s_name, s.code as s_code,
                       s.contact_name as s_contact_name, s.email as s_email, s.phone as s_phone
                FROM supplier_order so
                LEFT JOIN supplier s ON so.supplier_id = s.id
                WHERE so.id = %s
                """,
                (order_id,)
            )
            row = cur.fetchone()

            if not row:
                raise NotFoundError(f"Commande {order_id} non trouvée")

            cols = [desc[0] for desc in cur.description]
            result = self._convert_decimals(dict(zip(cols, row)))
            result = self._map_supplier(result)
            result = self._compute_age_fields(result)
            result['lines'] = self._get_order_lines(order_id, conn)
            result['line_count'] = len(result['lines'])

            return result
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def get_by_order_number(self, order_number: str) -> Dict[str, Any]:
        """Récupère une commande par numéro avec fournisseur"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT so.*,
                       s.id as s_id, s.name as s_name, s.code as s_code,
                       s.contact_name as s_contact_name, s.email as s_email, s.phone as s_phone
                FROM supplier_order so
                LEFT JOIN supplier s ON so.supplier_id = s.id
                WHERE so.order_number = %s
                """,
                (order_number,)
            )
            row = cur.fetchone()

            if not row:
                raise NotFoundError(f"Commande {order_number} non trouvée")

            cols = [desc[0] for desc in cur.description]
            result = self._convert_decimals(dict(zip(cols, row)))
            result = self._map_supplier(result)
            result = self._compute_age_fields(result)
            result['lines'] = self._get_order_lines(str(result['id']), conn)
            result['line_count'] = len(result['lines'])

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

    def _get_export_lines(self, order_id: str, conn) -> List[Dict[str, Any]]:
        """Récupère les lignes enrichies pour l'export"""
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    sol.id, sol.supplier_order_id, sol.stock_item_id,
                    sol.quantity, sol.unit_price, sol.total_price,
                    sol.quantity_received, sol.is_selected,
                    sol.manufacturer, sol.manufacturer_ref,
                    -- Stock item details
                    si.id as si_id, si.name as si_name, si.ref as si_ref,
                    si.family_code, si.sub_family_code, si.spec as si_spec,
                    si.dimension, si.unit as si_unit,
                    si.standars_spec as si_standard_spec_id
                FROM supplier_order_line sol
                LEFT JOIN stock_item si ON sol.stock_item_id = si.id
                WHERE sol.supplier_order_id = %s
                ORDER BY sol.created_at ASC
                """,
                (order_id,)
            )
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]

            results = []
            for row in rows:
                line = self._convert_decimals(dict(zip(cols, row)))

                # Map stock_item as nested object
                if line.get('si_id'):
                    line['stock_item'] = {
                        'id': line['si_id'],
                        'name': line['si_name'],
                        'ref': line['si_ref'],
                        'family_code': line['family_code'],
                        'sub_family_code': line['sub_family_code'],
                        'spec': line['si_spec'],
                        'dimension': line['dimension'],
                        'unit': line['si_unit']
                    }
                else:
                    line['stock_item'] = None

                # Get linked purchase_requests
                line['purchase_requests'] = self._get_line_purchase_requests(
                    str(line['id']), conn
                )

                # Clean up intermediate columns
                for key in ['si_id', 'si_name', 'si_ref', 'family_code', 'sub_family_code',
                            'si_spec', 'dimension', 'si_unit', 'si_standard_spec_id']:
                    line.pop(key, None)

                results.append(line)

            return results
        except Exception as e:
            logger.error(
                "Erreur dans _get_export_lines pour order_id=%s: %s", order_id, str(e))
            return []

    def _get_line_purchase_requests(self, line_id: str, conn) -> List[Dict[str, Any]]:
        """Récupère les demandes d'achat liées à une ligne pour l'export"""
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    pr.id, pr.item_label, pr.requester_name,
                    pr.intervention_id, pr.urgency_level,
                    solpr.quantity_fulfilled as allocated_quantity
                FROM supplier_order_line_purchase_request solpr
                JOIN purchase_request pr ON solpr.purchase_request_id = pr.id
                WHERE solpr.supplier_order_line_id = %s
                ORDER BY solpr.created_at ASC
                """,
                (line_id,)
            )
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        except Exception:
            return []

    def get_export_data(self, order_id: str) -> Dict[str, Any]:
        """Récupère les données complètes pour l'export (CSV/Email)"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT so.id, so.order_number, so.supplier_id, so.status,
                       so.total_amount, so.ordered_at, so.expected_delivery_date,
                       so.notes, so.currency, so.created_at,
                       s.id as s_id, s.name as s_name, s.code as s_code,
                       s.contact_name as s_contact_name, s.email as s_email, s.phone as s_phone
                FROM supplier_order so
                LEFT JOIN supplier s ON so.supplier_id = s.id
                WHERE so.id = %s
                """,
                (order_id,)
            )
            row = cur.fetchone()

            if not row:
                raise NotFoundError(f"Commande {order_id} non trouvée")

            cols = [desc[0] for desc in cur.description]
            result = self._convert_decimals(dict(zip(cols, row)))
            result = self._map_supplier(result)
            result['lines'] = self._get_export_lines(order_id, conn)

            return result
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()
