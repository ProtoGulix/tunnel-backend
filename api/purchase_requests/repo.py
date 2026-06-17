from fastapi import HTTPException
from typing import Dict, Any, List, Optional, Literal
from uuid import uuid4
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

from api.db import get_connection, release_connection
from api.errors.exceptions import DatabaseError, raise_db_error, NotFoundError, ValidationError
from api.constants import DERIVED_STATUS_CONFIG, CLOSED_STATUS_CODE, SUPPLIER_ORDER_STATUS_CONFIG

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
                  AND i.id IN (
                      SELECT ia.intervention_id
                      FROM intervention_action_purchase_request iapr
                      JOIN intervention_action ia ON ia.id = iapr.intervention_action_id
                      WHERE iapr.purchase_request_id = %s
                  )
            )
            """,
            (CLOSED_STATUS_CODE, request_id),
        )
        if cur.fetchone()[0]:
            raise ValidationError(
                "Intervention fermée : aucune modification des demandes d'achat liées n'est autorisée"
            )

    def add(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une nouvelle demande d'achat."""
        from api.errors.exceptions import NotFoundError

        intervention_action_id = data.get('intervention_action_id')

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            if intervention_action_id:
                action_id_str = str(intervention_action_id)
                self._ensure_action_intervention_editable(cur, action_id_str)

            # Résolution part_id : priorité à part_id explicite,
            # fallback sur stock_item_id legacy (résolu via UUID reuse)
            part_id = data.get('part_id')
            if not part_id and data.get('stock_item_id'):
                stock_item_id_raw = str(data['stock_item_id'])
                cur.execute("SELECT id FROM part WHERE id = %s", (stock_item_id_raw,))
                row = cur.fetchone()
                if row:
                    part_id = str(row[0])
                else:
                    logger.warning(
                        "add(): stock_item_id=%s fourni mais aucun part correspondant — DA créée sans référence",
                        stock_item_id_raw
                    )

            request_id = str(uuid4())
            now = datetime.now()

            cur.execute(
                """
                INSERT INTO purchase_request
                (id, status, part_id, item_label, quantity, unit,
                 requested_by, urgency, reason, notes, workshop,
                 created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    request_id,
                    data.get('status', 'open'),
                    str(part_id) if part_id else None,
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
                'stock_item_id', 'part_id', 'item_label', 'quantity', 'unit',
                'requested_by', 'urgency', 'reason', 'notes', 'workshop',
                'quantity_approved',
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
        part_id: Optional[str] = None,
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
        - TO_QUALIFY : Pas de référence normalisée (ni stock_item_id ni part_id)
        - NO_SUPPLIER_REF : Référence ok, mais aucune référence fournisseur liée
        - PENDING_DISPATCH : Référence fournisseur ok, mais pas encore dans un supplier order
        - OPEN : Présent dans un supplier order (mutualisation)
        - QUOTED : Au moins un devis reçu
        - ORDERED : Au moins une ligne sélectionnée pour commande
        - PARTIAL : Livraison partielle
        - RECEIVED : Livraison complète
        """
        # Règle 1 : Pas de référence normalisée = À qualifier (legacy stock_item OU nouveau part)
        if stock_item_id is None and part_id is None:
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
        part_id: Optional[str] = None,
        supplier_refs_count: Optional[int] = None
    ) -> str:
        """
        Calcule le statut dérivé basé sur les order_lines.
        Wrapper autour de _derive_status pour compatibilité.
        """
        if not order_lines:
            return self._derive_status(
                stock_item_id=stock_item_id,
                part_id=part_id,
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
            part_id=part_id,
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
                where_clauses.append("ia.intervention_id = %s")
                params.append(intervention_id)

            if urgency:
                where_clauses.append("prd.urgency = %s")
                params.append(urgency)

            if ids:
                placeholders = ','.join(['%s'] * len(ids))
                where_clauses.append(f"prd.id IN ({placeholders})")
                params.extend(ids)

            where_sql = " AND ".join(where_clauses)

            query = f"""
                SELECT
                    prd.id,
                    COALESCE(prd.item_label, pt_pref.label, si.name) AS item_label,
                    prd.quantity,
                    prd.unit,
                    prd.stock_item_id,
                    pr_base.part_id,
                    prd.derived_status,
                    prd.quotes_count,
                    prd.selected_count,
                    prd.total_allocated,
                    prd.total_received,

                    -- Infos jointes stock_item (legacy)
                    si.ref AS stock_item_ref,
                    si.name AS stock_item_name,
                    -- Infos jointes part (nouveau)
                    pt.internal_ref AS part_internal_ref,
                    pt_pref.label AS part_display_name,
                    pr_intervention.code AS intervention_code,
                    prd.requested_by AS requester_name,
                    prd.urgency,
                    COUNT(DISTINCT so.supplier_id) AS suppliers_count,

                    prd.created_at,
                    prd.updated_at

                FROM purchase_request_derived_status prd
                JOIN purchase_request pr_base ON pr_base.id = prd.id
                LEFT JOIN stock_item si ON si.id = prd.stock_item_id
                LEFT JOIN part pt ON pt.id = pr_base.part_id
                LEFT JOIN LATERAL (
                    SELECT COALESCE(label, manufacturer_ref) AS label
                    FROM part_manufacturer_ref
                    WHERE part_id = pt.id
                    ORDER BY is_preferred DESC, created_at ASC
                    LIMIT 1
                ) pt_pref ON true
                LEFT JOIN LATERAL (
                    SELECT i.code
                    FROM intervention_action_purchase_request iapr2
                    JOIN intervention_action ia2 ON ia2.id = iapr2.intervention_action_id
                    JOIN intervention i ON i.id = ia2.intervention_id
                    WHERE iapr2.purchase_request_id = prd.id
                    LIMIT 1
                ) pr_intervention ON true
                LEFT JOIN supplier_order_line_purchase_request solpr ON solpr.purchase_request_id = prd.id
                LEFT JOIN supplier_order_line sol ON sol.id = solpr.supplier_order_line_id
                LEFT JOIN supplier_order so ON so.id = sol.supplier_order_id

                WHERE {where_sql}

                GROUP BY prd.id, prd.item_label, prd.quantity, prd.unit, prd.stock_item_id,
                         pr_base.part_id,
                         prd.derived_status, prd.quotes_count, prd.selected_count,
                         prd.total_allocated, prd.total_received, prd.requested_by, prd.urgency,
                         prd.created_at, prd.updated_at,
                         si.ref, si.name, pt.internal_ref, pt_pref.label, pr_intervention.code

                ORDER BY prd.created_at DESC
                LIMIT %s OFFSET %s
            """

            params.extend([limit, offset])
            cur.execute(query, params)
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]

            results = []
            for row in rows:
                item = dict(zip(cols, row))
                status_code = item.pop('derived_status')

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

            # Récupère la demande avec stock_item, part et intervention
            cur.execute(
                """
                SELECT
                    pr.*,
                    -- Stock item (legacy)
                    si.id as si_id, si.name as si_name, si.ref as si_ref,
                    si.family_code as si_family_code, si.sub_family_code as si_sub_family_code,
                    si.quantity as si_quantity, si.unit as si_unit, si.location as si_location,
                    (SELECT COUNT(*) FROM stock_item_supplier WHERE stock_item_id = si.id) as si_supplier_refs_count,
                    -- Part (nouveau)
                    pt.id as pt_id, pt.internal_ref as pt_internal_ref,
                    pt.family_code as pt_family_code, pt.sub_family_code as pt_sub_family_code,
                    pt.qty_in_stock as pt_qty_in_stock, pt.unit as pt_unit, pt.location as pt_location,
                    (SELECT COUNT(*) FROM part_supplier_ref psr
                     JOIN part_manufacturer_ref pmr ON pmr.id = psr.part_manufacturer_ref_id
                     WHERE pmr.part_id = pt.id) as pt_supplier_refs_count,
                    (SELECT COALESCE(label, manufacturer_ref) FROM part_manufacturer_ref
                     WHERE part_id = pt.id AND is_preferred = true LIMIT 1) as pt_display_name,
                    -- Intervention déduite via la table de jonction action↔DA
                    i.id as i_id, i.code as i_code, i.title as i_title,
                    i.priority as i_priority, i.status_actual as i_status_actual,
                    -- Équipement
                    e.id as e_id, e.code as e_code, e.name as e_name
                FROM purchase_request pr
                LEFT JOIN stock_item si ON pr.stock_item_id = si.id
                LEFT JOIN part pt ON pr.part_id = pt.id
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

            # Construit stock_item (legacy)
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

            # Construit part (nouveau)
            if data.get('pt_id'):
                data['part'] = {
                    'id': data['pt_id'],
                    'internal_ref': data['pt_internal_ref'],
                    'display_name': data.get('pt_display_name') or data['pt_internal_ref'],
                    'family_code': data['pt_family_code'],
                    'sub_family_code': data['pt_sub_family_code'],
                    'qty_in_stock': data['pt_qty_in_stock'],
                    'unit': data['pt_unit'],
                    'location': data['pt_location'],
                    'supplier_refs_count': data['pt_supplier_refs_count']
                }
            else:
                data['part'] = None

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
                if key.startswith('si_') or key.startswith('pt_') or key.startswith('i_') or key.startswith('e_'):
                    del data[key]

            # Récupère order_lines enrichis avec fournisseur
            order_lines = self._get_linked_order_lines_detail(request_id, conn)
            data['order_lines'] = order_lines

            # Calcule le statut dérivé (stock_item_id legacy OU part_id nouveau)
            stock_item_id = data.get('stock_item_id')
            part_id_val = data.get('part_id')
            part = data.get('part')
            stock_item = data.get('stock_item')
            supplier_refs_count = (
                part.get('supplier_refs_count') if part else
                stock_item.get('supplier_refs_count') if stock_item else None
            )
            status_code = self._derive_status_from_order_lines(
                order_lines,
                stock_item_id=str(stock_item_id) if stock_item_id else None,
                part_id=str(part_id_val) if part_id_val else None,
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
        """Récupère les order_lines enrichis avec fournisseur, ref catalogue et fabricant"""
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
                    sol.manufacturer as sol_manufacturer, sol.manufacturer_ref as sol_manufacturer_ref,
                    sol.lead_time_days, sol.notes,
                    so.status as supplier_order_status, so.order_number as supplier_order_number,
                    -- Fournisseur enrichi
                    s.id as supplier_id, s.name as supplier_name, s.code as supplier_code,
                    s.contact_name as supplier_contact_name, s.email as supplier_email, s.phone as supplier_phone,
                    -- Référence catalogue fournisseur
                    sis.supplier_ref as catalog_ref,
                    -- Fabricant depuis catalogue
                    mi.manufacturer_name as catalog_manufacturer,
                    mi.manufacturer_ref as catalog_manufacturer_ref
                FROM supplier_order_line_purchase_request solpr
                JOIN supplier_order_line sol ON solpr.supplier_order_line_id = sol.id
                JOIN supplier_order so ON sol.supplier_order_id = so.id
                LEFT JOIN supplier s ON so.supplier_id = s.id
                LEFT JOIN stock_item_supplier sis
                    ON sis.stock_item_id = sol.stock_item_id
                    AND sis.supplier_id = so.supplier_id
                LEFT JOIN manufacturer_item mi ON sis.manufacturer_item_id = mi.id
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

                # Statut commande : code → objet complet
                raw_status = line.get('supplier_order_status')
                if raw_status and raw_status in SUPPLIER_ORDER_STATUS_CONFIG:
                    cfg = SUPPLIER_ORDER_STATUS_CONFIG[raw_status]
                    line['supplier_order_status'] = {
                        'code': raw_status,
                        'label': cfg['label'],
                        'color': cfg['color'],
                        'description': cfg['description'],
                        'is_locked': cfg['is_locked'],
                    }

                # Référence catalogue (déjà dans line['catalog_ref'])

                # Fabricant : priorité champ manuel de la ligne, sinon catalogue
                sol_mfr = line.pop('sol_manufacturer', None)
                sol_mfr_ref = line.pop('sol_manufacturer_ref', None)
                mfr_name = sol_mfr or line.pop('catalog_manufacturer', None)
                mfr_ref = sol_mfr_ref or line.pop('catalog_manufacturer_ref', None)
                line['manufacturer'] = {'name': mfr_name, 'ref': mfr_ref} if (mfr_name or mfr_ref) else None

                # Nettoie colonnes intermédiaires supplier_*
                for key in list(line.keys()):
                    if key.startswith('supplier_') and key not in ('supplier_order_id', 'supplier_order_line_id', 'supplier_order_status', 'supplier_order_number'):
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
                    SELECT DISTINCT iapr.purchase_request_id AS id
                    FROM intervention_action_purchase_request iapr
                    JOIN intervention_action ia ON ia.id = iapr.intervention_action_id
                    WHERE ia.intervention_id = %s
                    ORDER BY 1
                    """,
                    (intervention_id,)
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

    def get_facets(self) -> Dict[str, Any]:
        """Compteurs par statut dérivé en temps réel, sans filtre de date."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT derived_status, COUNT(*) AS count
                FROM purchase_request_derived_status
                GROUP BY derived_status
            """)
            by_status = [
                {'status': row[0], 'count': row[1], **DERIVED_STATUS_CONFIG.get(row[0], {})}
                for row in cur.fetchall()
            ]
            pending_dispatch_count = next(
                (s['count'] for s in by_status if s['status'] == 'PENDING_DISPATCH'), 0
            )
            return {
                'by_status': by_status,
                'pending_dispatch_count': pending_dispatch_count,
            }
        except Exception as e:
            raise_db_error(e, "opération")
        finally:
            release_connection(conn)

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

    def _dispatch_to_supplier(self, cur, order_id: str, stock_item_id: Optional[str],
                              supplier_ref: str, unit_price, req_id_str: str,
                              req_quantity: int, part_id: Optional[str] = None):
        """Crée ou fusionne la ligne de commande et lie la purchase_request."""
        # Le ON CONFLICT doit cibler l'index partiel correspondant au type de référence
        if part_id:
            conflict_clause = "ON CONFLICT (supplier_order_id, part_id) WHERE part_id IS NOT NULL"
        else:
            conflict_clause = "ON CONFLICT (supplier_order_id, stock_item_id) WHERE stock_item_id IS NOT NULL"

        cur.execute(
            f"""
            INSERT INTO supplier_order_line
            (id, supplier_order_id, stock_item_id, part_id, supplier_ref_snapshot, quantity, unit_price)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            {conflict_clause}
            DO UPDATE SET quantity = COALESCE(supplier_order_line.quantity, 0) + EXCLUDED.quantity
            RETURNING id
            """,
            (
                str(uuid4()),
                order_id,
                stock_item_id,
                part_id,
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

    def _search_part(self, cur, search_term: str) -> Optional[Dict[str, Any]]:
        """Cherche la meilleure pièce correspondant au terme de recherche."""
        pat = f"%{search_term}%"
        cur.execute(
            """
            SELECT
                p.id,
                p.internal_ref,
                COALESCE(
                    (SELECT COALESCE(pmr.label, pmr.manufacturer_ref)
                     FROM part_manufacturer_ref pmr
                     WHERE pmr.part_id = p.id AND pmr.is_preferred = true
                     LIMIT 1),
                    (SELECT COALESCE(pmr.label, pmr.manufacturer_ref)
                     FROM part_manufacturer_ref pmr
                     WHERE pmr.part_id = p.id
                     LIMIT 1)
                ) AS display_name
            FROM part p
            WHERE
                p.internal_ref ILIKE %s
                OR EXISTS (
                    SELECT 1 FROM part_manufacturer_ref pmr2
                    WHERE pmr2.part_id = p.id
                    AND (pmr2.manufacturer_ref ILIKE %s OR pmr2.label ILIKE %s OR pmr2.manufacturer_name ILIKE %s)
                )
                OR EXISTS (
                    SELECT 1 FROM part_supplier_ref psr2
                    JOIN part_manufacturer_ref pmr3 ON pmr3.id = psr2.part_manufacturer_ref_id
                    WHERE pmr3.part_id = p.id AND psr2.supplier_ref ILIKE %s
                )
            LIMIT 1
            """,
            (pat, pat, pat, pat, pat)
        )
        row = cur.fetchone()
        if not row:
            return None
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))

    def _count_existing_to_qualify(self, cur, part_id: Optional[str], item_label: str) -> int:
        """
        Retourne le nombre de DA À qualifier (TO_QUALIFY) déjà existantes
        pour cette pièce (si part_id trouvé) ou ce libellé (si pas de part).
        """
        if part_id:
            cur.execute(
                """
                SELECT COUNT(*) FROM purchase_request
                WHERE part_id = %s
                  AND stock_item_id IS NULL
                  AND id NOT IN (
                    SELECT purchase_request_id FROM supplier_order_line_purchase_request
                  )
                """,
                (part_id,)
            )
        else:
            cur.execute(
                """
                SELECT COUNT(*) FROM purchase_request
                WHERE part_id IS NULL
                  AND stock_item_id IS NULL
                  AND item_label ILIKE %s
                """,
                (item_label,)
            )
        row = cur.fetchone()
        return int(row[0]) if row and row[0] else 0

    def _check_duplicate_on_intervention(self, cur, part_id: Optional[str], item_label: str, intervention_id: str) -> Optional[int]:
        """
        Vérifie si une DA avec ce part_id (ou ce label si pas de part) existe déjà sur l'intervention.
        Retourne la quantité déjà commandée si doublon, None sinon.
        """
        if part_id:
            cur.execute(
                """
                SELECT SUM(pr.quantity)
                FROM purchase_request pr
                JOIN intervention_action_purchase_request iapr ON iapr.purchase_request_id = pr.id
                JOIN intervention_action ia ON ia.id = iapr.intervention_action_id
                WHERE ia.intervention_id = %s AND pr.part_id = %s
                """,
                (intervention_id, part_id)
            )
        else:
            cur.execute(
                """
                SELECT SUM(pr.quantity)
                FROM purchase_request pr
                JOIN intervention_action_purchase_request iapr ON iapr.purchase_request_id = pr.id
                JOIN intervention_action ia ON ia.id = iapr.intervention_action_id
                WHERE ia.intervention_id = %s AND pr.part_id IS NULL AND pr.item_label ILIKE %s
                """,
                (intervention_id, item_label)
            )
        row = cur.fetchone()
        existing_qty = row[0] if row and row[0] is not None else None
        return int(existing_qty) if existing_qty else None

    def import_from_csv(
        self,
        rows: List[Dict[str, str]],
        intervention_id: str,
        col_ref: str,
        col_qty: str,
        urgency: str = 'normal',
        reason_code: str = 'IMPORT_CSV',
        dry_run: bool = False,
        excluded_rows: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Importe des DA en masse depuis les lignes d'un CSV.

        Pour chaque ligne :
        1. Tente de matcher la ref via recherche dans le catalogue part
        2. Vérifie les doublons sur l'intervention (warning non bloquant)
        3. Compte les DA À qualifier existantes pour cette référence
        4. Si dry_run=True : analyse sans créer (status='preview')
        5. Si excluded_rows contient le numéro de ligne : ignore (status='skipped')
        6. Sinon : crée la DA via la même mécanique que add()
        """
        excluded_set = set(excluded_rows or [])
        lines = []
        created = 0
        skipped = 0
        errors = 0

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            for idx, raw_row in enumerate(rows):
                row_num = idx + 1
                raw_ref = str(raw_row.get(col_ref, '') or '').strip()
                raw_qty = str(raw_row.get(col_qty, '') or '').strip()

                if not raw_ref:
                    errors += 1
                    lines.append({
                        'row': row_num,
                        'raw_ref': raw_ref,
                        'raw_qty': raw_qty,
                        'part_id': None,
                        'display_name': None,
                        'internal_ref': None,
                        'status': 'error',
                        'da_status': None,
                        'duplicate_warning': False,
                        'existing_qty': None,
                        'existing_to_qualify': 0,
                        'error': 'Référence vide',
                    })
                    continue

                try:
                    qty = int(float(raw_qty))
                    if qty <= 0:
                        raise ValueError
                except (ValueError, TypeError):
                    errors += 1
                    lines.append({
                        'row': row_num,
                        'raw_ref': raw_ref,
                        'raw_qty': raw_qty,
                        'part_id': None,
                        'display_name': None,
                        'internal_ref': None,
                        'status': 'error',
                        'da_status': None,
                        'duplicate_warning': False,
                        'existing_qty': None,
                        'existing_to_qualify': 0,
                        'error': f"Quantité invalide : '{raw_qty}'",
                    })
                    continue

                try:
                    # Recherche dans le catalogue
                    part = self._search_part(cur, raw_ref)
                    part_id_str = str(part['id']) if part else None
                    display_name = part.get('display_name') if part else None
                    internal_ref = part.get('internal_ref') if part else None

                    # Vérification doublon sur l'intervention
                    existing_qty = self._check_duplicate_on_intervention(
                        cur, part_id_str, raw_ref, intervention_id
                    )
                    duplicate_warning = existing_qty is not None

                    # Compte les DA À qualifier existantes pour cette référence
                    existing_to_qualify = self._count_existing_to_qualify(
                        cur, part_id_str, display_name or raw_ref
                    )

                    # Ligne exclue par l'utilisateur (dry_run=False requis)
                    if not dry_run and row_num in excluded_set:
                        skipped += 1
                        lines.append({
                            'row': row_num,
                            'raw_ref': raw_ref,
                            'raw_qty': raw_qty,
                            'part_id': part_id_str,
                            'display_name': display_name,
                            'internal_ref': internal_ref,
                            'status': 'skipped',
                            'da_status': None,
                            'duplicate_warning': duplicate_warning,
                            'existing_qty': existing_qty,
                            'existing_to_qualify': existing_to_qualify,
                            'error': None,
                        })
                        continue

                    if dry_run:
                        # Mode aperçu : analyse sans création
                        lines.append({
                            'row': row_num,
                            'raw_ref': raw_ref,
                            'raw_qty': raw_qty,
                            'part_id': part_id_str,
                            'display_name': display_name,
                            'internal_ref': internal_ref,
                            'status': 'preview',
                            'da_status': None,
                            'duplicate_warning': duplicate_warning,
                            'existing_qty': existing_qty,
                            'existing_to_qualify': existing_to_qualify,
                            'error': None,
                        })
                        continue

                    # Préparation du payload DA
                    da_data = {
                        'item_label': display_name or raw_ref,
                        'quantity': qty,
                        'urgency': urgency,
                        'reason_code': reason_code,
                    }
                    if part_id_str:
                        da_data['part_id'] = part_id_str

                    # Création via la mécanique existante (sans intervention_action_id car DA autonome)
                    created_da = self.add(da_data)

                    da_status_code = created_da.get('derived_status', {}).get('code')
                    created += 1

                    lines.append({
                        'row': row_num,
                        'raw_ref': raw_ref,
                        'raw_qty': raw_qty,
                        'part_id': part_id_str,
                        'display_name': display_name,
                        'internal_ref': internal_ref,
                        'status': 'created',
                        'da_status': da_status_code,
                        'duplicate_warning': duplicate_warning,
                        'existing_qty': existing_qty,
                        'existing_to_qualify': existing_to_qualify,
                        'error': None,
                    })

                except Exception as e:
                    logger.error("Erreur import ligne %d ('%s'): %s", row_num, raw_ref, str(e))
                    errors += 1
                    lines.append({
                        'row': row_num,
                        'raw_ref': raw_ref,
                        'raw_qty': raw_qty,
                        'part_id': None,
                        'display_name': None,
                        'internal_ref': None,
                        'status': 'error',
                        'da_status': None,
                        'duplicate_warning': False,
                        'existing_qty': None,
                        'existing_to_qualify': 0,
                        'error': str(e),
                    })

        finally:
            release_connection(conn)

        return {
            'total': len(rows),
            'created': created,
            'skipped': skipped,
            'errors': errors,
            'lines': lines,
        }

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
                    part_id = req.get('part_id')
                    if not stock_item_id and not part_id:
                        cur.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                        errors.append({
                            'purchase_request_id': req_id_str,
                            'item_label': req.get('item_label', ''),
                            'error': "Pièce catalogue non liée — qualifier la demande d'abord",
                        })
                        continue

                    req_quantity = req.get('quantity', 1)
                    stock_item_id_str = str(stock_item_id) if stock_item_id else None
                    part_id_str = str(part_id) if part_id else None

                    # Récupère les fournisseurs : via part_supplier_ref si part_id, sinon stock_item_supplier
                    if part_id_str:
                        cur.execute(
                            """
                            SELECT psr.supplier_id, psr.supplier_ref, psr.unit_price,
                                   psr.is_preferred, s.name AS supplier_name
                            FROM part_supplier_ref psr
                            JOIN part_manufacturer_ref pmr ON pmr.id = psr.part_manufacturer_ref_id
                            LEFT JOIN supplier s ON s.id = psr.supplier_id
                            WHERE pmr.part_id = %s
                            ORDER BY psr.is_preferred DESC, s.name ASC
                            """,
                            (part_id_str,)
                        )
                    else:
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
                            'item_label': req.get('item_label', ''),
                            'error': 'Aucun fournisseur référencé pour cette pièce',
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
                            supplier_ref, unit_price, req_id_str, req_quantity,
                            part_id=part_id_str
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
                                supplier_ref, unit_price, req_id_str, req_quantity,
                                part_id=part_id_str
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
                    raw = str(e)
                    if 'supplier_order_seq' in raw:
                        user_msg = "Séquence de numérotation des commandes manquante (contacter l'admin)"
                    elif 'not-null constraint' in raw and 'stock_item_id' in raw:
                        user_msg = "Référence article manquante sur la ligne de commande"
                    elif 'unique constraint' in raw or 'UniqueViolation' in raw:
                        user_msg = "Cette demande est déjà présente dans un panier fournisseur"
                    elif 'Aucun fournisseur' in raw:
                        user_msg = raw
                    else:
                        user_msg = "Erreur technique lors du dispatch"
                    errors.append({
                        'purchase_request_id': req_id_str,
                        'item_label': req.get('item_label', ''),
                        'error': user_msg,
                        'error_detail': raw,
                    })
                    logger.error(
                        "Error dispatching request %s: %s", req['id'], raw)

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
