-- ============================================================================
-- fn_dispatch_purchase_requests.sql - Dispatch automatique des demandes d'achat
-- ============================================================================
-- Fonction stockée qui dispatche les demandes d'achat vers les paniers
-- fournisseurs en créant des lignes (supplier_order_line) pour chaque
-- article avec un fournisseur préféré défini.
--
-- Logique :
-- 1. Fetch demandes ouvertes (status = 'open')
-- 2. Pour chaque, trouver le fournisseur préféré de l'article lié
-- 3. Créer/utiliser panier du fournisseur (status = 'OPEN')
-- 4. Créer ligne dans le panier
-- 5. Mettre à jour demande à status = 'in_progress'
--
-- Retour : JSON { dispatched: [], toQualify: [], errors: [] }
-- ============================================================================

CREATE OR REPLACE FUNCTION public.dispatch_purchase_requests()
RETURNS json
LANGUAGE plpgsql
AS $$
DECLARE
  v_dispatched TEXT[] := ARRAY[]::TEXT[];
  v_to_qualify TEXT[] := ARRAY[]::TEXT[];
  v_errors json[] := ARRAY[]::json[];
  
  v_req RECORD;
  v_pref_supplier_id UUID;
  v_pref_supplier_ref VARCHAR;
  v_supplier_order_id UUID;
BEGIN
  -- Loop sur toutes les demandes ouvertes avec article lié
  FOR v_req IN
    SELECT 
      pr.id,
      pr.stock_item_id,
      pr.quantity,
      pr.status
    FROM public.purchase_request pr
    WHERE pr.status = 'open' 
      AND pr.stock_item_id IS NOT NULL
  LOOP
    -- Trouver le fournisseur préféré pour cet article
    SELECT 
      sis.supplier_id,
      sis.supplier_ref
    INTO v_pref_supplier_id, v_pref_supplier_ref
    FROM public.stock_item_supplier sis
    WHERE sis.stock_item_id = v_req.stock_item_id
      AND sis.is_preferred = TRUE
    LIMIT 1;

    -- Si pas de fournisseur préféré
    IF v_pref_supplier_id IS NULL THEN
      v_to_qualify := array_append(v_to_qualify, v_req.id::TEXT);
      CONTINUE;
    END IF;

    BEGIN
      -- Chercher panier OPEN du fournisseur, sinon en créer un
      SELECT so.id
      INTO v_supplier_order_id
      FROM public.supplier_order so
      WHERE so.supplier_id = v_pref_supplier_id
        AND so.status = 'OPEN'
      ORDER BY so.created_at DESC
      LIMIT 1;

      IF v_supplier_order_id IS NULL THEN
        -- Créer nouveau panier
        INSERT INTO public.supplier_order (supplier_id, status, total_amount)
        VALUES (v_pref_supplier_id, 'OPEN', 0)
        RETURNING id INTO v_supplier_order_id;
      END IF;

      -- Créer ou mettre à jour la ligne dans le panier (évite l'unicité supplier_order_id + stock_item_id)
      INSERT INTO public.supplier_order_line (
        supplier_order_id,
        stock_item_id,
        supplier_ref_snapshot,
        quantity,
        unit_price,
        total_price
      )
      VALUES (
        v_supplier_order_id,
        v_req.stock_item_id,
        v_pref_supplier_ref,
        COALESCE(v_req.quantity, 1),
        NULL,
        NULL
      )
      ON CONFLICT (supplier_order_id, stock_item_id)
      DO UPDATE SET quantity = COALESCE(public.supplier_order_line.quantity, 0) + COALESCE(EXCLUDED.quantity, 1);

      -- Mettre à jour statut demande à 'in_progress'
      UPDATE public.purchase_request
      SET status = 'in_progress'
      WHERE id = v_req.id;

      v_dispatched := array_append(v_dispatched, v_req.id::TEXT);

    EXCEPTION WHEN OTHERS THEN
      -- Log erreur et continue
      v_errors := array_append(
        v_errors,
        json_build_object(
          'id', v_req.id::TEXT,
          'error', SQLERRM
        )
      );
    END;
  END LOOP;

  -- Retourner résultat au format JSON
  RETURN json_build_object(
    'dispatched', COALESCE(v_dispatched, ARRAY[]::TEXT[]),
    'toQualify', COALESCE(v_to_qualify, ARRAY[]::TEXT[]),
    'errors', COALESCE(v_errors, ARRAY[]::json[])
  );
END;
$$;

-- Commentaire
COMMENT ON FUNCTION public.dispatch_purchase_requests() 
IS 'Dispatche les demandes d''achat (status=open) vers les paniers fournisseurs en créant supplier_order_line pour chaque article avec fournisseur préféré. Retourne {dispatched, toQualify, errors}.';
