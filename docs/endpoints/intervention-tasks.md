# Intervention Tasks

Tâches attachées à une intervention. Une tâche représente **quoi faire** — elle peut provenir d'un plan de maintenance préventive (`origin = plan`) ou être créée manuellement par un responsable (`resp`) ou un technicien (`tech`).

> Voir aussi : [Preventive Plans](preventive-plans.md) | [Preventive Occurrences](preventive-occurrences.md) | [Interventions](interventions.md) | [Intervention Actions](intervention-actions.md)

> **Audit log** : tout `POST`, `PATCH` et `DELETE` sur cette ressource exige un champ `reason_code` dans le body. Voir [Audit Log — règle commune](audit-log.md#règle-commune--reason_code-obligatoire).

---

## Modèle sémantique

| Niveau       | Question              | Unité                              |
| ------------ | --------------------- | ---------------------------------- |
| DI           | pourquoi              | motif                              |
| Intervention | sur quoi              | cadre + équipement                 |
| **Tâche**    | **quoi faire**        | intitulé, origine, assigné, statut |
| Action       | qui, combien, comment | temps + catégorie + note           |

---

## Cycle de vie d'une tâche

```
todo → in_progress → done
  ↘ skipped (avec motif)
```

| Statut        | Description                                                         |
| ------------- | ------------------------------------------------------------------- |
| `todo`        | Tâche créée, pas encore commencée                                   |
| `in_progress` | Au moins une action est liée à cette tâche (transition automatique) |
| `done`        | Tâche terminée                                                      |
| `skipped`     | Tâche ignorée (motif obligatoire)                                   |

> **Transition automatique** : à la création d'une action via `POST /intervention-actions` avec `task_id`, si la tâche est en `todo`, elle passe automatiquement en `in_progress`.

> **Clôture bloquée** : si l'intervention a des tâches non-optionnelles (`optional = false`) en `todo` ou `in_progress`, le passage au statut fermé retourne `400`.

---

## Structure de réponse — enveloppe `{ items, pagination, audit }`

`GET /intervention-tasks` et `GET /tasks/workspace` partagent la **même mécanique** et la **même structure de réponse** — source de vérité unique dans `InterventionTaskRepository.get_workspace()`.

```json
{
  "items": [
    {
      "id": "uuid-intervention",
      "code": "CN001-CUR-20260428-QC",
      "title": "Remplacement roulement principal",
      "status": "ouvert",
      "equipement": { "id": "uuid", "name": "Scie principale", "code": "EQ-001" },
      "tasks": [
        {
          "id": "uuid-task",
          "label": "Contrôle tension de la lame",
          "status": "todo",
          "origin": "plan",
          "optional": false,
          "due_date": "2026-04-30",
          "skip_reason": null,
          "time_spent_total": 0.0,
          "created_at": "2026-04-25T08:00:00Z",
          "created_by": null,
          "assigned_to": {
            "id": "uuid-tech",
            "initials": "JD",
            "first_name": "Jean",
            "last_name": "Dupont"
          },
          "actions": []
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
    "count": 1
  },
  "counters": null,
  "options": null,
  "meta": { "generated_at": "2026-05-14T08:00:00", "etag": "abc123" },
  "audit": {
    "required": true,
    "reasons": [
      { "code": "CLIENT_REQUEST", "label": "Demande client", "color": "#8b5cf6", "requires_text": false },
      { "code": "OTHER", "label": "Autre raison", "color": "#9ca3af", "requires_text": true }
    ]
  }
}
```

> **Pagination sur les interventions** : `total` = nombre d'interventions distinctes contenant des tâches correspondant aux filtres. Toutes les tâches d'une même intervention sont retournées dans le même item.

| Champ              | Description                                                                 |
| ------------------ | --------------------------------------------------------------------------- |
| `audit.required`   | `true` → le front doit afficher un sélecteur de raison avant toute mutation |
| `audit.reasons`    | Raisons disponibles filtrées pour cette entité (catégories `manual`/`user`) |
| `requires_text`    | `true` si la raison exige un texte libre (`reason_code = "OTHER"`)          |

---

## `GET /intervention-tasks`

### Query params

| Param              | Type   | Défaut | Description                                               |
| ------------------ | ------ | ------ | --------------------------------------------------------- |
| `intervention_id`  | uuid   | —      | Filtrer par intervention (fiche intervention)             |
| `assigned_to`      | uuid   | —      | UUID technicien assigné, ou `"unassigned"`                |
| `status`           | csv    | —      | `todo,in_progress,done,skipped`                           |
| `origin`           | csv    | —      | `plan,resp,tech`                                          |
| `q`                | string | —      | Recherche full-text sur label, titre et code intervention |
| `include_done`     | bool   | false  | Inclure les tâches `done` et `skipped`                    |
| `skip`             | int    | 0      | Offset (nombre d'interventions à sauter)                  |
| `limit`            | int    | 20     | Nombre d'interventions par page (max : 200)               |
| `include_actions`  | bool   | false  | Inclure les actions liées à chaque tâche                  |
| `include_options`  | bool   | false  | Inclure les listes de filtres (users, interventions)      |
| `include_counters` | bool   | false  | Inclure les compteurs globaux (toutes tâches, sans filtre de page) |

### Champs d'une tâche dans `items[].tasks`

| Champ              | Description                                                                    |
| ------------------ | ------------------------------------------------------------------------------ |
| `origin`           | `plan` (préventif), `resp` (responsable), `tech` (technicien)                  |
| `optional`         | `true` : peut être ignorée sans bloquer la clôture                             |
| `time_spent_total` | Temps total des actions liées (agrégat calculé via `intervention_action_task`) |
| `actions`          | Présent uniquement si `include_actions=true`                                   |

### Compteurs (`include_counters=true`)

```json
{
  "counters": {
    "total": 45,
    "todo": 20,
    "in_progress": 8,
    "done": 12,
    "skipped": 5,
    "backlog_unassigned_todo": 3
  }
}
```

---

## `GET /intervention-tasks/progress`

Calcule la progression des tâches pour une intervention **ou** une occurrence.

### Query params

| Param             | Type | Requis       | Description                                     |
| ----------------- | ---- | ------------ | ----------------------------------------------- |
| `intervention_id` | uuid | conditionnel | ID de l'intervention                            |
| `occurrence_id`   | uuid | conditionnel | ID de l'occurrence (avant acceptation de la DI) |

### Réponse `200`

```json
{
  "total": 5,
  "todo": 1,
  "in_progress": 1,
  "done": 2,
  "skipped": 1,
  "blocking_pending": 1,
  "is_complete": false
}
```

| Champ              | Description                                                                       |
| ------------------ | --------------------------------------------------------------------------------- |
| `total`            | Nombre total de tâches                                                            |
| `todo`             | Tâches non commencées                                                             |
| `in_progress`      | Tâches en cours                                                                   |
| `done`             | Tâches terminées                                                                  |
| `skipped`          | Tâches ignorées                                                                   |
| `blocking_pending` | Tâches en attente (`todo`+`in_progress`) **non-optionnelles** — bloque la clôture |
| `is_complete`      | `true` si `blocking_pending == 0` et `total > 0`                                  |

### Erreurs

| Code | Cas                                            |
| ---- | ---------------------------------------------- |
| 400  | Ni `intervention_id` ni `occurrence_id` fourni |

---

## `GET /intervention-tasks/{id}`

Détail d'une tâche par ID avec agrégats calculés.

### Réponse `200`

```json
{
  "data": {
    "id": "uuid-task",
    "intervention_id": "uuid-intervention",
    "label": "Contrôle tension de la lame",
    "origin": "plan",
    "status": "todo",
    "optional": false,
    "assigned_to": {
      "id": "uuid-tech",
      "first_name": "Jean",
      "last_name": "Dupont",
      "email": "jean.dupont@example.com",
      "initial": "JD",
      "status": "active",
      "role": "uuid"
    },
    "due_date": null,
    "sort_order": 1,
    "skip_reason": null,
    "gamme_step_id": "uuid-step",
    "occurrence_id": "uuid-occurrence",
    "closed_by": null,
    "created_by": null,
    "created_at": "2026-04-25T08:00:00Z",
    "updated_at": null,
    "action_count": 0,
    "time_spent": 0.0
  },
  "audit": { "required": true, "reasons": [ ... ] }
}
```

### Erreurs

| Code | Cas               |
| ---- | ----------------- |
| 404  | Tâche introuvable |

---

## `POST /intervention-tasks`

Crée une tâche manuelle. `origin` doit être `resp` ou `tech` — `plan` est réservé à la génération automatique d'occurrences préventives. Par défaut, `origin = "tech"`.

### Entrée

```json
{
  "intervention_id": "uuid-intervention",
  "label": "Vérifier le serrage des brides",
  "optional": false,
  "assigned_to": "uuid-tech",
  "due_date": "2026-04-30",
  "sort_order": 10,
  "reason_code": "CLIENT_REQUEST"
}
```

| Champ             | Type   | Requis       | Description                                         |
| ----------------- | ------ | ------------ | --------------------------------------------------- |
| `intervention_id` | uuid   | **oui**      | Intervention parente                                |
| `label`           | string | **oui**      | Intitulé de la tâche                                |
| `origin`          | string | non          | `resp` ou `tech`. Défaut : `tech` (`plan` interdit) |
| `optional`        | bool   | non          | Défaut `false`                                      |
| `assigned_to`     | uuid   | non          | Technicien assigné                                  |
| `due_date`        | date   | non          | Échéance (format `YYYY-MM-DD`)                      |
| `sort_order`      | int    | non          | Ordre d'affichage, défaut `0`                       |
| `reason_code`     | string | **oui**      | Code raison pour l'audit. Voir `GET /audit/reasons` |
| `reason_text`     | string | conditionnel | Obligatoire si `reason_code = "OTHER"`              |

### Réponse `201`

Tâche créée avec `status = "todo"`.

### Erreurs

| Code | Cas                        |
| ---- | -------------------------- |
| 422  | `origin = "plan"` interdit |
| 422  | Champ requis manquant      |

---

## `PATCH /intervention-tasks/{id}`

Met à jour partiellement une tâche. Seuls les champs fournis sont modifiés.

### Entrée

```json
{
  "status": "skipped",
  "skip_reason": "Étape non applicable sur ce modèle",
  "assigned_to": "uuid-tech",
  "reason_code": "TECHNICIAN_UNAVAILABLE"
}
```

| Champ         | Type   | Requis       | Description                              |
| ------------- | ------ | ------------ | ---------------------------------------- |
| `label`       | string | non          | Nouvel intitulé                          |
| `status`      | string | non          | `skipped` uniquement via PATCH direct    |
| `skip_reason` | string | si `skipped` | **Obligatoire si status = "skipped"**    |
| `assigned_to` | uuid   | non          | Technicien assigné                       |
| `due_date`    | date   | non          | Échéance                                 |
| `sort_order`  | int    | non          | Ordre d'affichage                        |
| `reason_code` | string | **oui**      | Code raison pour l'audit. Voir `GET /audit/reasons` |
| `reason_text` | string | conditionnel | Obligatoire si `reason_code = "OTHER"`   |

> Les transitions vers `in_progress` et `done` passent obligatoirement par `POST /intervention-actions`.

### Réponse `200`

Tâche mise à jour.

### Erreurs

| Code | Cas                                     |
| ---- | --------------------------------------- |
| 400  | `status = "skipped"` sans `skip_reason` |
| 400  | `status` invalide                       |
| 404  | Tâche introuvable                       |

---

## `DELETE /intervention-tasks/{id}`

Supprime une tâche. La suppression n'est autorisée que si :

- `status = "todo"` (tâche pas encore commencée)
- Aucune liaison dans `intervention_action_task` (aucune action n'a traité cette tâche)

### Body

```json
{
  "reason_code": "OTHER",
  "reason_text": "Tâche créée par erreur"
}
```

| Champ         | Type   | Requis       | Description                            |
| ------------- | ------ | ------------ | -------------------------------------- |
| `reason_code` | string | **oui**      | Code raison pour l'audit               |
| `reason_text` | string | conditionnel | Obligatoire si `reason_code = "OTHER"` |

### Réponse `204`

Pas de corps.

### Erreurs

| Code | Cas                                        |
| ---- | ------------------------------------------ |
| 400  | Tâche pas en statut `todo`                 |
| 400  | Au moins une action est liée à cette tâche |
| 404  | Tâche introuvable                          |
