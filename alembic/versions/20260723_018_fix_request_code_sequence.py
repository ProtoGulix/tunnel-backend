"""Corrige fn_generate_request_code() : COUNT(*)+1 → MAX(numéro extrait)+1

fn_generate_request_code() calculait le prochain numéro de séquence DI-YYYY-NNNN
avec COUNT(*)+1 sur les codes de l'année. Après suppression d'une ou plusieurs
demandes (ex: DELETE /intervention-requests/{id} sur une DI en erreur de saisie),
COUNT(*) chute sous le numéro max déjà attribué, et COUNT(*)+1 retombe sur un code
déjà utilisé : violation de la contrainte unique intervention_request_code_key,
bloquant toute création de DI tant que le décalage persiste.

Remplacé par MAX(numéro extrait)+1, insensible aux trous laissés par des
suppressions.

Revision ID: 018_fix_request_code_sequence
Revises: 017_audit_rule_table
Create Date: 2026-07-23
"""
from __future__ import annotations

from typing import Union

from alembic import op

revision: str = "018_fix_request_code_sequence"
down_revision: Union[str, None] = "017_audit_rule_table"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


_NEW_FN = """
    CREATE OR REPLACE FUNCTION public.fn_generate_request_code()
     RETURNS trigger
     LANGUAGE plpgsql
    AS $function$
    DECLARE
        v_year TEXT := to_char(now(), 'YYYY');
        v_seq  INT;
    BEGIN
        SELECT COALESCE(MAX((regexp_match(code, 'DI-' || v_year || '-(\\d+)'))[1]::int), 0) + 1
        INTO v_seq
        FROM public.intervention_request
        WHERE code LIKE 'DI-' || v_year || '-%';

        NEW.code := 'DI-' || v_year || '-' || lpad(v_seq::TEXT, 4, '0');
        RETURN NEW;
    END;
    $function$
"""

_OLD_FN = """
    CREATE OR REPLACE FUNCTION public.fn_generate_request_code()
     RETURNS trigger
     LANGUAGE plpgsql
    AS $function$
    DECLARE
        v_year TEXT := to_char(now(), 'YYYY');
        v_seq  INT;
    BEGIN
        SELECT COUNT(*) + 1
        INTO v_seq
        FROM public.intervention_request
        WHERE code LIKE 'DI-' || v_year || '-%';

        NEW.code := 'DI-' || v_year || '-' || lpad(v_seq::TEXT, 4, '0');
        RETURN NEW;
    END;
    $function$
"""


def upgrade() -> None:
    op.execute(_NEW_FN)


def downgrade() -> None:
    op.execute(_OLD_FN)
