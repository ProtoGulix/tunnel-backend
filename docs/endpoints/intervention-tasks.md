# Intervention Tasks

Tâches attachées à une intervention. Une tâche représente **quoi faire** — elle peut provenir d'un plan de maintenance préventive (`origin = plan`) ou être créée manuellement par un responsable (`resp`) ou un technicien (`tech`).

> Voir aussi : [Preventive Plans](preventive-plans.md) | [Preventive Occurrences](preventive-occurrences.md) | [Interventions](interventions.md) | [Intervention Actions](intervention-actions.md)

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

## `GET /intervention-tasks`

Liste les tâches avec filtres optionnels. Par défaut, les tâches `done` et `skipped` sont exclues.

### Query params

| Param             | Type | Défaut | Description                            |
| ----------------- | ---- | ------ | -------------------------------------- |
| `intervention_id` | uuid | —      | Filtrer par intervention               |
| `assigned_to`     | uuid | —      | Filtrer par technicien assigné         |
| `status`          | csv  | —      | `todo,in_progress,done,skipped`        |
| `origin`          | csv  | —      | `plan,resp,tech`                       |
| `include_done`    | bool | false  | Inclure les tâches `done` et `skipped` |

### Réponse `200`

```json
[
  {
    "id": "uuid-task-1",
    "intervention_id": "uuid-intervention",
    "label": "Contrôle tension de la lame",
    "origin": "plan",
    "status": "todo",
    "optional": false,
    "assigned_to": null,
    "due_date": null,
    "sort_order": 1,
    "skip_reason": null,
    "gamme_step_id": "uuid-step",
    "occurrence_id": "uuid-occurrence",
    "action_id": null,
    "closed_by": null,
    "created_by": null,
    "created_at": "2026-04-25T08:00:00Z",
    "updated_at": null,
    "action_count": 0,
    "time_spent": 0.0
  },
  {
    "id": "uuid-task-2",
    "intervention_id": "uuid-intervention",
    "label": "Lubrification des guides",
    "origin": "plan",
    "status": "done",
    "optional": true,
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
    "sort_order": 2,
    "skip_reason": null,
    "gamme_step_id": "uuid-step-2",
    "occurrence_id": "uuid-occurrence",
    "action_id": "uuid-action",
    "closed_by": "uuid-tech",
    "created_by": null,
    "created_at": "2026-04-25T08:00:00Z",
    "updated_at": "2026-04-25T10:00:00Z",
    "action_count": 1,
    "time_spent": 0.5
  }
]
```

| Champ           | Description                                                          |
| --------------- | -------------------------------------------------------------------- |
| `origin`        | `plan` (préventif), `resp` (responsable), `tech` (technicien)        |
| `optional`      | `true` : peut être ignorée sans bloquer la clôture                   |
| `gamme_step_id` | UUID du step de gamme d'origine (`null` pour tâches non-préventives) |
| `action_count`  | Nombre d'actions liées (agrégat calculé)                             |
| `time_spent`    | Temps total des actions liées (agrégat calculé)                      |
| `closed_by`     | UUID du technicien ayant terminé/ignoré la tâche                     |

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

Détail d'une tâche avec agrégats calculés.

### Réponse `200`

Même structure que la liste.

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
  "sort_order": 10
}
```

| Champ             | Type   | Requis  | Description                                         |
| ----------------- | ------ | ------- | --------------------------------------------------- |
| `intervention_id` | uuid   | **oui** | Intervention parente                                |
| `label`           | string | **oui** | Intitulé de la tâche                                |
| `origin`          | string | non     | `resp` ou `tech`. Défaut : `tech` (`plan` interdit) |
| `optional`        | bool   | non     | Défaut `false`                                      |
| `assigned_to`     | uuid   | non     | Technicien assigné                                  |
| `due_date`        | date   | non     | Échéance (format `YYYY-MM-DD`)                      |
| `sort_order`      | int    | non     | Ordre d'affichage, défaut `0`                       |

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
  "assigned_to": "uuid-tech"
}
```

| Champ         | Type   | Requis       | Description                              |
| ------------- | ------ | ------------ | ---------------------------------------- |
| `label`       | string | non          | Nouvel intitulé                          |
| `status`      | string | non          | `todo`, `in_progress`, `done`, `skipped` |
| `skip_reason` | string | si `skipped` | **Obligatoire si status = "skipped"**    |
| `assigned_to` | uuid   | non          | Technicien assigné                       |
| `due_date`    | date   | non          | Échéance                                 |
| `sort_order`  | int    | non          | Ordre d'affichage                        |

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
- Aucune action liée (`action_id IS NULL`)

### Réponse `204`

Pas de corps.

### Erreurs

| Code | Cas                                        |
| ---- | ------------------------------------------ |
| 400  | Tâche pas en statut `todo`                 |
| 400  | Au moins une action est liée à cette tâche |
| 404  | Tâche introuvable                          |
