"""Récupération et parsing tolérant du CHANGELOG.md du frontend.

Le CHANGELOG.md est la source unique de vérité : ce module ne fait que le
lire et l'interpréter, jamais de duplication de son contenu en base.

Format attendu (non strict, dérive tolérée) :
    ## [3.51.0] — 2026-07-14
    ### Titre de section
    - entrée user-facing
    ### [interne] Titre technique
    - entrée exclue de l'affichage utilisateur

Les entrées mal formées (version sans date, ancien format en fin de
fichier) sont ignorées plutôt que de faire échouer le parsing.
"""
from __future__ import annotations

import logging
import re
from typing import List, Optional

import httpx

from api.settings import settings

logger = logging.getLogger(__name__)

# Nombre maximum de versions considérées : les entrées les plus anciennes du
# fichier dérivent vers un format non structuré et ne sont de toute façon
# jamais pertinentes pour un utilisateur qui revient après une mise à jour.
MAX_VERSIONS = 20

VERSION_HEADER_RE = re.compile(r"^##\s*\[(\d+\.\d+\.\d+)\]\s*(?:—|-)?\s*(.*)$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SECTION_HEADER_RE = re.compile(r"^###\s*(.+)$")
INTERNAL_MARKER_RE = re.compile(r"^\[interne\]", re.IGNORECASE)


class ChangelogEntry:
    def __init__(self, version: str, date: Optional[str], sections: List[dict]):
        self.version = version
        self.date = date
        self.sections = sections


def fetch_changelog_raw() -> str:
    """Récupère le contenu brut de CHANGELOG.md servi statiquement par le frontend."""
    try:
        response = httpx.get(settings.FRONTEND_CHANGELOG_URL, timeout=5.0)
        response.raise_for_status()
        return response.text
    except httpx.HTTPError as e:
        logger.warning("Impossible de récupérer CHANGELOG.md (%s) : %s", settings.FRONTEND_CHANGELOG_URL, e)
        return ""


def parse_changelog(raw: str) -> List[ChangelogEntry]:
    """Parse le markdown en entrées par version, en ignorant les sections internes
    et les blocs mal formés. Tolérant par construction : ne lève jamais d'exception."""
    entries: List[ChangelogEntry] = []
    current_version: Optional[str] = None
    current_date: Optional[str] = None
    current_sections: List[dict] = []
    current_section: Optional[dict] = None
    skip_section = False

    def flush_entry():
        if current_version is not None:
            entries.append(ChangelogEntry(current_version, current_date, current_sections))

    for line in raw.splitlines():
        version_match = VERSION_HEADER_RE.match(line)
        if version_match:
            if current_section is not None and not skip_section:
                current_sections.append(current_section)
            flush_entry()

            current_version = version_match.group(1)
            trailing = version_match.group(2).strip()
            current_date = trailing if DATE_RE.match(trailing) else None
            current_sections = []
            current_section = None
            skip_section = False

            if len(entries) >= MAX_VERSIONS:
                break
            continue

        if current_version is None:
            continue

        section_match = SECTION_HEADER_RE.match(line)
        if section_match:
            if current_section is not None and not skip_section:
                current_sections.append(current_section)
            title = section_match.group(1).strip()
            skip_section = bool(INTERNAL_MARKER_RE.match(title))
            current_section = {"title": title, "items": []} if not skip_section else None
            continue

        stripped = line.strip()
        if stripped.startswith("- ") and current_section is not None and not skip_section:
            current_section["items"].append(stripped[2:].strip())

    if current_section is not None and not skip_section:
        current_sections.append(current_section)
    flush_entry()

    return entries[:MAX_VERSIONS]


def get_parsed_changelog() -> List[ChangelogEntry]:
    raw = fetch_changelog_raw()
    if not raw:
        return []
    return parse_changelog(raw)
