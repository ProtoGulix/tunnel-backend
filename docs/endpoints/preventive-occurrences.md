# Preventive Occurrences

Occurrences de maintenance préventive générées par les plans actifs. Chaque occurrence lie un plan à une machine avec une date planifiée. Lors de la génération, une demande d'intervention (DI) est créée automatiquement.

> Voir aussi : [Preventive Plans](preventive-plans.md) | [Intervention Requests](intervention-requests.md) | [Gamme Step Validations](gamme-step-validations.md)

---

## Cycle de vie d'une occurrence

```
pending → generated → completed
       ↘ skipped       ↑
         (via PATCH     └─ fermeture de l'intervention liée
          /:id/skip)       (automatique en cascade)
```

| Statut      | Description                                                                    |
| ----------- | ------------------------------------------------------------------------------ |
| `pending`   | Générée, en attente de création de DI                                          |
| `generated` | DI créée et liée via `di_id`; intervention liée via `intervention_id` si acceptée |
| `completed` | Intervention fermée — passage automatique lors de la fermeture de l'intervention |
| `skipped`   | Ignorée manuellement (raison obligatoire)                                      |

> **Rejet de la DI** : si la DI liée passe en `rejetee`, l'occurrence revient automatiquement à `pending` et `di_id` est vidé. Elle pourra être régénérée au prochain appel de `POST /generate`.

> **Fermeture en cascade** : la fermeture d'une intervention (via `PATCH /interventions/{id}` ou `POST /intervention-status-log`) passe automatiquement l'occurrence à `completed` et clôture la DI liée si elle est encore `acceptee`.

---

## `GET /preventive-occurrences`

Liste les occurrences de maintenance préventive avec filtres optionnels.

### Query params

| Param                 | Type   | Description                                    |
| --------------------- | ------ | ---------------------------------------------- |
| `plan_id`             | uuid   | Filtrer par plan préventif                     |
| `machine_id`          | uuid   | Filtrer par machine                            |
| `status`              | string | `pending`, `generated`, `completed`, `skipped` |
| `scheduled_date_from` | date   | Filtre date planifiée ≥ (format `YYYY-MM-DD`)  |
| `scheduled_date_to`   | date   | Filtre date planifiée ≤ (format `YYYY-MM-DD`)  |

### Réponse `200`

```json
[
  {
    "id": "uuid-occurrence-1",
    "plan_id": "uuid-plan",
    "plan_label": "Maintenance hebdomadaire scies",
    "machine_id": "uuid-machine",
    "machine_code": "SCIE-001",
    "machine_name": "Scie principale",
    "scheduled_date": "2026-04-14",
    "triggered_at": "2026-04-13T08:00:00",
    "hours_at_trigger": null,
    "di_id": "uuid-demande",
    "di_code": "DI-2026-0042",
    "di_statut": "nouvelle",
    "intervention_id": null,
    "status": "generated",
    "skip_reason": null,
    "created_at": "2026-04-13T08:00:00",
    "gamme_steps": [
      {
        "id": "uuid-step-validation",
        "step_id": "uuid-step",
        "step_label": "Graisser palier gauche",
        "step_sort_order": 1,
        "step_optional": false,
        "occurrence_id": "uuid-occurrence-1",
        "intervention_id": null,
        "action_id": null,
        "status": "pending",
        "skip_reason": null,
        "validated_at": null,
        "validated_by": null
      }
    ]
  }
]
```

> **Diagnostic** : si `intervention_id` est `null` sur les steps alors que l'occurrence a un `intervention_id`, c'est le Bug 1 (corriger via `POST /repair`). Si tous les steps sont `pending` sur une occurrence dont l'intervention est fermée, c'est le Bug 2.

---

## `GET /preventive-occurrences/{id}`

Détail d'une occurrence.

### Réponse `200`

Même structure que la liste, incluant `gamme_steps`.

### Erreurs

| Code | Cas                        |
| ---- | -------------------------- |
| 404  | Occurrence introuvable     |

---

## `POST /preventive-occurrences/generate`

Déclenche la génération des occurrences pour tous les plans préventifs actifs.

**Logique de génération :**

- Pour chaque plan actif, pour chaque machine de la classe d'équipement du plan :
  - **trigger_type = `periodicity`** : génère si `last_scheduled_date + periodicity_days ≤ today` (ou si aucune occurrence précédente)
  - **trigger_type = `hours`** : génère si `current_hours - last_trigger_hours ≥ hours_threshold`
  - Insère avec `ON CONFLICT (plan_id, machine_id, scheduled_date) DO NOTHING` — pas de doublon
  - Crée automatiquement une DI (`demandeur_nom = "Système préventif"`, `statut = "nouvelle"`, `is_system = true`, `suggested_type_inter = "PRE"`)
  - Si `plan.auto_accept = true` : crée aussi l'intervention (`type_inter = "PRE"`, `tech_initials = "SYS"`)

- Chaque machine est traitée dans sa **propre transaction** — l'échec sur une machine n'annule pas les autres.

### Réponse `200`

```json
{
  "generated": 5,
  "skipped_conflicts": 2,
  "errors": [
    "Plan Maintenance moteurs / Machine CONV-003: machine_hours introuvable"
  ]
}
```

| Champ               | Description                                              |
| ------------------- | -------------------------------------------------------- |
| `generated`         | Nombre d'occurrences créées avec succès                  |
| `skipped_conflicts` | Occurrences ignorées car déjà existantes (ON CONFLICT)   |
| `errors`            | Liste des erreurs par machine (n'empêchent pas les autres) |

---

## `PATCH /preventive-occurrences/{id}/skip`

Ignore une occurrence en statut `pending`.

### Entrée

```json
{
  "skip_reason": "Machine en arrêt technique prolongé"
}
```

| Champ         | Type   | Requis  | Description              |
| ------------- | ------ | ------- | ------------------------ |
| `skip_reason` | string | **oui** | Motif de l'ignorance (non vide) |

### Réponse `200`

Occurrence mise à jour avec `status = "skipped"`.

### Erreurs

| Code | Cas                                                           |
| ---- | ------------------------------------------------------------- |
| 400  | L'occurrence n'est pas en statut `pending`                    |
| 400  | `skip_reason` vide                                            |
| 404  | Occurrence introuvable                                        |

---

## `POST /preventive-occurrences/repair`

Répare les données corrompues par deux bugs présents avant le fix du 2026-04-15.

Cette procédure est **idempotente** — elle peut être appelée plusieurs fois sans effet secondaire. Elle ne modifie que les enregistrements réellement dans un état incohérent.

### Bug 1 — Steps de gamme non liés à l'intervention

Lors de l'acceptation manuelle d'une DI préventive, un problème de curseur partagé empêchait le rattachement des `gamme_step_validation` à l'intervention créée. Les steps restaient avec `intervention_id = NULL` et n'apparaissaient pas dans les actions de l'intervention.

**Correction appliquée** : pour chaque occurrence ayant un `intervention_id`, les `gamme_step_validation` dont `intervention_id` est encore `NULL` sont rattachées.

### Bug 2 — Occurrence bloquée à `generated` après fermeture de l'intervention

La fermeture d'une intervention via `PATCH /interventions/{id}` ne propageait pas l'état sur l'occurrence préventive liée ni sur la demande associée.

**Correction appliquée** : pour chaque occurrence en `generated` dont l'intervention liée est fermée (code `ferme`) :
- l'occurrence passe à `completed`
- la DI liée passe à `cloturee` (si encore `acceptee`) avec log dans `request_status_log`

### Réponse `200`

```json
{
  "steps_relinked": 12,
  "occurrences_relinked": 3,
  "occurrences_completed": 3,
  "requests_closed": 3,
  "details": [
    "Bug 1 : 12 step(s) rattaché(s) aux interventions : abc-123, def-456",
    "Bug 2 : occurrence xyz-789 → 'completed' (intervention fermée : aaa-111)",
    "Bug 2 : demande zzz-222 → 'cloturee' (liée à l'occurrence xyz-789)"
  ]
}
```

| Champ                   | Description                                                                        |
| ----------------------- | ---------------------------------------------------------------------------------- |
| `steps_relinked`        | Nombre de `gamme_step_validation` rattachés (Bug 1)                                |
| `occurrences_relinked`  | Occurrences dont `intervention_id` a été rétabli depuis la DI liée (pré-étape Bug 2) |
| `occurrences_completed` | Nombre d'occurrences passées à `completed` (Bug 2)                                 |
| `requests_closed`       | Nombre de DI clôturées en cascade (Bug 2)                                          |
| `details`               | Journal détaillé de chaque correction appliquée                                    |
