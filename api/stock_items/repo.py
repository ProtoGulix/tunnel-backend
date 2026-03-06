from typing import Dict, Any, List, Optional
from uuid import uuid4

from api.settings import settings
from api.db import get_connection, release_connection
from api.errors.exceptions import DatabaseError, NotFoundError


class StockItemRepository:
    """Requêtes pour le domaine stock_item"""

    def _get_connection(self):
        return get_connection()

    def _build_where(
        self,
        family_code: Optional[str],
        sub_family_code: Optional[str],
        search: Optional[str],
        has_supplier: Optional[bool],
        table_alias: str = "si"
    ):
        """Construit la clause WHERE et les paramètres associés"""
        where_clauses = []
        params: List[Any] = []
        a = f"{table_alias}."

        if family_code:
            where_clauses.append(f"{a}family_code = %s")
            params.append(family_code)

        if sub_family_code:
            where_clauses.append(f"{a}sub_family_code = %s")
            params.append(sub_family_code)

        if search:
            where_clauses.append(f"({a}name ILIKE %s OR {a}ref ILIKE %s)")
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern])

        if has_supplier is True:
            where_clauses.append(
                f"EXISTS (SELECT 1 FROM stock_item_supplier sis WHERE sis.stock_item_id = {a}id)"
            )
        elif has_supplier is False:
            where_clauses.append(
                f"NOT EXISTS (SELECT 1 FROM stock_item_supplier sis WHERE sis.stock_item_id = {a}id)"
            )

        where_sql = ("WHERE " + " AND ".join(where_clauses)
                     ) if where_clauses else ""
        return where_sql, params

    def count_all(
        self,
        family_code: Optional[str] = None,
        sub_family_code: Optional[str] = None,
        search: Optional[str] = None,
        has_supplier: Optional[bool] = None
    ) -> int:
        """Compte le nombre total d'articles en stock avec filtres optionnels"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            where_sql, params = self._build_where(
                family_code, sub_family_code, search, has_supplier
            )
            query = f"SELECT COUNT(*) FROM stock_item si {where_sql}"
            cur.execute(query, params)
            result = cur.fetchone()
            return result[0] if result else 0
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            release_connection(conn)

    def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        family_code: Optional[str] = None,
        sub_family_code: Optional[str] = None,
        search: Optional[str] = None,
        has_supplier: Optional[bool] = None,
        sort_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Récupère les articles avec fournisseur préféré embarqué"""
        limit = min(limit, 1000)

        allowed_sort = {'name', 'ref', 'family_code', 'sub_family_code'}
        sort_col = sort_by if sort_by in allowed_sort else 'name'

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            where_sql, params = self._build_where(
                family_code, sub_family_code, search, has_supplier
            )

            query = f"""
                SELECT
                    si.id, si.name, si.ref, si.family_code, si.sub_family_code,
                    si.spec, si.dimension, si.quantity, si.unit, si.location,
                    si.supplier_refs_count,
                    pref.id              AS pref_id,
                    pref.supplier_id     AS pref_supplier_id,
                    s.name               AS pref_supplier_name,
                    pref.supplier_ref    AS pref_supplier_ref,
                    pref.unit_price      AS pref_unit_price,
                    pref.delivery_time_days AS pref_delivery_time_days
                FROM stock_item si
                LEFT JOIN stock_item_supplier pref
                    ON pref.stock_item_id = si.id AND pref.is_preferred = true
                LEFT JOIN supplier s ON s.id = pref.supplier_id
                {where_sql}
                ORDER BY si.{sort_col} ASC
                LIMIT %s OFFSET %s
            """

            cur.execute(query, (*params, limit, offset))
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            results = []
            for row in rows:
                d = dict(zip(cols, row))
                if d.get('pref_supplier_id'):
                    d['preferred_supplier'] = {
                        'supplier_id': d['pref_supplier_id'],
                        'supplier_name': d['pref_supplier_name'],
                        'supplier_ref': d['pref_supplier_ref'],
                        'unit_price': float(d['pref_unit_price']) if d['pref_unit_price'] else None,
                        'delivery_time_days': d['pref_delivery_time_days'],
                    }
                else:
                    d['preferred_supplier'] = None
                for k in ('pref_id', 'pref_supplier_id', 'pref_supplier_name',
                          'pref_supplier_ref', 'pref_unit_price', 'pref_delivery_time_days'):
                    d.pop(k, None)
                results.append(d)
            return results
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            release_connection(conn)

    def get_facets(self, search: Optional[str] = None) -> Dict[str, Any]:
        """
        Retourne les compteurs famille/sous-famille en une seule requête GROUP BY.
        Le filtre search est appliqué si présent ; les filtres famille/sous-famille
        ne sont pas appliqués pour que les facettes reflètent le catalogue complet.
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            params: List[Any] = []
            where_sql = ""

            if search:
                where_sql = "WHERE (si.name ILIKE %s OR si.ref ILIKE %s)"
                search_pattern = f"%{search}%"
                params.extend([search_pattern, search_pattern])

            query = f"""
                SELECT
                    si.family_code,
                    sf.label   AS family_label,
                    si.sub_family_code,
                    ssf.label  AS sub_family_label,
                    COUNT(*)   AS item_count
                FROM stock_item si
                LEFT JOIN stock_family sf ON sf.code = si.family_code
                LEFT JOIN stock_sub_family ssf
                    ON ssf.family_code = si.family_code
                    AND ssf.code = si.sub_family_code
                {where_sql}
                GROUP BY si.family_code, sf.label, si.sub_family_code, ssf.label
                ORDER BY si.family_code, si.sub_family_code
            """

            cur.execute(query, params)
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]

            families: Dict[str, Any] = {}
            for row in rows:
                d = dict(zip(cols, row))
                fc = d['family_code']
                if fc not in families:
                    families[fc] = {
                        'code': fc,
                        'label': d['family_label'],
                        'count': 0,
                        'sub_families': []
                    }
                families[fc]['count'] += d['item_count']
                families[fc]['sub_families'].append({
                    'code': d['sub_family_code'],
                    'label': d['sub_family_label'],
                    'count': d['item_count']
                })

            return {'families': list(families.values())}
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            release_connection(conn)

    def get_by_id(self, item_id: str) -> Dict[str, Any]:
        """Récupère un article par ID avec ses fournisseurs et le template de sous-famille"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Article principal
            cur.execute("SELECT * FROM stock_item WHERE id = %s", (item_id,))
            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Article {item_id} non trouvé")
            cols = [desc[0] for desc in cur.description]
            item = dict(zip(cols, row))

            # Fournisseurs (triés préféré en premier)
            cur.execute(
                """
                SELECT
                    sis.id, sis.supplier_id, s.name AS supplier_name,
                    sis.supplier_ref, sis.unit_price, sis.min_order_quantity,
                    sis.delivery_time_days, sis.is_preferred,
                    mi.id AS mi_id, mi.manufacturer_name, mi.manufacturer_ref
                FROM stock_item_supplier sis
                LEFT JOIN supplier s ON s.id = sis.supplier_id
                LEFT JOIN manufacturer_item mi ON mi.id = sis.manufacturer_item_id
                WHERE sis.stock_item_id = %s
                ORDER BY sis.is_preferred DESC, s.name ASC
                """,
                (item_id,)
            )
            sup_rows = cur.fetchall()
            sup_cols = [desc[0] for desc in cur.description]
            item['suppliers'] = []
            for sup_row in sup_rows:
                s = dict(zip(sup_cols, sup_row))
                if s.get('unit_price') is not None:
                    s['unit_price'] = float(s['unit_price'])
                if s.get('mi_id'):
                    s['manufacturer_item'] = {
                        'id': s['mi_id'],
                        'manufacturer_name': s['manufacturer_name'],
                        'manufacturer_ref': s['manufacturer_ref'],
                    }
                else:
                    s['manufacturer_item'] = None
                del s['mi_id'], s['manufacturer_name'], s['manufacturer_ref']
                item['suppliers'].append(s)

            # Template de la sous-famille
            cur.execute(
                """
                SELECT pt.id, pt.code, pt.version, pt.pattern
                FROM stock_sub_family ssf
                JOIN part_template pt ON pt.id = ssf.template_id
                WHERE ssf.family_code = %s AND ssf.code = %s
                """,
                (item['family_code'], item['sub_family_code'])
            )
            tmpl_row = cur.fetchone()
            if tmpl_row:
                tmpl_cols = [desc[0] for desc in cur.description]
                item['sub_family_template'] = dict(zip(tmpl_cols, tmpl_row))
            else:
                item['sub_family_template'] = None

            # Caractéristiques (template-based uniquement)
            if item.get('template_id'):
                cur.execute(
                    """
                    SELECT sc.field_id, f.field_key AS key, f.label,
                           sc.value_text, sc.value_number, sc.value_enum
                    FROM stock_item_characteristic sc
                    JOIN part_template_field f ON f.id = sc.field_id
                    WHERE sc.stock_item_id = %s
                    ORDER BY f.sort_order, f.field_key
                    """,
                    (item_id,)
                )
                char_rows = cur.fetchall()
                char_cols = [desc[0] for desc in cur.description]
                item['characteristics'] = [
                    dict(zip(char_cols, r)) for r in char_rows]
            else:
                item['characteristics'] = []

            return item
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            release_connection(conn)

    def get_by_ref(self, ref: str) -> Dict[str, Any]:
        """Récupère un article par référence"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id FROM stock_item WHERE ref = %s", (ref,))
            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Article avec référence {ref} non trouvé")
            return self.get_by_id(str(row[0]))
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            release_connection(conn)

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
                 quantity, unit, location, standars_spec)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
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
                    data.get('standars_spec')
                )
            )
            conn.commit()
            return self.get_by_id(item_id)
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la création de l'article: {str(e)}") from e
        finally:
            release_connection(conn)

    def update(self, item_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour un article existant"""
        self.get_by_id(item_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            updatable_fields = [
                'name', 'family_code', 'sub_family_code', 'spec', 'dimension',
                'quantity', 'unit', 'location', 'standars_spec'
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
            """

            cur.execute(query, params)
            conn.commit()
            return self.get_by_id(item_id)
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la mise à jour: {str(e)}") from e
        finally:
            release_connection(conn)

    def delete(self, item_id: str) -> bool:
        """Supprime un article"""
        self.get_by_id(item_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM stock_item WHERE id = %s", (item_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la suppression: {str(e)}") from e
        finally:
            release_connection(conn)

    def update_quantity(self, item_id: str, quantity: int) -> Dict[str, Any]:
        """Met à jour uniquement la quantité d'un article"""
        self.get_by_id(item_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE stock_item
                SET quantity = %s
                WHERE id = %s
                """,
                (quantity, item_id)
            )
            conn.commit()
            return self.get_by_id(item_id)
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la mise à jour de la quantité: {str(e)}") from e
        finally:
            release_connection(conn)
