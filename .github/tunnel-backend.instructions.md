# Tunnel Backend Instructions

## Backend Code Standards (Project)

### File Structure

```
api/
├── app.py              # Main app
├── settings.py         # Config
├── auth/
│   ├── middleware.py   # JWT middleware
│   └── jwt_handler.py  # JWT decode
├── errors/
│   ├── exceptions.py   # Exceptions
│   └── handlers.py     # Exception handlers
└── [domain]/
    ├── routes.py       # HTTP endpoints
    ├── repo.py         # Database queries
    └── schemas.py      # Pydantic models
```

### Code Style

- Names: English, descriptive, simple (e.g., `check_auth()`, `get_intervention()`)
- Functions: Small, single responsibility, max ~20 lines
- Classes: Only Exceptions and Repositories

### DRY

If logic appears 2+ times, extract it. Applies to calculations, validation, data transforms, API calls, DB queries.

### API Manifest Maintenance

- Update `API_MANIFEST.md` after any route change.
- List every endpoint (method/path/description/auth).
- Document schemas with full JSON structure, mark optional fields with `|null`, match actual responses.

### Temporal Filters (Project)

- Périodes: `start_date` optionnelle (défaut = NULL → toute l’historique), `end_date` optionnelle (défaut = NOW()).
- Si `start_date` absente, ne pas appliquer de borne basse.
- Respecter ces règles dans code et manifest; aucune autre convention de dates.

## Architecture (Project)

- Data: PostgreSQL as source of truth
- Auth: External JWT provider proxied by API (keep wording agnostic)
- API: FastAPI proxy/router (no caching, no queues, no unnecessary complexity)

Request flow:

```
Client (JWT header)
  ↓
JWT Middleware
  → Public route? continue
  → Valid JWT? set request.state.user_id
  → Invalid? 401
  ↓
Route Handler
  → /interventions/* → PostgreSQL
  → Other proxied calls → external auth provider
  ↓
JSON Response
```

Not allowed: Redis caching, Celery queues, event sourcing, complex observability. Keep it PostgreSQL → FastAPI → Frontend.

## How To Respond (Project)

Before coding (if ambiguous):

- Clarify scope and whether to modify/create files.
- If creating >2 files, confirm.

After coding:

- List modified files and tests run (or not run if skipped).

## Checklist Before Presenting (Project)

- Code works? (tested now)
- Simplest solution?
- Created >2 files? (avoid unless necessary)
- No extra docs created unasked?
- Understandable in 30 seconds?
- Can it be simpler?

## Concrete Example (Project)

Wrong (overkill for health check): created many files/scripts.

Right: add `@app.get("/health")` in app.py, adjust middleware, test; minimal files touched.
