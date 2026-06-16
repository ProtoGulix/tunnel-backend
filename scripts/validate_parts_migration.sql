-- =============================================================================
-- Script de validation post-migration : nouveau système de pièces (parts)
-- À exécuter AVANT la suppression des anciennes tables.
-- Chaque requête DOIT retourner 0 ligne pour valider la migration.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Toutes les pièces de stock_item ont un enregistrement dans part
-- ---------------------------------------------------------------------------
SELECT 'ECHEC: stock_item sans part' AS check_name, si.id, si.ref
FROM stock_item si
WHERE NOT EXISTS (SELECT 1 FROM part p WHERE p.id = si.id);

-- ---------------------------------------------------------------------------
-- 2. Toutes les part ont une internal_ref non nulle et unique
-- ---------------------------------------------------------------------------
SELECT 'ECHEC: part sans internal_ref' AS check_name, id
FROM part
WHERE internal_ref IS NULL OR internal_ref = '';

SELECT 'ECHEC: internal_ref dupliquée' AS check_name, internal_ref, COUNT(*) AS cnt
FROM part
GROUP BY internal_ref
HAVING COUNT(*) > 1;

-- ---------------------------------------------------------------------------
-- 3. Toutes les part ont au moins une part_manufacturer_ref
-- ---------------------------------------------------------------------------
SELECT 'ECHEC: part sans ref fabricant' AS check_name, p.id, p.internal_ref
FROM part p
WHERE NOT EXISTS (
    SELECT 1 FROM part_manufacturer_ref pmr WHERE pmr.part_id = p.id
);

-- ---------------------------------------------------------------------------
-- 4. Chaque part a exactement une part_manufacturer_ref is_preferred = true
-- ---------------------------------------------------------------------------
SELECT 'ECHEC: part sans ref fabricant préférée' AS check_name, p.id, p.internal_ref
FROM part p
WHERE NOT EXISTS (
    SELECT 1 FROM part_manufacturer_ref pmr
    WHERE pmr.part_id = p.id AND pmr.is_preferred = true
);

SELECT 'ECHEC: part avec plusieurs refs fabricant préférées' AS check_name,
       part_id, COUNT(*) AS cnt
FROM part_manufacturer_ref
WHERE is_preferred = true
GROUP BY part_id
HAVING COUNT(*) > 1;

-- ---------------------------------------------------------------------------
-- 5. Les stock_item_supplier ont été migrés vers part_supplier_ref
--    (tous les sis liés à des stock_items existants en part)
-- ---------------------------------------------------------------------------
SELECT 'ECHEC: stock_item_supplier non migré en part_supplier_ref' AS check_name,
       sis.id, sis.stock_item_id, sis.supplier_ref
FROM stock_item_supplier sis
WHERE EXISTS (SELECT 1 FROM part p WHERE p.id = sis.stock_item_id)
  AND NOT EXISTS (
      SELECT 1 FROM part_supplier_ref psr
      JOIN part_manufacturer_ref pmr ON pmr.id = psr.part_manufacturer_ref_id
      WHERE pmr.part_id = sis.stock_item_id
        AND psr.supplier_id = sis.supplier_id
        AND psr.supplier_ref = sis.supplier_ref
  );

-- ---------------------------------------------------------------------------
-- 6. Les supplier_order_line avec stock_item_id ont leur part_id rempli
-- ---------------------------------------------------------------------------
SELECT 'ECHEC: supplier_order_line avec stock_item_id mais sans part_id' AS check_name,
       sol.id, sol.stock_item_id
FROM supplier_order_line sol
WHERE sol.stock_item_id IS NOT NULL
  AND sol.part_id IS NULL
  AND EXISTS (SELECT 1 FROM part p WHERE p.id = sol.stock_item_id);

-- ---------------------------------------------------------------------------
-- 7. Les purchase_request avec stock_item_id ont leur part_id rempli
-- ---------------------------------------------------------------------------
SELECT 'ECHEC: purchase_request avec stock_item_id mais sans part_id' AS check_name,
       pr.id, pr.stock_item_id
FROM purchase_request pr
WHERE pr.stock_item_id IS NOT NULL
  AND pr.part_id IS NULL
  AND EXISTS (SELECT 1 FROM part p WHERE p.id = pr.stock_item_id);

-- ---------------------------------------------------------------------------
-- 8. Pas de part_manufacturer_ref orpheline (sans part parente)
-- ---------------------------------------------------------------------------
SELECT 'ECHEC: part_manufacturer_ref orpheline' AS check_name, pmr.id
FROM part_manufacturer_ref pmr
WHERE NOT EXISTS (SELECT 1 FROM part p WHERE p.id = pmr.part_id);

-- ---------------------------------------------------------------------------
-- 9. Pas de part_supplier_ref orpheline (sans part_manufacturer_ref parente)
-- ---------------------------------------------------------------------------
SELECT 'ECHEC: part_supplier_ref orpheline' AS check_name, psr.id
FROM part_supplier_ref psr
WHERE NOT EXISTS (
    SELECT 1 FROM part_manufacturer_ref pmr WHERE pmr.id = psr.part_manufacturer_ref_id
);

-- ---------------------------------------------------------------------------
-- 10. Les FK fournisseur dans part_supplier_ref pointent vers des suppliers valides
-- ---------------------------------------------------------------------------
SELECT 'ECHEC: part_supplier_ref avec supplier_id invalide' AS check_name, psr.id, psr.supplier_id
FROM part_supplier_ref psr
WHERE NOT EXISTS (SELECT 1 FROM supplier s WHERE s.id = psr.supplier_id);

-- ---------------------------------------------------------------------------
-- 11. Cohérence des compteurs (volumes)
-- ---------------------------------------------------------------------------
SELECT 'INFO: volumes de migration' AS check_name,
    (SELECT COUNT(*) FROM stock_item) AS stock_item_count,
    (SELECT COUNT(*) FROM part) AS part_count,
    (SELECT COUNT(*) FROM manufacturer_item) AS manufacturer_item_count,
    (SELECT COUNT(*) FROM part_manufacturer_ref) AS part_mfr_ref_count,
    (SELECT COUNT(*) FROM stock_item_supplier) AS stock_item_supplier_count,
    (SELECT COUNT(*) FROM part_supplier_ref) AS part_supplier_ref_count;

-- =============================================================================
-- Si toutes les requêtes ci-dessus retournent 0 ligne (hors requête INFO),
-- la migration est validée. Vous pouvez alors supprimer les anciennes tables
-- en exécutant la migration alembic 010_drop_legacy_stock_tables.
-- =============================================================================
