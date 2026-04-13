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
  "gamme_steps": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "step_id": "660e8400-e29b-41d4-a716-446655440001",
      "step_label": "Diagnostic initial",
      "step_sort_order": 1,
      "step_optional": false,
      "status": "validated",
      "skip_reason": null,
      "validated_at": "2026-01-13T14:35:00",
      "validated_by": "a1b2c3d4-..."
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "step_id": "660e8400-e29b-41d4-a716-446655440002",
      "step_label": "Remplacement pièce",
      "step_sort_order": 2,
      "step_optional": false,
      "status": "validated",
      "skip_reason": null,
      "validated_at": "2026-01-13T15:00:00",
      "validated_by": "a1b2c3d4-..."
    }
  ],
  "created_at": "2026-01-13T14:30:00",
  "updated_at": "2026-01-13T15:00:00"
}
```

> **Schemas imbriqués :**
>
> - `tech` : [UserListItem](users.md#userlistitem) (informations du technicien)
> - `purchase_requests` : tableau de [PurchaseRequestListItem](purchase-requests.md#get-purchase-requestslist-v120) — demandes d'achat liées à cette action via `intervention_action_purchase_request`. `intervention_code` est déduit via la jonction `→ intervention_action → intervention`.
> - `gamme_steps` : tableau de [GammeStepValidationDetail](#gammestepvalidationdetail) — steps de gamme validés/skippés par cette action (liés via `gamme_step_validation.action_id`). Vide si l'action ne valide aucun step.

### GammeStepValidationDetail

| Champ | Type | Description |
|-------|------|-------------|
| `id` | uuid | ID de la validation de step (gamme_step_validation.id) |
| `step_id` | uuid | ID du step de gamme (preventive_plan_gamme_step.id) |
| `step_label` | string | Libellé du step (ex: "Diagnostic initial") |
| `step_sort_order` | int | Ordre d'affichage du step dans la gamme |
| `step_optional` | boolean | Si le step est optionnel |
| `status` | string | `"validated"` ou `"skipped"` |
| `skip_reason` | string \| null | Motif du skip si applicable (null pour validated) |
| `validated_at` | datetime | Date/heure de la validation/skip |
| `validated_by` | uuid | ID du technicien qui a validé |

---

## `POST /intervention-actions`

Ajoute une action à une intervention.

Deux modes exclusifs pour saisir le temps — la logique est gérée par trigger PostgreSQL :

- **Mode bornes** : fournir `action_start` + `action_end` → `time_spent` est calculé automatiquement (ignoré si fourni)
- **Mode direct** : fournir `time_spent` → `action_start`/`action_end` sont ignorés

Fournir les deux ou aucun des deux déclenche une erreur `400` avec le message du trigger.

### Embarquement de la validation de gamme steps (optionnel)

Vous pouvez **valider ou skipper automatiquement plusieurs steps de gamme** lors de la création de l'action, en un seul appel.

Fournissez `gamme_step_validations` (liste d'objets) avec :
- `step_validation_id` : UUID du step à traiter
- `status` : `"validated"` ou `"skipped"`
- `skip_reason` : **Requis si status="skipped"**; ignoré sinon

**Comportement** :
- **Status "validated"** : L'action créée lie ce step (`action_id = new_action.id`), `validated_by = tech`
- **Status "skipped"** : Skip le step avec motif, pas d'action_id, `validated_by = tech`

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

### Entrée — mode direct avec validation de gamme steps

L'exemple ci-dessous crée une action **ET valide 2 steps de gamme + skippe 1 step** en un seul appel :

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
  "gamme_step_validations": [
    {
      "step_validation_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "validated"
    },
    {
      "step_validation_id": "550e8400-e29b-41d4-a716-446655440001",
      "status": "validated"
    },
    {
      "step_validation_id": "550e8400-e29b-41d4-a716-446655440002",
      "status": "skipped",
      "skip_reason": "Pièce de rechange non disponible"
    }
  ]
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
| `gamme_step_validations` | array | non | Liste optionnelle de steps à valider/skipper. Voir schéma ci-dessous |

#### Schéma `GammeStepValidationRequest`

| Champ | Type | Requis | Description |
|-------|------|--------|-------------|
| `step_validation_id` | uuid | oui | ID du gamme_step_validation à traiter |
| `status` | string | oui | `"validated"` ou `"skipped"` |
| `skip_reason` | string | conditionnel | **Requis si status="skipped"**. Raison du skip (non-vide). Ignoré sinon |

### Réponse `201`

Action complète avec sous-catégorie enrichie.

### Erreurs

| Code | Cas                                                    |
| ---- | ------------------------------------------------------ |
| 400  | `action_start` et `time_spent` tous les deux fournis   |
| 400  | Ni `action_start`/`action_end` ni `time_spent` fournis |
| 400  | `action_end` ≤ `action_start`                          |
| 400  | Bornes ou `time_spent` non multiples de 0.25h          |
| 400  | Step dans `gamme_step_validations` inexistant          |
| 400  | Step n'appartient pas à la même intervention           |
| 400  | `skip_reason` vide/whitespace quand status="skipped"   |
| 400  | Step déjà validé/skippé (`status != 'pending'`)        |
| 422  | Validation d'un step échoue (ex: action_id invalide)   |

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
