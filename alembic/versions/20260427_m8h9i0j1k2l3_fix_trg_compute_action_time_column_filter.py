"""Fix trigger trg_compute_action_time — ne se déclenche que sur les colonnes temps

Revision ID: m8h9i0j1k2l3
Revises: l7g8h9i0j1k2
Create Date: 2026-04-27

Problème : le trigger BEFORE INSERT OR UPDATE se déclenchait sur tout UPDATE,
y compris un simple SET task_id. À ce moment la ligne avait déjà time_spent
calculé (par l'INSERT) ET action_start/action_end → exception « Ambiguïté ».

Correction : remplacer le trigger sans filtre par deux triggers :
  - BEFORE INSERT → même logique
  - BEFORE UPDATE OF time_spent, action_start, action_end → même logique
Ainsi un UPDATE SET task_id (seul) ne déclenche rien.
"""
from alembic import op

revision = "m8h9i0j1k2l3"
down_revision = "l7g8h9i0j1k2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS trg_compute_action_time ON public.intervention_action"
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.fn_compute_action_time()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        DECLARE
            has_bounds BOOLEAN := (NEW.action_start IS NOT NULL AND NEW.action_end IS NOT NULL);
            has_time   BOOLEAN := (NEW.time_spent IS NOT NULL);
        BEGIN
            IF has_bounds AND has_time THEN
                RAISE EXCEPTION 'Ambiguïté : fournir soit les bornes horaires soit time_spent, pas les deux';
            END IF;
            IF NOT has_bounds AND NOT has_time THEN
                RAISE EXCEPTION 'time_spent ou les bornes action_start/action_end sont requis';
            END IF;
            IF has_bounds THEN
                IF EXTRACT(MINUTE FROM NEW.action_start) NOT IN (0, 15, 30, 45) THEN
                    RAISE EXCEPTION 'action_start doit être un multiple de 15 minutes';
                END IF;
                IF EXTRACT(MINUTE FROM NEW.action_end) NOT IN (0, 15, 30, 45) THEN
                    RAISE EXCEPTION 'action_end doit être un multiple de 15 minutes';
                END IF;
                IF NEW.action_end <= NEW.action_start THEN
                    RAISE EXCEPTION 'action_end doit être postérieur à action_start';
                END IF;
                NEW.time_spent := EXTRACT(EPOCH FROM (NEW.action_end - NEW.action_start)) / 3600.0;
            END IF;
            IF has_time THEN
                IF (NEW.time_spent * 4) <> FLOOR(NEW.time_spent * 4) THEN
                    RAISE EXCEPTION 'time_spent doit être un multiple de 0.25';
                END IF;
                IF NEW.time_spent < 0.25 THEN
                    RAISE EXCEPTION 'time_spent minimum est 0.25h';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_compute_action_time_insert
            BEFORE INSERT ON public.intervention_action
            FOR EACH ROW EXECUTE FUNCTION public.fn_compute_action_time()
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_compute_action_time_update
            BEFORE UPDATE OF time_spent, action_start, action_end
            ON public.intervention_action
            FOR EACH ROW EXECUTE FUNCTION public.fn_compute_action_time()
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS trg_compute_action_time_insert ON public.intervention_action"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS trg_compute_action_time_update ON public.intervention_action"
    )
    op.execute(
        """
        CREATE TRIGGER trg_compute_action_time
            BEFORE INSERT OR UPDATE ON public.intervention_action
            FOR EACH ROW EXECUTE FUNCTION public.fn_compute_action_time()
        """
    )
