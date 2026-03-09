from typing import Dict, Any

from api.errors.exceptions import ValidationError
from api.db import get_connection, release_connection

# Transitions de statut autorisées
# CLOSED et CANCELLED sont des états finaux — aucune transition possible
ALLOWED_TRANSITIONS: Dict[str, list] = {
    'OPEN':      ['SENT', 'CANCELLED'],
    'SENT':      ['ACK', 'RECEIVED', 'OPEN', 'CANCELLED'],
    'ACK':       ['RECEIVED', 'CANCELLED'],
    'RECEIVED':  ['CLOSED'],
    'CLOSED':    [],
    'CANCELLED': [],
}

# Messages d'erreur contextuels par transition invalide
TRANSITION_MESSAGES: Dict[str, str] = {
    'CLOSED':    "Ce panier est clôturé — aucune modification n'est possible.",
    'CANCELLED': "Ce panier est annulé — aucune modification n'est possible.",
}

# Description des transitions valides pour guider l'UI
TRANSITION_DESCRIPTIONS: Dict[str, Dict[str, str]] = {
    'OPEN': {
        'SENT':      "Envoyer le devis au fournisseur — le panier sera verrouillé.",
        'CANCELLED': "Annuler ce panier.",
    },
    'SENT': {
        'ACK':      "Le fournisseur a répondu — passer en négociation.",
        'RECEIVED': "Commande directe confirmée — passer en cours de livraison (sans étape de négociation).",
        'OPEN':     "Réouvrir le panier — toutes les lignes sont conservées.",
        'CANCELLED': "Annuler ce panier.",
    },
    'ACK': {
        'RECEIVED':  "Négociation terminée — passer la commande ferme.",
        'CANCELLED': "Annuler ce panier.",
    },
    'RECEIVED': {
        'CLOSED': "Clôturer le panier — tous les produits ont été reçus.",
    },
}


class SupplierOrderValidator:
    """Validation des règles métier pour les commandes fournisseur"""

    @staticmethod
    def validate_status_transition(current_status: str, new_status: str) -> None:
        """
        Valide qu'une transition de statut est autorisée.

        Transitions autorisées :
          OPEN      → SENT, CANCELLED
          SENT      → ACK, RECEIVED, OPEN, CANCELLED
          ACK       → RECEIVED, CANCELLED
          RECEIVED  → CLOSED
          CLOSED    → (état final)
          CANCELLED → (état final)
        """
        if current_status == new_status:
            return  # Pas de changement, toujours valide

        allowed = ALLOWED_TRANSITIONS.get(current_status, [])

        if not allowed:
            # État final
            msg = TRANSITION_MESSAGES.get(
                current_status,
                f"Le statut '{_status_label(current_status)}' est un état final — aucune modification n'est possible."
            )
            raise ValidationError(msg)

        if new_status not in allowed:
            current_label = _status_label(current_status)
            new_label = _status_label(new_status)
            allowed_labels = [f'"{_status_label(s)}"' for s in allowed]
            raise ValidationError(
                f"Transition invalide : \"{current_label}\" → \"{new_label}\". "
                f"Actions possibles depuis \"{current_label}\" : {', '.join(allowed_labels)}."
            )

    @staticmethod
    def validate_received_preconditions(order_id: str) -> None:
        """
        Valide les prérequis avant passage en RECEIVED :
          1. Au moins une ligne doit être sélectionnée
          2. Toutes les consultations multi-fournisseurs doivent être résolues
        """
        conn = get_connection()
        try:
            cur = conn.cursor()

            # Règle 1 : au moins une ligne sélectionnée
            cur.execute(
                "SELECT COUNT(*) FROM supplier_order_line WHERE supplier_order_id = %s AND is_selected = true",
                (order_id,)
            )
            if cur.fetchone()[0] == 0:
                raise ValidationError(
                    "Aucune ligne n'est sélectionnée. "
                    "Sélectionnez au moins une ligne avant de passer en cours de livraison, "
                    "ou annulez la commande."
                )

            # Règle 2 : toutes les consultations doivent être résolues
            cur.execute(
                """
                SELECT COUNT(*) FROM supplier_order_line sol
                WHERE sol.supplier_order_id = %s
                AND EXISTS (
                    SELECT 1 FROM supplier_order_line_purchase_request solpr2
                    JOIN supplier_order_line sol2 ON sol2.id = solpr2.supplier_order_line_id
                    WHERE solpr2.purchase_request_id IN (
                        SELECT purchase_request_id FROM supplier_order_line_purchase_request
                        WHERE supplier_order_line_id = sol.id
                    )
                    AND sol2.supplier_order_id != sol.supplier_order_id
                )
                AND NOT EXISTS (
                    SELECT 1 FROM supplier_order_line_purchase_request solpr3
                    JOIN supplier_order_line sol3 ON sol3.id = solpr3.supplier_order_line_id
                    WHERE solpr3.purchase_request_id IN (
                        SELECT purchase_request_id FROM supplier_order_line_purchase_request
                        WHERE supplier_order_line_id = sol.id
                    )
                    AND sol3.is_selected = true
                )
                """,
                (order_id,)
            )
            unresolved_count = cur.fetchone()[0]
            if unresolved_count > 0:
                raise ValidationError(
                    f"{unresolved_count} ligne(s) de consultation sans fournisseur sélectionné. "
                    "Sélectionnez une ligne par article avant de passer en cours de livraison."
                )
        finally:
            release_connection(conn)

    @staticmethod
    def get_allowed_transitions(current_status: str) -> list:
        """Retourne les transitions autorisées depuis un statut donné, avec descriptions."""
        transitions = ALLOWED_TRANSITIONS.get(current_status, [])
        descriptions = TRANSITION_DESCRIPTIONS.get(current_status, {})
        return [
            {"to": status, "description": descriptions.get(status, "")}
            for status in transitions
        ]


def _status_label(code: str) -> str:
    """Retourne le label lisible d'un code statut."""
    from api.constants import SUPPLIER_ORDER_STATUS_CONFIG
    cfg = SUPPLIER_ORDER_STATUS_CONFIG.get(code, {})
    return cfg.get('label', code)
