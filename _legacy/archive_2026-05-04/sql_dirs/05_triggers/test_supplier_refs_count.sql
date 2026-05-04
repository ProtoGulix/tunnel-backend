-- ============================================================================
-- test_supplier_refs_count.sql - Tests du trigger supplier_refs_count
-- ============================================================================
-- Script de validation pour vérifier que le trigger fonctionne correctement
-- ============================================================================

-- Nettoyage (optionnel - décommenter si besoin)
-- DELETE FROM stock_item_supplier WHERE stock_item_id IN (SELECT id FROM stock_item WHERE ref LIKE 'TEST-%');
-- DELETE FROM stock_item WHERE ref LIKE 'TEST-%';

BEGIN;

-- ============================================================================
-- TEST 1 : Créer un article et vérifier l'initialisation à 0
-- ============================================================================
DO $$
DECLARE
    v_item_id UUID;
    v_count INTEGER;
BEGIN
    RAISE NOTICE '=== TEST 1 : Initialisation ===';
    
    INSERT INTO stock_item (ref, designation, family_code, unit)
    VALUES ('TEST-001', 'Article test 1', 'TEST', 'pcs')
    RETURNING id INTO v_item_id;
    
    SELECT supplier_refs_count INTO v_count
    FROM stock_item WHERE id = v_item_id;
    
    IF v_count = 0 THEN
        RAISE NOTICE '✓ TEST 1 PASSÉ : Compteur initialisé à 0';
    ELSE
        RAISE EXCEPTION '✗ TEST 1 ÉCHOUÉ : Compteur = % au lieu de 0', v_count;
    END IF;
END $$;

-- ============================================================================
-- TEST 2 : Ajouter une référence fournisseur (INSERT)
-- ============================================================================
DO $$
DECLARE
    v_item_id UUID;
    v_supplier_id UUID;
    v_count INTEGER;
BEGIN
    RAISE NOTICE '=== TEST 2 : INSERT référence fournisseur ===';
    
    -- Récupérer l'item de test
    SELECT id INTO v_item_id FROM stock_item WHERE ref = 'TEST-001';
    
    -- Récupérer ou créer un fournisseur
    SELECT id INTO v_supplier_id FROM supplier LIMIT 1;
    IF v_supplier_id IS NULL THEN
        INSERT INTO supplier (name, code) VALUES ('Test Supplier', 'TEST-SUPP')
        RETURNING id INTO v_supplier_id;
    END IF;
    
    -- Ajouter une référence
    INSERT INTO stock_item_supplier (stock_item_id, supplier_id, supplier_ref, is_preferred)
    VALUES (v_item_id, v_supplier_id, 'REF-TEST-001', false);
    
    -- Vérifier le compte
    SELECT supplier_refs_count INTO v_count
    FROM stock_item WHERE id = v_item_id;
    
    IF v_count = 1 THEN
        RAISE NOTICE '✓ TEST 2 PASSÉ : Compteur = 1 après INSERT';
    ELSE
        RAISE EXCEPTION '✗ TEST 2 ÉCHOUÉ : Compteur = % au lieu de 1', v_count;
    END IF;
END $$;

-- ============================================================================
-- TEST 3 : Ajouter une deuxième référence
-- ============================================================================
DO $$
DECLARE
    v_item_id UUID;
    v_supplier_id UUID;
    v_count INTEGER;
BEGIN
    RAISE NOTICE '=== TEST 3 : Ajouter deuxième référence ===';
    
    SELECT id INTO v_item_id FROM stock_item WHERE ref = 'TEST-001';
    
    -- Créer un second fournisseur
    INSERT INTO supplier (name, code) VALUES ('Test Supplier 2', 'TEST-SUPP2')
    RETURNING id INTO v_supplier_id;
    
    -- Ajouter deuxième référence
    INSERT INTO stock_item_supplier (stock_item_id, supplier_id, supplier_ref, is_preferred)
    VALUES (v_item_id, v_supplier_id, 'REF-TEST-002', true);
    
    SELECT supplier_refs_count INTO v_count
    FROM stock_item WHERE id = v_item_id;
    
    IF v_count = 2 THEN
        RAISE NOTICE '✓ TEST 3 PASSÉ : Compteur = 2 après 2 INSERT';
    ELSE
        RAISE EXCEPTION '✗ TEST 3 ÉCHOUÉ : Compteur = % au lieu de 2', v_count;
    END IF;
END $$;

-- ============================================================================
-- TEST 4 : Supprimer une référence (DELETE)
-- ============================================================================
DO $$
DECLARE
    v_item_id UUID;
    v_ref_id UUID;
    v_count INTEGER;
BEGIN
    RAISE NOTICE '=== TEST 4 : DELETE référence fournisseur ===';
    
    SELECT id INTO v_item_id FROM stock_item WHERE ref = 'TEST-001';
    
    -- Supprimer une référence
    SELECT id INTO v_ref_id 
    FROM stock_item_supplier 
    WHERE stock_item_id = v_item_id 
    LIMIT 1;
    
    DELETE FROM stock_item_supplier WHERE id = v_ref_id;
    
    SELECT supplier_refs_count INTO v_count
    FROM stock_item WHERE id = v_item_id;
    
    IF v_count = 1 THEN
        RAISE NOTICE '✓ TEST 4 PASSÉ : Compteur = 1 après DELETE';
    ELSE
        RAISE EXCEPTION '✗ TEST 4 ÉCHOUÉ : Compteur = % au lieu de 1', v_count;
    END IF;
END $$;

-- ============================================================================
-- TEST 5 : UPDATE qui change stock_item_id
-- ============================================================================
DO $$
DECLARE
    v_item1_id UUID;
    v_item2_id UUID;
    v_ref_id UUID;
    v_count1 INTEGER;
    v_count2 INTEGER;
BEGIN
    RAISE NOTICE '=== TEST 5 : UPDATE change stock_item_id ===';
    
    -- Créer un deuxième item
    INSERT INTO stock_item (ref, designation, family_code, unit)
    VALUES ('TEST-002', 'Article test 2', 'TEST', 'pcs')
    RETURNING id INTO v_item2_id;
    
    SELECT id INTO v_item1_id FROM stock_item WHERE ref = 'TEST-001';
    
    -- Déplacer la référence restante vers l'item 2
    SELECT id INTO v_ref_id 
    FROM stock_item_supplier 
    WHERE stock_item_id = v_item1_id 
    LIMIT 1;
    
    UPDATE stock_item_supplier 
    SET stock_item_id = v_item2_id 
    WHERE id = v_ref_id;
    
    -- Vérifier les comptes
    SELECT supplier_refs_count INTO v_count1 FROM stock_item WHERE id = v_item1_id;
    SELECT supplier_refs_count INTO v_count2 FROM stock_item WHERE id = v_item2_id;
    
    IF v_count1 = 0 AND v_count2 = 1 THEN
        RAISE NOTICE '✓ TEST 5 PASSÉ : Item1=0, Item2=1 après UPDATE';
    ELSE
        RAISE EXCEPTION '✗ TEST 5 ÉCHOUÉ : Item1=%, Item2=% au lieu de 0,1', v_count1, v_count2;
    END IF;
END $$;

-- ============================================================================
-- TEST 6 : Vérification cohérence globale
-- ============================================================================
DO $$
DECLARE
    v_mismatch_count INTEGER;
BEGIN
    RAISE NOTICE '=== TEST 6 : Cohérence globale ===';
    
    -- Comparer les comptes stockés avec les comptes réels
    SELECT COUNT(*) INTO v_mismatch_count
    FROM (
        SELECT 
            si.id,
            si.ref,
            si.supplier_refs_count as stored_count,
            COUNT(sis.id) as actual_count
        FROM stock_item si
        LEFT JOIN stock_item_supplier sis ON sis.stock_item_id = si.id
        WHERE si.ref LIKE 'TEST-%'
        GROUP BY si.id, si.ref, si.supplier_refs_count
        HAVING si.supplier_refs_count != COUNT(sis.id)
    ) AS mismatches;
    
    IF v_mismatch_count = 0 THEN
        RAISE NOTICE '✓ TEST 6 PASSÉ : Tous les comptes sont cohérents';
    ELSE
        RAISE EXCEPTION '✗ TEST 6 ÉCHOUÉ : % articles avec comptes incorrects', v_mismatch_count;
    END IF;
END $$;

-- ============================================================================
-- Résumé des tests
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '════════════════════════════════════════════';
    RAISE NOTICE '✓ TOUS LES TESTS RÉUSSIS !';
    RAISE NOTICE '════════════════════════════════════════════';
    RAISE NOTICE 'Le trigger supplier_refs_count fonctionne correctement.';
    RAISE NOTICE '';
END $$;

ROLLBACK;
-- Si vous voulez garder les données de test, remplacez ROLLBACK par COMMIT
