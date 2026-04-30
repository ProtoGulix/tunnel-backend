-- ============================================================================
-- trg_update_supplier_refs_count.sql - Maintenir le compte de références fournisseurs
-- ============================================================================
-- Optimisation : Calculer et stocker le nombre de références fournisseurs
-- pour chaque article au lieu de le recalculer côté frontend
--
-- Déclencheurs sur INSERT/UPDATE/DELETE de stock_item_supplier
-- pour mettre à jour automatiquement le champ supplier_refs_count
-- ============================================================================

-- Étape 1 : Ajouter la colonne supplier_refs_count à stock_item (si elle n'existe pas)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'stock_item' 
        AND column_name = 'supplier_refs_count'
    ) THEN
        ALTER TABLE public.stock_item 
        ADD COLUMN supplier_refs_count INTEGER DEFAULT 0 NOT NULL;
        
        COMMENT ON COLUMN public.stock_item.supplier_refs_count 
        IS 'Nombre de références fournisseurs (calculé automatiquement)';
    END IF;
END $$;

-- Étape 2 : Créer l'index pour améliorer les performances des requêtes
CREATE INDEX IF NOT EXISTS idx_stock_item_supplier_refs_count 
    ON public.stock_item(supplier_refs_count);

-- Étape 3 : Fonction pour recalculer le compte d'un article spécifique
CREATE OR REPLACE FUNCTION public.fn_update_supplier_refs_count()
RETURNS TRIGGER AS $$
DECLARE
    v_stock_item_id UUID;
    v_count INTEGER;
BEGIN
    -- Déterminer quel stock_item_id traiter
    IF (TG_OP = 'DELETE') THEN
        v_stock_item_id := OLD.stock_item_id;
    ELSE
        v_stock_item_id := NEW.stock_item_id;
    END IF;

    -- Si l'UPDATE change le stock_item_id, mettre à jour les deux items
    IF (TG_OP = 'UPDATE' AND OLD.stock_item_id IS DISTINCT FROM NEW.stock_item_id) THEN
        -- Mettre à jour l'ancien item
        SELECT COUNT(*) INTO v_count
        FROM public.stock_item_supplier
        WHERE stock_item_id = OLD.stock_item_id;
        
        UPDATE public.stock_item
        SET supplier_refs_count = v_count
        WHERE id = OLD.stock_item_id;
        
        -- Traiter le nouveau item ci-dessous
        v_stock_item_id := NEW.stock_item_id;
    END IF;

    -- Calculer le compte pour le stock_item_id concerné
    IF v_stock_item_id IS NOT NULL THEN
        SELECT COUNT(*) INTO v_count
        FROM public.stock_item_supplier
        WHERE stock_item_id = v_stock_item_id;
        
        UPDATE public.stock_item
        SET supplier_refs_count = v_count
        WHERE id = v_stock_item_id;
    END IF;

    -- Retourner la bonne valeur selon l'opération
    IF (TG_OP = 'DELETE') THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Étape 4 : Créer les triggers sur stock_item_supplier
DROP TRIGGER IF EXISTS trg_stock_item_supplier_refs_count_insert ON public.stock_item_supplier;
CREATE TRIGGER trg_stock_item_supplier_refs_count_insert
    AFTER INSERT ON public.stock_item_supplier
    FOR EACH ROW
    EXECUTE FUNCTION public.fn_update_supplier_refs_count();

DROP TRIGGER IF EXISTS trg_stock_item_supplier_refs_count_update ON public.stock_item_supplier;
CREATE TRIGGER trg_stock_item_supplier_refs_count_update
    AFTER UPDATE ON public.stock_item_supplier
    FOR EACH ROW
    EXECUTE FUNCTION public.fn_update_supplier_refs_count();

DROP TRIGGER IF EXISTS trg_stock_item_supplier_refs_count_delete ON public.stock_item_supplier;
CREATE TRIGGER trg_stock_item_supplier_refs_count_delete
    AFTER DELETE ON public.stock_item_supplier
    FOR EACH ROW
    EXECUTE FUNCTION public.fn_update_supplier_refs_count();

-- Étape 5 : Initialiser les comptes existants (migration de données)
DO $$
DECLARE
    v_updated_count INTEGER;
BEGIN
    WITH counts AS (
        SELECT stock_item_id, COUNT(*) as ref_count
        FROM public.stock_item_supplier
        GROUP BY stock_item_id
    )
    UPDATE public.stock_item si
    SET supplier_refs_count = COALESCE(c.ref_count, 0)
    FROM counts c
    WHERE si.id = c.stock_item_id;
    
    GET DIAGNOSTICS v_updated_count = ROW_COUNT;
    RAISE NOTICE 'Initialized supplier_refs_count for % stock items', v_updated_count;
    
    -- Mettre à 0 les items sans références
    UPDATE public.stock_item
    SET supplier_refs_count = 0
    WHERE supplier_refs_count IS NULL;
END $$;

-- Commentaire final
COMMENT ON COLUMN public.stock_item.supplier_refs_count IS 
'Nombre de références fournisseurs pour cet article (mis à jour automatiquement par trigger)';
