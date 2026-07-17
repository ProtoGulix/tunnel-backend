from fastapi import APIRouter, Depends, HTTPException, Request

from api.auth.permissions import require_authenticated
from api.changelog.parser import get_parsed_changelog
from api.changelog.repo import ChangelogRepository, entries_since
from api.changelog.schemas import ChangelogResponse, ChangelogSection, ChangelogVersionEntry

router = APIRouter(prefix="/users/me", tags=["changelog"], dependencies=[Depends(require_authenticated)])


@router.get("/changelog", response_model=ChangelogResponse)
def get_my_changelog(request: Request):
    """Nouveautés (extraites de CHANGELOG.md) depuis la dernière visite de l'utilisateur."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentification requise")

    parsed = get_parsed_changelog()
    current_version = parsed[0].version if parsed else None

    repo = ChangelogRepository()
    last_seen_version = repo.get_last_seen_version(str(user_id))
    new_entries = entries_since(parsed, last_seen_version)

    return ChangelogResponse(
        current_version=current_version,
        entries=[
            ChangelogVersionEntry(
                version=entry.version,
                date=entry.date,
                sections=[ChangelogSection(title=s["title"], items=s["items"]) for s in entry.sections],
            )
            for entry in new_entries
        ],
    )


@router.patch("/changelog-seen", status_code=200)
def mark_my_changelog_seen(request: Request):
    """Marque le changelog comme vu jusqu'à la version courante du frontend."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentification requise")

    parsed = get_parsed_changelog()
    current_version = parsed[0].version if parsed else None
    if current_version is None:
        raise HTTPException(status_code=503, detail="Changelog indisponible")

    repo = ChangelogRepository()
    repo.mark_seen(str(user_id), current_version)
    return {"last_seen_changelog_version": current_version}
