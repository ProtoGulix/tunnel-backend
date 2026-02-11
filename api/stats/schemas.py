from typing import List, Optional
from pydantic import BaseModel


class StatusLabel(BaseModel):
    color: str
    text: str


class Breakdown(BaseModel):
    prod_hours: float
    dep_hours: float
    pilot_hours: float
    frag_hours: float
    total_hours: float


class Capacity(BaseModel):
    total_hours: float
    capacity_hours: float
    charge_percent: float
    status: StatusLabel


class TopCause(BaseModel):
    name: str
    total_hours: float
    action_count: int
    percent: float


class Fragmentation(BaseModel):
    action_count: int
    short_action_count: int
    short_action_percent: float
    frag_percent: float
    status: StatusLabel
    top_causes: List[TopCause]


class Pilotage(BaseModel):
    pilot_hours: float
    pilot_percent: float
    status: StatusLabel


class SiteConsumption(BaseModel):
    site_name: str
    total_hours: float
    frag_hours: float
    percent_total: float
    percent_frag: float


class Period(BaseModel):
    start_date: str
    end_date: str
    days: int


class ServiceStatusResponse(BaseModel):
    period: Period
    capacity: Capacity
    breakdown: Breakdown
    fragmentation: Fragmentation
    pilotage: Pilotage
    site_consumption: List[SiteConsumption]

    class Config:
        from_attributes = True


# --- Charge Technique ---

class ChargeTechniqueParams(BaseModel):
    start_date: str
    end_date: str
    period_type: str


class ChargeBreakdown(BaseModel):
    charge_totale: float
    charge_depannage: float
    charge_constructive: float
    charge_depannage_evitable: float
    charge_depannage_subi: float


class TauxDepannageEvitable(BaseModel):
    taux: float
    status: StatusLabel


class ComplexityFactorBreakdown(BaseModel):
    code: str
    label: str | None
    category: str | None
    hours: float
    action_count: int
    percent: float


class EquipementClassCause(BaseModel):
    code: str
    label: str | None
    category: str | None
    hours: float
    percent: float


class EvitableBreakdown(BaseModel):
    """Ventilation du dépannage évitable par critère"""
    hours_with_factor: float  # Heures avec facteur de complexité renseigné
    hours_systemic: float  # Heures de problèmes récurrents (≥3 fois)
    hours_both: float  # Heures avec les deux critères
    total_evitable: float  # Total évitable


class EquipementClassBreakdown(BaseModel):
    equipement_class_id: str
    equipement_class_code: str
    equipement_class_label: str
    charge_totale: float
    charge_depannage: float
    charge_constructive: float
    charge_depannage_evitable: float
    taux_depannage_evitable: float
    status: StatusLabel
    evitable_breakdown: EvitableBreakdown
    explanation: str
    top_causes: List[EquipementClassCause]
    recommended_action: str


class ChargeTechniquePeriod(BaseModel):
    period: Period
    charges: ChargeBreakdown
    taux_depannage_evitable: TauxDepannageEvitable
    cause_breakdown: List[ComplexityFactorBreakdown]
    by_equipement_class: List[EquipementClassBreakdown]


class TauxEvitableSeuil(BaseModel):
    min: float
    max: float | None
    color: str
    label: str
    action: str


class CategoryAction(BaseModel):
    category: str
    color: str
    action: str


class ChargeTechniqueGuide(BaseModel):
    objectif: str
    seuils_taux_evitable: List[TauxEvitableSeuil]
    actions_par_categorie: List[CategoryAction]


class ChargeTechniqueResponse(BaseModel):
    params: ChargeTechniqueParams
    guide: ChargeTechniqueGuide
    periods: List[ChargeTechniquePeriod]

    class Config:
        from_attributes = True


# --- Anomalies Saisie ---

class AnomaliesSaisieParams(BaseModel):
    start_date: str | None
    end_date: str | None


class RepetitiveAnomaly(BaseModel):
    category: str
    categoryName: str
    machine: str
    machineId: str
    month: str
    count: int
    interventionCount: int
    severity: str
    message: str


class FragmentedAnomaly(BaseModel):
    category: str
    categoryName: str
    count: int
    totalTime: float
    avgTime: float
    interventionCount: int
    severity: str
    message: str


class TooLongAnomaly(BaseModel):
    actionId: str
    category: str
    categoryName: str
    time: float
    intervention: str
    interventionId: str
    interventionTitle: str
    machine: str
    tech: str
    date: str
    severity: str
    message: str


class BadClassificationAnomaly(BaseModel):
    actionId: str
    category: str
    categoryName: str
    foundKeywords: List[str]
    description: str
    intervention: str
    interventionId: str
    interventionTitle: str
    machine: str
    tech: str
    date: str
    severity: str
    message: str


class BackToBackAnomaly(BaseModel):
    tech: str
    techId: str
    intervention: str
    interventionId: str
    interventionTitle: str
    machine: str
    daysDiff: float
    date1: str
    date2: str
    category1: str
    category2: str
    severity: str
    message: str


class LowValueHighLoadAnomaly(BaseModel):
    category: str
    categoryName: str
    totalTime: float
    count: int
    avgTime: float
    interventionCount: int
    machineCount: int
    techCount: int
    severity: str
    message: str


class AnomaliesByType(BaseModel):
    too_repetitive: int
    too_fragmented: int
    too_long_for_category: int
    bad_classification: int
    back_to_back: int
    low_value_high_load: int


class AnomaliesBySeverity(BaseModel):
    high: int
    medium: int


class AnomaliesSummary(BaseModel):
    total_anomalies: int
    by_type: AnomaliesByType
    by_severity: AnomaliesBySeverity


class AnomaliesDetail(BaseModel):
    too_repetitive: List[RepetitiveAnomaly]
    too_fragmented: List[FragmentedAnomaly]
    too_long_for_category: List[TooLongAnomaly]
    bad_classification: List[BadClassificationAnomaly]
    back_to_back: List[BackToBackAnomaly]
    low_value_high_load: List[LowValueHighLoadAnomaly]


class RepetitiveThresholds(BaseModel):
    monthly_count: int
    high_severity_count: int


class FragmentedThresholds(BaseModel):
    max_duration: float
    min_occurrences: int
    high_severity_count: int


class TooLongThresholds(BaseModel):
    max_duration: float
    high_severity_duration: float


class BadClassificationThresholds(BaseModel):
    high_severity_keywords: int


class BackToBackThresholds(BaseModel):
    max_days_diff: float
    high_severity_days: float


class LowValueHighLoadThresholds(BaseModel):
    min_total_hours: float
    high_severity_hours: float


class AnomaliesThresholds(BaseModel):
    repetitive: RepetitiveThresholds
    fragmented: FragmentedThresholds
    too_long: TooLongThresholds
    bad_classification: BadClassificationThresholds
    back_to_back: BackToBackThresholds
    low_value_high_load: LowValueHighLoadThresholds


class AnomaliesConfig(BaseModel):
    thresholds: AnomaliesThresholds
    simple_categories: List[str]
    low_value_categories: List[str]
    suspicious_keywords: List[str]


class AnomaliesSaisieResponse(BaseModel):
    params: AnomaliesSaisieParams
    summary: AnomaliesSummary
    anomalies: AnomaliesDetail
    config: AnomaliesConfig

    class Config:
        from_attributes = True


# --- Qualité Données ---

class QualiteDonneesContexte(BaseModel):
    """Contexte variable selon l'entité concernée"""
    intervention_id: str | None = None
    intervention_code: str | None = None
    created_at: str | None = None
    stock_item_ref: str | None = None
    stock_item_name: str | None = None
    purchase_request_id: str | None = None


class QualiteDonneesProbleme(BaseModel):
    code: str
    severite: str
    entite: str
    entite_id: str
    message: str
    contexte: QualiteDonneesContexte


class QualiteDonneesParSeverite(BaseModel):
    high: int = 0
    medium: int = 0


class QualiteDonneesResponse(BaseModel):
    total: int
    par_severite: QualiteDonneesParSeverite
    problemes: List[QualiteDonneesProbleme]

    class Config:
        from_attributes = True
