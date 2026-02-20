# API Manifest — GMAO API v2.2.0

> Dernière mise à jour : 2026-02-20

Documentation complète de l'API. Chaque endpoint possède sa propre page avec formats JSON d'entrée/sortie, règles métier et exemples.

## Quick Start

```bash
# Démarrer l'API
docker-compose up -d

# Ou en local
python -m uvicorn api.app:app --reload
```

Documentation OpenAPI interactive : `http://localhost:8000/docs`

## Endpoints

| Méthode | Endpoint                                               | Description                   | Documentation                                                           |
| ------- | ------------------------------------------------------ | ----------------------------- | ----------------------------------------------------------------------- |
| GET     | `/health`                                              | Health check                  | [health.md](docs/endpoints/health.md)                                   |
| POST    | `/auth/login`                                          | Authentification              | [auth.md](docs/endpoints/auth.md)                                       |
| GET     | `/interventions`                                       | Liste interventions           | [interventions.md](docs/endpoints/interventions.md)                     |
| GET     | `/interventions/{id}`                                  | Détail intervention           | [interventions.md](docs/endpoints/interventions.md)                     |
| GET     | `/interventions/{id}/actions`                          | Actions d'une intervention    | [interventions.md](docs/endpoints/interventions.md)                     |
| POST    | `/interventions`                                       | Créer intervention            | [interventions.md](docs/endpoints/interventions.md)                     |
| PUT     | `/interventions/{id}`                                  | Modifier intervention         | [interventions.md](docs/endpoints/interventions.md)                     |
| DELETE  | `/interventions/{id}`                                  | Supprimer intervention        | [interventions.md](docs/endpoints/interventions.md)                     |
| GET     | `/intervention-actions`                                | Liste actions                 | [intervention-actions.md](docs/endpoints/intervention-actions.md)       |
| GET     | `/intervention-actions/{id}`                           | Détail action                 | [intervention-actions.md](docs/endpoints/intervention-actions.md)       |
| POST    | `/intervention-actions`                                | Créer action                  | [intervention-actions.md](docs/endpoints/intervention-actions.md)       |
| PUT     | `/intervention-actions/{id}`                           | Modifier action               | [intervention-actions.md](docs/endpoints/intervention-actions.md)       |
| DELETE  | `/intervention-actions/{id}`                           | Supprimer action              | [intervention-actions.md](docs/endpoints/intervention-actions.md)       |
| GET     | `/intervention-status`                                 | Référentiel statuts           | [intervention-status.md](docs/endpoints/intervention-status.md)         |
| GET     | `/intervention-status/{code}`                          | Détail statut                 | [intervention-status.md](docs/endpoints/intervention-status.md)         |
| GET     | `/intervention-status-log`                             | Historique changements statut | [intervention-status-log.md](docs/endpoints/intervention-status-log.md) |
| GET     | `/intervention-status-log/{id}`                        | Détail changement statut      | [intervention-status-log.md](docs/endpoints/intervention-status-log.md) |
| POST    | `/intervention-status-log`                             | Créer changement statut       | [intervention-status-log.md](docs/endpoints/intervention-status-log.md) |
| GET     | `/action-categories`                                   | Catégories d'actions          | [action-categories.md](docs/endpoints/action-categories.md)             |
| GET     | `/action-categories/{id}`                              | Détail catégorie              | [action-categories.md](docs/endpoints/action-categories.md)             |
| GET     | `/action-categories/{id}/subcategories`                | Sous-catégories               | [action-categories.md](docs/endpoints/action-categories.md)             |
| GET     | `/action-subcategories`                                | Toutes sous-catégories        | [action-categories.md](docs/endpoints/action-categories.md)             |
| GET     | `/action-subcategories/{id}`                           | Détail sous-catégorie         | [action-categories.md](docs/endpoints/action-categories.md)             |
| GET     | `/complexity-factors`                                  | Facteurs de complexité        | [complexity-factors.md](docs/endpoints/complexity-factors.md)           |
| GET     | `/complexity-factors/{code}`                           | Détail facteur                | [complexity-factors.md](docs/endpoints/complexity-factors.md)           |
| GET     | `/equipements`                                         | Liste équipements             | [equipements.md](docs/endpoints/equipements.md)                         |
| GET     | `/equipements/{id}`                                    | Détail équipement             | [equipements.md](docs/endpoints/equipements.md)                         |
| GET     | `/equipements/{id}/stats`                              | Statistiques équipement       | [equipements.md](docs/endpoints/equipements.md)                         |
| GET     | `/equipements/{id}/health`                             | Santé équipement              | [equipements.md](docs/endpoints/equipements.md)                         |
| GET     | `/equipement-class`                                    | Classes d'équipements         | [equipement-class.md](docs/endpoints/equipement-class.md)               |
| GET     | `/equipement-class/{id}`                               | Détail classe                 | [equipement-class.md](docs/endpoints/equipement-class.md)               |
| POST    | `/equipement-class`                                    | Créer classe                  | [equipement-class.md](docs/endpoints/equipement-class.md)               |
| PATCH   | `/equipement-class/{id}`                               | Modifier classe               | [equipement-class.md](docs/endpoints/equipement-class.md)               |
| DELETE  | `/equipement-class/{id}`                               | Supprimer classe              | [equipement-class.md](docs/endpoints/equipement-class.md)               |
| GET     | `/purchase-requests`                                   | Liste demandes [LEGACY]       | [purchase-requests.md](docs/endpoints/purchase-requests.md)             |
| GET     | `/purchase-requests/list`                              | Liste optimisée               | [purchase-requests.md](docs/endpoints/purchase-requests.md)             |
| GET     | `/purchase-requests/detail/{id}`                       | Détail enrichi                | [purchase-requests.md](docs/endpoints/purchase-requests.md)             |
| GET     | `/purchase-requests/stats`                             | Statistiques dashboard        | [purchase-requests.md](docs/endpoints/purchase-requests.md)             |
| GET     | `/purchase-requests/{id}`                              | Détail [LEGACY]               | [purchase-requests.md](docs/endpoints/purchase-requests.md)             |
| GET     | `/purchase-requests/intervention/{id}`                 | Par intervention [LEGACY]     | [purchase-requests.md](docs/endpoints/purchase-requests.md)             |
| GET     | `/purchase-requests/intervention/{id}/optimized`       | Par intervention optimisé     | [purchase-requests.md](docs/endpoints/purchase-requests.md)             |
| POST    | `/purchase-requests`                                   | Créer demande                 | [purchase-requests.md](docs/endpoints/purchase-requests.md)             |
| PUT     | `/purchase-requests/{id}`                              | Modifier demande              | [purchase-requests.md](docs/endpoints/purchase-requests.md)             |
| DELETE  | `/purchase-requests/{id}`                              | Supprimer demande             | [purchase-requests.md](docs/endpoints/purchase-requests.md)             |
| POST    | `/purchase-requests/dispatch`                          | Dispatch automatique          | [purchase-requests.md](docs/endpoints/purchase-requests.md)             |
| GET     | `/stock-items`                                         | Liste articles                | [stock-items.md](docs/endpoints/stock-items.md)                         |
| GET     | `/stock-items/{id}`                                    | Détail article                | [stock-items.md](docs/endpoints/stock-items.md)                         |
| GET     | `/stock-items/{id}/with-characteristics`               | Article avec caractéristiques | [stock-items.md](docs/endpoints/stock-items.md)                         |
| GET     | `/stock-items/ref/{ref}`                               | Par référence                 | [stock-items.md](docs/endpoints/stock-items.md)                         |
| POST    | `/stock-items`                                         | Créer article                 | [stock-items.md](docs/endpoints/stock-items.md)                         |
| PUT     | `/stock-items/{id}`                                    | Modifier article              | [stock-items.md](docs/endpoints/stock-items.md)                         |
| PATCH   | `/stock-items/{id}/quantity`                           | Modifier quantité             | [stock-items.md](docs/endpoints/stock-items.md)                         |
| DELETE  | `/stock-items/{id}`                                    | Supprimer article             | [stock-items.md](docs/endpoints/stock-items.md)                         |
| GET     | `/stock-families`                                      | Liste familles stock          | [stock-families.md](docs/endpoints/stock-families.md)                   |
| GET     | `/stock-families/{code}`                               | Détail famille                | [stock-families.md](docs/endpoints/stock-families.md)                   |
| GET     | `/stock-sub-families`                                  | Sous-familles stock           | [stock-sub-families.md](docs/endpoints/stock-sub-families.md)           |
| GET     | `/stock-sub-families/{family}/{sub}`                   | Détail sous-famille           | [stock-sub-families.md](docs/endpoints/stock-sub-families.md)           |
| GET     | `/part-templates`                                      | Templates de pièces           | [part-templates.md](docs/endpoints/part-templates.md)                   |
| GET     | `/part-templates/{id}`                                 | Détail template               | [part-templates.md](docs/endpoints/part-templates.md)                   |
| POST    | `/part-templates`                                      | Créer template                | [part-templates.md](docs/endpoints/part-templates.md)                   |
| PUT     | `/part-templates/{id}`                                 | Modifier template             | [part-templates.md](docs/endpoints/part-templates.md)                   |
| DELETE  | `/part-templates/{id}`                                 | Supprimer template            | [part-templates.md](docs/endpoints/part-templates.md)                   |
| GET     | `/supplier-orders`                                     | Liste commandes fournisseurs  | [supplier-orders.md](docs/endpoints/supplier-orders.md)                 |
| GET     | `/supplier-orders/{id}`                                | Détail commande               | [supplier-orders.md](docs/endpoints/supplier-orders.md)                 |
| GET     | `/supplier-orders/number/{n}`                          | Par numéro commande           | [supplier-orders.md](docs/endpoints/supplier-orders.md)                 |
| POST    | `/supplier-orders`                                     | Créer commande                | [supplier-orders.md](docs/endpoints/supplier-orders.md)                 |
| PUT     | `/supplier-orders/{id}`                                | Modifier commande             | [supplier-orders.md](docs/endpoints/supplier-orders.md)                 |
| DELETE  | `/supplier-orders/{id}`                                | Supprimer commande            | [supplier-orders.md](docs/endpoints/supplier-orders.md)                 |
| POST    | `/supplier-orders/{id}/export/csv`                     | Export CSV                    | [supplier-orders.md](docs/endpoints/supplier-orders.md)                 |
| POST    | `/supplier-orders/{id}/export/email`                   | Génération email              | [supplier-orders.md](docs/endpoints/supplier-orders.md)                 |
| GET     | `/supplier-order-lines`                                | Liste lignes commande         | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md)       |
| GET     | `/supplier-order-lines/{id}`                           | Détail ligne                  | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md)       |
| GET     | `/supplier-order-lines/order/{id}`                     | Lignes d'une commande         | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md)       |
| POST    | `/supplier-order-lines`                                | Créer ligne                   | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md)       |
| PUT     | `/supplier-order-lines/{id}`                           | Modifier ligne                | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md)       |
| DELETE  | `/supplier-order-lines/{id}`                           | Supprimer ligne               | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md)       |
| POST    | `/supplier-order-lines/{id}/purchase-requests`         | Lier demande achat            | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md)       |
| DELETE  | `/supplier-order-lines/{id}/purchase-requests/{pr_id}` | Délier demande achat          | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md)       |
| GET     | `/suppliers`                                           | Liste fournisseurs            | [suppliers.md](docs/endpoints/suppliers.md)                             |
| GET     | `/suppliers/{id}`                                      | Détail fournisseur            | [suppliers.md](docs/endpoints/suppliers.md)                             |
| GET     | `/suppliers/code/{code}`                               | Par code fournisseur          | [suppliers.md](docs/endpoints/suppliers.md)                             |
| POST    | `/suppliers`                                           | Créer fournisseur             | [suppliers.md](docs/endpoints/suppliers.md)                             |
| PUT     | `/suppliers/{id}`                                      | Modifier fournisseur          | [suppliers.md](docs/endpoints/suppliers.md)                             |
| DELETE  | `/suppliers/{id}`                                      | Supprimer fournisseur         | [suppliers.md](docs/endpoints/suppliers.md)                             |
| GET     | `/stock-item-suppliers`                                | Références fournisseurs       | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md)       |
| GET     | `/stock-item-suppliers/{id}`                           | Détail référence              | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md)       |
| GET     | `/stock-item-suppliers/stock-item/{id}`                | Par article                   | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md)       |
| GET     | `/stock-item-suppliers/supplier/{id}`                  | Par fournisseur               | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md)       |
| POST    | `/stock-item-suppliers`                                | Créer référence               | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md)       |
| PUT     | `/stock-item-suppliers/{id}`                           | Modifier référence            | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md)       |
| POST    | `/stock-item-suppliers/{id}/set-preferred`             | Définir préféré               | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md)       |
| DELETE  | `/stock-item-suppliers/{id}`                           | Supprimer référence           | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md)       |
| GET     | `/users`                                               | Liste utilisateurs            | [users.md](docs/endpoints/users.md)                                     |
| GET     | `/users/{id}`                                          | Détail utilisateur            | [users.md](docs/endpoints/users.md)                                     |
| GET     | `/stats/service-status`                                | Indicateurs de service        | [stats.md](docs/endpoints/stats.md)                                     |
| GET     | `/stats/charge-technique`                              | Charge technique [BETA]       | [stats.md](docs/endpoints/stats.md)                                     |
| GET     | `/stats/anomalies-saisie`                              | Anomalies de saisie [BETA]    | [stats.md](docs/endpoints/stats.md)                                     |
| POST    | `/exports/intervention/{id}/pdf`                       | Export PDF intervention       | [exports.md](docs/endpoints/exports.md)                                 |
| GET     | `/exports/intervention/{id}/qr`                        | QR Code intervention          | [exports.md](docs/endpoints/exports.md)                                 |

## Configuration

Variables d'environnement (fichier `.env`) :

- `DATABASE_URL` : Connexion PostgreSQL
- `DIRECTUS_URL` : Service d'authentification
- `DIRECTUS_SECRET` : Secret Directus
- `DIRECTUS_KEY` : Clé API Directus
- `AUTH_DISABLED` : `true` pour désactiver l'authentification (dev uniquement)
- `FRONTEND_URL` : URL du frontend (CORS)
- `EXPORT_TEMPLATE_DIR` : Répertoire des templates d'export
- `EXPORT_TEMPLATE_FILE` : Fichier template PDF
- `EXPORT_TEMPLATE_VERSION` : Version du template

## Schemas

### InterventionIn (POST/PUT)

```json
{
  "title": "string|null",
  "machine_id": "uuid|null",
  "type_inter": "string|null",
  "priority": "string|null",
  "reported_by": "string|null",
  "tech_initials": "string|null",
  "status_actual": "string|null",
  "printed_fiche": "boolean|null",
  "reported_date": "date|null"
}
```

### InterventionOut

Note: `GET /interventions` returns `actions: []` and `status_logs: []` (empty), `GET /interventions/{id}` returns full actions and status logs.

For `GET /interventions/{id}`:

- The `equipements` object is fetched via `EquipementRepository.get_by_id()` to ensure schema consistency
- The `status_logs` array is fetched via `InterventionStatusLogRepository.get_by_intervention()` to include complete status change history

```json
{
  "id": "uuid",
  "code": "string",
  "title": "string",
  "equipements": {
    "id": "uuid",
    "code": "string|null",
    "name": "string",
    "health": {
      "level": "ok|maintenance|warning|critical",
      "reason": "string",
      "rules_triggered": ["string"]
    },
    "parent_id": "uuid|null",
    "children_ids": ["uuid"]
  },
  "type_inter": "string",
  "priority": "string",
  "reported_by": "string",
  "tech_initials": "string",
  "status_actual": "string",
  "updated_by": "uuid",
  "printed_fiche": "boolean",
  "reported_date": "date",
  "stats": {
    "action_count": "int",
    "total_time": "float",
    "avg_complexity": "float|null",
    "purchase_count": "int"
  },
  "actions": ["InterventionActionOut"],
  "status_logs": ["InterventionStatusLogOut"]
}
```

### InterventionActionOut

Note: Actions are fetched via `InterventionActionRepository.get_by_intervention()` when included in intervention queries to ensure schema consistency.

```json
{
  "id": "uuid",
  "intervention_id": "uuid",
  "description": "string|null",
  "time_spent": "float|null",
  "subcategory": {
    "id": "int",
    "name": "string",
    "code": "string|null",
    "category": {
      "id": "int",
      "name": "string",
      "code": "string|null",
      "color": "string|null"
    }
  },
  "tech": "uuid|null",
  "complexity_score": "int|null",
  "complexity_anotation": "object|null",
  "purchase_requests": ["PurchaseRequestOut"],
  "created_at": "datetime|null",
  "updated_at": "datetime|null"
}
```

### InterventionStatus

```json
{
  "id": "string",
  "code": "string",
  "label": "string|null",
  "color": "string|null",
  "value": "string|null"
}
```

### InterventionStatusLogIn (POST)

```json
{
  "intervention_id": "uuid",
  "status_from": "string|null",
  "status_to": "string",
  "technician_id": "uuid",
  "date": "datetime",
  "notes": "string|null"
}
```

### InterventionStatusLogOut

Note: Status logs are automatically included when fetching a specific intervention via `GET /interventions/{id}` to provide complete status change history. The `value` field in status details is converted to integer or null if the database stores non-numeric values.

```json
{
  "id": "uuid",
  "intervention_id": "uuid",
  "status_from": "string|null",
  "status_to": "string",
  "status_from_detail": {
    "id": "string",
    "code": "string|null",
    "label": "string|null",
    "color": "string|null",
    "value": "int|null"
  },
  "status_to_detail": {
    "id": "string",
    "code": "string|null",
    "label": "string|null",
    "color": "string|null",
    "value": "int|null"
  },
  "technician_id": "uuid|null",
  "date": "datetime",
  "notes": "string|null"
}
```

### InterventionActionIn (POST)

Notes:

- `complexity_anotation` is optional if `complexity_score` ≤ 5, but required if `complexity_score` > 5
- `created_at` is optional - defaults to current timestamp if null/omitted, allowing backdating of actions. Supports "YYYY-MM-DD", "YYYY-MM-DDTHH:MM:SS", or with timezone

```json
{
  "intervention_id": "uuid",
  "description": "string",
  "time_spent": "float",
  "action_subcategory": "int",
  "tech": "uuid",
  "complexity_score": "int",
  "complexity_anotation": "string|null",
  "created_at": "datetime|null"
}
```

### ComplexityFactorOut

```json
{
  "code": "string",
  "label": "string|null",
  "category": "string|null"
}
```

Note: `GET /interventions` returns `actions: []` and `status_logs: []` (empty), `GET /interventions/{id}` returns full actions and status logs with schemas defined in `InterventionActionOut` and `InterventionStatusLogOut`.

### ActionCategoryOut

```json
{
  "id": "int",
  "name": "string",
  "code": "string|null",
  "color": "string|null"
}
```

### ActionSubcategoryOut

```json
{
  "id": "int",
  "category_id": "int|null",
  "name": "string",
  "code": "string|null"
}
```

### EquipementHealth

```json
{
  "level": "ok|maintenance|warning|critical",
  "reason": "string",
  "rules_triggered": ["string"] // Optional, for debug/audit
}
```

### EquipementListItem (GET /equipements)

```json
{
  "id": "uuid",
  "code": "string|null",
  "name": "string",
  "health": {
    "level": "ok|maintenance|warning|critical",
    "reason": "string"
  },
  "parent_id": "uuid|null"
}
```

Note: Sorted by urgent count (desc), then open count (desc), then name (asc). Health rules: urgent >= 1 → critical, open > 5 → warning, open > 0 → maintenance, else ok.

### EquipementDetail (GET /equipements/{id})

```json
{
  "id": "uuid",
  "code": "string|null",
  "name": "string",
  "health": {
    "level": "ok|maintenance|warning|critical",
    "reason": "string",
    "rules_triggered": ["URGENT_OPEN >= 1", "OPEN_TOTAL > 5"]
  },
  "parent_id": "uuid|null",
  "children_ids": ["uuid"]
}
```

### EquipementStats (GET /equipements/{id}/stats)

Query params:

- `start_date` (YYYY-MM-DD, optional, default NULL = all history)
- `end_date` (YYYY-MM-DD, optional, default NOW)

```json
{
  "interventions": {
    "open": "int",
    "closed": "int",
    "by_status": {
      "1": "int",
      "2": "int",
      "3": "int"
    },
    "by_priority": {
      "faible": "int",
      "normale": "int",
      "important": "int",
      "urgent": "int"
    }
  }
}
```

### EquipementHealthOnly (GET /equipements/{id}/health)

```json
{
  "level": "ok|maintenance|warning|critical",
  "reason": "string"
}
```

### ServiceStatusResponse

```json
{
  "period": {
    "start_date": "date",
    "end_date": "date",
    "days": "int"
  },
  "capacity": {
    "total_hours": "float",
    "capacity_hours": "float",
    "charge_percent": "float",
    "status": {
      "color": "string",
      "text": "string"
    }
  },
  "breakdown": {
    "prod_hours": "float",
    "dep_hours": "float",
    "pilot_hours": "float",
    "frag_hours": "float",
    "total_hours": "float"
  },
  "fragmentation": {
    "action_count": "int",
    "short_action_count": "int",
    "short_action_percent": "float",
    "frag_percent": "float",
    "status": {
      "color": "string",
      "text": "string"
    },
    "top_causes": [
      {
        "name": "string",
        "total_hours": "float",
        "action_count": "int",
        "percent": "float"
      }
    ]
  },
  "pilotage": {
    "pilot_hours": "float",
    "pilot_percent": "float",
    "status": {
      "color": "string",
      "text": "string"
    }
  },
  "site_consumption": [
    {
      "site_name": "string",
      "total_hours": "float",
      "frag_hours": "float",
      "percent_total": "float",
      "percent_frag": "float"
    }
  ]
}
```

### AuthLoginResponse

```json
{
  "data": {
    "access_token": "string",
    "refresh_token": "string",
    "expires": "int"
  }
}
```

### PurchaseRequestIn (POST)

```json
{
  "item_label": "string",
  "quantity": "int",
  "stock_item_id": "uuid|null",
  "unit": "string|null",
  "requested_by": "string|null",
  "urgency": "string|null",
  "reason": "string|null",
  "notes": "string|null",
  "workshop": "string|null",
  "intervention_id": "uuid|null",
  "quantity_requested": "int|null",
  "urgent": "boolean|null",
  "requester_name": "string|null"
}
```

### PurchaseRequestListItem

Note: Schéma léger pour listes (tableau, pagination). Retourné par `/purchase_requests/list`.

```json
{
  "id": "uuid",
  "item_label": "string",
  "quantity": "int",
  "unit": "string|null",
  "derived_status": {
    "code": "TO_QUALIFY|NO_SUPPLIER_REF|PENDING_DISPATCH|OPEN|QUOTED|ORDERED|PARTIAL|RECEIVED|REJECTED",
    "label": "string",
    "color": "string (hex)"
  },
  "stock_item_id": "uuid|null",
  "stock_item_ref": "string|null",
  "stock_item_name": "string|null",
  "intervention_code": "string|null",
  "requester_name": "string|null",
  "urgency": "string|null",
  "urgent": "boolean",
  "quotes_count": "int",
  "selected_count": "int",
  "suppliers_count": "int",
  "created_at": "datetime|null",
  "updated_at": "datetime|null"
}
```

### PurchaseRequestOut

Note:

- `derived_status` est calculé automatiquement selon l'avancement (pas de champ `status` manuel)
- When `stock_item_id` is not null, the `stock_item` object is automatically populated
- When `intervention_id` is not null, the `intervention` object is automatically populated with equipement details
- `order_lines` contains all supplier order lines linked via M2M table

```json
{
  "id": "uuid",
  "derived_status": {
    "code": "TO_QUALIFY|NO_SUPPLIER_REF|PENDING_DISPATCH|OPEN|QUOTED|ORDERED|PARTIAL|RECEIVED|REJECTED",
    "label": "string",
    "color": "string (hex)"
  },
  "stock_item_id": "uuid|null",
  "stock_item": "StockItemListItem|null",
  "item_label": "string",
  "quantity": "int",
  "unit": "string|null",
  "requested_by": "string|null",
  "urgency": "string|null",
  "reason": "string|null",
  "notes": "string|null",
  "workshop": "string|null",
  "intervention_id": "uuid|null",
  "intervention": "InterventionInfo|null",
  "quantity_requested": "int|null",
  "quantity_approved": "int|null",
  "urgent": "boolean|null",
  "requester_name": "string|null",
  "approver_name": "string|null",
  "approved_at": "datetime|null",
  "order_lines": ["LinkedOrderLine"],
  "created_at": "datetime|null",
  "updated_at": "datetime|null"
}
```

### InterventionInfo (embedded in PurchaseRequestOut)

Note: Lightweight intervention object with equipement context.

```json
{
  "id": "uuid",
  "code": "string|null",
  "title": "string",
  "priority": "string|null",
  "status_actual": "string|null",
  "equipement": {
    "id": "uuid",
    "code": "string|null",
    "name": "string"
  }
}
```

### DerivedStatus (embedded in PurchaseRequestOut)

Statut calculé automatiquement basé sur l'avancement de la demande :

- `TO_QUALIFY`: Pas de référence stock normalisée (stock_item_id is null)
- `NO_SUPPLIER_REF`: Référence stock ok, mais aucune référence fournisseur liée
- `PENDING_DISPATCH`: Référence fournisseur ok, prête à être dispatchée
- `OPEN`: En attente de dispatch (aucune ligne de commande)
- `QUOTED`: Au moins un devis reçu
- `ORDERED`: Au moins une ligne sélectionnée pour commande
- `PARTIAL`: Livraison partielle
- `RECEIVED`: Livraison complète
- `REJECTED`: Demande annulée

```json
{
  "code": "string",
  "label": "string",
  "color": "string (hex)"
}
```

### LinkedOrderLine (embedded in PurchaseRequestOut)

Note: Includes all fields needed for purchase request status calculation:

- `quote_received`: devis reçu pour cette ligne
- `quote_price`: prix du devis
- `is_selected`: ligne sélectionnée pour passer commande
- `supplier_order_status`: statut de la commande fournisseur (OPEN, SENT, PARTIAL, RECEIVED, CLOSED)

```json
{
  "id": "uuid",
  "supplier_order_line_id": "uuid",
  "quantity_allocated": "int",
  "supplier_order_id": "uuid",
  "supplier_order_status": "string|null",
  "supplier_order_number": "string|null",
  "stock_item_id": "uuid",
  "stock_item_name": "string|null",
  "stock_item_ref": "string|null",
  "quantity": "int",
  "unit_price": "float|null",
  "total_price": "float|null",
  "quote_received": "boolean|null",
  "quote_price": "float|null",
  "quantity_received": "int|null",
  "is_selected": "boolean|null",
  "created_at": "datetime|null"
}
```

### PurchaseRequestStats

Note: Statistiques agrégées pour les dashboards. Par défaut, analyse les 3 derniers mois.

```json
{
  "period": {
    "start_date": "date (YYYY-MM-DD)",
    "end_date": "date (YYYY-MM-DD)"
  },
  "totals": {
    "total_requests": "int",
    "urgent_count": "int"
  },
  "by_status": [
    {
      "status": "TO_QUALIFY|NO_SUPPLIER_REF|PENDING_DISPATCH|OPEN|QUOTED|ORDERED|PARTIAL|RECEIVED|REJECTED",
      "count": "int",
      "label": "string",
      "color": "string (hex)"
    }
  ],
  "by_urgency": [
    {
      "urgency": "string (normal, high, critical)",
      "count": "int"
    }
  ],
  "top_items": [
    {
      "item_label": "string",
      "stock_item_ref": "string|null",
      "request_count": "int",
      "total_quantity": "int"
    }
  ]
}
```

### DispatchResult

Note: Résultat du dispatch automatique des demandes PENDING_DISPATCH vers les supplier_orders.

```json
{
  "dispatched_count": "int",
  "created_orders": "int",
  "errors": [
    {
      "purchase_request_id": "string (uuid)",
      "error": "string"
    }
  ]
}
```

### StockItemIn (POST)

```json
{
  "name": "string",
  "family_code": "string",
  "sub_family_code": "string",
  "dimension": "string",
  "spec": "string|null",
  "quantity": "int|null",
  "unit": "string|null",
  "location": "string|null",
  "standars_spec": "uuid|null",
  "manufacturer_item_id": "uuid|null"
}
```

### StockItemOut

```json
{
  "id": "uuid",
  "name": "string",
  "family_code": "string",
  "sub_family_code": "string",
  "spec": "string|null",
  "dimension": "string",
  "ref": "string|null",
  "quantity": "int|null",
  "unit": "string|null",
  "location": "string|null",
  "standars_spec": "uuid|null",
  "supplier_refs_count": "int|null",
  "manufacturer_item_id": "uuid|null"
}
```

### StockItemListItem (lightweight)

```json
{
  "id": "uuid",
  "name": "string",
  "ref": "string|null",
  "family_code": "string",
  "sub_family_code": "string",
  "quantity": "int|null",
  "unit": "string|null",
  "location": "string|null"
}
```

### SupplierOrderLineIn (POST)

```json
{
  "supplier_order_id": "uuid",
  "stock_item_id": "uuid",
  "quantity": "int",
  "supplier_ref_snapshot": "string|null",
  "unit_price": "float|null",
  "notes": "string|null",
  "quote_received": "boolean|null",
  "is_selected": "boolean|null",
  "quote_price": "float|null",
  "manufacturer": "string|null",
  "manufacturer_ref": "string|null",
  "quote_received_at": "datetime|null",
  "rejected_reason": "string|null",
  "lead_time_days": "int|null",
  "purchase_requests": [{ "purchase_request_id": "uuid", "quantity": "int" }]
}
```

### SupplierOrderLineOut

Note: Includes `stock_item` details and `purchase_requests` linked via M2M table.

```json
{
  "id": "uuid",
  "supplier_order_id": "uuid",
  "stock_item_id": "uuid",
  "stock_item": "StockItemListItem|null",
  "supplier_ref_snapshot": "string|null",
  "quantity": "int",
  "unit_price": "float|null",
  "total_price": "float|null",
  "quantity_received": "int|null",
  "notes": "string|null",
  "quote_received": "boolean|null",
  "is_selected": "boolean|null",
  "quote_price": "float|null",
  "manufacturer": "string|null",
  "manufacturer_ref": "string|null",
  "quote_received_at": "datetime|null",
  "rejected_reason": "string|null",
  "lead_time_days": "int|null",
  "purchase_requests": ["LinkedPurchaseRequest"],
  "created_at": "datetime|null",
  "updated_at": "datetime|null"
}
```

### LinkedPurchaseRequest (embedded in SupplierOrderLineOut)

```json
{
  "id": "uuid",
  "purchase_request_id": "uuid",
  "quantity": "int",
  "item_label": "string|null",
  "requester_name": "string|null",
  "intervention_id": "uuid|null",
  "created_at": "datetime|null"
}
```

### SupplierOrderLineListItem (lightweight)

```json
{
  "id": "uuid",
  "supplier_order_id": "uuid",
  "stock_item_id": "uuid",
  "stock_item_name": "string|null",
  "stock_item_ref": "string|null",
  "quantity": "int",
  "unit_price": "float|null",
  "total_price": "float|null",
  "quantity_received": "int|null",
  "is_selected": "boolean|null",
  "purchase_request_count": "int|null"
}
```

### SupplierOrderIn (POST)

```json
{
  "supplier_id": "uuid",
  "status": "string|null",
  "ordered_at": "datetime|null",
  "expected_delivery_date": "date|null",
  "notes": "string|null",
  "currency": "float|null"
}
```

### SupplierOrderOut

Note: Includes `lines` array, `supplier` object, and computed age fields (`age_days`, `age_color`, `is_blocking`).

```json
{
  "id": "uuid",
  "order_number": "string",
  "supplier_id": "uuid",
  "supplier": {
    "id": "uuid",
    "name": "string",
    "code": "string|null",
    "contact_name": "string|null",
    "email": "string|null",
    "phone": "string|null"
  },
  "status": "OPEN|SENT|ACK|RECEIVED|CLOSED|CANCELLED",
  "total_amount": "float|null",
  "ordered_at": "datetime|null",
  "expected_delivery_date": "date|null",
  "received_at": "datetime|null",
  "notes": "string|null",
  "currency": "float|null",
  "lines": ["SupplierOrderLineListItem"],
  "line_count": "int",
  "age_days": "int",
  "age_color": "gray|orange|red",
  "is_blocking": "boolean",
  "created_at": "datetime|null",
  "updated_at": "datetime|null"
}
```

### SupplierOrderListItem (lightweight)

Note: Includes enriched `supplier` object and computed age fields.

```json
{
  "id": "uuid",
  "order_number": "string",
  "supplier_id": "uuid",
  "supplier": {
    "id": "uuid",
    "name": "string",
    "code": "string|null",
    "contact_name": "string|null",
    "email": "string|null",
    "phone": "string|null"
  },
  "status": "OPEN|SENT|ACK|RECEIVED|CLOSED|CANCELLED",
  "total_amount": "float|null",
  "ordered_at": "datetime|null",
  "expected_delivery_date": "date|null",
  "line_count": "int",
  "age_days": "int",
  "age_color": "gray|orange|red",
  "is_blocking": "boolean",
  "created_at": "datetime|null",
  "updated_at": "datetime|null"
}
```

### EmailExportOut (POST /supplier_orders/{id}/export/email)

Note: Generated email content for supplier order. Includes text and HTML versions of the email body.

```json
{
  "subject": "string",
  "body_text": "string",
  "body_html": "string",
  "supplier_email": "string|null"
}
```

### SupplierIn (POST)

```json
{
  "name": "string",
  "code": "string|null",
  "contact_name": "string|null",
  "email": "string|null",
  "phone": "string|null",
  "address": "string|null",
  "notes": "string|null",
  "is_active": "boolean|null"
}
```

### SupplierOut

```json
{
  "id": "uuid",
  "name": "string",
  "code": "string|null",
  "contact_name": "string|null",
  "email": "string|null",
  "phone": "string|null",
  "address": "string|null",
  "notes": "string|null",
  "is_active": "boolean|null",
  "created_at": "datetime|null",
  "updated_at": "datetime|null"
}
```

### SupplierListItem (lightweight)

```json
{
  "id": "uuid",
  "name": "string",
  "code": "string|null",
  "contact_name": "string|null",
  "email": "string|null",
  "phone": "string|null",
  "is_active": "boolean|null"
}
```

### StockItemSupplierIn (POST)

```json
{
  "stock_item_id": "uuid",
  "supplier_id": "uuid",
  "supplier_ref": "string",
  "unit_price": "float|null",
  "min_order_quantity": "int|null",
  "delivery_time_days": "int|null",
  "is_preferred": "boolean|null",
  "manufacturer_item_id": "uuid|null"
}
```

### StockItemSupplierOut

Note: Includes enriched `stock_item_name`, `stock_item_ref`, `supplier_name`, `supplier_code`.

```json
{
  "id": "uuid",
  "stock_item_id": "uuid",
  "supplier_id": "uuid",
  "supplier_ref": "string",
  "unit_price": "float|null",
  "min_order_quantity": "int|null",
  "delivery_time_days": "int|null",
  "is_preferred": "boolean|null",
  "manufacturer_item_id": "uuid|null",
  "stock_item_name": "string|null",
  "stock_item_ref": "string|null",
  "supplier_name": "string|null",
  "supplier_code": "string|null",
  "created_at": "datetime|null",
  "updated_at": "datetime|null"
}
```

### StockItemSupplierListItem (lightweight)

```json
{
  "id": "uuid",
  "stock_item_id": "uuid",
  "supplier_id": "uuid",
  "supplier_ref": "string",
  "unit_price": "float|null",
  "min_order_quantity": "int|null",
  "delivery_time_days": "int|null",
  "is_preferred": "boolean|null",
  "stock_item_name": "string|null",
  "stock_item_ref": "string|null",
  "supplier_name": "string|null",
  "supplier_code": "string|null"
}
```
