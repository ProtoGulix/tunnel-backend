"""
Restaure les colonnes UUID tech perdues lors de la migration 001_fk_tunnel_user.

Contexte :
  La migration a tourne avec tunnel_user vide => tous les UUIDs traites comme
  orphelins => SET NULL sur toutes les colonnes tech/assigned_to.

Sources de recuperation (par ordre de fiabilite) :
  1. directus_activity.user (CREATE) -> auteur exact de chaque enregistrement
  2. intervention.tech_initials -> pilote de l'intervention (fallback)

Tables traitees :
  - intervention.tech_id          : tech_initials -> tunnel_user.initial (exact)
  - intervention_action.tech      : directus_activity (exact) puis fallback
  - intervention_status_log       : directus_activity (exact) puis fallback
  - intervention_task.assigned_to : fallback uniquement (pas d'activite Directus)

Non recuperables sans backup :
  - intervention.updated_by
  - intervention_task.created_by
  - intervention_task.assigned_to pour les 114 taches sans intervention_id
"""
import sys
import argparse
from scripts.db_connection import get_cursor, get_dict_cursor


def _count(cur, sql: str, params=None) -> int:
    cur.execute(sql, params or [])
    return cur.fetchone()['nb']


def dry_run(cur) -> None:
    print("=== DRY-RUN - aucun changement en base ===\n")

    # --- 1. intervention.tech_id ---
    cur.execute("""
        SELECT i.tech_initials, COUNT(*) AS nb, tu.id AS tunnel_id, tu.first_name, tu.last_name
        FROM intervention i
        LEFT JOIN tunnel_user tu ON tu.initial = i.tech_initials
        WHERE i.tech_initials IS NOT NULL AND i.tech_initials != ''
          AND i.tech_id IS NULL
        GROUP BY i.tech_initials, tu.id, tu.first_name, tu.last_name
        ORDER BY nb DESC
    """)
    rows = cur.fetchall()
    total = sum(r['nb'] for r in rows)
    matched = sum(r['nb'] for r in rows if r['tunnel_id'])
    print(f"[1] intervention.tech_id : {matched}/{total} (source: tech_initials exact)")
    for r in rows:
        d = dict(r)
        status = "EXACT" if d['tunnel_id'] else "NO MATCH"
        print(f"    {status} | {d['tech_initials']} -> {d['first_name']} {d['last_name']} ({d['nb']})")

    # --- 2. intervention_action.tech ---
    # Source A : directus_activity (exact)
    cur.execute("""
        SELECT COUNT(DISTINCT da.item) AS nb
        FROM directus_activity da
        JOIN intervention_action ia ON ia.id = CAST(da.item AS uuid)
        WHERE da.collection = 'intervention_action'
          AND da.action = 'create'
          AND ia.tech IS NULL
          AND da.user IS NOT NULL
          AND EXISTS (SELECT 1 FROM tunnel_user tu WHERE tu.id = da.user)
    """)
    exact_actions = cur.fetchone()['nb']

    # Source B : fallback via intervention.tech_id (apres avoir applique source A)
    cur.execute("""
        SELECT COUNT(ia.id) AS nb
        FROM intervention_action ia
        JOIN intervention i ON i.id = ia.intervention_id
        LEFT JOIN tunnel_user tu ON tu.initial = i.tech_initials
        WHERE ia.tech IS NULL
          AND tu.id IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM directus_activity da
              WHERE da.collection = 'intervention_action'
                AND da.action = 'create'
                AND da.item = CAST(ia.id AS text)
                AND da.user IS NOT NULL
                AND EXISTS (SELECT 1 FROM tunnel_user tu2 WHERE tu2.id = da.user)
          )
    """)
    fallback_actions = cur.fetchone()['nb']

    cur.execute("SELECT COUNT(*) AS nb FROM intervention_action WHERE tech IS NULL")
    total_null = cur.fetchone()['nb']
    print(f"\n[2] intervention_action.tech : {total_null} NULL au total")
    print(f"    {exact_actions} via directus_activity (exact)")
    print(f"    {fallback_actions} via intervention.tech_id (fallback approx.)")
    print(f"    {total_null - exact_actions - fallback_actions} irrecuperables")

    # --- 3. intervention_status_log.technician_id ---
    cur.execute("""
        SELECT COUNT(DISTINCT da.item) AS nb
        FROM directus_activity da
        JOIN intervention_status_log isl ON isl.id = CAST(da.item AS uuid)
        WHERE da.collection = 'intervention_status_log'
          AND da.action = 'create'
          AND isl.technician_id IS NULL
          AND da.user IS NOT NULL
          AND EXISTS (SELECT 1 FROM tunnel_user tu WHERE tu.id = da.user)
    """)
    exact_logs = cur.fetchone()['nb']

    cur.execute("""
        SELECT COUNT(isl.id) AS nb
        FROM intervention_status_log isl
        JOIN intervention i ON i.id = isl.intervention_id
        LEFT JOIN tunnel_user tu ON tu.initial = i.tech_initials
        WHERE isl.technician_id IS NULL
          AND tu.id IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM directus_activity da
              WHERE da.collection = 'intervention_status_log'
                AND da.action = 'create'
                AND da.item = CAST(isl.id AS text)
                AND da.user IS NOT NULL
                AND EXISTS (SELECT 1 FROM tunnel_user tu2 WHERE tu2.id = da.user)
          )
    """)
    fallback_logs = cur.fetchone()['nb']

    cur.execute("SELECT COUNT(*) AS nb FROM intervention_status_log WHERE technician_id IS NULL")
    total_logs = cur.fetchone()['nb']
    print(f"\n[3] intervention_status_log.technician_id : {total_logs} NULL au total")
    print(f"    {exact_logs} via directus_activity (exact)")
    print(f"    {fallback_logs} via intervention.tech_id (fallback approx.)")
    print(f"    {total_logs - exact_logs - fallback_logs} irrecuperables")

    # --- 4. intervention_task.assigned_to ---
    cur.execute("""
        SELECT COUNT(it.id) AS nb
        FROM intervention_task it
        JOIN intervention i ON i.id = it.intervention_id
        JOIN tunnel_user tu ON tu.initial = i.tech_initials
        WHERE it.assigned_to IS NULL
    """)
    task_fallback = cur.fetchone()['nb']

    cur.execute("SELECT COUNT(*) AS nb FROM intervention_task WHERE assigned_to IS NULL AND intervention_id IS NULL")
    task_no_inter = cur.fetchone()['nb']

    cur.execute("SELECT COUNT(*) AS nb FROM intervention_task WHERE assigned_to IS NULL")
    total_tasks = cur.fetchone()['nb']
    print(f"\n[4] intervention_task.assigned_to : {total_tasks} NULL au total")
    print(f"    {task_fallback} via intervention.tech_id (fallback approx.)")
    print(f"    {task_no_inter} sans intervention_id -> irrecuperables")

    print("\n--- Non recuperables sans backup ---")
    cur.execute("SELECT COUNT(*) AS nb FROM intervention WHERE updated_by IS NULL")
    print(f"  intervention.updated_by NULL : {cur.fetchone()['nb']}")
    cur.execute("SELECT COUNT(*) AS nb FROM intervention_task WHERE created_by IS NULL")
    print(f"  intervention_task.created_by NULL : {cur.fetchone()['nb']}")

    print("\n(Pour appliquer : relancer avec --apply)")


def apply(cur) -> None:
    print("=== APPLICATION des restaurations ===\n")

    # 1. intervention.tech_id (exact via tech_initials)
    cur.execute("""
        UPDATE intervention i
        SET tech_id = tu.id
        FROM tunnel_user tu
        WHERE tu.initial = i.tech_initials
          AND i.tech_initials IS NOT NULL
          AND i.tech_id IS NULL
    """)
    print(f"[1] intervention.tech_id : {cur.rowcount} lignes (exact via tech_initials)")

    # 2a. intervention_action.tech : directus_activity (exact)
    cur.execute("""
        UPDATE intervention_action ia
        SET tech = da.user
        FROM directus_activity da
        WHERE ia.id = CAST(da.item AS uuid)
          AND da.collection = 'intervention_action'
          AND da.action = 'create'
          AND ia.tech IS NULL
          AND da.user IS NOT NULL
          AND EXISTS (SELECT 1 FROM tunnel_user tu WHERE tu.id = da.user)
    """)
    exact_actions = cur.rowcount
    print(f"[2a] intervention_action.tech : {exact_actions} lignes (exact via directus_activity)")

    # 2b. intervention_action.tech : fallback via intervention.tech_id
    cur.execute("""
        UPDATE intervention_action ia
        SET tech = i.tech_id
        FROM intervention i
        WHERE ia.intervention_id = i.id
          AND ia.tech IS NULL
          AND i.tech_id IS NOT NULL
    """)
    print(f"[2b] intervention_action.tech : {cur.rowcount} lignes (fallback via intervention.tech_id)")

    # 3a. intervention_status_log.technician_id : directus_activity (exact)
    cur.execute("""
        UPDATE intervention_status_log isl
        SET technician_id = da.user
        FROM directus_activity da
        WHERE isl.id = CAST(da.item AS uuid)
          AND da.collection = 'intervention_status_log'
          AND da.action = 'create'
          AND isl.technician_id IS NULL
          AND da.user IS NOT NULL
          AND EXISTS (SELECT 1 FROM tunnel_user tu WHERE tu.id = da.user)
    """)
    exact_logs = cur.rowcount
    print(f"[3a] status_log.technician_id : {exact_logs} lignes (exact via directus_activity)")

    # 3b. intervention_status_log.technician_id : fallback
    cur.execute("""
        UPDATE intervention_status_log sl
        SET technician_id = i.tech_id
        FROM intervention i
        WHERE sl.intervention_id = i.id
          AND sl.technician_id IS NULL
          AND i.tech_id IS NOT NULL
    """)
    print(f"[3b] status_log.technician_id : {cur.rowcount} lignes (fallback via intervention.tech_id)")

    # 4. intervention_task.assigned_to : fallback via intervention.tech_id
    cur.execute("""
        UPDATE intervention_task it
        SET assigned_to = i.tech_id
        FROM intervention i
        WHERE it.intervention_id = i.id
          AND it.assigned_to IS NULL
          AND i.tech_id IS NOT NULL
    """)
    print(f"[4]  intervention_task.assigned_to : {cur.rowcount} lignes (fallback via intervention.tech_id)")

    print("\n--- Non recuperables (aucune source disponible) ---")
    cur.execute("SELECT COUNT(*) AS nb FROM intervention_action WHERE tech IS NULL")
    print(f"  intervention_action.tech NULL restant : {cur.fetchone()['nb']}")
    cur.execute("SELECT COUNT(*) AS nb FROM intervention_status_log WHERE technician_id IS NULL")
    print(f"  status_log.technician_id NULL restant : {cur.fetchone()['nb']}")
    cur.execute("SELECT COUNT(*) AS nb FROM intervention_task WHERE assigned_to IS NULL")
    print(f"  intervention_task.assigned_to NULL restant : {cur.fetchone()['nb']}")
    cur.execute("SELECT COUNT(*) AS nb FROM intervention WHERE updated_by IS NULL")
    print(f"  intervention.updated_by NULL : {cur.fetchone()['nb']}")


def main():
    parser = argparse.ArgumentParser(description="Restaure les UUIDs tech perdus lors de la migration.")
    parser.add_argument("--apply", action="store_true", help="Applique les modifications (defaut : dry-run)")
    args = parser.parse_args()

    if args.apply:
        with get_dict_cursor() as cur:
            apply(cur)
        print("\nCommit effectue.")
    else:
        with get_dict_cursor(autocommit=True) as cur:
            dry_run(cur)


if __name__ == "__main__":
    main()
