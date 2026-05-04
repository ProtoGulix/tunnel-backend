# Migration v1.4.1 -> v1.5.0

**Date** : 6 mars 2026  
**Auteur** : Quentin  
**Type** : Mineure

## Description

Renforcement du modèle de données fabricants : ajout d'une contrainte d'intégrité sur le nom fabricant et liaison formelle entre les références fournisseurs et les références fabricants.

## Changements

### 1. `manufacturer_item.manufacturer_name` → NOT NULL

Une référence fabricant sans nom de fabricant n'a aucune valeur métier. La colonne passe à `NOT NULL`.

**Avant :**

```sql
manufacturer_name TEXT
```

**Après :**

```sql
manufacturer_name TEXT NOT NULL
```

> Les lignes existantes avec `manufacturer_name IS NULL` sont mises à jour avec la valeur `'Inconnu'` avant l'ajout de la contrainte.

### 2. FK : `stock_item_supplier.manufacturer_item_id → manufacturer_item(id)`

La colonne `manufacturer_item_id` existait dans `stock_item_supplier` sans contrainte référentielle. La FK est maintenant déclarée avec `ON DELETE SET NULL` : si une référence fabricant est supprimée, les lignes fournisseurs restent intactes.

**Relation finale :**

```
stock_item ──< stock_item_supplier >── supplier
                      │
                      └──> manufacturer_item  (référence catalogue fabricant)
```

## Fichiers SQL modifiés (baseline)

- `01_core/manufacturer_item.sql` — `manufacturer_name NOT NULL`
- `05_triggers/99_foreign_keys.sql` — ajout de `stock_item_supplier_manufacturer_item_id_fkey`

## Impact

- **Breaking changes** : Non (la valeur `'Inconnu'` est assignée aux NULLs existants)
- **Data migration** : UPDATE automatique dans `up.sql` avant l'ALTER
- **Compatibilité** : Le rollback (`down.sql`) supprime la FK et retire le NOT NULL sans perte de données

## Tests suggérés

```sql
-- Vérifie qu'aucun NULL ne reste sur manufacturer_name
SELECT COUNT(*) FROM manufacturer_item WHERE manufacturer_name IS NULL;
-- Attendu : 0

-- Vérifie que la FK est active
SELECT conname FROM pg_constraint
WHERE conname = 'stock_item_supplier_manufacturer_item_id_fkey';
-- Attendu : 1 ligne

-- Test ON DELETE SET NULL
-- Insérer un manufacturer_item, le lier à un stock_item_supplier, puis supprimer le manufacturer_item
-- manufacturer_item_id doit être NULL dans stock_item_supplier après suppression
```
