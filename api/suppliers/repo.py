from typing import Dict, Any, List, Optional
from uuid import uuid4

from api.settings import settings
from api.errors.exceptions import DatabaseError, NotFoundError


class SupplierRepository:
    """Requêtes pour le domaine supplier"""

    def _get_connection(self):
        """Ouvre une connexion à la base de données via settings"""
        try:
            return settings.get_db_connection()
        except Exception as e:
            raise DatabaseError(
                f"Erreur de connexion base de données: {str(e)}") from e

    def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Récupère tous les fournisseurs avec filtres optionnels"""
        limit = min(limit, 1000)

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            where_clauses = []
            params: List[Any] = []

            if is_active is not None:
                where_clauses.append("is_active = %s")
                params.append(is_active)

            if search:
                where_clauses.append(
                    "(name ILIKE %s OR code ILIKE %s OR contact_name ILIKE %s)")
                search_pattern = f"%{search}%"
                params.extend([search_pattern, search_pattern, search_pattern])

            where_sql = ("WHERE " + " AND ".join(where_clauses)
                         ) if where_clauses else ""

            query = f"""
                SELECT id, name, code, contact_name, email, phone, is_active
                FROM supplier
                {where_sql}
                ORDER BY name ASC
                LIMIT %s OFFSET %s
            """

            cur.execute(query, (*params, limit, offset))
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]

            return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def get_by_id(self, supplier_id: str) -> Dict[str, Any]:
        """Récupère un fournisseur par ID"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM supplier WHERE id = %s",
                (supplier_id,)
            )
            row = cur.fetchone()

            if not row:
                raise NotFoundError(f"Fournisseur {supplier_id} non trouvé")

            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def get_by_code(self, code: str) -> Dict[str, Any]:
        """Récupère un fournisseur par code"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM supplier WHERE code = %s",
                (code,)
            )
            row = cur.fetchone()

            if not row:
                raise NotFoundError(f"Fournisseur avec code {code} non trouvé")

            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def add(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée un nouveau fournisseur"""
        # Validation 1: Nom >= 2 caractères (après trim)
        name = (data.get('name') or '').strip()
        if not name or len(name) < 2:
            raise ValueError("Le nom doit contenir au moins 2 caractères")

        data['name'] = name

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Validation 2: Vérification doublon (nom unique)
            cur.execute(
                "SELECT id FROM supplier WHERE name = %s",
                (name,)
            )
            if cur.fetchone():
                raise ValueError(f"Le fournisseur '{name}' existe déjà")

            supplier_id = str(uuid4())

            cur.execute(
                """
                INSERT INTO supplier
                (id, name, code, contact_name, email, phone, address, notes, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    supplier_id,
                    name,
                    data.get('code'),
                    data.get('contact_name'),
                    data.get('email'),
                    data.get('phone'),
                    data.get('address'),
                    data.get('notes'),
                    data.get('is_active', True)
                )
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la création du fournisseur: {str(e)}") from e
        finally:
            conn.close()

        return self.get_by_id(supplier_id)

    def update(self, supplier_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour un fournisseur existant"""
        # Vérifie que le fournisseur existe
        self.get_by_id(supplier_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Champs modifiables
            updatable_fields = [
                'name', 'code', 'contact_name', 'email', 'phone',
                'address', 'notes', 'is_active'
            ]

            set_clauses = []
            params = []

            for field in updatable_fields:
                if field in data:
                    set_clauses.append(f"{field} = %s")
                    params.append(data[field])

            if not set_clauses:
                return self.get_by_id(supplier_id)

            params.append(supplier_id)

            query = f"""
                UPDATE supplier
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

        return self.get_by_id(supplier_id)

    def delete(self, supplier_id: str) -> bool:
        """Supprime un fournisseur"""
        # Vérifie que le fournisseur existe
        self.get_by_id(supplier_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Validation: Vérifier qu'il n'a pas de références
            cur.execute(
                "SELECT COUNT(*) FROM stock_item_supplier WHERE supplier_id = %s",
                (supplier_id,)
            )
            ref_count = cur.fetchone()[0]

            if ref_count > 0:
                raise ValueError(
                    f"Ce fournisseur possède {ref_count} référence(s). Supprimez-les d'abord."
                )

            cur.execute(
                "DELETE FROM supplier WHERE id = %s", (supplier_id,))
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
