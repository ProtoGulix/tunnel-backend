from fastapi import APIRouter, Request, Response, Depends
from fastapi.responses import StreamingResponse
from io import BytesIO
import hashlib
import re
from uuid import UUID

from api.exports.repo import ExportRepository
from api.exports.pdf_generator import PDFGenerator
from api.exports.qr_generator import QRGenerator
from api.errors.exceptions import ValidationError


from api.auth.permissions import require_authenticated

router = APIRouter(prefix="/exports", tags=["exports"], dependencies=[Depends(require_authenticated)])


@router.get("/interventions/{intervention_id}/pdf")
async def export_intervention_pdf(intervention_id: str, request: Request):
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
async def export_intervention_qrcode(intervention_id: str):
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
