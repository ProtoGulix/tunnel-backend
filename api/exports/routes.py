from fastapi import APIRouter, Request, Response, Depends, Query
from fastapi.responses import StreamingResponse
from io import BytesIO
import hashlib
import re
from uuid import UUID
from typing import Optional
from datetime import datetime, timedelta, date

from api.exports.repo import ExportRepository
from api.exports.pdf_generator import PDFGenerator
from api.exports.qr_generator import QRGenerator
from api.exports.planning_repo import PlanningRepository
from api.errors.exceptions import ValidationError
from api.limiter import limiter

from api.auth.permissions import require_authenticated

router = APIRouter(prefix="/exports", tags=["exports"], dependencies=[Depends(require_authenticated)])


@router.get("/interventions/{intervention_id}/pdf")
@limiter.limit("5/minute")
def export_intervention_pdf(intervention_id: str, request: Request):
    """
    Export PDF d'une intervention (authentification requise)

    Args:
        intervention_id: UUID de l'intervention

    Returns:
        Fichier PDF avec nom basé sur le code intervention
    """
    # Validate UUID format
    try:
        UUID(intervention_id)
    except ValueError:
        raise ValidationError("Format UUID invalide")

    # Fetch intervention data
    repo = ExportRepository()
    data = repo.get_intervention_export_data(intervention_id)

    # Generate PDF
    generator = PDFGenerator()
    html = generator.render_html(data)
    pdf_bytes = generator.generate_pdf(html)

    # Prepare response — sanitize filename to prevent header injection
    safe_code = re.sub(r'[^\w\-]', '_', str(data.get('code') or intervention_id))
    filename = f"{safe_code}.pdf"
    etag = hashlib.md5(pdf_bytes).hexdigest()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "ETag": etag,
            "Cache-Control": "no-cache, no-store, must-revalidate"
        }
    )


@router.get("/interventions/{intervention_id}/qrcode")
def export_intervention_qrcode(intervention_id: str):
    """
    Génère QR code pour intervention (public, pas d'authentification)

    Le QR code pointe vers la page de détail de l'intervention dans le frontend.
    Conçu pour être imprimé sur les rapports physiques.

    Args:
        intervention_id: UUID de l'intervention

    Returns:
        Image PNG du QR code
    """
    # Validate UUID format
    try:
        UUID(intervention_id)
    except ValueError:
        raise ValidationError("Format UUID invalide")

    # Get intervention code for filename
    repo = ExportRepository()
    code = repo.get_intervention_code(intervention_id)

    # Generate QR code
    generator = QRGenerator()
    qr_img = generator.generate_qr_code(intervention_id)

    # Convert to bytes
    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")
    buffer.seek(0)

    safe_code = re.sub(r'[^\w\-]', '_', str(code))
    return StreamingResponse(
        buffer,
        media_type="image/png",
        headers={
            "Content-Disposition": f'inline; filename="{safe_code}.png"',
            "Cache-Control": "public, max-age=3600"
        }
    )


# ── Helpers pour le calcul des bornes de semaine ISO ──────────────────────────

_FR_DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
_FR_MONTHS = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


def _parse_iso_week(week_iso: str):
    """Retourne (monday, friday, week_number, year) depuis 'YYYY-Www'."""
    try:
        monday = datetime.strptime(f"{week_iso}-1", "%G-W%V-%u").date()
    except ValueError:
        raise ValidationError(f"Format de semaine invalide : '{week_iso}'. Attendu YYYY-Www (ex: 2026-W24)")
    friday = monday + timedelta(days=4)
    iso_cal = monday.isocalendar()
    return monday, friday, iso_cal[1], iso_cal[0]


def _current_iso_week() -> str:
    iso = datetime.now().isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def _week_range_label(monday: date, friday: date) -> str:
    """Ex: '9 – 13 juin 2026' ou '30 mars – 3 avril 2026'."""
    if monday.month == friday.month:
        return f"{monday.day}\u2013{friday.day} {_FR_MONTHS[friday.month - 1]} {friday.year}"
    return (
        f"{monday.day} {_FR_MONTHS[monday.month - 1]}"
        f" – {friday.day} {_FR_MONTHS[friday.month - 1]} {friday.year}"
    )


def _day_label(d: date) -> str:
    """Ex: 'Lundi 9 juin'."""
    return f"{_FR_DAYS[d.weekday()]} {d.day} {_FR_MONTHS[d.month - 1]}"


# ── Route fiche de semaine ────────────────────────────────────────────────────


@router.get("/planning/semaine")
@limiter.limit("5/minute")
def export_planning_semaine(
    request: Request,
    tech_id: str = Query(..., description="UUID du technicien"),
    week: Optional[str] = Query(None, description="Semaine ISO YYYY-Www (défaut: semaine courante)"),
):
    """
    Export PDF fiche de semaine pour un technicien.

    Args:
        tech_id: UUID du technicien
        week: Semaine ISO format YYYY-Www (ex: 2026-W24). Défaut: semaine courante.

    Returns:
        PDF binaire avec les tâches de la semaine groupées par jour.
    """
    try:
        UUID(tech_id)
    except ValueError:
        raise ValidationError("Format UUID invalide pour tech_id")

    week_iso = week or _current_iso_week()
    monday, friday, week_number, year = _parse_iso_week(week_iso)

    # Semaine suivante pour les extras
    next_monday = monday + timedelta(days=7)
    next_friday = friday + timedelta(days=7)
    next_iso = f"{next_monday.isocalendar()[0]}-W{next_monday.isocalendar()[1]:02d}"

    repo = PlanningRepository()

    tech = repo.get_tech_info(tech_id)

    # Tâches semaine courante
    tasks_raw = repo.get_tasks_for_week(tech_id, monday, friday)

    # Grouper par jour
    tasks_by_day = []
    current_day = None
    current_tasks = []
    for task in tasks_raw:
        d = task["due_date"]
        if isinstance(d, datetime):
            d = d.date()
        label = _day_label(d)
        if label != current_day:
            if current_day is not None:
                tasks_by_day.append({"day_label": current_day, "tasks": current_tasks})
            current_day = label
            current_tasks = []
        current_tasks.append({
            "equip_code": task.get("equip_code") or "",
            "inter_code": task.get("inter_code") or "",
            "type": task.get("type", "projet"),
            "label": task.get("label") or "",
        })
    if current_day is not None:
        tasks_by_day.append({"day_label": current_day, "tasks": current_tasks})

    # Extras semaine suivante (max 5)
    extras_raw = repo.get_tasks_for_week(tech_id, next_monday, next_friday)
    extras = [
        {
            "equip_code": t.get("equip_code") or "",
            "inter_code": t.get("inter_code") or "",
            "type": t.get("type", "projet"),
            "label": t.get("label") or "",
            "week_label": f"S{next_monday.isocalendar()[1]}",
        }
        for t in extras_raw[:5]
    ]

    next_week_number = next_monday.isocalendar()[1]
    extras_week_label = (
        f"Semaine {next_week_number} "
        f"({_week_range_label(next_monday, next_friday)})"
    )

    data = {
        "tech": {
            "id": str(tech["id"]),
            "initial": tech.get("initial") or "",
            "first_name": tech.get("first_name") or "",
            "last_name": tech.get("last_name") or "",
        },
        "week_label": f"Semaine {week_number}",
        "week_range": _week_range_label(monday, friday),
        "week_iso": week_iso,
        "tasks_by_day": tasks_by_day,
        "extras": extras,
        "extras_week_label": extras_week_label,
        "now": datetime.now().strftime("%d/%m/%Y"),
    }

    generator = PDFGenerator()
    html = generator.render_html(data, template_file="fiche_semaine_v1.html")
    pdf_bytes = generator.generate_pdf(html)

    safe_initial = re.sub(r'[^\w]', '', tech.get("initial") or "TECH")
    safe_week = re.sub(r'[^\w\-]', '_', week_iso)
    filename = f"planning_{safe_initial}_{safe_week}.pdf"
    etag = hashlib.md5(pdf_bytes).hexdigest()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "ETag": etag,
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )
