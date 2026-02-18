# API Manifest — GMAO API v2.0.0
2> Dernière mise à jour : 2026-02-18
ulfilled, SupplierOrderUpdate)

## Endpoints

### Health

- `GET /health` - Check API health with database and authentication service status (Public)

### Auth

- `POST /auth/login` - Login proxy, returns JWT payload and sets session cookie (Public)
  - Body (json): `{ "email": "string", "password": "string", "mode": "session" }`

### Interventions

- `GET /interventions` - List interventions with filters, sort, pagination and stats (Auth: Optional if AUTH_DISABLED)
  - Query params:
    - `skip` (default 0), `limit` (default 100, max 1000)
    - `equipement_id` (uuid) - Filter by intervention.machine_id
    - `status` (csv) - Filter by status codes (ex: ouvert,ferme,en_cours) - case insensitive
    - `priority` (csv) - Filter by priorities from PRIORITY_TYPES (faible,normale,important,urgent)
    - `printed` (boolean, optional) - Filter by printed status (true: only printed, false: only non-printed, omit: all)
    - `sort` (csv) - Sort fields with - prefix for DESC (ex: -priority,-reported_date)
    - `include` (csv) - Include optional data (stats). Stats included by default if omitted
- `GET /interventions/{id}` - Get intervention by ID with actions, status logs, and stats (Auth: Optional if AUTH_DISABLED)
- `GET /interventions/{id}/actions` - Get actions for specific intervention (Auth: Optional if AUTH_DISABLED)
- `POST /interventions` - Create a new intervention (Auth: Optional if AUTH_DISABLED)
  - Body (json):
    ```json
    {
      "title": "string|null",
      "machine_id": "uuid|null",
      "type_inter": "string|null",
      "priority": "string|null (faible, normale, important, urgent)",
      "reported_by": "string|null",
      "tech_initials": "string|null",
      "status_actual": "string|null (default: ouvert)",
      "printed_fiche": "boolean|null (default: false)",
      "reported_date": "date|null"
    }
    ```
  - Returns: Full intervention with equipement, stats, actions, status_logs
- `PUT /interventions/{id}` - Update an existing intervention (Auth: Optional if AUTH_DISABLED)
  - Body: Same as POST (all fields optional)
  - Updatable fields: title, machine_id, type_inter, priority, reported_by, tech_initials, status_actual, printed_fiche, reported_date
- `DELETE /interventions/{id}` - Delete an intervention (Auth: Optional if AUTH_DISABLED)

### Intervention Status
| GET     | `/intervention-actions`      | Liste       | [intervention-actions.md](docs/endpoints/intervention-actions.md) |
| GET     | `/intervention-actions/{id}` | Détail      | [intervention-actions.md](docs/endpoints/intervention-actions.md) |
| POST    | `/intervention-actions`      | Créer       | [intervention-actions.md](docs/endpoints/intervention-actions.md) |
id` (uuid, optional) - Filter logs by intervention
    - `skip` (default 0), `limit` (default 100, max 1000)
  - Returns: Array of logs ordered by date DESC with enriched status details
- `GET /intervention_status_log/{id}` - Get specific status change log by ID (Auth: Optional if AUTH_DISABLED)
- `POST /interv| GET     | `/intervention-status`          | Référentiel statuts    | [intervention-status.md](docs/endpoints/intervention-status.md)         |
| GET     | `/intervention-status-log`      | Historique changements | [intervention-status-log.md](docs/endpoints/intervention-status-log.md) |
| GET     | `/intervention-status-log/{id}` | Détail d'un log        | [intervention-status-log.md](docs/endpoints/intervention-status-log.md) |
| POST    | `/intervention-status-log`      | Créer un changement    | [intervention-status-log.md](docs/endpoints/intervention-status-log.md) |
Y-MM-DD", "YYYY-MM-DDTHH:MM:SS", or with timezone. Invalid dates like 2026-01-36 are rejected
    - All status transitions are allowed
    - `notes`: HTML stripped and sanitized
  - Returns: Full log with enriched status details (status_from_detail, status_to_detail)
  - Note: Database trigger automatica| GET     | `/action-categories`                    | Catégories d'actions       | [action-categories.md](docs/endpoints/action-categories.md)   |
| GET     | `/action-categories/{id}`               | Détail catégorie           | [action-categories.md](docs/endpoints/action-categories.md)   |
| GET     | `/action-categories/{id}/subcategories` | Sous-catégories            | [action-categories.md](docs/endpoints/action-categories.md)   |
| GET     | `/action-subcategories`                 | Toutes les sous-catégories | [action-categories.md](docs/endpoints/action-categories.md)   |
| GET     | `/action-subcategories/{id}`            | Détail sous-catégorie      | [action-categories.md](docs/endpoints/action-categories.md)   |
| GET     | `/complexity-factors`                   | Facteurs de complexité     | [complexity-factors.md](docs/endpoints/complexity-factors.md) |
| GET     | `/complexity-factors/{code}`            | Détail facteur             | [complexity-factors.md](docs/endpoints/complexity-factors.md) |
or omitted, uses current timestamp. Allows backdating actions. Supports "YYYY-MM-DD", "YYYY-MM-DDTHH:MM:SS", or with timezone
    - `description`: HTML stripped and sanitized
  - Returns: Full action with subcategory details, complexity stored as `{"AUT": true}` in DB

### Action Categories

- `GET /action_categories` - List all action categories (Auth: Optional if AUTH_DISABLED)
- `GET /action_categories/{id}` - Get specific action category by ID (Auth: Optional if AUTH_DISABLED)
- `GET /action_categories/{id}/subcategories` - Get subcategories for a specific category (Auth: Optional if AUTH_DISABLED)

### Action Subcategories

- `GET /action_subcategories` - List all action subcategories (Auth: Optional if AUTH_DISABLED)
- `GET /action_subcategories/{id}` - Get specific action subcategory by ID (Auth: Optional if AUTH_DISABLED)

### Complexity Factors

- `GET /complexity_factors` - List all complexity factors ordered by category and code (Auth: Optional if AUTH_DISABLED)
- `GET /complexity_factors/{code}` - Get specific complexity factor by code (Auth: Optional if AUTH_DISABLED)

### Equipements

- `GET /equipements` - List all equipements with health (lightweight, cacheable) (Auth: Optional if AUTH_DISABLED)
  - Returns: id, code, name, health (level + reason), parent_id
- `GET | GET     | `/equipement-class`      | Liste       | [equipement-class.md](docs/endpoints/equipement-class.md) |
| GET     | `/equipement-class/{id}` | Détail      | [equipement-class.md](docs/endpoints/equipement-class.md) |
| POST    | `/equipement-class`      | Créer       | [equipement-class.md](docs/endpoints/equipement-class.md) |
| PATCH   | `/equipement-class/{id}` | Modifier    | [equipement-class.md](docs/endpoints/equipement-class.md) |
| DELETE  | `/equipement-class/{id}` | Supprimer   | [equipement-class.md](docs/endpoints/equipement-class.md) |
a-lightweight, polling-friendly) (Auth: Optional if AUTH_DISABLED)
  - Returns: level, reason

### Stats

- `GET /stats/service-status` - Get service health metrics (Auth: Optional if AUTH_DISABLED)
  - Query params: `start_date` (YYYY-MM-DD, default: 3 months ago), `end_date` (YYYY-MM-DD, default: today)
  - Returns: charge, fragmentation, pilotage capacity, top 10 causes, site consumption

### Purchase Requests

- `GET /purchase_requests` - [LEGACY] List all purchase requests with optional filters (Auth: Optional if AUTH_DISABLED)
  - Query params:
    - `skip` (default 0), `limit` (default 100, max 1000)
    - `status` (string, optional) - Filter by derived status (TO_QUALIFY, NO_SUPPLIER_REF, PENDING_DISPATCH, OPEN, QUOTED, ORDERED, PARTIAL, RECEIVED, REJECTED)
    - `intervention_id` (uuid, optional) - Filter by linked intervention
    - `urgency` (string, optional) - Filter by urgency level (normal, high, critical)
  - Returns: Array of purchase requests wit| GET     | `/purchase-requests`                             | Liste [LEGACY]            | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| GET     | `/purchase-requests/list`                        | Liste optimisée [v1.2.0]  | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| GET     | `/purchase-requests/detail/{id}`                 | Détail enrichi [v1.2.0]   | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| GET     | `/purchase-requests/stats`                       | Dashboard stats [v1.2.0]  | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| GET     | `/purchase-requests/{id}`                        | Détail [LEGACY]           | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| GET     | `/purchase-requests/intervention/{id}`           | Par intervention [LEGACY] | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| GET     | `/purchase-requests/intervention/{id}/optimized` | Par intervention [v1.2.0] | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| POST    | `/purchase-requests`                             | Créer                     | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| PUT     | `/purchase-requests/{id}`                        | Modifier                  | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| DELETE  | `/purchase-requests/{id}`                        | Supprimer                 | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| POST    | `/purchase-requests/dispatch`                    | Dispatch auto [v1.2.12]   | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
,
      "urgent": "boolean|null (default: false)",
      "requester_name": "string|null"
    }
    ```
  - Business rules:
    - `item_label` and `quantity` are required
    - `quantity` must be > 0
    - `intervention_id` is optional - links the request to an intervention/action
    - `derived_| GET     | `/stock-items`                           | Liste avec filtres                     | [stock-items.md](docs/endpoints/stock-items.md) |
| GET     | `/stock-items/{id}`                      | Détail                                 | [stock-items.md](docs/endpoints/stock-items.md) |
| GET     | `/stock-items/{id}/with-characteristics` | Détail avec caractéristiques [v1.11.0] | [stock-items.md](docs/endpoints/stock-items.md) |
| GET     | `/stock-items/ref/{ref}`                 | Par référence                          | [stock-items.md](docs/endpoints/stock-items.md) |
| POST    | `/stock-items`                           | Créer (legacy ou template) [v1.11.0]   | [stock-items.md](docs/endpoints/stock-items.md) |
| PUT     | `/stock-items/{id}`                      | Modifier                               | [stock-items.md](docs/endpoints/stock-items.md) |
| PATCH   | `/stock-items/{id}/quantity`             | Modifier quantité                      | [stock-items.md](docs/endpoints/stock-items.md) |
| DELETE  | `/stock-items/{id}`                      | Supprimer                              | [stock-items.md](docs/endpoints/stock-items.md) |
onal filters (Auth: Optional if AUTH_DISABLED)
  - Query params:
    - `skip` (default 0), `limit` (default 100, max 1000)
    - `family_code` (string, optional) - Filter by family code
    - `sub_family_code` (string, optional) - Filter by sub-family code
    - `search` (string, optional) - Search by name or reference (ILIKE)
  - Returns: Array of stock items ordered by name ASC (lightweight schema)
- `GET /stock_items/{id}` - Get specific stock item by ID (Auth: Optional if AUTH_DISABLED)
- `GET /stock_items/ref/{ref}` - Get stock item by reference (Auth: Optional if AUTH_DISABLED)
- `POST /stock_items` - Create a new stock item (Auth: Optional if AUTH_DISABLED)
  - Body (json):
    ```json
    {
      "name": "string",
      "family_code": "string (max 20)",
      "sub_family_code": "string (max 20)",
      "dimension": "string",
      "spec": "string|null (max 50)",
      "quantity": "int|null (default: 0)",
      "unit": "string|null (max 50)",
      "location": "string|null",
      "standars_spec": "uuid|null",
      "manufacturer_item_id": "uuid|null"
    }
    ```
  - Business rules:
    - `name`, `family_code`, `sub_family_code`, `dimension` are required
    - `ref` is auto-generated by database trigger based on family/sub_family/spec/dimension
    - `supplier_refs_count` is managed by database trigger
  - Returns: Full stock item with generated ID and ref
- `PUT /stock_items/{id}` - Update an existing stock item (Auth: Optional if AUTH_DISABLED)
  - Body: Same as POST
  - Note: If family_code, sub_family_code, spec, or dimension change, ref is regenerated by trigger
- `PATCH /stock_items/{id}/quantity` - Update only the quantity of a stock item (Auth: Optional if AUTH_DISABLED)
  - Body: `{ "quantity": int }`
- `DELETE /stock_items/{id}` - Delete a stock item (Auth: Optional if AUTH_DISABLED)

### Supplier Order Lines

- `GET /supplier_order_lines` - List all supplier order lines with optional filters (Auth: Optional if AUTH_DISABLED)
  - Query params:
    - `skip` (default 0), `limit` (default 100, max 1000)
    - `supplier_order_id` (uuid, optional) - Filter by supplier order
    - `stock_item_id` (uuid, optional) - Filter by stock item
    - `is_selected` (boolean, optional) - Filter by selection status
  - Returns: Array of lines (lightweight schema) with purchase_request_| GET     | `/supplier-orders`                   | Liste avec filtres  | [supplier-orders.md](docs/endpoints/supplier-orders.md) |
| GET     | `/supplier-orders/{id}`              | Détail avec lignes  | [supplier-orders.md](docs/endpoints/supplier-orders.md) |
| GET     | `/supplier-orders/number/{n}`        | Par numéro          | [supplier-orders.md](docs/endpoints/supplier-orders.md) |
| POST    | `/supplier-orders`                   | Créer               | [supplier-orders.md](docs/endpoints/supplier-orders.md) |
| PUT     | `/supplier-orders/{id}`              | Modifier            | [supplier-orders.md](docs/endpoints/supplier-orders.md) |
| DELETE  | `/supplier-orders/{id}`              | Supprimer (cascade) | [supplier-orders.md](docs/endpoints/supplier-orders.md) |
| POST    | `/supplier-orders/{id}/export/csv`   | Export CSV          | [supplier-orders.md](docs/endpoints/supplier-orders.md) |
| POST    | `/supplier-orders/{id}/export/email` | Génération email    | [supplier-orders.md](docs/endpoints/supplier-orders.md) |

      ]
    }
    ```
  - Business rules:
    - `supplier_order_id`, `stock_item_id`, `quantity` are required
    - `total_price` is auto-calculated by trigger (quantity \* unit_price)
    - `purchase_requests` is optional - links to purchase requests via M2M table
    - **Only one line can be selected per purchase_request**: when| GET     | `/supplier-order-lines`                                | Liste            | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md) |
| GET     | `/supplier-order-lines/{id}`                           | Détail           | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md) |
| GET     | `/supplier-order-lines/order/{id}`                     | Par commande     | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md) |
| POST    | `/supplier-order-lines`                                | Créer            | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md) |
| PUT     | `/supplier-order-lines/{id}`                           | Modifier         | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md) |
| DELETE  | `/supplier-order-lines/{id}`                           | Supprimer        | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md) |
| POST    | `/supplier-order-lines/{id}/purchase-requests`         | Lier une demande | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md) |
| DELETE  | `/supplier-order-lines/{id}/purchase-requests/{pr_id}` | Délier           | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md) |
x 1000)
    - `status` (string, optional) - Filter by status (OPEN, SENT, PARTIAL, RECEIVED, CLOSED)
    - `supplier_id` (uuid, optional) - Filter by supplier
  - Returns: Array of orders (lightweight schema) with line_count
- `GET /supplier_orders/{id}` - Get specific order by ID with lines (Auth: Optional if AUTH_DISABLED)
- `GET /supplier_orders/number/{order_number}` - Get order by order number (Auth: Optional if AUTH_DISABLED)
- `POST /supplier_orders` - Create a new supplier order (Auth: Optional if AUTH_DISABLED)
  - Body (json):
    ```json
    {
      "supplier_id": "uuid",
      "status": "string|null (default: OPEN)",
      "ordered_at": "datetime|null",
      "expected_delivery_date": "date|null",
      "notes": "string|null",
      "currency": "float|null"
    }
    ```
  - Business rules:
    - `supplier_id` is required
    - `order_number` is auto-generated by database trigger
    - `total_amount` is computed by trigger from lines
  - Returns: Full order with generated ID and order_number
- `PUT /supplier_orders/{id}` - Update an existing order (Auth: Optional if AUTH_DISABLED)
  - | GET     | `/stock-item-suppliers`                    | Liste           | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md) |
| GET     | `/stock-item-suppliers/{id}`               | Détail          | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md) |
| GET     | `/stock-item-suppliers/stock-item/{id}`    | Par article     | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md) |
| GET     | `/stock-item-suppliers/supplier/{id}`      | Par fournisseur | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md) |
| POST    | `/stock-item-suppliers`                    | Créer           | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md) |
| PUT     | `/stock-item-suppliers/{id}`               | Modifier        | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md) |
| POST    | `/stock-item-suppliers/{id}/set-preferred` | Définir préféré | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md) |
| DELETE  | `/stock-item-suppliers/{id}`               | Supprimer       | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md) |
    - `is_active` (boolean, optional) - Filter by active status
    - `search` (string, optional) - Search by name, code, or contact_name (ILIKE)
  - Returns: Array of suppliers (lightweight schema) ordered by name ASC
- `GET /suppliers/{id}` - Get specific supplier by ID (Auth: Optional if AUTH_DISABLED)
- `GET /suppliers/code/{code}` - Get supplier by code (Auth: Optional if AUTH_DISABLED)
- `POST /suppliers` - Create a new supplier (Auth: Optional if AUTH_DISABLED)
  - Body (json):
    ```json
    {
      "name": "string",
      "code": "string|null",
      "contact_name": "string|null",
      "email": "string|null",
      "phone": "string|null",
      "address": "string|null",
      "notes": "string|null",
      "is_active": "boolean|null (default: true)"
    }
    ```
  - Business rules:
    - `name` is required
    - `updated_at` is auto-updated by database trigger
  - Returns: Full supplier with generated ID
- `PUT /suppliers/{id}` - Update an existing supplier (Auth: Optional if AUTH_DISABLED)
  - Body: Same as POST
- `DELETE /suppliers/{id}` - Delete a supplier (Auth: Optional if AUTH_DISABLED)

### Stock Item Suppliers

- `GET /stock_item_suppliers` - List all supplier references with optional filters (Auth: Optional if AUTH_DISABLED)
  - Query params:
    - `skip` (default 0), `limit` (default 100, max 1000)
    - `stock_item_id` (uuid, optional) - Filter by stock item
    - `supplier_id` (uuid, optional) - Filter by supplier
    - `is_preferred` (boolean, optional) - Filter by preferred status
  - Returns: Array of references (lightweight schema) ordered by is_preferred DESC, supplier name ASC
- `GET /stock_item_suppliers/{id}` - Get specific reference by ID (Auth: Optional if AUTH_DISABLED)
- `GET /stock_item_suppliers/stock_item/{stock_item_id}` - Get all supplier references for a stock item (Auth: Optional if AUTH_DISABLED)
- `GET /stock_item_suppliers/supplier/{supplier_id}` - Get all stock item references for a supplier (Auth: Optional if AUTH_DISABLED)
- `POST /stock_item_suppliers` - Create a new supplier reference (Auth: Optional if AUTH_DISABLED)
  - Body (json):
    ```json
    {
      "stock_item_id": "uuid",
      "supplier_id": "uuid",
      "supplier_ref": "string",
      "unit_price": "float|null",
      "min_order_quantity": "int|null (default: 1)",
      "delivery_time_days": "int|null",
      "is_preferred": "boolean|null (default: false)",
      "manufacturer_item_id": "uuid|null"
    }
    ```
  - Business rules:
    - `stock_item_id`, `supplier_id`, `supplier_ref` are required
    - Unique constraint on (stock_item_id, supplier_id)
    - **Only one preferred supplier per stock_item**: when `is_preferred = true`, other references for the same stock_item are automatically set to `is_preferred = false`
    - `supplier_refs_count` on stock_item is updated by database trigger
  - Returns: Full reference with stock_item and supplier details
- `PUT /stock_item_suppliers/{id}` - Update an existing reference (Auth: Optional if AUTH_DISABLED)
  - Body: Same as POST
  - Note: Same `is_preferred` business rule applies
- `POST /stock_item_suppliers/{id}/set_preferred` - Set this reference as preferred for the stock item (Auth: Optional if AUTH_DISABLED)
  - Note: All other references for the same stock_item are set to `is_preferred = false`
- `DELETE /stock_item_suppliers/{id}` - Delete a supplier reference (Auth: Optional if AUTH_DISABLED)

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

## Configuration

- **AUTH_DISABLED**: Set to `true` in `.env` to skip JWT validation for testing
- **DATABASE_URL**: PostgreSQL connection string
- **DIRECTUS_URL**: Authentication service URL
