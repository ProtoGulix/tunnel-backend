from typing import Dict, Any, List, Optional
from uuid import uuid4
from decimal import Decimal

from api.settings import settings
from api.errors.exceptions import DatabaseError, NotFoundError


class StockItemSupplierRepository:
    """Requêtes pour le domaine stock_item_supplier"""

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

    def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        stock_item_id: Optional[str] = None,
        supplier_id: Optional[str] = None,
        is_preferred: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Récupère toutes les références fournisseurs avec filtres optionnels"""
        limit = min(limit, 1000)

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            where_clauses = []
            params: List[Any] = []

            if stock_item_id:
                where_clauses.append("sis.stock_item_id = %s")
                params.append(stock_item_id)

            if supplier_id:
                where_clauses.append("sis.supplier_id = %s")
                params.append(supplier_id)

            if is_preferred is not None:
                where_clauses.append("sis.is_preferred = %s")
                params.append(is_preferred)

            where_sql = ("WHERE " + " AND ".join(where_clauses)
                         ) if where_clauses else ""

            query = f"""
                SELECT
                    sis.id, sis.stock_item_id, sis.supplier_id, sis.supplier_ref,
                    sis.unit_price, sis.min_order_quantity, sis.delivery_time_days,
                    sis.is_preferred,
                    si.name as stock_item_name, si.ref as stock_item_ref,
                    s.name as supplier_name, s.code as supplier_code
                FROM stock_item_supplier sis
                LEFT JOIN stock_item si ON sis.stock_item_id = si.id
                LEFT JOIN supplier s ON sis.supplier_id = s.id
                {where_sql}
                ORDER BY sis.is_preferred DESC, s.name ASC
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

    def get_by_id(self, ref_id: str) -> Dict[str, Any]:
        """Récupère une référence fournisseur par ID"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    sis.*,
                    si.name as stock_item_name, si.ref as stock_item_ref,
                    s.name as supplier_name, s.code as supplier_code
                FROM stock_item_supplier sis
                LEFT JOIN stock_item si ON sis.stock_item_id = si.id
                LEFT JOIN supplier s ON sis.supplier_id = s.id
                WHERE sis.id = %s
                """,
                (ref_id,)
            )
            row = cur.fetchone()

            if not row:
                raise NotFoundError(
                    f"Référence fournisseur {ref_id} non trouvée")

            cols = [desc[0] for desc in cur.description]
            return self._convert_decimals(dict(zip(cols, row)))
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def get_by_stock_item(self, stock_item_id: str) -> List[Dict[str, Any]]:
        """Récupère toutes les références fournisseurs d'un article"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    sis.*,
                    si.name as stock_item_name, si.ref as stock_item_ref,
                    s.name as supplier_name, s.code as supplier_code
                FROM stock_item_supplier sis
                LEFT JOIN stock_item si ON sis.stock_item_id = si.id
                LEFT JOIN supplier s ON sis.supplier_id = s.id
                WHERE sis.stock_item_id = %s
                ORDER BY sis.is_preferred DESC, s.name ASC
                """,
                (stock_item_id,)
            )
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]

            return [self._convert_decimals(dict(zip(cols, row))) for row in rows]
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def get_by_supplier(self, supplier_id: str) -> List[Dict[str, Any]]:
        """Récupère toutes les références fournisseurs d'un fournisseur"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    sis.*,
                    si.name as stock_item_name, si.ref as stock_item_ref,
                    s.name as supplier_name, s.code as supplier_code
                FROM stock_item_supplier sis
                LEFT JOIN stock_item si ON sis.stock_item_id = si.id
                LEFT JOIN supplier s ON sis.supplier_id = s.id
                WHERE sis.supplier_id = %s
                ORDER BY si.name ASC
                """,
                (supplier_id,)
            )
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]

            return [self._convert_decimals(dict(zip(cols, row))) for row in rows]
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def add(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une nouvelle référence fournisseur"""
        # Validation 1: stock_item_id obligatoire
        if not data.get('stock_item_id'):
            raise ValueError("L'article est obligatoire")

        # Validation 2: supplier_id obligatoire
        if not data.get('supplier_id'):
            raise ValueError("Le fournisseur est obligatoire")

        # Validation 3: supplier_ref >= 2 caractères (après trim)
        supplier_ref = (data.get('supplier_ref') or '').strip()
        if not supplier_ref or len(supplier_ref) < 2:
            raise ValueError(
                "La référence doit contenir au moins 2 caractères")

        data['supplier_ref'] = supplier_ref

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            ref_id = str(uuid4())

            # Validation 4: Vérification doublon (stock_item + supplier + ref)
            cur.execute(
                """
                SELECT id FROM stock_item_supplier
                WHERE stock_item_id = %s AND supplier_id = %s AND supplier_ref = %s
                """,
                (str(data['stock_item_id']), str(
                    data['supplier_id']), supplier_ref)
            )
            if cur.fetchone():
                raise ValueError(
                    "Cette référence existe déjà pour ce fournisseur")

            # Si is_preferred = true, désactive les autres préférés pour cet article
            if data.get('is_preferred') is True:
                cur.execute(
                    """
                    UPDATE stock_item_supplier
                    SET is_preferred = false
                    WHERE stock_item_id = %s AND is_preferred = true
                    """,
                    (str(data['stock_item_id']),)
                )

            cur.execute(
                """
                INSERT INTO stock_item_supplier
                (id, stock_item_id, supplier_id, supplier_ref, unit_price,
                 min_order_quantity, delivery_time_days, is_preferred, manufacturer_item_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    ref_id,
                    str(data['stock_item_id']),
                    str(data['supplier_id']),
                    data['supplier_ref'],
                    data.get('unit_price'),
                    data.get('min_order_quantity', 1),
                    data.get('delivery_time_days'),
                    data.get('is_preferred', False),
                    str(data['manufacturer_item_id']) if data.get(
                        'manufacturer_item_id') else None
                )
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la création de la référence fournisseur: {str(e)}") from e
        finally:
            conn.close()

        return self.get_by_id(ref_id)

    def update(self, ref_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour une référence fournisseur existante"""
        # Vérifie que la référence existe
        existing = self.get_by_id(ref_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Si is_preferred = true, désactive les autres préférés pour cet article
            if data.get('is_preferred') is True:
                stock_item_id = data.get(
                    'stock_item_id', existing['stock_item_id'])
                cur.execute(
                    """
                    UPDATE stock_item_supplier
                    SET is_preferred = false
                    WHERE stock_item_id = %s AND is_preferred = true AND id != %s
                    """,
                    (str(stock_item_id), ref_id)
                )

            # Champs modifiables
            updatable_fields = [
                'stock_item_id', 'supplier_id', 'supplier_ref', 'unit_price',
                'min_order_quantity', 'delivery_time_days', 'is_preferred',
                'manufacturer_item_id'
            ]

            set_clauses = []
            params = []

            for field in updatable_fields:
                if field in data:
                    set_clauses.append(f"{field} = %s")
                    value = data[field]
                    if field in ['stock_item_id', 'supplier_id', 'manufacturer_item_id'] and value:
                        value = str(value)
                    params.append(value)

            if not set_clauses:
                return self.get_by_id(ref_id)

            params.append(ref_id)

            query = f"""
                UPDATE stock_item_supplier
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

        return self.get_by_id(ref_id)

    def delete(self, ref_id: str) -> bool:
        """Supprime une référence fournisseur"""
        # Vérifie que la référence existe
        ref = self.get_by_id(ref_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Validation: Si préféré, vérifier qu'il y a d'autres références
            if ref.get('is_preferred'):
                cur.execute(
                    """
                    SELECT COUNT(*) FROM stock_item_supplier
                    WHERE stock_item_id = %s AND id != %s
                    """,
                    (str(ref['stock_item_id']), ref_id)
                )
                other_count = cur.fetchone()[0]

                if other_count > 0:
                    raise ValueError(
                        "Définissez un autre fournisseur préféré avant de supprimer")

            cur.execute(
                "DELETE FROM stock_item_supplier WHERE id = %s", (ref_id,))
            conn.commit()
            return True
        except ValueError:
            raise
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la suppression: {str(e)}") from e
        finally:
            conn.close()

    def set_preferred(self, ref_id: str) -> Dict[str, Any]:
        """Définit une référence comme préférée (et désactive les autres)"""
        existing = self.get_by_id(ref_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Désactive tous les préférés pour cet article
            cur.execute(
                """
                UPDATE stock_item_supplier
                SET is_preferred = false
                WHERE stock_item_id = %s
                """,
                (str(existing['stock_item_id']),)
            )

            # Active le préféré pour cette référence
            cur.execute(
                """
                UPDATE stock_item_supplier
                SET is_preferred = true
                WHERE id = %s
                """,
                (ref_id,)
            )

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la mise à jour du préféré: {str(e)}") from e
        finally:
            conn.close()

        return self.get_by_id(ref_id)
