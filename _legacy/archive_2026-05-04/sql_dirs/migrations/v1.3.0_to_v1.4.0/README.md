# Migration v1.3.0 → v1.4.0

## Objectif

Implémenter un système robuste, scalable et versionné de caractérisation des pièces basé sur des templates avec champs structurés, enum contrôlées et intégrité référentielle forte.

## Contexte

Dans les systèmes GMAO modernes, les pièces de stock nécessitent souvent des caractéristiques techniques précises (dimensions, matériaux, propriétés électriques, etc.). Cette migration introduit une infrastructure flexible permettant de :

- Définir des **templates versionnés** de caractéristiques
- Structurer les **champs par type** (number, text, enum)
- Contrôler les **valeurs autorisées** pour les énumérations
- Lier les templates aux **sous-familles** et **pièces**
- Stocker les **valeurs concrètes** avec intégrité forte

## Architecture

```
📁 02_ref/ (Référentiels)
├── part_template              → Templates versionnés
├── part_template_field        → Champs des templates (number/text/enum)
├── part_template_field_enum   → Valeurs autorisées pour champs enum
└── stock_sub_family           → +template_id (template par défaut)

📁 01_core/ (Transactionnel)
├── stock_item                 → +template_id, +template_version
└── stock_item_characteristic  → Valeurs des caractéristiques par pièce
```

## Changements détaillés

### Nouvelles tables

#### 1. `part_template` (02_ref)

Template versionné définissant la structure des caractéristiques.

**Colonnes clés :**

- `code` + `version` : UNIQUE ensemble (permet plusieurs versions)
- `is_active` : Indicateur d'activation
- `pattern` : Règles ou description du template

**Contraintes :**

- UNIQUE(code, version)
- CHECK(version > 0)

#### 2. `part_template_field` (02_ref)

Champs structurés de chaque template.

**Colonnes clés :**

- `template_id` : FK → part_template
- `field_key` : Identifiant unique du champ dans le template
- `field_type` : 'number', 'text' ou 'enum'
- `unit` : Unité de mesure (optionnel)
- `sort_order` : Ordre d'affichage

**Contraintes :**

- UNIQUE(template_id, field_key)
- CHECK(field_type IN ('number', 'text', 'enum'))
- CHECK(sort_order > 0)

#### 3. `part_template_field_enum` (02_ref)

Valeurs autorisées pour les champs de type 'enum'.

**Colonnes clés :**

- `field_id` : FK → part_template_field
- `value` : Valeur technique
- `label` : Libellé affiché

**Contraintes :**

- UNIQUE(field_id, value)

#### 4. `stock_item_characteristic` (01_core)

Valeurs des caractéristiques pour chaque pièce.

**Colonnes clés :**

- `stock_item_id` : FK → stock_item (CASCADE)
- `field_id` : FK → part_template_field (RESTRICT)
- `value_text`, `value_number`, `value_enum` : Stockage typé

**Contraintes :**

- UNIQUE(stock_item_id, field_id)
- CHECK : Exactement une valeur non NULL parmi text/number/enum

### Modifications de tables existantes

#### `stock_sub_family` (02_ref)

- **Ajout :** `template_id` uuid (nullable)
- **FK :** → part_template(id) ON DELETE SET NULL
- **Usage :** Template par défaut suggéré pour les pièces de cette sous-famille

#### `stock_item` (01_core)

- **Ajout :** `template_id` uuid, `template_version` integer (nullable)
- **FK :** → part_template(id) ON DELETE RESTRICT
- **Usage :** Traçabilité de la version du template utilisée lors de la création

## Caractéristiques techniques

### Scalabilité

- Templates versionnés : permet l'évolution sans rupture
- Pas de schéma JSON : requêtabilité SQL native
- Index optimisés sur toutes les colonnes critiques

### Intégrité

- FK avec ON DELETE adaptés (CASCADE/RESTRICT/SET NULL)
- Contraintes CHECK strictes
- UNIQUE sur les clés métier

### Performance

- Index sur toutes les FK
- Index partiels (WHERE) pour filtres courants
- Index composites pour requêtes multi-critères

### Évolution future

- Colonnes nullable permettent migration progressive
- Versionnement permet ajout de nouveaux champs
- Structure extensible pour nouveaux types de champs

## Exécution

### Méthode 1 : Via migration_runner.py (recommandé)

```bash
cd scripts

# Migration UP
python migration_runner.py --version v1.3.0_to_v1.4.0 --direction up

# Rollback (si nécessaire)
python migration_runner.py --version v1.3.0_to_v1.4.0 --direction down
```

### Méthode 2 : Via psql

```bash
# Migration UP
psql -U username -d database_name -f migrations/v1.3.0_to_v1.4.0/up.sql

# Rollback
psql -U username -d database_name -f migrations/v1.3.0_to_v1.4.0/down.sql
```

## Validation post-migration

```sql
-- Vérifier la création des tables
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name LIKE 'part_%' OR table_name = 'stock_item_characteristic';

-- Vérifier les colonnes ajoutées
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name IN ('stock_item', 'stock_sub_family')
  AND column_name LIKE 'template%';

-- Vérifier les contraintes FK
SELECT conname, contype, confdeltype
FROM pg_constraint
WHERE conrelid::regclass::text IN (
    'stock_item', 'stock_sub_family', 'stock_item_characteristic',
    'part_template_field', 'part_template_field_enum'
);
```

## Exemple d'utilisation

### 1. Créer un template "Roulement"

```sql
-- Template
INSERT INTO part_template (code, version, label, pattern)
VALUES ('ROULEMENT', 1, 'Roulement à billes', 'Caractéristiques techniques des roulements');

-- Champs
INSERT INTO part_template_field (template_id, field_key, label, field_type, unit, required, sort_order)
SELECT
    id,
    'diametre_int',
    'Diamètre intérieur',
    'number',
    'mm',
    true,
    1
FROM part_template WHERE code = 'ROULEMENT' AND version = 1;

INSERT INTO part_template_field (template_id, field_key, label, field_type, required, sort_order)
SELECT
    id,
    'type',
    'Type de roulement',
    'enum',
    true,
    2
FROM part_template WHERE code = 'ROULEMENT' AND version = 1;

-- Valeurs enum pour le type
INSERT INTO part_template_field_enum (field_id, value, label)
SELECT
    ptf.id,
    v.val,
    v.lbl
FROM part_template_field ptf
CROSS JOIN (VALUES
    ('BILLES', 'Roulement à billes'),
    ('ROULEAUX', 'Roulement à rouleaux'),
    ('AIGUILLES', 'Roulement à aiguilles')
) AS v(val, lbl)
WHERE ptf.field_key = 'type';
```

### 2. Associer le template à une sous-famille

```sql
UPDATE stock_sub_family
SET template_id = (
    SELECT id FROM part_template
    WHERE code = 'ROULEMENT' AND version = 1
)
WHERE code = 'RLT';
```

### 3. Créer une pièce avec caractéristiques

```sql
-- Créer la pièce
INSERT INTO stock_item (template_id, template_version, ...)
SELECT
    id,
    1,
    ...
FROM part_template
WHERE code = 'ROULEMENT' AND version = 1;

-- Ajouter les caractéristiques
INSERT INTO stock_item_characteristic (stock_item_id, field_id, value_number)
SELECT
    si.id,
    ptf.id,
    25.5  -- diamètre intérieur
FROM stock_item si
JOIN part_template_field ptf ON ptf.template_id = si.template_id
WHERE si.id = '...' AND ptf.field_key = 'diametre_int';

INSERT INTO stock_item_characteristic (stock_item_id, field_id, value_enum)
SELECT
    si.id,
    ptf.id,
    'BILLES'  -- type de roulement
FROM stock_item si
JOIN part_template_field ptf ON ptf.template_id = si.template_id
WHERE si.id = '...' AND ptf.field_key = 'type';
```

## Rollback

Le rollback supprime :

- ✅ Toutes les nouvelles tables
- ✅ Toutes les colonnes ajoutées
- ✅ Toutes les contraintes et index associés

⚠️ **Attention :** Les données créées dans ces tables seront **définitivement perdues**. Effectuez une sauvegarde avant rollback.

## Notes importantes

### Colonnes nullable sur stock_item

Les colonnes `template_id` et `template_version` sont nullable pour permettre la migration sur une base existante.

**Après migration des pièces existantes**, vous pouvez les rendre NOT NULL :

```sql
-- Après avoir attribué un template à toutes les pièces
ALTER TABLE stock_item ALTER COLUMN template_id SET NOT NULL;
ALTER TABLE stock_item ALTER COLUMN template_version SET NOT NULL;
```

### Pas de trigger, pas de JSON

- ✅ Conformité stricte avec les contraintes du projet
- ✅ Pas d'automatisme complexe
- ✅ Requêtabilité SQL native
- ✅ Performance optimale

## Documentation associée

- [README_PART_TEMPLATE.md](README_PART_TEMPLATE.md) - Documentation complète du système de templates (référentiels)
- [README_PART_CHARACTERISTIC.md](README_PART_CHARACTERISTIC.md) - Documentation des caractéristiques transactionnelles
