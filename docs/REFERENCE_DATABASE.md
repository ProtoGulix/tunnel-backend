# Référence base de données — Tunnel GMAO

> **Version** : v1.4.1 (schéma courant au 3 mars 2026)  
> **Base** : PostgreSQL — schéma `public`  
> **Usage** : Document de référence métier et technique destiné à l'intégration ERP.  
> Toutes les informations sont issues directement du DDL et des triggers en production.

---

## Table des matières

1. [Architecture générale](#1-architecture-générale)
2. [Module Équipements](#2-module-équipements)
3. [Module Interventions](#3-module-interventions)
4. [Module Stock](#4-module-stock)
5. [Module Approvisionnement](#5-module-approvisionnement)
6. [Module Maintenance préventive](#6-module-maintenance-préventive)
7. [Mécanique des triggers](#7-mécanique-des-triggers)
8. [Règles métier transversales](#8-règles-métier-transversales)
9. [Conventions d'identification](#9-conventions-didentification)

---

## 1. Architecture générale

La base est organisée en couches d'exécution chargées dans l'ordre suivant :

| Dossier | Rôle |
|---|---|
| `00_extensions.sql` | Extensions PostgreSQL (uuid-ossp, etc.) |
| `01_core/` | Tables transactionnelles — données vivantes |
| `02_ref/` | Tables référentielles — valeurs stables, paramétrables |
| `03_meta/` | Configuration méta, sondes de classification |
| `04_preventive/` | Moteur de maintenance préventive (règles + suggestions) |
| `05_triggers/` | Fonctions et triggers — toute l'automatisation |

**Principe** : les tables `01_core` portent la réalité opérationnelle, les tables `02_ref` portent les valeurs contrôlées qui leur donnent du sens. Aucune logique métier n'est embarquée dans les tables : tout passe par les triggers de `05_triggers`.

---

## 2. Module Équipements

### 2.1 Vue d'ensemble

Ce module est le point de départ de toute activité de maintenance. Chaque intervention est rattachée à une machine. Une machine appartient à une classe d'équipement et peut être localisée physiquement.

### 2.2 Tables

#### `machine` — Inventaire des équipements

Table centrale du patrimoine équipement. Chaque ligne représente un équipement physique soumis à maintenance.

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID PK | Identifiant unique |
| `code` | VARCHAR(50) UNIQUE NOT NULL | Code court lisible (ex: `CONV-01`, `POMP-02`) — utilisé dans la génération du code d'intervention |
| `name` | VARCHAR(200) NOT NULL | Désignation de l'équipement |
| `no_machine` | INTEGER | Numéro machine hérité (compatibilité codes interventions anciens) |
| `affectation` | VARCHAR | Lieu ou département d'affectation |
| `equipement_mere` | UUID FK → machine | Auto-référence : équipement parent (hiérarchie) |
| `is_mere` | BOOLEAN DEFAULT FALSE | Indique si l'équipement est un équipement mère (contient des sous-équipements) |
| `fabricant` | VARCHAR | Nom du fabricant |
| `numero_serie` | VARCHAR | Numéro de série |
| `date_mise_service` | DATE | Date de mise en service |
| `notes` | TEXT | Notes libres |
| `equipment_class_id` | UUID FK → equipment_class | Classe d'équipement (SET NULL si suppression de classe) |

**Règles métier** :
- Le `code` est unique et immuable dans l'usage courant — il est intégré dans le code de chaque intervention rattachée.
- La hiérarchie est auto-référentielle : un équipement peut avoir un `equipement_mere`. La suppression du parent est bloquée (`ON DELETE NO ACTION`).
- Un équipement sans `equipment_class_id` est valide (FK nullable).

#### `equipment_class` — Classes d'équipement (référentiel)

Classifie les machines par nature technologique. Données stables, maintenues par les administrateurs.

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID PK | Identifiant |
| `code` | VARCHAR(255) UNIQUE NOT NULL | Code court (ex: `SCIE`, `EXT`, `LIG`, `POMP`) |
| `label` | TEXT NOT NULL | Libellé lisible |
| `description` | TEXT | Description optionnelle |

**Exemples de codes** : `EXT` (Extrudeuse), `LIG` (Ligne), `TPE` (Transpalette électrique), `TRY` (Trémie). La table contient 66 classes à la mise en production initiale.

#### `location` — Localisations physiques

Emplacements physiques. Table simple, utilisée optionnellement pour situer les équipements.

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID PK | Identifiant |
| `name` | TEXT NOT NULL | Nom du lieu (ex: Atelier A, Zone Production) |
| `description` | TEXT | Description optionnelle |

---

## 3. Module Interventions

### 3.1 Vue d'ensemble

Le module intervention est le cœur opérationnel du GMAO. Une intervention représente un acte de maintenance sur une machine. Elle possède un cycle de vie contrôlé, un historique complet des changements de statut, peut être décomposée en sous-tâches et en actions, et consomme des pièces du stock.

### 3.2 Cycle de vie d'une intervention

```
[Création] → ouvert → en_cours → fermé
                              ↘ annulé
```

- À la création (`INSERT`) : le statut est automatiquement positionné à `ouvert` par trigger, et un enregistrement initial est créé dans `intervention_status_log`.
- Chaque changement de `status_actual` est enregistré dans `intervention_status_log` par trigger.
- Le champ `status_actual` de `intervention` est toujours synchronisé avec la dernière entrée du log.

### 3.3 Tables

#### `intervention` — Table principale

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID PK | Identifiant |
| `code` | VARCHAR(255) UNIQUE | Code auto-généré par trigger (voir §7.1) |
| `machine_id` | UUID FK → machine | Équipement concerné |
| `updated_by` | UUID | Référence utilisateur externe (non géré en DB) |
| `type_inter` | VARCHAR | Type : `PREV`, `COR`, `INST`, etc. |
| `tech_initials` | VARCHAR | Initiales du technicien (intégrées dans le code) |
| `description` | TEXT | Description de l'intervention |
| `date_debut` | TIMESTAMPTZ | Date/heure de début |
| `date_fin` | TIMESTAMPTZ | Date/heure de fin |
| `status_actual` | VARCHAR | Statut courant (synchronisé avec le log) |
| `created_at` | TIMESTAMPTZ | Date de création |
| `updated_at` | TIMESTAMPTZ | Date de dernière modification |

**Règles métier** :
- `machine_id` doit pointer une machine existante. Le trigger de génération de code l'exige et lève une exception si la machine est inconnue.
- `type_inter` et `tech_initials` sont nécessaires à la génération du code. Sans eux, l'insertion échoue.
- `status_actual` ne doit jamais être modifié directement sans passer par le mécanisme de log (cohérence garantie par trigger).

#### `intervention_status_ref` — Référentiel des statuts

| Colonne | Type | Description |
|---|---|---|
| `code` | VARCHAR(255) PK | Code du statut (ex: `ouvert`, `en_cours`, `ferme`, `annule`) |
| `label` | TEXT | Libellé affiché |
| `color` | VARCHAR(255) | Couleur hexadécimale pour l'UI (ex: `#3b82f6`) |

#### `intervention_status_log` — Historique des statuts

Trace immuable de toutes les transitions de statut. Alimenté exclusivement par triggers.

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID PK | Identifiant |
| `intervention_id` | UUID FK → intervention | Intervention concernée |
| `technician_id` | UUID | Utilisateur ayant effectué le changement |
| `status_from` | VARCHAR | Statut précédent (`NULL` à la création initiale) |
| `status_to` | VARCHAR | Nouveau statut |
| `date` | TIMESTAMPTZ | Horodatage de la transition |
| `notes` | TEXT | Notes (ex: "Création intervention", "Changement statut automatique") |

**Règle** : `status_from IS NULL` uniquement pour la première entrée (création). Toute transition ultérieure a un `status_from` renseigné.

#### `intervention_action` — Actions réalisées

Détail des actions effectuées dans le cadre d'une intervention. C'est sur ces objets que fonctionne le moteur de détection préventive.

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID PK | Identifiant |
| `intervention_id` | UUID FK → intervention | Intervention parente |
| `action_subcategory` | INTEGER FK → action_subcategory | Classification de l'action |
| `tech` | UUID | Technicien ayant réalisé l'action |
| `description` | TEXT | Description textuelle de l'action (analysée par le moteur préventif) |
| `time_spent` | NUMERIC(6,2) DEFAULT 0 | Temps passé en heures décimales (ex: `1.5` = 1h30) |
| `complexity_score` | INTEGER | Score de complexité global calculé |
| `complexity_anotation` | JSON | Détail JSON des facteurs de complexité contributifs (champ historique, coexiste avec FK `complexity_factor`) |
| `created_at` | TIMESTAMPTZ | Date de création |
| `updated_at` | TIMESTAMPTZ | Date de modification |

**Note** : La colonne `complexity_anotation` (JSON) est un champ héritage de la v1.2. En v1.3, la FK `complexity_factor` a été ajoutée dans `intervention_action` pour remplacer la clé JSON par une valeur normalisée. Les deux colonnes coexistent pendant la période de transition.

#### `action_category` — Catégories d'actions (référentiel)

Niveau haut de classification des actions.

| Colonne | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Identifiant séquentiel |
| `code` | VARCHAR(255) UNIQUE | Code court (ex: `DEP`, `FAB`, `PREV`, `SUP`, `BAT`) |
| `name` | TEXT NOT NULL | Libellé |
| `color` | VARCHAR(255) | Couleur badge UI |

**Codes en production** :
| Code | Libellé |
|---|---|
| `DEP` | Dépannage |
| `FAB` | Fabrication |
| `PREV` | Préventif |
| `SUP` | Support / Administratif |
| `BAT` | Bâtiment / Nettoyage |

#### `action_subcategory` — Sous-catégories d'actions (référentiel)

Granularité fine de classification. La convention de nommage est `CATÉGORIE_DÉTAIL`.

| Colonne | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Identifiant séquentiel |
| `category_id` | INTEGER FK → action_category | Catégorie parente |
| `code` | VARCHAR(255) UNIQUE | Code (ex: `DEP_ELEC`, `DEP_MECA`, `PREV_GRAIS`) |
| `name` | TEXT NOT NULL | Libellé |

**Règle critique** : Le moteur préventif filtre les actions sur les sous-catégories dont le code commence par `DEP_`. Une action de sous-catégorie `PREV_*` ou `FAB_*` ne déclenche aucune suggestion préventive.

#### `complexity_factor` — Facteurs de complexité (référentiel)

Valeurs de complexité qualitative des actions.

| Colonne | Type | Description |
|---|---|---|
| `code` | VARCHAR(255) PK | Code facteur (ex: `simple`, `moyen`, `eleve`, `critique`) |
| `label` | TEXT | Libellé |
| `category` | VARCHAR | Dimension (ex: `technique`, `organisationnel`) |

#### `subtask` — Sous-tâches

Décomposition d'une intervention en tâches assignables individuellement.

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID PK | Identifiant |
| `intervention_id` | UUID FK → intervention | Intervention parente |
| `assigned_to` | UUID | Technicien assigné (référence utilisateur externe) |
| `description` | TEXT | Contenu de la sous-tâche |
| `status` | VARCHAR | État : `todo`, `in_progress`, `done`, `blocked` |

#### `intervention_part` — Pièces consommées

Lien entre interventions et articles de stock consommés.

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID PK | Identifiant |
| `intervention_id` | UUID FK → intervention | Intervention |
| `stock_item_id` | UUID FK → stock_item | Article consommé |
| `quantity` | INTEGER | Quantité consommée |
| `notes` | TEXT | Notes libres |

**Règle** : La décrémentation réelle du stock n'est pas opérée automatiquement par trigger à ce stade du schéma. C'est la couche applicative (backend) qui porte cette responsabilité.

---

## 4. Module Stock

### 4.1 Vue d'ensemble

Le stock est organisé en une hiérarchie à deux niveaux : Famille → Sous-famille → Article. Chaque article possède une référence auto-générée, peut être rattaché à un ou plusieurs fournisseurs, et peut être caractérisé par un template de champs structurés.

### 4.2 Hiérarchie de classification

```
stock_family (ex: VIS)
  └── stock_sub_family (ex: VIS-CHC)
        └── stock_item (ex: VIS-CHC-M8-20)
```

### 4.3 Tables

#### `stock_family` — Familles (référentiel)

| Colonne | Type | Description |
|---|---|---|
| `code` | VARCHAR(255) PK | Code famille (ex: `VIS`, `ROUL`, `COURR`, `HUIL`, `ELEC`) |
| `name` | TEXT NOT NULL | Libellé |

#### `stock_sub_family` — Sous-familles (référentiel)

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID PK | Identifiant |
| `family_code` | VARCHAR FK → stock_family | Famille parente |
| `code` | VARCHAR(255) NOT NULL | Code sous-famille (ex: `CHC`, `TH`, `BIL`) |
| `name` | TEXT NOT NULL | Libellé |
| `template_id` | UUID FK → part_template (nullable) | Template de caractéristiques par défaut pour la sous-famille |

**Contrainte** : `(family_code, code)` est unique — le code de sous-famille est unique à l'intérieur d'une famille.

#### `stock_item` — Articles en stock

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID PK | Identifiant |
| `ref` | TEXT UNIQUE | Référence auto-générée : `FAM-SFAM-SPEC-DIM` (trigger) |
| `name` | TEXT NOT NULL | Désignation de l'article |
| `family_code` | VARCHAR(20) NOT NULL FK → stock_family | Famille |
| `sub_family_code` | VARCHAR(20) NOT NULL FK → stock_sub_family | Sous-famille |
| `spec` | VARCHAR(50) | Spécification technique (ex: `M8`, `Ø20mm`) — optionnel |
| `dimension` | TEXT NOT NULL | Dimension physique |
| `unit` | VARCHAR(50) | Unité (ex: `pièce`, `mètre`, `litre`, `kg`) |
| `quantity` | INTEGER DEFAULT 0 | Quantité en stock (≥ 0, contrainte CHECK) |
| `location` | TEXT | Localisation physique dans le stock |
| `manufacturer_item_id` | UUID FK → manufacturer_item | Référence fabricant |
| `standars_spec` | UUID FK → stock_item_standard_spec | Spécification normée (note : faute de frappe historique dans le nom de colonne) |
| `supplier_refs_count` | INTEGER | Nombre de références fournisseurs actives (maintenu par trigger) |
| `template_id` | UUID FK → part_template (nullable) | Template utilisé lors de la création |
| `template_version` | INTEGER (nullable) | Version du template au moment de la création |

**Règles métier** :
- La contrainte `CHECK (quantity >= 0)` interdit le stock négatif.
- La `ref` est générée automatiquement à l'insertion ou quand `family_code`, `sub_family_code`, `spec` ou `dimension` sont modifiés (BEFORE INSERT OR UPDATE trigger). Les valeurs NULL dans `spec` ou `dimension` sont gérées par `COALESCE` (résultat partiel possible, ex: `VIS-CHC--20`).
- Un article ne peut pas avoir deux lignes fournisseurs pour le même fournisseur.

#### `manufacturer_item` — Références fabricants

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID PK | Identifiant |
| `manufacturer_name` | TEXT | Nom du fabricant |
| `manufacturer_ref` | TEXT | Référence catalogue fabricant |
| `notes` | TEXT | Notes |

#### `stock_item_standard_spec` — Spécifications normées

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID PK | Identifiant |
| `stock_item_id` | UUID FK → stock_item | Article concerné |
| `standard_name` | VARCHAR | Nom de la norme (ex: `ISO 4762`, `DIN 912`) |
| `standard_value` | TEXT | Valeur nominale |
| `unit` | VARCHAR | Unité de mesure |
| `tolerance` | VARCHAR | Tolérance (ex: `±0.1mm`) |
| `notes` | TEXT | Notes |

#### `stock_item_supplier` — Catalogue fournisseurs par article

Table de relation N:N entre articles et fournisseurs, enrichie des conditions commerciales.

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID PK | Identifiant |
| `stock_item_id` | UUID FK → stock_item | Article |
| `supplier_id` | UUID FK → supplier | Fournisseur |
| `manufacturer_item_id` | UUID FK → manufacturer_item | Référence fabricant associée |
| `supplier_ref` | VARCHAR(255) | Référence catalogue fournisseur |
| `unit_price` | NUMERIC(10,2) | Prix unitaire |
| `min_order_quantity` | INTEGER | Quantité minimale de commande (MOQ) |
| `lead_time_days` | INTEGER | Délai de livraison en jours |
| `is_preferred` | BOOLEAN DEFAULT FALSE | Fournisseur préféré pour cet article |
| `notes` | TEXT | Notes |

**Contrainte** : `(stock_item_id, supplier_id)` est unique — un article ne peut avoir qu'une ligne par fournisseur.

**Règle métier** : Le flag `is_preferred` est utilisé par le moteur de dispatch des demandes d'achat (`dispatch_purchase_requests()`) pour router automatiquement les demandes vers le bon panier fournisseur.

**Index partiel** : Un index `WHERE is_preferred = TRUE` optimise les requêtes de dispatch.

### 4.4 Système de templates de caractéristiques (v1.4.0)

Ce système permet de définir des champs techniques structurés pour les articles, sans recours au JSON et sans perte de requêtabilité SQL.

#### `part_template` — Templates versionnés

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID PK | Identifiant |
| `code` | VARCHAR(50) NOT NULL | Code template (ex: `ROULEMENT`, `VIS_CHC`) |
| `version` | INTEGER NOT NULL DEFAULT 1 | Numéro de version (> 0) |
| `label` | VARCHAR(100) NOT NULL | Libellé descriptif |
| `pattern` | TEXT NOT NULL | Pattern ou règles associées au template |
| `is_active` | BOOLEAN DEFAULT TRUE | Actif ou archivé |

**Contrainte** : `(code, version)` est unique. Le versionnement permet d'évoluer la structure des champs sans rompre les articles déjà caractérisés.

#### `part_template_field` — Champs d'un template

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID PK | Identifiant |
| `template_id` | UUID FK → part_template (CASCADE) | Template parent |
| `field_key` | VARCHAR(50) NOT NULL | Clé unique du champ dans le template |
| `label` | VARCHAR(100) NOT NULL | Libellé affiché |
| `field_type` | VARCHAR(30) NOT NULL | Type : `number`, `text` ou `enum` |
| `unit` | VARCHAR(20) | Unité (pour les champs `number`) |
| `required` | BOOLEAN DEFAULT FALSE | Champ obligatoire |
| `sortable` | BOOLEAN DEFAULT TRUE | Champ triable |
| `sort_order` | INTEGER NOT NULL | Ordre d'affichage (> 0) |

**Contrainte** : `field_type` est contraint à `('number', 'text', 'enum')` par CHECK. `(template_id, field_key)` est unique.

#### `part_template_field_enum` — Valeurs autorisées (enum)

Valeurs admissibles pour les champs de type `enum`.  
_(Structure consultable dans `02_ref/part_template_field_enum.sql`)_

#### `stock_item_characteristic` — Valeurs de caractéristiques par article

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID PK | Identifiant |
| `stock_item_id` | UUID FK → stock_item (CASCADE) | Article |
| `field_id` | UUID FK → part_template_field (RESTRICT) | Champ du template |
| `value_text` | TEXT | Valeur texte (si `field_type = text`) |
| `value_number` | NUMERIC | Valeur numérique (si `field_type = number`) |
| `value_enum` | VARCHAR(50) | Valeur enum (si `field_type = enum`) |

**Contraintes critiques** :
- `(stock_item_id, field_id)` est unique : une seule valeur par champ et par article.
- CHECK d'exclusivité : exactement une des trois colonnes de valeur doit être non-NULL. Il est impossible de renseigner `value_text` et `value_number` simultanément sur la même ligne.

---

## 5. Module Approvisionnement

### 5.1 Vue d'ensemble

Le circuit d'approvisionnement part d'une demande d'achat (`purchase_request`) et aboutit à une commande fournisseur (`supplier_order`). Le dispatch automatique assure la création des paniers fournisseurs depuis les demandes ouvertes.

### 5.2 Cycle de vie d'une demande d'achat

```
en_attente → open → in_progress → reçu
                  ↘ refuse
```

_(Les codes de statuts sont gérés dans `purchase_status`)_

### 5.3 Circuit complet

```
purchase_request (demande)
    ↓ dispatch_purchase_requests() [fonction manuelle]
supplier_order_line (ligne panier fournisseur)
    → dans supplier_order (panier/commande)
    ↕
supplier_order_line_purchase_request (traçabilité du lien)
```

### 5.4 Tables

#### `supplier` — Annuaire fournisseurs

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID PK | Identifiant |
| `name` | TEXT NOT NULL | Raison sociale |
| `contact_name` | VARCHAR | Nom du contact |
| `email` | VARCHAR | Email |
| `phone` | VARCHAR | Téléphone |
| `address` | TEXT | Adresse |
| `is_active` | BOOLEAN DEFAULT TRUE | Actif (`FALSE` = archivé) |
| `notes` | TEXT | Notes |

#### `purchase_request` — Demandes d'achat

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID PK | Identifiant |
| `stock_item_id` | UUID FK → stock_item | Article demandé |
| `intervention_id` | UUID FK → intervention (nullable) | Intervention à l'origine de la demande |
| `quantity_requested` | INTEGER NOT NULL | Quantité demandée |
| `quantity_approved` | INTEGER | Quantité approuvée (peut différer) |
| `reason` | TEXT | Justification |
| `notes` | TEXT | Notes complémentaires |
| `urgent` | BOOLEAN DEFAULT FALSE | Demande urgente |
| `status` | VARCHAR DEFAULT `en_attente` | Statut courant |
| `requester_name` | VARCHAR | Nom du demandeur |
| `approver_name` | VARCHAR | Nom de l'approbateur |
| `created_at` | TIMESTAMPTZ | Date de création |
| `approved_at` | TIMESTAMPTZ | Date d'approbation |

#### `purchase_status` — Statuts demandes d'achat (référentiel)

| Colonne | Type | Description |
|---|---|---|
| `code` | VARCHAR(255) PK | Code (ex: `en_attente`, `approuve`, `commande`, `recu`, `refuse`) |
| `label` | TEXT | Libellé |
| `order_index` | INTEGER | Ordre d'affichage |

#### `supplier_order` — Commandes fournisseurs

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID PK | Identifiant |
| `order_number` | TEXT UNIQUE | Numéro auto-généré par trigger : `CMD-YYYYMMDD-NNNN` |
| `supplier_id` | UUID FK → supplier | Fournisseur |
| `ordered_at` | TIMESTAMPTZ | Date de commande |
| `expected_delivery_date` | DATE | Date livraison prévue |
| `received_at` | TIMESTAMPTZ | Date de réception réelle |
| `status` | VARCHAR DEFAULT `brouillon` | État : `brouillon`, `OPEN`, `envoyé`, `reçu`, `annulé` |
| `total_amount` | NUMERIC(10,2) | Montant total calculé |
| `currency` | REAL | Devise |
| `notes` | TEXT | Notes |

**Note** : Le statut `OPEN` est utilisé par `dispatch_purchase_requests()` pour identifier les paniers en cours d'alimentation.

#### `supplier_order_line` — Lignes de commande

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID PK | Identifiant |
| `supplier_order_id` | UUID FK → supplier_order | Commande parente |
| `stock_item_id` | UUID FK → stock_item | Article commandé |
| `supplier_ref_snapshot` | TEXT | Snapshot de la référence fournisseur au moment de la commande |
| `quantity` | INTEGER NOT NULL | Quantité commandée |
| `unit_price` | NUMERIC(10,2) | Prix unitaire |
| `total_price` | NUMERIC(10,2) | Total auto-calculé : `unit_price × quantity` (trigger) |
| `quantity_received` | INTEGER | Quantité effectivement reçue |
| `notes` | TEXT | Notes |

**Contrainte** : `(supplier_order_id, stock_item_id)` est unique — un article ne peut apparaître qu'une fois par commande.

**En cas de conflit (dispatch)** : la quantité est additionnée (`DO UPDATE SET quantity = quantity + EXCLUDED.quantity`).

#### `supplier_order_line_purchase_request` — Table de jonction

Traçabilité du lien entre une ligne de commande et la ou les demandes d'achat qu'elle couvre.

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID PK | Identifiant |
| `supplier_order_line_id` | UUID FK → supplier_order_line | Ligne de commande |
| `purchase_request_id` | UUID FK → purchase_request | Demande d'achat |
| `quantity_fulfilled` | INTEGER NOT NULL | Quantité de la demande couverte par cette ligne |

**Contrainte** : `(supplier_order_line_id, purchase_request_id)` est unique.

---

## 6. Module Maintenance préventive

### 6.1 Concept

Le moteur préventif analyse automatiquement les descriptions d'actions de dépannage pour détecter des opportunités de maintenance préventive. Il fonctionne par correspondance de mots-clés, sans IA ni NLP — uniquement du texte normalisé en minuscule.

### 6.2 Principe de fonctionnement

```
intervention_action (description)
    ↓  [trigger AFTER INSERT]
detect_preventive_suggestions()
    ↓  [filtre : sous-catégorie DEP_* uniquement]
    ↓  [cherche mots-clés dans lower(description)]
    ↓  [pour chaque match : preventive_rule]
preventive_suggestion (INSERT, ON CONFLICT DO NOTHING)
```

**Règle de déduplication** : Une machine ne peut avoir qu'une seule suggestion active par code de préconisation (`UNIQUE(machine_id, preventive_code)`). Si la préconisation existe déjà, l'insertion est silencieusement ignorée.

### 6.3 Tables

#### `preventive_rule` — Règles de détection (référentiel)

| Colonne | Type | Description |
|---|---|---|
| `id` | SERIAL PK | Identifiant |
| `keyword` | TEXT NOT NULL UNIQUE | Mot-clé à détecter dans la description (comparaison en minuscule) |
| `preventive_code` | TEXT NOT NULL | Code standardisé de la préconisation (ex: `PREV_COURROIE`) |
| `preventive_label` | TEXT NOT NULL | Libellé lisible (ex: "Contrôle tension & alignement courroies") |
| `weight` | INT DEFAULT 1 | Poids/importance de la règle (1 = faible, 2 = standard) |
| `active` | BOOLEAN DEFAULT TRUE | Règle active ou désactivée sans suppression |

**Règles actives au démarrage** :

| Mot-clé | Code | Poids |
|---|---|---|
| `courroie` | `PREV_COURROIE` | 2 |
| `lame` | `PREV_LAME` | 2 |
| `couteau` | `PREV_LAME` | 2 |
| `roulement` | `PREV_ROULEMENT` | 2 |
| `capteur` | `PREV_CAPTEUR` | 2 |
| `filtre` | `PREV_FILTRE` | 2 |
| `cable` | `PREV_CABLE` | 1 |
| `vis` | `PREV_SERRAGE` | 1 |
| `axe` | `PREV_SERRAGE` | 1 |
| `pompe` | `PREV_POMPE` | 2 |

**Gestion** :
- Désactiver une règle : `UPDATE preventive_rule SET active = FALSE WHERE keyword = 'vis';`
- Ajouter une règle : `INSERT INTO preventive_rule (keyword, preventive_code, preventive_label, weight) VALUES (...);`

#### `preventive_suggestion` — Préconisations détectées

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID PK | Identifiant |
| `intervention_action_id` | UUID FK → intervention_action (RESTRICT) UNIQUE | Action ayant déclenché la détection |
| `machine_id` | UUID FK → machine (RESTRICT) | Machine concernée |
| `preventive_code` | TEXT NOT NULL | Code de la préconisation |
| `preventive_label` | TEXT NOT NULL | Libellé copié depuis la règle (snapshot) |
| `score` | INT NOT NULL | Poids de la règle au moment de la détection (snapshot) |
| `status` | TEXT DEFAULT `NEW` | État : `NEW`, `REVIEWED`, `ACCEPTED`, `REJECTED` |
| `detected_at` | TIMESTAMP | Date de détection automatique |
| `handled_at` | TIMESTAMP | Date de traitement par le superviseur |
| `handled_by` | UUID | Superviseur ayant traité la suggestion |

### 6.4 Cycle de vie d'une suggestion préventive

```
NEW (détectée automatiquement)
  → REVIEWED (superviseur a consulté)
  → ACCEPTED (prise en compte → création manuelle d'une DI_PREV)
  → REJECTED (refusée, conservée pour trace)
```

**Contrainte de cohérence** :
- `handled_at IS NULL` → `status` doit être `NEW`
- `handled_at IS NOT NULL` → `status` doit être `REVIEWED`, `ACCEPTED` ou `REJECTED`

**Contrainte de déduplication** : `UNIQUE(machine_id, preventive_code)` — la même préconisation ne peut être en attente deux fois pour la même machine.

### 6.5 Vue `preventive_suggestion_by_status`

Vue SQL préconstruite pour les requêtes API (jointure `preventive_suggestion` + `machine`), permettant de lister les suggestions par statut et machine directement depuis Directus ou le backend.

---

## 7. Mécanique des triggers

### 7.1 Code d'intervention — `trg_interv_code`

**Déclencheur** : BEFORE INSERT sur `intervention`  
**Fonction** : `generate_intervention_code()`

**Format** : `{machine.code}-{type_inter}-{YYYYMMDD}-{tech_initials}`

**Exemple** : `CONV01-PREV-20241228-JD`

**Comportement** : Si `machine_id` ne correspond à aucune machine, lève une exception PostgreSQL. La transaction est annulée.

### 7.2 Historique statut intervention — `trg_init_status_log` / `trg_log_status_change`

**`trg_init_status_log`** : AFTER INSERT sur `intervention`  
→ Positionne `status_actual = 'ouvert'`  
→ Crée l'entrée initiale dans `intervention_status_log` (`status_from = NULL`, `status_to = 'ouvert'`, `notes = 'Création intervention'`)

**`trg_log_status_change`** : AFTER UPDATE sur `intervention` (WHEN `status_actual` change)  
→ Crée une entrée dans `intervention_status_log` avec `status_from = OLD.status_actual`, `status_to = NEW.status_actual`  
→ Ignore les créations (`OLD.status_actual IS NULL`)

### 7.3 Référence article stock — `trg_generate_stock_item_ref`

**Déclencheur** : BEFORE INSERT OR UPDATE OF `family_code`, `sub_family_code`, `spec`, `dimension` sur `stock_item`  
**Fonction** : `generate_stock_item_ref()`

**Format** : `{family_code}-{sub_family_code}[-{spec}][-{dimension}]`

Les segments `spec` et `dimension` ne sont concaténés que s'ils sont non-NULL et non-vides. Résultats possibles :
- Complet : `VIS-CHC-M8-20`
- Sans spec : `VIS-CHC--20`
- Minimum : `VIS-CHC`

### 7.4 Numérotation commande fournisseur — `trg_generate_supplier_order_number`

**Déclencheur** : BEFORE INSERT sur `supplier_order`  
**Fonction** : `generate_supplier_order_number()`

**Format** : `CMD-{YYYYMMDD}-{NNNN}` (séquence `supplier_order_seq`, paddée sur 4 chiffres)

**Exemple** : `CMD-20241228-0001`

**Comportement** : Ne génère un numéro que si `order_number` est NULL ou vide à l'insertion — permet de forcer un numéro manuellement.

### 7.5 Total ligne commande — `trg_calculate_line_total`

**Déclencheur** : BEFORE INSERT OR UPDATE OF `unit_price`, `quantity` sur `supplier_order_line`  
**Calcul** : `total_price = unit_price × quantity` (si les deux sont non-NULL)

### 7.6 Horodatage `updated_at` — `trg_*_updated_at`

Triggers BEFORE UPDATE sur : `purchase_request`, `stock_item_supplier`, `supplier_order_line`, `supplier_order`, `supplier`. Positionnent `updated_at = NOW()` automatiquement.

### 7.7 Compteur de références fournisseurs — `trg_update_supplier_refs_count`

**Déclencheur** : sur `stock_item_supplier` (INSERT / UPDATE / DELETE)  
**Effet** : Maintient `stock_item.supplier_refs_count` à jour — compte le nombre de lignes dans `stock_item_supplier` pour chaque article.

### 7.8 Moteur préventif — `detect_preventive_suggestions`

**Déclencheur** : AFTER INSERT sur `intervention_action`  
Voir [§6.2](#62-principe-de-fonctionnement) pour le détail complet.

### 7.9 Dispatch demandes d'achat — `dispatch_purchase_requests()`

**Type** : Fonction stockée appelée manuellement (non attachée à un trigger)  
**Retour** : JSON `{ dispatched: [...], toQualify: [...], errors: [...] }`

**Algorithme** :
1. Sélectionne toutes les `purchase_request` avec `status = 'open'` et `stock_item_id IS NOT NULL`
2. Pour chaque demande, cherche le fournisseur préféré (`is_preferred = TRUE`) dans `stock_item_supplier`
3. Si aucun fournisseur préféré → l'article est placé en `toQualify`
4. Sinon : cherche ou crée un panier `supplier_order` avec `status = 'OPEN'` pour ce fournisseur
5. Insère ou agrège la ligne dans `supplier_order_line` (`ON CONFLICT DO UPDATE` sur la quantité)
6. Passe la `purchase_request` à `status = 'in_progress'`

---

## 8. Règles métier transversales

### 8.1 Intégrité référentielle

| Relation | ON DELETE |
|---|---|
| `machine.equipment_class_id` → `equipment_class` | SET NULL |
| `machine.equipement_mere` → `machine` | NO ACTION (bloquant) |
| `intervention_action` → `intervention_action` (préventif) | RESTRICT |
| `preventive_suggestion.machine_id` → `machine` | RESTRICT |
| `stock_item_characteristic.stock_item_id` → `stock_item` | CASCADE |
| `stock_item_characteristic.field_id` → `part_template_field` | RESTRICT |
| `part_template_field.template_id` → `part_template` | CASCADE |
| `stock_sub_family.template_id` → `part_template` | SET NULL |

### 8.2 Unicités métier importantes

| Table | Contrainte d'unicité |
|---|---|
| `machine` | `code` |
| `intervention` | `code` (auto-généré) |
| `stock_item` | `ref` (auto-générée) |
| `stock_item_supplier` | `(stock_item_id, supplier_id)` |
| `supplier_order` | `order_number` |
| `supplier_order_line` | `(supplier_order_id, stock_item_id)` |
| `supplier_order_line_purchase_request` | `(supplier_order_line_id, purchase_request_id)` |
| `preventive_suggestion` | `intervention_action_id` (1 suggestion par action) |
| `preventive_suggestion` | `(machine_id, preventive_code)` (1 préco active par type et machine) |
| `stock_item_characteristic` | `(stock_item_id, field_id)` |
| `part_template` | `(code, version)` |
| `action_subcategory` | `code` |
| `stock_sub_family` | `(family_code, code)` |

### 8.3 Contraintes CHECK notables

| Table | Contrainte |
|---|---|
| `stock_item` | `quantity >= 0` |
| `part_template` | `version > 0` |
| `part_template_field` | `field_type IN ('number', 'text', 'enum')` |
| `part_template_field` | `sort_order > 0` |
| `stock_item_characteristic` | Exactement une valeur non-NULL parmi `value_text`, `value_number`, `value_enum` |
| `preventive_suggestion` | `handled_at IS NULL ↔ status = 'NEW'` |

### 8.4 Identifiants utilisateurs

Les colonnes `tech`, `updated_by`, `technician_id`, `assigned_to`, `handled_by` stockent des UUID référençant des utilisateurs gérés **en dehors** de cette base (Directus, système d'authentification externe). Il n'existe pas de table `user` dans ce schéma — aucune FK n'est posée sur ces colonnes.

---

## 9. Conventions d'identification

### 9.1 Identifiants techniques

Toutes les tables utilisent un `id UUID` généré par `uuid_generate_v4()` (extension `uuid-ossp`) ou `gen_random_uuid()`. Aucune table n'utilise d'entier auto-incrémenté comme PK, à l'exception de `action_category`, `action_subcategory` (INTEGER séquentiel) et `preventive_rule` (SERIAL).

### 9.2 Codes métier auto-générés

| Entité | Format | Exemple | Trigger |
|---|---|---|---|
| Intervention | `{machine.code}-{type_inter}-{YYYYMMDD}-{initials}` | `CONV01-PREV-20241228-JD` | `trg_interv_code` |
| Article stock | `{FAM}-{SFAM}[-{spec}][-{dim}]` | `VIS-CHC-M8-20` | `trg_generate_stock_item_ref` |
| Commande fournisseur | `CMD-{YYYYMMDD}-{NNNN}` | `CMD-20241228-0001` | `trg_generate_supplier_order_number` |

### 9.3 Codes métier stables (référentiels)

| Domaine | Table | Exemples de codes |
|---|---|---|
| Catégories action | `action_category.code` | `DEP`, `FAB`, `PREV`, `SUP`, `BAT` |
| Sous-catégories action | `action_subcategory.code` | `DEP_ELEC`, `DEP_MECA`, `PREV_GRAIS` |
| Statuts intervention | `intervention_status_ref.code` | `ouvert`, `en_cours`, `ferme`, `annule` |
| Statuts achat | `purchase_status.code` | `en_attente`, `approuve`, `commande`, `recu`, `refuse` |
| Familles stock | `stock_family.code` | `VIS`, `ROUL`, `COURR`, `HUIL`, `ELEC` |
| Classes équipement | `equipment_class.code` | `EXT`, `LIG`, `TPE`, `TRY`, `POMP` |
| Facteurs complexité | `complexity_factor.code` | `simple`, `moyen`, `eleve`, `critique` |
| Préconisations préventive | `preventive_rule.preventive_code` | `PREV_COURROIE`, `PREV_ROULEMENT` |

### 9.4 Conventions de nommage des colonnes

- Les timestamps de création sont toujours `created_at TIMESTAMPTZ`.
- Les timestamps de modification sont `updated_at TIMESTAMPTZ`, maintenus par trigger.
- Les booléens d'état sont préfixés `is_` (ex: `is_active`, `is_preferred`, `is_mere`).
- Les FK vers des tables référentielles par code utilisent le suffixe `_code` (ex: `family_code`, `sub_family_code`).
- Les FK par UUID utilisent le suffixe `_id` (ex: `machine_id`, `supplier_id`).

---

*Document généré le 3 mars 2026 — basé exclusivement sur le DDL de production v1.4.1.*
