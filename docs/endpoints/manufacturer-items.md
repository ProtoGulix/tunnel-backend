# Manufacturer Items

Références fabricants/constructeurs. Chaque référence fournisseur (`stock-item-suppliers`) peut être liée à une référence fabricant.

> Voir aussi : [Stock Item Suppliers](stock-item-suppliers.md) | [Stock Items](stock-items.md)

---

## `GET /manufacturer-items`

Liste toutes les références fabricants.

### Query params

| Param    | Type   | Défaut | Description                                                       |
| -------- | ------ | ------ | ----------------------------------------------------------------- |
| `skip`   | int    | 0      | Offset                                                            |
| `limit`  | int    | 100    | Max: 1000                                                         |
| `search` | string | —      | Recherche (nom fabricant **ou** référence, insensible à la casse) |

### Réponse `200` — PaginatedResponse

```json
{
  "items": [
    {
      "id": "uuid",
      "manufacturer_name": "SKF",
      "manufacturer_ref": "6205-2RS"
    }
  ],
  "pagination": {
    "total": 42,
    "page": 1,
    "page_size": 100,
    "total_pages": 1,
    "offset": 0,
    "count": 42
  }
}
```

Trié par `manufacturer_name` ASC. La recherche `search` filtre simultanément sur `manufacturer_name` et `manufacturer_ref`.

---

## `GET /manufacturer-items/{id}`

Détail d'une référence fabricant avec toutes les références fournisseurs qui l'utilisent.

### Réponse `200` — ManufacturerItemDetail

```json
{
  "id": "uuid",
  "manufacturer_name": "SKF",
  "manufacturer_ref": "6205-2RS",
  "supplier_items": [
    {
      "id": "uuid",
      "supplier_ref": "P1115070",
      "unit_price": 4.2,
      "min_order_quantity": 10,
      "delivery_time_days": 3,
      "is_preferred": true,
      "stock_item_name": "Roulement à billes 6205",
      "stock_item_ref": "MEC-ROUL-6205",
      "supplier_name": "PONS & SABOT",
      "supplier_code": "PS"
    }
  ]
}
```

### Erreurs

| Code | Cas                   |
| ---- | --------------------- |
| 404  | Référence introuvable |

---

## `POST /manufacturer-items`

Crée une nouvelle référence fabricant.

### Entrée

```json
{
  "manufacturer_name": "SKF",
  "manufacturer_ref": "6205-2RS",
  "notes": "Roulement à billes rangée simple"
}
```

| Champ               | Type   | Requis | Description                      |
| ------------------- | ------ | ------ | -------------------------------- |
| `manufacturer_name` | string | oui    | Nom du fabricant/constructeur    |
| `manufacturer_ref`  | string | non    | Référence catalogue du fabricant |

### Réponse `201` — ManufacturerItemOut

---

## `PATCH /manufacturer-items/{id}`

Met à jour partiellement une référence fabricant.

### Entrée — champs modifiables

| Champ               | Type   | Description                      |
| ------------------- | ------ | -------------------------------- |
| `manufacturer_name` | string | Nom du fabricant                 |
| `manufacturer_ref`  | string | Référence catalogue du fabricant |

### Réponse `200` — ManufacturerItemOut

---

## `DELETE /manufacturer-items/{id}`

Supprime une référence fabricant.

### Réponse `204`

Pas de contenu.

### Erreurs

| Code | Cas                   |
| ---- | --------------------- |
| 404  | Référence introuvable |

---

## Schémas

### ManufacturerItemOut

Utilisé dans la liste et en objet embarqué dans `StockItemSupplierOut`.

```json
{
  "id": "uuid",
  "manufacturer_name": "string",
  "manufacturer_ref": "string | null"
}
```

### ManufacturerItemDetail

Retourné par `GET /manufacturer-items/{id}`. Hérite de `ManufacturerItemOut` et ajoute :

```json
{
  "id": "uuid",
  "manufacturer_name": "string",
  "manufacturer_ref": "string | null",
  "supplier_items": [
    {
      "id": "uuid",
      "supplier_ref": "string",
      "unit_price": "float | null",
      "min_order_quantity": "int",
      "delivery_time_days": "int | null",
      "is_preferred": "bool",
      "stock_item_name": "string | null",
      "stock_item_ref": "string | null",
      "supplier_name": "string | null",
      "supplier_code": "string | null"
    }
  ]
}
```

Trié par `supplier_name` ASC, `supplier_ref` ASC.
