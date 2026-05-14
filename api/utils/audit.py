"""Utilitaire pour charger les règles d'audit d'une entité."""

from typing import Any, Dict, List

from api.audits.schemas import AuditRules, AuditRuleReason


# Entités qui exigent un reason_code sur toute mutation
_ENTITIES_WITH_REQUIRED_AUDIT = {
    "intervention",
    "request",
    "purchase_request",
    "task",
    "action",
}


def get_audit_rules(entity_type: str) -> AuditRules:
    """Retourne les règles d'audit pour une entité, avec la liste des raisons applicables.

    Charge les raisons depuis la DB (catégorie manual + user uniquement —
    les raisons system sont réservées aux mutations internes).
    """
    # Import lazy pour éviter la circularité éventuelle avec audits.repo
    from api.audits.repo import AuditRepository

    required = entity_type in _ENTITIES_WITH_REQUIRED_AUDIT

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

    return AuditRules(required=required, reasons=reasons)
