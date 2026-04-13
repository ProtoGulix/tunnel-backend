# Gamme Step Validations

Suivi de la validation des étapes de gamme lors d'une intervention préventive. Chaque validation est liée à une étape du plan (`preventive_plan_gamme_step`), à l'occurrence qui l'a générée, et — après acceptation de la DI — à l'intervention.

> Voir aussi : [Preventive Plans](preventive-plans.md) | [Preventive Occurrences](preventive-occurrences.md) | [Interventions](interventions.md)

---

## Cycle de vie d'une validation

Les validations sont créées automatiquement lors de l'appel `POST /preventive-occurrences/generate`, dans la même transaction que l'occurrence. `occurrence_id` est renseigné immédiatement ; `intervention_id` est `null` jusqu'à ce que la DI liée soit acceptée (transition `acceptee`), moment où toutes les validations de l'occurrence sont rattachées à l'intervention créée.

---

## `GET /gamme-step-validations`

Liste les validations pour une intervention **ou** une occurrence. Un des deux paramètres est obligatoire.

### Query params

| Param             | Type | Requis      | Description                                    |
| ----------------- | ---- | ----------- | ---------------------------------------------- |
| `intervention_id` | uuid | conditionnel | ID de l'intervention                           |
| `occurrence_id`   | uuid | conditionnel | ID de l'occurrence (avant acceptation de la DI) |

### Réponse `200`

```json
[
  {
    "id": "uuid-validation-1",
    "step_id": "uuid-step-1",
    "step_label": "Contrôle de la tension de la lame",
    "step_sort_order": 1,
    "step_optional": false,
    "occurrence_id": "uuid-occurrence",
    "intervention_id": null,
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
    "occurrence_id": "uuid-occurrence",
    "intervention_id": "uuid-intervention",
    "action_id": "uuid-action",
    "status": "validated",
    "skip_reason": null,
    "validated_at": "2026-04-13T09:30:00",
    "validated_by": "uuid-technicien"
  }
]
```

| Champ              | Description                                                                              |
| ------------------ | ---------------------------------------------------------------------------------------- |
| `occurrence_id`    | Occurrence préventive qui a généré cette validation                                      |
| `intervention_id`  | `null` avant acceptation de la DI ; renseigné automatiquement lors de la transition `acceptee` |
| `step_optional`    | `true` : l'étape peut être ignorée sans bloquer la clôture                               |
| `action_id`        | Action d'intervention optionnellement liée à cette validation                            |
| `status`           | `pending`, `validated`, `skipped`                                                        |
| `validated_by`     | UUID du technicien qui a validé/ignoré l'étape                                           |

### Erreurs

| Code | Cas                                                   |
| ---- | ----------------------------------------------------- |
| 400  | Ni `intervention_id` ni `occurrence_id` fourni        |

---

## `GET /gamme-step-validations/by-occurrence?occurrence_id=`

Alias explicite pour lister les validations par occurrence (même résultat que `GET /?occurrence_id=`).

### Query params

| Param           | Type | Requis  | Description        |
| --------------- | ---- | ------- | ------------------ |
| `occurrence_id` | uuid | **oui** | ID de l'occurrence |

### Réponse `200`

Même structure que `GET /`.

---

## `GET /gamme-step-validations/progress`

Calcule la progression de la gamme pour une intervention **ou** une occurrence. Un des deux paramètres est obligatoire.

### Query params

| Param             | Type | Requis      | Description                                     |
| ----------------- | ---- | ----------- | ----------------------------------------------- |
| `intervention_id` | uuid | conditionnel | ID de l'intervention                            |
| `occurrence_id`   | uuid | conditionnel | ID de l'occurrence (avant acceptation de la DI) |

### Réponse `200`

```json
{
  "total": 5,
  "validated": 3,
  "skipped": 1,
  "pending": 1,
  "blocking_pending": 1,
  "is_complete": false
}
```

| Champ              | Description                                                                          |
| ------------------ | ------------------------------------------------------------------------------------ |
| `total`            | Nombre total d'étapes                                                                |
| `validated`        | Étapes validées                                                                      |
| `skipped`          | Étapes ignorées                                                                      |
| `pending`          | Toutes les étapes en attente (optionnelles + obligatoires)                           |
| `blocking_pending` | Étapes en attente **non optionnelles** — c'est ce compteur qui bloque la clôture     |
| `is_complete`      | `true` si `blocking_pending == 0` et `total > 0`                                     |

### Erreurs

| Code | Cas                                                   |
| ---- | ----------------------------------------------------- |
| 400  | Ni `intervention_id` ni `occurrence_id` fourni        |

> **Clôture** : si l'intervention a un plan de gamme (`plan_id` non null), le passage en `ferme` est bloqué quand `blocking_pending > 0` (retourne `409` avec `"Des étapes de gamme sont en attente de validation"`). Les étapes optionnelles (`step_optional = true`) peuvent être ignorées sans impact sur `is_complete`.

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
