"""Utilitaires de construction de clauses de recherche SQL"""

import re
from typing import Any, List, Sequence, Tuple

# Repère "<expr> ILIKE %s" dans un fragment pour l'envelopper avec unaccent(),
# ex: "p.internal_ref ILIKE %s" -> "unaccent(p.internal_ref) ILIKE unaccent(%s)"
_ILIKE_RE = re.compile(r"([\w.]+)\s+ILIKE\s+%s")


def _unaccent_fragment(fragment: str) -> str:
    """Enveloppe la comparaison ILIKE d'un fragment avec unaccent() (extension
    Postgres `unaccent`, cf. migration 022_enable_unaccent_extension), pour que
    la recherche soit aussi insensible aux accents (ex: "secable" trouve
    "sécable")."""
    return _ILIKE_RE.sub(r"unaccent(\1) ILIKE unaccent(%s)", fragment)


def build_search_clause(search: str, fragments: Sequence[str]) -> Tuple[str, List[Any]]:
    """
    Construit une clause WHERE de recherche multi-mots, insensible à la casse,
    aux accents, et à l'ordre des mots.

    `fragments` est une liste de fragments SQL, chacun contenant exactement UNE
    comparaison `<expr> ILIKE %s` (ex: "p.internal_ref ILIKE %s",
    "EXISTS (... x.label ILIKE %s ...)") — automatiquement enveloppée avec
    unaccent() des deux côtés.

    Chaque mot de `search` (séparé par des espaces) doit matcher au moins un des
    fragments (OR), et tous les mots doivent matcher (AND) pour qu'une ligne soit
    retenue. Ainsi "lame sauteuse" trouve "lame scie sauteuse" quel que soit l'ordre
    des mots, alors qu'un simple `ILIKE '%lame sauteuse%'` ne le trouverait pas.
    Et "secable" trouve "sécable" grâce à unaccent().

    Retourne (clause_sql, params). Si `search` est vide/blanc (aucun mot), retourne
    ("TRUE", []) — une clause neutre, sans effet de filtre, mais toujours valide une
    fois injectée dans un WHERE/AND (contrairement à une chaîne vide).
    """
    words = [w for w in search.split() if w]
    if not words:
        return "TRUE", []

    or_clause = " OR ".join(_unaccent_fragment(f) for f in fragments)
    word_clauses = []
    params: List[Any] = []
    for word in words:
        pattern = f"%{word}%"
        word_clauses.append(f"({or_clause})")
        params.extend([pattern] * len(fragments))

    return "(" + " AND ".join(word_clauses) + ")", params
