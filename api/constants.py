"""Constantes et configurations de l'API"""

# Type de priorité des interventions
PRIORITY_TYPES = [
    {'id': 'faible', 'title': 'Faible', 'color': 'green'},
    {'id': 'normal', 'title': 'Normale', 'color': 'amber'},
    {'id': 'important', 'title': 'Important', 'color': 'red'},
    {'id': 'urgent', 'title': 'Urgent', 'color': 'purple'},
]

# Types d'intervention avec leurs propriétés visuelles
INTERVENTION_TYPES = [
    {'id': 'CUR', 'title': 'Curatif', 'color': 'red'},
    {'id': 'PRE', 'title': 'Préventif', 'color': 'green'},
    {'id': 'REA', 'title': 'Réapprovisionnement', 'color': 'blue'},
    {'id': 'BAT', 'title': 'Batiment', 'color': 'gray'},
    {'id': 'PRO', 'title': 'Projet', 'color': 'blue'},
    {'id': 'COF', 'title': 'Remise en conformité', 'color': 'amber'},
    {'id': 'PIL', 'title': 'Pilotage', 'color': 'blue'},
    {'id': 'MES', 'title': 'Mise en service', 'color': 'amber'},
]

# Mapping rapide ID -> type complet
INTERVENTION_TYPES_MAP = {t['id']: t for t in INTERVENTION_TYPES}

# IDs uniquement pour validation
INTERVENTION_TYPE_IDS = [t['id'] for t in INTERVENTION_TYPES]


def get_active_status_ids():
    """Récupère dynamiquement les IDs des statuts actifs depuis la DB"""
    from api.intervention_status.repo import InterventionStatusRepository
    repo = InterventionStatusRepository()
    return repo.get_active_status_ids()
