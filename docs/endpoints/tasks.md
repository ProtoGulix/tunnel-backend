# Endpoint `/tasks/workspace` — Espace unifié de gestion des tâches

**Version API** : 2.5.0+  
**Authentification** : ✅ Requise (JWT)  
**Dernière mise à jour** : 2026-04-26

---

## Vue d'ensemble

Endpoint **unique et optimisé** pour la page Tasks du frontend. Consolidate toutes les données nécessaires pour afficher :

- Liste complète des tâches avec filtres
- Compteurs de statuts (todo, in_progress, done, skipped)
- Options de filtrage (utilisateurs, interventions)
- Tâches enrichies avec actions liées (optionnel)

**Objectif** : Minimiser les appels réseau côté frontend (1 appel = tous les détails precharges).

---

## Requête

### GET `/tasks/workspace`

```http
GET /tasks/workspace?q=search&status=todo,in_progress&origin=tech&assignee_id=uuid&include_counters=true&include_actions=false&limit=50
Authorization: Bearer <JWT>
```

### Paramètres

| Paramètre          | Type                 | Défaut | Description                                                                              |
| ------------------ | -------------------- | ------ | ---------------------------------------------------------------------------------------- |
| `q`                | string               | null   | Recherche full-text sur `label`, `intervention.title`, `intervention.code`               |
| `status`           | string (CSV)         | null   | Filtres statut (valeurs : `todo`, `in_progress`, `done`, `skipped`)                      |
| `origin`           | string (CSV)         | null   | Filtres origine (valeurs : `plan`, `resp`, `tech`)                                       |
| `assignee_id`      | uuid \| "unassigned" | null   | UUID d'utilisateur ou `"unassigned"` pour tâches non assignées                           |
| `grouping`         | string               | null   | Groupage optionnel pour UI (valeurs : `intervention`, `machine`, `status`, `technician`) |
| `cursor`           | string               | null   | Curseur pagination (UUID de tâche)                                                       |
| `limit`            | integer (1-200)      | 50     | Nombre de tâches par page                                                                |
| `include_closed`   | boolean              | false  | Inclure tâches avec statut `done` ou `skipped`                                           |
| `include_actions`  | boolean              | false  | Charger les actions liées à chaque tâche                                                 |
| `include_options`  | boolean              | false  | Inclure listes de filtrage (utilisateurs, interventions)                                 |
| `include_counters` | boolean              | false  | Inclure compteurs globaux (total, todo, in_progress, etc.)                               |

### Exemples

**Page accueil minimale** (chargement initial) :

```http
GET /tasks/workspace?limit=50&include_counters=true&include_options=true
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
GET /tasks/workspace?cursor=0ceccde1-17c2-4fb0-a1cc-6144b10752f6&limit=50
```

---

## Réponse

### HTTP 200 OK

```json
{
  "tasks": [
    {
      "id": "uuid",
      "label": "string",
      "status": "todo|in_progress|done|skipped",
      "origin": "plan|resp|tech",
      "optional": false,
      "due_date": "2026-04-30",
      "skip_reason": null,
      "time_spent_total": 1.5,
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
      "intervention": {
        "id": "uuid",
        "code": "INT-2026-001",
        "title": "Maintenance curative moteur",
        "status": "ouvert"
      },
      "equipement": {
        "id": "uuid",
        "name": "Compresseur C-450",
        "code": "EQUIP-0012"
      },
      "actions": [
        {
          "id": "uuid",
          "created_at": "2026-04-26T10:15:00Z",
          "description": "Remplacement joints d'étanchéité",
          "time_spent": 2.5,
          "tech": {
            "id": "uuid",
            "initials": "MD",
            "first_name": "Marc",
            "last_name": "DUPUIS"
          }
        }
      ]
    }
  ],
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
  "pagination": {
    "next_cursor": "uuid",
    "has_more": true
  },
  "meta": {
    "generated_at": "2026-04-26T12:00:00Z",
    "etag": "abc123def456"
  },
  "errors": null
}
```

### Schéma complet

#### TaskDetail

| Champ              | Type            | Description                                                   |
| ------------------ | --------------- | ------------------------------------------------------------- |
| `id`               | uuid            | Identifiant tâche                                             |
| `label`            | string          | Libellé/titre                                                 |
| `status`           | enum            | `todo`, `in_progress`, `done`, `skipped`                      |
| `origin`           | enum            | `plan` (préventif), `resp` (responsable), `tech` (technicien) |
| `optional`         | boolean         | Optionnel ou obligatoire                                      |
| `due_date`         | date            | Échéance optionnelle                                          |
| `skip_reason`      | string\|null    | Raison si skippée                                             |
| `time_spent_total` | float           | Temps accumulé toutes actions                                 |
| `created_at`       | timestamp       | Date création                                                 |
| `created_by`       | UserRef\|null   | Créateur                                                      |
| `assigned_to`      | UserRef\|null   | Assigné à                                                     |
| `intervention`     | InterventionRef | Intervention parent                                           |
| `equipement`       | EquipementRef   | Équipement lié                                                |
| `actions`          | ActionRef[]     | Actions liées (si `include_actions=true`)                     |

#### TasksCounter

| Champ                     | Type    | Description                 |
| ------------------------- | ------- | --------------------------- |
| `total`                   | integer | Total tâches                |
| `todo`                    | integer | Statut `todo`               |
| `in_progress`             | integer | Statut `in_progress`        |
| `done`                    | integer | Statut `done`               |
| `skipped`                 | integer | Statut `skipped`            |
| `backlog_unassigned_todo` | integer | Tâches `todo` non assignées |

#### UserRef

| Champ        | Type   | Description          |
| ------------ | ------ | -------------------- |
| `id`         | uuid   | UUID Directus        |
| `initials`   | string | Initiales (ex: "CC") |
| `first_name` | string | Prénom               |
| `last_name`  | string | Nom                  |

#### InterventionRef

| Champ    | Type   | Description                      |
| -------- | ------ | -------------------------------- |
| `id`     | uuid   | UUID intervention                |
| `code`   | string | Code unique (ex: "INT-2026-001") |
| `title`  | string | Titre                            |
| `status` | string | Statut actuel                    |

#### EquipementRef

| Champ  | Type   | Description             |
| ------ | ------ | ----------------------- |
| `id`   | uuid   | UUID équipement/machine |
| `name` | string | Nom                     |
| `code` | string | Code                    |

#### ActionRef (si `include_actions=true`)

| Champ         | Type          | Description            |
| ------------- | ------------- | ---------------------- |
| `id`          | uuid          | UUID action            |
| `created_at`  | timestamp     | Date création          |
| `description` | string        | Description action     |
| `time_spent`  | float         | Heures passées         |
| `tech`        | UserRef\|null | Technicien qui a saisi |

#### TasksPagination

| Champ         | Type         | Description                       |
| ------------- | ------------ | --------------------------------- |
| `next_cursor` | string\|null | UUID prochaine tâche (pagination) |
| `has_more`    | boolean      | S'il y a plus de résultats        |

#### TasksMetadata

| Champ          | Type      | Description                                        |
| -------------- | --------- | -------------------------------------------------- |
| `generated_at` | timestamp | Instant génération réponse                         |
| `etag`         | string    | Hash pour cache client (change si tâches changent) |

---

## Comportements

### Filtrage

- **`q`** : Recherche ILIKE (insensible à la casse) sur `label` + `intervention.title` + `intervention.code`
- **`status`** : Agrégation OR (ex: `status=todo,in_progress` = statut IN (todo, in_progress))
- **`origin`** : Agrégation OR
- **`assignee_id`** : Strictement égal ou NULL si "unassigned"
- **`include_closed`=false** : Exclut statuts `done` et `skipped` (par défaut)

### Pagination

- Curseur-based (pas offset)
- Clé : `(created_at DESC, id DESC)`
- `next_cursor` = ID de la dernière tâche retournée (si `has_more=true`)
- Limite max : 200 tâches/page

### Champs conditionnels

- **`include_actions=true`** → charge `intervention_action` et joint à tâches (JOIN LATERAL pour éviter N+1)
- **`include_options=true`** → exécute requêtes séparées pour listes utilisateurs/interventions (max 100 each)
- **`include_counters=true`** → FILTER agregates pour compteurs globaux

### Etag

- Généré depuis IDs tâches retournées
- Frontend peut stocker + vérifier avant prochain appel (simple cache validation)

---

## Errors

### 400 Bad Request

```json
{
  "detail": "Paramètre invalide",
  "errors": {
    "q": "max 500 caractères",
    "limit": "doit être entre 1 et 200"
  }
}
```

### 401 Unauthorized

```json
{
  "detail": "Token invalide ou expiré"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Erreur base de données",
  "request_id": "req-uuid"
}
```

---

## Performance

### Optimisations appliquées

1. **Batch queries** : Actions chargées en une requête GROUP BY
2. **Pagination curseur** : Évite OFFSET coûteux
3. **Conditional loading** : Options/actions/counters chargés uniquement si demandés
4. **Index DB** :
   - `intervention_task(status, created_at DESC, id DESC)`
   - `intervention_task(assigned_to)`
   - `intervention_task(origin)`

### Temps typique

- 50 tâches : ~150-300ms (réseau inclus)
- Avec actions liées : +100-200ms (LATERAL JOIN)
- Avec options/counters : +50-100ms (requêtes parallèles)

---

## Cas d'usage frontend

### 1. Chargement page accueil

```javascript
const resp = await fetch(
  "/tasks/workspace?include_counters=true&include_options=true&limit=50",
);
const { tasks, counters, options } = await resp.json();
// Afficher badges + première page + listes filtres
```

### 2. Filtre utilisateur

```javascript
const resp = await fetch(
  "/tasks/workspace?status=todo&assignee_id=user-uuid&limit=50",
);
const { tasks } = await resp.json();
// Afficher tâches assignées
```

### 3. Recherche avec actions

```javascript
const resp = await fetch(
  "/tasks/workspace?q=maintenance&include_actions=true&limit=20",
);
const { tasks } = await resp.json();
// Afficher tâches + historique actions
```

### 4. Pagination

```javascript
// Première page
const p1 = await fetch("/tasks/workspace?limit=50");
const { tasks: t1, pagination } = await p1.json();

// Page suivante
const p2 = await fetch(
  `/tasks/workspace?limit=50&cursor=${pagination.next_cursor}`,
);
const { tasks: t2 } = await p2.json();
```

---

## Changelog

| Date       | Version | Modification                                                   |
| ---------- | ------- | -------------------------------------------------------------- |
| 2026-04-26 | 2.5.0   | ✨ Endpoint créé, support filtres complets, pagination curseur |
