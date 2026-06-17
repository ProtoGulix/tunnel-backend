from typing import Any, Dict, List, Optional

from api.db import get_connection, release_connection
from api.errors.exceptions import NotFoundError, raise_db_error
from api.utils.sanitizer import strip_html


class PartRepository:
    """Requêtes pour le domaine part (catalogue pièces V4)"""

    def get_all(
        self,
        limit: int = 50,
        offset: int = 0,
        family_code: Optional[str] = None,
        sub_family_code: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Liste les pièces avec leur référence fabricant préférée"""
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                where_clauses = []
                params: List[Any] = []

                if family_code:
                    where_clauses.append("p.family_code = %s")
                    params.append(family_code)

                if sub_family_code:
                    where_clauses.append("p.sub_family_code = %s")
                    params.append(sub_family_code)

                if search:
                    where_clauses.append(
                        "(p.internal_ref ILIKE %s OR pmr.manufacturer_ref ILIKE %s OR pmr.label ILIKE %s)"
                    )
                    pattern = f"%{search}%"
                    params.extend([pattern, pattern, pattern])

                where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

                cur.execute(
                    f"""
                    SELECT
                        p.id, p.internal_ref, p.family_code, p.sub_family_code,
                        p.unit, p.location, p.qty_in_stock,
                        pmr.manufacturer_name  AS preferred_manufacturer_name,
                        pmr.manufacturer_ref   AS preferred_manufacturer_ref,
                        pmr.label              AS preferred_label
                    FROM part p
                    LEFT JOIN part_manufacturer_ref pmr
                        ON pmr.part_id = p.id AND pmr.is_preferred = true
                    {where_sql}
                    ORDER BY p.internal_ref ASC
                    LIMIT %s OFFSET %s
                    """,
                    (*params, limit, offset),
                )
                rows = cur.fetchall()
                cols = [desc[0] for desc in cur.description]
                return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            raise_db_error(e, "liste des pièces")
        finally:
            if conn:
                release_connection(conn)

    def count_all(
        self,
        family_code: Optional[str] = None,
        sub_family_code: Optional[str] = None,
        search: Optional[str] = None,
    ) -> int:
        """Compte le total de pièces pour la pagination"""
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                where_clauses = []
                params: List[Any] = []

                if family_code:
                    where_clauses.append("p.family_code = %s")
                    params.append(family_code)

                if sub_family_code:
                    where_clauses.append("p.sub_family_code = %s")
                    params.append(sub_family_code)

                if search:
                    where_clauses.append(
                        "(p.internal_ref ILIKE %s OR pmr.manufacturer_ref ILIKE %s OR pmr.label ILIKE %s)"
                    )
                    pattern = f"%{search}%"
                    params.extend([pattern, pattern, pattern])

                where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

                cur.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM part p
                    LEFT JOIN part_manufacturer_ref pmr
                        ON pmr.part_id = p.id AND pmr.is_preferred = true
                    {where_sql}
                    """,
                    params,
                )
                return cur.fetchone()[0]
        except Exception as e:
            raise_db_error(e, "comptage des pièces")
        finally:
            if conn:
                release_connection(conn)

    def get_by_id(self, part_id: str) -> Dict[str, Any]:
        """Récupère une pièce avec toutes ses références fabricant et fournisseur"""
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, internal_ref, family_code, sub_family_code,
                           unit, location, qty_in_stock, created_at, updated_at
                    FROM part WHERE id = %s
                    """,
                    (part_id,),
                )
                row = cur.fetchone()
                if not row:
                    raise NotFoundError(f"Pièce {part_id} non trouvée")

                cols = [desc[0] for desc in cur.description]
                part = dict(zip(cols, row))

                cur.execute(
                    """
                    SELECT pmr.id, pmr.part_id, pmr.manufacturer_name, pmr.manufacturer_ref,
                           pmr.label, pmr.is_preferred, pmr.created_at, pmr.updated_at,
                           COALESCE(
                               json_agg(
                                   json_build_object(
                                       'id', psr.id,
                                       'part_manufacturer_ref_id', psr.part_manufacturer_ref_id,
                                       'supplier_id', psr.supplier_id,
                                       'supplier_name', s.name,
                                       'supplier_ref', psr.supplier_ref,
                                       'unit_price', psr.unit_price,
                                       'min_order_quantity', psr.min_order_quantity,
                                       'delivery_time_days', psr.delivery_time_days,
                                       'is_preferred', psr.is_preferred,
                                       'product_url', psr.product_url,
                                       'created_at', psr.created_at,
                                       'updated_at', psr.updated_at
                                   ) ORDER BY psr.is_preferred DESC, psr.created_at ASC
                               ) FILTER (WHERE psr.id IS NOT NULL),
                               '[]'
                           ) AS supplier_refs
                    FROM part_manufacturer_ref pmr
                    LEFT JOIN part_supplier_ref psr ON psr.part_manufacturer_ref_id = pmr.id
                    LEFT JOIN supplier s ON s.id = psr.supplier_id
                    WHERE pmr.part_id = %s
                    GROUP BY pmr.id
                    ORDER BY pmr.is_preferred DESC, pmr.created_at ASC
                    """,
                    (part_id,),
                )
                mfr_rows = cur.fetchall()
                mfr_cols = [desc[0] for desc in cur.description]
                part["manufacturer_refs"] = [dict(zip(mfr_cols, r)) for r in mfr_rows]

                return part
        except NotFoundError:
            raise
        except Exception as e:
            raise_db_error(e, "récupération de la pièce")
        finally:
            if conn:
                release_connection(conn)

    def get_by_internal_ref(self, internal_ref: str) -> Dict[str, Any]:
        """Récupère une pièce par sa référence interne (P000001)"""
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM part WHERE internal_ref = %s",
                    (internal_ref,),
                )
                row = cur.fetchone()
                if not row:
                    raise NotFoundError(f"Pièce {internal_ref} non trouvée")
                return self.get_by_id(str(row[0]))
        except NotFoundError:
            raise
        except Exception as e:
            raise_db_error(e, "récupération par référence interne")
        finally:
            if conn:
                release_connection(conn)

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une nouvelle pièce (internal_ref générée automatiquement)"""
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO part (family_code, sub_family_code, unit, location, qty_in_stock)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        data["family_code"],
                        data["sub_family_code"],
                        data.get("unit"),
                        strip_html(data.get("location") or ""),
                        data.get("qty_in_stock", 0),
                    ),
                )
                part_id = str(cur.fetchone()[0])
            conn.commit()
            return self.get_by_id(part_id)
        except Exception as e:
            if conn:
                conn.rollback()
            raise_db_error(e, "création de la pièce")
        finally:
            if conn:
                release_connection(conn)

    def update(self, part_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour une pièce (PATCH partiel)"""
        self.get_by_id(part_id)

        updatable = ["family_code", "sub_family_code", "unit", "location", "qty_in_stock"]
        set_clauses = []
        params: List[Any] = []

        for field in updatable:
            if field in data and data[field] is not None:
                set_clauses.append(f"{field} = %s")
                value = strip_html(data[field]) if field == "location" else data[field]
                params.append(value)

        if not set_clauses:
            return self.get_by_id(part_id)

        params.append(part_id)
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE part SET {', '.join(set_clauses)} WHERE id = %s",
                    params,
                )
            conn.commit()
            return self.get_by_id(part_id)
        except Exception as e:
            if conn:
                conn.rollback()
            raise_db_error(e, "mise à jour de la pièce")
        finally:
            if conn:
                release_connection(conn)

    def add_manufacturer_ref(self, part_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ajoute une référence fabricant à une pièce"""
        self.get_by_id(part_id)

        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                if data.get("is_preferred"):
                    cur.execute(
                        "UPDATE part_manufacturer_ref SET is_preferred = false WHERE part_id = %s",
                        (part_id,),
                    )
                cur.execute(
                    """
                    INSERT INTO part_manufacturer_ref
                        (part_id, manufacturer_name, manufacturer_ref, label, is_preferred)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        part_id,
                        data["manufacturer_name"],
                        data["manufacturer_ref"],
                        strip_html(data.get("label") or ""),
                        data.get("is_preferred", False),
                    ),
                )
            conn.commit()
            return self.get_by_id(part_id)
        except Exception as e:
            if conn:
                conn.rollback()
            raise_db_error(e, "ajout référence fabricant")
        finally:
            if conn:
                release_connection(conn)

    def add_supplier_ref(self, part_id: str, mfr_ref_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ajoute une référence fournisseur à une référence fabricant"""
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM part_manufacturer_ref WHERE id = %s AND part_id = %s",
                    (mfr_ref_id, part_id),
                )
                if not cur.fetchone():
                    raise NotFoundError(f"Référence fabricant {mfr_ref_id} non trouvée pour la pièce {part_id}")

                if data.get("is_preferred"):
                    cur.execute(
                        "UPDATE part_supplier_ref SET is_preferred = false WHERE part_manufacturer_ref_id = %s",
                        (mfr_ref_id,),
                    )

                cur.execute(
                    """
                    INSERT INTO part_supplier_ref
                        (part_manufacturer_ref_id, supplier_id, supplier_ref,
                         unit_price, min_order_quantity, delivery_time_days, is_preferred, product_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        mfr_ref_id,
                        str(data["supplier_id"]),
                        data["supplier_ref"],
                        data.get("unit_price"),
                        data.get("min_order_quantity", 1),
                        data.get("delivery_time_days"),
                        data.get("is_preferred", False),
                        data.get("product_url"),
                    ),
                )
            conn.commit()
            return self.get_by_id(part_id)
        except NotFoundError:
            raise
        except Exception as e:
            if conn:
                conn.rollback()
            raise_db_error(e, "ajout référence fournisseur")
        finally:
            if conn:
                release_connection(conn)
