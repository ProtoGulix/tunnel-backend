# Supplier Order Lines

Lignes de commande fournisseur. Liées aux [Supplier Orders](supplier-orders.md) et aux [Purchase Requests](purchase-requests.md) via table M2M.

> Voir aussi : [Stock Items](stock-items.md) | [Purchase Requests](purchase-requests.md)
>
> Schema partagé : [LinkedPurchaseRequest](../shared-schemas.md#linkedpurchaserequest)

---

## `GET /supplier-order-lines`

Liste avec filtres.

### Query params

| Param | Type | Défaut | Description |
|---|---|---|---|
| `skip` | int | 0 | Offset |
| `limit` | int | 100 | Max: 1000 |
| `supplier_order_id` | uuid | — | Filtrer par commande |
| `stock_item_id` | uuid | — | Filtrer par article |
| `is_selected` | bool | — | Filtrer par sélection |

### Réponse `200` — SupplierOrderLineListItem

```json
[
  {
    "id": "uuid",
    "supplier_order_id": "uuid",
    "stock_item_id": "uuid",
    "stock_item_name": "Roulement SKF 6205",
    "stock_item_ref": "OUT-ROUL-SKF-6205",
    "quantity": 10,
    "unit_price": 12.50,
    "total_price": 125.00,
    "quantity_received": null,
    "is_selected": true,
    "purchase_request_count": 2
  }
]
```

---

## `GET /supplier-order-lines/{id}`

Détail avec `stock_item` et `purchase_requests` enrichis.

### Réponse `200` — SupplierOrderLineOut

```json
{
  "id": "uuid",
  "supplier_order_id": "uuid",
  "stock_item_id": "uuid",
  "stock_item": { "id": "uuid", "name": "Roulement SKF 6205", "ref": "OUT-ROUL-SKF-6205", "..." : "..." },
  "supplier_ref_snapshot": "P-SKF6205",
  "quantity": 10,
  "unit_price": 12.50,
  "total_price": 125.00,
  "quantity_received": null,
  "notes": null,
  "quote_received": true,
  "is_selected": true,
  "quote_price": 11.80,
  "manufacturer": "SKF",
  "manufacturer_ref": "6205-2RS",
  "quote_received_at": "2026-02-01T10:00:00",
  "rejected_reason": null,
  "lead_time_days": 5,
  "purchase_requests": [
    { "id": "uuid", "purchase_request_id": "uuid", "quantity": 5, "item_label": "Roulement SKF 6205", "requester_name": "Jean", "intervention_id": "uuid", "created_at": "..." }
  ],
  "created_at": "2026-01-30T09:00:00",
  "updated_at": "2026-02-01T10:00:00"
}
```

---

## `GET /supplier-order-lines/order/{supplier_order_id}`

Toutes les lignes d'une commande avec détails complets.

---

## `POST /supplier-order-lines`

Crée une ligne.

### Entrée

```json
{
  "supplier_order_id": "uuid",
  "stock_item_id": "uuid",
  "quantity": 10,
  "supplier_ref_snapshot": "P-SKF6205",
  "unit_price": 12.50,
  "notes": null,
  "quote_received": false,
  "is_selected": false,
  "quote_price": null,
  "manufacturer": "SKF",
  "manufacturer_ref": "6205-2RS",
  "quote_received_at": null,
  "rejected_reason": null,
  "lead_time_days": null,
  "purchase_requests": [
    { "purchase_request_id": "uuid", "quantity": 5 }
  ]
}
```

| Champ | Type | Requis | Description |
|---|---|---|---|
| `supplier_order_id` | uuid | oui | Commande parente |
| `stock_item_id` | uuid | oui | Article en stock |
| `quantity` | int | oui | Quantité (> 0) |
| `purchase_requests` | array | non | Liaison aux demandes d'achat (M2M) |

### Règles métier

- `total_price` = `quantity` x `unit_price` (calculé par trigger)
- **Exclusivité de sélection** : quand `is_selected = true`, toutes les autres lignes liées aux mêmes `purchase_requests` sont automatiquement désélectionnées

---

## `PUT /supplier-order-lines/{id}`

Met à jour. Si `purchase_requests` est fourni, les liens existants sont **remplacés**. Même règle d'exclusivité sur `is_selected`.

---

## `DELETE /supplier-order-lines/{id}`

Supprime (cascade M2M). Réponse `204`.

---

## `POST /supplier-order-lines/{id}/purchase-requests`

Lie une demande d'achat à cette ligne.

### Entrée

```json
{ "purchase_request_id": "uuid", "quantity": 5 }
```

> Upsert : met à jour la quantité si le lien existe déjà.

---

## `DELETE /supplier-order-lines/{id}/purchase-requests/{purchase_request_id}`

Supprime le lien avec une demande d'achat.
