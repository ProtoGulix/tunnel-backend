# API Manifest

Last updated: 2026-01-25

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
    - `sort` (csv) - Sort fields with - prefix for DESC (ex: -priority,-reported_date)
    - `include` (csv) - Include optional data (stats). Stats included by default if omitted
- `GET /interventions/{id}` - Get intervention by ID with actions and stats (Auth: Optional if AUTH_DISABLED)
- `GET /interventions/{id}/actions` - Get actions for specific intervention (Auth: Optional if AUTH_DISABLED)

### Intervention Status

- `GET /intervention_status` - List all available intervention statuses from database (Auth: Optional if AUTH_DISABLED)
  - Returns: id, code, label, color, value for each status

### Intervention Actions

- `GET /intervention_actions` - List all intervention actions (Auth: Optional if AUTH_DISABLED)
- `GET /intervention_actions/{id}` - Get specific intervention action by ID (Auth: Optional if AUTH_DISABLED)

### Action Categories

- `GET /action_categories` - List all action categories (Auth: Optional if AUTH_DISABLED)
- `GET /action_categories/{id}` - Get specific action category by ID (Auth: Optional if AUTH_DISABLED)
- `GET /action_categories/{id}/subcategories` - Get subcategories for a specific category (Auth: Optional if AUTH_DISABLED)

### Action Subcategories

- `GET /action_subcategories` - List all action subcategories (Auth: Optional if AUTH_DISABLED)
- `GET /action_subcategories/{id}` - Get specific action subcategory by ID (Auth: Optional if AUTH_DISABLED)

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

## Schemas

### InterventionOut

```json
{
  "id": "uuid",
  "code": "string",
  "title": "string",
  "equipements": {
    "id": "uuid",
    "code": "string|null",
    "name": "string",
    "no_machine": "int|null",
    "affectation": "string|null",
    "marque": "string|null",
    "model": "string|null",
    "no_serie": "string|null",
    "equipement_mere": "uuid|null",
    "is_mere": "boolean",
    "type_equipement": "string|null",
    "fabricant": "string|null",
    "numero_serie": "string|null",
    "date_mise_service": "date|null",
    "notes": "string|null"
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
  "actions": [
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
  ]
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

Note: `GET /interventions` retourne `actions: []` (vide), `GET /interventions/{id}` retourne les actions complètes.

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

## Configuration

- **AUTH_DISABLED**: Set to `true` in `.env` to skip JWT validation for testing
- **DATABASE_URL**: PostgreSQL connection string
- **DIRECTUS_URL**: Authentication service URL
