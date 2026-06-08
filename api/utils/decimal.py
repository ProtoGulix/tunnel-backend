from decimal import Decimal
from typing import Any, Dict, List


def convert_decimals(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convertit les valeurs Decimal en float pour la sérialisation JSON."""
    for key, value in data.items():
        if isinstance(value, Decimal):
            data[key] = float(value)
    return data


def convert_decimals_list(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Applique convert_decimals sur une liste de dicts."""
    return [convert_decimals(row) for row in rows]
