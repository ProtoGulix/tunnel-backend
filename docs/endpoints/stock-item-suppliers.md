# Stock Item Suppliers

Références fournisseurs pour les articles en stock. Table de liaison entre [Stock Items](stock-items.md) et [Suppliers](suppliers.md).

---

## `GET /stock-item-suppliers`

Liste les références avec filtres.

### Query params

| Param           | Type | Défaut | Description                     |
| --------------- | ---- | ------ | ------------------------------- |
| `skip`          | int  | 0      | Offset                          |
| `limit`         | int  | 100    | Max: 1000                       |
| `stock_item_id` | uuid | —      | Filtrer par article             |
| `supplier_id`   | uuid | —      | Filtrer par fournisseur         |
| `is_preferred`  | bool | —      | Filtrer par fournisseur préféré |

### Réponse `200` — StockItemSupplierListItem

```json
[
  {
    "id": "uuid",
    "stock_item_id": "uuid",
    "supplier_id": "uuid",
    "supplier_ref": "P1115070",
    "unit_price": 12.5,
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

## `GET /stock-item-suppliers/{id}`

Détail complet (StockItemSupplierOut) avec timestamps.

---

## `GET /stock-item-suppliers/stock-item/{stock_item_id}`

Tous les fournisseurs d'un article.

---

## `GET /stock-item-suppliers/supplier/{supplier_id}`

Tous les articles d'un fournisseur.

---

## `POST /stock-item-suppliers`

Crée une référence fournisseur.

### Entrée

```json
{
  "stock_item_id": "uuid",
  "supplier_id": "uuid",
  "supplier_ref": "P1115070",
  "unit_price": 12.5,
  "min_order_quantity": 5,
  "delivery_time_days": 3,
  "is_preferred": true,
  "manufacturer_item_id": "uuid"
}
```

| Champ                  | Type   | Requis | Description                                      |
| ---------------------- | ------ | ------ | ------------------------------------------------ |
| `stock_item_id`        | uuid   | oui    | Article en stock                                 |
| `supplier_id`          | uuid   | oui    | Fournisseur                                      |
| `supplier_ref`         | string | oui    | Référence chez le fournisseur (min 2 caractères) |
| `is_preferred`         | bool   | non    | Défaut: false                                    |
| `manufacturer_item_id` | uuid   | non    | Article fabricant lié                            |

### Règles métier

- `stock_item_id` est **obligatoire**
- `supplier_id` est **obligatoire**
- `supplier_ref` doit contenir **au moins 2 caractères** (après trim)
- **Pas de doublons** : la combinaison (`stock_item_id`, `supplier_id`, `supplier_ref`) doit être unique
- **Un seul fournisseur préféré par article** : quand `is_preferred = true`, les autres références du même `stock_item` passent à `false`
- `supplier_refs_count` sur le stock_item est mis à jour par trigger

### Erreurs

| Code  | Cas                    | Message                                            |
| ----- | ---------------------- | -------------------------------------------------- |
| `400` | stock_item_id manquant | `L'article est obligatoire`                        |
| `400` | supplier_id manquant   | `Le fournisseur est obligatoire`                   |
| `400` | supplier_ref < 2 chars | `La référence doit contenir au moins 2 caractères` |
| `400` | Doublon                | `Cette référence existe déjà pour ce fournisseur`  |

---

## `DELETE /stock-item-suppliers/{id}`

Supprime une référence fournisseur.

### Règle métier

- **Protection fournisseur préféré** : Si la référence est marquée `is_preferred = true` et qu'il existe d'autres références pour le même article, la suppression est **bloquée**
- Il faut d'abord définir un autre fournisseur comme préféré avant de supprimer l'actuel

### Erreurs

| Code  | Cas                       | Message                                                      |
| ----- | ------------------------- | ------------------------------------------------------------ |
| `404` | Référence introuvable     | `Référence fournisseur {id} non trouvée`                     |
| `400` | Préféré avec alternatives | `Définissez un autre fournisseur préféré avant de supprimer` |

### Réponse `200`

```json
{
  "message": "Référence {id} supprimée"
}
```

Met à jour. Même règle `is_preferred`.

---

## `POST /stock-item-suppliers/{id}/set-preferred`

Raccourci pour marquer cette référence comme préférée (désélectionne les autres automatiquement).

---

## `DELETE /stock-item-suppliers/{id}`

Supprime. Réponse `204`.
