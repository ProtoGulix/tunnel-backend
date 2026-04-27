# Système de Caractérisation des Pièces

Système robuste et scalable pour la gestion des caractéristiques des pièces via des templates versionnés avec champs structurés.

## 📋 Ordre d'exécution

Les fichiers doivent être exécutés dans cet ordre pour respecter les dépendances :

### 📁 Référentiels (02_ref/)

1. **[part_template.sql](part_template.sql)** - Table des templates versionnés
2. **[part_template_field.sql](part_template_field.sql)** - Table des champs de template
3. **[part_template_field_enum.sql](part_template_field_enum.sql)** - Table des valeurs enum
4. **[stock_sub_family_template.sql](stock_sub_family_template.sql)** - Ajout du lien template dans stock_sub_family

### 📁 Core transactionnel (01_core/)

5. **[../01_core/stock_item_template.sql](../01_core/stock_item_template.sql)** - Ajout du versionnement template dans stock_item
6. **[../01_core/stock_item_characteristic.sql](../01_core/stock_item_characteristic.sql)** - Table des valeurs de caractéristiques

## 🏗️ Architecture

```
part_template (template versionné)
    ↓
part_template_field (champs du template)
    ↓
part_template_field_enum (valeurs enum)

stock_sub_family → part_template (template par défaut)
stock_item → part_template (template + version utilisée)
stock_item_characteristic → stock_item + part_template_field (valeurs)
```

## 🔑 Caractéristiques

- ✅ Templates versionnés (code + version)
- ✅ Trois types de champs : `number`, `text`, `enum`
- ✅ Contrôle strict des valeurs (enum contrôlées)
- ✅ Une seule valeur par caractéristique (CHECK constraint)
- ✅ Index sur toutes les colonnes critiques
- ✅ ON DELETE cohérents (CASCADE/RESTRICT/SET NULL)
- ✅ Pas de JSON, pas de triggers, pas de fonctions

## 📝 Note importante

Les colonnes ajoutées à `stock_item` sont nullable pour permettre l'exécution sur une table existante.

Après migration des données, les rendre NOT NULL :

```sql
ALTER TABLE stock_item ALTER COLUMN template_id SET NOT NULL;
ALTER TABLE stock_item ALTER COLUMN template_version SET NOT NULL;
```
