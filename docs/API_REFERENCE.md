# Référence Complète API — Tunnel GMAO

**Version API :** 2.6.0  
**Date :** 2026-03-02  
**Base URL :** `http://<host>:8000`

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Authentification](#2-authentification)
3. [Équipements](#3-équipements)
4. [Interventions — Cycle de vie complet](#4-interventions--cycle-de-vie-complet)
5. [Actions d'intervention](#5-actions-dintervention)
6. [Statuts & Journal de traçabilité](#6-statuts--journal-de-traçabilité)
7. [Stock — Architecture & Catalogage](#7-stock--architecture--catalogage)
8. [Templates de pièces](#8-templates-de-pièces)
9. [Fournisseurs & Références pièces](#9-fournisseurs--références-pièces)
10. [Demandes d'achat — Cycle de vie complet](#10-demandes-dachat--cycle-de-vie-complet)
11. [Commandes fournisseurs](#11-commandes-fournisseurs)
12. [Statistiques & KPIs](#12-statistiques--kpis)
13. [Exports](#13-exports)
14. [Référentiels](#14-référentiels)
15. [Conventions transversales](#15-conventions-transversales)

---

## 1. Vue d'ensemble

Tunnel est un **GMAO** (Gestion de Maintenance Assistée par Ordinateur). La philosophie centrale est que **l'action est l'unité réelle de travail** : le temps, la complexité et les pièces sont tracés action par action, jamais au niveau de l'intervention globale.

### Flux principal

```
Équipement → Intervention → Action(s) → Demande(s) d'achat
                                               ↓
                                     Dispatch automatique
                                               ↓
                                   Ligne commande fournisseur
                                               ↓
                                    Commande fournisseur
                                               ↓
                                      Réception pièces
```

### Vérification de santé

```
GET /health
```

Réponse publique (pas d'auth requise) :

```json
{
  "status": "ok",
  "database": "connected",
  "auth_service": "reachable"
}
```

---

## 2. Authentification

### `POST /auth/login`

Authentification via proxy Directus. Configures un cookie de session **et** retourne un JWT Bearer.

```json
{
  "email": "user@example.com",
  "password": "secret",
  "mode": "session"
}
```

**Réponse `200` :**

```json
{
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "abc123...",
    "expires": 900000
  }
}
```

| Champ          | Description                        |
| -------------- | ---------------------------------- |
| `access_token` | JWT valide, identique au cookie    |
| `expires`      | Durée de validité en millisecondes |

### Cookie de session

Un cookie `session_token` est automatiquement positionné :

| Propriété | Valeur               |
| --------- | -------------------- |
| Nom       | `session_token`      |
| HttpOnly  | `true`               |
| SameSite  | `Lax`                |
| Max-Age   | 86400 secondes (24h) |

### Modes d'utilisation

**Navigateur** — le cookie est envoyé automatiquement :

```
GET /users/me
Cookie: session_token=eyJhbG...
```

**Mobile / API** — header Authorization :

```
GET /users/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Mode développement

Quand `AUTH_DISABLED=true` dans `.env`, les requêtes sans token passent. **Ne jamais utiliser en production.**

---

## 3. Équipements

### Structure de données

**Table :** `machine`

| Champ                 | Type    | Description                      |
| --------------------- | ------- | -------------------------------- |
| `id`                  | UUID    | Identifiant auto-généré          |
| `name`                | string  | **Requis** — Nom de l'équipement |
| `code`                | string  | Code utilisateur                 |
| `no_machine`          | string  | Numéro machine                   |
| `affectation`         | string  | Localisation / atelier           |
| `is_mere`             | boolean | Flag parent                      |
| `fabricant`           | string  | Fabricant                        |
| `numero_serie`        | string  | Numéro de série                  |
| `date_mise_service`   | date    | Date de mise en service          |
| `notes`               | text    | Notes libres                     |
| `parent_id`           | UUID FK | Équipement parent                |
| `equipement_class_id` | UUID FK | Classe d'équipement              |

### Hiérarchie

Un équipement peut avoir un parent (`parent_id`) et N enfants. Navigation via :

- `GET /equipements/{id}/children` — enfants paginés avec état de santé
- `children_count` calculé par COUNT en base

### État de santé (calculé, jamais stocké)

L'état de santé (`health`) est recalculé à chaque lecture depuis les interventions ouvertes. Une intervention est considérée **ouverte** si `status_actual != code_ferme`.

| Priorité | Condition                               | Niveau        |
| -------- | --------------------------------------- | ------------- |
| 1        | Au moins 1 intervention urgente ouverte | `critical`    |
| 2        | Plus de 5 interventions ouvertes        | `warning`     |
| 3        | Au moins 1 intervention ouverte         | `maintenance` |
| 4        | Aucune intervention ouverte             | `ok`          |

```json
{
  "level": "critical",
  "reason": "1 intervention urgente ouverte",
  "rules_triggered": ["URGENT_OPEN >= 1"]
}
```

> `rules_triggered` est présent uniquement dans le détail (`GET /equipements/{id}`), absent en liste.

### Endpoints

| Méthode  | URL                          | Description                                                          |
| -------- | ---------------------------- | -------------------------------------------------------------------- |
| `GET`    | `/equipements`               | Liste légère triée par criticité (urgent DESC, ouvert DESC, nom ASC) |
| `GET`    | `/equipements/{id}`          | Détail complet avec interventions paginées                           |
| `GET`    | `/equipements/{id}/children` | Enfants paginés (search sur code/nom)                                |
| `GET`    | `/equipements/{id}/stats`    | Statistiques par statut et priorité sur une période                  |
| `POST`   | `/equipements`               | Création (`name` requis)                                             |
| `PUT`    | `/equipements/{id}`          | Mise à jour partielle                                                |
| `DELETE` | `/equipements/{id}`          | Suppression                                                          |

### Exemple de liste

```json
[
  {
    "id": "uuid",
    "code": "EQ-001",
    "name": "Scie principale",
    "health": { "level": "maintenance", "reason": "1 intervention ouverte" },
    "parent_id": null,
    "equipement_class": { "id": "uuid", "code": "SCIE", "label": "Scie" }
  }
]
```

### Statistiques par équipement

```
GET /equipements/{id}/stats?start_date=2026-01-01&end_date=2026-03-01
```

```json
{
  "interventions": {
    "open": 2,
    "closed": 5,
    "by_status": { "ouvert": 2, "ferme": 5 },
    "by_priority": { "faible": 1, "normale": 4, "urgent": 2 }
  }
}
```

---

## 4. Interventions — Cycle de vie complet

### Structure de données

**Table :** `intervention`

| Champ           | Type    | Défaut   | Description                    |
| --------------- | ------- | -------- | ------------------------------ |
| `id`            | UUID    | auto     | Généré par l'application       |
| `title`         | string  | null     | Titre libre                    |
| `machine_id`    | UUID FK | null     | Équipement concerné            |
| `type_inter`    | string  | null     | Type (voir tableau ci-dessous) |
| `priority`      | string  | null     | Priorité                       |
| `reported_by`   | string  | null     | Nom du signaleur               |
| `tech_initials` | string  | null     | Initiales du technicien        |
| `status_actual` | string  | `ouvert` | Identifiant du statut courant  |
| `printed_fiche` | boolean | `false`  | Fiche imprimée / archivée      |
| `reported_date` | date    | null     | Date de signalement            |
| `updated_by`    | UUID FK | null     | Dernier modificateur           |

### Types d'intervention (ENUM fixe)

| Code  | Label                | Couleur UI |
| ----- | -------------------- | ---------- |
| `CUR` | Curatif              | Rouge      |
| `PRE` | Préventif            | Vert       |
| `REA` | Réapprovisionnement  | Bleu       |
| `BAT` | Bâtiment             | Gris       |
| `PRO` | Projet               | Bleu       |
| `COF` | Remise en conformité | Ambre      |
| `PIL` | Pilotage             | Bleu       |
| `MES` | Mise en service      | Ambre      |

### Priorités (ordre de sévérité)

| Valeur      | Priorité numérique | Couleur |
| ----------- | ------------------ | ------- |
| `urgent`    | 0 (la plus haute)  | Violet  |
| `important` | 1                  | Rouge   |
| `normal`    | 2                  | Ambre   |
| `faible`    | 3 (la plus basse)  | Vert    |

Tri SQL par sévérité décroissante :

```sql
CASE priority
  WHEN 'urgent'    THEN 0
  WHEN 'important' THEN 1
  WHEN 'normal'    THEN 2
  WHEN 'faible'    THEN 3
  ELSE 4
END ASC
```

### Statistiques calculées

Ces champs sont calculés depuis les actions, jamais stockés :

| Champ            | Calcul                                                |
| ---------------- | ----------------------------------------------------- |
| `action_count`   | `COUNT(DISTINCT intervention_action.id)`              |
| `total_time`     | `SUM(intervention_action.time_spent)`                 |
| `avg_complexity` | `ROUND(AVG(intervention_action.complexity_score), 2)` |
| `purchase_count` | `COUNT(DISTINCT purchase_requests liées)`             |

### Cycle de vie d'une intervention

```
         CRÉATION
             │
             ▼
         [ouvert]  ◄────────────────────────────────┐
             │                                       │
             │  POST /intervention-status-log        │
             ▼                                       │
         [en_cours]                                  │
             │                                       │
             │  Actions saisies via                  │
             │  POST /intervention-actions            │
             │                                       │
             │  Pièces demandées via                 │
             │  POST /purchase-requests              │
             │                                       │
             ▼                                       │
         [en_attente] (pièces manquantes)            │
             │                                       │
             │  Pièces reçues                        │
             ▼                                       │
         [en_cours]  ──────────────────── Réouverture┘
             │
             │  POST /intervention-status-log
             │  (status_to = id du statut "ferme")
             ▼
          [ferme]  ──── PDF générable via GET /exports/interventions/{id}/pdf
```

**Points clés :**

- `status_actual` est initialisé à `ouvert` à la création si non fourni
- La mise à jour directe via `PUT /interventions/{id}` (champ `status_actual`) ne génère **aucune trace dans le journal**
- Pour un audit complet, utiliser `POST /intervention-status-log` (qui met à jour `status_actual` via trigger DB)
- La fermeture (`ferme`) est le seul statut excluant une intervention du calcul de santé des équipements

### Endpoints

| Méthode  | URL                           | Description                            |
| -------- | ----------------------------- | -------------------------------------- |
| `GET`    | `/interventions`              | Liste avec filtres, tri, pagination    |
| `GET`    | `/interventions/{id}`         | Détail complet (actions + status_logs) |
| `GET`    | `/interventions/{id}/actions` | Raccourci vers les actions             |
| `POST`   | `/interventions`              | Création                               |
| `PUT`    | `/interventions/{id}`         | Mise à jour                            |
| `DELETE` | `/interventions/{id}`         | Suppression                            |

### Filtres disponibles

| Param            | Type | Description                                             |
| ---------------- | ---- | ------------------------------------------------------- |
| `skip` / `limit` | int  | Pagination (max 1000)                                   |
| `equipement_id`  | uuid | Filtrer par équipement                                  |
| `status`         | csv  | Codes statut (ex: `ouvert,en_cours`)                    |
| `priority`       | csv  | Priorités (ex: `urgent,important`)                      |
| `printed`        | bool | `true` = fiches archivées seulement                     |
| `sort`           | csv  | Tri avec `-` pour DESC (ex: `-priority,-reported_date`) |
| `include`        | csv  | `stats` pour inclure les statistiques calculées         |

### Réponse list (note importante)

```json
{
  "id": "uuid",
  "code": "CN001-REA-20260113-QC",
  "equipements": { ... },
  "stats": { "action_count": 3, "total_time": 4.5, "avg_complexity": 6.2, "purchase_count": 1 },
  "actions": [],
  "status_logs": []
}
```

> `actions` et `status_logs` sont toujours `[]` en liste. Utiliser `GET /interventions/{id}` pour les obtenir.

---

## 5. Actions d'intervention

L'action est l'unité réelle de travail. Elle porte le temps, la complexité et les pièces.

### Structure de données

**Table :** `intervention_action`

| Champ                | Type      | Obligatoire  | Description                                  |
| -------------------- | --------- | ------------ | -------------------------------------------- |
| `id`                 | UUID      | auto         | Généré par l'application                     |
| `intervention_id`    | UUID FK   | **Oui**      | Intervention parente                         |
| `description`        | text      | **Oui**      | Description (HTML nettoyé + trim)            |
| `time_spent`         | float     | **Oui**      | Temps en heures (multiple de 0.25, min 0.25) |
| `action_subcategory` | int FK    | **Oui**      | Sous-catégorie d'action                      |
| `tech`               | UUID FK   | **Oui**      | Technicien (`directus_users`)                |
| `complexity_score`   | int       | **Oui**      | Score 1 à 10                                 |
| `complexity_factor`  | string FK | Conditionnel | **Obligatoire si score > 5**                 |
| `created_at`         | datetime  | Non          | Défaut : `NOW()`. Backdating autorisé        |

### Règles de validation (CRITIQUES)

#### time_spent — Granularité quart d'heure

```
Valeurs valides : 0.25, 0.50, 0.75, 1.00, 1.25, 1.50 ...
ERREUR si time_spent < 0.25
ERREUR si time_spent % 0.25 != 0
```

#### complexity_score — Entier 1 à 10

```
ERREUR si < 1 ou > 10 ou non entier
```

#### complexity_factor — Justification de complexité élevée

```
SI complexity_score > 5 → complexity_factor OBLIGATOIRE (code dans complexity_factor)
SI complexity_score <= 5 → complexity_factor ignoré même s'il est fourni
```

**Justification métier :** Un score élevé doit être documenté par un facteur connu.

#### description — Sanitisation obligatoire

```
1. Supprimer tout HTML
2. Trimmer les espaces
3. ERREUR si résultat vide
```

#### created_at — Backdating autorisé

Un technicien peut saisir une action rétroactivement. Si null → `NOW()`.

### Endpoints

| Méthode  | URL                          | Description                                   |
| -------- | ---------------------------- | --------------------------------------------- |
| `GET`    | `/intervention-actions`      | Liste globale                                 |
| `GET`    | `/intervention-actions/{id}` | Détail avec sous-catégorie + demandes d'achat |
| `POST`   | `/intervention-actions`      | Création                                      |
| `PUT`    | `/intervention-actions/{id}` | Mise à jour                                   |
| `DELETE` | `/intervention-actions/{id}` | Suppression                                   |

### Structure de retour (InterventionActionOut)

```json
{
  "id": "uuid",
  "intervention_id": "uuid",
  "description": "Remplacement du roulement SKF 6205",
  "time_spent": 1.5,
  "subcategory": {
    "id": 30,
    "name": "Remplacement pièce",
    "code": "DEP_REM",
    "category": {
      "id": 3,
      "name": "Dépannage",
      "code": "DEP",
      "color": "#e53e3e"
    }
  },
  "tech": {
    "id": "uuid",
    "first_name": "Jean",
    "last_name": "Dupont",
    "email": "jean.dupont@example.com",
    "initial": "JD"
  },
  "complexity_score": 7,
  "complexity_factor": "PCE",
  "purchase_requests": [],
  "created_at": "2026-01-13T14:30:00",
  "updated_at": "2026-01-13T15:00:00"
}
```

### Facteurs de complexité

Récupérables via `GET /complexity-factors`. Exemples :

| Code  | Label                        | Catégorie   |
| ----- | ---------------------------- | ----------- |
| `PCE` | Pièce manquante ou inadaptée | Logistique  |
| `ACC` | Accès difficile              | Technique   |
| `DOC` | Documentation manquante      | Information |

---

## 6. Statuts & Journal de traçabilité

### Référentiel des statuts

**Table :** `intervention_status_ref`

```
GET /intervention-status
```

```json
[
  {
    "id": "uuid",
    "code": "ouvert",
    "label": "Ouvert",
    "color": "#22c55e",
    "value": 1
  },
  {
    "id": "uuid",
    "code": "en_cours",
    "label": "En cours",
    "color": "#3b82f6",
    "value": 2
  },
  {
    "id": "uuid",
    "code": "ferme",
    "label": "Fermé",
    "color": "#6b7280",
    "value": 3
  }
]
```

**Constante critique :** Le code `ferme` est hardcodé dans l'application pour le calcul des interventions ouvertes.

### Journal des changements (intervention_status_log)

**Table :** `intervention_status_log`

| Champ             | Type     | Obligatoire | Description                                  |
| ----------------- | -------- | ----------- | -------------------------------------------- |
| `id`              | UUID     | auto        |                                              |
| `intervention_id` | UUID FK  | **Oui**     |                                              |
| `status_from`     | string   | Non         | Statut de départ (null = premier changement) |
| `status_to`       | string   | **Oui**     | Nouveau statut                               |
| `technician_id`   | UUID FK  | **Oui**     | Technicien responsable                       |
| `date`            | datetime | **Oui**     | Horodatage                                   |
| `notes`           | text     | Non         | Raison (HTML nettoyé)                        |

### Règle CRITIQUE : cohérence de status_from

```
SI status_from est fourni (non null) :
  → status_from DOIT correspondre au status_actual courant de l'intervention
  → SINON : erreur 400

SI status_from est null :
  → Autorisé (premier enregistrement)
```

**Exemple d'erreur :**

```
"Le status_from 'en_cours' ne correspond pas au statut actuel de l'intervention 'ouvert'"
```

### Trigger base de données

La création d'un `intervention_status_log` met automatiquement à jour `intervention.status_actual` avec `status_to` via trigger PostgreSQL. Il n'est **pas nécessaire** de faire un PUT séparé sur l'intervention.

### Endpoints

| Méthode | URL                             | Description                                      |
| ------- | ------------------------------- | ------------------------------------------------ |
| `GET`   | `/intervention-status`          | Liste des statuts de référence                   |
| `GET`   | `/intervention-status-log`      | Liste des entrées (filtre par `intervention_id`) |
| `GET`   | `/intervention-status-log/{id}` | Détail avec statuts enrichis                     |
| `POST`  | `/intervention-status-log`      | Crée un changement de statut                     |

### Réponse enrichie

```json
{
  "id": "uuid",
  "intervention_id": "uuid",
  "status_from": "ouvert",
  "status_to": "en_cours",
  "status_from_detail": {
    "id": "uuid",
    "code": "ouvert",
    "label": "Ouvert",
    "color": "#22c55e"
  },
  "status_to_detail": {
    "id": "uuid",
    "code": "en_cours",
    "label": "En cours",
    "color": "#3b82f6"
  },
  "technician_id": "uuid",
  "date": "2026-01-13T08:30:00",
  "notes": "Prise en charge par QC"
}
```

---

## 7. Stock — Architecture & Catalogage

### Hiérarchie du stock (4 niveaux)

```
StockFamily (famille)
  └── StockSubFamily (sous-famille)
        └── PartTemplate (template optionnel)
              └── StockItem (article)
```

### Familles et sous-familles

```
GET /stock-families        → Liste des familles (code PK, label)
GET /stock-sub-families    → Liste des sous-familles (code, family_code FK, label, template_id FK)
```

Les codes famille et sous-famille servent de clés dans tout le catalogue (ex: `OUT` / `ROUL`).

### Articles (StockItem)

**Table :** `stock_item`

| Champ              | Type      | Description                                               |
| ------------------ | --------- | --------------------------------------------------------- |
| `id`               | UUID      | Identifiant                                               |
| `name`             | string    | **Requis** — Nom de la pièce                              |
| `ref`              | string    | **Auto-générée par trigger DB** (ex: `OUT-ROUL-SKF-6205`) |
| `family_code`      | string FK | **Requis** — Code famille                                 |
| `sub_family_code`  | string FK | **Requis** — Code sous-famille                            |
| `spec`             | text      | Spécification libre                                       |
| `dimension`        | string    | Dimension (saisie en legacy, générée en template)         |
| `quantity`         | int       | Quantité en stock                                         |
| `unit`             | string    | Unité (pcs, m, kg, etc.)                                  |
| `location`         | string    | Emplacement physique                                      |
| `standars_spec`    | string    | Spec standard                                             |
| `template_id`      | UUID FK   | Template utilisé (null si legacy)                         |
| `template_version` | int       | Version du template                                       |

**Important :** La référence (`ref`) est **générée automatiquement par trigger PostgreSQL**. Elle ne peut pas être saisie manuellement.

### Deux modes de création

Le mode est déterminé automatiquement au moment de la création selon que la sous-famille possède un template ou non.

#### Mode LEGACY (sous-famille sans template)

```json
{
  "name": "Roulement SKF 6205",
  "family_code": "OUT",
  "sub_family_code": "ROUL",
  "dimension": "6205",
  "spec": "SKF",
  "quantity": 15,
  "unit": "pcs",
  "location": "Étagère A3"
}
```

| Règle             | Description                       |
| ----------------- | --------------------------------- |
| `dimension`       | **Obligatoire** (saisie manuelle) |
| `characteristics` | Ignoré                            |
| `template_id`     | Stocké `null`                     |

#### Mode TEMPLATE (sous-famille avec template)

```json
{
  "name": "Roulement à billes 6205",
  "family_code": "OUT",
  "sub_family_code": "ROUL",
  "spec": "SKF",
  "quantity": 10,
  "unit": "pcs",
  "location": "Étagère A3",
  "characteristics": [
    { "key": "DIAM_INT", "value": 25 },
    { "key": "DIAM_EXT", "value": 52 },
    { "key": "LARG", "value": 15 }
  ]
}
```

| Règle             | Description                                                                    |
| ----------------- | ------------------------------------------------------------------------------ |
| `dimension`       | **Interdit** en saisie — générée automatiquement depuis le pattern du template |
| `characteristics` | **Obligatoires** — validées selon le template                                  |
| `template_id`     | Renseigné automatiquement                                                      |

**Exemple de génération :**

```
Pattern : "{DIAM_INT}x{DIAM_EXT}x{LARG}"
Valeurs : DIAM_INT=25, DIAM_EXT=52, LARG=15
Dimension → "25x52x15"
Référence → "OUT-ROUL-SKF-25x52x15"
```

### Immutabilité des articles template

Une fois créé avec un template, ces champs sont **non modifiables** :

```
template_id, template_version, dimension, family_code, sub_family_code, characteristics
```

Champs modifiables même pour un article template :

```
name, spec, quantity, unit, location, standars_spec
```

### Mise à jour de quantité (endpoint dédié)

```
PATCH /stock-items/{id}/quantity
```

Permet de mettre à jour uniquement la quantité sans toucher aux autres champs.

### Endpoints

| Méthode  | URL                                      | Description                                  |
| -------- | ---------------------------------------- | -------------------------------------------- |
| `GET`    | `/stock-items`                           | Liste avec filtres, pagination, **facettes** |
| `GET`    | `/stock-items/{id}`                      | Détail avec fournisseurs et template         |
| `GET`    | `/stock-items/{id}/with-characteristics` | Détail + caractéristiques                    |
| `GET`    | `/stock-items/ref/{ref}`                 | Recherche par référence                      |
| `POST`   | `/stock-items`                           | Création (mode auto-détecté)                 |
| `PUT`    | `/stock-items/{id}`                      | Mise à jour partielle                        |
| `PATCH`  | `/stock-items/{id}/quantity`             | Mise à jour de quantité uniquement           |
| `DELETE` | `/stock-items/{id}`                      | Suppression                                  |

### Facettes (calculées en une seule requête)

La réponse de liste inclut des facettes pour l'UI :

```json
{
  "items": [ ... ],
  "pagination": { "total": 150, "page": 1, "page_size": 50, ... },
  "facets": {
    "families": [
      {
        "code": "OUT",
        "label": "Outillage",
        "count": 45,
        "sub_families": [
          { "code": "ROUL", "label": "Roulements", "count": 20 }
        ]
      }
    ]
  }
}
```

### Filtres de liste

| Param             | Description                                     |
| ----------------- | ----------------------------------------------- |
| `search`          | Recherche sur `name` ou `ref` (ILIKE)           |
| `family_code`     | Filtrer par famille                             |
| `sub_family_code` | Filtrer par sous-famille                        |
| `has_supplier`    | `true` : articles avec au moins un fournisseur  |
| `sort_by`         | `name`, `ref`, `family_code`, `sub_family_code` |

---

## 8. Templates de pièces

Les templates définissent la structure technique des pièces d'une sous-famille. Ils sont versionnés pour permettre l'évolution sans casser les articles existants.

### Structure

**Table :** `part_template`

| Champ       | Type    | Description                                      |
| ----------- | ------- | ------------------------------------------------ |
| `id`        | UUID    | Identifiant                                      |
| `code`      | string  | Code unique (ex: `VIS_STANDARD`)                 |
| `pattern`   | string  | Patron de génération (ex: `{DIAM}x{LONG}-{MAT}`) |
| `version`   | int     | Version du template                              |
| `is_active` | boolean | Actif ou archivé                                 |

**Table :** `part_template_field`

| Champ         | Type    | Description                                |
| ------------- | ------- | ------------------------------------------ |
| `key`         | string  | Clé du champ (ex: `DIAM`)                  |
| `label`       | string  | Libellé affiché                            |
| `field_type`  | enum    | `text` \| `number` \| `enum`               |
| `required`    | boolean | Champ obligatoire                          |
| `sort_order`  | int     | Ordre d'affichage                          |
| `unit`        | string  | Unité (mm, kg, etc.)                       |
| `enum_values` | array   | Valeurs possibles (si `field_type = enum`) |

### Validation des caractéristiques

| `field_type` | Type de `value` attendu                |
| ------------ | -------------------------------------- |
| `number`     | Nombre (float)                         |
| `text`       | Chaîne de caractères                   |
| `enum`       | Une valeur présente dans `enum_values` |

### Endpoints

| Méthode | URL                           | Description                                                |
| ------- | ----------------------------- | ---------------------------------------------------------- |
| `GET`   | `/part-templates`             | Liste tous les templates actifs avec leurs champs          |
| `GET`   | `/part-templates/{id}`        | Détail d'un template (version spécifique via `?version=2`) |
| `GET`   | `/part-templates/code/{code}` | Toutes les versions d'un template par code                 |
| `POST`  | `/part-templates`             | Création d'un template                                     |
| `PUT`   | `/part-templates/{id}`        | Mise à jour (crée une nouvelle version)                    |

### Exemple de template

```json
{
  "id": "uuid",
  "code": "VIS_STANDARD",
  "version": 2,
  "label": "Vis standard",
  "pattern": "{DIAM}x{LONG}-{MAT}-{TETE}",
  "is_active": true,
  "fields": [
    {
      "key": "DIAM",
      "label": "Diamètre",
      "field_type": "number",
      "unit": "mm",
      "required": true
    },
    {
      "key": "LONG",
      "label": "Longueur",
      "field_type": "number",
      "unit": "mm",
      "required": true
    },
    {
      "key": "MAT",
      "label": "Matériau",
      "field_type": "enum",
      "required": true,
      "enum_values": [
        { "value": "INOX", "label": "Inox A2" },
        { "value": "ACIER", "label": "Acier zingué" }
      ]
    }
  ]
}
```

---

## 9. Fournisseurs & Références pièces

### Fournisseurs

**Table :** `supplier`

| Champ          | Type    | Description                      |
| -------------- | ------- | -------------------------------- |
| `id`           | UUID    | Identifiant                      |
| `name`         | string  | **Requis** (min 2 chars, unique) |
| `code`         | string  | Code court (ex: `PS`)            |
| `contact_name` | string  | Nom du contact                   |
| `email`        | string  | Email de commande                |
| `phone`        | string  | Téléphone                        |
| `address`      | string  | Adresse                          |
| `is_active`    | boolean | Actif/inactif                    |

**Endpoints :**

| Méthode  | URL                      | Description                                      |
| -------- | ------------------------ | ------------------------------------------------ |
| `GET`    | `/suppliers`             | Liste (filtre `is_active`, `search`)             |
| `GET`    | `/suppliers/{id}`        | Détail complet                                   |
| `GET`    | `/suppliers/code/{code}` | Recherche par code                               |
| `POST`   | `/suppliers`             | Création                                         |
| `PUT`    | `/suppliers/{id}`        | Mise à jour                                      |
| `DELETE` | `/suppliers/{id}`        | Suppression (bloquée si des références existent) |

**Règles de suppression :** Un fournisseur ne peut être supprimé que si aucune `stock_item_supplier` ne le référence.

### Références fournisseurs (StockItemSupplier)

Table de liaison entre articles stock et fournisseurs. Un article peut avoir N fournisseurs, un fournisseur peut référencer N articles.

**Table :** `stock_item_supplier`

| Champ                  | Type    | Obligatoire | Description                                 |
| ---------------------- | ------- | ----------- | ------------------------------------------- |
| `id`                   | UUID    | auto        |                                             |
| `stock_item_id`        | UUID FK | **Oui**     | Article en stock                            |
| `supplier_id`          | UUID FK | **Oui**     | Fournisseur                                 |
| `supplier_ref`         | string  | **Oui**     | Référence chez ce fournisseur (min 2 chars) |
| `unit_price`           | decimal | Non         | Prix unitaire                               |
| `min_order_quantity`   | int     | Non         | Quantité minimale de commande               |
| `delivery_time_days`   | int     | Non         | Délai de livraison (jours)                  |
| `is_preferred`         | boolean | Non         | Fournisseur préféré pour cet article        |
| `manufacturer_item_id` | uuid    | Non         | Référence fabricant via ce canal            |

### Règle du fournisseur préféré

- Un seul fournisseur peut être `is_preferred = true` par article.
- Quand `is_preferred = true` est positionné sur une référence, toutes les autres références du même article passent automatiquement à `false`.
- Raccourci dédié : `POST /stock-item-suppliers/{id}/set-preferred`

**Impact sur le dispatch :**

| Situation                    | Comportement du dispatch                                |
| ---------------------------- | ------------------------------------------------------- |
| 1 fournisseur `is_preferred` | Dispatch uniquement vers lui (commande directe)         |
| Aucun `is_preferred`         | Dispatch vers tous les fournisseurs liés (consultation) |
| Aucun fournisseur référencé  | Erreur — demande non dispatchée                         |

### Endpoints

| Méthode  | URL                                        | Description                                               |
| -------- | ------------------------------------------ | --------------------------------------------------------- |
| `GET`    | `/stock-item-suppliers`                    | Liste avec filtres                                        |
| `GET`    | `/stock-item-suppliers/{id}`               | Détail                                                    |
| `GET`    | `/stock-item-suppliers/stock-item/{id}`    | Tous les fournisseurs d'un article                        |
| `GET`    | `/stock-item-suppliers/supplier/{id}`      | Tous les articles d'un fournisseur                        |
| `POST`   | `/stock-item-suppliers`                    | Création                                                  |
| `PUT`    | `/stock-item-suppliers/{id}`               | Mise à jour (`stock_item_id` et `supplier_id` immutables) |
| `POST`   | `/stock-item-suppliers/{id}/set-preferred` | Marquer comme préféré                                     |
| `DELETE` | `/stock-item-suppliers/{id}`               | Suppression (bloquée si `is_preferred` et alternatives)   |

**Contrainte d'unicité :** La combinaison (`stock_item_id`, `supplier_id`, `supplier_ref`) doit être unique.

### Vue article avec fournisseurs

`GET /stock-items/{id}` retourne les fournisseurs triés `is_preferred` DESC :

```json
{
  "suppliers": [
    {
      "id": "uuid",
      "supplier_name": "PONS & SABOT",
      "supplier_ref": "P1115070",
      "unit_price": 12.5,
      "min_order_quantity": 5,
      "delivery_time_days": 3,
      "is_preferred": true
    },
    {
      "id": "uuid",
      "supplier_name": "ACME Industrie",
      "supplier_ref": "ACM-6205",
      "unit_price": 14.0,
      "delivery_time_days": 7,
      "is_preferred": false
    }
  ]
}
```

---

## 10. Demandes d'achat — Cycle de vie complet

### Structure de données

**Table :** `purchase_request`

| Champ                | Type     | Défaut   | Description                                |
| -------------------- | -------- | -------- | ------------------------------------------ |
| `id`                 | UUID     | auto     |                                            |
| `item_label`         | string   | —        | **Requis** — Libellé de la pièce           |
| `quantity`           | int      | —        | **Requis** — Quantité (> 0)                |
| `stock_item_id`      | UUID FK  | null     | Article du catalogue (null = non qualifié) |
| `intervention_id`    | UUID FK  | null     | Intervention liée                          |
| `unit`               | string   | null     | Unité                                      |
| `urgency`            | string   | `normal` | `normal`, `high`, `critical`               |
| `urgent`             | boolean  | `false`  | Flag urgence booléen                       |
| `requester_name`     | string   | null     | Nom du demandeur                           |
| `approver_name`      | string   | null     | Nom de l'approbateur                       |
| `approved_at`        | datetime | null     | Date d'approbation                         |
| `reason`             | text     | null     | Motif                                      |
| `notes`              | text     | null     | Notes complémentaires                      |
| `workshop`           | string   | null     | Atelier                                    |
| `quantity_requested` | int      | null     | Quantité originale                         |
| `quantity_approved`  | int      | null     | Quantité approuvée                         |

> **Note :** Le champ `status` en base est un artefact legacy. Depuis v1.2.0, le statut réel est le `derived_status` calculé dynamiquement.

### Statut dérivé (calculé, jamais stocké)

Le `derived_status` est recalculé à chaque lecture à partir de l'état des données. L'algorithme est **déterministe et ordonné** :

```
ENTRÉES :
  stock_item_id       → UUID ou null
  supplier_refs_count → nombre de références fournisseurs pour cet article
  has_order_lines     → au moins 1 ligne de commande liée
  quotes_count        → lignes avec quote_received = true
  selected_count      → lignes avec is_selected = true
  total_allocated     → SUM(quantity) depuis supplier_order_line_purchase_request
  total_received      → SUM(quantity_received) depuis les lignes

ALGORITHME (ordre impératif) :
  1. SI stock_item_id IS NULL               → "TO_QUALIFY"
  2. SI supplier_refs_count == 0            → "NO_SUPPLIER_REF"
  3. SI NOT has_order_lines                 → "PENDING_DISPATCH"
  4. SI total_received >= total_allocated
     ET total_allocated > 0                → "RECEIVED"
  5. SI total_received > 0                 → "PARTIAL"
  6. SI selected_count > 0                 → "ORDERED"
  7. SI quotes_count > 0                   → "QUOTED"
  8. SINON                                 → "OPEN"
```

| Code               | Couleur   | Label              | Signification                                  |
| ------------------ | --------- | ------------------ | ---------------------------------------------- |
| `TO_QUALIFY`       | `#F59E0B` | À qualifier        | Pas d'article catalogue associé                |
| `NO_SUPPLIER_REF`  | `#F97316` | Sans fournisseur   | Article ok, 0 référence fournisseur            |
| `PENDING_DISPATCH` | `#A855F7` | À dispatcher       | Prête à être envoyée en commande               |
| `OPEN`             | `#6B7280` | En attente         | Dans une commande ouverte, en attente de devis |
| `QUOTED`           | `#FFA500` | Devis reçu         | Au moins 1 devis reçu                          |
| `ORDERED`          | `#3B82F6` | Commandé           | Au moins 1 ligne sélectionnée (devis retenu)   |
| `PARTIAL`          | `#8B5CF6` | Partiellement reçu | Livraison partielle                            |
| `RECEIVED`         | `#10B981` | Reçu               | Livraison complète                             |
| `REJECTED`         | `#EF4444` | Refusé             | Marqué refusé                                  |

### Cycle de vie d'une demande d'achat

```
   CRÉATION (item_label + quantity)
             │
             ▼
       [TO_QUALIFY]  ← stock_item_id est null
             │
             │ PUT /purchase-requests/{id}
             │ (ajout de stock_item_id)
             ▼
   [NO_SUPPLIER_REF]  ← article connu, aucun fournisseur
             │
             │ POST /stock-item-suppliers
             │ (au moins 1 référence ajoutée)
             ▼
   [PENDING_DISPATCH]  ← prête à être commandée
             │
             │ POST /purchase-requests/dispatch
             ▼
        ┌────┴────────────────────────────────────┐
        │  Fournisseur préféré défini              │  Aucun fournisseur préféré
        │  (mode "direct")                         │  (mode "consultation")
        ▼                                          ▼
  1 supplier_order_line                  N supplier_order_lines
  (1 fournisseur)                        (1 par fournisseur)
        │                                          │
        └────────────────┬────────────────────────┘
                         ▼
                      [OPEN]  ← dans une commande, en attente de devis
                         │
                         │ PUT /supplier-order-lines/{id}
                         │ (quote_received = true)
                         ▼
                      [QUOTED]  ← devis reçu
                         │
                         │ PUT /supplier-order-lines/{id}
                         │ (is_selected = true sur la meilleure offre)
                         ▼
                     [ORDERED]  ← commande passée
                         │
                         │ PUT /supplier-order-lines/{id}
                         │ (quantity_received > 0)
                         ▼
                 ┌────────┴──────────┐
                 │  Livraison        │  Livraison
                 │  partielle        │  complète
                 ▼                   ▼
            [PARTIAL]           [RECEIVED]
```

### Dispatch automatique (`POST /purchase-requests/dispatch`)

Transforme toutes les demandes `PENDING_DISPATCH` en lignes de commande fournisseur.

**Invariant :** Une demande déjà liée à une `supplier_order_line` n'est jamais re-dispatchée.

**Réponse :**

```json
{
  "dispatched_count": 5,
  "created_orders": 2,
  "errors": [
    { "purchase_request_id": "uuid", "error": "Aucun fournisseur référencé" }
  ],
  "details": [
    {
      "purchase_request_id": "uuid",
      "mode": "direct",
      "supplier_order_id": "uuid",
      "supplier_name": "PONS & SABOT"
    },
    {
      "purchase_request_id": "uuid",
      "mode": "consultation",
      "supplier_orders": [
        { "supplier_order_id": "uuid", "supplier_name": "PONS & SABOT" },
        { "supplier_order_id": "uuid", "supplier_name": "ACME Industrie" }
      ]
    }
  ]
}
```

### Endpoints

| Méthode  | URL                                              | Description                                     |
| -------- | ------------------------------------------------ | ----------------------------------------------- |
| `GET`    | `/purchase-requests/list`                        | Liste légère (v1.2.0) — payload ~95% plus léger |
| `GET`    | `/purchase-requests/detail/{id}`                 | Détail complet (v1.2.0)                         |
| `GET`    | `/purchase-requests/stats`                       | Statistiques agrégées                           |
| `GET`    | `/purchase-requests`                             | Liste complète LEGACY                           |
| `GET`    | `/purchase-requests/{id}`                        | Détail LEGACY                                   |
| `GET`    | `/purchase-requests/intervention/{id}`           | Demandes d'une intervention                     |
| `GET`    | `/purchase-requests/intervention/{id}/optimized` | Idem avec `?view=list\|full`                    |
| `POST`   | `/purchase-requests`                             | Création                                        |
| `POST`   | `/purchase-requests/dispatch`                    | Dispatch automatique                            |
| `PUT`    | `/purchase-requests/{id}`                        | Mise à jour (le `status` n'est plus modifiable) |
| `DELETE` | `/purchase-requests/{id}`                        | Suppression                                     |

### Vue liste légère (PurchaseRequestListItem)

```json
{
  "id": "uuid",
  "item_label": "Roulement SKF 6205",
  "quantity": 2,
  "unit": "pcs",
  "derived_status": {
    "code": "PENDING_DISPATCH",
    "label": "À dispatcher",
    "color": "#A855F7"
  },
  "stock_item_id": "uuid",
  "stock_item_ref": "OUT-ROUL-SKF-6205",
  "stock_item_name": "Roulement SKF 6205",
  "intervention_code": "CN001-REA-20260113-QC",
  "requester_name": "Jean Dupont",
  "urgency": "high",
  "urgent": true,
  "quotes_count": 0,
  "selected_count": 0,
  "suppliers_count": 2,
  "created_at": "2026-01-13T10:00:00",
  "updated_at": "2026-01-13T10:00:00"
}
```

### Statistiques des demandes d'achat

```
GET /purchase-requests/stats?start_date=2025-11-15&end_date=2026-02-15
```

```json
{
  "period": { "start_date": "2025-11-15", "end_date": "2026-02-15" },
  "totals": { "total_requests": 45, "urgent_count": 8 },
  "by_status": [
    {
      "status": "PENDING_DISPATCH",
      "count": 12,
      "label": "À dispatcher",
      "color": "#A855F7"
    }
  ],
  "by_urgency": [{ "urgency": "normal", "count": 30 }],
  "top_items": [
    {
      "item_label": "Roulement SKF 6205",
      "request_count": 5,
      "total_quantity": 12
    }
  ]
}
```

---

## 11. Commandes fournisseurs

### Structure de données

**Table :** `supplier_order`

| Champ                    | Type     | Description                                                  |
| ------------------------ | -------- | ------------------------------------------------------------ |
| `id`                     | UUID     | Identifiant                                                  |
| `order_number`           | string   | **Auto-généré par trigger PostgreSQL** (ex: `CMD-2026-0042`) |
| `supplier_id`            | UUID FK  | Fournisseur                                                  |
| `status`                 | string   | Statut courant                                               |
| `total_amount`           | decimal  | **Calculé par trigger** depuis les lignes                    |
| `ordered_at`             | datetime | Date de commande                                             |
| `expected_delivery_date` | date     | Date de livraison prévue                                     |
| `received_at`            | datetime | Date de réception complète                                   |
| `notes`                  | text     | Notes                                                        |
| `currency`               | string   | Devise                                                       |

**Important :** `order_number` et `total_amount` sont gérés par des triggers PostgreSQL. Ils ne sont pas modifiables manuellement.

### Statuts des commandes (ENUM)

| Statut     | Description                      |
| ---------- | -------------------------------- |
| `OPEN`     | Ouverte, en cours de remplissage |
| `SENT`     | Envoyée au fournisseur           |
| `ACK`      | Accusée de réception             |
| `QUOTED`   | Devisée                          |
| `ORDERED`  | Commandée                        |
| `PARTIAL`  | Livraison partielle              |
| `RECEIVED` | Reçue complètement               |
| `REJECTED` | Refusée                          |

### Indicateurs d'âge (calculés dynamiquement)

```
age_days = (NOW() - created_at).days

age_color :
  SI age_days >= 14 → "red"
  SI age_days >= 7  → "orange"
  SINON             → "gray"

is_blocking :
  SI status IN ("OPEN", "SENT", "ACK") AND age_days >= 7 → true
```

**Justification :** Une commande ouverte sans avancement depuis 7 jours est considérée bloquante.

### Lignes de commande

**Table :** `supplier_order_line`

| Champ                   | Type     | Description                                          |
| ----------------------- | -------- | ---------------------------------------------------- |
| `id`                    | UUID     | Identifiant                                          |
| `supplier_order_id`     | UUID FK  | Commande parente                                     |
| `stock_item_id`         | UUID FK  | Article commandé                                     |
| `quantity`              | int      | Quantité commandée                                   |
| `unit_price`            | decimal  | Prix unitaire                                        |
| `total_price`           | decimal  | **Calculé par trigger** (`quantity × unit_price`)    |
| `quantity_received`     | int      | Quantité reçue                                       |
| `is_selected`           | boolean  | Devis retenu                                         |
| `quote_price`           | decimal  | Prix du devis                                        |
| `quote_received`        | boolean  | Devis reçu                                           |
| `quote_received_at`     | datetime | Date réception devis                                 |
| `lead_time_days`        | int      | Délai fournisseur                                    |
| `manufacturer`          | string   | Fabricant                                            |
| `manufacturer_ref`      | string   | Référence fabricant                                  |
| `supplier_ref_snapshot` | string   | Snapshot de la réf fournisseur au moment du dispatch |
| `rejected_reason`       | string   | Raison de rejet                                      |

**Règle d'exclusivité sur `is_selected` :** Quand une ligne est sélectionnée (`is_selected = true`), toutes les autres lignes liées aux mêmes demandes d'achat sont automatiquement désélectionnées.

### Liaison ligne ↔ demandes d'achat (M2M)

**Table :** `supplier_order_line_purchase_request`

| Champ                    | Description                      |
| ------------------------ | -------------------------------- |
| `supplier_order_line_id` | Ligne de commande                |
| `purchase_request_id`    | Demande d'achat                  |
| `quantity`               | Quantité allouée sur cette ligne |

Une demande peut être liée à plusieurs lignes (consultation multi-fournisseurs). Une ligne peut couvrir plusieurs demandes.

### Endpoints commandes

| Méthode  | URL                                      | Description                     |
| -------- | ---------------------------------------- | ------------------------------- |
| `GET`    | `/supplier-orders`                       | Liste avec filtres              |
| `GET`    | `/supplier-orders/{id}`                  | Détail avec lignes              |
| `GET`    | `/supplier-orders/number/{order_number}` | Recherche par numéro            |
| `POST`   | `/supplier-orders`                       | Création (`supplier_id` requis) |
| `PUT`    | `/supplier-orders/{id}`                  | Mise à jour                     |
| `DELETE` | `/supplier-orders/{id}`                  | Suppression (cascade lignes)    |
| `POST`   | `/supplier-orders/{id}/export/csv`       | Export CSV                      |
| `POST`   | `/supplier-orders/{id}/export/email`     | Génère le contenu email         |

### Endpoints lignes

| Méthode  | URL                                                    | Description                                    |
| -------- | ------------------------------------------------------ | ---------------------------------------------- |
| `GET`    | `/supplier-order-lines`                                | Liste avec filtres                             |
| `GET`    | `/supplier-order-lines/{id}`                           | Détail avec article + demandes                 |
| `GET`    | `/supplier-order-lines/order/{id}`                     | Toutes les lignes d'une commande               |
| `POST`   | `/supplier-order-lines`                                | Création avec liaison M2M optionnelle          |
| `PUT`    | `/supplier-order-lines/{id}`                           | Mise à jour (replace des liens M2M si fournis) |
| `DELETE` | `/supplier-order-lines/{id}`                           | Suppression (cascade M2M)                      |
| `POST`   | `/supplier-order-lines/{id}/purchase-requests`         | Lie une demande (upsert quantité)              |
| `DELETE` | `/supplier-order-lines/{id}/purchase-requests/{pr_id}` | Délie une demande                              |

### Export CSV

`POST /supplier-orders/{id}/export/csv`

- Content-Type: `text/csv`
- Colonnes : Article, Référence, Spécification, Fabricant, Réf. Fabricant, Quantité, Unité, Prix unitaire, Prix total, Demandes liées

### Export email

`POST /supplier-orders/{id}/export/email`

```json
{
  "subject": "Commande CMD-2026-0042 - PONS & SABOT",
  "body_text": "Bonjour,\n\nVeuillez trouver ci-joint notre commande...",
  "body_html": "<html>...</html>",
  "supplier_email": "commandes@pons.fr"
}
```

> Templates modifiables dans `config/export_templates.py`.

---

## 12. Statistiques & KPIs

### Service Status (`GET /stats/service-status`)

Indicateurs de charge et de santé du service sur une période (défaut : 3 derniers mois).

```
GET /stats/service-status?start_date=2025-11-15&end_date=2026-02-15
```

| Bloc               | Description                                             |
| ------------------ | ------------------------------------------------------- |
| `capacity`         | Heures totales, capacité, taux de charge                |
| `breakdown`        | Répartition prod / dépannage / pilotage / fragmentation |
| `fragmentation`    | Ratio actions courtes, top causes                       |
| `pilotage`         | Taux heures de pilotage                                 |
| `site_consumption` | Consommation par site / atelier                         |

**Exemple de réponse :**

```json
{
  "period": {
    "start_date": "2025-11-15",
    "end_date": "2026-02-15",
    "days": 92
  },
  "capacity": {
    "total_hours": 450.5,
    "capacity_hours": 600,
    "charge_percent": 75.1,
    "status": { "color": "orange", "text": "Charge élevée" }
  },
  "fragmentation": {
    "action_count": 340,
    "short_action_count": 85,
    "short_action_percent": 25.0,
    "frag_percent": 11.1,
    "status": { "color": "green", "text": "OK" }
  }
}
```

### Charge technique (`GET /stats/charge-technique`) [BETA]

Analyse du dépannage évitable par classe d'équipement.

| Taux   | Couleur | Interprétation            |
| ------ | ------- | ------------------------- |
| < 20%  | Vert    | Faible levier             |
| 20-40% | Orange  | Levier de standardisation |
| > 40%  | Rouge   | Problème systémique       |

**Définition "dépannage évitable" :** Action DEP avec `complexity_factor IS NOT NULL` OU action répétée ≥ 3 fois (même sous-catégorie + même classe d'équipement sur la période).

### Anomalies de saisie (`GET /stats/anomalies-saisie`) [BETA]

Détection automatique de 6 types d'anomalies :

| Type                    | Sévérité    | Règle                                              |
| ----------------------- | ----------- | -------------------------------------------------- |
| `too_repetitive`        | high/medium | Même sous-catégorie + même machine > 3 fois/mois   |
| `too_fragmented`        | high/medium | Actions courtes (< 1h) ≥ 5 fois                    |
| `too_long_for_category` | high/medium | > 4h sur catégories rapides                        |
| `bad_classification`    | high/medium | Actions BAT_NET avec mots-clés techniques suspects |
| `back_to_back`          | high/medium | Même tech + même intervention, < 24h d'écart       |
| `low_value_high_load`   | high/medium | > 30h cumulées sur catégories faible valeur        |

---

## 13. Exports

### PDF d'intervention

```
GET /exports/interventions/{id}/pdf
```

**Auth :** JWT Bearer obligatoire.

**Réponse :** `application/pdf` avec filename `{code_intervention}.pdf`

**Contenu :**

- En-tête : logo, titre, code intervention, QR code
- Informations intervention : type, priorité, statut, dates, technicien, équipement
- Actions réalisées (technicien, temps, catégorie, complexité)
- Historique des changements de statut
- Demandes d'achat liées (qté, réf. interne, désignation, fournisseur, réf. fournisseur, fabricant, réf. fabricant, urgence)
- Pied de page : version API, code intervention, pagination, date

### QR code d'intervention

```
GET /exports/interventions/{id}/qrcode
```

**Auth :** Public (conçu pour impression physique).

**Réponse :** `image/png` inline, cache 1h.

**Contenu du QR :** `{EXPORT_QR_BASE_URL}/{intervention_id}` (URL vers le frontend).

---

## 14. Référentiels

### Catégories d'actions

```
GET /action-categories               → Liste avec sous-catégories imbriquées
GET /action-categories/{id}          → Détail d'une catégorie
GET /action-categories/{id}/subcategories → Sous-catégories d'une catégorie
GET /action-subcategories            → Liste toutes les sous-catégories (avec catégorie parente)
GET /action-subcategories/{id}       → Détail
```

**Structure :**

```json
{
  "id": 3,
  "name": "Dépannage",
  "code": "DEP",
  "color": "#e53e3e",
  "subcategories": [
    {
      "id": 30,
      "category_id": 3,
      "name": "Remplacement pièce",
      "code": "DEP_REM"
    }
  ]
}
```

### Classes d'équipements

```
GET /equipement-class      → Liste toutes les classes
GET /equipement-class/{id} → Détail
POST /equipement-class     → Création (code + label requis)
PUT /equipement-class/{id} → Mise à jour
DELETE /equipement-class/{id} → Suppression
```

### Facteurs de complexité

```
GET /complexity-factors        → Liste triée par catégorie puis code
GET /complexity-factors/{code} → Détail d'un facteur
```

Exemples :

| Code  | Label                        | Catégorie   |
| ----- | ---------------------------- | ----------- |
| `PCE` | Pièce manquante ou inadaptée | Logistique  |
| `ACC` | Accès difficile              | Technique   |
| `DOC` | Documentation manquante      | Information |

---

## 15. Conventions transversales

### Pagination

Format standard uniforme sur tous les endpoints paginés :

```json
{
  "items": [ ... ],
  "pagination": {
    "total": 150,
    "page": 2,
    "page_size": 50,
    "total_pages": 3,
    "offset": 50,
    "count": 50
  }
}
```

- Limite max : **1000 items** par requête
- Limite par défaut : **50-100** selon l'endpoint

### Tri

Syntaxe unifiée via le paramètre `sort` :

| Syntaxe                   | Résultat  |
| ------------------------- | --------- |
| `field`                   | Tri ASC   |
| `-field`                  | Tri DESC  |
| `priority,-reported_date` | Multi-tri |

### Sanitisation des entrées

Toute chaîne textuelle passe par :

1. Suppression de tout HTML (`strip_html`)
2. Trim des espaces
3. Chaîne vide → `null` (champ optionnel) ou erreur 400 (champ requis)

### UUIDs

Les UUIDs sont générés par l'application (uuid4), **pas** par la base de données. Exceptions gérées par trigger PostgreSQL :

- `supplier_order.order_number`
- `stock_item.ref`

### Types numériques

Les décimaux PostgreSQL (`NUMERIC`/`DECIMAL`) sont sérialisés en `float` dans les réponses JSON.

### Filtres textuels

Recherche insensible à la casse implémentée en `ILIKE %terme%` sur :

- Équipements : `code`, `name`
- Articles stock : `name`, `ref`
- Fournisseurs : `name`, `code`, `contact_name`
- Familles stock : `label`

### Codes HTTP

| Code  | Signification                               |
| ----- | ------------------------------------------- |
| `200` | Succès                                      |
| `201` | Créé avec succès                            |
| `204` | Suppression réussie (pas de contenu)        |
| `400` | Erreur de validation ou règle métier violée |
| `401` | Non authentifié                             |
| `404` | Ressource introuvable                       |
| `502` | Service Directus indisponible               |

---

_Document généré le 2026-03-02 — Source : docs/endpoints/_ — _web.tunnel-backend v2.6.0_
