from typing import Dict, Any, List
from datetime import date

from api.settings import settings
from api.errors.exceptions import DatabaseError
from api.stats.schemas import (
    ServiceStatusResponse,
    Period,
    Capacity,
    Breakdown,
    Fragmentation,
    Pilotage,
    SiteConsumption,
    StatusLabel,
    TopCause,
)


class StatsRepository:
    """Requêtes pour les statistiques du service"""

    def _get_connection(self):
        """Ouvre une connexion à la base de données via settings"""
        try:
            return settings.get_db_connection()
        except Exception as e:
            raise DatabaseError(f"Erreur de connexion base de données: {str(e)}")

    def get_service_status(self, start_date: date, end_date: date) -> ServiceStatusResponse:
        """Calcule les métriques de santé du service (8 calculs en SQL)"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            
            # Calcul #1-2-3 : Filtrer, classifier, agréger
            cur.execute(
                """
                WITH classified_actions AS (
                  SELECT 
                    ia.id,
                    ia.time_spent,
                    ia.created_at,
                    ia.action_subcategory,
                    s.name as subcategory_name,
                    c.id as category_id,
                    c.code as category_code,
                    i.machine_id,
                    m.equipement_mere,
                    m.is_mere,
                    m.name as machine_name,
                    parent.name as parent_name,
                    CASE 
                      WHEN c.id = 23 THEN 'FRAG'
                      WHEN c.code = 'SUP' THEN 'FRAG'
                      WHEN ia.time_spent < 0.5 AND c.code NOT IN ('DEP', 'PREV') THEN 'FRAG'
                      WHEN c.id = 19 THEN 'DEP'
                      WHEN c.id IN (20, 24) THEN 'PROD'
                      WHEN c.id IN (21, 22) THEN 'PILOT'
                      ELSE 'PROD'
                    END as time_type
                  FROM intervention_action ia
                  JOIN intervention i ON ia.intervention_id = i.id
                  LEFT JOIN action_subcategory s ON ia.action_subcategory = s.id
                  LEFT JOIN action_category c ON s.category_id = c.id
                  LEFT JOIN machine m ON i.machine_id = m.id
                  LEFT JOIN machine parent ON m.equipement_mere = parent.id
                  WHERE ia.created_at >= %s AND ia.created_at <= %s
                ),
                                breakdown AS (
                                    SELECT
                                        COALESCE(SUM(CASE WHEN time_type = 'PROD' THEN time_spent ELSE 0 END), 0) as prod_hours,
                                        COALESCE(SUM(CASE WHEN time_type = 'DEP' THEN time_spent ELSE 0 END), 0) as dep_hours,
                                        COALESCE(SUM(CASE WHEN time_type = 'PILOT' THEN time_spent ELSE 0 END), 0) as pilot_hours,
                                        COALESCE(SUM(CASE WHEN time_type = 'FRAG' THEN time_spent ELSE 0 END), 0) as frag_hours,
                                        COALESCE(SUM(time_spent), 0) as total_hours,
                                        COALESCE(COUNT(*), 0) as action_count,
                                        COALESCE(SUM(CASE WHEN time_spent < 0.5 THEN 1 ELSE 0 END), 0) as short_action_count
                                    FROM classified_actions
                                ),
                top_frag AS (
                  SELECT 
                    subcategory_name,
                    SUM(time_spent) as total_hours,
                    COUNT(*) as action_count
                  FROM classified_actions
                  WHERE time_type = 'FRAG' AND subcategory_name IS NOT NULL
                  GROUP BY subcategory_name
                  ORDER BY total_hours DESC
                  LIMIT 10
                ),
                site_consumption AS (
                  SELECT 
                    COALESCE(
                      CASE WHEN equipement_mere IS NOT NULL THEN parent_name 
                           WHEN is_mere THEN machine_name 
                           ELSE NULL END,
                      'Sans équipement'
                    ) as site_name,
                    SUM(time_spent) as total_hours,
                    SUM(CASE WHEN time_type = 'FRAG' THEN time_spent ELSE 0 END) as frag_hours
                  FROM classified_actions
                  GROUP BY site_name
                  ORDER BY frag_hours DESC
                )
                SELECT 
                  (SELECT row_to_json(breakdown.*) FROM breakdown) as breakdown,
                  (SELECT json_agg(row_to_json(top_frag.*)) FROM top_frag) as top_fragmentation,
                  (SELECT json_agg(row_to_json(site_consumption.*)) FROM site_consumption) as site_consumption
                """,
                (start_date, end_date)
            )
            
            result = cur.fetchone()
            
            if not result or not result[0]:
                return self._empty_metrics(start_date, end_date)
            
            breakdown = result[0]
            top_frag = result[1] or []
            site_consumption = result[2] or []
            
            # Calcul #4 : Charge vs capacité
            period_days = (end_date - start_date).days + 1
            capacity_hours = 320 * (period_days / 30)  # 320h/mois
            total_hours = breakdown.get('total_hours', 0)
            charge_percent = (total_hours / capacity_hours * 100) if capacity_hours > 0 else 0
            
            # Calcul #5 : Pourcentage actions courtes
            action_count = breakdown.get('action_count', 0)
            short_count = breakdown.get('short_action_count', 0)
            short_percent = (short_count / action_count * 100) if action_count > 0 else 0
            
            # Calcul #6 : Top 10 fragmentation avec pourcentages
            frag_hours = breakdown.get('frag_hours', 0)
            top_frag_formatted = self._format_top_causes(top_frag, frag_hours)
            
            # Calcul #7 : Consommation sites avec pourcentages
            site_consumption_formatted = self._format_site_consumption(site_consumption, total_hours, frag_hours)
            
            # Calcul #8 : Couleurs et interprétations
            frag_percent = (frag_hours / total_hours * 100) if total_hours > 0 else 0
            pilot_hours = breakdown.get('pilot_hours', 0)
            pilot_percent = (pilot_hours / total_hours * 100) if total_hours > 0 else 0
            
            charge_status = self._get_charge_status(charge_percent)
            frag_status = self._get_frag_status(frag_percent)
            pilot_status = self._get_pilot_status(pilot_percent)

            return self._build_response(
                start_date=start_date,
                end_date=end_date,
                period_days=period_days,
                total_hours=total_hours,
                capacity_hours=capacity_hours,
                charge_percent=charge_percent,
                charge_status=charge_status,
                breakdown=breakdown,
                pilot_hours=pilot_hours,
                frag_hours=frag_hours,
                action_count=action_count,
                short_count=short_count,
                short_percent=short_percent,
                frag_percent=frag_percent,
                frag_status=frag_status,
                pilot_percent=pilot_percent,
                pilot_status=pilot_status,
                top_causes=top_frag_formatted,
                site_consumption=site_consumption_formatted,
            )
            
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()
    
    def _empty_metrics(self, start_date: date, end_date: date) -> ServiceStatusResponse:
        """Retourne des métriques vides quand pas de données"""
        period_days = (end_date - start_date).days + 1
        capacity_hours = round(320 * (period_days / 30), 2)

        return self._build_response(
            start_date=start_date,
            end_date=end_date,
            period_days=period_days,
            total_hours=0,
            capacity_hours=capacity_hours,
            charge_percent=0,
            charge_status=self._status('green', 'Aucune charge'),
            breakdown={},
            pilot_hours=0,
            frag_hours=0,
            action_count=0,
            short_count=0,
            short_percent=0,
            frag_percent=0,
            frag_status=self._status('green', 'Aucune fragmentation'),
            pilot_percent=0,
            pilot_status=self._status('red', 'Aucune capacité'),
            top_causes=[],
            site_consumption=[],
        )
    
    def _format_top_causes(self, top_frag: List[Dict[str, Any]], frag_hours: float) -> List[TopCause]:
        """Formate les causes de fragmentation avec pourcentages"""
        return [
            TopCause(
                name=item['subcategory_name'],
                total_hours=round(item['total_hours'], 2),
                action_count=item['action_count'],
                percent=round((item['total_hours'] / frag_hours * 100), 1) if frag_hours > 0 else 0,
            )
            for item in top_frag
        ]

    def _format_site_consumption(
        self,
        site_consumption: List[Dict[str, Any]],
        total_hours: float,
        frag_hours: float,
    ) -> List[SiteConsumption]:
        """Formate la consommation des sites avec pourcentages"""
        return [
            SiteConsumption(
                site_name=item['site_name'],
                total_hours=round(item['total_hours'], 2),
                frag_hours=round(item['frag_hours'], 2),
                percent_total=round((item['total_hours'] / total_hours * 100), 1) if total_hours > 0 else 0,
                percent_frag=round((item['frag_hours'] / frag_hours * 100), 1) if frag_hours > 0 else 0,
            )
            for item in site_consumption
        ]

    def _build_response(
        self,
        *,
        start_date: date,
        end_date: date,
        period_days: int,
        total_hours: float,
        capacity_hours: float,
        charge_percent: float,
        charge_status: StatusLabel,
        breakdown: Dict[str, Any],
        pilot_hours: float,
        frag_hours: float,
        action_count: int,
        short_count: int,
        short_percent: float,
        frag_percent: float,
        frag_status: StatusLabel,
        pilot_percent: float,
        pilot_status: StatusLabel,
        top_causes: List[TopCause],
        site_consumption: List[SiteConsumption],
    ) -> ServiceStatusResponse:
        """Assemble la réponse selon le schéma Pydantic"""
        return ServiceStatusResponse(
            period=Period(
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                days=period_days,
            ),
            capacity=Capacity(
                total_hours=round(total_hours, 2),
                capacity_hours=round(capacity_hours, 2),
                charge_percent=round(charge_percent, 1),
                status=charge_status,
            ),
            breakdown=Breakdown(
                prod_hours=round(breakdown.get('prod_hours', 0), 2),
                dep_hours=round(breakdown.get('dep_hours', 0), 2),
                pilot_hours=round(pilot_hours, 2),
                frag_hours=round(frag_hours, 2),
                total_hours=round(total_hours, 2),
            ),
            fragmentation=Fragmentation(
                action_count=action_count,
                short_action_count=short_count,
                short_action_percent=round(short_percent, 1),
                frag_percent=round(frag_percent, 1),
                status=frag_status,
                top_causes=top_causes,
            ),
            pilotage=Pilotage(
                pilot_hours=round(pilot_hours, 2),
                pilot_percent=round(pilot_percent, 1),
                status=pilot_status,
            ),
            site_consumption=site_consumption,
        )

    def _status(self, color: str, text: str) -> StatusLabel:
        return StatusLabel(color=color, text=text)

    def _get_charge_status(self, charge_percent: float) -> StatusLabel:
        """Calcule statut de charge"""
        if charge_percent < 75:
            return self._status('green', 'Charge normale')
        if charge_percent < 100:
            return self._status('orange', 'Charge élevée')
        return self._status('red', 'Service au plafond')

    def _get_frag_status(self, frag_percent: float) -> StatusLabel:
        """Calcule statut de fragmentation"""
        if frag_percent < 5:
            return self._status('green', 'Fragmentation maîtrisée')
        if frag_percent < 15:
            return self._status('orange', 'Fragmentation notable')
        return self._status('red', 'Fragmentation élevée')

    def _get_pilot_status(self, pilot_percent: float) -> StatusLabel:
        """Calcule statut capacité de pilotage"""
        if pilot_percent > 20:
            return self._status('green', 'Capacité présente')
        if pilot_percent > 10:
            return self._status('orange', 'Capacité limitée')
        return self._status('red', 'Aucune capacité')
