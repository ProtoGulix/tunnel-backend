from typing import Dict, Any, List, Optional
from uuid import uuid4
from decimal import Decimal

from api.settings import settings
from api.errors.exceptions import DatabaseError, NotFoundError


class SupplierOrderLineRepository:
    """Requêtes pour le domaine supplier_order_line"""

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

    def _enrich_with_stock_item(self, line_dict: Dict[str, Any], conn) -> Dict[str, Any]:
        """Enrichit une ligne avec les détails du stock_item"""
        stock_item_id = line_dict.get('stock_item_id')
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
                    line_dict['stock_item'] = dict(zip(cols, row))
                else:
                    line_dict['stock_item'] = None
            except Exception:
                line_dict['stock_item'] = None
        else:
            line_dict['stock_item'] = None
        return line_dict

    def _get_linked_purchase_requests(self, line_id: str, conn) -> List[Dict[str, Any]]:
        """Récupère les demandes d'achat liées à une ligne"""
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    solpr.id, solpr.purchase_request_id, solpr.quantity_fulfilled as quantity, solpr.created_at,
                    pr.item_label, pr.requester_name, pr.intervention_id
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

    def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        supplier_order_id: Optional[str] = None,
        stock_item_id: Optional[str] = None,
        is_selected: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Récupère toutes les lignes de commande avec filtres optionnels"""
        limit = min(limit, 1000)

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            where_clauses = []
            params: List[Any] = []

            if supplier_order_id:
                where_clauses.append("sol.supplier_order_id = %s")
                params.append(supplier_order_id)

            if stock_item_id:
                where_clauses.append("sol.stock_item_id = %s")
                params.append(stock_item_id)

            if is_selected is not None:
                where_clauses.append("sol.is_selected = %s")
                params.append(is_selected)

            where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

            query = f"""
                SELECT
                    sol.id, sol.supplier_order_id, sol.stock_item_id,
                    sol.quantity, sol.unit_price, sol.total_price,
                    sol.quantity_received, sol.is_selected,
                    si.name as stock_item_name, si.ref as stock_item_ref,
                    (SELECT COUNT(*) FROM supplier_order_line_purchase_request
                     WHERE supplier_order_line_id = sol.id) as purchase_request_count
                FROM supplier_order_line sol
                LEFT JOIN stock_item si ON sol.stock_item_id = si.id
                {where_sql}
                ORDER BY sol.created_at DESC
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

    def get_by_id(self, line_id: str) -> Dict[str, Any]:
        """Récupère une ligne par ID avec stock_item et purchase_requests"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM supplier_order_line WHERE id = %s",
                (line_id,)
            )
            row = cur.fetchone()

            if not row:
                raise NotFoundError(f"Ligne de commande {line_id} non trouvée")

            cols = [desc[0] for desc in cur.description]
            result = self._convert_decimals(dict(zip(cols, row)))

            # Enrichit avec stock_item
            result = self._enrich_with_stock_item(result, conn)

            # Ajoute les purchase_requests liées
            result['purchase_requests'] = self._get_linked_purchase_requests(line_id, conn)

            return result
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def get_by_order(self, supplier_order_id: str) -> List[Dict[str, Any]]:
        """Récupère toutes les lignes d'une commande avec détails"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM supplier_order_line WHERE supplier_order_id = %s ORDER BY created_at ASC",
                (supplier_order_id,)
            )
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]

            results = []
            for row in rows:
                line = self._convert_decimals(dict(zip(cols, row)))
                line = self._enrich_with_stock_item(line, conn)
                line['purchase_requests'] = self._get_linked_purchase_requests(str(line['id']), conn)
                results.append(line)

            return results
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def add(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une nouvelle ligne de commande"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            line_id = str(uuid4())

            # Note: total_price est calculé par trigger
            cur.execute(
                """
                INSERT INTO supplier_order_line
                (id, supplier_order_id, stock_item_id, supplier_ref_snapshot,
                 quantity, unit_price, notes, quote_received, is_selected,
                 quote_price, manufacturer, manufacturer_ref, quote_received_at,
                 rejected_reason, lead_time_days)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    line_id,
                    data['supplier_order_id'],
                    data['stock_item_id'],
                    data.get('supplier_ref_snapshot'),
                    data['quantity'],
                    data.get('unit_price'),
                    data.get('notes'),
                    data.get('quote_received'),
                    data.get('is_selected'),
                    data.get('quote_price'),
                    data.get('manufacturer'),
                    data.get('manufacturer_ref'),
                    data.get('quote_received_at'),
                    data.get('rejected_reason'),
                    data.get('lead_time_days')
                )
            )

            # Gère les liens avec purchase_requests si fournis
            purchase_requests = data.get('purchase_requests')
            if purchase_requests:
                for pr_link in purchase_requests:
                    qty = pr_link.get('quantity_fulfilled', pr_link.get('quantity', 1))
                    cur.execute(
                        """
                        INSERT INTO supplier_order_line_purchase_request
                        (id, supplier_order_line_id, purchase_request_id, quantity_fulfilled)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            str(uuid4()),
                            line_id,
                            str(pr_link['purchase_request_id']),
                            qty
                        )
                    )

                # Règle métier: une seule ligne sélectionnée par purchase_request
                # Si is_selected = true, désélectionne les autres lignes liées aux mêmes PR
                if data.get('is_selected') is True:
                    pr_ids = [str(pr['purchase_request_id']) for pr in purchase_requests]
                    cur.execute(
                        """
                        UPDATE supplier_order_line
                        SET is_selected = false
                        WHERE id != %s
                        AND id IN (
                            SELECT DISTINCT supplier_order_line_id
                            FROM supplier_order_line_purchase_request
                            WHERE purchase_request_id = ANY(%s)
                        )
                        """,
                        (line_id, pr_ids)
                    )

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la création de la ligne: {str(e)}") from e
        finally:
            conn.close()

        return self.get_by_id(line_id)

    def update(self, line_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour une ligne de commande existante"""
        # Vérifie que la ligne existe
        self.get_by_id(line_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Champs modifiables
            updatable_fields = [
                'supplier_ref_snapshot', 'quantity', 'unit_price', 'quantity_received',
                'notes', 'quote_received', 'is_selected', 'quote_price',
                'manufacturer', 'manufacturer_ref', 'quote_received_at',
                'rejected_reason', 'lead_time_days'
            ]

            set_clauses = []
            params = []

            for field in updatable_fields:
                if field in data:
                    set_clauses.append(f"{field} = %s")
                    params.append(data[field])

            if set_clauses:
                params.append(line_id)
                query = f"""
                    UPDATE supplier_order_line
                    SET {', '.join(set_clauses)}
                    WHERE id = %s
                """
                cur.execute(query, params)

            # Règle métier: une seule ligne sélectionnée par purchase_request
            # Si is_selected = true, désélectionne les autres lignes liées aux mêmes PR
            if data.get('is_selected') is True:
                cur.execute(
                    """
                    UPDATE supplier_order_line
                    SET is_selected = false
                    WHERE id != %s
                    AND id IN (
                        SELECT DISTINCT sol2.id
                        FROM supplier_order_line sol2
                        JOIN supplier_order_line_purchase_request solpr2 ON sol2.id = solpr2.supplier_order_line_id
                        WHERE solpr2.purchase_request_id IN (
                            SELECT purchase_request_id
                            FROM supplier_order_line_purchase_request
                            WHERE supplier_order_line_id = %s
                        )
                    )
                    """,
                    (line_id, line_id)
                )

            # Met à jour les liens purchase_requests si fournis
            if 'purchase_requests' in data:
                # Supprime les liens existants
                cur.execute(
                    "DELETE FROM supplier_order_line_purchase_request WHERE supplier_order_line_id = %s",
                    (line_id,)
                )

                # Ajoute les nouveaux liens
                purchase_requests = data.get('purchase_requests') or []
                for pr_link in purchase_requests:
                    qty = pr_link.get('quantity_fulfilled', pr_link.get('quantity', 1))
                    cur.execute(
                        """
                        INSERT INTO supplier_order_line_purchase_request
                        (id, supplier_order_line_id, purchase_request_id, quantity_fulfilled)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            str(uuid4()),
                            line_id,
                            str(pr_link['purchase_request_id']),
                            qty
                        )
                    )

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la mise à jour: {str(e)}") from e
        finally:
            conn.close()

        return self.get_by_id(line_id)

    def delete(self, line_id: str) -> bool:
        """Supprime une ligne de commande (cascade sur M2M)"""
        # Vérifie que la ligne existe
        self.get_by_id(line_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM supplier_order_line WHERE id = %s", (line_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la suppression: {str(e)}") from e
        finally:
            conn.close()

    def link_purchase_request(
        self,
        line_id: str,
        purchase_request_id: str,
        quantity_fulfilled: int
    ) -> Dict[str, Any]:
        """Lie une demande d'achat à une ligne de commande"""
        # Vérifie que la ligne existe
        self.get_by_id(line_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO supplier_order_line_purchase_request
                (id, supplier_order_line_id, purchase_request_id, quantity_fulfilled)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (supplier_order_line_id, purchase_request_id)
                DO UPDATE SET quantity_fulfilled = EXCLUDED.quantity_fulfilled
                """,
                (str(uuid4()), line_id, purchase_request_id, quantity_fulfilled)
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la liaison: {str(e)}") from e
        finally:
            conn.close()

        return self.get_by_id(line_id)

    def unlink_purchase_request(self, line_id: str, purchase_request_id: str) -> Dict[str, Any]:
        """Retire le lien avec une demande d'achat"""
        # Vérifie que la ligne existe
        self.get_by_id(line_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                DELETE FROM supplier_order_line_purchase_request
                WHERE supplier_order_line_id = %s AND purchase_request_id = %s
                """,
                (line_id, purchase_request_id)
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la suppression du lien: {str(e)}") from e
        finally:
            conn.close()

        return self.get_by_id(line_id)
