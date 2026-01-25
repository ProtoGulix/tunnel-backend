"""Constantes et configurations de l'API"""

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
