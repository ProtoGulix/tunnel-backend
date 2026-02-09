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
    ChargeTechniqueGuide,
    TauxEvitableSeuil,
    CategoryAction,
    ChargeBreakdown,
    TauxDepannageEvitable,
    ComplexityFactorBreakdown,
    EquipementClassBreakdown,
    AnomaliesSaisieResponse,
    AnomaliesSaisieParams,
    AnomaliesSummary,
    AnomaliesByType,
    AnomaliesBySeverity,
    AnomaliesDetail,
    AnomaliesConfig,
    AnomaliesThresholds,
    RepetitiveThresholds,
    FragmentedThresholds,
    TooLongThresholds,
    BadClassificationThresholds,
    BackToBackThresholds,
    LowValueHighLoadThresholds,
    RepetitiveAnomaly,
    FragmentedAnomaly,
    TooLongAnomaly,
    BadClassificationAnomaly,
    BackToBackAnomaly,
    LowValueHighLoadAnomaly,
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

    CHARGE_TECHNIQUE_GUIDE = ChargeTechniqueGuide(
        objectif=(
            "Identifier où passe le temps du service maintenance "
            "et quelle part est récupérable pour d'autres activités "
            "(fabrication, amélioration, développement)."
        ),
        seuils_taux_evitable=[
            TauxEvitableSeuil(
                min=0, max=20, color="green",
                label="Levier limité",
                action="Dépannage majoritairement subi, difficile à réduire",
            ),
            TauxEvitableSeuil(
                min=20, max=40, color="orange",
                label="Standardisation rentable",
                action="Investir dans les standards et l'amélioration est rentable",
            ),
            TauxEvitableSeuil(
                min=40, max=None, color="red",
                label="Défaut système",
                action="La conception ou l'organisation est à revoir en profondeur",
            ),
        ],
        actions_par_categorie=[
            CategoryAction(
                category="Ressources", color="#ef4444",
                action="Homogénéiser l'architecture et les outils",
            ),
            CategoryAction(
                category="Technique", color="#3b82f6",
                action="Modifier la conception ou améliorer l'accessibilité",
            ),
            CategoryAction(
                category="Information", color="#8b5cf6",
                action="Capitaliser : documentation, méthodes, fiches",
            ),
            CategoryAction(
                category="Organisation", color="#f97316",
                action="Clarifier processus et consignes",
            ),
            CategoryAction(
                category="Environnement", color="#22c55e",
                action="Agir sur les systèmes primaires (air, eau, etc.)",
            ),
            CategoryAction(
                category="Logistique", color="#06b6d4",
                action="Créer ou renforcer les standards pièces",
            ),
            CategoryAction(
                category="Compétence", color="#eab308",
                action="Former et accompagner les équipes",
            ),
            CategoryAction(
                category="Divers", color="#6b7280",
                action="Analyser au cas par cas",
            ),
        ],
    )

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
            guide=self.CHARGE_TECHNIQUE_GUIDE,
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
                        cf.label as complexity_factor_label,
                        cf.category as complexity_factor_category,
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
                    LEFT JOIN complexity_factor cf ON ia.complexity_factor = cf.code
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
                        a.complexity_factor IS NOT NULL as has_factor,
                        EXISTS (
                            SELECT 1 FROM systemic sy
                            WHERE sy.action_subcategory = a.action_subcategory
                            AND (sy.equipement_class_id = a.equipement_class_id
                                 OR (sy.equipement_class_id IS NULL AND a.equipement_class_id IS NULL))
                        ) as is_systemic,
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
                        complexity_factor_label,
                        complexity_factor_category,
                        SUM(time_spent) as hours,
                        COUNT(*) as action_count
                    FROM classified
                    WHERE charge_type = 'DEP' AND is_evitable AND complexity_factor IS NOT NULL
                    GROUP BY complexity_factor, complexity_factor_label, complexity_factor_category
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
                        COALESCE(SUM(CASE WHEN charge_type = 'DEP' AND is_evitable THEN time_spent ELSE 0 END), 0) as charge_depannage_evitable,
                        COALESCE(SUM(CASE WHEN charge_type = 'DEP' AND has_factor THEN time_spent ELSE 0 END), 0) as hours_with_factor,
                        COALESCE(SUM(CASE WHEN charge_type = 'DEP' AND is_systemic THEN time_spent ELSE 0 END), 0) as hours_systemic,
                        COALESCE(SUM(CASE WHEN charge_type = 'DEP' AND has_factor AND is_systemic THEN time_spent ELSE 0 END), 0) as hours_both
                    FROM classified
                    WHERE equipement_class_id IS NOT NULL
                    GROUP BY equipement_class_id, equipement_class_code, equipement_class_label
                    ORDER BY charge_totale DESC
                ),
                causes_by_class AS (
                    SELECT
                        equipement_class_id,
                        json_agg(
                            json_build_object(
                                'code', complexity_factor,
                                'label', complexity_factor_label,
                                'category', complexity_factor_category,
                                'hours', hours,
                                'action_count', action_count
                            ) ORDER BY hours DESC
                        ) as causes
                    FROM (
                        SELECT
                            equipement_class_id,
                            complexity_factor,
                            complexity_factor_label,
                            complexity_factor_category,
                            SUM(time_spent) as hours,
                            COUNT(*) as action_count
                        FROM classified
                        WHERE charge_type = 'DEP' AND is_evitable AND complexity_factor IS NOT NULL AND equipement_class_id IS NOT NULL
                        GROUP BY equipement_class_id, complexity_factor, complexity_factor_label, complexity_factor_category
                    ) sub
                    GROUP BY equipement_class_id
                )
                SELECT
                    (SELECT row_to_json(global_agg.*) FROM global_agg) as global_charges,
                    (SELECT json_agg(row_to_json(cause_breakdown.*)) FROM cause_breakdown) as cause_breakdown,
                    (SELECT json_agg(
                        json_build_object(
                            'equipement_class_id', ec.equipement_class_id,
                            'equipement_class_code', ec.equipement_class_code,
                            'equipement_class_label', ec.equipement_class_label,
                            'charge_totale', ec.charge_totale,
                            'charge_depannage', ec.charge_depannage,
                            'charge_constructive', ec.charge_constructive,
                            'charge_depannage_evitable', ec.charge_depannage_evitable,
                            'hours_with_factor', ec.hours_with_factor,
                            'hours_systemic', ec.hours_systemic,
                            'hours_both', ec.hours_both,
                            'causes', COALESCE(cbc.causes, '[]'::json)
                        )
                    ) FROM by_equipement_class ec LEFT JOIN causes_by_class cbc ON ec.equipement_class_id = cbc.equipement_class_id) as by_equipement_class
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
            return self._status('green', 'Levier limité')
        if taux <= 40:
            return self._status('orange', 'Standardisation rentable')
        return self._status('red', 'Défaut système')

    def _format_cause_breakdown(
        self, cause_data: List[Dict[str, Any]], total_evitable: float
    ) -> List[ComplexityFactorBreakdown]:
        """Formate la ventilation par facteur de complexité"""
        return [
            ComplexityFactorBreakdown(
                code=item['complexity_factor'],
                label=item.get('complexity_factor_label'),
                category=item.get('complexity_factor_category'),
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
        from api.stats.schemas import EquipementClassCause, EvitableBreakdown
        
        results = []
        for item in ec_data:
            dep = item.get('charge_depannage', 0)
            evitable = item.get('charge_depannage_evitable', 0)
            taux = (evitable / dep * 100) if dep > 0 else 0
            
            # Ventilation du dépannage évitable
            hours_with_factor = item.get('hours_with_factor', 0)
            hours_systemic = item.get('hours_systemic', 0)
            hours_both = item.get('hours_both', 0)
            
            evitable_breakdown = EvitableBreakdown(
                hours_with_factor=round(hours_with_factor, 2),
                hours_systemic=round(hours_systemic, 2),
                hours_both=round(hours_both, 2),
                total_evitable=round(evitable, 2),
            )
            
            # Formater les causes pour cette classe
            causes_raw = item.get('causes', [])
            top_causes = []
            for cause in causes_raw[:3]:  # Top 3
                hours = cause.get('hours', 0)
                percent = (hours / evitable * 100) if evitable > 0 else 0
                top_causes.append(EquipementClassCause(
                    code=cause['code'],
                    label=cause.get('label'),
                    category=cause.get('category'),
                    hours=round(hours, 2),
                    percent=round(percent, 1),
                ))
            
            # Générer l'explication
            explanation = self._generate_class_explanation(
                taux, evitable, dep, top_causes, item['equipement_class_label'],
                evitable_breakdown
            )
            
            # Recommandation d'action
            recommended_action = self._generate_class_recommendation(taux, top_causes)
            
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
                    evitable_breakdown=evitable_breakdown,
                    explanation=explanation,
                    top_causes=top_causes,
                    recommended_action=recommended_action,
                )
            )
        return results
    
    def _generate_class_explanation(
        self, taux: float, evitable: float, depannage: float, 
        top_causes: List, class_label: str, breakdown
    ) -> str:
        """Génère une explication du diagnostic pour cette classe"""
        if depannage == 0:
            return f"Aucun dépannage enregistré sur {class_label}."
        
        # Construire l'explication de base
        base = f"{evitable:.1f}h de dépannage évitable sur {depannage:.1f}h total ({taux:.1f}%)."
        
        # Ajouter la ventilation par critère
        only_factor = breakdown.hours_with_factor - breakdown.hours_both
        only_systemic = breakdown.hours_systemic - breakdown.hours_both
        both = breakdown.hours_both
        
        criteria_parts = []
        if only_factor > 0:
            criteria_parts.append(f"{only_factor:.1f}h avec facteur de complexité")
        if only_systemic > 0:
            criteria_parts.append(f"{only_systemic:.1f}h de problèmes récurrents (≥3 fois)")
        if both > 0:
            criteria_parts.append(f"{both:.1f}h avec les deux critères")
        
        if criteria_parts:
            criteria_text = " : " + ", ".join(criteria_parts) + "."
        else:
            criteria_text = ""
        
        if taux < 20:
            return f"{base} Peu de marge d'amélioration identifiable{criteria_text}"
        
        # Construire le texte des causes principales
        if top_causes:
            causes_text = " Causes principales : " + ", ".join([
                f"{c.label or c.code} ({c.percent:.0f}%)" for c in top_causes[:2]
            ]) + "."
        else:
            causes_text = ""
        
        if taux <= 40:
            return f"{base}{criteria_text}{causes_text} Gains possibles par standardisation."
        
        return f"{base}{criteria_text}{causes_text} Problème systémique à traiter en priorité."
    
    def _generate_class_recommendation(self, taux: float, top_causes: List) -> str:
        """Génère une recommandation d'action pour cette classe"""
        if taux < 20:
            return "Maintenir la surveillance. Le levier d'amélioration est limité."
        
        if not top_causes:
            return "Commencer par annoter les actions avec des facteurs de complexité pour identifier les causes."
        
        main_cause = top_causes[0]
        category = main_cause.category or "Divers"
        
        actions_map = {
            "Ressources": "Assurer la disponibilité des outillages et équipements nécessaires",
            "Technique": "Renforcer l'accessibilité et la conception des équipements",
            "Information": "Améliorer la documentation technique et les schémas",
            "Logistique": "Optimiser la gestion des pièces de rechange (stock, qualité, délais)",
            "Environnement": "Adapter les conditions de travail (température, bruit, sécurité)",
            "Organisation": "Revoir la planification et la synchronisation des interventions",
            "Compétence": "Former les équipes ou redistribuer les tâches selon les compétences",
        }
        
        base_action = actions_map.get(category, "Analyser les causes et mettre en place des actions correctives")
        
        if taux > 40:
            return f"URGENT - {base_action}. Le problème est systémique."
        
        return base_action

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

    # ── Anomalies Saisie ───────────────────────────────────────────────

    ANOMALIES_THRESHOLDS = {
        "repetitive": {"monthly_count": 3, "high_severity_count": 6},
        "fragmented": {"max_duration": 1.0, "min_occurrences": 5, "high_severity_count": 10},
        "too_long": {"max_duration": 4.0, "high_severity_duration": 8.0},
        "bad_classification": {"high_severity_keywords": 2},
        "back_to_back": {"max_days_diff": 1.0, "high_severity_days": 0.5},
        "low_value_high_load": {"min_total_hours": 30.0, "high_severity_hours": 60.0},
    }

    SIMPLE_CATEGORIES = ["BAT_NET", "BAT_RAN", "BAT_DIV", "LOG_MAG", "LOG_REC", "LOG_INV"]
    LOW_VALUE_CATEGORIES = ["BAT_NET", "BAT_RAN", "BAT_DIV", "LOG_MAG", "LOG_REC"]

    SUSPICIOUS_KEYWORDS = [
        "mécanique", "hydraulique", "électrique", "pneumatique", "soudure",
        "roulement", "vérin", "moteur", "pompe", "capteur", "automate",
        "variateur", "réducteur", "courroie", "chaîne", "graissage",
        "lubrification", "alignement", "vibration", "fuite",
    ]

    def get_anomalies_saisie(
        self, start_date: date, end_date: date
    ) -> AnomaliesSaisieResponse:
        """Détecte les 6 types d'anomalies de saisie sur la période"""
        too_repetitive = self._detect_repetitive(start_date, end_date)
        too_fragmented = self._detect_fragmented(start_date, end_date)
        too_long = self._detect_too_long(start_date, end_date)
        bad_classification = self._detect_bad_classification(start_date, end_date)
        back_to_back = self._detect_back_to_back(start_date, end_date)
        low_value = self._detect_low_value_high_load(start_date, end_date)

        all_anomalies = (
            too_repetitive + too_fragmented + too_long
            + bad_classification + back_to_back + low_value
        )
        high_count = sum(1 for a in all_anomalies if a.severity == "high")
        medium_count = sum(1 for a in all_anomalies if a.severity == "medium")

        thresholds = self.ANOMALIES_THRESHOLDS
        return AnomaliesSaisieResponse(
            params=AnomaliesSaisieParams(
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            ),
            summary=AnomaliesSummary(
                total_anomalies=len(all_anomalies),
                by_type=AnomaliesByType(
                    too_repetitive=len(too_repetitive),
                    too_fragmented=len(too_fragmented),
                    too_long_for_category=len(too_long),
                    bad_classification=len(bad_classification),
                    back_to_back=len(back_to_back),
                    low_value_high_load=len(low_value),
                ),
                by_severity=AnomaliesBySeverity(
                    high=high_count,
                    medium=medium_count,
                ),
            ),
            anomalies=AnomaliesDetail(
                too_repetitive=too_repetitive,
                too_fragmented=too_fragmented,
                too_long_for_category=too_long,
                bad_classification=bad_classification,
                back_to_back=back_to_back,
                low_value_high_load=low_value,
            ),
            config=AnomaliesConfig(
                thresholds=AnomaliesThresholds(
                    repetitive=RepetitiveThresholds(**thresholds["repetitive"]),
                    fragmented=FragmentedThresholds(**thresholds["fragmented"]),
                    too_long=TooLongThresholds(**thresholds["too_long"]),
                    bad_classification=BadClassificationThresholds(**thresholds["bad_classification"]),
                    back_to_back=BackToBackThresholds(**thresholds["back_to_back"]),
                    low_value_high_load=LowValueHighLoadThresholds(**thresholds["low_value_high_load"]),
                ),
                simple_categories=self.SIMPLE_CATEGORIES,
                low_value_categories=self.LOW_VALUE_CATEGORIES,
                suspicious_keywords=self.SUSPICIOUS_KEYWORDS,
            ),
        )

    # -- Type A : Actions répétitives --

    def _detect_repetitive(
        self, start_date: date, end_date: date
    ) -> List[RepetitiveAnomaly]:
        threshold = self.ANOMALIES_THRESHOLDS["repetitive"]["monthly_count"]
        high_threshold = self.ANOMALIES_THRESHOLDS["repetitive"]["high_severity_count"]

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    s.code as subcategory_code,
                    s.name as subcategory_name,
                    m.id as machine_id,
                    m.name as machine_name,
                    TO_CHAR(ia.created_at, 'YYYY-MM') as month,
                    COUNT(*) as cnt,
                    COUNT(DISTINCT ia.intervention_id) as intervention_count
                FROM intervention_action ia
                JOIN intervention i ON ia.intervention_id = i.id
                LEFT JOIN action_subcategory s ON ia.action_subcategory = s.id
                LEFT JOIN action_category c ON s.category_id = c.id
                LEFT JOIN machine m ON i.machine_id = m.id
                WHERE ia.created_at >= %s AND ia.created_at <= %s
                  AND (c.code IS NULL OR c.code != 'PREV')
                GROUP BY s.code, s.name, m.id, m.name, TO_CHAR(ia.created_at, 'YYYY-MM')
                HAVING COUNT(*) > %s
                ORDER BY cnt DESC
                """,
                (start_date, end_date, threshold),
            )
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            results = []
            for row in rows:
                r = dict(zip(cols, row))
                cnt = r["cnt"]
                severity = "high" if cnt >= high_threshold else "medium"
                results.append(RepetitiveAnomaly(
                    category=r["subcategory_code"] or "",
                    categoryName=r["subcategory_name"] or "",
                    machine=r["machine_name"] or "",
                    machineId=str(r["machine_id"] or ""),
                    month=r["month"],
                    count=cnt,
                    interventionCount=r["intervention_count"],
                    severity=severity,
                    message=(
                        f"{r['subcategory_code'] or '?'} sur {r['machine_name'] or '?'} : "
                        f"{cnt} fois ce mois ({r['intervention_count']} interventions)"
                    ),
                ))
            return results
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()

    # -- Type B : Actions fragmentées --

    def _detect_fragmented(
        self, start_date: date, end_date: date
    ) -> List[FragmentedAnomaly]:
        max_dur = self.ANOMALIES_THRESHOLDS["fragmented"]["max_duration"]
        min_occ = self.ANOMALIES_THRESHOLDS["fragmented"]["min_occurrences"]
        high_threshold = self.ANOMALIES_THRESHOLDS["fragmented"]["high_severity_count"]

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    s.code as subcategory_code,
                    s.name as subcategory_name,
                    COUNT(*) as cnt,
                    SUM(ia.time_spent) as total_time,
                    ROUND(AVG(ia.time_spent)::numeric, 2)::float as avg_time,
                    COUNT(DISTINCT ia.intervention_id) as intervention_count
                FROM intervention_action ia
                LEFT JOIN action_subcategory s ON ia.action_subcategory = s.id
                LEFT JOIN action_category c ON s.category_id = c.id
                WHERE ia.created_at >= %s AND ia.created_at <= %s
                  AND ia.time_spent < %s
                  AND (c.code IS NULL OR c.code != 'PREV')
                GROUP BY s.code, s.name
                HAVING COUNT(*) >= %s
                ORDER BY cnt DESC
                """,
                (start_date, end_date, max_dur, min_occ),
            )
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            results = []
            for row in rows:
                r = dict(zip(cols, row))
                cnt = r["cnt"]
                severity = "high" if cnt >= high_threshold else "medium"
                results.append(FragmentedAnomaly(
                    category=r["subcategory_code"] or "",
                    categoryName=r["subcategory_name"] or "",
                    count=cnt,
                    totalTime=round(r["total_time"], 2),
                    avgTime=r["avg_time"],
                    interventionCount=r["intervention_count"],
                    severity=severity,
                    message=(
                        f"{r['subcategory_code'] or '?'} : {cnt} actions < {max_dur}h "
                        f"(total: {round(r['total_time'], 1)}h, {r['intervention_count']} interventions)"
                    ),
                ))
            return results
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()

    # -- Type C : Actions trop longues pour leur catégorie --

    def _detect_too_long(
        self, start_date: date, end_date: date
    ) -> List[TooLongAnomaly]:
        max_dur = self.ANOMALIES_THRESHOLDS["too_long"]["max_duration"]
        high_dur = self.ANOMALIES_THRESHOLDS["too_long"]["high_severity_duration"]
        simple_cats = self.SIMPLE_CATEGORIES

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            placeholders = ",".join(["%s"] * len(simple_cats))
            cur.execute(
                f"""
                SELECT
                    ia.id as action_id,
                    s.code as subcategory_code,
                    s.name as subcategory_name,
                    ia.time_spent,
                    i.code as intervention_code,
                    i.id as intervention_id,
                    i.title as intervention_title,
                    m.name as machine_name,
                    u.first_name,
                    u.last_name,
                    ia.created_at
                FROM intervention_action ia
                JOIN intervention i ON ia.intervention_id = i.id
                LEFT JOIN action_subcategory s ON ia.action_subcategory = s.id
                LEFT JOIN machine m ON i.machine_id = m.id
                LEFT JOIN directus_users u ON ia.tech = u.id
                WHERE ia.created_at >= %s AND ia.created_at <= %s
                  AND ia.time_spent > %s
                  AND s.code IN ({placeholders})
                ORDER BY ia.time_spent DESC
                """,
                (start_date, end_date, max_dur, *simple_cats),
            )
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            results = []
            for row in rows:
                r = dict(zip(cols, row))
                time_spent = r["time_spent"]
                severity = "high" if time_spent >= high_dur else "medium"
                tech_name = f"{r['first_name'] or ''} {r['last_name'] or ''}".strip()
                results.append(TooLongAnomaly(
                    actionId=str(r["action_id"]),
                    category=r["subcategory_code"] or "",
                    categoryName=r["subcategory_name"] or "",
                    time=time_spent,
                    intervention=r["intervention_code"] or "",
                    interventionId=str(r["intervention_id"]),
                    interventionTitle=r["intervention_title"] or "",
                    machine=r["machine_name"] or "",
                    tech=tech_name,
                    date=r["created_at"].isoformat() if r["created_at"] else "",
                    severity=severity,
                    message=(
                        f"{time_spent}h sur {r['subcategory_code'] or '?'} "
                        f"(intervention {r['intervention_code'] or '?'})"
                    ),
                ))
            return results
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()

    # -- Type D : Mauvaise classification --

    def _detect_bad_classification(
        self, start_date: date, end_date: date
    ) -> List[BadClassificationAnomaly]:
        high_kw_threshold = self.ANOMALIES_THRESHOLDS["bad_classification"]["high_severity_keywords"]
        keywords = self.SUSPICIOUS_KEYWORDS

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    ia.id as action_id,
                    s.code as subcategory_code,
                    s.name as subcategory_name,
                    ia.description,
                    i.code as intervention_code,
                    i.id as intervention_id,
                    i.title as intervention_title,
                    m.name as machine_name,
                    u.first_name,
                    u.last_name,
                    ia.created_at
                FROM intervention_action ia
                JOIN intervention i ON ia.intervention_id = i.id
                LEFT JOIN action_subcategory s ON ia.action_subcategory = s.id
                LEFT JOIN machine m ON i.machine_id = m.id
                LEFT JOIN directus_users u ON ia.tech = u.id
                WHERE ia.created_at >= %s AND ia.created_at <= %s
                  AND s.code = 'BAT_NET'
                ORDER BY ia.created_at DESC
                """,
                (start_date, end_date),
            )
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            results = []
            for row in rows:
                r = dict(zip(cols, row))
                desc_lower = (r["description"] or "").lower()
                found = [kw for kw in keywords if kw in desc_lower]
                if not found:
                    continue
                severity = "high" if len(found) > high_kw_threshold else "medium"
                tech_name = f"{r['first_name'] or ''} {r['last_name'] or ''}".strip()
                results.append(BadClassificationAnomaly(
                    actionId=str(r["action_id"]),
                    category=r["subcategory_code"] or "",
                    categoryName=r["subcategory_name"] or "",
                    foundKeywords=found,
                    description=r["description"] or "",
                    intervention=r["intervention_code"] or "",
                    interventionId=str(r["intervention_id"]),
                    interventionTitle=r["intervention_title"] or "",
                    machine=r["machine_name"] or "",
                    tech=tech_name,
                    date=r["created_at"].isoformat() if r["created_at"] else "",
                    severity=severity,
                    message=f"BAT_NET mais contient: {', '.join(found)}",
                ))
            return results
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()

    # -- Type E : Retours back-to-back --

    def _detect_back_to_back(
        self, start_date: date, end_date: date
    ) -> List[BackToBackAnomaly]:
        max_days = self.ANOMALIES_THRESHOLDS["back_to_back"]["max_days_diff"]
        high_days = self.ANOMALIES_THRESHOLDS["back_to_back"]["high_severity_days"]

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    ia.id as action_id,
                    ia.tech,
                    u.first_name,
                    u.last_name,
                    ia.intervention_id,
                    i.code as intervention_code,
                    i.title as intervention_title,
                    m.name as machine_name,
                    s.name as subcategory_name,
                    ia.created_at
                FROM intervention_action ia
                JOIN intervention i ON ia.intervention_id = i.id
                LEFT JOIN action_subcategory s ON ia.action_subcategory = s.id
                LEFT JOIN action_category c ON s.category_id = c.id
                LEFT JOIN machine m ON i.machine_id = m.id
                LEFT JOIN directus_users u ON ia.tech = u.id
                WHERE ia.created_at >= %s AND ia.created_at <= %s
                  AND (c.code IS NULL OR c.code != 'PREV')
                ORDER BY ia.tech, ia.intervention_id, ia.created_at ASC
                """,
                (start_date, end_date),
            )
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            actions = [dict(zip(cols, row)) for row in rows]

            results = []
            seen_pairs = set()
            for i in range(len(actions) - 1):
                a1 = actions[i]
                a2 = actions[i + 1]
                if a1["tech"] != a2["tech"]:
                    continue
                if a1["intervention_id"] != a2["intervention_id"]:
                    continue
                if not a1["created_at"] or not a2["created_at"]:
                    continue
                diff = (a2["created_at"] - a1["created_at"]).total_seconds() / 86400.0
                if diff > max_days:
                    continue
                pair_key = (str(a1["action_id"]), str(a2["action_id"]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)
                severity = "high" if diff <= high_days else "medium"
                tech_name = f"{a1['first_name'] or ''} {a1['last_name'] or ''}".strip()
                days_diff = round(diff, 1)
                results.append(BackToBackAnomaly(
                    tech=tech_name,
                    techId=str(a1["tech"] or ""),
                    intervention=a1["intervention_code"] or "",
                    interventionId=str(a1["intervention_id"]),
                    interventionTitle=a1["intervention_title"] or "",
                    machine=a1["machine_name"] or "",
                    daysDiff=days_diff,
                    date1=a1["created_at"].isoformat() if a1["created_at"] else "",
                    date2=a2["created_at"].isoformat() if a2["created_at"] else "",
                    category1=a1["subcategory_name"] or "",
                    category2=a2["subcategory_name"] or "",
                    severity=severity,
                    message=(
                        f"{a1['intervention_code'] or '?'} : retour après {days_diff}j "
                        f"({a1['subcategory_name'] or '?'} → {a2['subcategory_name'] or '?'})"
                    ),
                ))
            return results
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()

    # -- Type F : Faible valeur / charge élevée --

    def _detect_low_value_high_load(
        self, start_date: date, end_date: date
    ) -> List[LowValueHighLoadAnomaly]:
        min_hours = self.ANOMALIES_THRESHOLDS["low_value_high_load"]["min_total_hours"]
        high_hours = self.ANOMALIES_THRESHOLDS["low_value_high_load"]["high_severity_hours"]
        low_value_cats = self.LOW_VALUE_CATEGORIES

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            placeholders = ",".join(["%s"] * len(low_value_cats))
            cur.execute(
                f"""
                SELECT
                    s.code as subcategory_code,
                    s.name as subcategory_name,
                    SUM(ia.time_spent) as total_time,
                    COUNT(*) as cnt,
                    ROUND(AVG(ia.time_spent)::numeric, 2)::float as avg_time,
                    COUNT(DISTINCT ia.intervention_id) as intervention_count,
                    COUNT(DISTINCT i.machine_id) as machine_count,
                    COUNT(DISTINCT ia.tech) as tech_count
                FROM intervention_action ia
                JOIN intervention i ON ia.intervention_id = i.id
                LEFT JOIN action_subcategory s ON ia.action_subcategory = s.id
                WHERE ia.created_at >= %s AND ia.created_at <= %s
                  AND s.code IN ({placeholders})
                GROUP BY s.code, s.name
                HAVING SUM(ia.time_spent) >= %s
                ORDER BY total_time DESC
                """,
                (start_date, end_date, *low_value_cats, min_hours),
            )
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            results = []
            for row in rows:
                r = dict(zip(cols, row))
                total_time = round(r["total_time"], 2)
                severity = "high" if total_time >= high_hours else "medium"
                results.append(LowValueHighLoadAnomaly(
                    category=r["subcategory_code"] or "",
                    categoryName=r["subcategory_name"] or "",
                    totalTime=total_time,
                    count=r["cnt"],
                    avgTime=r["avg_time"],
                    interventionCount=r["intervention_count"],
                    machineCount=r["machine_count"],
                    techCount=r["tech_count"],
                    severity=severity,
                    message=(
                        f"{r['subcategory_code'] or '?'} : {total_time}h cumulées "
                        f"({r['cnt']} actions, {r['intervention_count']} interventions)"
                    ),
                ))
            return results
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()
