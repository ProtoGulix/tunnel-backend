# Endpoint `/tasks/workspace` — Espace unifié de gestion des tâches

**Version API** : 3.5.0+  
**Authentification** : ✅ Requise (JWT)  
**Dernière mise à jour** : 2026-05-10

---

## Vue d'ensemble

Endpoint **unique et optimisé** pour la page Tasks du frontend. Retourne la liste des **interventions avec leurs tâches agrégées**, avec pagination offset sur les interventions.

**Structure de réponse** : chaque `item` est une intervention contenant toutes ses tâches correspondant aux filtres actifs. Si plusieurs tâches d'une même intervention matchent le filtre, elles sont regroupées sous la même intervention.

**Objectif** : 1 appel = toutes les interventions de la page avec leurs tâches préchargées.

---

## Requête

### GET `/tasks/workspace`

```http
GET /tasks/workspace?q=search&status=todo,in_progress&origin=tech&assignee_id=uuid&include_counters=true&skip=0&limit=20
Authorization: Bearer <JWT>
```

### Paramètres

| Paramètre          | Type                 | Défaut | Description                                                                 |
| ------------------ | -------------------- | ------ | --------------------------------------------------------------------------- |
| `q`                | string               | null   | Recherche full-text sur `label`, `intervention.title`, `intervention.code`  |
| `status`           | string (CSV)         | null   | Filtres statut (valeurs : `todo`, `in_progress`, `done`, `skipped`)         |
| `origin`           | string (CSV)         | null   | Filtres origine (valeurs : `plan`, `resp`, `tech`)                          |
| `assignee_id`      | uuid \| "unassigned" | null   | UUID d'utilisateur ou `"unassigned"` pour tâches non assignées              |
| `skip`             | integer (≥0)         | 0      | Offset — nombre d'interventions à sauter                                    |
| `limit`            | integer (1-200)      | 20     | Nombre d'interventions par page                                             |
| `include_closed`   | boolean              | false  | Inclure tâches avec statut `done` ou `skipped`                              |
| `include_actions`  | boolean              | false  | Charger les actions liées à chaque tâche                                    |
| `include_options`  | boolean              | false  | Inclure listes de filtrage (utilisateurs, interventions)                    |
| `include_counters` | boolean              | false  | Inclure compteurs globaux (total, todo, in_progress, etc.)                  |

### Exemples

**Page accueil minimale** (chargement initial) :

```http
GET /tasks/workspace?limit=20&include_counters=true&include_options=true
```

**Filtre par statut** :

```http
GET /tasks/workspace?status=todo,in_progress&assignee_id=unassigned&limit=20
```

**Recherche avec actions** :

```http
GET /tasks/workspace?q=maintenance&include_actions=true&limit=10
```

**Pagination** :

```http
GET /tasks/workspace?skip=20&limit=20
GET /tasks/workspace?skip=40&limit=20
```

---

## Réponse

### HTTP 200 OK

```json
{
  "items": [
    {
      "id": "uuid-intervention",
      "code": "INT-2026-001",
      "title": "Maintenance curative moteur",
      "status": "ouvert",
      "equipement": {
        "id": "uuid",
        "name": "Compresseur C-450",
        "code": "EQUIP-0012"
      },
      "tasks": [
        {
          "id": "uuid-tache-1",
          "label": "Vérifier les joints",
          "status": "todo",
          "origin": "plan",
          "optional": false,
          "due_date": "2026-04-30",
          "skip_reason": null,
          "time_spent_total": 0.0,
          "created_at": "2026-04-26T08:57:22Z",
          "created_by": {
            "id": "uuid",
            "initials": "CC",
            "first_name": "Charles",
            "last_name": "CATHERINE"
          },
          "assigned_to": {
            "id": "uuid",
            "initials": "JD",
            "first_name": "Jean",
            "last_name": "DUPONT"
          },
          "actions": []
        },
        {
          "id": "uuid-tache-2",
          "label": "Remplacement courroie",
          "status": "in_progress",
          "origin": "tech",
          "optional": true,
          "due_date": null,
          "skip_reason": null,
          "time_spent_total": 1.5,
          "created_at": "2026-04-25T14:00:00Z",
          "created_by": null,
          "assigned_to": null,
          "actions": [
            {
              "id": "uuid",
              "created_at": "2026-04-26T10:15:00Z",
              "description": "Démontage effectué",
              "time_spent": 1.5,
              "tech": {
                "id": "uuid",
                "initials": "MD",
                "first_name": "Marc",
                "last_name": "DUPUIS"
              }
            }
          ]
        }
      ]
    }
  ],
  "pagination": {
    "total": 12,
    "page": 1,
    "page_size": 20,
    "total_pages": 1,
    "offset": 0,
    "count": 12
  },
  "counters": {
    "total": 29,
    "todo": 19,
    "in_progress": 2,
    "done": 8,
    "skipped": 0,
    "backlog_unassigned_todo": 19
  },
  "options": {
    "users": [
      {
        "id": "uuid",
        "initials": "CC",
        "first_name": "Charles",
        "last_name": "CATHERINE"
      }
    ],
    "interventions": [
      {
        "id": "uuid",
        "code": "INT-2026-001",
        "title": "Maintenance curative moteur",
        "status": "ouvert"
      }
    ]
  },
  "meta": {
    "generated_at": "2026-05-10T12:00:00Z",
    "etag": "abc123def456"
  },
  "errors": null
}
```

> `actions` est `[]` pour chaque tâche sauf si `include_actions=true`.
>
> `counters` et `options` sont `null` sauf si `include_counters=true` / `include_options=true`.

---

## Schéma complet

### InterventionGroup — item de premier niveau

| Champ        | Type              | Description                                         |
| ------------ | ----------------- | --------------------------------------------------- |
| `id`         | uuid              | UUID intervention                                   |
| `code`       | string            | Code unique (ex: "INT-2026-001")                    |
| `title`      | string            | Titre de l'intervention                             |
| `status`     | string            | Statut actuel                                       |
| `equipement` | EquipementRef     | Équipement lié (null si aucun)                      |
| `tasks`      | TaskDetail[]      | Tâches matchant les filtres, triées created_at DESC |

### TaskDetail

| Champ              | Type          | Description                                                   |
| ------------------ | ------------- | ------------------------------------------------------------- |
| `id`               | uuid          | Identifiant tâche                                             |
| `label`            | string        | Libellé/titre                                                 |
| `status`           | enum          | `todo`, `in_progress`, `done`, `skipped`                      |
| `origin`           | enum          | `plan` (préventif), `resp` (responsable), `tech` (technicien) |
| `optional`         | boolean       | Optionnel ou obligatoire                                      |
| `due_date`         | date          | Échéance optionnelle                                          |
| `skip_reason`      | string\|null  | Raison si skippée                                             |
| `time_spent_total` | float         | Temps accumulé toutes actions                                 |
| `created_at`       | timestamp     | Date création                                                 |
| `created_by`       | UserRef\|null | Créateur                                                      |
| `assigned_to`      | UserRef\|null | Assigné à                                                     |
| `actions`          | ActionRef[]   | Actions liées (si `include_actions=true`, sinon `[]`)         |

### TasksPagination

| Champ         | Type    | Description                                    |
| ------------- | ------- | ---------------------------------------------- |
| `total`       | integer | Nombre total d'interventions (tous filtres)    |
| `page`        | integer | Numéro de page actuelle (commence à 1)         |
| `page_size`   | integer | Nombre d'interventions par page                |
| `total_pages` | integer | Nombre total de pages                          |
| `offset`      | integer | Valeur `skip` appliquée                        |
| `count`       | integer | Nombre d'interventions retournées dans la page |

### TasksCounter

| Champ                     | Type    | Description                 |
| ------------------------- | ------- | --------------------------- |
| `total`                   | integer | Total tâches (global)       |
| `todo`                    | integer | Statut `todo`               |
| `in_progress`             | integer | Statut `in_progress`        |
| `done`                    | integer | Statut `done`               |
| `skipped`                 | integer | Statut `skipped`            |
| `backlog_unassigned_todo` | integer | Tâches `todo` non assignées |

### UserRef

| Champ        | Type   | Description          |
| ------------ | ------ | -------------------- |
| `id`         | uuid   | UUID Directus        |
| `initials`   | string | Initiales (ex: "CC") |
| `first_name` | string | Prénom               |
| `last_name`  | string | Nom                  |

### EquipementRef

| Champ  | Type   | Description             |
| ------ | ------ | ----------------------- |
| `id`   | uuid   | UUID équipement/machine |
| `name` | string | Nom                     |
| `code` | string | Code                    |

### ActionRef (si `include_actions=true`)

| Champ         | Type          | Description            |
| ------------- | ------------- | ---------------------- |
| `id`          | uuid          | UUID action            |
| `created_at`  | timestamp     | Date création          |
| `description` | string        | Description action     |
| `time_spent`  | float         | Heures passées         |
| `tech`        | UserRef\|null | Technicien qui a saisi |

---

## Comportements

### Agrégation par intervention

- La pagination porte sur les **interventions** (premier niveau), pas sur les tâches.
- Toutes les tâches d'une intervention qui matchent les filtres sont retournées dans le même bloc — il n'y a pas de limite sur le nombre de tâches par intervention.
- Une intervention n'apparaît dans la réponse que si au moins une de ses tâches correspond aux filtres actifs.

### Filtrage

- **`q`** : Recherche ILIKE sur `label` + `intervention.title` + `intervention.code` — s'applique au niveau tâche
- **`status`** : OR entre les valeurs (ex: `todo,in_progress` = tâches dans l'un ou l'autre statut)
- **`origin`** : OR entre les valeurs
- **`assignee_id`** : strictement égal ou NULL si `"unassigned"`
- **`include_closed=false`** (défaut) : exclut les tâches `done` et `skipped`

### Pagination

- Pagination **offset standard** (`skip` / `limit`) sur les interventions.
- `pagination.total` = nombre total d'interventions distinctes matchant les filtres.
- `pagination.page` = `(skip // limit) + 1`.

### Champs conditionnels

- **`include_actions=true`** → charge les `intervention_action` liées aux tâches de la page
- **`include_options=true`** → exécute des requêtes séparées pour listes utilisateurs/interventions (max 100 chacune)
- **`include_counters=true`** → compteurs globaux sur toutes les tâches (sans filtre de page)

### Etag

Généré depuis les IDs d'interventions et de tâches retournées. Permet au frontend de valider son cache local.

---

## Erreurs

### 400 Bad Request

```json
{
  "detail": "Paramètre invalide",
  "errors": {
    "limit": "doit être entre 1 et 200"
  }
}
```

### 401 Unauthorized

```json
{ "detail": "Token invalide ou expiré" }
```

### 500 Internal Server Error

```json
{ "detail": "Erreur base de données" }
```

---

## Performance

### Stratégie d'exécution

1. **Requête COUNT** : compte les interventions distinctes matchées (pour `pagination.total`)
2. **Requête interventions** : `DISTINCT` sur la page demandée (`LIMIT/OFFSET`)
3. **Requête tâches** : charge toutes les tâches des interventions de la page en une seule requête, avec `LATERAL` pour `time_spent_total`
4. **Requête actions** (optionnelle) : une seule requête `IN (task_ids)` si `include_actions=true`

### Index DB recommandés

- `intervention_task(status, intervention_id)`
- `intervention_task(assigned_to)`
- `intervention_task(origin)`
- `intervention_action(task_id)`

---

## Cas d'usage frontend

### 1. Chargement page accueil

```javascript
const resp = await fetch(
  "/tasks/workspace?include_counters=true&include_options=true&limit=20",
);
const { items, counters, options, pagination } = await resp.json();
// items = interventions avec leurs tâches
```

### 2. Page suivante

```javascript
const resp = await fetch(`/tasks/workspace?skip=20&limit=20`);
const { items, pagination } = await resp.json();
```

### 3. Filtre statut + assigné

```javascript
const resp = await fetch(
  "/tasks/workspace?status=todo&assignee_id=unassigned&limit=20",
);
const { items } = await resp.json();
// Chaque item.tasks ne contient que les tâches todo non assignées
```

### 4. Recherche avec actions

```javascript
const resp = await fetch(
  "/tasks/workspace?q=maintenance&include_actions=true&limit=10",
);
const { items } = await resp.json();
// items[0].tasks[0].actions = [...] si include_actions=true
```

---

## Changelog

| Date       | Version | Modification                                                                    |
| ---------- | ------- | ------------------------------------------------------------------------------- |
| 2026-04-26 | 2.5.0   | ✨ Endpoint créé, support filtres complets, pagination curseur                  |
| 2026-05-10 | 3.5.0   | ♻️ Pagination offset sur interventions, agrégation tâches par intervention       |
