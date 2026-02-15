# Stock Item Suppliers

Références fournisseurs pour les articles en stock. Table de liaison entre [Stock Items](stock-items.md) et [Suppliers](suppliers.md).

---

## `GET /stock_item_suppliers`

Liste les références avec filtres.

### Query params

| Param | Type | Défaut | Description |
|---|---|---|---|
| `skip` | int | 0 | Offset |
| `limit` | int | 100 | Max: 1000 |
| `stock_item_id` | uuid | — | Filtrer par article |
| `supplier_id` | uuid | — | Filtrer par fournisseur |
| `is_preferred` | bool | — | Filtrer par fournisseur préféré |

### Réponse `200` — StockItemSupplierListItem

```json
[
  {
    "id": "uuid",
    "stock_item_id": "uuid",
    "supplier_id": "uuid",
    "supplier_ref": "P1115070",
    "unit_price": 12.50,
    "min_order_quantity": 5,
    "delivery_time_days": 3,
    "is_preferred": true,
    "stock_item_name": "Foret pilote D7",
    "stock_item_ref": "OUT-COUP-FORET-PILOTE-D7",
    "supplier_name": "PONS & SABOT",
    "supplier_code": "PS"
  }
]
```

Trié par `is_preferred` DESC, nom fournisseur ASC.

---

## `GET /stock_item_suppliers/{id}`

Détail complet (StockItemSupplierOut) avec timestamps.

---

## `GET /stock_item_suppliers/stock_item/{stock_item_id}`

Tous les fournisseurs d'un article.

---

## `GET /stock_item_suppliers/supplier/{supplier_id}`

Tous les articles d'un fournisseur.

---

## `POST /stock_item_suppliers`

Crée une référence fournisseur.

### Entrée

```json
{
  "stock_item_id": "uuid",
  "supplier_id": "uuid",
  "supplier_ref": "P1115070",
  "unit_price": 12.50,
  "min_order_quantity": 5,
  "delivery_time_days": 3,
  "is_preferred": true,
  "manufacturer_item_id": "uuid"
}
```

| Champ | Type | Requis | Description |
|---|---|---|---|
| `stock_item_id` | uuid | oui | Article en stock |
| `supplier_id` | uuid | oui | Fournisseur |
| `supplier_ref` | string | oui | Référence chez le fournisseur |
| `is_preferred` | bool | non | Défaut: false |
| `manufacturer_item_id` | uuid | non | Article fabricant lié |

### Règles métier

- Contrainte d'unicité sur (`stock_item_id`, `supplier_id`)
- **Un seul fournisseur préféré par article** : quand `is_preferred = true`, les autres références du même `stock_item` passent à `false`
- `supplier_refs_count` sur le stock_item est mis à jour par trigger

---

## `PUT /stock_item_suppliers/{id}`

Met à jour. Même règle `is_preferred`.

---

## `POST /stock_item_suppliers/{id}/set_preferred`

Raccourci pour marquer cette référence comme préférée (désélectionne les autres automatiquement).

---

## `DELETE /stock_item_suppliers/{id}`

Supprime. Réponse `204`.
