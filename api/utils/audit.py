"""Utilitaire pour charger les règles d'audit d'une entité."""

from typing import Any, Dict, List, Optional

from api.audits.schemas import AuditRules, AuditRuleReason


# Entités qui exigent un reason_code sur toute mutation
_ENTITIES_WITH_REQUIRED_AUDIT = {
    "intervention",
    "request",
    "purchase_request",
    "task",
    "action",
}

# Entités dont les mutations courantes sont silencieuses côté UX :
# le front envoie _AUTO_REASON_CODE sans afficher de sélecteur.
_SILENT_ENTITY_TYPES = {"task", "action",
                        "request", "intervention", "purchase_request"}

_AUTO_REASON_CODE = "ROUTINE"

# Champs dont la modification est toujours silencieuse (pas de dialog raison)
# Les autres champs modifiables déclencheront le dialog côté front.
_SILENT_FIELDS_BY_ENTITY: Dict[str, List[str]] = {
    "intervention": ["printed_fiche", "title"],
}


def get_audit_rules(entity_type: str) -> AuditRules:
    """Retourne les règles d'audit pour une entité.

    - Catégories manual + user → affichées dans le picker front
    - Catégorie auto            → envoyée silencieusement (jamais dans le picker)
    - Catégorie system          → réservée aux mutations internes
    """
    # Import lazy pour éviter la circularité éventuelle avec audits.repo
    from api.audits.repo import AuditRepository

    required = entity_type in _ENTITIES_WITH_REQUIRED_AUDIT
    silent = entity_type in _SILENT_ENTITY_TYPES

    repo = AuditRepository()
    raw_reasons: List[Dict[str, Any]] = repo.get_all_reasons(
        active_only=True,
        entity_type=entity_type,
    )

    reasons = [
        AuditRuleReason(
            code=r["code"],
            label=r["label"],
            color=r.get("color"),
            requires_text=(r["code"] == "OTHER"),
        )
        for r in raw_reasons
        if r.get("category") in ("manual", "user")
    ]

    return AuditRules(
        required=required,
        silent=silent,
        default_reason_code=_AUTO_REASON_CODE if silent else None,
        silent_fields=_SILENT_FIELDS_BY_ENTITY.get(entity_type),
        reasons=reasons,
    )
