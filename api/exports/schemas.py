from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class ExportMetadata(BaseModel):
    """Métadonnées export"""
    intervention_id: UUID
    intervention_code: Optional[str] = None
    generated_at: str
    file_size_bytes: int


class PDFExportInfo(BaseModel):
    """Info export PDF (pour docs OpenAPI)"""
    content_type: str = "application/pdf"
    requires_auth: bool = True


class QRExportInfo(BaseModel):
    """Info export QR (pour docs OpenAPI)"""
    content_type: str = "image/png"
    requires_auth: bool = False
