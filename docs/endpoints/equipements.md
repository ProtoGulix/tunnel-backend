# Equipements

Gestion du parc d'équipements avec état de santé calculé, classification et hiérarchie parent/enfants.

> Voir aussi : [Equipement Classes](equipement-class.md) | [Equipement Statuts](equipement-statuts.md) | [Interventions](interventions.md)
>
> Schemas partagés : [EquipementHealth](../shared-schemas.md#equipementhealth) | [EquipementClass](../shared-schemas.md#equipementclass) | [EmbeddedInterventionItem](../shared-schemas.md#embeddedinterventionitem)

---

## `GET /equipements`

Liste les équipements avec leur état de santé, paginée, avec facettes par classe.

Tri par défaut : urgents DESC, ouverts DESC, nom ASC.

### Query params

| Param           | Type   | Défaut | Description                                                                      |
| --------------- | ------ | ------ | -------------------------------------------------------------------------------- |
| `search`        | string | —      | Recherche insensible à la casse sur `code`, `name`, `affectation`                |
| `skip`          | int    | 0      | Nombre d'éléments à ignorer (offset)                                             |
| `limit`         | int    | 50     | Nombre d'éléments par page (max 500)                                             |
| `select_class`  | string | —      | Codes de classes à inclure (filtre exclusif), séparés par virgule. Ex: `POM,SCI` |
| `exclude_class` | string | —      | Codes de classes à exclure, séparés par virgule. Ex: `POM,SCI`                   |
| `select_mere`   | uuid   | —      | UUID de l'équipement parent : retourne uniquement ses enfants directs            |

### Réponse `200`

```json
{
  "items": [
    {
      "id": "5e6b5a20-5d7f-4f6b-9a1f-4ccfb0b7a2a1",
      "code": "EQ-001",
      "name": "Scie principale",
      "health": {
        "level": "ok",
        "reason": "Aucune intervention ouverte",
        "open_interventions_count": 0,
        "urgent_count": 0,
        "open_requests_count": 0,
        "new_requests_count": 0,
        "request_status_counts": {},
        "open_tasks_count": 0,
        "overdue_tasks_count": 0,
        "unassigned_tasks_count": 0,
        "open_purchase_requests_count": 0,
        "purchase_request_status_counts": {},
        "has_affectation": true,
        "rules_triggered": []
      },
      "parent": null,
      "equipement_class": {
        "id": "b28f1f4f-...",
        "code": "SCIE",
        "label": "Scie"
      },
      "statut": {
        "id": 3,
        "code": "EN_SERVICE",
        "label": "En service",
        "interventions": true,
        "couleur": "#10B981"
      }
    }
  ],
  "pagination": {
    "total": 142,
    "page": 1,
    "page_size": 50,
    "total_pages": 3,
    "offset": 0,
    "count": 50
  },
  "facets": {
    "equipement_class": [
      { "code": "SCIE", "label": "Scie", "count": 12 },
      { "code": null, "label": null, "count": 5 }
    ]
  }
}
```

> `equipement_class` dans les items est `null` si aucune classe assignée.
> `statut` est `null` si aucun statut assigné à l'équipement (compatibilité ascendante).
> Les facettes comptent les équipements **sans** tenir compte du filtre `exclude_class`, pour permettre l'affichage des compteurs même sur les classes exclues.

---

## `GET /equipements/{id}`

Détail complet d'un équipement avec tous les champs de la base, `children_count`, interventions directement liées (paginées), et 3 blocs contextuels : plans de maintenance, occurrences préventives, et demandes d'intervention ouvertes.

### Query params

| Param                 | Type | Défaut | Description              |
| --------------------- | ---- | ------ | ------------------------ |
| `interventions_page`  | int  | 1      | Page des interventions   |
| `interventions_limit` | int  | 20     | Taille de page (max 100) |

### Réponse `200`

```json
{
  "id": "5e6b5a20-...",
  "code": "EQ-001",
  "name": "Scie principale",
  "no_machine": "M-042",
  "affectation": "Atelier A",
  "is_mere": true,
  "fabricant": "Bosch",
  "numero_serie": "SN-99887",
  "date_mise_service": "2019-03-15",
  "notes": "Révision annuelle prévue",
  "health": {
    "level": "critical",
    "reason": "1 intervention urgente ouverte",
    "open_interventions_count": 3,
    "urgent_count": 1,
    "open_requests_count": 2,
    "new_requests_count": 2,
    "request_status_counts": {
      "nouvelle": 2,
      "en_attente": 1
    },
    "open_tasks_count": 4,
    "overdue_tasks_count": 1,
    "unassigned_tasks_count": 2,
    "open_purchase_requests_count": 3,
    "purchase_request_status_counts": {
      "OPEN": 2,
      "ORDERED": 1
    },
    "has_affectation": true,
    "rules_triggered": [
      "URGENT_OPEN >= 1",
      "OVERDUE_TASKS > 0",
      "OPEN_TASKS > 0",
      "OPEN_REQUESTS > 0",
      "OPEN_PURCHASE_REQUESTS > 0"
    ]
  },
  "parent": {
    "id": "uuid-parent",
    "code": "EQ-000",
    "name": "Machine mère"
  },
  "equipement_class": { "id": "uuid", "code": "SCIE", "label": "Scie" },
  "statut": {
    "id": 3,
    "code": "EN_SERVICE",
    "label": "En service",
    "interventions": true,
    "couleur": "#10B981"
  },
  "children_count": 233,
  "interventions": {
    "total": 47,
    "page": 1,
    "page_size": 20,
    "total_pages": 3,
    "items": [
      {
        "id": "uuid",
        "code": "INT-0091",
        "title": "Remplacement lame",
        "type_inter": {
          "code": "CUR",
          "label": "Curatif"
        },
        "status_actual": "ouvert",
        "priority": "urgent",
        "reported_date": "2026-02-10"
      }
    ]
  },
  "preventive_plans": [
    {
      "id": "uuid-plan-1",
      "code": "PRE-SCIE-001",
      "label": "Maintenance mensuelle Scie",
      "trigger_type": "periodicity",
      "periodicity_days": 30,
      "hours_threshold": null,
      "active": true,
      "next_occurrence": "2026-05-15"
    }
  ],
  "preventive_occurrences_summary": {
    "pending_count": 1,
    "generated_count": 3,
    "skipped_count": 2,
    "next_scheduled": "2026-05-15",
    "last_skipped_reason": "Équipement en révision"
  },
  "open_requests": [
    {
      "id": "uuid-req-1",
      "code": "DI-0451",
      "description": "Remplacement courroie d'entraînement",
      "statut": "nouvelle",
      "statut_label": "Nouvelle demande",
      "statut_color": "#EF4444",
      "is_system": false,
      "created_at": "2026-04-12"
    }
  ]
}
```

### Détail des nouveaux blocs

#### `preventive_plans` (optionnel)

Plans de maintenance préventive applicables à cet équipement (via sa classe d'équipement).

| Champ              | Type         | Description                                                |
| ------------------ | ------------ | ---------------------------------------------------------- |
| `id`               | UUID         | ID du plan                                                 |
| `code`             | string       | Code du plan                                               |
| `label`            | string       | Libellé descriptif                                         |
| `trigger_type`     | string       | Type de déclenchement : `"periodicity"` ou `"hours"`       |
| `periodicity_days` | int \| null  | Intervalle en jours (si trigger_type = periodicity)        |
| `hours_threshold`  | int \| null  | Seuil d'heures (si trigger_type = hours)                   |
| `active`           | bool         | Statut d'activation du plan                                |
| `next_occurrence`  | date \| null | Date de la prochaine occurrence pending/générée, si existe |

Retourne `null` si aucune classe d'équipement assignée. Vide `[]` si la classe n'a pas de plans actifs.

#### `preventive_occurrences_summary` (obligatoire)

Résumé agrégé des occurrences préventives liées à cet équipement.

| Champ                 | Type           | Description                               |
| --------------------- | -------------- | ----------------------------------------- |
| `pending_count`       | int            | Nombre d'occurrences en attente (pending) |
| `generated_count`     | int            | Nombre d'occurrences générées             |
| `skipped_count`       | int            | Nombre d'occurrences skippées             |
| `next_scheduled`      | date \| null   | Date de la prochaine occurrence pending   |
| `last_skipped_reason` | string \| null | Raison du dernier skip                    |

Retourne toujours un objet, avec compteurs à zéro et dates `null` si aucune occurrence.

#### `open_requests` (optionnel)

Demandes d'intervention ouvertes liées à cet équipement (tous les statuts sauf `"rejetee"` et `"cloturee"`).

| Champ          | Type           | Description                          |
| -------------- | -------------- | ------------------------------------ |
| `id`           | UUID           | ID de la demande                     |
| `code`         | string \| null | Code de la demande                   |
| `description`  | string \| null | Description de la demande            |
| `statut`       | string         | Code du statut (ex. `"nouvelle"`)    |
| `statut_label` | string \| null | Libellé du statut                    |
| `statut_color` | string \| null | Couleur associée au statut (hex)     |
| `is_system`    | bool           | Indique si c'est une demande système |
| `created_at`   | date \| null   | Date de création                     |

Retourne `null` si aucune demande ouverte. Triées par `created_at DESC`.

---

> Les interventions retournées sont uniquement celles **directement liées** à cet équipement (`machine_id`), triées par `reported_date DESC`.
> En cas de problème lors de la récupération des blocs contextuels (plans, occurrences, demandes), l'endpoint retourne `200` avec les blocs retournant `null` ou des listes vides, pour garantir la résilience.

---

## `POST /equipements`

Crée un équipement.

### Entrée

```json
{
  "name": "Scie principale",
  "code": "EQ-001",
  "no_machine": "M-042",
  "affectation": "Atelier A",
  "is_mere": true,
  "fabricant": "Bosch",
  "numero_serie": "SN-99887",
  "date_mise_service": "2019-03-15",
  "notes": "Révision annuelle prévue",
  "parent_id": null,
  "equipement_class_id": "b28f1f4f-...",
  "statut_id": 3,
  "children_ids": ["uuid-enfant-1", "uuid-enfant-2"]
}
```

| Champ                 | Type   | Requis | Description                                                       |
| --------------------- | ------ | ------ | ----------------------------------------------------------------- |
| `name`                | string | oui    | Nom de l'équipement                                               |
| `code`                | string | non    | Code unique                                                       |
| `no_machine`          | string | non    | Numéro machine interne                                            |
| `affectation`         | string | non    | Lieu ou service d'affectation                                     |
| `is_mere`             | bool   | non    | Indique si l'équipement est une machine mère                      |
| `fabricant`           | string | non    | Fabricant                                                         |
| `numero_serie`        | string | non    | Numéro de série                                                   |
| `date_mise_service`   | date   | non    | Date de mise en service (YYYY-MM-DD)                              |
| `notes`               | string | non    | Notes libres                                                      |
| `parent_id`           | uuid   | non    | UUID de l'équipement parent                                       |
| `equipement_class_id` | uuid   | non    | UUID de la classe d'équipement                                    |
| `statut_id`           | int    | non    | ID du statut (voir `GET /equipement-statuts`)                     |
| `children_ids`        | uuid[] | non    | UUIDs des équipements à rattacher comme enfants de cet équipement |

### Réponse `201`

Équipement complet (même format que `GET /equipements/{id}`).

---

## `PUT /equipements/{id}`

Remplace complètement un équipement. `name` est obligatoire. Tous les champs non envoyés passent à `null`.

### Entrée

Même body que `POST`, avec `name` obligatoire.

### Réponse `200`

Équipement complet (même format que `GET /equipements/{id}`).

---

## `PATCH /equipements/{id}`

Met à jour partiellement un équipement. Seuls les champs envoyés sont modifiés.

### Entrée

Même body que `POST`, tous les champs optionnels (dont `name`).

```json
{
  "statut_id": 4,
  "affectation": "Atelier B"
}
```

### Réponse `200`

Équipement complet (même format que `GET /equipements/{id}`).

> `children_ids` fonctionne de la même façon pour `PUT` et `PATCH` : les équipements listés voient leur `equipement_mere` mis à jour pour pointer vers cet équipement. Les enfants existants non listés ne sont pas modifiés.

---

## `DELETE /equipements/{id}`

Supprime un équipement. Réponse `204`.

---

## `GET /equipements/{id}/stats`

Statistiques détaillées pour un équipement.

### Query params

| Param        | Type | Défaut                   | Description      |
| ------------ | ---- | ------------------------ | ---------------- |
| `start_date` | date | null (tout l'historique) | Début de période |
| `end_date`   | date | now                      | Fin de période   |

### Réponse `200`

```json
{
  "interventions": {
    "open": 2,
    "closed": 5,
    "by_status": { "ouvert": 2, "ferme": 5 },
    "by_priority": { "faible": 1, "normale": 4, "urgent": 2 }
  }
}
```

---

## `GET /equipements/{id}/health`

État de santé uniquement (ultra-léger, polling-friendly).

### Réponse `200`

```json
{
  "level": "ok",
  "reason": "Aucune intervention ouverte",
  "open_interventions_count": 0,
  "urgent_count": 0,
  "open_requests_count": 0,
  "new_requests_count": 0,
  "request_status_counts": {},
  "open_tasks_count": 0,
  "overdue_tasks_count": 0,
  "unassigned_tasks_count": 0,
  "open_purchase_requests_count": 0,
  "purchase_request_status_counts": {},
  "has_affectation": true,
  "rules_triggered": []
}
```
