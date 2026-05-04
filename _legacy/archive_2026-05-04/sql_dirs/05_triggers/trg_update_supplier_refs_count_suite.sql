-- ============================================================================
-- Script de migration - Suite (sans ajout de colonne)
-- Optimisation du compte de références fournisseurs
-- ============================================================================
-- Ce script suppose que la colonne supplier_refs_count existe déjà
-- Il crée : index, fonction trigger, triggers, et initialise les données
-- ============================================================================

-- 1. Créer l'index pour optimiser les requêtes sur supplier_refs_count
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_stock_item_supplier_refs_count 
ON public.stock_item(supplier_refs_count);

COMMENT ON INDEX idx_stock_item_supplier_refs_count IS 
'Index pour optimiser les filtres et tris sur le nombre de références fournisseurs';


-- 2. Créer la fonction trigger qui maintient le compte
-- ============================================================================
CREATE OR REPLACE FUNCTION public.fn_update_supplier_refs_count()
RETURNS TRIGGER AS $$
BEGIN
    -- Cas INSERT : incrémenter le compte de l'article
    IF (TG_OP = 'INSERT') THEN
        UPDATE public.stock_item
        SET supplier_refs_count = supplier_refs_count + 1
        WHERE id = NEW.stock_item_id;
        RETURN NEW;
    END IF;

    -- Cas DELETE : décrémenter le compte de l'article
    IF (TG_OP = 'DELETE') THEN
        UPDATE public.stock_item
        SET supplier_refs_count = GREATEST(0, supplier_refs_count - 1)
        WHERE id = OLD.stock_item_id;
        RETURN OLD;
    END IF;

    -- Cas UPDATE : si stock_item_id change, ajuster les deux articles
    IF (TG_OP = 'UPDATE') THEN
        IF (OLD.stock_item_id != NEW.stock_item_id) THEN
            -- Décrémenter l'ancien article
            UPDATE public.stock_item
            SET supplier_refs_count = GREATEST(0, supplier_refs_count - 1)
            WHERE id = OLD.stock_item_id;
            
            -- Incrémenter le nouvel article
            UPDATE public.stock_item
            SET supplier_refs_count = supplier_refs_count + 1
            WHERE id = NEW.stock_item_id;
        END IF;
        RETURN NEW;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION public.fn_update_supplier_refs_count() IS 
'Fonction trigger pour maintenir automatiquement le champ supplier_refs_count dans stock_item';


-- 3. Créer les triggers sur stock_item_supplier
-- ============================================================================

-- Trigger INSERT
DROP TRIGGER IF EXISTS trg_stock_item_supplier_refs_count_insert ON public.stock_item_supplier;
CREATE TRIGGER trg_stock_item_supplier_refs_count_insert
AFTER INSERT ON public.stock_item_supplier
FOR EACH ROW
EXECUTE FUNCTION public.fn_update_supplier_refs_count();

COMMENT ON TRIGGER trg_stock_item_supplier_refs_count_insert ON public.stock_item_supplier IS 
'Incrémente supplier_refs_count quand une référence fournisseur est ajoutée';

-- Trigger UPDATE
DROP TRIGGER IF EXISTS trg_stock_item_supplier_refs_count_update ON public.stock_item_supplier;
CREATE TRIGGER trg_stock_item_supplier_refs_count_update
AFTER UPDATE ON public.stock_item_supplier
FOR EACH ROW
WHEN (OLD.stock_item_id IS DISTINCT FROM NEW.stock_item_id)
EXECUTE FUNCTION public.fn_update_supplier_refs_count();

COMMENT ON TRIGGER trg_stock_item_supplier_refs_count_update ON public.stock_item_supplier IS 
'Met à jour supplier_refs_count quand une référence change d''article';

-- Trigger DELETE
DROP TRIGGER IF EXISTS trg_stock_item_supplier_refs_count_delete ON public.stock_item_supplier;
CREATE TRIGGER trg_stock_item_supplier_refs_count_delete
AFTER DELETE ON public.stock_item_supplier
FOR EACH ROW
EXECUTE FUNCTION public.fn_update_supplier_refs_count();

COMMENT ON TRIGGER trg_stock_item_supplier_refs_count_delete ON public.stock_item_supplier IS 
'Décrémente supplier_refs_count quand une référence fournisseur est supprimée';


-- 4. Initialiser les valeurs pour les données existantes
-- ============================================================================
DO $$
DECLARE
    v_updated_count INTEGER;
BEGIN
    RAISE NOTICE '🔄 Initialisation des valeurs existantes...';
    
    -- Mettre à jour tous les articles avec leur compte actuel
    UPDATE public.stock_item si
    SET supplier_refs_count = (
        SELECT COUNT(*)
        FROM public.stock_item_supplier sis
        WHERE sis.stock_item_id = si.id
    );
    
    GET DIAGNOSTICS v_updated_count = ROW_COUNT;
    RAISE NOTICE '✅ % articles mis à jour avec leur nombre de références', v_updated_count;
    
    -- Vérification : afficher quelques exemples
    RAISE NOTICE '📊 Exemples de valeurs initialisées :';
    PERFORM (
        SELECT string_agg(
            format('  - %s : %s référence(s)', si.ref, si.supplier_refs_count),
            E'\n'
        )
        FROM (
            SELECT ref, supplier_refs_count
            FROM public.stock_item
            ORDER BY supplier_refs_count DESC, ref
            LIMIT 5
        ) si
    );
END $$;


-- 5. Rapport final
-- ============================================================================
DO $$
DECLARE
    v_total_items INTEGER;
    v_items_with_refs INTEGER;
    v_total_refs INTEGER;
    v_avg_refs NUMERIC;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '╔════════════════════════════════════════════════════════════════╗';
    RAISE NOTICE '║           MIGRATION TERMINÉE AVEC SUCCÈS                       ║';
    RAISE NOTICE '╚════════════════════════════════════════════════════════════════╝';
    RAISE NOTICE '';
    
    -- Statistiques
    SELECT 
        COUNT(*),
        COUNT(*) FILTER (WHERE supplier_refs_count > 0),
        SUM(supplier_refs_count),
        ROUND(AVG(supplier_refs_count), 2)
    INTO v_total_items, v_items_with_refs, v_total_refs, v_avg_refs
    FROM public.stock_item;
    
    RAISE NOTICE '📊 Statistiques :';
    RAISE NOTICE '  - Articles totaux : %', v_total_items;
    RAISE NOTICE '  - Articles avec références : %', v_items_with_refs;
    RAISE NOTICE '  - Références totales : %', v_total_refs;
    RAISE NOTICE '  - Moyenne par article : %', v_avg_refs;
    RAISE NOTICE '';
    RAISE NOTICE '✅ Éléments créés :';
    RAISE NOTICE '  - Index : idx_stock_item_supplier_refs_count';
    RAISE NOTICE '  - Fonction : fn_update_supplier_refs_count()';
    RAISE NOTICE '  - 3 triggers sur stock_item_supplier (INSERT/UPDATE/DELETE)';
    RAISE NOTICE '';
    RAISE NOTICE '📝 Prochaines étapes :';
    RAISE NOTICE '  1. Exécuter les tests : db/schema/05_triggers/test_supplier_refs_count.sql';
    RAISE NOTICE '  2. Redémarrer l''application';
    RAISE NOTICE '  3. Vérifier que les performances sont améliorées';
    RAISE NOTICE '';
END $$;
