"""Requêtes pour le domaine classes d'équipement"""
from typing import Dict, Any, List
from uuid import uuid4

from api.settings import settings
from api.errors.exceptions import DatabaseError, NotFoundError, ValidationError


class EquipementClassRepository:
    """Requêtes pour le domaine classes d'équipement"""

    def _get_connection(self):
        """Ouvre une connexion à la base de données via settings"""
        try:
            return settings.get_db_connection()
        except Exception as e:
            raise DatabaseError(
                f"Erreur de connexion base de données: {str(e)}") from e

    def get_all(self) -> List[Dict[str, Any]]:
        """Récupère toutes les classes d'équipement"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, code, label, description
                FROM equipement_class
                ORDER BY code ASC
            """)
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def get_by_id(self, class_id: str) -> Dict[str, Any]:
        """Récupère une classe d'équipement par ID"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, code, label, description
                FROM equipement_class
                WHERE id = %s
            """, (class_id,))
            row = cur.fetchone()
            if not row:
                raise NotFoundError(
                    f"Classe d'équipement {class_id} non trouvée")

            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def create(self, code: str, label: str, description: str | None = None) -> Dict[str, Any]:
        """Crée une nouvelle classe d'équipement"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Vérifier si le code existe déjà
            cur.execute(
                "SELECT id FROM equipement_class WHERE code = %s", (code,))
            if cur.fetchone():
                raise ValidationError(
                    f"Une classe avec le code '{code}' existe déjà")

            # Générer l'UUID
            new_id = str(uuid4())

            # Créer la classe
            cur.execute("""
                INSERT INTO equipement_class (id, code, label, description)
                VALUES (%s, %s, %s, %s)
                RETURNING id, code, label, description
            """, (new_id, code, label, description))

            row = cur.fetchone()
            conn.commit()

            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
        except ValidationError:
            raise
        except Exception as e:
            conn.rollback()
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def update(self, class_id: str, code: str | None = None, label: str | None = None, description: str | None = None) -> Dict[str, Any]:
        """Met à jour une classe d'équipement"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Vérifier que la classe existe
            cur.execute(
                "SELECT id FROM equipement_class WHERE id = %s", (class_id,))
            if not cur.fetchone():
                raise NotFoundError(
                    f"Classe d'équipement {class_id} non trouvée")

            # Si le code change, vérifier l'unicité
            if code:
                cur.execute(
                    "SELECT id FROM equipement_class WHERE code = %s AND id != %s", (code, class_id))
                if cur.fetchone():
                    raise ValidationError(
                        f"Une classe avec le code '{code}' existe déjà")

            # Construire la requête UPDATE
            updates = []
            params = []
            if code is not None:
                updates.append("code = %s")
                params.append(code)
            if label is not None:
                updates.append("label = %s")
                params.append(label)
            if description is not None:
                updates.append("description = %s")
                params.append(description)

            if not updates:
                # Aucune mise à jour, retourner l'objet existant
                return self.get_by_id(class_id)

            params.append(class_id)
            query = f"""
                UPDATE equipement_class
                SET {', '.join(updates)}
                WHERE id = %s
                RETURNING id, code, label, description
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
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def delete(self, class_id: str) -> None:
        """Supprime une classe d'équipement"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Vérifier que la classe existe
            cur.execute(
                "SELECT id FROM equipement_class WHERE id = %s", (class_id,))
            if not cur.fetchone():
                raise NotFoundError(
                    f"Classe d'équipement {class_id} non trouvée")

            # Vérifier qu'aucun équipement n'utilise cette classe
            cur.execute(
                "SELECT COUNT(*) FROM machine WHERE equipement_class_id = %s", (class_id,))
            count = cur.fetchone()[0]
            if count > 0:
                raise ValidationError(
                    f"Impossible de supprimer: {count} équipement(s) utilise(nt) cette classe")

            # Supprimer la classe
            cur.execute(
                "DELETE FROM equipement_class WHERE id = %s", (class_id,))
            conn.commit()
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            conn.rollback()
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()
