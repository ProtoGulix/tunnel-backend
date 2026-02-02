from typing import Dict, Any, List, Optional, Literal
from uuid import uuid4
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

from api.settings import settings
from api.errors.exceptions import DatabaseError, NotFoundError

logger = logging.getLogger(__name__)


# Mapping statuts dérivés
DERIVED_STATUS_CONFIG = {
    'OPEN': {'label': 'En attente', 'color': '#6B7280'},
    'QUOTED': {'label': 'Devis reçu', 'color': '#FFA500'},
    'ORDERED': {'label': 'Commandé', 'color': '#3B82F6'},
    'PARTIAL': {'label': 'Partiellement reçu', 'color': '#8B5CF6'},
    'RECEIVED': {'label': 'Reçu', 'color': '#10B981'},
    'REJECTED': {'label': 'Refusé', 'color': '#EF4444'}
}


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

            where_sql = ("WHERE " + " AND ".join(where_clauses)
                         ) if where_clauses else ""

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
                pr['order_lines'] = self._get_linked_order_lines(
                    str(pr['id']), conn)
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
                raise NotFoundError(
                    f"Demande d'achat {request_id} non trouvée")

            cols = [desc[0] for desc in cur.description]
            result = self._map_with_stock_item(dict(zip(cols, row)))
            result['order_lines'] = self._get_linked_order_lines(
                request_id, conn)
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
                pr['order_lines'] = self._get_linked_order_lines(
                    str(pr['id']), conn)
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

    # ========== Méthodes optimisées v1.2.0 ==========

    def _map_derived_status(self, status_code: str) -> Dict[str, Any]:
        """Mappe un code statut vers objet DerivedStatus"""
        config = DERIVED_STATUS_CONFIG.get(
            status_code, DERIVED_STATUS_CONFIG['OPEN'])
        return {
            'code': status_code,
            'label': config['label'],
            'color': config['color']
        }

    def _derive_status_from_order_lines(self, order_lines: List[Dict]) -> str:
        """Calcule le statut dérivé basé sur les order_lines"""
        if not order_lines:
            return 'OPEN'

        has_quotes = any(line.get('quote_received') for line in order_lines)
        has_selected = any(line.get('is_selected') for line in order_lines)
        total_qty = sum(line.get('quantity_allocated', 0) for line in order_lines)
        received_qty = sum(line.get('quantity_received', 0) or 0 for line in order_lines)

        if received_qty >= total_qty and total_qty > 0:
            return 'RECEIVED'
        if received_qty > 0:
            return 'PARTIAL'
        if has_selected:
            return 'ORDERED'
        if has_quotes:
            return 'QUOTED'
        return 'OPEN'

    def get_list(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        intervention_id: Optional[str] = None,
        urgency: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Liste optimisée avec statut dérivé et compteurs agrégés.
        Retourne PurchaseRequestListItem.
        """
        limit = min(limit, 1000)
        logger.debug(
            "Fetching purchase request list: limit=%s, offset=%s", limit, offset)

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            where_clauses = ["1=1"]
            params: List[Any] = []

            if intervention_id:
                where_clauses.append("pr.intervention_id = %s")
                params.append(intervention_id)

            if urgency:
                where_clauses.append("pr.urgency = %s")
                params.append(urgency)

            where_sql = " AND ".join(where_clauses)

            query = f"""
                SELECT
                    pr.id,
                    pr.item_label,
                    pr.quantity,
                    pr.unit,

                    -- Infos directes (pas d'objets imbriqués)
                    si.ref AS stock_item_ref,
                    si.name AS stock_item_name,
                    i.code AS intervention_code,
                    pr.requester_name,
                    pr.urgency,
                    pr.urgent,

                    -- Compteurs agrégés
                    COALESCE(agg.quotes_count, 0) AS quotes_count,
                    COALESCE(agg.selected_count, 0) AS selected_count,
                    COALESCE(agg.suppliers_count, 0) AS suppliers_count,
                    COALESCE(agg.total_allocated, 0) AS total_allocated,
                    COALESCE(agg.total_received, 0) AS total_received,

                    pr.created_at,
                    pr.updated_at

                FROM purchase_request pr
                LEFT JOIN stock_item si ON pr.stock_item_id = si.id
                LEFT JOIN intervention i ON pr.intervention_id = i.id
                LEFT JOIN LATERAL (
                    SELECT
                        COUNT(DISTINCT CASE WHEN sol.quote_received THEN sol.id END) AS quotes_count,
                        COUNT(DISTINCT CASE WHEN sol.is_selected THEN sol.id END) AS selected_count,
                        COUNT(DISTINCT so.supplier_id) AS suppliers_count,
                        SUM(solpr.quantity) AS total_allocated,
                        SUM(COALESCE(sol.quantity_received, 0)) AS total_received
                    FROM supplier_order_line_purchase_request solpr
                    JOIN supplier_order_line sol ON solpr.supplier_order_line_id = sol.id
                    JOIN supplier_order so ON sol.supplier_order_id = so.id
                    WHERE solpr.purchase_request_id = pr.id
                ) agg ON TRUE

                WHERE {where_sql}

                ORDER BY pr.created_at DESC
                LIMIT %s OFFSET %s
            """

            params.extend([limit, offset])
            cur.execute(query, params)
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]

            results = []
            for row in rows:
                item = dict(zip(cols, row))

                # Calcule le statut dérivé
                quotes_count = item.get('quotes_count', 0)
                selected_count = item.get('selected_count', 0)
                total_allocated = item.pop('total_allocated', 0)
                total_received = item.pop('total_received', 0)

                if total_received >= total_allocated and total_allocated > 0:
                    status_code = 'RECEIVED'
                elif total_received > 0:
                    status_code = 'PARTIAL'
                elif selected_count > 0:
                    status_code = 'ORDERED'
                elif quotes_count > 0:
                    status_code = 'QUOTED'
                else:
                    status_code = 'OPEN'

                # Filtre par statut si demandé
                if status and status_code != status:
                    continue

                item['derived_status'] = self._map_derived_status(status_code)
                results.append(item)

            logger.info("Fetched %d purchase requests (list view)", len(results))
            return results
        except Exception as e:
            logger.error("Error fetching purchase request list: %s", str(e))
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def get_detail(self, request_id: str) -> Dict[str, Any]:
        """
        Détail complet avec contexte enrichi.
        Retourne PurchaseRequestDetail avec intervention, stock_item, order_lines enrichis.
        """
        logger.debug("Fetching purchase request detail: %s", request_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Récupère la demande avec stock_item et intervention
            cur.execute(
                """
                SELECT
                    pr.*,
                    -- Stock item
                    si.id as si_id, si.name as si_name, si.ref as si_ref,
                    si.family_code as si_family_code, si.sub_family_code as si_sub_family_code,
                    si.quantity as si_quantity, si.unit as si_unit, si.location as si_location,
                    (SELECT COUNT(*) FROM stock_item_supplier WHERE stock_item_id = si.id) as si_supplier_refs_count,
                    -- Intervention
                    i.id as i_id, i.code as i_code, i.title as i_title,
                    i.priority as i_priority, i.status_actual as i_status_actual,
                    -- Équipement
                    e.id as e_id, e.code as e_code, e.name as e_name
                FROM purchase_request pr
                LEFT JOIN stock_item si ON pr.stock_item_id = si.id
                LEFT JOIN intervention i ON pr.intervention_id = i.id
                LEFT JOIN equipement e ON i.equipement_id = e.id
                WHERE pr.id = %s
                """,
                (request_id,)
            )
            row = cur.fetchone()

            if not row:
                raise NotFoundError(f"Demande d'achat {request_id} non trouvée")

            cols = [desc[0] for desc in cur.description]
            data = dict(zip(cols, row))

            # Construit stock_item
            if data.get('si_id'):
                data['stock_item'] = {
                    'id': data['si_id'],
                    'name': data['si_name'],
                    'ref': data['si_ref'],
                    'family_code': data['si_family_code'],
                    'sub_family_code': data['si_sub_family_code'],
                    'quantity': data['si_quantity'],
                    'unit': data['si_unit'],
                    'location': data['si_location'],
                    'supplier_refs_count': data['si_supplier_refs_count']
                }
            else:
                data['stock_item'] = None

            # Construit intervention avec équipement
            if data.get('i_id'):
                equipement = None
                if data.get('e_id'):
                    equipement = {
                        'id': data['e_id'],
                        'code': data['e_code'],
                        'name': data['e_name']
                    }
                data['intervention'] = {
                    'id': data['i_id'],
                    'code': data['i_code'],
                    'title': data['i_title'],
                    'priority': data['i_priority'],
                    'status_actual': data['i_status_actual'],
                    'equipement': equipement
                }
            else:
                data['intervention'] = None

            # Nettoie les colonnes intermédiaires
            for key in list(data.keys()):
                if key.startswith('si_') or key.startswith('i_') or key.startswith('e_'):
                    del data[key]

            # Récupère order_lines enrichis avec fournisseur
            order_lines = self._get_linked_order_lines_detail(request_id, conn)
            data['order_lines'] = order_lines

            # Calcule le statut dérivé
            status_code = self._derive_status_from_order_lines(order_lines)
            data['derived_status'] = self._map_derived_status(status_code)

            logger.info("Fetched purchase request detail: %s", request_id)
            return data

        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Error fetching purchase request detail: %s", str(e))
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def _get_linked_order_lines_detail(self, purchase_request_id: str, conn) -> List[Dict[str, Any]]:
        """Récupère les order_lines enrichis avec fournisseur pour le détail"""
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    solpr.id, solpr.supplier_order_line_id, solpr.quantity as quantity_allocated,
                    solpr.created_at,
                    sol.supplier_order_id, sol.unit_price, sol.total_price,
                    sol.quantity_received, sol.is_selected,
                    sol.quote_received, sol.quote_price, sol.quote_received_at,
                    sol.manufacturer, sol.manufacturer_ref, sol.lead_time_days, sol.notes,
                    so.status as supplier_order_status, so.order_number as supplier_order_number,
                    -- Fournisseur enrichi
                    s.id as supplier_id, s.name as supplier_name, s.code as supplier_code,
                    s.contact_name as supplier_contact_name, s.email as supplier_email, s.phone as supplier_phone
                FROM supplier_order_line_purchase_request solpr
                JOIN supplier_order_line sol ON solpr.supplier_order_line_id = sol.id
                JOIN supplier_order so ON sol.supplier_order_id = so.id
                LEFT JOIN supplier s ON so.supplier_id = s.id
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

                # Construit objet supplier
                if line.get('supplier_id'):
                    line['supplier'] = {
                        'id': line['supplier_id'],
                        'name': line['supplier_name'],
                        'code': line['supplier_code'],
                        'contact_name': line['supplier_contact_name'],
                        'email': line['supplier_email'],
                        'phone': line['supplier_phone']
                    }
                else:
                    line['supplier'] = None

                # Nettoie colonnes supplier_*
                for key in list(line.keys()):
                    if key.startswith('supplier_') and key != 'supplier_order_id' and key != 'supplier_order_line_id' and key != 'supplier_order_status' and key != 'supplier_order_number':
                        del line[key]

                results.append(line)
            return results
        except Exception:
            return []

    def get_by_intervention_optimized(
        self,
        intervention_id: str,
        view: Literal['list', 'full'] = 'list'
    ) -> List[Dict[str, Any]]:
        """
        Filtre par intervention avec choix de granularité.
        view=list : retourne liste légère
        view=full : retourne détail complet
        """
        logger.debug("Fetching purchase requests for intervention %s (view=%s)",
                    intervention_id, view)

        if view == 'full':
            # Récupère les IDs puis appelle get_detail pour chacun
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                cur.execute(
                    "SELECT id FROM purchase_request WHERE intervention_id = %s ORDER BY created_at DESC",
                    (intervention_id,)
                )
                rows = cur.fetchall()
            finally:
                conn.close()

            results = []
            for row in rows:
                try:
                    detail = self.get_detail(str(row[0]))
                    results.append(detail)
                except Exception:
                    continue
            return results
        else:
            # Vue liste optimisée
            return self.get_list(
                limit=1000,
                offset=0,
                intervention_id=intervention_id
            )

    def get_stats(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        group_by: str = "status"
    ) -> Dict[str, Any]:
        """
        Statistiques agrégées pour dashboards.
        """
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=90)

        logger.debug("Fetching stats from %s to %s", start_date, end_date)

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Compteurs totaux
            cur.execute(
                """
                SELECT
                    COUNT(*) as total_requests,
                    COUNT(CASE WHEN urgency = 'critical' OR urgent = true THEN 1 END) as urgent_count
                FROM purchase_request
                WHERE created_at >= %s AND created_at <= %s
                """,
                (start_date, end_date)
            )
            row = cur.fetchone()
            totals = {
                'total_requests': row[0] if row else 0,
                'urgent_count': row[1] if row else 0
            }

            # Par urgence
            cur.execute(
                """
                SELECT
                    COALESCE(urgency, 'normal') as urgency,
                    COUNT(*) as count
                FROM purchase_request
                WHERE created_at >= %s AND created_at <= %s
                GROUP BY urgency
                ORDER BY count DESC
                """,
                (start_date, end_date)
            )
            by_urgency = [{'urgency': row[0], 'count': row[1]} for row in cur.fetchall()]

            # Top articles demandés
            cur.execute(
                """
                SELECT
                    pr.item_label,
                    si.ref as stock_item_ref,
                    COUNT(*) as request_count,
                    SUM(pr.quantity) as total_quantity
                FROM purchase_request pr
                LEFT JOIN stock_item si ON pr.stock_item_id = si.id
                WHERE pr.created_at >= %s AND pr.created_at <= %s
                GROUP BY pr.item_label, si.ref
                ORDER BY request_count DESC
                LIMIT 10
                """,
                (start_date, end_date)
            )
            top_items = [
                {
                    'item_label': row[0],
                    'stock_item_ref': row[1],
                    'request_count': row[2],
                    'total_quantity': row[3]
                }
                for row in cur.fetchall()
            ]

            # Calcul par statut dérivé (en Python car pas de fonction SQL)
            all_requests = self.get_list(limit=1000, offset=0)
            by_status = {}
            for req in all_requests:
                req_date = req.get('created_at')
                if req_date:
                    if isinstance(req_date, datetime):
                        req_date = req_date.date()
                    if start_date <= req_date <= end_date:
                        status_code = req['derived_status']['code']
                        by_status[status_code] = by_status.get(status_code, 0) + 1

            by_status_list = [
                {'status': code, 'count': count, **DERIVED_STATUS_CONFIG.get(code, {})}
                for code, count in by_status.items()
            ]

            return {
                'period': {
                    'start_date': str(start_date),
                    'end_date': str(end_date)
                },
                'totals': totals,
                'by_status': by_status_list,
                'by_urgency': by_urgency,
                'top_items': top_items
            }

        except Exception as e:
            logger.error("Error fetching stats: %s", str(e))
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()
