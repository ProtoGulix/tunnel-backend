# API Manifest

Last updated: 2026-02-12 (v1.8.0)

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
      "complexity_factor": "AUT",
      "created_at": "datetime|null"
    }
    ```
  - Business rules:
    - `time_spent`: Quarter hours only (0.25, 0.5, 0.75, 1.0...), minimum 0.25
    - `complexity_score`: Integer between 1 and 10
    - `complexity_factor`: Optional if score ≤ 5, **required** if score > 5. Code must exist in complexity_factor table
    - `created_at`: Optional datetime. If null or omitted, uses current timestamp. Allows backdating actions. Supports "YYYY-MM-DD", "YYYY-MM-DDTHH:MM:SS", or with timezone
    - `description`: HTML stripped and sanitized
  - Returns: Full action with subcategory details

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
  - Returns: id, code, name, health (level + reason), parent_id, **equipement_class** (⚠️ **NEW in v1.3.0**)
  - Response (json):
    ```json
    [
      {
        "id": "5e6b5a20-5d7f-4f6b-9a1f-4ccfb0b7a2a1",
        "code": "EQ-001",
        "name": "Scie principale",
        "health": {
          "level": "ok",
          "reason": "Aucune anomalie détectée",
          "rules_triggered": null
        },
        "parent_id": null,
        "equipement_class": {
          "id": "b28f1f4f-2a2a-4c9a-9b58-9f9a6d5f0b0c",
          "code": "SCIE",
          "label": "Scie"
        }
      }
    ]
    ```
- `GET /equipements/{id}` - Get specific equipement with health and children (Auth: Optional if AUTH_DISABLED)
  - Returns: id, code, name, health (level + reason + rules_triggered), parent_id, children_ids, **equipement_class** (⚠️ **NEW in v1.3.0**)
  - Response (json):
    ```json
    {
      "id": "5e6b5a20-5d7f-4f6b-9a1f-4ccfb0b7a2a1",
      "code": "EQ-001",
      "name": "Scie principale",
      "health": {
        "level": "warning",
        "reason": "Maintenance planifiée dépassée",
        "rules_triggered": ["maintenance_overdue"]
      },
      "parent_id": null,
      "equipement_class": {
        "id": "b28f1f4f-2a2a-4c9a-9b58-9f9a6d5f0b0c",
        "code": "SCIE",
        "label": "Scie"
      },
      "children_ids": ["7f2cda3c-1b2e-4e1e-a0b7-9a1e2f3b4c5d"]
    }
    ```
- `POST /equipements` - Create a new equipement (Auth: Optional if AUTH_DISABLED)
  - Body (json):
    ```json
    {
      "name": "Scie principale",
      "code": "EQ-001",
      "parent_id": null,
      "equipement_class_id": "b28f1f4f-2a2a-4c9a-9b58-9f9a6d5f0b0c"
    }
    ```
  - Returns: Full equipement with health, children_ids, equipement_class
  - Response (json):
    ```json
    {
      "id": "5e6b5a20-5d7f-4f6b-9a1f-4ccfb0b7a2a1",
      "code": "EQ-001",
      "name": "Scie principale",
      "health": {
        "level": "ok",
        "reason": "Aucune anomalie detectee",
        "rules_triggered": []
      },
      "parent_id": null,
      "equipement_class": {
        "id": "b28f1f4f-2a2a-4c9a-9b58-9f9a6d5f0b0c",
        "code": "SCIE",
        "label": "Scie"
      },
      "children_ids": []
    }
    ```
- `PUT /equipements/{id}` - Update an existing equipement (Auth: Optional if AUTH_DISABLED)
  - Body (json): Same as POST (all fields optional)
  - Response (json):
    ```json
    {
      "id": "5e6b5a20-5d7f-4f6b-9a1f-4ccfb0b7a2a1",
      "code": "EQ-001",
      "name": "Scie principale",
      "health": {
        "level": "ok",
        "reason": "Aucune anomalie detectee",
        "rules_triggered": []
      },
      "parent_id": null,
      "equipement_class": {
        "id": "b28f1f4f-2a2a-4c9a-9b58-9f9a6d5f0b0c",
        "code": "SCIE",
        "label": "Scie"
      },
      "children_ids": []
    }
    ```
- `DELETE /equipements/{id}` - Delete an equipement (Auth: Optional if AUTH_DISABLED)
  - Returns: 204 No Content
- `GET /equipements/{id}/stats` - Get detailed statistics for equipement (opt-in) (Auth: Optional if AUTH_DISABLED)
  - Query params: `start_date` (YYYY-MM-DD, optional, default NULL = all), `end_date` (YYYY-MM-DD, optional, default NOW)
  - Returns: interventions (open, closed, by_status, by_priority)
  - Response (json):
    ```json
    {
      "interventions": {
        "open": 2,
        "closed": 5,
        "by_status": {
          "ouvert": 2,
          "ferme": 5
        },
        "by_priority": {
          "faible": 1,
          "normale": 4,
          "urgent": 2
        }
      }
    }
    ```
- `GET /equipements/{id}/health` - Get health only (ultra-lightweight, polling-friendly) (Auth: Optional if AUTH_DISABLED)
  - Returns: level, reason
  - Response (json):
    ```json
    {
      "level": "ok",
      "reason": "Aucune anomalie détectée"
    }
    ```

### Equipement Classes (⚠️ NEW in v1.3.0)

Data mapping: table `equipement_class`, column `machine.equipement_class_id`.

- `GET /equipement_class` - List all equipement classes (Auth: Optional if AUTH_DISABLED)
  - Returns: Array of equipement classes ordered by code ASC
  - Response (json):
    ```json
    [
      {
        "id": "b28f1f4f-2a2a-4c9a-9b58-9f9a6d5f0b0c",
        "code": "SCIE",
        "label": "Scie",
        "description": "Machines de sciage"
      }
    ]
    ```
- `GET /equipement_class/{id}` - Get specific equipement class by ID (Auth: Optional if AUTH_DISABLED)
  - Response (json):
    ```json
    {
      "id": "b28f1f4f-2a2a-4c9a-9b58-9f9a6d5f0b0c",
      "code": "SCIE",
      "label": "Scie",
      "description": "Machines de sciage"
    }
    ```
- `POST /equipement_class` - Create a new equipement class (Auth: Optional if AUTH_DISABLED)
  - Body (json):
    ```json
    {
      "code": "string (unique)",
      "label": "string",
      "description": "string|null"
    }
    ```
  - Business rules:
    - `code` and `label` are required
    - `code` must be unique
  - Returns: Full equipement class with generated UUID
  - Response (json):
    ```json
    {
      "id": "b28f1f4f-2a2a-4c9a-9b58-9f9a6d5f0b0c",
      "code": "SCIE",
      "label": "Scie",
      "description": "Machines de sciage"
    }
    ```
- `PATCH /equipement_class/{id}` - Update an existing equipement class (Auth: Optional if AUTH_DISABLED)
  - Body: Same as POST (all fields optional)
  - Note: If code changes, uniqueness is validated
  - Response (json):
    ```json
    {
      "id": "b28f1f4f-2a2a-4c9a-9b58-9f9a6d5f0b0c",
      "code": "SCIE",
      "label": "Scie",
      "description": "Machines de sciage"
    }
    ```
- `DELETE /equipement_class/{id}` - Delete an equipement class (Auth: Optional if AUTH_DISABLED)
  - Business rules:
    - Cannot delete class if any equipement is using it (returns ValidationError)
  - Returns: 204 No Content on success

### Stats

- `GET /stats/service-status` - Get service health metrics (Auth: Optional if AUTH_DISABLED)
  - Query params: `start_date` (YYYY-MM-DD, default: 3 months ago), `end_date` (YYYY-MM-DD, default: today)
  - Returns: charge, fragmentation, pilotage capacity, top 10 causes, site consumption

- `GET /stats/charge-technique` - [BETA] Analyse de la charge technique (Auth: Optional if AUTH_DISABLED)
  - Query params:
    - `start_date` (YYYY-MM-DD, default: 3 months ago)
    - `end_date` (YYYY-MM-DD, default: today)
    - `period_type` (string, default: `custom`) - Découpage: `month`, `week`, `quarter`, `custom`
  - Business rules:
    - Analyse par **classe d'équipement** (jamais par machine isolée, jamais par technicien)
    - Une action DEP est **évitable** si : `complexity_factor IS NOT NULL` OU action répétée ≥3 fois (même `action_subcategory` + même `equipement_class`) sur la période
    - Taux de dépannage évitable : <20% vert, 20-40% orange, >40% rouge
  - Returns: `ChargeTechniqueResponse`

- `GET /stats/anomalies-saisie` - [BETA] Détection des anomalies de saisie des actions d'intervention (Auth: Optional if AUTH_DISABLED)
  - Query params:
    - `start_date` (YYYY-MM-DD, default: 3 months ago)
    - `end_date` (YYYY-MM-DD, default: today)
  - Description: Analyse la qualité des saisies d'actions et détecte 6 types d'anomalies :
    - **too_repetitive** : Même sous-catégorie + même machine répétée plus de 3 fois dans un mois
    - **too_fragmented** : Actions courtes (< 1h) sur une même sous-catégorie apparaissant 5+ fois
    - **too_long_for_category** : Actions > 4h sur des catégories normalement rapides (BAT_NET, BAT_RAN, etc.)
    - **bad_classification** : Actions BAT_NET dont la description contient des mots-clés techniques suspects (mécanique, hydraulique, etc.)
    - **back_to_back** : Même technicien + même intervention avec deux actions consécutives espacées de moins de 24h
    - **low_value_high_load** : Catégories à faible valeur ajoutée dont le temps cumulé dépasse 30h
  - Chaque anomalie a une sévérité `high` ou `medium` selon des seuils configurables
  - La réponse inclut un bloc `config` avec les seuils et listes appliqués
  - Returns: `AnomaliesSaisieResponse`

- `GET /stats/qualite-donnees` - Détection des problèmes de complétude et cohérence des données (Auth: Optional if AUTH_DISABLED)
  - Query params:
    - `severite` (string, optional) - Filter by severity: `high`, `medium`
    - `entite` (string, optional) - Filter by entity: `intervention_action`, `intervention`, `stock_item`, `purchase_request`
    - `code` (string, optional) - Filter by specific anomaly code
  - Description: Identifie les données manquantes ou incohérentes avec les règles métier explicites. 13 règles de détection sur 4 entités :
    - **intervention_action** : `action_time_null` (high), `action_complexity_sans_facteur` (high), `action_subcategory_null` (high), `action_tech_null` (medium), `action_description_vide` (medium), `action_time_suspect` (medium), `action_sur_intervention_fermee` (high)
    - **intervention** : `intervention_fermee_sans_action` (high), `intervention_sans_type` (medium), `intervention_en_cours_inactive` (medium)
    - **stock_item** : `stock_sans_seuil_min` (medium), `stock_sans_fournisseur` (medium)
    - **purchase_request** : `demande_sans_stock_item` (medium)
  - Tri : high d'abord, puis medium, puis par entité, puis created_at DESC
  - Chaque règle est une requête SQL indépendante
  - Returns: `QualiteDonneesResponse`

### Purchase Requests

- `GET /purchase_requests` - [LEGACY] List all purchase requests with optional filters (Auth: Optional if AUTH_DISABLED)
  - Query params:
    - `skip` (default 0), `limit` (default 100, max 1000)
    - `status` (string, optional) - Filter by derived status (TO_QUALIFY, NO_SUPPLIER_REF, PENDING_DISPATCH, OPEN, QUOTED, ORDERED, PARTIAL, RECEIVED, REJECTED)
    - `intervention_id` (uuid, optional) - Filter by linked intervention
    - `urgency` (string, optional) - Filter by urgency level (normal, high, critical)
  - Returns: Array of purchase requests with `derived_status` ordered by created_at DESC
- `GET /purchase_requests/list` - [v1.2.0] Liste optimisée légère pour tableaux (Auth: Optional if AUTH_DISABLED)
  - Query params: same as above
  - Returns: `PurchaseRequestListItem[]` - payload ~95% plus léger
- `GET /purchase_requests/detail/{id}` - [v1.2.0] Détail complet avec contexte enrichi (Auth: Optional if AUTH_DISABLED)
  - Returns: `PurchaseRequestDetail` avec intervention, stock_item, order_lines enrichis
- `GET /purchase_requests/stats` - [v1.2.0] Statistiques agrégées pour dashboards (Auth: Optional if AUTH_DISABLED)
  - Query params: `start_date`, `end_date`, `group_by`
  - Returns: `PurchaseRequestStats`
- `GET /purchase_requests/{id}` - [LEGACY] Get specific purchase request by ID (Auth: Optional if AUTH_DISABLED)
- `GET /purchase_requests/intervention/{intervention_id}` - [LEGACY] Get all purchase requests linked to an intervention (Auth: Optional if AUTH_DISABLED)
- `GET /purchase_requests/intervention/{intervention_id}/optimized` - [v1.2.0] Filtre par intervention avec choix de granularité (Auth: Optional if AUTH_DISABLED)
  - Query params: `view` (list|full)
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
    - `derived_status` is calculated automatically based on progress
  - Returns: Full purchase request with generated ID, timestamps and `derived_status`
- `PUT /purchase_requests/{id}` - Update an existing purchase request (Auth: Optional if AUTH_DISABLED)
  - Body: Same as POST (all fields optional except required ones)
  - Additional updatable fields: `quantity_approved`, `approver_name`, `approved_at`
  - Note: `status` is no longer manually updatable - use `derived_status` which is calculated automatically
- `DELETE /purchase_requests/{id}` - Delete a purchase request (Auth: Optional if AUTH_DISABLED)
- `POST /purchase_requests/dispatch` - [v1.2.12] Dispatch automatique des demandes PENDING_DISPATCH (Auth: Optional if AUTH_DISABLED)
  - Dispatches all purchase requests with status PENDING_DISPATCH to supplier orders
  - For each request, finds supplier references linked to stock_item
  - Creates or reuses OPEN supplier_orders per supplier
  - Creates supplier_order_lines linked to purchase_requests
  - Returns: `DispatchResult` with dispatched_count, created_orders, errors

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
    - `total_price` is auto-calculated by trigger (quantity \* unit_price)
    - `purchase_requests` is optional - links to purchase requests via M2M table
    - **Only one line can be selected per purchase_request**: when `is_selected = true`, all other lines linked to the same purchase_request(s) are automatically deselected
  - Returns: Full line with stock_item and purchase_requests
- `PUT /supplier_order_lines/{id}` - Update an existing line (Auth: Optional if AUTH_DISABLED)
  - Body: Same as POST
  - Notes:
    - If `purchase_requests` is provided, existing links are replaced
    - **Only one line can be selected per purchase_request**: when `is_selected = true`, all other lines linked to the same purchase_request(s) are automatically deselected
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
- `POST /supplier_orders/{id}/export/csv` - Export order as CSV file (Auth: Optional if AUTH_DISABLED)
  - Returns: CSV file with headers: Article, Référence, Spécification, Fabricant, Réf. Fabricant, Quantité, Unité, Prix unitaire, Prix total, Demandes liées
  - Exports all lines of the order
  - Content-Type: text/csv
  - **Configuration**: Templates modifiables dans `config/export_templates.py` (headers, format, filename)
- `POST /supplier_orders/{id}/export/email` - Generate email content for order (Auth: Optional if AUTH_DISABLED)
  - Returns: `EmailExportOut` with subject, body_text, body_html, supplier_email
  - Includes all lines of the order
  - **Configuration**: Templates modifiables dans `config/export_templates.py` (subject, body_text, body_html)

### Suppliers

- `GET /suppliers` - List all suppliers with optional filters (Auth: Optional if AUTH_DISABLED)
  - Query params:
    - `skip` (default 0), `limit` (default 100, max 1000)
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

⚠️ **BREAKING CHANGE in v1.4.0**: Field `complexity_anotation` renamed to `complexity_factor`. Type changed from `object|null` to `string|null` (now a direct FK to complexity_factor table).

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
  "complexity_factor": "string|null",
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

⚠️ **BREAKING CHANGE in v1.4.0**: Field `complexity_anotation` renamed to `complexity_factor`.

Notes:

- `complexity_factor` is optional if `complexity_score` ≤ 5, but required if `complexity_score` > 5
- `created_at` is optional - defaults to current timestamp if null/omitted, allowing backdating of actions. Supports "YYYY-MM-DD", "YYYY-MM-DDTHH:MM:SS", or with timezone

```json
{
  "intervention_id": "uuid",
  "description": "string",
  "time_spent": "float",
  "action_subcategory": "int",
  "tech": "uuid",
  "complexity_score": "int",
  "complexity_factor": "string|null",
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

⚠️ **BREAKING CHANGE in v1.3.0**: New `equipement_class` field added.

```json
{
  "id": "uuid",
  "code": "string|null",
  "name": "string",
  "health": {
    "level": "ok|maintenance|warning|critical",
    "reason": "string"
  },
  "parent_id": "uuid|null",
  "equipement_class": {
    "id": "uuid",
    "code": "string",
    "label": "string"
  } | null
}
```

Note: Sorted by urgent count (desc), then open count (desc), then name (asc). Health rules: urgent >= 1 → critical, open > 5 → warning, open > 0 → maintenance, else ok. `equipement_class` is null if no class is assigned to the equipement.

### EquipementDetail (GET /equipements/{id})

⚠️ **BREAKING CHANGE in v1.3.0**: New `equipement_class` field added.

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
  "equipement_class": {
    "id": "uuid",
    "code": "string",
    "label": "string"
  } | null,
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

### ChargeTechniqueResponse

```json
{
  "params": {
    "start_date": "date",
    "end_date": "date",
    "period_type": "month|week|quarter|custom"
  },
  "guide": {
    "objectif": "string (description de l'objectif de l'analyse)",
    "seuils_taux_evitable": [
      {
        "min": "float",
        "max": "float|null",
        "color": "green|orange|red",
        "label": "string",
        "action": "string (recommandation d'action)"
      }
    ],
    "actions_par_categorie": [
      {
        "category": "string (Ressources, Technique, Information, Organisation, Environnement, Logistique, Compétence, Divers)",
        "color": "string (hex color)",
        "action": "string (recommandation d'action)"
      }
    ]
  },
  "periods": [
    {
      "period": {
        "start_date": "date",
        "end_date": "date",
        "days": "int"
      },
      "charges": {
        "charge_totale": "float",
        "charge_depannage": "float",
        "charge_constructive": "float",
        "charge_depannage_evitable": "float",
        "charge_depannage_subi": "float"
      },
      "taux_depannage_evitable": {
        "taux": "float (0-100)",
        "status": {
          "color": "green|orange|red",
          "text": "string"
        }
      },
      "cause_breakdown": [
        {
          "code": "string (ACC, AUT, CMP, COM, DIAG, DOC, OUT, PCE, PCS, PRD, RCH, TEM, VIE)",
          "label": "string|null",
          "category": "string|null (Environnement, Divers, Compétence, Organisation, Technique, Information, Ressources, Logistique)",
          "hours": "float",
          "action_count": "int",
          "percent": "float"
        }
      ],
      "by_equipement_class": [
        {
          "equipement_class_id": "uuid",
          "equipement_class_code": "string",
          "equipement_class_label": "string",
          "charge_totale": "float",
          "charge_depannage": "float",
          "charge_constructive": "float",
          "charge_depannage_evitable": "float",
          "taux_depannage_evitable": "float (0-100)",
          "status": {
            "color": "green|orange|red",
            "text": "string"
          },
          "evitable_breakdown": {
            "hours_with_factor": "float (heures avec facteur de complexité renseigné)",
            "hours_systemic": "float (heures de problèmes récurrents ≥3 fois)",
            "hours_both": "float (heures avec les deux critères)",
            "total_evitable": "float (total évitable = somme - doublon)"
          },
          "explanation": "string (diagnostic détaillé avec ventilation par critère)",
          "top_causes": [
            {
              "code": "string (ACC, PCE, DOC, etc.)",
              "label": "string|null",
              "category": "string|null (Technique, Logistique, etc.)",
              "hours": "float",
              "percent": "float (% du dépannage évitable de cette classe)"
            }
          ],
          "recommended_action": "string (action concrète recommandée pour cette classe spécifique)"
        }
      ]
    }
  ]
}
```

### AnomaliesSaisieResponse

```json
{
  "params": {
    "start_date": "date|null",
    "end_date": "date|null"
  },
  "summary": {
    "total_anomalies": "int",
    "by_type": {
      "too_repetitive": "int",
      "too_fragmented": "int",
      "too_long_for_category": "int",
      "bad_classification": "int",
      "back_to_back": "int",
      "low_value_high_load": "int"
    },
    "by_severity": {
      "high": "int",
      "medium": "int"
    }
  },
  "anomalies": {
    "too_repetitive": [
      {
        "category": "string (subcategory code)",
        "categoryName": "string",
        "machine": "string",
        "machineId": "string",
        "month": "string (YYYY-MM)",
        "count": "int",
        "interventionCount": "int",
        "severity": "high|medium",
        "message": "string"
      }
    ],
    "too_fragmented": [
      {
        "category": "string",
        "categoryName": "string",
        "count": "int",
        "totalTime": "float",
        "avgTime": "float",
        "interventionCount": "int",
        "severity": "high|medium",
        "message": "string"
      }
    ],
    "too_long_for_category": [
      {
        "actionId": "string",
        "category": "string",
        "categoryName": "string",
        "time": "float",
        "intervention": "string",
        "interventionId": "string",
        "interventionTitle": "string",
        "machine": "string",
        "tech": "string (Prénom Nom)",
        "date": "string (ISO 8601)",
        "severity": "high|medium",
        "message": "string"
      }
    ],
    "bad_classification": [
      {
        "actionId": "string",
        "category": "string",
        "categoryName": "string",
        "foundKeywords": ["string"],
        "description": "string",
        "intervention": "string",
        "interventionId": "string",
        "interventionTitle": "string",
        "machine": "string",
        "tech": "string",
        "date": "string (ISO 8601)",
        "severity": "high|medium",
        "message": "string"
      }
    ],
    "back_to_back": [
      {
        "tech": "string",
        "techId": "string",
        "intervention": "string",
        "interventionId": "string",
        "interventionTitle": "string",
        "machine": "string",
        "daysDiff": "float",
        "date1": "string (ISO 8601)",
        "date2": "string (ISO 8601)",
        "category1": "string",
        "category2": "string",
        "severity": "high|medium",
        "message": "string"
      }
    ],
    "low_value_high_load": [
      {
        "category": "string",
        "categoryName": "string",
        "totalTime": "float",
        "count": "int",
        "avgTime": "float",
        "interventionCount": "int",
        "machineCount": "int",
        "techCount": "int",
        "severity": "high|medium",
        "message": "string"
      }
    ]
  },
  "config": {
    "thresholds": {
      "repetitive": { "monthly_count": 3, "high_severity_count": 6 },
      "fragmented": { "max_duration": 1.0, "min_occurrences": 5, "high_severity_count": 10 },
      "too_long": { "max_duration": 4.0, "high_severity_duration": 8.0 },
      "bad_classification": { "high_severity_keywords": 2 },
      "back_to_back": { "max_days_diff": 1.0, "high_severity_days": 0.5 },
      "low_value_high_load": { "min_total_hours": 30.0, "high_severity_hours": 60.0 }
    },
    "simple_categories": ["BAT_NET", "BAT_RAN", "BAT_DIV", "LOG_MAG", "LOG_REC", "LOG_INV"],
    "low_value_categories": ["BAT_NET", "BAT_RAN", "BAT_DIV", "LOG_MAG", "LOG_REC"],
    "suspicious_keywords": ["mécanique", "hydraulique", "électrique", "..."]
  }
}
```

### QualiteDonneesResponse

```json
{
  "total": "int",
  "par_severite": {
    "high": "int",
    "medium": "int"
  },
  "problemes": [
    {
      "code": "string (action_time_null, action_complexity_sans_facteur, ...)",
      "severite": "high|medium",
      "entite": "intervention_action|intervention|stock_item|purchase_request",
      "entite_id": "string (uuid)",
      "message": "string (label en français)",
      "contexte": {
        "intervention_id": "string|null",
        "intervention_code": "string|null",
        "created_at": "string (ISO 8601)|null",
        "stock_item_ref": "string|null",
        "stock_item_name": "string|null",
        "purchase_request_id": "string|null"
      }
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

### Exports (v1.8.0+)

- `GET /exports/interventions/{id}/pdf` - Generate PDF report for intervention (Auth: Required - JWT Bearer token)
  - Headers:
    - `Authorization: Bearer {token}` (required)
  - Returns: PDF file (application/pdf)
  - Filename: `{intervention_code}.pdf` (e.g., "INT-2026-001.pdf")
  - Features:
    - A4 optimized layout with professional formatting
    - Complete intervention data: equipment, actions, status logs, statistics
    - Customizable Jinja2 HTML template
    - WeasyPrint rendering for print quality
    - ETag support for client-side caching
  - Errors:
    - 400: Invalid UUID format
    - 401: Missing or invalid JWT token
    - 404: Intervention not found
    - 500: PDF generation failed
  - Example:
    ```bash
    curl -X GET "http://localhost:8000/exports/interventions/{id}/pdf" \
         -H "Authorization: Bearer {token}" \
         -o intervention.pdf
    ```

- `GET /exports/interventions/{id}/qrcode` - Generate QR code linking to intervention (Auth: Public)
  - Headers: None (public endpoint for printing on physical reports)
  - Returns: PNG image (image/png)
  - Filename: `{intervention_code}.png` (inline display, not download)
  - QR Content: `{FRONTEND_URL}/interventions/{id}` (configurable via EXPORT_QR_BASE_URL)
  - Features:
    - Optional logo overlay (configured via EXPORT_QR_LOGO_PATH)
    - High error correction (ERROR_CORRECT_H) for reliable scanning
    - Optimized for printing on physical reports
    - 1 hour cache (public, max-age=3600)
  - Errors:
    - 400: Invalid UUID format
    - 404: Intervention not found
    - 500: QR generation failed
  - Example:
    ```bash
    curl -X GET "http://localhost:8000/exports/interventions/{id}/qrcode" \
         -o qrcode.png
    ```

## Configuration

- **AUTH_DISABLED**: Set to `true` in `.env` to skip JWT validation for testing
- **DATABASE_URL**: PostgreSQL connection string
- **DIRECTUS_URL**: Authentication service URL

### Export Configuration (v1.8.0+)

- **EXPORT_TEMPLATE_DIR**: Template directory path (default: `api/exports/templates`)
- **EXPORT_TEMPLATE_FILE**: HTML template filename (default: `fiche_intervention_v1.html`)
- **EXPORT_QR_BASE_URL**: Frontend base URL for QR codes (default: `http://localhost:5173/interventions`)
- **EXPORT_QR_LOGO_PATH**: Logo overlay path for QR codes (default: `api/exports/templates/logo.png`)
