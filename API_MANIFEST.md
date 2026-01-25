# API Manifest

Last updated: 2026-01-24

## Endpoints

### Health

- `GET /health` - Check API health with database and Directus status (Public)

### Auth

- `POST /auth/login` - Login proxy, returns JWT payload and sets session cookie (Public)
  - Body (json): `{ "email": "string", "password": "string", "mode": "session" }`

### Interventions

- `GET /interventions` - List interventions with pagination (default 100, max 1000) and stats (Auth: Optional if AUTH_DISABLED)
  - Query params: `skip` (default 0), `limit` (default 100, max 1000)
- `GET /interventions/{id}` - Get intervention by ID with actions and stats (Auth: Optional if AUTH_DISABLED)
- `GET /interventions/{id}/actions` - Get actions for specific intervention (Auth: Optional if AUTH_DISABLED)

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

- `GET /equipements` - List all equipements (simple) (Auth: Optional if AUTH_DISABLED)
- `GET /equipements/list` - List all equipements with intervention statistics for park overview (Auth: Optional if AUTH_DISABLED)
- `GET /equipements/{id}` - Get specific equipement by ID (simple) (Auth: Optional if AUTH_DISABLED)
- `GET /equipements/{id}/detail` - Get equipement with decisional interventions and period statistics (Auth: Optional if AUTH_DISABLED)
  - Query params: `period_days` (default 30) - Period in days for decisional interventions and time spent
- `GET /equipements/{id}/sous_equipements` - Get sub-equipements for a specific equipement (Auth: Optional if AUTH_DISABLED)

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

### EquipementOut

```json
{
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
}
```

### EquipementListItem

```json
{
  "id": "uuid",
  "code": "string|null",
  "name": "string",
  "status": "ok|maintenance|warning|critical",
  "status_color": "green|blue|orange|red",
  "open_interventions_count": "int",
  "interventions_by_type": {
    "CUR": "int",
    "PRE": "int"
  },
  "parent": {
    "id": "uuid",
    "code": "string|null",
    "name": "string"
  },
  "equipement_mere": "uuid|null",
  "is_mere": "boolean"
}
```

Note: Equipements sorted by open interventions count (desc), then name (asc). Status calculated: urgent → critical, ≥3 open → warning, >0 open → maintenance, else ok.

### EquipementDetail

```json
{
  "id": "uuid",
  "code": "string|null",
  "name": "string",
  "status": "ok|maintenance|warning|critical",
  "status_color": "green|blue|orange|red",
  "parent": {
    "id": "uuid",
    "code": "string|null",
    "name": "string"
  },
  "interventions": [
    {
      "id": "uuid",
      "code": "string",
      "title": "string",
      "status": "open|in_progress|closed",
      "priority": "normal|urgent",
      "reported_date": "date",
      "type_inter": "CUR|PRE",
      "closed_date": "datetime|null"
    }
  ],
  "actions": [
    {
      "id": "uuid",
      "intervention_id": "uuid",
      "time_spent": "float|null",
      "created_at": "datetime|null"
    }
  ],
  "time_spent_period_hours": "float",
  "period_days": "int",
  "equipement_mere": "uuid|null",
  "is_mere": "boolean",
  "no_machine": "int|null",
  "affectation": "string|null",
  "marque": "string|null",
  "model": "string|null",
  "no_serie": "string|null",
  "type_equipement": "string|null",
  "fabricant": "string|null",
  "numero_serie": "string|null",
  "date_mise_service": "date|null",
  "notes": "string|null"
}
```

Note: Interventions = open + in_progress + closed within period_days. Sorted by urgency (urgent first), then status (open, in_progress, closed), then reported_date desc.

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
- **DIRECTUS_URL**: Directus instance URL for auth
