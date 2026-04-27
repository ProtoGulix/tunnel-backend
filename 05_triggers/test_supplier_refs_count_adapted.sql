-- ============================================================================
-- Tests pour les triggers supplier_refs_count
-- Adaptés à la structure réelle de la base de données
-- ============================================================================

BEGIN;

DO $$
DECLARE
    v_test_item_id UUID;
    v_test_item_id_2 UUID;
    v_supplier_id UUID;
    v_ref_id UUID;
    v_count INTEGER;
BEGIN
    -- Récupérer un item existant pour les tests
    SELECT id INTO v_test_item_id FROM stock_item LIMIT 1;
    SELECT id INTO v_test_item_id_2 FROM stock_item OFFSET 1 LIMIT 1;
    SELECT id INTO v_supplier_id FROM supplier LIMIT 1;
    
    IF v_test_item_id IS NULL OR v_supplier_id IS NULL THEN
        RAISE EXCEPTION 'Pas de données de test disponibles';
    END IF;
    
    RAISE NOTICE '';
    RAISE NOTICE '╔════════════════════════════════════════════════════════════════╗';
    RAISE NOTICE '║           TESTS DES TRIGGERS SUPPLIER_REFS_COUNT               ║';
    RAISE NOTICE '╚════════════════════════════════════════════════════════════════╝';
    RAISE NOTICE '';
    
    -- ========================================================================
    -- TEST 1 : État initial
    -- ========================================================================
    RAISE NOTICE '=== TEST 1 : État initial ===';
    
    SELECT supplier_refs_count INTO v_count FROM stock_item WHERE id = v_test_item_id;
    RAISE NOTICE '  Article % : supplier_refs_count = %', v_test_item_id, v_count;
    
    IF v_count IS NULL THEN
        RAISE EXCEPTION '❌ ERREUR : supplier_refs_count est NULL';
    END IF;
    
    RAISE NOTICE '  ✅ TEST 1 RÉUSSI : Champ initialisé';
    RAISE NOTICE '';
    
    -- ========================================================================
    -- TEST 2 : INSERT - Ajout d''une référence
    -- ========================================================================
    RAISE NOTICE '=== TEST 2 : INSERT - Ajout référence ===';
    
    -- Sauvegarder le count actuel
    SELECT supplier_refs_count INTO v_count FROM stock_item WHERE id = v_test_item_id;
    
    -- Ajouter une référence
    INSERT INTO stock_item_supplier (stock_item_id, supplier_id, supplier_ref, is_preferred)
    VALUES (v_test_item_id, v_supplier_id, 'TEST-REF-INSERT', false)
    RETURNING id INTO v_ref_id;
    
    -- Vérifier l'incrémentation
    IF (SELECT supplier_refs_count FROM stock_item WHERE id = v_test_item_id) = v_count + 1 THEN
        RAISE NOTICE '  ✅ TEST 2 RÉUSSI : Count incrémenté de % à %', v_count, v_count + 1;
    ELSE
        RAISE EXCEPTION '❌ ERREUR : Count devrait être %, trouvé %', 
            v_count + 1, 
            (SELECT supplier_refs_count FROM stock_item WHERE id = v_test_item_id);
    END IF;
    RAISE NOTICE '';
    
    -- ========================================================================
    -- TEST 3 : DELETE - Suppression d''une référence
    -- ========================================================================
    RAISE NOTICE '=== TEST 3 : DELETE - Suppression référence ===';
    
    -- Sauvegarder le count actuel
    SELECT supplier_refs_count INTO v_count FROM stock_item WHERE id = v_test_item_id;
    
    -- Supprimer la référence
    DELETE FROM stock_item_supplier WHERE id = v_ref_id;
    
    -- Vérifier la décrémentation
    IF (SELECT supplier_refs_count FROM stock_item WHERE id = v_test_item_id) = v_count - 1 THEN
        RAISE NOTICE '  ✅ TEST 3 RÉUSSI : Count décrémenté de % à %', v_count, v_count - 1;
    ELSE
        RAISE EXCEPTION '❌ ERREUR : Count devrait être %, trouvé %', 
            v_count - 1, 
            (SELECT supplier_refs_count FROM stock_item WHERE id = v_test_item_id);
    END IF;
    RAISE NOTICE '';
    
    -- ========================================================================
    -- TEST 4 : UPDATE - Changement de stock_item_id
    -- ========================================================================
    RAISE NOTICE '=== TEST 4 : UPDATE - Changement stock_item_id ===';
    
    -- Créer une nouvelle référence
    INSERT INTO stock_item_supplier (stock_item_id, supplier_id, supplier_ref, is_preferred)
    VALUES (v_test_item_id, v_supplier_id, 'TEST-REF-UPDATE', false)
    RETURNING id INTO v_ref_id;
    
    -- Sauvegarder les counts
    DECLARE
        v_count_1 INTEGER;
        v_count_2 INTEGER;
    BEGIN
        SELECT supplier_refs_count INTO v_count_1 FROM stock_item WHERE id = v_test_item_id;
        SELECT supplier_refs_count INTO v_count_2 FROM stock_item WHERE id = v_test_item_id_2;
        
        RAISE NOTICE '  Avant UPDATE :';
        RAISE NOTICE '    Article 1 : %', v_count_1;
        RAISE NOTICE '    Article 2 : %', v_count_2;
        
        -- Déplacer la référence vers le second article
        UPDATE stock_item_supplier 
        SET stock_item_id = v_test_item_id_2
        WHERE id = v_ref_id;
        
        -- Vérifier les deux articles
        IF (SELECT supplier_refs_count FROM stock_item WHERE id = v_test_item_id) = v_count_1 - 1 AND
           (SELECT supplier_refs_count FROM stock_item WHERE id = v_test_item_id_2) = v_count_2 + 1 THEN
            RAISE NOTICE '  Après UPDATE :';
            RAISE NOTICE '    Article 1 : % → %', v_count_1, v_count_1 - 1;
            RAISE NOTICE '    Article 2 : % → %', v_count_2, v_count_2 + 1;
            RAISE NOTICE '  ✅ TEST 4 RÉUSSI : Les deux articles mis à jour correctement';
        ELSE
            RAISE EXCEPTION '❌ ERREUR UPDATE : Counts incorrects';
        END IF;
    END;
    
    -- Nettoyer
    DELETE FROM stock_item_supplier WHERE id = v_ref_id;
    RAISE NOTICE '';
    
    -- ========================================================================
    -- TEST 5 : Cohérence globale
    -- ========================================================================
    RAISE NOTICE '=== TEST 5 : Cohérence globale ===';
    RAISE NOTICE '  Vérification que tous les counts correspondent aux counts réels...';
    
    DECLARE
        v_incoherent_count INTEGER;
    BEGIN
        -- Compter les articles avec des counts incohérents
        SELECT COUNT(*) INTO v_incoherent_count
        FROM (
            SELECT 
                si.id,
                si.supplier_refs_count,
                COUNT(sis.id) as actual_count
            FROM stock_item si
            LEFT JOIN stock_item_supplier sis ON sis.stock_item_id = si.id
            GROUP BY si.id, si.supplier_refs_count
            HAVING si.supplier_refs_count != COUNT(sis.id)
        ) incohérences;
        
        IF v_incoherent_count = 0 THEN
            RAISE NOTICE '  ✅ TEST 5 RÉUSSI : Tous les counts sont cohérents';
        ELSE
            RAISE EXCEPTION '❌ ERREUR : % articles avec counts incohérents', v_incoherent_count;
        END IF;
    END;
    RAISE NOTICE '';
    
    -- ========================================================================
    -- RÉSUMÉ
    -- ========================================================================
    RAISE NOTICE '╔════════════════════════════════════════════════════════════════╗';
    RAISE NOTICE '║           ✅ TOUS LES TESTS RÉUSSIS !                          ║';
    RAISE NOTICE '╚════════════════════════════════════════════════════════════════╝';
    RAISE NOTICE '';
    RAISE NOTICE '✓ Trigger INSERT : Incrémente correctement';
    RAISE NOTICE '✓ Trigger DELETE : Décrémente correctement';
    RAISE NOTICE '✓ Trigger UPDATE : Met à jour les deux articles';
    RAISE NOTICE '✓ Cohérence globale : Tous les counts sont justes';
    RAISE NOTICE '';
    RAISE NOTICE 'ℹ️  Note : Ce test utilise ROLLBACK pour ne pas modifier les données';
    
END $$;

ROLLBACK;
