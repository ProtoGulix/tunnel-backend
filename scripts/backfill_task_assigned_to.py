"""
Backfille assigned_to et due_date sur les tâches préventives existantes.

- assigned_to : depuis intervention.tech_id (si tâche non assignée)
- due_date    : depuis intervention.reported_date (si due_date absent, origin 'plan')
"""
import psycopg2

conn = psycopg2.connect(
    "postgresql://directus:directus@192.168.1.161:5432/directus")
cur = conn.cursor()

cur.execute("""
    UPDATE intervention_task it
    SET
        assigned_to = COALESCE(it.assigned_to, i.tech_id),
        due_date    = COALESCE(it.due_date, i.reported_date)
    FROM intervention i
    WHERE it.intervention_id = i.id
      AND it.origin = 'plan'
      AND (it.assigned_to IS NULL OR it.due_date IS NULL)
      AND (i.tech_id IS NOT NULL OR i.reported_date IS NOT NULL)
""")

print(f"Tâches mises à jour : {cur.rowcount}")
conn.commit()
cur.close()
conn.close()
