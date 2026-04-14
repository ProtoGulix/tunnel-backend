# Preventive Plans

Gestion des gammes de maintenance préventive. Chaque plan définit un déclencheur (périodicité en jours ou seuil d'heures machine), s'applique à une classe d'équipement et contient une liste d'étapes de gamme ordonnées.

> Voir aussi : [Preventive Occurrences](preventive-occurrences.md) | [Gamme Step Validations](gamme-step-validations.md)

---

## `GET /preventive-plans`

Liste tous les plans de maintenance préventive.

### Query params

| Param         | Type | Défaut | Description                                |
| ------------- | ---- | ------ | ------------------------------------------ |
| `active_only` | bool | `true` | `false` pour inclure les plans désactivés  |

### Réponse `200`

```json
[
  {
    "id": "a1b2c3d4-0000-0000-0000-000000000001",
    "code": "PM-SCIE-H",
    "label": "Maintenance hebdomadaire scies",
    "equipement_class_id": "uuid-classe-scie",
    "equipement_class_label": "Scie",
    "trigger_type": "periodicity",
    "periodicity_days": 7,
    "hours_threshold": null,
    "auto_accept": false,
    "active": true,
    "created_at": "2026-03-01T10:00:00",
    "updated_at": "2026-03-01T10:00:00",
    "steps": [
      {
        "id": "uuid-step-1",
        "plan_id": "a1b2c3d4-0000-0000-0000-000000000001",
        "label": "Contrôle de la tension de la lame",
        "sort_order": 1,
        "optional": false
      },
      {
        "id": "uuid-step-2",
        "plan_id": "a1b2c3d4-0000-0000-0000-000000000001",
        "label": "Lubrification des guides",
        "sort_order": 2,
        "optional": true
      }
    ]
  }
]
```

---

## `GET /preventive-plans/{id}`

Détail complet d'un plan de maintenance préventive avec ses étapes de gamme.

### Réponse `200`

Même structure que la liste.

### Erreurs

| Code | Cas                         |
| ---- | --------------------------- |
| 404  | Plan préventif introuvable  |

---

## `POST /preventive-plans`

Crée un nouveau plan de maintenance préventive.

### Entrée

```json
{
  "code": "PM-SCIE-H",
  "label": "Maintenance hebdomadaire scies",
  "equipement_class_id": "uuid-classe-scie",
  "trigger_type": "periodicity",
  "periodicity_days": 7,
  "auto_accept": false,
  "steps": [
    { "label": "Contrôle de la tension de la lame", "sort_order": 1, "optional": false },
    { "label": "Lubrification des guides", "sort_order": 2, "optional": true }
  ]
}
```

| Champ                  | Type    | Requis  | Description                                                            |
| ---------------------- | ------- | ------- | ---------------------------------------------------------------------- |
| `code`                 | string  | **oui** | Code unique du plan                                                    |
| `label`                | string  | **oui** | Libellé du plan                                                        |
| `equipement_class_id`  | uuid    | **oui** | Classe d'équipement cible                                              |
| `trigger_type`         | string  | **oui** | `periodicity` ou `hours`                                               |
| `periodicity_days`     | int     | *cond*  | Requis si `trigger_type = "periodicity"`. Intervalle en jours          |
| `hours_threshold`      | int     | *cond*  | Requis si `trigger_type = "hours"`. Seuil en heures machine            |
| `auto_accept`          | bool    | non     | `true` : crée automatiquement l'intervention sans attendre acceptation |
| `steps`                | array   | non     | Étapes de gamme ordonnées (peut être vide)                             |
| `steps[].label`        | string  | **oui** | Libellé de l'étape                                                     |
| `steps[].sort_order`   | int     | **oui** | Ordre d'affichage (croissant)                                          |
| `steps[].optional`     | bool    | non     | `false` par défaut                                                     |

> **Validation Pydantic** : `periodicity_days` est requis si `trigger_type = "periodicity"` ; `hours_threshold` est requis si `trigger_type = "hours"`. Retourne `422` si la contrainte n'est pas respectée.

### Réponse `201`

Plan complet créé avec ses étapes.

### Erreurs

| Code | Cas                                    |
| ---- | -------------------------------------- |
| 409  | Code déjà utilisé                      |
| 400  | Référence `equipement_class_id` invalide |
| 422  | Champ trigger manquant (Pydantic)      |

---

## `PUT /preventive-plans/{id}`

Met à jour un plan existant (PATCH sémantique — seuls les champs fournis sont modifiés). **Le champ `code` est immuable**.

### Entrée

Tous les champs sont optionnels sauf `code` (non accepté).

```json
{
  "label": "Maintenance bi-hebdomadaire scies",
  "periodicity_days": 14,
  "steps": [
    { "label": "Contrôle de la tension de la lame", "sort_order": 1, "optional": false }
  ]
}
```

> Si `steps` est fourni, les étapes existantes sont **entièrement remplacées**.

### Réponse `200`

Plan complet mis à jour.

### Erreurs

| Code | Cas                         |
| ---- | --------------------------- |
| 404  | Plan préventif introuvable  |

---

## `PATCH /preventive-plans/{id}/steps`

Remplace entièrement les étapes de gamme d'un plan.

### Entrée

```json
[
  { "label": "Contrôle de la tension de la lame", "sort_order": 1, "optional": false },
  { "label": "Lubrification des guides", "sort_order": 2, "optional": true },
  { "label": "Nettoyage du plateau", "sort_order": 3, "optional": false }
]
```

### Réponse `200`

Liste des nouvelles étapes.

### Erreurs

| Code | Cas                         |
| ---- | --------------------------- |
| 404  | Plan préventif introuvable  |

---

## `DELETE /preventive-plans/{id}`

Désactive un plan de maintenance préventive (soft delete — `active = false`).

### Réponse `204`

Pas de corps.

### Erreurs

| Code | Cas                         |
| ---- | --------------------------- |
| 404  | Plan préventif introuvable  |
