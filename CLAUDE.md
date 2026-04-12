# CLAUDE.md — web.tunnel-backend

Instructions permanentes pour Claude Code sur ce projet.
Ce fichier a la priorité sur tout comportement par défaut.

---

## CONTEXTE DU PROJET

API GMAO (Gestion de Maintenance Assistée par Ordinateur) en FastAPI + PostgreSQL.
Auth via JWT Directus. Version courante : voir `api/settings.py` → `API_VERSION`.

**Stack** : Python 3.12, FastAPI, psycopg2, Pydantic v2, WeasyPrint, slowapi

---

## LANGUE

Tous les échanges, commentaires de code, docstrings et messages de commit sont en **français**.
Exception : noms de variables/fonctions en anglais (PEP8).

---

## ARCHITECTURE — PATTERNS OBLIGATOIRES

### Structure d'un module métier

Chaque domaine suit **exactement** cette structure :

```
api/<domaine>/
├── __init__.py      (vide)
├── routes.py        (FastAPI router — pas de logique métier)
├── schemas.py       (Pydantic models — pas de DB)
├── repo.py          (accès DB — pas de validation métier)
└── validators.py    (optionnel — règles métier uniquement)
```

**Règle** : Ne JAMAIS mettre de logique métier dans `routes.py`. Ne JAMAIS faire de requêtes SQL dans `routes.py`.

### Repository pattern

- Chaque repo est une **classe** `XxxRepository` avec docstring de classe
- Méthodes publiques : `get_all()`, `get_by_id()`, `create()`, `update()`, `get_facets()`
- Les connexions DB sont **toujours** via `get_connection()` / `release_connection()` avec `finally`
- Utiliser `RealDictCursor` ou `dict(zip(cols, row))` de façon **cohérente** dans tout le repo

### Validators

- Classe `XxxValidator` avec méthode principale `validate_and_prepare(data, context) -> dict`
- Lève `ValidationError` (pas `HTTPException`)
- Testable indépendamment de FastAPI

---

## CONVENTIONS DE CODE

### Nommage

| Élément | Convention | Exemple |
|---------|-----------|---------|
| Fichiers | snake_case | `stock_items.py` |
| Classes | PascalCase | `StockItemRepository` |
| Fonctions/méthodes | snake_case | `get_by_id()` |
| Variables | snake_case | `filter_params` |
| Constantes | UPPER_SNAKE | `PRIORITY_TYPES` |
| Booléens | préfixe `is_` | `is_active`, `is_locked` |

### Dualité machine/équipement

La table DB s'appelle `machine`, l'API expose le concept sous `equipement`.
- Alias DB dans les requêtes : `m` pour machine (`FROM machine m`)
- Schemas Pydantic : préfixe `Equipement`
- Ne pas mélanger les deux dans un même contexte sans commentaire explicatif

### Imports circulaires

Les imports lazys (dans le corps d'une fonction) sont **acceptables** pour éviter les imports circulaires, mais doivent être **commentés** :
```python
# Import lazy pour éviter la circularité avec interventions.repo
from api.interventions.repo import InterventionRepository
```

---

## GESTION DES ERREURS

### Hiérarchie d'exceptions (ne pas dévier)

```
api/errors/exceptions.py
├── NotFoundError        → 404
├── ValidationError      → 400
├── ConflictError        → 409
├── UnauthorizedError    → 401
├── ForbiddenError       → 403
├── DatabaseError        → 500
├── ExportError          → 500
└── RenderError          → 500
```

- **Toujours** utiliser `raise_db_error(e, contexte)` dans les blocs `except Exception` des repos
- Ne **jamais** attraper `HTTPException` dans les repos
- Ne **jamais** lever `HTTPException` directement dans un repo (utiliser les exceptions custom)

### Pattern DB obligatoire

```python
conn = None
try:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(...)
        result = cur.fetchone()
    conn.commit()
    return result
except Exception as e:
    if conn:
        conn.rollback()
    raise_db_error(e, "description de l'opération")
finally:
    if conn:
        release_connection(conn)
```

---

## SÉCURITÉ

### PUBLIC_ROUTES

Le fichier `api/auth/middleware.py` définit `PUBLIC_ROUTES`.

**Règle** : `/docs`, `/openapi.json`, `/redoc` ne doivent PAS être accessibles en production sans auth.
Avant d'ajouter une route publique, justifier dans un commentaire pourquoi.

### QR code

Les endpoints `/qrcode` sont publics via check `endswith("/qrcode")` dans le middleware.
Ne pas ajouter d'autres exceptions path-based sans les documenter dans `PUBLIC_ROUTES`.

### SQL

- Toujours utiliser des **paramètres préparés** (`%s`, jamais de f-string dans une requête SQL)
- Toujours appliquer `strip_html()` sur les champs texte libres venant de l'utilisateur

---

## SCHEMAS PYDANTIC

- `model_config = ConfigDict(from_attributes=True)` sur tous les schemas de réponse
- Utiliser `Optional[X]` pour les champs nullables
- Séparer `XxxCreate`, `XxxUpdate`, `XxxDetail`, `XxxListItem` si les structures diffèrent
- Les listes paginées héritent de `PaginatedResponse` (api/utils/pagination.py)

---

## ENDPOINTS

### Conventions REST

| Action | Méthode | Code retour |
|--------|---------|-------------|
| Lister | GET | 200 |
| Détail | GET /{id} | 200 / 404 |
| Créer | POST | 201 |
| Modifier (partiel) | PATCH | 200 |
| Modifier (complet) | PUT | 200 |

- Utiliser **PATCH** pour les modifications partielles, **PUT** pour les remplacements complets — ne pas mélanger
- Ne pas exposer DELETE sans décision explicite sur soft vs hard delete

### Rate limiting

Les endpoints coûteux (stats, exports) doivent avoir un rate limit via `slowapi`.
Format : `@limiter.limit("10/minute")` avec `request: Request` comme premier paramètre.

---

## PROBLÈMES CONNUS (à corriger)

### Critiques

- [ ] **Doublon facets** : `api/equipements/routes.py` appelle `repo.get_facets()` deux fois (ligne ~44-45). Supprimer le doublon.
- [ ] **Docs en production** : `PUBLIC_ROUTES` expose `/docs` et `/openapi.json` en prod. À conditionner sur `API_ENV`.
- [ ] **Zéro tests** : Aucun test dans le projet. Priorité haute pour les validators et les routes critiques.

### Majeurs

- [ ] **python-jose inutilisé** : Présent dans `requirements.txt` mais jamais importé. Supprimer.
- [ ] **DIRECTUS_KEY inutilisé** : Défini dans `settings.py` mais jamais utilisé. Supprimer ou documenter.
- [ ] **Magic numbers** : Seuils age commandes (7j/14j), capacité équipe (400h/mois), limites pagination → externaliser en config.
- [ ] **Decimal incohérent** : `supplier_orders/repo.py` convertit Decimal→float, `purchase_requests/repo.py` non. Uniformiser.
- [ ] **Timezone** : Certains repos utilisent `datetime.now()` sans timezone. Standardiser sur UTC.
- [ ] **constants.py** : `get_active_status_ids()` (ligne ~99-103) utilise un import lazy mais la fonction n'est jamais appelée. Supprimer.

### Mineurs

- [ ] **Logging dupliqué** : Exceptions loggées dans `__init__` ET dans le handler. Choisir une seule approche.
- [ ] **Rate limit QR endpoint** : Public et sans limite. Ajouter un rate limit basique.
- [ ] **Architecture.md absent** : Créer un diagramme de flux dans `docs/`.

---

## TESTS (roadmap)

Structure cible :
```
tests/
├── conftest.py                  # Fixtures DB test
├── test_validators/
│   ├── test_intervention_actions.py
│   ├── test_intervention_status_log.py
│   └── test_intervention_requests.py
├── test_routes/
│   ├── test_auth.py
│   ├── test_equipements.py
│   └── test_interventions.py
└── test_utils/
    └── test_pagination.py
```

Prioriser : validators métier > routes auth > routes CRUD principales

---

## CHECKLIST AVANT MERGE

Avant de proposer ou valider une modification :

1. [ ] La logique métier est dans `validators.py` ou `repo.py`, pas dans `routes.py`
2. [ ] Les connexions DB sont fermées dans un `finally`
3. [ ] Les erreurs DB passent par `raise_db_error()`
4. [ ] Les champs texte libres sont nettoyés avec `strip_html()`
5. [ ] Les nouvelles routes ont un `response_model` Pydantic explicite
6. [ ] Les nouveaux endpoints de création retournent `status_code=201`
7. [ ] Les imports circulaires lazys sont commentés
8. [ ] Aucun `print()` laissé dans le code (utiliser `logger`)
9. [ ] Les nouvelles variables de config ont un défaut sensible dans `settings.py`
10. [ ] Si endpoint coûteux → rate limit ajouté

---

## MODULES CLÉS — RÉFÉRENCE RAPIDE

| Fichier | Rôle |
|---------|------|
| `api/app.py` | App FastAPI, lifespan, middleware, routers |
| `api/settings.py` | Config env avec guards production |
| `api/db.py` | Pool psycopg2, get/release connection |
| `api/constants.py` | Types, priorités, statuts, config métier |
| `api/errors/exceptions.py` | Hiérarchie d'exceptions HTTP |
| `api/errors/handlers.py` | Exception handlers FastAPI |
| `api/auth/middleware.py` | JWTMiddleware + PUBLIC_ROUTES |
| `api/auth/permissions.py` | `require_authenticated` dependency |
| `api/utils/pagination.py` | `PaginatedResponse`, `Facets` |
| `api/utils/sanitizer.py` | `strip_html()` |
| `api/utils/validators.py` | `validate_date()` |
