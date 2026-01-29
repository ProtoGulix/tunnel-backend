# API Manifest

Last updated: 2026-01-29 (v1.1.7 - Supplier Orders endpoint)

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

### Intervention Status

- `GET /intervention_status` - List all available intervention statuses from database (Auth: Optional if AUTH_DISABLED)
  - Returns: id, code, label, color, value for each status

### Intervention Status Log

- `GET /intervention_status_log` - List all status change logs with optional filters (Auth: Optional if AUTH_DISABLED)
  - Query params:
    - `intervention_id` (uuid, optional) - Filter logs by intervention
    - `skip` (default 0), `limit` (default 100, max 1000)
  - Returns: Array of logs ordered by date DESC with enriched status details
- `GET /intervention_status_log/{id}` - Get specific status change log by ID (Auth: Optional if AUTH_DISABLED)
- `POST /intervention_status_log` - Create a new status change log (Auth: Optional if AUTH_DISABLED)
  - Body (json):
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
  - Business rules:
    - `intervention_id`, `status_to`, `technician_id`, `date` are required
    - `status_from` must match current intervention status (except if null for first change)
    - `date`: Must be a valid date/datetime. Supports "YYYY-MM-DD", "YYYY-MM-DDTHH:MM:SS", or with timezone. Invalid dates like 2026-01-36 are rejected
    - All status transitions are allowed
    - `notes`: HTML stripped and sanitized
  - Returns: Full log with enriched status details (status_from_detail, status_to_detail)
  - Note: Database trigger automatically updates intervention.status_actual with status_to

### Intervention Actions

- `GET /intervention_actions` - List all intervention actions (Auth: Optional if AUTH_DISABLED)
- `GET /intervention_actions/{id}` - Get specific intervention action by ID (Auth: Optional if AUTH_DISABLED)
- `POST /intervention_actions` - Add a new action to an intervention (Auth: Optional if AUTH_DISABLED)
  - Body (json):
    ```json
    {
      "intervention_id": "uuid",
      "description": "string",
      "time_spent": 0.75,
      "action_subcategory": 30,
      "tech": "uuid",
      "complexity_score": 7,
      "complexity_anotation": "AUT",
      "created_at": "datetime|null"
    }
    ```
  - Business rules:
    - `time_spent`: Quarter hours only (0.25, 0.5, 0.75, 1.0...), minimum 0.25
    - `complexity_score`: Integer between 1 and 10
    - `complexity_anotation`: Optional if score ≤ 5, **required** if score > 5. Code must exist in complexity_factor table
    - `created_at`: Optional datetime. If null or omitted, uses current timestamp. Allows backdating actions. Supports "YYYY-MM-DD", "YYYY-MM-DDTHH:MM:SS", or with timezone
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
- `GET /equipements/{id}` - Get specific equipement with health and children (Auth: Optional if AUTH_DISABLED)
  - Returns: id, code, name, health (level + reason + rules_triggered), parent_id, children_ids
- `GET /equipements/{id}/stats` - Get detailed statistics for equipement (opt-in) (Auth: Optional if AUTH_DISABLED)
  - Query params: `start_date` (YYYY-MM-DD, optional, default NULL = all), `end_date` (YYYY-MM-DD, optional, default NOW)
  - Returns: interventions (open, closed, by_status, by_priority)
- `GET /equipements/{id}/health` - Get health only (ultra-lightweight, polling-friendly) (Auth: Optional if AUTH_DISABLED)
  - Returns: level, reason

### Stats

- `GET /stats/service-status` - Get service health metrics (Auth: Optional if AUTH_DISABLED)
  - Query params: `start_date` (YYYY-MM-DD, default: 3 months ago), `end_date` (YYYY-MM-DD, default: today)
  - Returns: charge, fragmentation, pilotage capacity, top 10 causes, site consumption

### Purchase Requests

- `GET /purchase_requests` - List all purchase requests with optional filters (Auth: Optional if AUTH_DISABLED)
  - Query params:
    - `skip` (default 0), `limit` (default 100, max 1000)
    - `status` (string, optional) - Filter by status (open, approved, ordered, received, rejected)
    - `intervention_id` (uuid, optional) - Filter by linked intervention
    - `urgency` (string, optional) - Filter by urgency level (normal, high, critical)
  - Returns: Array of purchase requests ordered by created_at DESC
- `GET /purchase_requests/{id}` - Get specific purchase request by ID (Auth: Optional if AUTH_DISABLED)
- `GET /purchase_requests/intervention/{intervention_id}` - Get all purchase requests linked to an intervention (Auth: Optional if AUTH_DISABLED)
- `POST /purchase_requests` - Create a new purchase request (Auth: Optional if AUTH_DISABLED)
  - Body (json):
    ```json
    {
      "item_label": "string",
      "quantity": "int (> 0)",
      "stock_item_id": "uuid|null",
      "unit": "string|null",
      "requested_by": "string|null",
      "urgency": "string|null (default: normal)",
      "reason": "string|null",
      "notes": "string|null",
      "workshop": "string|null",
      "intervention_id": "uuid|null",
      "quantity_requested": "int|null",
      "urgent": "boolean|null (default: false)",
      "requester_name": "string|null"
    }
    ```
  - Business rules:
    - `item_label` and `quantity` are required
    - `quantity` must be > 0
    - `intervention_id` is optional - links the request to an intervention/action
    - Default status is "open"
  - Returns: Full purchase request with generated ID and timestamps
- `PUT /purchase_requests/{id}` - Update an existing purchase request (Auth: Optional if AUTH_DISABLED)
  - Body: Same as POST (all fields optional except required ones)
  - Additional updatable fields: `quantity_approved`, `approver_name`, `approved_at`
- `DELETE /purchase_requests/{id}` - Delete a purchase request (Auth: Optional if AUTH_DISABLED)

### Stock Items

- `GET /stock_items` - List all stock items with optional filters (Auth: Optional if AUTH_DISABLED)
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
  - Returns: Array of lines (lightweight schema) with purchase_request_count
- `GET /supplier_order_lines/{id}` - Get specific line by ID with stock_item and purchase_requests (Auth: Optional if AUTH_DISABLED)
- `GET /supplier_order_lines/order/{supplier_order_id}` - Get all lines for a supplier order with full details (Auth: Optional if AUTH_DISABLED)
- `POST /supplier_order_lines` - Create a new supplier order line (Auth: Optional if AUTH_DISABLED)
  - Body (json):
    ```json
    {
      "supplier_order_id": "uuid",
      "stock_item_id": "uuid",
      "quantity": "int (> 0)",
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
      "purchase_requests": [
        { "purchase_request_id": "uuid", "quantity": "int" }
      ]
    }
    ```
  - Business rules:
    - `supplier_order_id`, `stock_item_id`, `quantity` are required
    - `total_price` is auto-calculated by trigger (quantity * unit_price)
    - `purchase_requests` is optional - links to purchase requests via M2M table
  - Returns: Full line with stock_item and purchase_requests
- `PUT /supplier_order_lines/{id}` - Update an existing line (Auth: Optional if AUTH_DISABLED)
  - Body: Same as POST
  - Note: If `purchase_requests` is provided, existing links are replaced
- `DELETE /supplier_order_lines/{id}` - Delete a line (cascades to M2M) (Auth: Optional if AUTH_DISABLED)
- `POST /supplier_order_lines/{id}/purchase_requests` - Link a purchase request to a line (Auth: Optional if AUTH_DISABLED)
  - Body: `{ "purchase_request_id": "uuid", "quantity": int }`
  - Note: Upserts - updates quantity if link already exists
- `DELETE /supplier_order_lines/{id}/purchase_requests/{purchase_request_id}` - Unlink a purchase request (Auth: Optional if AUTH_DISABLED)

### Supplier Orders

- `GET /supplier_orders` - List all supplier orders with optional filters (Auth: Optional if AUTH_DISABLED)
  - Query params:
    - `skip` (default 0), `limit` (default 100, max 1000)
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
  - Body: Same as POST
  - Note: `order_number` cannot be modified
- `DELETE /supplier_orders/{id}` - Delete an order (cascades to lines) (Auth: Optional if AUTH_DISABLED)

## Schemas

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
    "avg_complexity": "float|null"
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

### PurchaseRequestOut

Note:
- When `stock_item_id` is not null, the `stock_item` object is automatically populated
- `order_lines` contains all supplier order lines linked via M2M table

```json
{
  "id": "uuid",
  "status": "string",
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

### LinkedOrderLine (embedded in PurchaseRequestOut)

```json
{
  "id": "uuid",
  "supplier_order_line_id": "uuid",
  "quantity_allocated": "int",
  "supplier_order_id": "uuid",
  "stock_item_id": "uuid",
  "stock_item_name": "string|null",
  "stock_item_ref": "string|null",
  "quantity": "int",
  "unit_price": "float|null",
  "total_price": "float|null",
  "quantity_received": "int|null",
  "is_selected": "boolean|null",
  "created_at": "datetime|null"
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
  "purchase_requests": [
    { "purchase_request_id": "uuid", "quantity": "int" }
  ]
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

Note: Includes `lines` array with all supplier order lines for this order.

```json
{
  "id": "uuid",
  "order_number": "string",
  "supplier_id": "uuid",
  "status": "string",
  "total_amount": "float|null",
  "ordered_at": "datetime|null",
  "expected_delivery_date": "date|null",
  "received_at": "datetime|null",
  "notes": "string|null",
  "currency": "float|null",
  "lines": ["SupplierOrderLineListItem"],
  "created_at": "datetime|null",
  "updated_at": "datetime|null"
}
```

### SupplierOrderListItem (lightweight)

```json
{
  "id": "uuid",
  "order_number": "string",
  "supplier_id": "uuid",
  "status": "string",
  "total_amount": "float|null",
  "ordered_at": "datetime|null",
  "expected_delivery_date": "date|null",
  "line_count": "int|null"
}
```

## Configuration

- **AUTH_DISABLED**: Set to `true` in `.env` to skip JWT validation for testing
- **DATABASE_URL**: PostgreSQL connection string
- **DIRECTUS_URL**: Authentication service URL
