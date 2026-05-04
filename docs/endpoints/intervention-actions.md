# Intervention Actions

Actions réalisées sur une intervention (réparation, diagnostic, etc.). Chaque action est liée à un technicien, une sous-catégorie et peut avoir des demandes d'achat.

> Voir aussi : [Interventions](interventions.md) | [Action Categories](action-categories.md) | [Complexity Factors](complexity-factors.md) | [Purchase Requests](purchase-requests.md)

---

## `GET /intervention-actions`

Liste les actions groupées par date (`created_at::date`), du plus récent au plus ancien. À l'intérieur de chaque jour, les actions sont triées par heure croissante.

### Query params

| Param        | Type | Défaut      | Description                              |
| ------------ | ---- | ----------- | ---------------------------------------- |
| `start_date` | date | aujourd'hui | Date de début incluse (ex: `2026-03-10`) |
| `end_date`   | date | aujourd'hui | Date de fin incluse (ex: `2026-03-15`)   |
| `tech_id`    | uuid | —           | Filtre sur le technicien                 |

> Sans paramètre, retourne uniquement les actions du jour. Pour une semaine : `start_date=2026-03-10&end_date=2026-03-15`.

### Réponse `200`

```json
[
  {
    "date": "2026-03-15",
    "actions": [
      {
        "id": "c3d4e5f6-1234-5678-9abc-def012345678",
        "intervention_id": "5ecf60d5-8471-4739-8ba8-0fdad7b51781",
        "intervention": {
          "id": "5ecf60d5-8471-4739-8ba8-0fdad7b51781",
          "code": "CN001-REA-20260315-QC",
          "title": "Remplacement roulement principal",
          "status_actual": "en_cours",
          "equipement_id": "e1f2a3b4-aaaa-bbbb-cccc-111122223333",
          "equipement_code": "EQ-001",
          "equipement_name": "Scie principale"
        },
        "description": "Diagnostic complet de la transmission",
        "time_spent": 1.5,
        "subcategory": {
          "id": 30,
          "name": "Remplacement pièce",
          "code": "DEP_REM",
          "category": { "id": 3, "name": "Dépannage", "code": "DEP", "color": "#e53e3e" }
        },
        "tech": {
          "id": "a1b2c3d4-1111-2222-3333-444455556666",
          "first_name": "Jean",
          "last_name": "Dupont",
          "email": "jean.dupont@example.com",
          "initial": "JD",
          "status": "active",
          "role": "b9f3e2a1-0000-1111-2222-333344445555"
        },
        "complexity_score": 5,
        "complexity_factor": null,
        "action_start": "08:00:00",
        "action_end": "09:30:00",
        "purchase_requests": [],
        "tasks": [],
        "created_at": "2026-03-15T08:00:00",
        "updated_at": "2026-03-15T08:00:00"
      }
    ]
  },
  {
    "date": "2026-03-14",
    "actions": [
      {
        "id": "a0b1c2d3-9999-8888-7777-666655554444",
        "intervention_id": "5ecf60d5-8471-4739-8ba8-0fdad7b51781",
        "intervention": {
          "id": "5ecf60d5-8471-4739-8ba8-0fdad7b51781",
          "code": "CN001-REA-20260315-QC",
          "title": "Remplacement roulement principal",
          "status_actual": "en_cours",
          "equipement_id": "e1f2a3b4-aaaa-bbbb-cccc-111122223333",
          "equipement_code": "EQ-001",
          "equipement_name": "Scie principale"
        },
        "description": null,
        "time_spent": 0.5,
        "subcategory": {
          "id": 12,
          "name": "Inspection visuelle",
          "code": "DIAG_VIS",
          "category": { "id": 1, "name": "Diagnostic", "code": "DIAG", "color": "#3b82f6" }
        },
        "tech": {
          "id": "a1b2c3d4-1111-2222-3333-444455556666",
          "first_name": "Jean",
          "last_name": "Dupont",
          "email": "jean.dupont@example.com",
          "initial": "JD",
          "status": "active",
          "role": "b9f3e2a1-0000-1111-2222-333344445555"
        },
        "complexity_score": 3,
        "complexity_factor": null,
        "action_start": "14:00:00",
        "action_end": "14:30:00",
        "purchase_requests": [],
        "tasks": [],
        "created_at": "2026-03-14T14:00:00",
        "updated_at": "2026-03-14T14:00:00"
      }
    ]
  }
]
```

---

## `GET /intervention-actions/{id}`

Détail complet d'une action avec tout le contexte de l'intervention parente. Conçu pour permettre une analyse complète par un agent IA sans appel supplémentaire.

### Réponse `200` — InterventionActionDetail

```json
{
  "id": "c3d4e5f6-1234-5678-9abc-def012345678",
  "intervention_id": "5ecf60d5-8471-4739-8ba8-0fdad7b51781",
  "description": "Remplacement du roulement SKF 6205 — graissage effectué",
  "time_spent": 1.5,
  "subcategory": {
    "id": 30,
    "name": "Remplacement pièce",
    "code": "DEP_REM",
    "category": {
      "id": 3,
      "name": "Dépannage",
      "code": "DEP",
      "color": "#e53e3e"
    }
  },
  "tech": {
    "id": "a1b2c3d4-1111-2222-3333-444455556666",
    "first_name": "Jean",
    "last_name": "Dupont",
    "email": "jean.dupont@example.com",
    "initial": "JD",
    "status": "active",
    "role": "b9f3e2a1-0000-1111-2222-333344445555"
  },
  "complexity_score": 7,
  "complexity_factor": "PCE",
  "action_start": "08:00:00",
  "action_end": "09:30:00",
  "purchase_requests": [
    {
      "id": "d5e6f7a8-2345-6789-abcd-ef0123456789",
      "item_label": "Roulement SKF 6205",
      "quantity": 2,
      "unit": "pcs",
      "derived_status": { "code": "PENDING_DISPATCH", "label": "À dispatcher", "color": "#A855F7" },
      "stock_item_id": "f9a0b1c2-3456-789a-bcde-f01234567890",
      "stock_item_ref": "OUT-ROUL-SKF-6205",
      "stock_item_name": "Roulement SKF 6205",
      "intervention_code": "CN001-REA-20260113-QC",
      "requester_name": "Jean Dupont",
      "urgency": "high",
      "quotes_count": 0,
      "selected_count": 0,
      "suppliers_count": 2,
      "created_at": "2026-01-13T10:00:00",
      "updated_at": "2026-01-13T10:00:00"
    }
  ],
  "tasks": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "intervention_id": "5ecf60d5-8471-4739-8ba8-0fdad7b51781",
      "label": "Remplacement roulement SKF 6205",
      "origin": "plan",
      "status": "done",
      "optional": false,
      "assigned_to": {
        "id": "a1b2c3d4-1111-2222-3333-444455556666",
        "first_name": "Jean",
        "last_name": "Dupont",
        "email": "jean.dupont@example.com",
        "initial": "JD",
        "status": "active",
        "role": "b9f3e2a1-0000-1111-2222-333344445555"
      },
      "due_date": "2026-01-14",
      "sort_order": 2,
      "skip_reason": null,
      "closed_by": "a1b2c3d4-1111-2222-3333-444455556666",
      "created_by": "f7c9d0e1-aaaa-bbbb-cccc-ddddeeee0000",
      "action_count": 1,
      "time_spent": 1.5,
      "created_at": "2026-01-13T08:00:00",
      "updated_at": "2026-01-13T15:00:00"
    }
  ],
  "created_at": "2026-01-13T14:30:00",
  "updated_at": "2026-01-13T15:00:00",
  "intervention": {
    "id": "5ecf60d5-8471-4739-8ba8-0fdad7b51781",
    "code": "CN001-REA-20260113-QC",
    "title": "Remplacement roulement principal",
    "status_actual": "en_cours",
    "type_inter": "corrective",
    "priority": "high",
    "reported_by": "Chef atelier",
    "tech_initials": "JD",
    "tech_id": "a1b2c3d4-1111-2222-3333-444455556666",
    "reported_date": "2026-01-13",
    "equipements": {
      "id": "e1f2a3b4-aaaa-bbbb-cccc-111122223333",
      "code": "EQ-001",
      "name": "Scie principale",
      "health": "degraded",
      "parent": {
        "id": "b2c3d4e5-ffff-eeee-dddd-000011112222",
        "code": "LIGNE-A",
        "name": "Ligne de production A"
      },
      "equipement_class": {
        "id": 4,
        "name": "Machine rotative",
        "code": "ROT"
      }
    },
    "request": {
      "id": "77c8d9e0-5678-90ab-cdef-012345678901",
      "code": "DI-2026-0042",
      "demandeur_nom": "Marie Curie",
      "demandeur_service": "Production",
      "description": "Bruit anormal sur la scie depuis 2 jours, vibrations importantes",
      "statut": "accepted",
      "statut_label": "Acceptée",
      "statut_color": "#22c55e",
      "intervention_id": "5ecf60d5-8471-4739-8ba8-0fdad7b51781",
      "created_at": "2026-01-12T09:00:00",
      "updated_at": "2026-01-13T08:00:00"
    },
    "stats": {
      "action_count": 3,
      "total_time": 4.5,
      "avg_complexity": 6.33,
      "purchase_count": 1
    },
    "tasks": [
      {
        "id": "440d7300-d18a-30c3-9605-335544330000",
        "intervention_id": "5ecf60d5-8471-4739-8ba8-0fdad7b51781",
        "label": "Diagnostic vibratoire",
        "origin": "plan",
        "status": "done",
        "optional": false,
        "assigned_to": null,
        "due_date": null,
        "sort_order": 1,
        "skip_reason": null,
        "closed_by": "a1b2c3d4-1111-2222-3333-444455556666",
        "created_by": "f7c9d0e1-aaaa-bbbb-cccc-ddddeeee0000",
        "action_count": 1,
        "time_spent": 0.5,
        "created_at": "2026-01-13T07:00:00",
        "updated_at": "2026-01-13T09:00:00"
      },
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "intervention_id": "5ecf60d5-8471-4739-8ba8-0fdad7b51781",
        "label": "Remplacement roulement SKF 6205",
        "origin": "plan",
        "status": "done",
        "optional": false,
        "assigned_to": {
          "id": "a1b2c3d4-1111-2222-3333-444455556666",
          "first_name": "Jean",
          "last_name": "Dupont",
          "email": "jean.dupont@example.com",
          "initial": "JD",
          "status": "active",
          "role": "b9f3e2a1-0000-1111-2222-333344445555"
        },
        "due_date": "2026-01-14",
        "sort_order": 2,
        "skip_reason": null,
        "closed_by": "a1b2c3d4-1111-2222-3333-444455556666",
        "created_by": "f7c9d0e1-aaaa-bbbb-cccc-ddddeeee0000",
        "action_count": 1,
        "time_spent": 1.5,
        "created_at": "2026-01-13T08:00:00",
        "updated_at": "2026-01-13T15:00:00"
      },
      {
        "id": "661f9511-f3ac-52e5-b827-557766551111",
        "intervention_id": "5ecf60d5-8471-4739-8ba8-0fdad7b51781",
        "label": "Test de remise en service",
        "origin": "plan",
        "status": "in_progress",
        "optional": false,
        "assigned_to": null,
        "due_date": null,
        "sort_order": 3,
        "skip_reason": null,
        "closed_by": null,
        "created_by": "f7c9d0e1-aaaa-bbbb-cccc-ddddeeee0000",
        "action_count": 0,
        "time_spent": 0.0,
        "created_at": "2026-01-13T07:00:00",
        "updated_at": "2026-01-13T15:00:00"
      }
    ],
    "task_progress": {
      "total": 3,
      "done": 2,
      "in_progress": 1,
      "todo": 0,
      "skipped": 0,
      "blocking_pending": 0,
      "is_complete": false
    },
    "status_logs": [
      {
        "id": "88d0e1f2-6789-01bc-def0-123456789012",
        "from_status": null,
        "to_status": "ouvert",
        "changed_by": "f7c9d0e1-aaaa-bbbb-cccc-ddddeeee0000",
        "changed_at": "2026-01-13T08:00:00",
        "note": null
      },
      {
        "id": "99e1f2a3-7890-12cd-ef01-234567890123",
        "from_status": "ouvert",
        "to_status": "en_cours",
        "changed_by": "a1b2c3d4-1111-2222-3333-444455556666",
        "changed_at": "2026-01-13T09:00:00",
        "note": null
      }
    ]
  }
}
```

> **Champs de l'action :**
>
> - `purchase_requests` : demandes d'achat liées à **cette action** via `intervention_action_purchase_request` → [PurchaseRequestListItem](purchase-requests.md)
> - `tasks` : tâches traitées par **cette action** (via `intervention_task.action_id`) → `InterventionTaskOut` complet avec `skip_reason`, `assigned_to`, `closed_by`, `action_count`, `time_spent`
>
> **Champs de `intervention` (contexte parente) :**
>
> - `equipements` : équipement complet avec santé, parent et classe → [EquipementDetail](equipements.md)
> - `request` : demande d'intervention à l'origine de l'intervention → [InterventionRequestListItem](intervention-requests.md)
> - `stats` : statistiques agrégées sur **toutes** les actions de l'intervention
> - `tasks` : **toutes** les tâches de l'intervention (pas uniquement celles de cette action)
> - `task_progress` : avancement global des tâches
> - `status_logs` : historique complet des transitions de statut

### InterventionTaskOut (tâches de l'action)

| Champ            | Type   | Description                                                         |
| ---------------- | ------ | ------------------------------------------------------------------- |
| `id`             | uuid   | ID de la tâche                                                      |
| `intervention_id`| uuid   | Intervention parente                                                |
| `label`          | string | Intitulé de la tâche                                                |
| `status`         | string | `todo`, `in_progress`, `done`, `skipped`                            |
| `origin`         | string | `plan`, `resp`, `tech`                                              |
| `optional`       | bool   | Tâche optionnelle                                                   |
| `assigned_to`    | object | Technicien assigné ([UserListItem](users.md)) — `null` si non assigné |
| `due_date`       | date   | Échéance — `null` si non définie                                    |
| `sort_order`     | int    | Ordre d'affichage dans la liste des tâches                          |
| `skip_reason`    | string | Raison du skip — `null` si non skippée                              |
| `closed_by`      | uuid   | UUID de l'utilisateur qui a clôturé la tâche                        |
| `created_by`     | uuid   | UUID de l'utilisateur qui a créé la tâche                           |
| `action_count`   | int    | Nombre d'actions ayant contribué à cette tâche                      |
| `time_spent`     | float  | Temps total passé sur cette tâche (heures, via l'action liée)       |
| `created_at`     | datetime | Date de création                                                  |
| `updated_at`     | datetime | Date de dernière modification                                     |

> **`InterventionTaskRef`** (version légère) est uniquement utilisé dans `GET /intervention-actions` (liste) où les tâches ne sont pas enrichies pour des raisons de performance.

### InterventionStats

| Champ           | Type  | Description                                         |
| --------------- | ----- | --------------------------------------------------- |
| `action_count`  | int   | Nombre total d'actions sur l'intervention           |
| `total_time`    | float | Temps total cumulé (heures)                         |
| `avg_complexity`| float | Complexité moyenne des actions (`null` si aucune)   |
| `purchase_count`| int   | Nombre de demandes d'achat liées via les actions    |

---

## `POST /intervention-actions`

Ajoute une action à une intervention.

Deux modes exclusifs pour saisir le temps — la logique est gérée par trigger PostgreSQL :

- **Mode bornes** : fournir `action_start` + `action_end` → `time_spent` est calculé automatiquement (ignoré si fourni)
- **Mode direct** : fournir `time_spent` → `action_start`/`action_end` sont ignorés

Fournir les deux ou aucun des deux déclenche une erreur `400` avec le message du trigger.

### Association à des tâches (optionnel)

Fournissez `tasks` (liste) pour tagger une ou plusieurs tâches de l'intervention en même temps que la création de l'action.

**Comportement** :

- Chaque tâche reçoit `action_id = cette_action.id`
- Le trigger DB gère automatiquement `todo → in_progress` au SET action_id
- `close_task=true` clôt la tâche à `done` après liaison
- `skip=true` passe la tâche à `skipped` (mutuellement exclusif avec `close_task`)
- Le `time_spent` est porté par l'action — non divisé entre les tâches

| Champ         | Type   | Description                                                          |
| ------------- | ------ | -------------------------------------------------------------------- |
| `task_id`     | uuid   | ID de la tâche à lier (doit appartenir à la même intervention)       |
| `close_task`  | bool   | Passe la tâche à `done` après liaison. Défaut : `false`              |
| `skip`        | bool   | Passe la tâche à `skipped` — mutuellement exclusif avec `close_task` |
| `skip_reason` | string | Obligatoire si `skip=true`                                           |

### Entrée — mode bornes

```json
{
  "intervention_id": "5ecf60d5-8471-4739-8ba8-0fdad7b51781",
  "action_start": "08:00:00",
  "action_end": "09:30:00",
  "action_subcategory": 30,
  "tech": "a1b2c3d4-...",
  "complexity_score": 7,
  "complexity_factor": "PCE"
}
```

### Entrée — mode direct avec tâches

```json
{
  "intervention_id": "5ecf60d5-8471-4739-8ba8-0fdad7b51781",
  "time_spent": 1.5,
  "action_subcategory": 30,
  "tech": "a1b2c3d4-...",
  "complexity_score": 7,
  "complexity_factor": "PCE",
  "created_at": "2026-01-13T14:30:00",
  "tasks": [
    { "task_id": "550e8400-e29b-41d4-a716-446655440000", "close_task": true },
    {
      "task_id": "661f9511-f3ac-52e5-b827-557766551111",
      "skip": true,
      "skip_reason": "Non nécessaire"
    }
  ]
}
```

### Entrée — mode direct avec note

```json
{
  "intervention_id": "5ecf60d5-8471-4739-8ba8-0fdad7b51781",
  "description": "Roulement remplacé par un SKF 6205 de secours",
  "time_spent": 1.5,
  "action_subcategory": 30,
  "tech": "a1b2c3d4-...",
  "complexity_score": 7,
  "complexity_factor": "PCE",
  "created_at": "2026-01-13T14:30:00"
}
```

| Champ                | Type     | Requis       | Description                                                                                                             |
| -------------------- | -------- | ------------ | ----------------------------------------------------------------------------------------------------------------------- |
| `intervention_id`    | uuid     | **oui**      | Intervention parente                                                                                                    |
| `description`        | string   | non          | Note libre sur l'action (HTML nettoyé)                                                                                  |
| `time_spent`         | float    | conditionnel | Mode direct : quarts d'heure uniquement (0.25, 0.5…). Min: 0.25. Mutuellement exclusif avec `action_start`/`action_end` |
| `action_start`       | time     | conditionnel | Mode bornes : heure de début (HH:MM:SS). Mutuellement exclusif avec `time_spent`                                        |
| `action_end`         | time     | conditionnel | Mode bornes : heure de fin (HH:MM:SS). Doit être > `action_start`                                                       |
| `action_subcategory` | int      | **oui**      | ID de la sous-catégorie                                                                                                 |
| `tech`               | uuid     | **oui**      | Technicien                                                                                                              |
| `complexity_score`   | int      | **oui**      | Score 1-10                                                                                                              |
| `complexity_factor`  | string   | conditionnel | **Requis si score > 5**. Code existant dans [complexity_factors](complexity-factors.md)                                 |
| `created_at`         | datetime | non          | Défaut: `now()`. Permet le backdating                                                                                   |
| `tasks`              | array    | non          | Liste de tâches à tagger (voir tableau ci-dessus). Liste vide interdite                                                 |

### Réponse `201`

Action complète avec sous-catégorie enrichie et champ `tasks` hydraté (liste vide si pas de tâches liées).

### Erreurs

| Code | Cas                                                      |
| ---- | -------------------------------------------------------- |
| 400  | `action_start` et `time_spent` tous les deux fournis     |
| 400  | Ni `action_start`/`action_end` ni `time_spent` fournis   |
| 400  | `action_end` ≤ `action_start`                            |
| 400  | Bornes ou `time_spent` non multiples de 0.25h            |
| 400  | `tasks` est une liste vide                               |
| 400  | `task_id` en double dans le lot `tasks`                  |
| 404  | Une tâche du lot introuvable                             |
| 400  | Une tâche du lot n'appartient pas à la même intervention |
| 400  | Une tâche du lot est déjà clôturée                       |
| 400  | `skip=true` et `close_task=true` simultanés              |
| 400  | `skip=true` sans `skip_reason`                           |

---

## `PATCH /intervention-actions/{id}`

Met à jour partiellement une action existante. Seuls les champs fournis sont modifiés. Tous les champs de saisie sont modifiables, y compris la date (`created_at`) en cas d'erreur.

### Entrée

```json
{
  "description": "Remplacement roulement + graissage",
  "action_start": "08:00:00",
  "action_end": "09:30:00",
  "action_subcategory": 30,
  "tech": "a1b2c3d4-...",
  "complexity_score": 6,
  "complexity_factor": "PCE",
  "created_at": "2026-03-14T08:00:00"
}
```

| Champ                | Type     | Requis       | Description                                                                                                  |
| -------------------- | -------- | ------------ | ------------------------------------------------------------------------------------------------------------ |
| `description`        | string   | non          | Description (HTML nettoyé)                                                                                   |
| `time_spent`         | float    | conditionnel | Mode direct : quarts d'heure uniquement (0.25, 0.5…). Mutuellement exclusif avec `action_start`/`action_end` |
| `action_start`       | time     | conditionnel | Mode bornes : heure de début (HH:MM:SS). Mutuellement exclusif avec `time_spent`                             |
| `action_end`         | time     | conditionnel | Mode bornes : heure de fin (HH:MM:SS). Doit être > `action_start`                                            |
| `action_subcategory` | int      | non          | ID de la sous-catégorie                                                                                      |
| `tech`               | uuid     | non          | Technicien                                                                                                   |
| `complexity_score`   | int      | non          | Score 1-10                                                                                                   |
| `complexity_factor`  | string   | non          | **Obligatoire si le score résultant > 5**. Code dans [complexity_factors](complexity-factors.md)             |
| `created_at`         | datetime | non          | Date de l'action. Modifiable pour corriger une erreur de saisie (backdating)                                 |

> Les règles métier s'appliquent également sur les champs partiels : si `complexity_score > 5` (valeur finale), `complexity_factor` doit être renseigné (valeur courante ou fournie).
>
> `intervention_id` n'est **pas modifiable** via PATCH.

### Réponse `200`

Action complète avec sous-catégorie enrichie (`InterventionActionOut`).
