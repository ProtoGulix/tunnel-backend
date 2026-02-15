# Stock Items

Catalogue d'articles en stock. La référence (`ref`) est auto-générée par trigger base de données.

> Voir aussi : [Stock Item Suppliers](stock-item-suppliers.md) | [Purchase Requests](purchase-requests.md)
>
> Schema partagé : [StockItemListItem](../shared-schemas.md#stockitemlistitem)

---

## `GET /stock_items`

Liste les articles avec filtres.

### Query params

| Param | Type | Défaut | Description |
|---|---|---|---|
| `skip` | int | 0 | Offset |
| `limit` | int | 100 | Max: 1000 |
| `family_code` | string | — | Filtrer par famille |
| `sub_family_code` | string | — | Filtrer par sous-famille |
| `search` | string | — | Recherche nom ou référence (ILIKE) |

### Réponse `200` — StockItemListItem

Tableau trié par nom ASC. Schema léger (voir [StockItemListItem](../shared-schemas.md#stockitemlistitem)).

---

## `GET /stock_items/{id}`

Détail complet.

### Réponse `200` — StockItemOut

```json
{
  "id": "uuid",
  "name": "Roulement SKF 6205",
  "family_code": "OUT",
  "sub_family_code": "ROUL",
  "spec": "SKF",
  "dimension": "6205",
  "ref": "OUT-ROUL-SKF-6205",
  "quantity": 15,
  "unit": "pcs",
  "location": "Étagère A3",
  "standars_spec": null,
  "supplier_refs_count": 2,
  "manufacturer_item_id": "uuid"
}
```

---

## `GET /stock_items/ref/{ref}`

Recherche par référence (ex: `OUT-ROUL-SKF-6205`).

---

## `POST /stock_items`

Crée un article.

### Entrée

```json
{
  "name": "Roulement SKF 6205",
  "family_code": "OUT",
  "sub_family_code": "ROUL",
  "dimension": "6205",
  "spec": "SKF",
  "quantity": 15,
  "unit": "pcs",
  "location": "Étagère A3",
  "standars_spec": null,
  "manufacturer_item_id": null
}
```

| Champ | Type | Requis | Description |
|---|---|---|---|
| `name` | string | oui | Nom de l'article |
| `family_code` | string | oui | Code famille (max 20) |
| `sub_family_code` | string | oui | Code sous-famille (max 20) |
| `dimension` | string | oui | Dimension |
| `spec` | string | non | Spécification (max 50) |
| `quantity` | int | non | Défaut: 0 |
| `unit` | string | non | Unité (max 50) |
| `location` | string | non | Emplacement |
| `manufacturer_item_id` | uuid | non | Article fabricant lié |

### Règles métier

- `ref` est auto-générée par trigger : `{family_code}-{sub_family_code}-{spec}-{dimension}`
- `supplier_refs_count` est géré par trigger

---

## `PUT /stock_items/{id}`

Met à jour. Si `family_code`, `sub_family_code`, `spec` ou `dimension` changent, `ref` est régénérée.

---

## `PATCH /stock_items/{id}/quantity`

Mise à jour rapide de la quantité uniquement.

### Entrée

```json
{ "quantity": 20 }
```

---

## `DELETE /stock_items/{id}`

Supprime un article. Réponse `204`.
