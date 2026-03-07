# Stock Item Suppliers

Références fournisseurs pour les articles en stock. Table de liaison entre [Stock Items](stock-items.md) et [Suppliers](suppliers.md).

> Voir aussi : [Manufacturer Items](manufacturer-items.md) | [Purchase Requests](purchase-requests.md)

---

## Règles métier globales

### Unicité

- La combinaison (`stock_item_id`, `supplier_id`, `supplier_ref`) doit être **unique**
- `supplier_ref` doit contenir **au moins 2 caractères** (après trim)

### Fournisseur préféré (`is_preferred`)

- **Un seul fournisseur préféré par article** : si un fournisseur préféré existe déjà pour un article, toute tentative de créer ou modifier une autre référence avec `is_preferred = true` est **bloquée** avec une erreur `400`
- Pour **changer** le fournisseur préféré, utiliser exclusivement `POST /{id}/set-preferred` — c'est la seule opération qui transfère le flag d'une référence à une autre
- Pour **supprimer** le fournisseur préféré alors que d'autres fournisseurs existent, définir d'abord un nouvel préféré via `set-preferred`, puis supprimer

#### Impact sur le dispatch

Le flag `is_preferred` pilote le comportement du [dispatch automatique](purchase-requests.md#post-purchase-requestsdispatch) :

| Situation                                | Comportement                                       |
| ---------------------------------------- | -------------------------------------------------- |
| `is_preferred = true` sur un fournisseur | Dispatch uniquement vers lui (commande directe)    |
| Aucun `is_preferred` sur l'article       | Dispatch vers tous les fournisseurs (consultation) |
| Aucun fournisseur référencé              | Erreur — demande non dispatchée                    |

### Intégrité des compteurs

- `supplier_refs_count` sur `stock_item` est mis à jour automatiquement par trigger à chaque INSERT/DELETE sur `stock_item_supplier`

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
    "manufacturer_item": {
      "id": "uuid",
      "manufacturer_name": "SKF",
      "manufacturer_ref": "6205-2RS"
    },
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
  "is_preferred": false,
  "manufacturer_item_id": "uuid"
}
```

| Champ                  | Type   | Requis | Description                                                                                 |
| ---------------------- | ------ | ------ | ------------------------------------------------------------------------------------------- |
| `stock_item_id`        | uuid   | oui    | Article en stock                                                                            |
| `supplier_id`          | uuid   | oui    | Fournisseur                                                                                 |
| `supplier_ref`         | string | oui    | Référence chez le fournisseur (min 2 caractères)                                            |
| `unit_price`           | float  | non    | Prix unitaire                                                                               |
| `min_order_quantity`   | int    | non    | Quantité minimale de commande                                                               |
| `delivery_time_days`   | int    | non    | Délai de livraison en jours                                                                 |
| `is_preferred`         | bool   | non    | Défaut: `false`. Ne peut être `true` que si aucun préféré n'existe déjà pour cet article    |
| `manufacturer_item_id` | uuid   | non    | Ref fabricant telle que référencée par ce fournisseur (peut différer de celle de l'article) |

> Le détail complet de la référence fabricant est retourné en objet embarqué `manufacturer_item` dans toutes les réponses. Voir [Manufacturer Items](manufacturer-items.md).

### Erreurs

| Code  | Cas                                          | Message                                                                                                           |
| ----- | -------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `400` | `stock_item_id` manquant                     | `L'article est obligatoire`                                                                                       |
| `400` | `supplier_id` manquant                       | `Le fournisseur est obligatoire`                                                                                  |
| `400` | `supplier_ref` < 2 chars                     | `La référence doit contenir au moins 2 caractères`                                                                |
| `400` | Doublon `(stock_item, supplier, ref)`        | `Cette référence existe déjà pour ce fournisseur`                                                                 |
| `400` | `is_preferred=true` et préféré déjà existant | `Un fournisseur préféré existe déjà pour cet article. Utilisez POST /{id}/set-preferred pour changer le préféré.` |

---

## `PUT /stock-item-suppliers/{id}`

Met à jour une référence fournisseur existante.

### Champs modifiables

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

| Code  | Cas                                              | Message                                                                                                           |
| ----- | ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| `404` | Référence introuvable                            | `Référence fournisseur {id} non trouvée`                                                                          |
| `400` | `supplier_ref` < 2 chars                         | `La référence doit contenir au moins 2 caractères`                                                                |
| `400` | Doublon `(stock_item, supplier, ref)`            | `Cette référence existe déjà pour ce fournisseur`                                                                 |
| `400` | `is_preferred=true` et un autre préféré existant | `Un fournisseur préféré existe déjà pour cet article. Utilisez POST /{id}/set-preferred pour changer le préféré.` |

---

## `POST /stock-item-suppliers/{id}/set-preferred`

Transfère le flag `is_preferred` vers cette référence. Désélectionne automatiquement l'ancien préféré du même article.

C'est la **seule opération** qui permet de changer le fournisseur préféré d'un article.

### Réponse `200` — StockItemSupplierOut

La référence mise à jour avec `is_preferred: true`.

### Erreurs

| Code  | Cas                   | Message                                  |
| ----- | --------------------- | ---------------------------------------- |
| `404` | Référence introuvable | `Référence fournisseur {id} non trouvée` |

---

## `DELETE /stock-item-suppliers/{id}`

Supprime une référence fournisseur.

### Règle métier

Si la référence est `is_preferred = true` et que d'autres références existent pour le même article, la suppression est **bloquée** : définir d'abord un nouvel préféré via `set-preferred`.

### Erreurs

| Code  | Cas                              | Message                                                      |
| ----- | -------------------------------- | ------------------------------------------------------------ |
| `404` | Référence introuvable            | `Référence fournisseur {id} non trouvée`                     |
| `400` | Préféré avec d'autres références | `Définissez un autre fournisseur préféré avant de supprimer` |

### Réponse `204`
