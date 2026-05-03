import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request, HTTPException, status

from api.admin.repo import (
    AdminUserRepository, AdminRoleRepository,
    AdminEndpointRepository, AdminSecurityRepository,
)
from api.admin.schemas import (
    AdminUserCreate, AdminUserUpdate, AdminUserRolePatch, AdminUserActivePatch,
    AdminUserOut, AdminUserListItem, PasswordResetOut,
    RoleOut, PermissionOut, PermissionPatch, EndpointOut, EndpointPatch, AuditLogOut,
    ActionCategoryPatch, ActionCategoryActivePatch,
    ActionSubcategoryCreate, ActionSubcategoryPatch, ActionSubcategoryActivePatch,
    ComplexityFactorPatch, ComplexityFactorActivePatch,
    InterventionTypeCreate, InterventionTypePatch, InterventionTypeActivePatch,
    InterventionStatusPatch,
    SecurityLogOut, IpBlocklistCreate, IpBlocklistOut,
    EmailDomainRuleCreate, EmailDomainRuleOut,
    MailSettingsOut,
)
from api.auth.permissions import require_role
from api.db import get_connection, release_connection
from api.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

_resp_admin = Depends(require_role("RESP", "ADMIN"))
_admin_only = Depends(require_role("ADMIN"))


def _get_user_id(request: Request) -> str:
    return str(getattr(request.state, "user_id", ""))


# ------------------------------------------------------------------ #
# Utilisateurs                                                        #
# ------------------------------------------------------------------ #

@router.get("/users", response_model=List[AdminUserListItem], dependencies=[_resp_admin])
def list_users(
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    role_code: Optional[str] = Query(None),
):
    return AdminUserRepository().get_all(search=search, is_active=is_active, role_code=role_code)


@router.post("/users", response_model=AdminUserOut, status_code=201, dependencies=[_resp_admin])
def create_user(payload: AdminUserCreate):
    return AdminUserRepository().create(
        email=payload.email,
        password=payload.password,
        first_name=payload.first_name,
        last_name=payload.last_name,
        initial=payload.initial,
        role_id=str(payload.role_id),
    )


@router.get("/users/{user_id}", response_model=AdminUserOut, dependencies=[_resp_admin])
def get_user(user_id: str):
    return AdminUserRepository().get_by_id(user_id)


@router.put("/users/{user_id}", response_model=AdminUserOut, dependencies=[_resp_admin])
def update_user(user_id: str, payload: AdminUserUpdate):
    return AdminUserRepository().update(
        user_id=user_id,
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        initial=payload.initial,
    )


@router.patch("/users/{user_id}/role", status_code=200)
def patch_user_role(user_id: str, payload: AdminUserRolePatch,
                    request: Request, _=_resp_admin):
    AdminUserRepository().set_role(user_id, str(payload.role_id), _get_user_id(request))
    return {"message": "Rôle mis à jour"}


@router.patch("/users/{user_id}/active", status_code=200)
def patch_user_active(user_id: str, payload: AdminUserActivePatch,
                      request: Request, _=_resp_admin):
    AdminUserRepository().set_active(user_id, payload.is_active, _get_user_id(request))
    return {"message": "Statut mis à jour"}


@router.post("/users/{user_id}/reset-password", response_model=PasswordResetOut)
def reset_password(user_id: str, _=_resp_admin):
    temp_pwd = AdminUserRepository().reset_password(user_id)
    return PasswordResetOut(
        temporary_password=temp_pwd,
        message="Mot de passe temporaire généré — valide pour une seule connexion.",
    )


@router.delete("/users/{user_id}", status_code=200)
def delete_user(user_id: str, _=_resp_admin):
    AdminUserRepository().soft_delete(user_id)
    return {"message": "Utilisateur supprimé"}


# ------------------------------------------------------------------ #
# Rôles et permissions                                                #
# ------------------------------------------------------------------ #

@router.get("/roles", response_model=List[RoleOut], dependencies=[_admin_only])
def list_roles():
    return AdminRoleRepository().get_roles()


@router.get("/roles/{role_id}/permissions", response_model=List[PermissionOut],
            dependencies=[_admin_only])
def get_role_permissions(role_id: str):
    return AdminRoleRepository().get_role_permissions(role_id)


@router.patch("/permissions/{permission_id}", status_code=200)
def patch_permission(permission_id: str, payload: PermissionPatch,
                     request: Request, _=_admin_only):
    AdminRoleRepository().patch_permission(
        permission_id, payload.allowed, _get_user_id(request))
    return {"message": "Permission mise à jour"}


@router.get("/audit/permissions", response_model=List[AuditLogOut], dependencies=[_admin_only])
def get_audit_permissions(
    role_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
):
    return AdminRoleRepository().get_audit_log(
        role_id=role_id, start_date=start_date, end_date=end_date)


# ------------------------------------------------------------------ #
# Endpoints catalogue                                                  #
# ------------------------------------------------------------------ #

@router.get("/endpoints", response_model=List[EndpointOut], dependencies=[_admin_only])
def list_endpoints(
    module: Optional[str] = Query(None),
    method: Optional[str] = Query(None),
):
    return AdminEndpointRepository().get_all(module=module, method=method)


@router.get("/endpoints/modules", dependencies=[_admin_only])
def list_endpoint_modules():
    return AdminEndpointRepository().get_modules()


@router.patch("/endpoints/{endpoint_id}", response_model=EndpointOut,
              dependencies=[_admin_only])
def patch_endpoint(endpoint_id: str, payload: EndpointPatch):
    return AdminEndpointRepository().patch(
        endpoint_id,
        description=payload.description,
        module=payload.module,
        is_sensitive=payload.is_sensitive,
    )


@router.post("/endpoints/sync", status_code=200, dependencies=[_admin_only])
async def sync_endpoints(request: Request):
    """Force un rescan des routes FastAPI et UPSERT dans tunnel_endpoint."""
    from api.app import app as fastapi_app
    from api.app import sync_endpoints_catalog
    await sync_endpoints_catalog()
    return {"message": "Catalogue synchronisé"}


# ------------------------------------------------------------------ #
# Référentiel actions — catégories                                    #
# ------------------------------------------------------------------ #

@router.get("/action-categories", dependencies=[_resp_admin])
def list_action_categories():
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM action_category ORDER BY name ASC")
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        if conn:
            release_connection(conn)


@router.patch("/action-categories/{category_id}", dependencies=[_resp_admin])
def patch_action_category(category_id: int, payload: ActionCategoryPatch):
    conn = None
    try:
        conn = get_connection()
        sets, params = [], []
        if payload.label is not None:
            sets.append("name = %s"); params.append(payload.label)
        if payload.color is not None:
            sets.append("color = %s"); params.append(payload.color)
        if not sets:
            raise HTTPException(status_code=400, detail="Rien à mettre à jour")
        params.append(category_id)
        with conn.cursor() as cur:
            cur.execute(f"UPDATE action_category SET {', '.join(sets)} WHERE id = %s", params)
        conn.commit()
        return {"message": "Catégorie mise à jour"}
    finally:
        if conn:
            release_connection(conn)


@router.patch("/action-categories/{category_id}/active", dependencies=[_resp_admin])
def patch_action_category_active(category_id: int, payload: ActionCategoryActivePatch):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE action_category SET is_active = %s WHERE id = %s",
                (payload.is_active, category_id),
            )
        conn.commit()
        return {"message": "Statut mis à jour"}
    finally:
        if conn:
            release_connection(conn)


# ------------------------------------------------------------------ #
# Référentiel actions — sous-catégories                              #
# ------------------------------------------------------------------ #

@router.get("/action-subcategories", dependencies=[_resp_admin])
def list_action_subcategories(
    category_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
):
    conn = None
    try:
        conn = get_connection()
        wheres, params = [], []
        if category_id is not None:
            wheres.append("category_id = %s"); params.append(category_id)
        if is_active is not None:
            wheres.append("is_active = %s"); params.append(is_active)
        where_sql = ("WHERE " + " AND ".join(wheres)) if wheres else ""
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT * FROM action_subcategory {where_sql} ORDER BY name ASC", params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        if conn:
            release_connection(conn)


@router.post("/action-subcategories", status_code=201, dependencies=[_resp_admin])
def create_action_subcategory(payload: ActionSubcategoryCreate):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO action_subcategory (code, name, category_id) VALUES (%s, %s, %s) RETURNING id",
                (payload.code, payload.label, payload.category_id),
            )
            new_id = cur.fetchone()[0]
        conn.commit()
        return {"id": new_id, "message": "Sous-catégorie créée"}
    finally:
        if conn:
            release_connection(conn)


@router.patch("/action-subcategories/{subcat_id}", dependencies=[_resp_admin])
def patch_action_subcategory(subcat_id: int, payload: ActionSubcategoryPatch):
    conn = None
    try:
        conn = get_connection()
        if payload.label is None:
            raise HTTPException(status_code=400, detail="Rien à mettre à jour")
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE action_subcategory SET name = %s WHERE id = %s",
                (payload.label, subcat_id),
            )
        conn.commit()
        return {"message": "Sous-catégorie mise à jour"}
    finally:
        if conn:
            release_connection(conn)


@router.patch("/action-subcategories/{subcat_id}/active", dependencies=[_resp_admin])
def patch_action_subcategory_active(subcat_id: int, payload: ActionSubcategoryActivePatch):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE action_subcategory SET is_active = %s WHERE id = %s",
                (payload.is_active, subcat_id),
            )
        conn.commit()
        return {"message": "Statut mis à jour"}
    finally:
        if conn:
            release_connection(conn)


# ------------------------------------------------------------------ #
# Référentiel actions — facteurs de complexité                        #
# ------------------------------------------------------------------ #

@router.get("/complexity-factors", dependencies=[_resp_admin])
def list_complexity_factors():
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM complexity_factor ORDER BY label ASC")
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        if conn:
            release_connection(conn)


@router.patch("/complexity-factors/{factor_id}", dependencies=[_resp_admin])
def patch_complexity_factor(factor_id: int, payload: ComplexityFactorPatch):
    conn = None
    try:
        conn = get_connection()
        sets, params = [], []
        if payload.label is not None:
            sets.append("label = %s"); params.append(payload.label)
        if payload.category is not None:
            sets.append("category = %s"); params.append(payload.category)
        if not sets:
            raise HTTPException(status_code=400, detail="Rien à mettre à jour")
        params.append(factor_id)
        with conn.cursor() as cur:
            cur.execute(f"UPDATE complexity_factor SET {', '.join(sets)} WHERE id = %s", params)
        conn.commit()
        return {"message": "Facteur mis à jour"}
    finally:
        if conn:
            release_connection(conn)


@router.patch("/complexity-factors/{factor_id}/active", dependencies=[_resp_admin])
def patch_complexity_factor_active(factor_id: int, payload: ComplexityFactorActivePatch):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE complexity_factor SET is_active = %s WHERE id = %s",
                (payload.is_active, factor_id),
            )
        conn.commit()
        return {"message": "Statut mis à jour"}
    finally:
        if conn:
            release_connection(conn)


# ------------------------------------------------------------------ #
# Référentiel interventions — types                                   #
# ------------------------------------------------------------------ #

@router.get("/intervention-types", dependencies=[_resp_admin])
def list_intervention_types():
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM intervention_type ORDER BY label ASC")
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        if conn:
            release_connection(conn)


@router.post("/intervention-types", status_code=201, dependencies=[_resp_admin])
def create_intervention_type(payload: InterventionTypeCreate):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO intervention_type (code, label) VALUES (%s, %s) RETURNING id",
                (payload.code, payload.label),
            )
            new_id = cur.fetchone()[0]
        conn.commit()
        return {"id": new_id, "message": "Type créé"}
    finally:
        if conn:
            release_connection(conn)


@router.patch("/intervention-types/{type_id}", dependencies=[_resp_admin])
def patch_intervention_type(type_id: int, payload: InterventionTypePatch):
    conn = None
    try:
        conn = get_connection()
        if payload.label is None:
            raise HTTPException(status_code=400, detail="Rien à mettre à jour")
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE intervention_type SET label = %s WHERE id = %s",
                (payload.label, type_id),
            )
        conn.commit()
        return {"message": "Type mis à jour"}
    finally:
        if conn:
            release_connection(conn)


@router.patch("/intervention-types/{type_id}/active", dependencies=[_resp_admin])
def patch_intervention_type_active(type_id: int, payload: InterventionTypeActivePatch):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE intervention_type SET is_active = %s WHERE id = %s",
                (payload.is_active, type_id),
            )
        conn.commit()
        return {"message": "Statut mis à jour"}
    finally:
        if conn:
            release_connection(conn)


# ------------------------------------------------------------------ #
# Référentiel interventions — statuts                                 #
# ------------------------------------------------------------------ #

@router.get("/intervention-statuses", dependencies=[_resp_admin])
def list_intervention_statuses():
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM intervention_status ORDER BY id ASC")
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        if conn:
            release_connection(conn)


@router.patch("/intervention-statuses/{status_id}", dependencies=[_resp_admin])
def patch_intervention_status(status_id: int, payload: InterventionStatusPatch):
    conn = None
    try:
        conn = get_connection()
        sets, params = [], []
        if payload.label is not None:
            sets.append("label = %s"); params.append(payload.label)
        if payload.color is not None:
            sets.append("color = %s"); params.append(payload.color)
        if not sets:
            raise HTTPException(status_code=400, detail="Rien à mettre à jour")
        params.append(status_id)
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE intervention_status SET {', '.join(sets)} WHERE id = %s", params)
        conn.commit()
        return {"message": "Statut mis à jour"}
    finally:
        if conn:
            release_connection(conn)


# ------------------------------------------------------------------ #
# Sécurité                                                            #
# ------------------------------------------------------------------ #

@router.get("/security-logs", response_model=List[SecurityLogOut], dependencies=[_admin_only])
def list_security_logs(
    event_type: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    ip_address: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
):
    return AdminSecurityRepository().get_security_logs(
        event_type=event_type, user_id=user_id, ip_address=ip_address,
        start_date=start_date, end_date=end_date, limit=limit,
    )


@router.get("/ip-blocklist", response_model=List[IpBlocklistOut], dependencies=[_admin_only])
def list_ip_blocklist():
    return AdminSecurityRepository().get_ip_blocklist()


@router.post("/ip-blocklist", response_model=IpBlocklistOut, status_code=201)
def add_ip_block(payload: IpBlocklistCreate, request: Request, _=_admin_only):
    return AdminSecurityRepository().add_ip_block(
        ip_address=payload.ip_address,
        reason=payload.reason,
        blocked_until=payload.blocked_until,
        created_by=_get_user_id(request),
    )


@router.delete("/ip-blocklist/{block_id}", status_code=200, dependencies=[_admin_only])
def remove_ip_block(block_id: str):
    AdminSecurityRepository().remove_ip_block(block_id)
    return {"message": "Blocage supprimé"}


@router.get("/email-domain-rules", response_model=List[EmailDomainRuleOut],
            dependencies=[_admin_only])
def list_email_domain_rules():
    return AdminSecurityRepository().get_email_domain_rules()


@router.post("/email-domain-rules", response_model=EmailDomainRuleOut, status_code=201,
             dependencies=[_admin_only])
def add_email_domain_rule(payload: EmailDomainRuleCreate):
    return AdminSecurityRepository().add_email_domain_rule(payload.domain, payload.allowed)


@router.delete("/email-domain-rules/{rule_id}", status_code=200, dependencies=[_admin_only])
def remove_email_domain_rule(rule_id: str):
    AdminSecurityRepository().remove_email_domain_rule(rule_id)
    return {"message": "Règle supprimée"}


# ------------------------------------------------------------------ #
# Configuration mail                                                  #
# ------------------------------------------------------------------ #

@router.get("/settings/mail", response_model=MailSettingsOut, dependencies=[_admin_only])
def get_mail_settings():
    """Retourne la config mail sans le mot de passe SMTP."""
    return MailSettingsOut(
        mail_enabled=settings.MAIL_ENABLED,
        smtp_host=settings.SMTP_HOST,
        smtp_port=settings.SMTP_PORT,
        smtp_user=settings.SMTP_USER,
        smtp_from=settings.SMTP_FROM,
        smtp_from_name=settings.SMTP_FROM_NAME,
        smtp_starttls=settings.SMTP_STARTTLS,
    )


@router.post("/settings/mail/test", status_code=200)
async def test_mail(request: Request, _=_admin_only):
    """Envoie un email de test à l'adresse du user connecté."""
    if not settings.MAIL_ENABLED:
        raise HTTPException(status_code=400, detail="MAIL_ENABLED=false — mail désactivé")

    user_id = _get_user_id(request)
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT email FROM tunnel_user WHERE id = %s::uuid", (user_id,))
            row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        to_email = row[0]
    finally:
        if conn:
            release_connection(conn)

    try:
        import aiosmtplib
        from email.mime.text import MIMEText
        msg = MIMEText("Ceci est un email de test Tunnel GMAO.")
        msg["Subject"] = "Test email Tunnel GMAO"
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM}>"
        msg["To"] = to_email
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=settings.SMTP_STARTTLS,
        )
        return {"message": f"Email de test envoyé à {to_email}"}
    except ImportError:
        raise HTTPException(status_code=501,
                            detail="aiosmtplib non installé — ajouter au requirements.txt")
    except Exception as e:
        logger.error("Erreur envoi mail test : %s", e)
        raise HTTPException(status_code=500, detail=f"Erreur envoi mail : {e}") from e
