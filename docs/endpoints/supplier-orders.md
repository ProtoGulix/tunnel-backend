# Supplier Orders

Commandes fournisseurs avec suivi d'âge, lignes de commande et exports (CSV, email).

> Voir aussi : [Supplier Order Lines](supplier-order-lines.md) | [Suppliers](suppliers.md) | [Purchase Requests](purchase-requests.md)

---

## `GET /supplier-orders/statuses`

Retourne tous les statuts possibles avec leur label et couleur. Utiliser pour construire des filtres et badges côté frontend sans hardcoder les valeurs.

### Réponse `200`

```json
[
  { "code": "OPEN",      "label": "En mutualisation",     "color": "#3B82F6", "description": "Panier ouvert, nouvelles DA acceptées",                                    "is_locked": false },
  { "code": "SENT",      "label": "Devis envoyé",         "color": "#F97316", "description": "Devis envoyé au fournisseur, en attente de réponse — panier verrouillé",  "is_locked": true  },
  { "code": "ACK",       "label": "En négociation",       "color": "#6366F1", "description": "Réponse fournisseur reçue, sélection des lignes retenues",                "is_locked": true  },
  { "code": "RECEIVED",  "label": "En cours de livraison","color": "#10B981", "description": "Commande passée, en attente de réception physique",                       "is_locked": true  },
  { "code": "CLOSED",    "label": "Clôturé",              "color": "#6B7280", "description": "Tous les produits reçus, fin de vie du panier",                           "is_locked": true  },
  { "code": "CANCELLED", "label": "Annulé",               "color": "#EF4444", "description": "Commande annulée",                                                        "is_locked": true  }
]
```

| Champ | Description |
|---|---|
| `code` | Valeur stockée en base |
| `label` | Libellé affiché côté frontend |
| `description` | Explication métier du statut |
| `is_locked` | `true` = panier verrouillé, impossible d'ajouter des DA |

> Source : `api/constants.py` — `SUPPLIER_ORDER_STATUS_CONFIG`.

---

## `GET /supplier-orders`

Liste les commandes avec filtres, pagination et facets.

### Query params

| Param | Type | Défaut | Description |
|---|---|---|---|
| `skip` | int | 0 | Offset |
| `limit` | int | 100 | Max: 1000 |
| `status` | string | — | `OPEN`, `SENT`, `ACK`, `RECEIVED`, `CLOSED`, `CANCELLED` |
| `supplier_id` | uuid | — | Filtrer par fournisseur |

### Réponse `200` — SupplierOrderListResponse

```json
{
  "pagination": {
    "total": 42,
    "page": 1,
    "page_size": 100,
    "total_pages": 1,
    "offset": 0,
    "count": 42
  },
  "facets": [
    { "status": "ACK",       "count": 3  },
    { "status": "CANCELLED", "count": 1  },
    { "status": "OPEN",      "count": 28 },
    { "status": "RECEIVED",  "count": 10 }
  ],
  "items": [
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
}
```

| Champ | Description |
|---|---|
| `pagination.total` | Nombre total de commandes après filtres |
| `pagination.page` | Page actuelle (commence à 1) |
| `pagination.page_size` | Taille de page demandée |
| `pagination.total_pages` | Nombre total de pages |
| `pagination.count` | Nombre d'éléments retournés dans cette page |
| `facets` | Compteurs par statut **sans** le filtre `status` (toujours complet) |
| `items` | Page de résultats |

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

## `GET /supplier-orders/{id}/transitions`

Retourne les transitions de statut autorisées depuis le statut actuel. Utiliser côté UI pour afficher uniquement les actions disponibles.

### Réponse `200`

```json
{
  "current_status": "SENT",
  "transitions": [
    { "to": "ACK",       "description": "Le fournisseur a répondu — passer en négociation." },
    { "to": "RECEIVED",  "description": "Commande directe confirmée — passer en cours de livraison (sans étape de négociation)." },
    { "to": "OPEN",      "description": "Réouvrir le panier — toutes les lignes sont conservées." },
    { "to": "CANCELLED", "description": "Annuler ce panier." }
  ]
}
```

> Si `transitions` est vide, le statut est un **état final** (`CLOSED` ou `CANCELLED`).

---

## Règles métier — transitions de statut

### Graphe des transitions autorisées

```
OPEN      → SENT, CANCELLED
SENT      → ACK, RECEIVED, OPEN, CANCELLED
ACK       → RECEIVED, CANCELLED
RECEIVED  → CLOSED
CLOSED    → (état final)
CANCELLED → (état final)
```

### Règles associées

| Règle | Détail |
|---|---|
| `SENT → OPEN` | Réouverture autorisée — toutes les lignes sont conservées |
| `SENT → RECEIVED` | Commande directe (ex : Würth, Fabory) — sans étape de négociation |
| `CLOSED` | Déclenché manuellement — état final absolu |
| `CANCELLED` | État final absolu — aucune réouverture possible |
| Panier verrouillé | Dès `SENT` — le dispatch crée un **nouveau** panier `OPEN` pour ce fournisseur |

### Erreurs de transition

Un `PUT /supplier-orders/{id}` avec un `status` invalide retourne :

```json
{
  "detail": "Transition invalide : 'SENT' (Devis envoyé) → 'CLOSED' (Clôturé). Transitions autorisées depuis 'SENT' : 'ACK', 'RECEIVED', 'OPEN', 'CANCELLED'."
}
```

| Code | Cas |
|---|---|
| `400` | Transition non autorisée |
| `400` | Tentative de modification d'un état final (`CLOSED`, `CANCELLED`) |

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
