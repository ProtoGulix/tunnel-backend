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
