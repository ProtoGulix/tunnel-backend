# Migration v1.4.0 -> v1.4.1

**Date** : 18 février 2026  
**Auteur** : Quentin  
**Type** : Patch

## Description

Correctif du trigger `generate_stock_item_ref()` qui ne générait pas de référence lorsque les champs `spec` ou `dimension` contenaient des valeurs NULL.

## Problème

En PostgreSQL, l'opérateur de concaténation `||` retourne NULL si n'importe quelle valeur de la chaîne est NULL. Cela empêchait la génération de la référence article lorsque `spec` ou `dimension` était NULL.

De plus, utiliser `COALESCE()` avec des chaînes vides créait des tirets consécutifs indésirables (ex: `TEST-TEST--M30`).

**Avant :**

```sql
NEW.ref := NEW.family_code || '-' || NEW.sub_family_code || '-' || NEW.spec || '-' || NEW.dimension;
```

Si `spec` ou `dimension` est NULL, alors `NEW.ref` devient NULL.

## Solution

Construction conditionnelle de la référence : le séparateur `-` n'est ajouté que si la valeur suivante existe et n'est pas vide.

**Après :**

```sql
NEW.ref := NEW.family_code;

IF NEW.sub_family_code IS NOT NULL AND NEW.sub_family_code != '' THEN
  NEW.ref := NEW.ref || '-' || NEW.sub_family_code;
END IF;

IF NEW.spec IS NOT NULL AND NEW.spec != '' THEN
  NEW.ref := NEW.ref || '-' || NEW.spec;
END IF;

IF NEW.dimension IS NOT NULL AND NEW.dimension != '' THEN
  NEW.ref := NEW.ref || '-' || NEW.dimension;
END IF;
```

## Changements

### Fichiers modifiés

- `public.generate_stock_item_ref()` - Construction conditionnelle pour éviter les tirets inutiles

### Exemples de résultats

- `spec = NULL` → `VIS-CHC-20` (au lieu de NULL ou `VIS-CHC--20`)
- `dimension = NULL` → `VIS-CHC-M8` (au lieu de NULL ou `VIS-CHC-M8-`)
- `spec = NULL, dimension = NULL` → `VIS-CHC` (au lieu de NULL ou `VIS-CHC--`)

## Impact

- **Breaking changes** : Non
- **Data migration** : Non (le trigger s'applique uniquement aux nouvelles insertions/updates)
- **Compatibilité** : Rétrocompatible, améliore le comportement existant

## Tests suggérés

```sql
-- Test 1 : Valeurs complètes
INSERT INTO stock_item (family_code, sub_family_code, spec, dimension)
VALUES ('VIS', 'CHC', 'M8', '20');
-- Résultat attendu : ref = 'VIS-CHC-M8-20'

-- Test 2 : spec NULL
INSERT INTO stock_item (family_code, sub_family_code, spec, dimension)
VALUES ('VIS', 'CHC', NULL, '20');
-- Résultat attendu : ref = 'VIS-CHC-20'

-- Test 3 : dimension NULL
INSERT INTO stock_item (family_code, sub_family_code, spec, dimension)
VALUES ('VIS', 'CHC', 'M8', NULL);
-- Résultat attendu : ref = 'VIS-CHC-M8'

-- Test 4 : spec et dimension NULL
INSERT INTO stock_item (family_code, sub_family_code, spec, dimension)
VALUES ('VIS', 'CHC', NULL, NULL);
-- Résultat attendu : ref = 'VIS-CHC'

-- Test 5 : Seul family_code (cas extrême)
INSERT INTO stock_item (family_code, sub_family_code, spec, dimension)
VALUES ('VIS', NULL, NULL, NULL);
-- Résultat attendu : ref = 'VIS'
```

## Rollback

En cas de problème, exécuter `down.sql` pour revenir à la version 1.4.0.

**Note** : Le rollback restaure le comportement original (concaténation sans COALESCE), ce qui signifie que le bug réapparaîtra.
