"""Requêtes pour le domaine services"""
from typing import Dict, Any, List
from uuid import uuid4

from api.db import get_connection, release_connection
from api.errors.exceptions import DatabaseError, raise_db_error, NotFoundError, ValidationError


class ServiceRepository:
    """Requêtes pour le domaine services"""

    def _get_connection(self):
        return get_connection()

    def get_all(self) -> List[Dict[str, Any]]:
        """Récupère tous les services actifs"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, code, label, is_active
                FROM service
                WHERE is_active = TRUE
                ORDER BY label ASC
            """)
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            raise_db_error(e, "récupération des services")
        finally:
            release_connection(conn)

    def get_by_id(self, service_id: str) -> Dict[str, Any]:
        """Récupère un service par ID"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, code, label, is_active
                FROM service
                WHERE id = %s
            """, (service_id,))
            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Service {service_id} non trouvé")

            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
        except NotFoundError:
            raise
        except Exception as e:
            raise_db_error(e, "récupération du service")
        finally:
            release_connection(conn)

    def create(self, code: str, label: str, is_active: bool = True) -> Dict[str, Any]:
        """Crée un nouveau service"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Vérifier si le code existe déjà
            cur.execute(
                "SELECT id FROM service WHERE code = %s", (code,))
            if cur.fetchone():
                raise ValidationError(
                    f"Un service avec le code '{code}' existe déjà")

            # Générer l'UUID
            new_id = str(uuid4())

            # Créer le service
            cur.execute("""
                INSERT INTO service (id, code, label, is_active)
                VALUES (%s, %s, %s, %s)
                RETURNING id, code, label, is_active
            """, (new_id, code, label, is_active))

            row = cur.fetchone()
            conn.commit()

            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
        except ValidationError:
            raise
        except Exception as e:
            conn.rollback()
            raise_db_error(e, "création du service")
        finally:
            release_connection(conn)

    def update(self, service_id: str, code: str | None = None, label: str | None = None, is_active: bool | None = None) -> Dict[str, Any]:
        """Met à jour un service"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Vérifier que le service existe
            cur.execute(
                "SELECT id FROM service WHERE id = %s", (service_id,))
            if not cur.fetchone():
                raise NotFoundError(f"Service {service_id} non trouvé")

            # Rejeter toute tentative de modification du code
            if code is not None:
                raise ValidationError(
                    "Le code d'un service ne peut pas être modifié")

            # Construire la requête UPDATE
            updates = []
            params = []
            if label is not None:
                updates.append("label = %s")
                params.append(label)
            if is_active is not None:
                updates.append("is_active = %s")
                params.append(is_active)

            if not updates:
                # Aucune mise à jour, retourner l'objet existant
                return self.get_by_id(service_id)

            params.append(service_id)
            query = f"""
                UPDATE service
                SET {', '.join(updates)}
                WHERE id = %s
                RETURNING id, code, label, is_active
            """

            cur.execute(query, tuple(params))
            row = cur.fetchone()
            conn.commit()

            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            conn.rollback()
            raise_db_error(e, "mise à jour du service")
        finally:
            release_connection(conn)
