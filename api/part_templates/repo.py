import logging
from typing import List, Dict, Any
from uuid import uuid4

from api.settings import settings
from api.errors.exceptions import DatabaseError, NotFoundError, ValidationError
from api.part_templates.schemas import PartTemplateIn, PartTemplateUpdate

logger = logging.getLogger(__name__)


class PartTemplateRepository:
    """Requêtes pour le domaine part_template"""

    def _get_connection(self):
        """Ouvre une connexion à la base de données"""
        try:
            return settings.get_db_connection()
        except Exception as e:
            raise DatabaseError(
                "Erreur de connexion base de données: %s" % str(e)) from e

    def get_all(self) -> List[Dict[str, Any]]:
        """Récupère tous les templates (dernière version de chaque)"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT DISTINCT ON (id) 
                    id, code, version, pattern
                FROM part_template
                ORDER BY id, version DESC
                """
            )
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            logger.error(
                "Erreur lors de la récupération des templates: %s", str(e))
            raise DatabaseError(
                "Erreur lors de la récupération des templates: %s" % str(e)) from e
        finally:
            conn.close()

    def get_by_id_with_fields(self, template_id: str, version: int = None) -> Dict[str, Any]:
        """
        Récupère un template complet avec ses fields et enum_values
        Si version est None, retourne la version la plus récente

        CETTE méthode est la SOURCE DE VÉRITÉ pour charger un template complet.
        Utilisée par TemplateService.load_template()
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Récupération du template
            if version is None:
                cur.execute(
                    """
                    SELECT id, code, version, label, pattern, is_active
                    FROM part_template
                    WHERE id = %s
                    ORDER BY version DESC
                    LIMIT 1
                    """,
                    (template_id,)
                )
            else:
                cur.execute(
                    """
                    SELECT id, code, version, label, pattern, is_active
                    FROM part_template
                    WHERE id = %s AND version = %s
                    """,
                    (template_id, version)
                )

            template_row = cur.fetchone()
            if not template_row:
                raise NotFoundError(
                    "Template %s version %s non trouvé" % (template_id, version))

            template_cols = [desc[0] for desc in cur.description]
            template_data = dict(zip(template_cols, template_row))

            # Récupération des champs pour ce template_id
            cur.execute(
                """
                SELECT id, field_key, label, field_type, unit, required, sort_order
                FROM part_template_field
                WHERE template_id = %s
                ORDER BY sort_order, field_key
                """,
                (str(template_id),)
            )

            field_rows = cur.fetchall()
            field_cols = [desc[0] for desc in cur.description]
            fields_data = [dict(zip(field_cols, row)) for row in field_rows]

            # Pour chaque champ de type enum, récupérer les valeurs possibles
            fields = []
            for field_data in fields_data:
                field_dict = dict(field_data)
                field_id = field_dict.pop('id')  # Retirer l'id interne

                # Convertir field_key → key pour matcher le schéma de réponse
                field_dict['key'] = field_dict.pop('field_key')

                if field_data['field_type'] == 'enum':
                    cur.execute(
                        """
                        SELECT value, label
                        FROM part_template_field_enum
                        WHERE field_id = %s
                        ORDER BY value
                        """,
                        (field_id,)
                    )
                    enum_rows = cur.fetchall()
                    enum_cols = [desc[0] for desc in cur.description]
                    field_dict['enum_values'] = [
                        dict(zip(enum_cols, enum_row))
                        for enum_row in enum_rows
                    ]
                else:
                    field_dict['enum_values'] = None

                fields.append(field_dict)

            template_data['fields'] = fields
            return template_data

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(
                "Erreur lors de la récupération du template: %s", str(e))
            raise DatabaseError(
                "Erreur lors de la récupération du template: %s" % str(e)) from e
        finally:
            conn.close()

    def get_by_id(self, template_id: str, version: int = None) -> Dict[str, Any]:
        """
        Récupère un template par ID
        Si version est None, retourne la version la plus récente
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            if version is None:
                cur.execute(
                    """
                    SELECT id, code, version, pattern
                    FROM part_template
                    WHERE id = %s
                    ORDER BY version DESC
                    LIMIT 1
                    """,
                    (template_id,)
                )
            else:
                cur.execute(
                    """
                    SELECT id, code, version, pattern
                    FROM part_template
                    WHERE id = %s AND version = %s
                    """,
                    (template_id, version)
                )

            row = cur.fetchone()
            if not row:
                raise NotFoundError(
                    "Template %s version %s non trouvé" % (template_id, version))

            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(
                "Erreur lors de la récupération du template: %s", str(e))
            raise DatabaseError(
                "Erreur lors de la récupération du template: %s" % str(e)) from e
        finally:
            conn.close()

    def get_by_code(self, code: str) -> List[Dict[str, Any]]:
        """Récupère toutes les versions d'un template par code"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, code, version, pattern
                FROM part_template
                WHERE code = %s
                ORDER BY version DESC
                """,
                (code,)
            )
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            logger.error(
                "Erreur lors de la récupération du template: %s", str(e))
            raise DatabaseError(
                "Erreur lors de la récupération du template: %s" % str(e)) from e
        finally:
            conn.close()

    def create(self, data: PartTemplateIn) -> Dict[str, Any]:
        """
        Crée un nouveau template (version 1)
        Transaction complète avec fields et enum_values
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            template_id = str(uuid4())
            version = 1

            # Insertion du template
            cur.execute(
                """
                INSERT INTO part_template (id, code, version, label, pattern, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, code, version, label, pattern, is_active
                """,
                (template_id, data.code, version,
                 data.label or data.code, data.pattern, data.active)
            )

            template_row = cur.fetchone()
            template_cols = [desc[0] for desc in cur.description]
            template_data = dict(zip(template_cols, template_row))

            # Insertion des fields
            for idx, field in enumerate(data.fields):
                field_id = str(uuid4())
                order = field.order if (
                    hasattr(field, 'order') and field.order and field.order > 0) else (idx + 1)

                cur.execute(
                    """
                    INSERT INTO part_template_field 
                    (id, template_id, field_key, label, field_type, unit, required, sortable, sort_order)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        field_id,
                        template_id,
                        field.key,
                        field.label,
                        field.field_type,
                        field.unit,
                        field.required,
                        False,  # sortable par défaut
                        order
                    )
                )

                # Insertion des enum_values si type enum
                if field.field_type == 'enum' and field.enum_values:
                    for enum_val in field.enum_values:
                        cur.execute(
                            """
                            INSERT INTO part_template_field_enum
                            (id, field_id, value, label)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (
                                str(uuid4()),
                                field_id,
                                enum_val.value,
                                enum_val.label
                            )
                        )

            conn.commit()
            logger.info("Template créé: %s v%s", data.code, version)
            return template_data

        except Exception as e:
            conn.rollback()
            logger.error("Erreur lors de la création du template: %s", str(e))
            raise DatabaseError(
                "Erreur lors de la création du template: %s" % str(e)) from e
        finally:
            conn.close()

    def create_new_version(self, template_id: str, data: PartTemplateUpdate) -> Dict[str, Any]:
        """
        Crée une nouvelle version d'un template existant
        Incrémente automatiquement le numéro de version
        """
        # Vérifier que le template existe et récupérer la dernière version
        current = self.get_by_id(template_id)
        new_version = current['version'] + 1

        # Utiliser les nouvelles données ou garder les anciennes
        new_pattern = data.pattern if data.pattern else current['pattern']
        new_fields = data.fields if data.fields else None

        if not new_fields:
            raise ValidationError(
                "fields est obligatoire pour créer une nouvelle version")

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Insertion du nouveau template
            cur.execute(
                """
                INSERT INTO part_template (id, code, version, label, pattern, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, code, version, label, pattern, is_active
                """,
                (template_id, current['code'], new_version, current.get(
                    'label', current['code']), new_pattern, current.get('is_active', True))
            )

            template_row = cur.fetchone()
            template_cols = [desc[0] for desc in cur.description]
            template_data = dict(zip(template_cols, template_row))

            # Insertion des fields
            for idx, field in enumerate(new_fields):
                field_id = str(uuid4())
                order = field.order if (
                    hasattr(field, 'order') and field.order and field.order > 0) else (idx + 1)

                cur.execute(
                    """
                    INSERT INTO part_template_field 
                    (id, template_id, field_key, label, field_type, unit, required, sortable, sort_order)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        field_id,
                        template_id,
                        field.key,
                        field.label,
                        field.field_type,
                        field.unit,
                        field.required,
                        False,
                        order
                    )
                )

                # Insertion des enum_values si type enum
                if field.field_type == 'enum' and field.enum_values:
                    for enum_val in field.enum_values:
                        cur.execute(
                            """
                            INSERT INTO part_template_field_enum
                            (id, field_id, value, label)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (
                                str(uuid4()),
                                field_id,
                                enum_val.value,
                                enum_val.label
                            )
                        )

            conn.commit()
            logger.info("Nouvelle version créée: %s v%s",
                        current['code'], new_version)
            return template_data

        except Exception as e:
            conn.rollback()
            logger.error(
                "Erreur lors de la création de la version: %s", str(e))
            raise DatabaseError(
                "Erreur lors de la création de la version: %s" % str(e)) from e
        finally:
            conn.close()

    def delete(self, template_id: str, version: int = None) -> bool:
        """
        Supprime un template ou une version spécifique
        Si version est None, supprime toutes les versions (CASCADE)
        """
        # Vérifier que le template n'est pas utilisé par des stock_items
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            if version is None:
                # Vérifier utilisation
                cur.execute(
                    "SELECT COUNT(*) FROM stock_item WHERE template_id = %s",
                    (template_id,)
                )
            else:
                # Vérifier utilisation de cette version spécifique
                cur.execute(
                    "SELECT COUNT(*) FROM stock_item WHERE template_id = %s AND template_version = %s",
                    (template_id, version)
                )

            count = cur.fetchone()[0]
            if count > 0:
                raise ValidationError(
                    "Impossible de supprimer: %s pièce(s) utilise(nt) ce template" % count
                )

            # Suppression (CASCADE supprimera automatiquement fields et enum_values)
            if version is None:
                cur.execute(
                    "DELETE FROM part_template WHERE id = %s",
                    (template_id,)
                )
            else:
                cur.execute(
                    "DELETE FROM part_template WHERE id = %s AND version = %s",
                    (template_id, version)
                )

            conn.commit()
            logger.info("Template supprimé: %s v%s",
                        template_id, version or "all")
            return True

        except ValidationError:
            raise
        except Exception as e:
            conn.rollback()
            logger.error(
                "Erreur lors de la suppression du template: %s", str(e))
            raise DatabaseError(
                "Erreur lors de la suppression du template: %s" % str(e)) from e
        finally:
            conn.close()
