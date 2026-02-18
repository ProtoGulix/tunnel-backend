"""Repository pour les familles de stock"""
import logging
from typing import List

from api.settings import settings
from api.errors.exceptions import DatabaseError, NotFoundError
from api.stock_families.schemas import StockFamilyListItem, StockFamilyDetail
from api.stock_items.template_schemas import StockSubFamily
from api.stock_items.template_service import TemplateService

logger = logging.getLogger(__name__)


class StockFamilyRepository:
    """Requêtes pour le domaine stock_family"""

    def __init__(self):
        self.template_service = TemplateService()

    def _get_connection(self):
        """Ouvre une connexion à la base de données"""
        try:
            return settings.get_db_connection()
        except Exception as e:
            raise DatabaseError(
                f"Erreur de connexion base de données: {str(e)}") from e

    def get_all(self) -> List[StockFamilyListItem]:
        """
        Liste toutes les familles de stock avec le nombre de sous-familles

        Returns:
            Liste des familles triées par family_code
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            cur.execute(
                """
                SELECT 
                    family_code,
                    COUNT(*) as sub_family_count
                FROM stock_sub_family
                GROUP BY family_code
                ORDER BY family_code
                """
            )

            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]

            return [StockFamilyListItem(**dict(zip(cols, row))) for row in rows]

        except Exception as e:
            logger.error("Erreur lors du chargement des familles: %s", str(e))
            raise DatabaseError(
                f"Erreur lors du chargement des familles: {str(e)}") from e
        finally:
            conn.close()

    def get_by_code(self, family_code: str) -> StockFamilyDetail:
        """
        Récupère une famille par son code avec ses sous-familles et templates

        Args:
            family_code: Code de la famille

        Returns:
            Détail de la famille avec liste des sous-familles et templates complets

        Raises:
            NotFoundError: Si la famille n'existe pas
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Récupérer les sous-familles avec template_id
            cur.execute(
                """
                SELECT 
                    family_code,
                    code,
                    label,
                    template_id
                FROM stock_sub_family
                WHERE family_code = %s
                ORDER BY code
                """,
                (family_code,)
            )

            rows = cur.fetchall()

            if not rows:
                raise NotFoundError(f"Famille {family_code} non trouvée")

            cols = [desc[0] for desc in cur.description]
            sub_families_data = [dict(zip(cols, row)) for row in rows]

            # Charger les templates pour chaque sous-famille
            sub_families = []
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

                sub_families.append(StockSubFamily(**sf_data))

            return StockFamilyDetail(
                family_code=family_code,
                sub_families=sub_families,
                sub_family_count=len(sub_families)
            )

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(
                "Erreur lors du chargement de la famille %s: %s", family_code, str(e))
            raise DatabaseError(
                f"Erreur lors du chargement de la famille: {str(e)}") from e
        finally:
            conn.close()
