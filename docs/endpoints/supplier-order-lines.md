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
    "quantity_received": 10,
    "is_fully_received": true,
    "is_consultation": true,
    "consultation_resolved": false,
    "is_selected": null,
    "purchase_request_count": 2
  }
]
```

| Champ | Description |
|---|---|
| `quantity_received` | Quantité physiquement réceptionnée |
| `is_fully_received` | `true` si `quantity_received >= quantity` — calculé dynamiquement |
| `is_consultation` | `true` si la ligne est issue d'un dispatch multi-fournisseurs (aucun préféré) |
| `consultation_resolved` | `true` si une ligne sœur (même DA, autre panier) est sélectionnée — ou si pas de consultation |
| `is_selected` | Ligne retenue pour la commande ferme |
| `purchase_request_count` | Nombre de DA liées |

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
  "is_fully_received": false,
  "is_consultation": true,
  "consultation_resolved": false,
  "notes": null,
  "quote_received": true,
  "is_selected": null,
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

## `PATCH /supplier-order-lines/{id}`

Met à jour partiellement une ligne — seuls les champs fournis sont modifiés.

### Entrée

```json
{ "is_selected": true, "quantity": 2, "unit_price": 10 }
```

| Champ | Type | Description |
|---|---|---|
| `quantity` | int > 0 | Quantité commandée |
| `unit_price` | float | Prix unitaire |
| `quantity_received` | int ≥ 0 | Quantité réceptionnée |
| `is_selected` | bool | Sélectionner cette ligne (désélectionne automatiquement les sœurs) |
| `quote_received` | bool | Devis reçu |
| `quote_price` | float | Prix du devis |
| `manufacturer` | string | Fabricant |
| `manufacturer_ref` | string | Référence fabricant |
| `quote_received_at` | datetime | Date réception devis |
| `rejected_reason` | string | Raison du rejet |
| `lead_time_days` | int | Délai de livraison en jours |
| `supplier_ref_snapshot` | string | Référence fournisseur snapshot |
| `notes` | string | Notes libres |
| `purchase_requests` | array | Remplace les liens DA existants si fourni |

> Règle d'exclusivité : `is_selected = true` désélectionne automatiquement toutes les lignes sœurs liées aux mêmes DA.

---

## `PUT /supplier-order-lines/{id}`

Remplacement complet — `supplier_order_id` et `stock_item_id` requis. Préférer `PATCH` pour les mises à jour partielles.

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
