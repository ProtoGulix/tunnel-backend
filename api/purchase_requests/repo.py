from fastapi import HTTPException
from typing import Dict, Any, List, Optional, Literal
from uuid import uuid4
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

from api.db import get_connection, release_connection
from api.errors.exceptions import DatabaseError, raise_db_error, NotFoundError, ValidationError
from api.constants import DERIVED_STATUS_CONFIG, CLOSED_STATUS_CODE

logger = logging.getLogger(__name__)


class PurchaseRequestRepository:
    """Requêtes pour le domaine purchase_request"""

    def _get_connection(self):
        return get_connection()

    def _exists(self, request_id: str) -> None:
        """Vérifie qu'une demande existe, lève NotFoundError sinon."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT 1 FROM purchase_request WHERE id = %s", (request_id,))
            if not cur.fetchone():
                raise NotFoundError(
                    f"Demande d'achat {request_id} non trouvée")
        finally:
            release_connection(conn)

    def _ensure_action_intervention_editable(self, cur, action_id: str) -> None:
        """Bloque les écritures DA si l'action appartient à une intervention fermée."""
        cur.execute(
            """
            SELECT ia.intervention_id, i.status_actual
            FROM intervention_action ia
            LEFT JOIN intervention i ON i.id = ia.intervention_id
            WHERE ia.id = %s
            """,
            (action_id,),
        )
        row = cur.fetchone()
        if not row:
            raise NotFoundError(f"Action {action_id} non trouvée")

        status_actual = str(row[1] or "").strip().lower()
        if status_actual == CLOSED_STATUS_CODE:
            raise ValidationError(
                "Intervention fermée : aucune modification des demandes d'achat liées n'est autorisée"
            )

    def _ensure_request_intervention_editable(self, cur, request_id: str) -> None:
        """Bloque les écritures DA si la demande est liée à une intervention fermée."""
        cur.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM intervention i
                WHERE i.status_actual = %s
                  AND (
                    i.id = (
                        SELECT pr.intervention_id
                        FROM purchase_request pr
                        WHERE pr.id = %s
                    )
                    OR i.id IN (
                        SELECT ia.intervention_id
                        FROM intervention_action_purchase_request iapr
                        JOIN intervention_action ia ON ia.id = iapr.intervention_action_id
                        WHERE iapr.purchase_request_id = %s
                    )
                  )
            )
            """,
            (CLOSED_STATUS_CODE, request_id, request_id),
        )
        if cur.fetchone()[0]:
            raise ValidationError(
                "Intervention fermée : aucune modification des demandes d'achat liées n'est autorisée"
            )

    def add(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle demande d'achat.

        Deux modes :
        - Lié à une action (intervention_action_id fourni) : liaison insérée dans
          intervention_action_purchase_request. intervention_id reste NULL sur la DA.
        - Autonome (intervention_action_id absent) : DA spontanée sans aucune relation.
        """
        from api.errors.exceptions import NotFoundError

        intervention_action_id = data.get('intervention_action_id')

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            if intervention_action_id:
                # Vérifie que l'action existe
                action_id_str = str(intervention_action_id)
                self._ensure_action_intervention_editable(cur, action_id_str)

            request_id = str(uuid4())
            now = datetime.now()

            cur.execute(
                """
                INSERT INTO purchase_request
                (id, status, stock_item_id, item_label, quantity, unit,
                 requested_by, urgency, reason, notes, workshop,
                 created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    now,
                    now
                )
            )

            if intervention_action_id:
                # Liaison action → DA dans la table de jonction
                cur.execute(
                    """
                    INSERT INTO intervention_action_purchase_request
                    (intervention_action_id, purchase_request_id)
                    VALUES (%s, %s)
                    """,
                    (str(intervention_action_id), request_id)
                )

            conn.commit()
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la création de la demande d'achat: {str(e)}") from e
        finally:
            release_connection(conn)

        return self.get_detail(request_id)

    def update(self, request_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour une demande d'achat existante"""
        self._exists(request_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            self._ensure_request_intervention_editable(cur, request_id)

            now = datetime.now()

            # Champs modifiables (status supprimé car calculé automatiquement)
            updatable_fields = [
                'stock_item_id', 'item_label', 'quantity', 'unit',
                'requested_by', 'urgency', 'reason', 'notes', 'workshop',
                'intervention_id', 'quantity_approved',
                'approver_name', 'approved_at'
            ]

            set_clauses = []
            params = []

            for field in updatable_fields:
                if field in data:
                    set_clauses.append(f"{field} = %s")
                    params.append(data[field])

            if not set_clauses:
                return self.get_detail(request_id)

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
        except (NotFoundError, ValidationError):
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la mise à jour: {str(e)}") from e
        finally:
            release_connection(conn)

        return self.get_detail(request_id)

    def delete(self, request_id: str) -> bool:
        """Supprime une demande d'achat"""
        self._exists(request_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            self._ensure_request_intervention_editable(cur, request_id)

            cur.execute(
                "DELETE FROM purchase_request WHERE id = %s", (request_id,))
            conn.commit()
            return True
        except (NotFoundError, ValidationError):
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la suppression: {str(e)}") from e
        finally:
            release_connection(conn)

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

    def _derive_status(
        self,
        stock_item_id: Optional[str] = None,
        supplier_refs_count: Optional[int] = None,
        has_order_lines: bool = False,
        quotes_count: int = 0,
        selected_count: int = 0,
        total_allocated: int = 0,
        total_received: int = 0
    ) -> str:
        """
        Calcule le statut dérivé basé sur les compteurs agrégés.

        Règles métier :
        - TO_QUALIFY : Pas de référence stock normalisée (stock_item_id is NULL)
        - NO_SUPPLIER_REF : Référence stock ok, mais aucune référence fournisseur liée
        - PENDING_DISPATCH : Référence fournisseur ok, mais pas encore dans un supplier order
        - OPEN : Présent dans un supplier order (mutualisation)
        - QUOTED : Au moins un devis reçu
        - ORDERED : Au moins une ligne sélectionnée pour commande
        - PARTIAL : Livraison partielle
        - RECEIVED : Livraison complète
        """
        # Règle 1 : Pas de référence normalisée = À qualifier
        if stock_item_id is None:
            return 'TO_QUALIFY'

        # Règle 2 : Référence fournisseur manquante
        if supplier_refs_count == 0:
            return 'NO_SUPPLIER_REF'

        # Règle 3 : Référence fournisseur ok mais pas de lignes = À dispatcher
        if not has_order_lines:
            return 'PENDING_DISPATCH'

        # Règle 4+ : Statuts basés sur les order_lines
        if total_received >= total_allocated and total_allocated > 0:
            return 'RECEIVED'
        if total_received > 0:
            return 'PARTIAL'
        if selected_count > 0:
            return 'ORDERED'
        if quotes_count > 0:
            return 'QUOTED'
        return 'OPEN'

    def _derive_status_from_order_lines(
        self,
        order_lines: List[Dict],
        stock_item_id: Optional[str] = None,
        supplier_refs_count: Optional[int] = None
    ) -> str:
        """
        Calcule le statut dérivé basé sur les order_lines.
        Wrapper autour de _derive_status pour compatibilité.
        """
        if not order_lines:
            return self._derive_status(
                stock_item_id=stock_item_id,
                supplier_refs_count=supplier_refs_count,
                has_order_lines=False
            )

        quotes_count = sum(
            1 for line in order_lines if line.get('quote_received'))
        selected_count = sum(
            1 for line in order_lines if line.get('is_selected'))
        total_allocated = sum(line.get('quantity_allocated', 0)
                              for line in order_lines)
        total_received = sum(line.get('quantity_received', 0)
                             or 0 for line in order_lines)

        # Rejeté : toutes les lignes sont dans un panier terminal (CANCELLED/CLOSED) sans sélection
        terminal_statuses = ('CANCELLED', 'CLOSED')
        all_terminal = all(
            line.get('supplier_order_status') in terminal_statuses
            for line in order_lines
        )
        if all_terminal and selected_count == 0:
            return 'REJECTED'

        # Reçu : toutes les lignes en panier terminal avec au moins une sélectionnée
        # (panier CLOSED + sélection = commande livrée et clôturée)
        if all_terminal and selected_count > 0:
            return 'RECEIVED'

        # En chiffrage : le panier a quitté OPEN (SENT/ACK = devis demandé), pas encore de réponse
        has_locked_order = any(
            line.get('supplier_order_status') in ('SENT', 'ACK')
            for line in order_lines
        )
        if has_locked_order and selected_count == 0 and quotes_count == 0:
            return 'CONSULTATION'

        return self._derive_status(
            stock_item_id=stock_item_id,
            supplier_refs_count=supplier_refs_count,
            has_order_lines=True,
            quotes_count=quotes_count,
            selected_count=selected_count,
            total_allocated=total_allocated,
            total_received=total_received
        )

    def get_list(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        intervention_id: Optional[str] = None,
        urgency: Optional[str] = None,
        ids: Optional[List[str]] = None,
        exclude_statuses: Optional[List[str]] = None
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
                # Agrège les deux modèles :
                # - Legacy : pr.intervention_id direct (Directus)
                # - Nouveau : via table de jonction action↔DA
                where_clauses.append(
                    "(pr.intervention_id = %s OR ia.intervention_id = %s)"
                )
                params.append(intervention_id)
                params.append(intervention_id)

            if urgency:
                where_clauses.append("pr.urgency = %s")
                params.append(urgency)

            if ids:
                placeholders = ','.join(['%s'] * len(ids))
                where_clauses.append(f"pr.id IN ({placeholders})")
                params.extend(ids)

            where_sql = " AND ".join(where_clauses)

            query = f"""
                SELECT
                    pr.id,
                    pr.item_label,
                    pr.quantity,
                    pr.unit,
                    pr.stock_item_id,
                    (SELECT COUNT(*) FROM stock_item_supplier WHERE stock_item_id = si.id) AS supplier_refs_count,

                    -- Infos directes (pas d'objets imbriqués)
                    si.ref AS stock_item_ref,
                    si.name AS stock_item_name,
                    i.code AS intervention_code,
                    pr.requested_by AS requester_name,
                    pr.urgency,

                    -- Compteurs agrégés
                    COALESCE(agg.quotes_count, 0) AS quotes_count,
                    COALESCE(agg.selected_count, 0) AS selected_count,
                    COALESCE(agg.suppliers_count, 0) AS suppliers_count,
                    COALESCE(agg.total_allocated, 0) AS total_allocated,
                    COALESCE(agg.total_received, 0) AS total_received,
                    COALESCE(agg.has_locked_order, false) AS has_locked_order,
                    COALESCE(agg.all_terminal, false) AS all_terminal,

                    pr.created_at,
                    pr.updated_at

                FROM purchase_request pr
                LEFT JOIN stock_item si ON pr.stock_item_id = si.id
                -- Intervention déduite via la table de jonction action↔DA
                LEFT JOIN intervention_action_purchase_request iapr ON iapr.purchase_request_id = pr.id
                LEFT JOIN intervention_action ia ON ia.id = iapr.intervention_action_id
                LEFT JOIN intervention i ON i.id = ia.intervention_id
                LEFT JOIN LATERAL (
                    SELECT
                        COUNT(DISTINCT CASE WHEN sol.quote_received THEN sol.id END) AS quotes_count,
                        COUNT(DISTINCT CASE WHEN sol.is_selected THEN sol.id END) AS selected_count,
                        COUNT(DISTINCT so.supplier_id) AS suppliers_count,
                        SUM(solpr.quantity) AS total_allocated,
                        SUM(COALESCE(sol.quantity_received, 0)) AS total_received,
                        BOOL_OR(so.status IN ('SENT', 'ACK')) AS has_locked_order,
                        BOOL_AND(so.status IN ('CANCELLED', 'CLOSED')) AS all_terminal
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

                # Extrait les données pour le calcul du statut
                stock_item_id = item.get('stock_item_id')
                supplier_refs_count = item.pop('supplier_refs_count', None)
                quotes_count = item.get('quotes_count', 0) or 0
                selected_count = item.get('selected_count', 0) or 0
                total_allocated = item.pop('total_allocated', 0) or 0
                total_received = item.pop('total_received', 0) or 0
                suppliers_count = item.get('suppliers_count', 0) or 0
                has_locked_order = item.pop('has_locked_order', False) or False
                all_terminal = item.pop('all_terminal', False) or False
                has_order_lines = (
                    quotes_count > 0
                    or selected_count > 0
                    or suppliers_count > 0
                    or total_allocated > 0
                )

                # Rejeté : toutes les lignes dans un panier terminal (CANCELLED/CLOSED), aucune sélectionnée
                if all_terminal and selected_count == 0 and has_order_lines:
                    status_code = 'REJECTED'
                # Reçu : toutes les lignes en panier terminal avec au moins une sélectionnée
                elif all_terminal and selected_count > 0 and has_order_lines:
                    status_code = 'RECEIVED'
                # Mode consultation : panier verrouillé (SENT/ACK), sans devis ni sélection
                elif has_locked_order and selected_count == 0 and quotes_count == 0 and has_order_lines:
                    status_code = 'CONSULTATION'
                else:
                    # Calcule le statut dérivé via la fonction centralisée
                    status_code = self._derive_status(
                        stock_item_id=str(
                            stock_item_id) if stock_item_id else None,
                        supplier_refs_count=supplier_refs_count,
                        has_order_lines=has_order_lines,
                        quotes_count=quotes_count,
                        selected_count=selected_count,
                        total_allocated=total_allocated,
                        total_received=total_received
                    )

                # Filtre par statut si demandé
                if status and status_code != status:
                    continue

                # Exclut les statuts explicitement exclus
                if exclude_statuses and status_code in exclude_statuses:
                    continue

                item['derived_status'] = self._map_derived_status(status_code)
                results.append(item)

            logger.info(
                "Fetched %d purchase requests (list view)", len(results))
            return results
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error fetching purchase request list: %s", str(e))
            raise_db_error(e, "opération")
        finally:
            release_connection(conn)

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
                -- Intervention déduite via la table de jonction action↔DA
                LEFT JOIN intervention_action_purchase_request iapr ON iapr.purchase_request_id = pr.id
                LEFT JOIN intervention_action ia ON ia.id = iapr.intervention_action_id
                LEFT JOIN intervention i ON i.id = ia.intervention_id
                LEFT JOIN machine e ON i.machine_id = e.id
                WHERE pr.id = %s
                """,
                (request_id,)
            )
            row = cur.fetchone()

            if not row:
                raise NotFoundError(
                    f"Demande d'achat {request_id} non trouvée")

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

            # Calcule le statut dérivé (passe stock_item_id pour règle "À qualifier")
            stock_item_id = data.get('stock_item_id')
            stock_item = data.get('stock_item')
            supplier_refs_count = (
                stock_item.get('supplier_refs_count') if stock_item else None
            )
            status_code = self._derive_status_from_order_lines(
                order_lines,
                stock_item_id=str(stock_item_id) if stock_item_id else None,
                supplier_refs_count=supplier_refs_count
            )
            data['derived_status'] = self._map_derived_status(status_code)
            data['is_editable'] = status_code in {
                'TO_QUALIFY', 'NO_SUPPLIER_REF', 'PENDING_DISPATCH'}

            logger.info("Fetched purchase request detail: %s", request_id)
            return data

        except NotFoundError:
            raise
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error fetching purchase request detail: %s", str(e))
            raise_db_error(e, "opération")
        finally:
            release_connection(conn)

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
                    """
                    SELECT DISTINCT pr.id FROM purchase_request pr
                    LEFT JOIN intervention_action_purchase_request iapr ON iapr.purchase_request_id = pr.id
                    LEFT JOIN intervention_action ia ON ia.id = iapr.intervention_action_id
                    WHERE pr.intervention_id = %s
                       OR ia.intervention_id = %s
                    ORDER BY pr.id
                    """,
                    (intervention_id, intervention_id)
                )
                rows = cur.fetchall()
            finally:
                release_connection(conn)

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
                    COUNT(CASE WHEN urgency IN ('critical', 'high') THEN 1 END) as urgent_count
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
            by_urgency = [{'urgency': row[0], 'count': row[1]}
                          for row in cur.fetchall()]

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
                        by_status[status_code] = by_status.get(
                            status_code, 0) + 1

            by_status_list = [
                {'status': code, 'count': count, **
                    DERIVED_STATUS_CONFIG.get(code, {})}
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

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error fetching stats: %s", str(e))
            raise_db_error(e, "opération")
        finally:
            release_connection(conn)

    def _find_or_create_order(self, cur, supplier_id_str: str, orders_cache: dict) -> tuple:
        """
        Trouve ou crée un supplier_order OPEN pour un fournisseur.
        Retourne (order_id, was_created).
        """
        if supplier_id_str in orders_cache:
            return orders_cache[supplier_id_str], False

        cur.execute(
            """
            SELECT id FROM supplier_order
            WHERE supplier_id = %s AND status = 'OPEN'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (supplier_id_str,)
        )
        row = cur.fetchone()
        if row:
            order_id = str(row[0])
            orders_cache[supplier_id_str] = order_id
            return order_id, False

        new_order_id = str(uuid4())
        cur.execute(
            """
            INSERT INTO supplier_order (id, supplier_id, status, created_at)
            VALUES (%s, %s, 'OPEN', NOW())
            """,
            (new_order_id, supplier_id_str)
        )
        orders_cache[supplier_id_str] = new_order_id
        logger.info("Created new supplier_order %s for supplier %s",
                    new_order_id, supplier_id_str)
        return new_order_id, True

    def _dispatch_to_supplier(self, cur, order_id: str, stock_item_id: str,
                              supplier_ref: str, unit_price, req_id_str: str,
                              req_quantity: int):
        """Crée ou fusionne la ligne de commande et lie la purchase_request."""
        cur.execute(
            """
            INSERT INTO supplier_order_line
            (id, supplier_order_id, stock_item_id, supplier_ref_snapshot, quantity, unit_price)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (supplier_order_id, stock_item_id)
            DO UPDATE SET quantity = COALESCE(supplier_order_line.quantity, 0) + EXCLUDED.quantity
            RETURNING id
            """,
            (
                str(uuid4()),
                order_id,
                stock_item_id,
                supplier_ref,
                req_quantity,
                float(unit_price) if unit_price else None
            )
        )
        line_id = str(cur.fetchone()[0])

        # Invariant anti-doublon : ON CONFLICT ignore si déjà lié
        cur.execute(
            """
            INSERT INTO supplier_order_line_purchase_request
            (id, supplier_order_line_id, purchase_request_id, quantity)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (supplier_order_line_id, purchase_request_id)
            DO UPDATE SET quantity = EXCLUDED.quantity
            """,
            (str(uuid4()), line_id, req_id_str, req_quantity)
        )

    def dispatch_all(self) -> Dict[str, Any]:
        """
        Dispatch toutes les demandes PENDING_DISPATCH vers des supplier_orders.

        Règles métier :
        - Fournisseur préféré (is_preferred=true) → mode DIRECT : 1 commande, 1 ligne
        - Aucun préféré → mode CONSULTATION : 1 commande par fournisseur référencé
        - Aucun fournisseur → erreur remontée dans errors[]
        - Invariant : une demande déjà liée à une supplier_order_line est ignorée
        """
        logger.info("Starting dispatch_all for PENDING_DISPATCH requests")

        pending_requests = [
            req for req in self.get_list(limit=1000, offset=0)
            if req.get('derived_status', {}).get('code') == 'PENDING_DISPATCH'
        ]

        logger.info("Found %d requests to dispatch", len(pending_requests))

        dispatched_count = 0
        created_orders = 0
        errors = []
        details = []
        orders_cache = {}  # Cache: supplier_id_str -> order_id

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            for req in pending_requests:
                req_id_str = str(req['id'])
                savepoint_name = f"sp_{req_id_str.replace('-', '_')[:8]}"

                try:
                    cur.execute(f"SAVEPOINT {savepoint_name}")

                    stock_item_id = req.get('stock_item_id')
                    if not stock_item_id:
                        cur.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                        errors.append({
                            'purchase_request_id': req_id_str,
                            'error': 'Pas de stock_item_id'
                        })
                        continue

                    req_quantity = req.get('quantity', 1)
                    stock_item_id_str = str(stock_item_id)

                    # Récupère tous les fournisseurs de l'article (préféré en premier)
                    cur.execute(
                        """
                        SELECT sis.supplier_id, sis.supplier_ref, sis.unit_price,
                               sis.is_preferred, s.name AS supplier_name
                        FROM stock_item_supplier sis
                        LEFT JOIN supplier s ON s.id = sis.supplier_id
                        WHERE sis.stock_item_id = %s
                        ORDER BY sis.is_preferred DESC, s.name ASC
                        """,
                        (stock_item_id_str,)
                    )
                    supplier_rows = cur.fetchall()

                    if not supplier_rows:
                        cur.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                        errors.append({
                            'purchase_request_id': req_id_str,
                            'error': 'Aucun fournisseur référencé'
                        })
                        continue

                    # Détermine le mode : préféré trouvé → direct, sinon consultation
                    # is_preferred du premier
                    has_preferred = supplier_rows[0][3]

                    if has_preferred:
                        # Mode DIRECT : un seul fournisseur (le préféré)
                        supplier_id_str, supplier_ref, unit_price, _, supplier_name = supplier_rows[
                            0]
                        supplier_id_str = str(supplier_id_str)

                        order_id, was_created = self._find_or_create_order(
                            cur, supplier_id_str, orders_cache
                        )
                        if was_created:
                            created_orders += 1

                        self._dispatch_to_supplier(
                            cur, order_id, stock_item_id_str,
                            supplier_ref, unit_price, req_id_str, req_quantity
                        )

                        details.append({
                            'purchase_request_id': req_id_str,
                            'mode': 'direct',
                            'supplier_order_id': order_id,
                            'supplier_name': supplier_name
                        })

                    else:
                        # Mode CONSULTATION : tous les fournisseurs
                        consultation_orders = []
                        for sup_row in supplier_rows:
                            supplier_id_str, supplier_ref, unit_price, _, supplier_name = sup_row
                            supplier_id_str = str(supplier_id_str)

                            order_id, was_created = self._find_or_create_order(
                                cur, supplier_id_str, orders_cache
                            )
                            if was_created:
                                created_orders += 1

                            self._dispatch_to_supplier(
                                cur, order_id, stock_item_id_str,
                                supplier_ref, unit_price, req_id_str, req_quantity
                            )

                            consultation_orders.append({
                                'supplier_order_id': order_id,
                                'supplier_name': supplier_name
                            })

                        details.append({
                            'purchase_request_id': req_id_str,
                            'mode': 'consultation',
                            'supplier_orders': consultation_orders
                        })

                    cur.execute(f"RELEASE SAVEPOINT {savepoint_name}")
                    dispatched_count += 1
                    logger.debug("Dispatched request %s", req['id'])

                except Exception as e:
                    try:
                        cur.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                    except Exception:
                        pass
                    errors.append({
                        'purchase_request_id': req_id_str,
                        'error': str(e)
                    })
                    logger.error(
                        "Error dispatching request %s: %s", req['id'], str(e))

            conn.commit()
            logger.info("Dispatch completed: %d dispatched, %d orders created, %d errors",
                        dispatched_count, created_orders, len(errors))

            return {
                'dispatched_count': dispatched_count,
                'created_orders': created_orders,
                'errors': errors,
                'details': details
            }

        except Exception as e:
            conn.rollback()
            logger.error("Dispatch failed: %s", str(e))
            raise DatabaseError(f"Erreur lors du dispatch: {str(e)}") from e
        finally:
            release_connection(conn)
