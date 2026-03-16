"""Constantes et configurations de l'API"""

# Statut fermé d'une intervention (constante)
CLOSED_STATUS_CODE = 'ferme'

# Capacité de l'équipe maintenance
# Équipe : 2 techs à 39h/sem + 1 renfort 1 sem/mois à 39h (tech 3 à 35h exclu)
# Calcul : (2 × 39 × 4.33) + 39 ≈ 377h → arrondi conservateur
TEAM_CAPACITY_HOURS_PER_MONTH = 400

# Base horaire journalière d'un ETP (contrat 39h ÷ 5 jours)
ETP_HOURS_PER_DAY = 7.8

# Statut "pris en charge" d'une intervention (appliqué à la création depuis une demande acceptée)
IN_PROGRESS_STATUS_CODE = 'in_progress'

# Statuts dérivés des demandes d'achat (calculés automatiquement)
DERIVED_STATUS_CONFIG = {
    # Pas de référence normalisée
    'TO_QUALIFY': {'label': 'À qualifier', 'color': '#F59E0B'},
    'NO_SUPPLIER_REF': {'label': 'Sans fournisseur', 'color': '#F97316'},
    'PENDING_DISPATCH': {'label': 'À dispatcher', 'color': '#A855F7'},
    'OPEN': {'label': 'Mutualisation', 'color': '#6B7280'},
    'CONSULTATION': {'label': 'En chiffrage', 'color': '#0EA5E9'},
    'QUOTED': {'label': 'Devis reçu', 'color': '#FFA500'},
    'ORDERED': {'label': 'Commandé', 'color': '#3B82F6'},
    'PARTIAL': {'label': 'Partiellement reçu', 'color': '#8B5CF6'},
    'RECEIVED': {'label': 'Reçu', 'color': '#10B981'},
    'REJECTED': {'label': 'Refusé', 'color': '#EF4444'}
}

# Statuts des commandes fournisseur
SUPPLIER_ORDER_STATUS_CONFIG = {
    'OPEN': {
        'label': 'En mutualisation',
        'color': '#3B82F6',
        'description': 'Panier ouvert, nouvelles DA acceptées',
        'is_locked': False,
    },
    'SENT': {
        'label': 'Devis envoyé',
        'color': '#F97316',
        'description': 'Devis envoyé au fournisseur, en attente de réponse — panier verrouillé',
        'is_locked': True,
    },
    'ACK': {
        'label': 'En négociation',
        'color': '#6366F1',
        'description': 'Réponse fournisseur reçue, sélection des lignes retenues',
        'is_locked': True,
    },
    'RECEIVED': {
        'label': 'En cours de livraison',
        'color': '#10B981',
        'description': 'Commande passée, en attente de réception physique',
        'is_locked': True,
    },
    'CLOSED': {
        'label': 'Clôturé',
        'color': '#6B7280',
        'description': 'Tous les produits reçus, fin de vie du panier',
        'is_locked': True,
    },
    'CANCELLED': {
        'label': 'Annulé',
        'color': '#EF4444',
        'description': 'Commande annulée',
        'is_locked': True,
    },
}

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
