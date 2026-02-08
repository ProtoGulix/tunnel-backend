from typing import Dict, Any, List, Tuple
from datetime import date, timedelta
from calendar import monthrange

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
    ChargeTechniqueResponse,
    ChargeTechniqueParams,
    ChargeTechniquePeriod,
    ChargeBreakdown,
    TauxDepannageEvitable,
    ComplexityFactorBreakdown,
    EquipementClassBreakdown,
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

    # ── Charge Technique ──────────────────────────────────────────────

    def get_charge_technique(
        self, start_date: date, end_date: date, period_type: str = "custom"
    ) -> ChargeTechniqueResponse:
        """Analyse de la charge technique sur une ou plusieurs périodes"""
        periods = self._split_periods(start_date, end_date, period_type)
        results = [
            self._compute_charge_technique_period(p_start, p_end)
            for p_start, p_end in periods
        ]
        return ChargeTechniqueResponse(
            params=ChargeTechniqueParams(
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                period_type=period_type,
            ),
            periods=results,
        )

    def _split_periods(
        self, start_date: date, end_date: date, period_type: str
    ) -> List[Tuple[date, date]]:
        """Découpe la plage en sous-périodes selon le type"""
        if period_type == "custom":
            return [(start_date, end_date)]

        periods: List[Tuple[date, date]] = []
        current = start_date

        if period_type == "month":
            while current <= end_date:
                month_end = date(
                    current.year, current.month,
                    monthrange(current.year, current.month)[1],
                )
                period_end = min(month_end, end_date)
                periods.append((current, period_end))
                current = month_end + timedelta(days=1)

        elif period_type == "week":
            while current <= end_date:
                week_end = current + timedelta(days=6 - current.weekday())
                period_end = min(week_end, end_date)
                periods.append((current, period_end))
                current = period_end + timedelta(days=1)

        elif period_type == "quarter":
            while current <= end_date:
                quarter_month = ((current.month - 1) // 3 + 1) * 3
                quarter_end = date(
                    current.year, quarter_month,
                    monthrange(current.year, quarter_month)[1],
                )
                period_end = min(quarter_end, end_date)
                periods.append((current, period_end))
                current = period_end + timedelta(days=1)

        return periods

    def _compute_charge_technique_period(
        self, start_date: date, end_date: date
    ) -> ChargeTechniquePeriod:
        """Calcule la charge technique pour une seule période"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                WITH actions_base AS (
                    SELECT
                        ia.id,
                        ia.time_spent,
                        ia.complexity_factor,
                        ia.action_subcategory,
                        c.code as category_code,
                        ec.id as equipement_class_id,
                        ec.code as equipement_class_code,
                        ec.label as equipement_class_label
                    FROM intervention_action ia
                    JOIN intervention i ON ia.intervention_id = i.id
                    LEFT JOIN action_subcategory s ON ia.action_subcategory = s.id
                    LEFT JOIN action_category c ON s.category_id = c.id
                    LEFT JOIN machine m ON i.machine_id = m.id
                    LEFT JOIN equipement_class ec ON m.equipement_class_id = ec.id
                    WHERE ia.created_at >= %s AND ia.created_at <= %s
                ),
                systemic AS (
                    SELECT action_subcategory, equipement_class_id
                    FROM actions_base
                    WHERE category_code = 'DEP'
                    GROUP BY action_subcategory, equipement_class_id
                    HAVING COUNT(*) >= 3
                ),
                classified AS (
                    SELECT
                        a.*,
                        CASE WHEN a.category_code = 'DEP' THEN 'DEP' ELSE 'CONSTRUCTIVE' END as charge_type,
                        CASE
                            WHEN a.category_code = 'DEP' AND (
                                a.complexity_factor IS NOT NULL
                                OR EXISTS (
                                    SELECT 1 FROM systemic sy
                                    WHERE sy.action_subcategory = a.action_subcategory
                                    AND (sy.equipement_class_id = a.equipement_class_id
                                         OR (sy.equipement_class_id IS NULL AND a.equipement_class_id IS NULL))
                                )
                            ) THEN true
                            ELSE false
                        END as is_evitable
                    FROM actions_base a
                ),
                global_agg AS (
                    SELECT
                        COALESCE(SUM(time_spent), 0) as charge_totale,
                        COALESCE(SUM(CASE WHEN charge_type = 'DEP' THEN time_spent ELSE 0 END), 0) as charge_depannage,
                        COALESCE(SUM(CASE WHEN charge_type = 'CONSTRUCTIVE' THEN time_spent ELSE 0 END), 0) as charge_constructive,
                        COALESCE(SUM(CASE WHEN charge_type = 'DEP' AND is_evitable THEN time_spent ELSE 0 END), 0) as charge_depannage_evitable,
                        COALESCE(SUM(CASE WHEN charge_type = 'DEP' AND NOT is_evitable THEN time_spent ELSE 0 END), 0) as charge_depannage_subi
                    FROM classified
                ),
                cause_breakdown AS (
                    SELECT
                        complexity_factor,
                        SUM(time_spent) as hours,
                        COUNT(*) as action_count
                    FROM classified
                    WHERE charge_type = 'DEP' AND is_evitable AND complexity_factor IS NOT NULL
                    GROUP BY complexity_factor
                    ORDER BY hours DESC
                ),
                by_equipement_class AS (
                    SELECT
                        equipement_class_id,
                        equipement_class_code,
                        equipement_class_label,
                        COALESCE(SUM(time_spent), 0) as charge_totale,
                        COALESCE(SUM(CASE WHEN charge_type = 'DEP' THEN time_spent ELSE 0 END), 0) as charge_depannage,
                        COALESCE(SUM(CASE WHEN charge_type = 'CONSTRUCTIVE' THEN time_spent ELSE 0 END), 0) as charge_constructive,
                        COALESCE(SUM(CASE WHEN charge_type = 'DEP' AND is_evitable THEN time_spent ELSE 0 END), 0) as charge_depannage_evitable
                    FROM classified
                    WHERE equipement_class_id IS NOT NULL
                    GROUP BY equipement_class_id, equipement_class_code, equipement_class_label
                    ORDER BY charge_totale DESC
                )
                SELECT
                    (SELECT row_to_json(global_agg.*) FROM global_agg) as global_charges,
                    (SELECT json_agg(row_to_json(cause_breakdown.*)) FROM cause_breakdown) as cause_breakdown,
                    (SELECT json_agg(row_to_json(by_equipement_class.*)) FROM by_equipement_class) as by_equipement_class
                """,
                (start_date, end_date),
            )

            result = cur.fetchone()

            if not result or not result[0]:
                return self._empty_charge_technique_period(start_date, end_date)

            global_charges = result[0]
            cause_data = result[1] or []
            ec_data = result[2] or []

            period_days = (end_date - start_date).days + 1

            charge_dep = global_charges.get('charge_depannage', 0)
            charge_evitable = global_charges.get('charge_depannage_evitable', 0)
            taux = (charge_evitable / charge_dep * 100) if charge_dep > 0 else 0

            return ChargeTechniquePeriod(
                period=Period(
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat(),
                    days=period_days,
                ),
                charges=ChargeBreakdown(
                    charge_totale=round(global_charges.get('charge_totale', 0), 2),
                    charge_depannage=round(charge_dep, 2),
                    charge_constructive=round(global_charges.get('charge_constructive', 0), 2),
                    charge_depannage_evitable=round(charge_evitable, 2),
                    charge_depannage_subi=round(global_charges.get('charge_depannage_subi', 0), 2),
                ),
                taux_depannage_evitable=TauxDepannageEvitable(
                    taux=round(taux, 1),
                    status=self._get_taux_evitable_status(taux),
                ),
                cause_breakdown=self._format_cause_breakdown(cause_data, charge_evitable),
                by_equipement_class=self._format_equipement_class_breakdown(ec_data),
            )

        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()

    def _get_taux_evitable_status(self, taux: float) -> StatusLabel:
        """Statut couleur du taux de dépannage évitable"""
        if taux < 20:
            return self._status('green', 'Faible levier')
        if taux <= 40:
            return self._status('orange', 'Levier de standardisation')
        return self._status('red', 'Problème systémique')

    def _format_cause_breakdown(
        self, cause_data: List[Dict[str, Any]], total_evitable: float
    ) -> List[ComplexityFactorBreakdown]:
        """Formate la ventilation par facteur de complexité"""
        return [
            ComplexityFactorBreakdown(
                code=item['complexity_factor'],
                hours=round(item['hours'], 2),
                action_count=item['action_count'],
                percent=round((item['hours'] / total_evitable * 100), 1) if total_evitable > 0 else 0,
            )
            for item in cause_data
        ]

    def _format_equipement_class_breakdown(
        self, ec_data: List[Dict[str, Any]]
    ) -> List[EquipementClassBreakdown]:
        """Formate la ventilation par classe d'équipement"""
        results = []
        for item in ec_data:
            dep = item.get('charge_depannage', 0)
            evitable = item.get('charge_depannage_evitable', 0)
            taux = (evitable / dep * 100) if dep > 0 else 0
            results.append(
                EquipementClassBreakdown(
                    equipement_class_id=str(item['equipement_class_id']),
                    equipement_class_code=item['equipement_class_code'],
                    equipement_class_label=item['equipement_class_label'],
                    charge_totale=round(item.get('charge_totale', 0), 2),
                    charge_depannage=round(dep, 2),
                    charge_constructive=round(item.get('charge_constructive', 0), 2),
                    charge_depannage_evitable=round(evitable, 2),
                    taux_depannage_evitable=round(taux, 1),
                    status=self._get_taux_evitable_status(taux),
                )
            )
        return results

    def _empty_charge_technique_period(
        self, start_date: date, end_date: date
    ) -> ChargeTechniquePeriod:
        """Retourne une période vide quand pas de données"""
        period_days = (end_date - start_date).days + 1
        return ChargeTechniquePeriod(
            period=Period(
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                days=period_days,
            ),
            charges=ChargeBreakdown(
                charge_totale=0,
                charge_depannage=0,
                charge_constructive=0,
                charge_depannage_evitable=0,
                charge_depannage_subi=0,
            ),
            taux_depannage_evitable=TauxDepannageEvitable(
                taux=0,
                status=self._status('green', 'Aucune donnée'),
            ),
            cause_breakdown=[],
            by_equipement_class=[],
        )
