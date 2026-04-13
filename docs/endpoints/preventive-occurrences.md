# Preventive Occurrences

Occurrences de maintenance préventive générées par les plans actifs. Chaque occurrence lie un plan à une machine avec une date planifiée. Lors de la génération, une demande d'intervention (DI) est créée automatiquement.

> Voir aussi : [Preventive Plans](preventive-plans.md) | [Intervention Requests](intervention-requests.md) | [Gamme Step Validations](gamme-step-validations.md)

---

## Cycle de vie d'une occurrence

```
pending → generated → (intervention liée) → ferme
                   ↘ skipped  (via PATCH /:id/skip)
```

| Statut      | Description                                                  |
| ----------- | ------------------------------------------------------------ |
| `pending`   | Générée, en attente de création de DI                        |
| `generated` | DI créée, liée via `di_id`                                   |
| `skipped`   | Ignorée manuellement (raison obligatoire)                    |

---

## `GET /preventive-occurrences`

Liste les occurrences de maintenance préventive avec filtres optionnels.

### Query params

| Param                 | Type   | Description                                    |
| --------------------- | ------ | ---------------------------------------------- |
| `plan_id`             | uuid   | Filtrer par plan préventif                     |
| `machine_id`          | uuid   | Filtrer par machine                            |
| `status`              | string | `pending`, `generated`, `skipped`              |
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
    "intervention_id": null,
    "status": "generated",
    "skip_reason": null,
    "created_at": "2026-04-13T08:00:00"
  }
]
```

---

## `GET /preventive-occurrences/{id}`

Détail d'une occurrence.

### Réponse `200`

Même structure que la liste.

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
  - Crée automatiquement une DI (`demandeur_nom = "Système préventif"`, `statut = "nouvelle"`)
  - Si `plan.auto_accept = true` : crée aussi l'intervention (`type_inter = "PREV"`, `tech_initials = "SYS"`)

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
