"""Helpers de normalisation des réponses API.

Trois formats standards :
- single()     → { data, audit? }          GET /{id}, POST, PUT, PATCH
- paginated()  → { items, pagination, facets?, audit? }  GET / (liste paginée)
- referentiel() → liste plate              GET /statuses, /types, etc.
"""
from typing import Any, Dict, List, Optional

from api.utils.pagination import PaginationMeta, create_pagination_meta


def single(data: Any, audit_entity: Optional[str] = None) -> Dict[str, Any]:
    """Retourne { data, audit? } pour un objet unique."""
    result: Dict[str, Any] = {"data": data}
    if audit_entity is not None:
        # Import lazy pour éviter la circularité avec audits.repo
        from api.utils.audit import get_audit_rules
        result["audit"] = get_audit_rules(audit_entity)
    return result


def paginated(
    items: List[Any],
    total: int,
    offset: int,
    limit: int,
    facets: Optional[Dict[str, Any]] = None,
    audit_entity: Optional[str] = None,
) -> Dict[str, Any]:
    """Retourne { items, pagination, facets?, audit? } pour une liste paginée."""
    result: Dict[str, Any] = {
        "items": items,
        "pagination": create_pagination_meta(
            total=total, offset=offset, limit=limit, count=len(items)
        ),
    }
    if facets is not None:
        result["facets"] = facets
    if audit_entity is not None:
        # Import lazy pour éviter la circularité avec audits.repo
        from api.utils.audit import get_audit_rules
        result["audit"] = get_audit_rules(audit_entity)
    return result


def referentiel(items: List[Any]) -> List[Any]:
    """Passe-travers explicite pour les listes plates de référentiel (statuts, types…)."""
    return items
