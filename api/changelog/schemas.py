from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChangelogSection(BaseModel):
    """Une sous-section (### titre) d'une entrée de version."""
    model_config = ConfigDict(from_attributes=True)

    title: str
    items: List[str] = Field(default_factory=list)


class ChangelogVersionEntry(BaseModel):
    """Le contenu user-facing d'une version du changelog."""
    model_config = ConfigDict(from_attributes=True)

    version: str
    date: Optional[str] = Field(default=None)
    sections: List[ChangelogSection] = Field(default_factory=list)


class ChangelogResponse(BaseModel):
    """Réponse de GET /users/me/changelog : nouveautés depuis la dernière visite."""
    model_config = ConfigDict(from_attributes=True)

    current_version: Optional[str] = Field(default=None)
    entries: List[ChangelogVersionEntry] = Field(default_factory=list)
