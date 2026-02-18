# Supplier Orders

Commandes fournisseurs avec suivi d'âge, lignes de commande et exports (CSV, email).

> Voir aussi : [Supplier Order Lines](supplier-order-lines.md) | [Suppliers](suppliers.md) | [Purchase Requests](purchase-requests.md)

---

## `GET /supplier-orders`

Liste les commandes avec filtres.

### Query params

| Param | Type | Défaut | Description |
|---|---|---|---|
| `skip` | int | 0 | Offset |
| `limit` | int | 100 | Max: 1000 |
| `status` | string | — | `OPEN`, `SENT`, `ACK`, `RECEIVED`, `CLOSED`, `CANCELLED` |
| `supplier_id` | uuid | — | Filtrer par fournisseur |

### Réponse `200` — SupplierOrderListItem

```json
[
  {
    "id": "uuid",
    "order_number": "CMD-2026-0042",
    "supplier_id": "uuid",
    "supplier": {
      "id": "uuid", "name": "PONS & SABOT", "code": "PS",
      "contact_name": "M. Martin", "email": "commandes@pons.fr", "phone": "01 23 45 67 89"
    },
    "status": "OPEN",
    "total_amount": 1250.50,
    "ordered_at": null,
    "expected_delivery_date": null,
    "line_count": 3,
    "age_days": 5,
    "age_color": "gray",
    "is_blocking": false,
    "created_at": "2026-02-10T09:00:00",
    "updated_at": "2026-02-10T09:00:00"
  }
]
```

### Indicateurs d'âge

| `age_color` | Condition | `is_blocking` |
|---|---|---|
| `gray` | < 7 jours | false |
| `orange` | 7-14 jours | true |
| `red` | > 14 jours | true |

---

## `GET /supplier-orders/{id}`

Détail avec `lines` (tableau de SupplierOrderLineListItem).

---

## `GET /supplier-orders/number/{order_number}`

Recherche par numéro de commande.

---

## `POST /supplier-orders`

Crée une commande.

### Entrée

```json
{
  "supplier_id": "uuid",
  "status": "OPEN",
  "ordered_at": null,
  "expected_delivery_date": null,
  "notes": null,
  "currency": null
}
```

| Champ | Type | Requis | Description |
|---|---|---|---|
| `supplier_id` | uuid | oui | Fournisseur |
| `status` | string | non | Défaut: `OPEN` |
| `notes` | string | non | Notes libres |

### Règles métier

- `order_number` est auto-généré par trigger
- `total_amount` est calculé par trigger depuis les lignes

---

## `PUT /supplier-orders/{id}`

Met à jour. `order_number` non modifiable. Tous champs optionnels (schema `SupplierOrderUpdate`).

---

## `DELETE /supplier-orders/{id}`

Supprime (cascade sur les lignes). Réponse `204`.

---

## `POST /supplier-orders/{id}/export/csv`

Exporte la commande en CSV.

### Réponse `200`

- Content-Type: `text/csv`
- Colonnes : Article, Référence, Spécification, Fabricant, Réf. Fabricant, Quantité, Unité, Prix unitaire, Prix total, Demandes liées

> Templates modifiables dans `config/export_templates.py`

---

## `POST /supplier-orders/{id}/export/email`

Génère le contenu d'un email de commande.

### Réponse `200`

```json
{
  "subject": "Commande CMD-2026-0042 - PONS & SABOT",
  "body_text": "Bonjour,\n\nVeuillez trouver ci-joint notre commande...",
  "body_html": "<html>...</html>",
  "supplier_email": "commandes@pons.fr"
}
```

> Templates modifiables dans `config/export_templates.py`
