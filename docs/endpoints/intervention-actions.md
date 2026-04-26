# Intervention Actions

Actions réalisées sur une intervention (réparation, diagnostic, etc.). Chaque action est liée à un technicien, une sous-catégorie et peut avoir des demandes d'achat.

> Voir aussi : [Interventions](interventions.md) | [Action Categories](action-categories.md) | [Complexity Factors](complexity-factors.md) | [Purchase Requests](purchase-requests.md)

---

## `GET /intervention-actions`

Liste les actions groupées par date (`created_at::date`), du plus récent au plus ancien. À l'intérieur de chaque jour, les actions sont triées par heure croissante.

### Query params

| Param        | Type | Défaut      | Description                               |
| ------------ | ---- | ----------- | ----------------------------------------- |
| `start_date` | date | aujourd'hui | Date de début incluse (ex: `2026-03-10`)  |
| `end_date`   | date | aujourd'hui | Date de fin incluse (ex: `2026-03-15`)    |
| `tech_id`    | uuid | —           | Filtre sur le technicien                  |

> Sans paramètre, retourne uniquement les actions du jour. Pour une semaine : `start_date=2026-03-10&end_date=2026-03-15`.

### Réponse `200`

```json
[
  {
    "date": "2026-03-15",
    "actions": [
      {
        "id": "uuid",
        "intervention_id": "uuid",
        "intervention": {
          "id": "uuid",
          "code": "CN001-REA-20260315-QC",
          "title": "Remplacement roulement principal",
          "status_actual": "en_cours",
          "equipement_id": "uuid",
          "equipement_code": "EQ-001",
          "equipement_name": "Scie principale"
        },
        "description": "Diagnostic complet",
        "time_spent": 1.5,
        "subcategory": { "id": 30, "name": "Remplacement pièce", "code": "DEP_REM", "category": { "..." } },
        "tech": { "..." },
        "complexity_score": 5,
        "complexity_factor": null,
        "action_start": "08:00:00",
        "action_end": "09:30:00",
        "purchase_requests": [],
        "created_at": "2026-03-15T08:00:00",
        "updated_at": "2026-03-15T08:00:00"
      }
    ]
  },
  {
    "date": "2026-03-14",
    "actions": [ { "..." } ]
  }
]
```

---

## `GET /intervention-actions/{id}`

Détail d'une action avec sous-catégorie et demandes d'achat.

### Réponse `200` — InterventionActionOut

```json
{
  "id": "uuid",
  "intervention_id": "uuid",
  "description": "Remplacement du roulement SKF 6205",
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
    "id": "a1b2c3d4-...",
    "first_name": "Jean",
    "last_name": "Dupont",
    "email": "jean.dupont@example.com",
    "initial": "JD",
    "status": "active",
    "role": "uuid"
  },
  "complexity_score": 7,
  "complexity_factor": "PCE",
  "action_start": "08:00:00",
  "action_end": "09:30:00",
  "purchase_requests": [
    {
      "id": "uuid",
      "item_label": "Roulement SKF 6205",
      "quantity": 2,
      "unit": "pcs",
      "derived_status": {
        "code": "PENDING_DISPATCH",
        "label": "À dispatcher",
        "color": "#A855F7"
      },
      "stock_item_id": "uuid",
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
  "task": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "label": "Diagnostic initial",
    "status": "in_progress",
    "origin": "plan"
  },
  "created_at": "2026-01-13T14:30:00",
  "updated_at": "2026-01-13T15:00:00"
}
```

> **Schemas imbriqués :**
>
> - `tech` : [UserListItem](users.md#userlistitem) (informations du technicien)
> - `purchase_requests` : tableau de [PurchaseRequestListItem](purchase-requests.md#get-purchase-requestslist-v120) — demandes d'achat liées à cette action via `intervention_action_purchase_request`. `intervention_code` est déduit via la jonction `→ intervention_action → intervention`.
> - `task` : objet [InterventionTaskRef](#interventiontaskref) — tâche liée à cette action (via `intervention_action.task_id`). `null` si l'action n'est pas liée à une tâche.

### InterventionTaskRef

| Champ | Type | Description |
|-------|------|-------------|
| `id` | uuid | ID de la tâche |
| `label` | string | Intitulé de la tâche |
| `status` | string | `todo`, `in_progress`, `done`, `skipped` |
| `origin` | string | `plan`, `resp`, `tech` |

---

## `POST /intervention-actions`

Ajoute une action à une intervention.

Deux modes exclusifs pour saisir le temps — la logique est gérée par trigger PostgreSQL :

- **Mode bornes** : fournir `action_start` + `action_end` → `time_spent` est calculé automatiquement (ignoré si fourni)
- **Mode direct** : fournir `time_spent` → `action_start`/`action_end` sont ignorés

Fournir les deux ou aucun des deux déclenche une erreur `400` avec le message du trigger.

### Lien optionnel à une tâche

Vous pouvez **lier l'action à une tâche** en fournissant `task_id`. La tâche doit appartenir à la même intervention.

**Comportement** :
- La tâche est liée à l'action via `intervention_action.task_id`
- Si la tâche est en `todo`, elle passe automatiquement en `in_progress`

### Entrée — mode bornes

```json
{
  "intervention_id": "5ecf60d5-8471-4739-8ba8-0fdad7b51781",
  "description": "Remplacement du roulement SKF 6205",
  "action_start": "08:00:00",
  "action_end": "09:30:00",
  "action_subcategory": 30,
  "tech": "a1b2c3d4-...",
  "complexity_score": 7,
  "complexity_factor": "PCE"
}
```

### Entrée — mode direct

```json
{
  "intervention_id": "5ecf60d5-8471-4739-8ba8-0fdad7b51781",
  "description": "Remplacement du roulement SKF 6205",
  "time_spent": 1.5,
  "action_subcategory": 30,
  "tech": "a1b2c3d4-...",
  "complexity_score": 7,
  "complexity_factor": "PCE",
  "created_at": "2026-01-13T14:30:00"
}
```

### Entrée — mode direct avec lien à une tâche

```json
{
  "intervention_id": "5ecf60d5-8471-4739-8ba8-0fdad7b51781",
  "description": "Remplacement du roulement SKF 6205",
  "time_spent": 1.5,
  "action_subcategory": 30,
  "tech": "a1b2c3d4-...",
  "complexity_score": 7,
  "complexity_factor": "PCE",
  "created_at": "2026-01-13T14:30:00",
  "task_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

| Champ                | Type     | Requis       | Description                                                                                                             |
| -------------------- | -------- | ------------ | ----------------------------------------------------------------------------------------------------------------------- |
| `intervention_id`    | uuid     | oui          | Intervention parente                                                                                                    |
| `description`        | string   | oui          | Description (HTML nettoyé)                                                                                              |
| `time_spent`         | float    | conditionnel | Mode direct : quarts d'heure uniquement (0.25, 0.5…). Min: 0.25. Mutuellement exclusif avec `action_start`/`action_end` |
| `action_start`       | time     | conditionnel | Mode bornes : heure de début (HH:MM:SS). Mutuellement exclusif avec `time_spent`                                        |
| `action_end`         | time     | conditionnel | Mode bornes : heure de fin (HH:MM:SS). Doit être > `action_start`                                                       |
| `action_subcategory` | int      | oui          | ID de la sous-catégorie                                                                                                 |
| `tech`               | uuid     | oui          | Technicien                                                                                                              |
| `complexity_score`   | int      | oui          | Score 1-10                                                                                                              |
| `complexity_factor`  | string   | conditionnel | **Requis si score > 5**. Code existant dans [complexity_factors](complexity-factors.md)                                 |
| `created_at`         | datetime | non          | Défaut: `now()`. Permet le backdating                                                                                   |
| `task_id`            | uuid     | non          | ID d'une tâche à lier (doit appartenir à la même intervention)                                                         |

### Réponse `201`

Action complète avec sous-catégorie enrichie et champ `task` hydraté si `task_id` fourni.

### Erreurs

| Code | Cas                                                    |
| ---- | ------------------------------------------------------ |
| 400  | `action_start` et `time_spent` tous les deux fournis   |
| 400  | Ni `action_start`/`action_end` ni `time_spent` fournis |
| 400  | `action_end` ≤ `action_start`                          |
| 400  | Bornes ou `time_spent` non multiples de 0.25h          |
| 400  | `task_id` introuvable                                  |
| 400  | La tâche n'appartient pas à la même intervention       |

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

| Champ                | Type     | Requis       | Description                                                                                                              |
| -------------------- | -------- | ------------ | ------------------------------------------------------------------------------------------------------------------------ |
| `description`        | string   | non          | Description (HTML nettoyé)                                                                                               |
| `time_spent`         | float    | conditionnel | Mode direct : quarts d'heure uniquement (0.25, 0.5…). Mutuellement exclusif avec `action_start`/`action_end`             |
| `action_start`       | time     | conditionnel | Mode bornes : heure de début (HH:MM:SS). Mutuellement exclusif avec `time_spent`                                         |
| `action_end`         | time     | conditionnel | Mode bornes : heure de fin (HH:MM:SS). Doit être > `action_start`                                                        |
| `action_subcategory` | int      | non          | ID de la sous-catégorie                                                                                                  |
| `tech`               | uuid     | non          | Technicien                                                                                                               |
| `complexity_score`   | int      | non          | Score 1-10                                                                                                               |
| `complexity_factor`  | string   | non          | **Obligatoire si le score résultant > 5**. Code dans [complexity_factors](complexity-factors.md)                         |
| `created_at`         | datetime | non          | Date de l'action. Modifiable pour corriger une erreur de saisie (backdating)                                             |

> Les règles métier s'appliquent également sur les champs partiels : si `complexity_score > 5` (valeur finale), `complexity_factor` doit être renseigné (valeur courante ou fournie).
>
> `intervention_id` n'est **pas modifiable** via PATCH.

### Réponse `200`

Action complète avec sous-catégorie enrichie (`InterventionActionOut`).
