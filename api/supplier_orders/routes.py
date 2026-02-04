from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional
from io import StringIO
import csv

from api.supplier_orders.repo import SupplierOrderRepository
from api.supplier_orders.schemas import SupplierOrderOut, SupplierOrderIn, SupplierOrderListItem, EmailExportOut
from config.export_templates import (
    get_csv_headers,
    format_csv_row,
    get_email_subject,
    get_email_body_text,
    get_email_body_html,
    get_csv_filename
)

router = APIRouter(prefix="/supplier_orders", tags=["supplier_orders"])


@router.get("/", response_model=List[SupplierOrderListItem])
async def list_supplier_orders(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Nombre max d'éléments"),
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    supplier_id: Optional[str] = Query(
        None, description="Filtrer par fournisseur")
):
    """Liste toutes les commandes fournisseur avec filtres optionnels"""
    repo = SupplierOrderRepository()
    return repo.get_all(
        limit=limit,
        offset=skip,
        status=status,
        supplier_id=supplier_id
    )


@router.get("/{order_id}", response_model=SupplierOrderOut)
async def get_supplier_order(order_id: str):
    """Récupère une commande fournisseur par ID avec ses lignes"""
    repo = SupplierOrderRepository()
    return repo.get_by_id(order_id)


@router.get("/number/{order_number}", response_model=SupplierOrderOut)
async def get_supplier_order_by_number(order_number: str):
    """Récupère une commande fournisseur par numéro"""
    repo = SupplierOrderRepository()
    return repo.get_by_order_number(order_number)


@router.post("/", response_model=SupplierOrderOut)
async def create_supplier_order(supplier_order: SupplierOrderIn):
    """Crée une nouvelle commande fournisseur"""
    repo = SupplierOrderRepository()
    try:
        return repo.add(supplier_order.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.put("/{order_id}", response_model=SupplierOrderOut)
async def update_supplier_order(order_id: str, supplier_order: SupplierOrderIn):
    """Met à jour une commande fournisseur existante"""
    repo = SupplierOrderRepository()
    try:
        return repo.update(order_id, supplier_order.model_dump(exclude_unset=True))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/{order_id}")
async def delete_supplier_order(order_id: str):
    """Supprime une commande fournisseur"""
    repo = SupplierOrderRepository()
    try:
        repo.delete(order_id)
        return {"message": f"Commande fournisseur {order_id} supprimée"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/{order_id}/export/csv")
async def export_supplier_order_csv(order_id: str):
    """
    Exporte une commande fournisseur en CSV (lignes sélectionnées uniquement).

    Configuration : Modifiez config/export_templates.py pour personnaliser :
    - get_csv_headers() : Colonnes du CSV
    - format_csv_row() : Format des données
    - get_csv_filename() : Nom du fichier
    """
    repo = SupplierOrderRepository()
    try:
        data = repo.get_export_data(order_id)

        output = StringIO()
        writer = csv.writer(output, delimiter=';')

        # En-tête (depuis template)
        writer.writerow(get_csv_headers())

        # Lignes de la commande (depuis template)
        for line in data.get('lines', []):
            writer.writerow(format_csv_row(line))

        output.seek(0)
        filename = get_csv_filename(data.get('order_number', order_id))

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/{order_id}/export/email", response_model=EmailExportOut)
async def export_supplier_order_email(order_id: str):
    """
    Génère le contenu d'un email de commande fournisseur.

    Configuration : Modifiez config/export_templates.py pour personnaliser :
    - get_email_subject() : Sujet de l'email
    - get_email_body_text() : Corps texte brut
    - get_email_body_html() : Corps HTML avec tableau
    """
    repo = SupplierOrderRepository()
    try:
        data = repo.get_export_data(order_id)

        order_number = data.get('order_number', '')
        supplier = data.get('supplier') or {}
        supplier_name = supplier.get('name', 'Fournisseur')
        supplier_email = supplier.get('email')
        lines = data.get('lines', [])

        # Génération depuis templates
        subject = get_email_subject(order_number)
        body_text = get_email_body_text(order_number, supplier_name, lines)
        body_html = get_email_body_html(order_number, supplier_name, lines)

        return EmailExportOut(
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            supplier_email=supplier_email
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
