from typing import Any, Dict, List
from uuid import uuid4

from api.settings import settings
from api.errors.exceptions import DatabaseError, NotFoundError
from api.intervention_status_log.validators import InterventionStatusLogValidator


class InterventionStatusLogRepository:
    """Repository pour les logs de changement de statut d'intervention"""

    def _get_connection(self):
        """Ouvre une connexion à la base de données via settings"""
        try:
            return settings.get_db_connection()
        except Exception as e:
            raise DatabaseError(
                f"Erreur de connexion base de données: {str(e)}") from e

    @staticmethod
    def _safe_int_value(value: Any) -> int | None:
        """Convertit une valeur en int, retourne None si impossible"""
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        return None

    def get_all(
        self,
        intervention_id: str | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Liste tous les logs avec filtres optionnels"""
        # Garde-fou: limit max 1000
        limit = min(limit, 1000)

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Construire la requête avec JOIN pour enrichir les statuts
            where_clause = ""
            params: List[Any] = []

            if intervention_id:
                where_clause = "WHERE isl.intervention_id = %s"
                params.append(intervention_id)

            query = f"""
                SELECT
                    isl.id,
                    isl.intervention_id,
                    isl.status_from,
                    isl.status_to,
                    isl.technician_id,
                    isl.date,
                    isl.notes,
                    sf.id as sf_id, sf.code as sf_code, sf.label as sf_label,
                    sf.color as sf_color, sf.value as sf_value,
                    st.id as st_id, st.code as st_code, st.label as st_label,
                    st.color as st_color, st.value as st_value
                FROM intervention_status_log isl
                LEFT JOIN intervention_status_ref sf ON isl.status_from = sf.id
                LEFT JOIN intervention_status_ref st ON isl.status_to = st.id
                {where_clause}
                ORDER BY isl.date DESC
                LIMIT %s OFFSET %s
            """

            params.extend([limit, offset])
            cur.execute(query, params)

            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]

            result = []
            for row in rows:
                row_dict = dict(zip(cols, row))

                # Construire l'objet status_from_detail
                if row_dict.get('sf_id'):
                    row_dict['status_from_detail'] = {
                        'id': row_dict.pop('sf_id'),
                        'code': row_dict.pop('sf_code', None),
                        'label': row_dict.pop('sf_label', None),
                        'color': row_dict.pop('sf_color', None),
                        'value': self._safe_int_value(row_dict.pop('sf_value', None))
                    }
                else:
                    row_dict['status_from_detail'] = None
                    # Nettoyer les colonnes sf_* si status_from est None
                    for key in list(row_dict.keys()):
                        if key.startswith('sf_'):
                            row_dict.pop(key)

                # Construire l'objet status_to_detail
                if row_dict.get('st_id'):
                    row_dict['status_to_detail'] = {
                        'id': row_dict.pop('st_id'),
                        'code': row_dict.pop('st_code', None),
                        'label': row_dict.pop('st_label', None),
                        'color': row_dict.pop('st_color', None),
                        'value': self._safe_int_value(row_dict.pop('st_value', None))
                    }
                else:
                    row_dict['status_to_detail'] = None
                    # Nettoyer les colonnes st_*
                    for key in list(row_dict.keys()):
                        if key.startswith('st_'):
                            row_dict.pop(key)

                result.append(row_dict)

            return result

        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def get_by_id(self, log_id: str) -> Dict[str, Any]:
        """Récupère un log par ID avec détails enrichis"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    isl.id,
                    isl.intervention_id,
                    isl.status_from,
                    isl.status_to,
                    isl.technician_id,
                    isl.date,
                    isl.notes,
                    sf.id as sf_id, sf.code as sf_code, sf.label as sf_label,
                    sf.color as sf_color, sf.value as sf_value,
                    st.id as st_id, st.code as st_code, st.label as st_label,
                    st.color as st_color, st.value as st_value
                FROM intervention_status_log isl
                LEFT JOIN intervention_status_ref sf ON isl.status_from = sf.id
                LEFT JOIN intervention_status_ref st ON isl.status_to = st.id
                WHERE isl.id = %s
                """,
                (log_id,)
            )

            row = cur.fetchone()

            if not row:
                raise NotFoundError(f"Log {log_id} non trouvé")

            cols = [desc[0] for desc in cur.description]
            row_dict = dict(zip(cols, row))

            # Construire l'objet status_from_detail
            if row_dict.get('sf_id'):
                row_dict['status_from_detail'] = {
                    'id': row_dict.pop('sf_id'),
                    'code': row_dict.pop('sf_code', None),
                    'label': row_dict.pop('sf_label', None),
                    'color': row_dict.pop('sf_color', None),
                    'value': self._safe_int_value(row_dict.pop('sf_value', None))
                }
            else:
                row_dict['status_from_detail'] = None
                # Nettoyer les colonnes sf_*
                for key in list(row_dict.keys()):
                    if key.startswith('sf_'):
                        row_dict.pop(key)

            # Construire l'objet status_to_detail
            if row_dict.get('st_id'):
                row_dict['status_to_detail'] = {
                    'id': row_dict.pop('st_id'),
                    'code': row_dict.pop('st_code', None),
                    'label': row_dict.pop('st_label', None),
                    'color': row_dict.pop('st_color', None),
                    'value': self._safe_int_value(row_dict.pop('st_value', None))
                }
            else:
                row_dict['status_to_detail'] = None
                # Nettoyer les colonnes st_*
                for key in list(row_dict.keys()):
                    if key.startswith('st_'):
                        row_dict.pop(key)

            return row_dict

        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def get_by_intervention(self, intervention_id: str) -> List[Dict[str, Any]]:
        """Récupère tous les logs d'une intervention, triés par date DESC"""
        return self.get_all(intervention_id=intervention_id, limit=1000, offset=0)

    def add(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée un nouveau log de changement de statut"""
        # Validation via validators
        validated_data = InterventionStatusLogValidator.validate_and_prepare(log_data)

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            log_id = str(uuid4())

            cur.execute(
                """
                INSERT INTO intervention_status_log
                (id, intervention_id, status_from, status_to, technician_id, date, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    log_id,
                    str(validated_data['intervention_id']),
                    validated_data.get('status_from'),
                    validated_data['status_to'],
                    str(validated_data['technician_id']),
                    validated_data['date'],
                    validated_data.get('notes')
                )
            )

            conn.commit()

            # Retourner l'objet enrichi
            return self.get_by_id(log_id)

        except ValueError:
            # Les ValueError viennent des validateurs, on les re-lève telles quelles
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise DatabaseError(f"Erreur lors de l'ajout du log: {str(e)}") from e
        finally:
            conn.close()
