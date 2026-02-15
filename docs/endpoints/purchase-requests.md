# Purchase Requests

Demandes d'achat de matériel, liées aux interventions et aux commandes fournisseurs. Le statut est **calculé automatiquement** ([DerivedStatus](../shared-schemas.md#derivedstatus)).

> Voir aussi : [Interventions](interventions.md) | [Stock Items](stock-items.md) | [Supplier Orders](supplier-orders.md) | [Supplier Order Lines](supplier-order-lines.md)

---

## `GET /purchase_requests` [LEGACY]

Liste toutes les demandes d'achat avec filtres.

### Query params

| Param | Type | Défaut | Description |
|---|---|---|---|
| `skip` | int | 0 | Offset |
| `limit` | int | 100 | Max: 1000 |
| `status` | string | — | Filtrer par [DerivedStatus](../shared-schemas.md#derivedstatus) |
| `intervention_id` | uuid | — | Filtrer par intervention |
| `urgency` | string | — | `normal`, `high`, `critical` |

### Réponse `200` — PurchaseRequestOut

```json
[
  {
    "id": "uuid",
    "derived_status": { "code": "PENDING_DISPATCH", "label": "À dispatcher", "color": "#f59e0b" },
    "stock_item_id": "uuid",
    "stock_item": { "id": "uuid", "name": "Roulement SKF 6205", "ref": "OUT-ROUL-SKF-6205", "..." : "..." },
    "item_label": "Roulement SKF 6205",
    "quantity": 2,
    "unit": "pcs",
    "requested_by": "Jean Dupont",
    "urgency": "high",
    "reason": "Remplacement urgent",
    "notes": null,
    "workshop": "Atelier 1",
    "intervention_id": "uuid",
    "intervention": {
      "id": "uuid", "code": "CN001-REA-20260113-QC", "title": "Remplacement roulement",
      "priority": "urgent", "status_actual": "en_cours",
      "equipement": { "id": "uuid", "code": "EQ-001", "name": "Scie principale" }
    },
    "quantity_requested": 2,
    "quantity_approved": null,
    "urgent": true,
    "requester_name": "Jean Dupont",
    "approver_name": null,
    "approved_at": null,
    "order_lines": [],
    "created_at": "2026-01-13T10:00:00",
    "updated_at": "2026-01-13T10:00:00"
  }
]
```

> `stock_item` : [StockItemListItem](../shared-schemas.md#stockitemlistitem) — hydraté si `stock_item_id` non null
>
> `intervention` : [InterventionInfo](../shared-schemas.md#interventioninfo) — hydraté si `intervention_id` non null
>
> `order_lines` : tableau de [LinkedOrderLine](../shared-schemas.md#linkedorderline)

---

## `GET /purchase_requests/list` [v1.2.0]

Liste optimisée légère pour tableaux. Payload ~95% plus léger.

### Réponse `200` — PurchaseRequestListItem

```json
[
  {
    "id": "uuid",
    "item_label": "Roulement SKF 6205",
    "quantity": 2,
    "unit": "pcs",
    "derived_status": { "code": "PENDING_DISPATCH", "label": "À dispatcher", "color": "#f59e0b" },
    "stock_item_id": "uuid",
    "stock_item_ref": "OUT-ROUL-SKF-6205",
    "stock_item_name": "Roulement SKF 6205",
    "intervention_code": "CN001-REA-20260113-QC",
    "requester_name": "Jean Dupont",
    "urgency": "high",
    "urgent": true,
    "quotes_count": 0,
    "selected_count": 0,
    "suppliers_count": 2,
    "created_at": "2026-01-13T10:00:00",
    "updated_at": "2026-01-13T10:00:00"
  }
]
```

---

## `GET /purchase_requests/detail/{id}` [v1.2.0]

Détail complet avec contexte enrichi.

### Réponse `200` — PurchaseRequestDetail

Même structure que PurchaseRequestOut avec toutes les relations hydratées.

---

## `GET /purchase_requests/stats` [v1.2.0]

Statistiques agrégées pour dashboards.

### Query params

| Param | Type | Description |
|---|---|---|
| `start_date` | date | Début (défaut: 3 mois) |
| `end_date` | date | Fin (défaut: aujourd'hui) |
| `group_by` | string | Regroupement |

### Réponse `200`

```json
{
  "period": { "start_date": "2025-11-15", "end_date": "2026-02-15" },
  "totals": { "total_requests": 45, "urgent_count": 8 },
  "by_status": [
    { "status": "PENDING_DISPATCH", "count": 12, "label": "À dispatcher", "color": "#f59e0b" }
  ],
  "by_urgency": [
    { "urgency": "normal", "count": 30 },
    { "urgency": "high", "count": 8 }
  ],
  "top_items": [
    { "item_label": "Roulement SKF 6205", "stock_item_ref": "OUT-ROUL-SKF-6205", "request_count": 5, "total_quantity": 12 }
  ]
}
```

---

## `GET /purchase_requests/{id}` [LEGACY]

Détail d'une demande par ID.

---

## `GET /purchase_requests/intervention/{intervention_id}` [LEGACY]

Demandes liées à une intervention.

---

## `GET /purchase_requests/intervention/{intervention_id}/optimized` [v1.2.0]

Filtre par intervention avec choix de granularité.

### Query params

| Param | Type | Description |
|---|---|---|
| `view` | string | `list` (léger) ou `full` (complet) |

---

## `POST /purchase_requests`

Crée une demande d'achat.

### Entrée

```json
{
  "item_label": "Roulement SKF 6205",
  "quantity": 2,
  "stock_item_id": "uuid",
  "unit": "pcs",
  "requested_by": "Jean Dupont",
  "urgency": "high",
  "reason": "Remplacement urgent",
  "notes": null,
  "workshop": "Atelier 1",
  "intervention_id": "uuid",
  "quantity_requested": 2,
  "urgent": true,
  "requester_name": "Jean Dupont"
}
```

| Champ | Type | Requis | Description |
|---|---|---|---|
| `item_label` | string | oui | Libellé de l'article |
| `quantity` | int | oui | Quantité (> 0) |
| `stock_item_id` | uuid | non | Article stock normalisé |
| `unit` | string | non | Unité (pcs, m, kg, etc.) |
| `intervention_id` | uuid | non | Intervention liée |
| `urgent` | bool | non | Défaut: false |
| `requester_name` | string | non | Nom du demandeur |

### Règles métier

- `item_label` et `quantity` sont requis
- `quantity` doit être > 0
- `derived_status` est calculé automatiquement (voir [DerivedStatus](../shared-schemas.md#derivedstatus))

---

## `PUT /purchase_requests/{id}`

Met à jour une demande. Champs supplémentaires modifiables : `quantity_approved`, `approver_name`, `approved_at`.

> `status` n'est plus modifiable manuellement.

---

## `DELETE /purchase_requests/{id}`

Supprime une demande. Réponse `204`.

---

## `POST /purchase_requests/dispatch` [v1.2.12]

Dispatch automatique des demandes `PENDING_DISPATCH` vers des [Supplier Orders](supplier-orders.md).

### Règles métier

1. Pour chaque demande PENDING_DISPATCH, récupère les fournisseurs liés au `stock_item`
2. Trouve ou crée un supplier_order OPEN par fournisseur
3. Crée les [Supplier Order Lines](supplier-order-lines.md) liées

### Réponse `200`

```json
{
  "dispatched_count": 5,
  "created_orders": 2,
  "errors": [
    { "purchase_request_id": "uuid", "error": "Aucun fournisseur référencé" }
  ]
}
```
