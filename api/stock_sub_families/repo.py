import logging
from typing import List, Optional
from uuid import UUID

from api.settings import settings
from api.errors.exceptions import DatabaseError, NotFoundError
from api.stock_items.template_service import TemplateService
from api.stock_items.template_schemas import StockSubFamily

logger = logging.getLogger(__name__)


class StockSubFamilyRepository:
    """Requêtes pour le domaine stock_sub_family"""

    def __init__(self):
        self.template_service = TemplateService()

    def _get_connection(self):
        """Ouvre une connexion à la base de données"""
        try:
            return settings.get_db_connection()
        except Exception as e:
            raise DatabaseError(
                f"Erreur de connexion base de données: {str(e)}") from e

    def get_template_id(self, family_code: str, sub_family_code: str) -> Optional[UUID]:
        """
        Récupère uniquement le template_id d'une sous-famille
        SOURCE DE VÉRITÉ pour les requêtes SQL sur stock_sub_family

        Returns:
            UUID du template ou None si pas de template ou sous-famille inexistante
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            cur.execute(
                """
                SELECT template_id
                FROM stock_sub_family
                WHERE family_code = %s AND code = %s
                """,
                (family_code, sub_family_code)
            )

            row = cur.fetchone()
            if not row:
                raise NotFoundError(
                    f"Sous-famille {family_code}/{sub_family_code} non trouvée")

            return row[0]  # None si template_id IS NULL

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(
                "Erreur lors de la récupération du template_id: %s", str(e))
            raise DatabaseError(
                f"Erreur lors de la récupération du template_id: {str(e)}") from e
        finally:
            conn.close()

    def get_all_with_templates(self) -> List[StockSubFamily]:
        """
        Récupère toutes les sous-familles avec leurs templates associés (si existants)
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            cur.execute(
                """
                SELECT family_code, code, label, template_id
                FROM stock_sub_family
                ORDER BY family_code, code
                """
            )

            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            sub_families_data = [dict(zip(cols, row)) for row in rows]

            result = []
            for sf_data in sub_families_data:
                template_id = sf_data.get('template_id')

                if template_id:
                    try:
                        # Charger le template complet
                        template = self.template_service.load_template(
                            template_id)
                        sf_data['template'] = template
                    except (DatabaseError, ValueError, KeyError) as e:
                        logger.warning(
                            "Impossible de charger le template %s: %s", template_id, str(e))
                        sf_data['template'] = None
                else:
                    sf_data['template'] = None

                # Retirer template_id du dict (pas dans le schéma de sortie)
                sf_data.pop('template_id', None)

                result.append(StockSubFamily(**sf_data))

            return result

        except Exception as e:
            logger.error(
                "Erreur lors du chargement des sous-familles: %s", str(e))
            raise DatabaseError(
                f"Erreur lors du chargement des sous-familles: {str(e)}") from e
        finally:
            conn.close()

    def get_by_codes_with_template(self, family_code: str, sub_family_code: str) -> StockSubFamily:
        """
        Récupère une sous-famille par ses codes avec son template associé (si existant)
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            cur.execute(
                """
                SELECT family_code, code, label, template_id
                FROM stock_sub_family
                WHERE family_code = %s AND code = %s
                """,
                (family_code, sub_family_code)
            )

            row = cur.fetchone()
            if not row:
                raise NotFoundError(
                    f"Sous-famille {family_code}/{sub_family_code} non trouvée")

            cols = [desc[0] for desc in cur.description]
            sf_data = dict(zip(cols, row))

            # Extraire template_id et le retirer du dict
            template_id = sf_data.pop('template_id', None)

            # Charger le template si présent
            if template_id:
                template = self.template_service.load_template(template_id)
            else:
                template = None

            sf_data['template'] = template

            return StockSubFamily(**sf_data)

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(
                "Erreur lors du chargement de la sous-famille: %s", str(e))
            raise DatabaseError(
                f"Erreur lors du chargement de la sous-famille: {str(e)}") from e
        finally:
            conn.close()

    def load_template_for_sub_family(self, family_code: str, sub_family_code: str) -> Optional['PartTemplate']:
        """
        Charge le template associé à une sous-famille si existant
        Retourne None si la sous-famille n'a pas de template

        SOURCE DE VÉRITÉ pour requêtes sur stock_sub_family + templates
        """
        try:
            template_id = self.get_template_id(family_code, sub_family_code)

            if template_id is None:
                return None

            return self.template_service.load_template(template_id)

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(
                "Erreur lors du chargement du template de sous-famille: %s", str(e))
            raise DatabaseError(
                f"Erreur lors du chargement du template: {str(e)}") from e
