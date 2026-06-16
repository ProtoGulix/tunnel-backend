"""Nouveau système de référencement des pièces : part, part_manufacturer_ref, part_supplier_ref

Remplace stock_item / manufacturer_item / stock_item_supplier par un modèle centré
sur la référence fabricant, avec référence interne séquentielle P000001.

Conçue pour être exécutée en production sans intervention manuelle :
- Toutes les anomalies de données sont traitées dans la migration elle-même.
- Idempotente (IF NOT EXISTS / ON CONFLICT).

Revision ID: 009_parts_schema
Revises: 008_audit_task_user_reasons
Create Date: 2026-06-16
"""
from __future__ import annotations

from typing import Union

from alembic import op

revision: str = "009_parts_schema"
down_revision: Union[str, None] = "008_audit_task_user_reasons"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:

    # =========================================================================
    # BLOC A — Création des nouvelles structures
    # =========================================================================

    # A1. Séquence pour internal_ref P000001 → P999999
    op.execute(
        "CREATE SEQUENCE IF NOT EXISTS part_internal_ref_seq "
        "START 1 INCREMENT 1 MINVALUE 1 MAXVALUE 999999 NO CYCLE"
    )

    # A2. Table part
    op.execute("""
        CREATE TABLE IF NOT EXISTS part (
            id              UUID NOT NULL DEFAULT uuid_generate_v4(),
            internal_ref    TEXT NOT NULL
                                DEFAULT ('P' || lpad(nextval('part_internal_ref_seq')::text, 6, '0')),
            family_code     VARCHAR(20) NOT NULL,
            sub_family_code VARCHAR(20) NOT NULL,
            unit            VARCHAR(50),
            location        TEXT,
            qty_in_stock    INTEGER NOT NULL DEFAULT 0,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (id),
            CONSTRAINT part_internal_ref_unique UNIQUE (internal_ref),
            CONSTRAINT part_family_code_fkey
                FOREIGN KEY (family_code) REFERENCES stock_family(code),
            CONSTRAINT part_sub_family_code_fkey
                FOREIGN KEY (sub_family_code, family_code)
                    REFERENCES stock_sub_family(code, family_code)
        )
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_part_family_code     ON part(family_code)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_part_sub_family_code ON part(family_code, sub_family_code)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_part_internal_ref    ON part(internal_ref)")

    # A3. Table part_manufacturer_ref
    op.execute("""
        CREATE TABLE IF NOT EXISTS part_manufacturer_ref (
            id                UUID NOT NULL DEFAULT uuid_generate_v4(),
            part_id           UUID NOT NULL,
            manufacturer_name TEXT NOT NULL,
            manufacturer_ref  TEXT NOT NULL,
            label             TEXT,
            is_preferred      BOOLEAN NOT NULL DEFAULT false,
            created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (id),
            CONSTRAINT part_manufacturer_ref_part_fk
                FOREIGN KEY (part_id) REFERENCES part(id) ON DELETE CASCADE,
            CONSTRAINT part_manufacturer_ref_unique
                UNIQUE (part_id, manufacturer_name, manufacturer_ref)
        )
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_part_mfr_ref_part_id   ON part_manufacturer_ref(part_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_part_mfr_ref_preferred "
        "ON part_manufacturer_ref(part_id, is_preferred) WHERE is_preferred = true"
    )

    # A4. Table part_supplier_ref
    op.execute("""
        CREATE TABLE IF NOT EXISTS part_supplier_ref (
            id                       UUID NOT NULL DEFAULT uuid_generate_v4(),
            part_manufacturer_ref_id UUID NOT NULL,
            supplier_id              UUID NOT NULL,
            supplier_ref             TEXT NOT NULL,
            unit_price               NUMERIC(10, 2),
            min_order_quantity       INTEGER NOT NULL DEFAULT 1,
            delivery_time_days       INTEGER,
            is_preferred             BOOLEAN NOT NULL DEFAULT false,
            product_url              TEXT,
            created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (id),
            CONSTRAINT part_supplier_ref_mfr_fk
                FOREIGN KEY (part_manufacturer_ref_id)
                    REFERENCES part_manufacturer_ref(id) ON DELETE CASCADE,
            CONSTRAINT part_supplier_ref_supplier_fk
                FOREIGN KEY (supplier_id) REFERENCES supplier(id),
            CONSTRAINT part_supplier_ref_unique
                UNIQUE (part_manufacturer_ref_id, supplier_id, supplier_ref)
        )
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_part_supplier_ref_mfr_id     ON part_supplier_ref(part_manufacturer_ref_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_part_supplier_ref_supplier_id ON part_supplier_ref(supplier_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_part_supplier_ref_preferred "
        "ON part_supplier_ref(part_manufacturer_ref_id, is_preferred) WHERE is_preferred = true"
    )

    # A5. Triggers updated_at (réutilise la fonction existante update_updated_at_column)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_trigger WHERE tgname = 'trg_part_updated_at'
            ) THEN
                CREATE TRIGGER trg_part_updated_at
                BEFORE UPDATE ON part
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            END IF;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_trigger WHERE tgname = 'trg_part_mfr_ref_updated_at'
            ) THEN
                CREATE TRIGGER trg_part_mfr_ref_updated_at
                BEFORE UPDATE ON part_manufacturer_ref
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            END IF;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_trigger WHERE tgname = 'trg_part_supplier_ref_updated_at'
            ) THEN
                CREATE TRIGGER trg_part_supplier_ref_updated_at
                BEFORE UPDATE ON part_supplier_ref
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            END IF;
        END $$
    """)

    # =========================================================================
    # BLOC B — Migration stock_item → part
    #
    # internal_ref : on génère une vraie séquence P000001 pour chaque ligne.
    # On n'utilise PAS l'ancienne ref FAM-SFAM-SPEC-DIM car elle disparaît.
    # =========================================================================
    op.execute("""
        INSERT INTO part (id, internal_ref, family_code, sub_family_code, unit, location, qty_in_stock, created_at, updated_at)
        SELECT
            si.id,
            'P' || lpad(nextval('part_internal_ref_seq')::text, 6, '0'),
            si.family_code,
            si.sub_family_code,
            si.unit,
            si.location,
            COALESCE(si.quantity, 0),
            now(),
            now()
        FROM stock_item si
        ORDER BY si.id          -- ordre déterministe pour que P000001 = même article en prod et en test
        ON CONFLICT (id) DO NOTHING
    """)

    # =========================================================================
    # BLOC C — Migration manufacturer_item → part_manufacturer_ref
    #
    # Étape C1 : refs liées via stock_item_supplier.manufacturer_item_id
    # Étape C2 : refs liées via stock_item.manufacturer_item_id (lien direct)
    # Étape C3 : rattrapage des stock_item sans aucune ref fabricant
    #            → ref synthétique manufacturer_name='INCONNU' pour respecter
    #              la contrainte métier "une part doit avoir au moins une ref fabricant"
    # Étape C4 : garantir is_preferred = true sur exactement une ref par part
    # =========================================================================

    # C1 — via stock_item_supplier.manufacturer_item_id
    op.execute("""
        INSERT INTO part_manufacturer_ref
            (id, part_id, manufacturer_name, manufacturer_ref, label, is_preferred, created_at, updated_at)
        SELECT
            uuid_generate_v4(),
            sis.stock_item_id,
            mi.manufacturer_name,
            COALESCE(NULLIF(trim(mi.manufacturer_ref), ''), 'REF-INCONNUE'),
            mi.designation,
            false,
            now(),
            now()
        FROM (
            SELECT DISTINCT stock_item_id, manufacturer_item_id
            FROM stock_item_supplier
            WHERE manufacturer_item_id IS NOT NULL
        ) sis
        JOIN manufacturer_item mi ON mi.id = sis.manufacturer_item_id
        WHERE EXISTS (SELECT 1 FROM part p WHERE p.id = sis.stock_item_id)
        ON CONFLICT (part_id, manufacturer_name, manufacturer_ref) DO NOTHING
    """)

    # C2 — via stock_item.manufacturer_item_id (lien direct, marque is_preferred=true)
    op.execute("""
        INSERT INTO part_manufacturer_ref
            (id, part_id, manufacturer_name, manufacturer_ref, label, is_preferred, created_at, updated_at)
        SELECT
            uuid_generate_v4(),
            si.id,
            mi.manufacturer_name,
            COALESCE(NULLIF(trim(mi.manufacturer_ref), ''), 'REF-INCONNUE'),
            mi.designation,
            true,
            now(),
            now()
        FROM stock_item si
        JOIN manufacturer_item mi ON mi.id = si.manufacturer_item_id
        WHERE si.manufacturer_item_id IS NOT NULL
          AND EXISTS (SELECT 1 FROM part p WHERE p.id = si.id)
        ON CONFLICT (part_id, manufacturer_name, manufacturer_ref)
            DO UPDATE SET is_preferred = true
    """)

    # C3 — Rattrapage : stock_item sans aucune ref fabricant connue
    #      manufacturer_name = 'INCONNU', manufacturer_ref = ancienne ref stock_item,
    #      label = nom de l'article (meilleure info disponible)
    op.execute("""
        INSERT INTO part_manufacturer_ref
            (id, part_id, manufacturer_name, manufacturer_ref, label, is_preferred, created_at, updated_at)
        SELECT
            uuid_generate_v4(),
            si.id,
            'INCONNU',
            COALESCE(NULLIF(trim(si.ref), ''), si.id::text),
            si.name,
            true,
            now(),
            now()
        FROM stock_item si
        WHERE NOT EXISTS (
            SELECT 1 FROM part_manufacturer_ref pmr WHERE pmr.part_id = si.id
        )
        ON CONFLICT (part_id, manufacturer_name, manufacturer_ref) DO NOTHING
    """)

    # C4 — Garantir exactement un is_preferred = true par part
    #      Cas 1 : aucune ref préférée → on en élit une (la plus ancienne)
    op.execute("""
        UPDATE part_manufacturer_ref pmr
        SET is_preferred = true
        WHERE pmr.id IN (
            SELECT DISTINCT ON (part_id) id
            FROM part_manufacturer_ref
            WHERE part_id NOT IN (
                SELECT part_id FROM part_manufacturer_ref WHERE is_preferred = true
            )
            ORDER BY part_id, created_at ASC
        )
    """)
    #      Cas 2 : plusieurs refs préférées → on n'en garde qu'une (la plus ancienne)
    op.execute("""
        UPDATE part_manufacturer_ref
        SET is_preferred = false
        WHERE id IN (
            SELECT id FROM (
                SELECT id,
                       row_number() OVER (PARTITION BY part_id ORDER BY created_at ASC) AS rn
                FROM part_manufacturer_ref
                WHERE is_preferred = true
            ) ranked
            WHERE rn > 1
        )
    """)

    # =========================================================================
    # BLOC D — Migration stock_item_supplier → part_supplier_ref
    #
    # Résolution de la FK part_manufacturer_ref_id :
    #   - Si sis.manufacturer_item_id IS NOT NULL → joint via manufacturer_item
    #   - Si sis.manufacturer_item_id IS NULL     → prend la ref préférée de la part
    #     (cas des stock_item_supplier sans info fabricant)
    # =========================================================================
    op.execute("""
        INSERT INTO part_supplier_ref (
            id, part_manufacturer_ref_id, supplier_id, supplier_ref,
            unit_price, min_order_quantity, delivery_time_days,
            is_preferred, product_url, created_at, updated_at
        )
        SELECT
            sis.id,
            pmr.id,
            sis.supplier_id,
            sis.supplier_ref,
            sis.unit_price,
            COALESCE(sis.min_order_quantity, 1),
            sis.delivery_time_days,
            sis.is_preferred,
            sis.product_url,
            COALESCE(sis.created_at, now()),
            COALESCE(sis.updated_at, now())
        FROM stock_item_supplier sis
        JOIN part_manufacturer_ref pmr
            ON pmr.part_id = sis.stock_item_id
            AND (
                (
                    -- Liaison via manufacturer_item
                    sis.manufacturer_item_id IS NOT NULL
                    AND EXISTS (
                        SELECT 1 FROM manufacturer_item mi
                        WHERE mi.id = sis.manufacturer_item_id
                          AND mi.manufacturer_name = pmr.manufacturer_name
                          AND COALESCE(NULLIF(trim(mi.manufacturer_ref), ''), 'REF-INCONNUE') = pmr.manufacturer_ref
                    )
                )
                OR (
                    -- Pas de manufacturer_item → ref préférée de la part
                    sis.manufacturer_item_id IS NULL
                    AND pmr.is_preferred = true
                )
            )
        WHERE EXISTS (SELECT 1 FROM part p WHERE p.id = sis.stock_item_id)
        ON CONFLICT (part_manufacturer_ref_id, supplier_id, supplier_ref) DO NOTHING
    """)

    # =========================================================================
    # BLOC E — Colonnes part_id sur les tables dépendantes
    # =========================================================================

    # E1 — supplier_order_line.part_id
    op.execute("""
        ALTER TABLE supplier_order_line
        ADD COLUMN IF NOT EXISTS part_id UUID
            REFERENCES part(id) ON DELETE RESTRICT
    """)
    op.execute("""
        UPDATE supplier_order_line sol
        SET part_id = sol.stock_item_id
        WHERE sol.stock_item_id IS NOT NULL
          AND sol.part_id IS NULL
          AND EXISTS (SELECT 1 FROM part p WHERE p.id = sol.stock_item_id)
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_supplier_order_line_part_id ON supplier_order_line(part_id)"
    )

    # E2 — purchase_request.part_id
    op.execute("""
        ALTER TABLE purchase_request
        ADD COLUMN IF NOT EXISTS part_id UUID
            REFERENCES part(id) ON DELETE SET NULL
    """)
    op.execute("""
        UPDATE purchase_request pr
        SET part_id = pr.stock_item_id
        WHERE pr.stock_item_id IS NOT NULL
          AND pr.part_id IS NULL
          AND EXISTS (SELECT 1 FROM part p WHERE p.id = pr.stock_item_id)
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_purchase_request_part_id ON purchase_request(part_id)"
    )

    # =========================================================================
    # BLOC F — Validation intégrée : lève une erreur si un invariant est brisé
    #          Bloque la migration en prod avant qu'elle soit commitée.
    # =========================================================================
    op.execute("""
        DO $$
        DECLARE
            v_parts_sans_ref        INTEGER;
            v_parts_sans_preferred  INTEGER;
            v_multi_preferred       INTEGER;
            v_sol_sans_part_id      INTEGER;
            v_pr_sans_part_id       INTEGER;
        BEGIN
            SELECT COUNT(*) INTO v_parts_sans_ref
            FROM part p
            WHERE NOT EXISTS (
                SELECT 1 FROM part_manufacturer_ref pmr WHERE pmr.part_id = p.id
            );

            SELECT COUNT(*) INTO v_parts_sans_preferred
            FROM part p
            WHERE NOT EXISTS (
                SELECT 1 FROM part_manufacturer_ref pmr
                WHERE pmr.part_id = p.id AND pmr.is_preferred = true
            );

            SELECT COUNT(*) INTO v_multi_preferred
            FROM (
                SELECT part_id FROM part_manufacturer_ref
                WHERE is_preferred = true
                GROUP BY part_id HAVING COUNT(*) > 1
            ) x;

            SELECT COUNT(*) INTO v_sol_sans_part_id
            FROM supplier_order_line sol
            WHERE sol.stock_item_id IS NOT NULL
              AND sol.part_id IS NULL
              AND EXISTS (SELECT 1 FROM part p WHERE p.id = sol.stock_item_id);

            SELECT COUNT(*) INTO v_pr_sans_part_id
            FROM purchase_request pr
            WHERE pr.stock_item_id IS NOT NULL
              AND pr.part_id IS NULL
              AND EXISTS (SELECT 1 FROM part p WHERE p.id = pr.stock_item_id);

            IF v_parts_sans_ref > 0 THEN
                RAISE EXCEPTION 'Migration 009 : % part(s) sans aucune référence fabricant', v_parts_sans_ref;
            END IF;
            IF v_parts_sans_preferred > 0 THEN
                RAISE EXCEPTION 'Migration 009 : % part(s) sans référence fabricant préférée', v_parts_sans_preferred;
            END IF;
            IF v_multi_preferred > 0 THEN
                RAISE EXCEPTION 'Migration 009 : % part(s) avec plusieurs références fabricant préférées', v_multi_preferred;
            END IF;
            IF v_sol_sans_part_id > 0 THEN
                RAISE EXCEPTION 'Migration 009 : % supplier_order_line avec stock_item_id sans part_id rempli', v_sol_sans_part_id;
            END IF;
            IF v_pr_sans_part_id > 0 THEN
                RAISE EXCEPTION 'Migration 009 : % purchase_request avec stock_item_id sans part_id rempli', v_pr_sans_part_id;
            END IF;

            RAISE NOTICE 'Migration 009 : validation OK — tous les invariants respectés';
        END $$
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_purchase_request_part_id")
    op.execute("ALTER TABLE purchase_request DROP COLUMN IF EXISTS part_id")

    op.execute("DROP INDEX IF EXISTS idx_supplier_order_line_part_id")
    op.execute("ALTER TABLE supplier_order_line DROP COLUMN IF EXISTS part_id")

    op.execute("DROP TABLE IF EXISTS part_supplier_ref CASCADE")
    op.execute("DROP TABLE IF EXISTS part_manufacturer_ref CASCADE")
    op.execute("DROP TABLE IF EXISTS part CASCADE")

    op.execute("DROP SEQUENCE IF EXISTS part_internal_ref_seq")
