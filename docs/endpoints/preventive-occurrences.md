# Preventive Occurrences

Occurrences de maintenance préventive générées par les plans actifs. Chaque occurrence lie un plan à une machine avec une date planifiée. Lors de la génération, une demande d'intervention (DI) est créée automatiquement.

> Voir aussi : [Preventive Plans](preventive-plans.md) | [Intervention Requests](intervention-requests.md) | [Intervention Tasks](intervention-tasks.md)

---

## Cycle de vie d'une occurrence

```
pending → generated → in_progress → completed
       ↘ skipped          ↑               ↑
         (via PATCH   DI acceptée    DI clôturée
          /:id/skip)  OU intervention  OU intervention
                         fermée (cascade)
```

| Statut        | Description                                                                       |
| ------------- | --------------------------------------------------------------------------------- |
| `pending`     | Générée, en attente de création de DI                                             |
| `generated`   | DI créée et liée via `di_id` (statut DI : `nouvelle`)                            |
| `in_progress` | DI acceptée — intervention liée via `intervention_id`, travaux en cours           |
| `completed`   | DI clôturée ou intervention fermée — passage automatique en cascade               |
| `skipped`     | Ignorée manuellement (raison obligatoire)                                         |

> **Rejet de la DI** : si la DI liée passe en `rejetee`, l'occurrence revient automatiquement à `pending` et `di_id` est vidé.

> **Acceptation en cascade** : DI `nouvelle` → `acceptee` passe l'occurrence à `in_progress` et renseigne `intervention_id`.

> **Clôture en cascade** : DI → `cloturee` **ou** fermeture de l'intervention (via PATCH ou POST /intervention-status-log) passent l'occurrence à `completed`.

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
    "tasks": [
      {
        "id": "uuid-task",
        "gamme_step_id": "uuid-step",
        "label": "Graisser palier gauche",
        "sort_order": 1,
        "optional": false,
        "occurrence_id": "uuid-occurrence-1",
        "intervention_id": null,
        "action_id": null,
        "status": "todo",
        "skip_reason": null,
        "updated_at": null,
        "closed_by": null
      }
    ]
  }
]
```

> **Diagnostic** : si `intervention_id` est `null` sur les tâches alors que l'occurrence a un `intervention_id`, c'est le Bug 1 (corriger via `POST /repair`). Si toutes les tâches sont en `todo` sur une occurrence dont l'intervention est fermée, c'est le Bug 2.

---

## `GET /preventive-occurrences/{id}`

Détail d'une occurrence.

### Réponse `200`

Même structure que la liste, incluant `tasks`.

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

Répare les données corrompues par plusieurs bugs. 

Cette procédure est **idempotente** — elle peut être appelée plusieurs fois sans effet secondaire. Elle ne modifie que les enregistrements réellement dans un état incohérent.

### Bug 1 — Tâches non liées à l'intervention

Lors de l'acceptation manuelle d'une DI préventive, un problème de curseur partagé empêchait le rattachement des `intervention_task` à l'intervention créée. Les tâches restaient avec `intervention_id = NULL` et n'apparaissaient pas dans l'intervention.

**Correction appliquée** : pour chaque occurrence ayant un `intervention_id` (direct ou via la DI liée), les `intervention_task` dont `intervention_id` est encore `NULL` sont rattachées.

### Bug 2 — Occurrence bloquée à `generated` après fermeture de l'intervention

La fermeture d'une intervention via `PATCH /interventions/{id}` ne propageait pas l'état sur l'occurrence préventive liée ni sur la demande associée.

**Correction appliquée** : pour chaque occurrence en `generated` ou `in_progress` dont l'intervention liée est fermée (code `ferme`) :
- l'occurrence passe à `completed`
- la DI liée passe à `cloturee` (si encore `acceptee`) avec log dans `request_status_log`

### Bug 3 — `plan_id` null sur une intervention préventive

Lors de l'acceptation manuelle d'une DI préventive via `POST /interventions` (chemin direct, sans passer par `PATCH /intervention-requests/{id}/status`), le `plan_id` n'était pas résolu depuis l'occurrence. Conséquence : les tâches préventives n'apparaissaient pas dans la réponse `GET /interventions/{id}`.

**Correction appliquée** : pour chaque intervention dont `plan_id` est `NULL` mais qui est liée à une occurrence préventive ayant un `plan_id`, le `plan_id` est rétabli.

### Réponse `200`

```json
{
  "tasks_relinked": 12,
  "occurrences_relinked": 3,
  "occurrences_set_in_progress": 3,
  "occurrences_completed": 2,
  "requests_closed": 2,
  "interventions_plan_fixed": 1,
  "details": [
    "Bug 3 : 1 intervention(s) — plan_id rétabli",
    "Bug 1 : 12 tâche(s) rattachée(s) aux interventions : abc-123, def-456",
    "Étape 3 : 3 occurrence(s) → 'in_progress' (DI acceptée)",
    "Bug 2 : occurrence xyz-789 → 'completed' (intervention fermée : aaa-111)"
  ]
}
```

| Champ                        | Description                                                                        |
| ---------------------------- | ---------------------------------------------------------------------------------- |
| `tasks_relinked`             | Nombre de `intervention_task` rattachées (Bug 1)                                   |
| `occurrences_relinked`       | Occurrences dont `intervention_id` a été rétabli depuis la DI liée                 |
| `occurrences_set_in_progress`| Occurrences passées de `generated` à `in_progress` (DI déjà acceptée)             |
| `occurrences_completed`      | Occurrences passées à `completed` (intervention fermée)                            |
| `requests_closed`            | DI clôturées en cascade                                                            |
| `interventions_plan_fixed`   | Interventions dont `plan_id` a été rétabli depuis l'occurrence liée (Bug 3)        |
| `details`                    | Journal détaillé de chaque correction appliquée                                    |
