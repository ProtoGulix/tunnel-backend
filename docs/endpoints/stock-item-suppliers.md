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
| `unit_price`           | float  | non    | Prix unitaire                                    |
| `min_order_quantity`   | int    | non    | Quantité minimale de commande                    |
| `delivery_time_days`   | int    | non    | Délai de livraison en jours                      |
| `is_preferred`         | bool   | non    | Défaut: false                                    |
| `manufacturer_item_id` | uuid   | non    | Ref fabricant telle que référencée par ce fournisseur (peut différer de celle de l'article) |

### Règles métier

- `stock_item_id` est **obligatoire**
- `supplier_id` est **obligatoire**
- `supplier_ref` doit contenir **au moins 2 caractères** (après trim)
- **Pas de doublons** : la combinaison (`stock_item_id`, `supplier_id`, `supplier_ref`) doit être unique
- **Un seul fournisseur préféré par article** : quand `is_preferred = true`, les autres références du même `stock_item` passent à `false`
- `supplier_refs_count` sur le stock_item est mis à jour par trigger

#### Impact sur le dispatch

Le flag `is_preferred` pilote le comportement du [dispatch automatique](purchase-requests.md#post-purchase-requestsdispatch) :

| Situation | Comportement |
|---|---|
| `is_preferred = true` sur un fournisseur | Dispatch uniquement vers lui (commande directe) |
| Aucun `is_preferred` sur l'article | Dispatch vers tous les fournisseurs (consultation) |
| Aucun fournisseur référencé | Erreur — demande non dispatchée |

### Erreurs

| Code  | Cas                    | Message                                            |
| ----- | ---------------------- | -------------------------------------------------- |
| `400` | stock_item_id manquant | `L'article est obligatoire`                        |
| `400` | supplier_id manquant   | `Le fournisseur est obligatoire`                   |
| `400` | supplier_ref < 2 chars | `La référence doit contenir au moins 2 caractères` |
| `400` | Doublon                | `Cette référence existe déjà pour ce fournisseur`  |

---

## `PUT /stock-item-suppliers/{id}`

Met à jour une référence fournisseur existante. Même règle d'unicité sur `is_preferred`.

### Entrée — champs modifiables

| Champ                  | Type   | Description                   |
| ---------------------- | ------ | ----------------------------- |
| `supplier_ref`         | string | Référence chez le fournisseur |
| `unit_price`           | float  | Prix unitaire                 |
| `min_order_quantity`   | int    | Quantité minimale de commande |
| `delivery_time_days`   | int    | Délai de livraison en jours   |
| `is_preferred`         | bool   | Fournisseur préféré           |
| `manufacturer_item_id` | uuid   | Article fabricant lié         |

> `stock_item_id` et `supplier_id` sont **immutables** après création.

### Erreurs

| Code  | Cas                    | Message                                            |
| ----- | ---------------------- | -------------------------------------------------- |
| `404` | Référence introuvable  | `Référence fournisseur {id} non trouvée`           |
| `400` | supplier_ref < 2 chars | `La référence doit contenir au moins 2 caractères` |
| `400` | Doublon                | `Cette référence existe déjà pour ce fournisseur`  |

---

## `POST /stock-item-suppliers/{id}/set-preferred`

Raccourci pour marquer cette référence comme préférée (désélectionne les autres du même article automatiquement).

### Réponse `200` — StockItemSupplierOut

La référence mise à jour avec `is_preferred: true`.

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

### Réponse `204`
