from typing import Dict, Any
from api.errors.exceptions import NotFoundError, DatabaseError
from api.settings import settings
from api.db import get_connection, release_connection
from api.constants import INTERVENTION_TYPES_MAP


class ExportRepository:
    """Repository spécialisé pour données d'export"""

    def _get_connection(self):
        return get_connection()

    def get_intervention_code(self, intervention_id: str) -> str:
        """Récupère uniquement le code intervention (lightweight pour QR)"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT code FROM intervention WHERE id = %s", (intervention_id,))
            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Intervention {intervention_id} non trouvée")
            return row[0] or intervention_id
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur DB: {str(e)}")
        finally:
            release_connection(conn)

    def get_intervention_export_data(self, intervention_id: str) -> Dict[str, Any]:
        """
        Récupère données complètes pour export PDF v9.

        Compatible legacy : les interventions clôturées sans DI liée
        exposent reported_by/title directement comme avant (v8).

        Structure retournée :
        {
          "code", "title", "priority", "status_actual",
          "reported_date", "reported_by", "type_inter",
          "tech_initials", "tech_full_name",
          "equipements": { code, name, no_machine, affectation, fabricant,
                           numero_serie, date_mise_service, equipement_type },
          "request": { code, demandeur_nom, demandeur_service, description,
                       statut, statut_label, statut_color } | None,
          "tasks": [{ label, status, optional, assigned_to, skip_reason,
                      sort_order, action_count, time_spent,
                      "actions": [...] }],
          "actions": [...],           # toutes les actions (legacy + v9)
          "status_logs": [...],
          "purchase_requests": [...],
          "stats": { action_count, total_time, purchase_requests_count,
                     task_total, task_done, task_skipped }
        }
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # ── Intervention + équipement + DI liée + technicien ──────────────
            cur.execute("""
                SELECT
                    i.id, i.code, i.title, i.priority, i.status_actual,
                    i.reported_date, i.reported_by, i.type_inter,
                    -- Technicien pilote
                    u.first_name  AS tech_first_name,
                    u.last_name   AS tech_last_name,
                    u.initial     AS tech_initial,
                    -- Équipement
                    m.id          AS machine_id,
                    m.code        AS machine_code,
                    m.name        AS machine_name,
                    m.no_machine,
                    m.affectation,
                    m.fabricant,
                    m.numero_serie,
                    m.date_mise_service,
                    -- Demande d'intervention liée
                    ir.id         AS req_id,
                    ir.code       AS req_code,
                    ir.demandeur_nom,
                    ir.demandeur_service_legacy AS demandeur_service,
                    ir.description AS req_description,
                    ir.statut     AS req_statut,
                    rs.label      AS req_statut_label,
                    rs.color      AS req_statut_color
                FROM intervention i
                LEFT JOIN tunnel_user u        ON u.id = i.tech_id
                LEFT JOIN machine m            ON m.id = i.machine_id
                LEFT JOIN intervention_request ir ON ir.intervention_id = i.id
                LEFT JOIN request_status_ref rs ON rs.code = ir.statut
                WHERE i.id = %s
            """, (intervention_id,))

            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Intervention {intervention_id} non trouvée")

            cols = [d[0] for d in cur.description]
            inter = dict(zip(cols, row))

            # ── Tâches de l'intervention ──────────────────────────────────────
            cur.execute("""
                SELECT
                    it.id, it.label, it.status, it.optional,
                    it.skip_reason, it.sort_order,
                    it.due_date,
                    u.first_name  AS assigned_first,
                    u.last_name   AS assigned_last,
                    u.initial     AS assigned_initial,
                    COALESCE(tagg.action_count, 0) AS action_count,
                    COALESCE(tagg.time_spent,   0) AS time_spent
                FROM intervention_task it
                LEFT JOIN tunnel_user u ON u.id = it.assigned_to
                LEFT JOIN LATERAL (
                    SELECT
                        COUNT(DISTINCT iat.action_id) AS action_count,
                        COALESCE(SUM(ia.time_spent), 0) AS time_spent
                    FROM intervention_action_task iat
                    INNER JOIN intervention_action ia ON ia.id = iat.action_id
                    WHERE iat.task_id = it.id
                ) tagg ON TRUE
                WHERE it.intervention_id = %s
                ORDER BY it.sort_order, it.created_at
            """, (intervention_id,))

            tasks_raw = []
            for t_row in cur.fetchall():
                t = dict(zip([d[0] for d in cur.description], t_row))
                af, al, ai = t.pop('assigned_first', None), t.pop('assigned_last', None), t.pop('assigned_initial', None)
                t['assigned_to'] = {'first_name': af, 'last_name': al, 'initial': ai} if af or al else None
                t['actions'] = []  # sera rempli ci-dessous
                tasks_raw.append(t)

            task_index = {str(t['id']): t for t in tasks_raw}

            # ── Actions ───────────────────────────────────────────────────────
            cur.execute("""
                SELECT
                    ia.id, ia.description, ia.time_spent, ia.created_at,
                    ia.action_start, ia.action_end,
                    ia.complexity_score, ia.complexity_factor,
                    u.first_name, u.last_name, u.initial AS tech_initial,
                    asub.id   AS sub_id,
                    asub.name AS sub_name,
                    asub.code AS sub_code,
                    ac.id     AS cat_id,
                    ac.name   AS cat_name,
                    ac.code   AS cat_code,
                    ac.color  AS cat_color
                FROM intervention_action ia
                LEFT JOIN tunnel_user u         ON u.id  = ia.tech
                LEFT JOIN action_subcategory asub ON asub.id = ia.action_subcategory
                LEFT JOIN action_category ac      ON ac.id  = asub.category_id
                WHERE ia.intervention_id = %s
                ORDER BY ia.created_at
            """, (intervention_id,))

            actions = []
            action_ids = []
            for a_row in cur.fetchall():
                a = dict(zip([d[0] for d in cur.description], a_row))
                fn, ln, ini = a.pop('first_name', None), a.pop('last_name', None), a.pop('tech_initial', None)
                full = f"{fn} {ln}".strip() if fn or ln else None
                a['tech'] = {
                    'first_name': fn,
                    'last_name': ln,
                    'initial': ini or (f"{fn[0]}{ln[0]}" if fn and ln else ''),
                    'full_name': full,
                }
                a['action_subcategory'] = {
                    'id':   a.pop('sub_id', None),
                    'name': a.pop('sub_name', None),
                    'code': a.pop('sub_code', None),
                    'category': {
                        'id':    a.pop('cat_id', None),
                        'name':  a.pop('cat_name', None),
                        'code':  a.pop('cat_code', None),
                        'color': a.pop('cat_color', None),
                    },
                }
                a['tasks'] = []  # sera rempli ci-dessous
                actions.append(a)
                action_ids.append(str(a['id']))

            # ── Liaisons action ↔ tâche ──────────────────────────────────────
            if action_ids:
                placeholders = ','.join(['%s'] * len(action_ids))
                cur.execute(f"""
                    SELECT iat.action_id, iat.task_id
                    FROM intervention_action_task iat
                    WHERE iat.action_id IN ({placeholders})
                """, action_ids)

                action_map = {str(a['id']): a for a in actions}
                for link_row in cur.fetchall():
                    a_id, t_id = str(link_row[0]), str(link_row[1])
                    # Rattacher l'action résumée à la tâche
                    if t_id in task_index:
                        task = task_index[t_id]
                        if a_id in action_map:
                            task['actions'].append(action_map[a_id])
                    # Rattacher la tâche résumée à l'action
                    if a_id in action_map and t_id in task_index:
                        t_ref = {
                            'id':     task_index[t_id]['id'],
                            'label':  task_index[t_id]['label'],
                            'status': task_index[t_id]['status'],
                        }
                        action_map[a_id]['tasks'].append(t_ref)

            # ── Statuts ───────────────────────────────────────────────────────
            cur.execute("""
                SELECT
                    sl.date, sl.status_from, sl.status_to,
                    u.first_name, u.last_name, u.initial
                FROM intervention_status_log sl
                LEFT JOIN tunnel_user u ON u.id = sl.technician_id
                WHERE sl.intervention_id = %s
                ORDER BY sl.date ASC
            """, (intervention_id,))

            status_logs = []
            for log_row in cur.fetchall():
                log = dict(zip([d[0] for d in cur.description], log_row))
                fn, ln, ini = log.pop('first_name', None), log.pop('last_name', None), log.pop('initial', None)
                log['technician_id'] = {
                    'first_name': fn,
                    'last_name': ln,
                    'initial': ini or (f"{fn[0]}{ln[0]}" if fn and ln else ''),
                }
                status_logs.append(log)

            # ── Demandes d'achat ──────────────────────────────────────────────
            cur.execute("""
                SELECT DISTINCT
                    pr.id, pr.item_label, pr.quantity, pr.unit,
                    pr.urgency, pr.requested_by AS requester_name, pr.created_at,
                    si.ref  AS stock_item_ref, si.name AS stock_item_name,
                    sis.supplier_ref,
                    s.name  AS supplier_name, s.code AS supplier_code,
                    mi.manufacturer_ref, mi.manufacturer_name
                FROM purchase_request pr
                JOIN intervention_action_purchase_request iapr ON iapr.purchase_request_id = pr.id
                JOIN intervention_action ia ON ia.id = iapr.intervention_action_id
                LEFT JOIN stock_item si         ON si.id  = pr.stock_item_id
                LEFT JOIN stock_item_supplier sis ON si.id = sis.stock_item_id AND sis.is_preferred = true
                LEFT JOIN supplier s            ON s.id   = sis.supplier_id
                LEFT JOIN manufacturer_item mi  ON mi.id  = sis.manufacturer_item_id
                WHERE ia.intervention_id = %s
                ORDER BY pr.created_at DESC
            """, (intervention_id,))

            purchase_requests = []
            for pr_row in cur.fetchall():
                pr = dict(zip([d[0] for d in cur.description], pr_row))
                pr['quantity_requested'] = pr.get('quantity')
                pr['quantity_approved'] = None
                pr['urgent'] = pr.get('urgency') == 'urgent'
                purchase_requests.append(pr)

            # ── Construction du technicien pilote ─────────────────────────────
            tech_fn = inter.get('tech_first_name')
            tech_ln = inter.get('tech_last_name')
            tech_ini = inter.get('tech_initial') or (f"{tech_fn[0]}{tech_ln[0]}" if tech_fn and tech_ln else '')
            tech_full = f"{tech_fn} {tech_ln}".strip() if tech_fn or tech_ln else None

            # ── Construction demande d'intervention ───────────────────────────
            request = None
            if inter.get('req_id'):
                request = {
                    'id':               inter['req_id'],
                    'code':             inter.get('req_code'),
                    'demandeur_nom':    inter.get('demandeur_nom'),
                    'demandeur_service': inter.get('demandeur_service'),
                    'description':      inter.get('req_description'),
                    'statut':           inter.get('req_statut'),
                    'statut_label':     inter.get('req_statut_label'),
                    'statut_color':     inter.get('req_statut_color'),
                }

            # ── Stats ─────────────────────────────────────────────────────────
            task_total   = len(tasks_raw)
            task_done    = sum(1 for t in tasks_raw if t['status'] == 'done')
            task_skipped = sum(1 for t in tasks_raw if t['status'] == 'skipped')

            return {
                "code":          inter.get("code"),
                "title":         inter.get("title"),
                "priority":      inter.get("priority"),
                "status_actual": inter.get("status_actual"),
                "reported_date": inter.get("reported_date"),
                "reported_by":   inter.get("reported_by"),
                "type_inter":    inter.get("type_inter"),
                "type_inter_label": INTERVENTION_TYPES_MAP.get(inter.get("type_inter", ""), {}).get("title"),
                "tech_initials": tech_ini,
                "tech_full_name": tech_full,
                "equipements": {
                    "code":            inter.get("machine_code"),
                    "name":            inter.get("machine_name"),
                    "no_machine":      inter.get("no_machine"),
                    "affectation":     inter.get("affectation"),
                    "fabricant":       inter.get("fabricant"),
                    "numero_serie":    inter.get("numero_serie"),
                    "date_mise_service": inter.get("date_mise_service"),
                },
                "request":          request,
                "tasks":            tasks_raw,
                "actions":          actions,
                "status_logs":      status_logs,
                "purchase_requests": purchase_requests,
                "stats": {
                    "action_count":            len(actions),
                    "total_time":              sum(a.get('time_spent', 0) or 0 for a in actions),
                    "purchase_requests_count": len(purchase_requests),
                    "task_total":              task_total,
                    "task_done":               task_done,
                    "task_skipped":            task_skipped,
                },
            }

        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur lors de la récupération des données export: {str(e)}")
        finally:
            release_connection(conn)
