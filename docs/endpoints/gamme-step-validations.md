# Gamme Step Validations

Suivi de la validation des étapes de gamme lors d'une intervention préventive. Chaque validation est liée à une étape du plan (`preventive_plan_gamme_step`) et à une intervention.

> Voir aussi : [Preventive Plans](preventive-plans.md) | [Interventions](interventions.md)

---

## `GET /gamme-step-validations?intervention_id=`

Liste les validations d'étapes de gamme pour une intervention, triées par `sort_order ASC`.

### Query params

| Param             | Type | Requis  | Description             |
| ----------------- | ---- | ------- | ----------------------- |
| `intervention_id` | uuid | **oui** | ID de l'intervention    |

### Réponse `200`

```json
[
  {
    "id": "uuid-validation-1",
    "step_id": "uuid-step-1",
    "step_label": "Contrôle de la tension de la lame",
    "step_sort_order": 1,
    "step_optional": false,
    "intervention_id": "uuid-intervention",
    "action_id": null,
    "status": "pending",
    "skip_reason": null,
    "validated_at": null,
    "validated_by": null
  },
  {
    "id": "uuid-validation-2",
    "step_id": "uuid-step-2",
    "step_label": "Lubrification des guides",
    "step_sort_order": 2,
    "step_optional": true,
    "intervention_id": "uuid-intervention",
    "action_id": "uuid-action",
    "status": "validated",
    "skip_reason": null,
    "validated_at": "2026-04-13T09:30:00",
    "validated_by": "uuid-technicien"
  }
]
```

| Champ              | Description                                                     |
| ------------------ | --------------------------------------------------------------- |
| `step_label`       | Libellé de l'étape (depuis `preventive_plan_gamme_step`)        |
| `step_optional`    | `true` : l'étape peut être ignorée sans bloquer la clôture      |
| `action_id`        | Action d'intervention optionnellement liée à cette validation   |
| `status`           | `pending`, `validated`, `skipped`                               |
| `validated_by`     | UUID du technicien qui a validé/ignoré l'étape                  |

---

## `GET /gamme-step-validations/progress?intervention_id=`

Calcule la progression de la gamme pour une intervention.

### Query params

| Param             | Type | Requis  | Description             |
| ----------------- | ---- | ------- | ----------------------- |
| `intervention_id` | uuid | **oui** | ID de l'intervention    |

### Réponse `200`

```json
{
  "total": 5,
  "validated": 3,
  "skipped": 1,
  "pending": 1,
  "is_complete": false
}
```

| Champ         | Description                                             |
| ------------- | ------------------------------------------------------- |
| `total`       | Nombre total d'étapes                                   |
| `validated`   | Étapes validées                                         |
| `skipped`     | Étapes ignorées                                         |
| `pending`     | Étapes en attente                                       |
| `is_complete` | `true` si `pending == 0` et `total > 0`                 |

> **Clôture** : si l'intervention a un plan de gamme (`plan_id` non null), un trigger DB peut bloquer le passage en `ferme` quand `pending > 0` (retourne `409` avec `"Des étapes de gamme sont en attente de validation"`). Les étapes optionnelles peuvent être ignorées via `PATCH /:id`.

---

## `PATCH /gamme-step-validations/{id}`

Met à jour le statut d'une étape de gamme (`validated` ou `skipped`).

> Une étape déjà traitée (`validated` ou `skipped`) ne peut pas être modifiée (`400`).

### Entrée

```json
{
  "status": "validated",
  "action_id": "uuid-action-liee",
  "validated_by": "uuid-technicien"
}
```

```json
{
  "status": "skipped",
  "skip_reason": "Étape non applicable sur ce modèle",
  "validated_by": "uuid-technicien"
}
```

| Champ          | Type   | Requis  | Condition                                                                   |
| -------------- | ------ | ------- | --------------------------------------------------------------------------- |
| `status`       | string | **oui** | `validated` ou `skipped` uniquement                                         |
| `validated_by` | uuid   | **oui** | Technicien réalisant la validation                                          |
| `action_id`    | uuid   | non     | Doit appartenir à la **même intervention** que la validation                |
| `skip_reason`  | string | *cond*  | Obligatoire si `status = "skipped"`, ignoré sinon                           |

### Réponse `200`

Validation mise à jour avec `validated_at` renseigné si `status = "validated"`.

### Erreurs

| Code | Cas                                                                 |
| ---- | ------------------------------------------------------------------- |
| 400  | Étape déjà traitée (`validated` ou `skipped`)                       |
| 400  | `skip_reason` absent ou vide pour un statut `skipped`               |
| 400  | `action_id` n'appartient pas à la même intervention                 |
| 404  | Validation introuvable                                              |
| 422  | `status` invalide (ni `validated` ni `skipped`) — erreur Pydantic   |
