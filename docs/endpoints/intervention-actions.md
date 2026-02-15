# Intervention Actions

Actions réalisées sur une intervention (réparation, diagnostic, etc.). Chaque action est liée à un technicien, une sous-catégorie et peut avoir des demandes d'achat.

> Voir aussi : [Interventions](interventions.md) | [Action Categories](action-categories.md) | [Complexity Factors](complexity-factors.md) | [Purchase Requests](purchase-requests.md)

---

## `GET /intervention_actions`

Liste toutes les actions d'intervention.

### Query params

| Param | Type | Défaut |
|---|---|---|
| `skip` | int | 0 |
| `limit` | int | 100 (max: 1000) |

---

## `GET /intervention_actions/{id}`

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
  "tech": "uuid",
  "complexity_score": 7,
  "complexity_factor": "PCE",
  "purchase_requests": [],
  "created_at": "2026-01-13T14:30:00",
  "updated_at": "2026-01-13T15:00:00"
}
```

> `purchase_requests` : tableau de [PurchaseRequestOut](purchase-requests.md#purchaserequestout)

---

## `POST /intervention_actions`

Ajoute une action à une intervention.

### Entrée

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

| Champ | Type | Requis | Description |
|---|---|---|---|
| `intervention_id` | uuid | oui | Intervention parente |
| `description` | string | oui | Description (HTML nettoyé) |
| `time_spent` | float | oui | Quarts d'heure uniquement : 0.25, 0.5, 0.75, 1.0... Min: 0.25 |
| `action_subcategory` | int | oui | ID de la sous-catégorie |
| `tech` | uuid | oui | Technicien |
| `complexity_score` | int | oui | Score 1-10 |
| `complexity_factor` | string | conditionnel | **Requis si score > 5**. Code existant dans [complexity_factors](complexity-factors.md) |
| `created_at` | datetime | non | Défaut: `now()`. Permet le backdating |

### Réponse `201`

Action complète avec sous-catégorie enrichie.
