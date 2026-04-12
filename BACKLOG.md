# BACKLOG — Corrections & Améliorations

Généré suite à l'audit du 2026-04-12. Priorisé par impact.

---

## 🔴 CRITIQUE

- [x] **[BUG] Doublon `get_facets()`**
  Fichier : `api/equipements/routes.py` lignes ~44-45
  Deux appels identiques à `repo.get_facets(search=search)` → double requête DB inutile.
  _Fix : supprimer la ligne en double._

- [x] **[SÉCURITÉ] Docs API exposés en production**
  Fichier : `api/auth/middleware.py`
  `/docs`, `/openapi.json`, `/redoc` sont dans `PUBLIC_ROUTES` sans condition.
  Toute la spec API est accessible sans auth en prod.
  _Fix : conditionner ces routes sur `settings.API_ENV != "production"`._

- [ ] **[QUALITÉ] Zéro tests dans le projet**
  Aucun fichier `test_*.py`. Les validators métier critiques (time_spent, status_from, transitions DA) ne sont pas couverts.
  _Fix : créer la structure `tests/` et commencer par `test_validators/`._

---

## 🟠 MAJEUR

- [ ] **[NETTOYAGE] Supprimer `python-jose` des dépendances**
  Fichier : `requirements.txt`
  `python-jose` est listé mais jamais importé. `PyJWT` fait le travail.
  _Fix : retirer la ligne `python-jose` de `requirements.txt`._

- [ ] **[NETTOYAGE] Supprimer `DIRECTUS_KEY` inutilisée**
  Fichier : `api/settings.py`
  Variable définie mais jamais utilisée dans la codebase.
  _Fix : supprimer ou documenter l'usage prévu._

- [ ] **[NETTOYAGE] Supprimer `get_active_status_ids()` morte**
  Fichier : `api/constants.py` lignes ~99-103
  Fonction avec import lazy jamais appelée dans le projet.
  _Fix : supprimer la fonction._

- [ ] **[CONFIG] Externaliser les magic numbers**
  Fichiers : `api/supplier_orders/repo.py`, `api/constants.py`
  Valeurs hardcodées : seuil orange = 7 jours, seuil rouge = 14 jours, capacité équipe = 400h/mois, limites pagination.
  _Fix : déplacer dans `settings.py` avec des défauts sensibles et des env vars._

- [ ] **[BUG] Conversion Decimal → float incohérente**
  `api/supplier_orders/repo.py` convertit les Decimal en float.
  `api/purchase_requests/repo.py` ne le fait pas.
  _Fix : uniformiser — soit une fonction `_serialize_decimals()` partagée, soit config Pydantic._

- [ ] **[BUG] `datetime.now()` sans timezone**
  Plusieurs repos utilisent `datetime.now()` alors que la DB stocke des timestamps UTC.
  _Fix : remplacer par `datetime.now(timezone.utc)` partout._

- [ ] **[SÉCURITÉ] Rate limit absent sur les endpoints QR code**
  Les URLs `/qrcode` sont publiques via une exception path-based dans le middleware, sans aucun rate limit.
  _Fix : ajouter `@limiter.limit("30/minute")` ou équivalent._

---

## 🟡 MINEUR

- [ ] **[QUALITÉ] Logging dupliqué sur les exceptions**
  Les exceptions sont loggées dans leur `__init__` ET dans les handlers FastAPI.
  _Fix : choisir une seule approche — supprimer le log dans `__init__` ou dans les handlers._

- [ ] **[DOC] Créer `docs/ARCHITECTURE.md`**
  Aucun document ne décrit le flux global : Frontend → API → PostgreSQL/Directus.
  _Fix : créer un document avec diagramme de flux et explication du repository pattern._

- [ ] **[QUALITÉ] Commenter les imports lazys circulaires**
  Fichiers : `api/intervention_actions/repo.py:87`, `api/intervention_status_log/validators.py:24`
  Les imports dans le corps des fonctions ne sont pas expliqués.
  _Fix : ajouter un commentaire `# Import lazy — évite la circularité avec xxx.repo`._

- [ ] **[QUALITÉ] Standardiser `response_model` sur toutes les routes**
  Certaines routes utilisent `response_model=dict` au lieu d'un schema Pydantic typé.
  _Fix : créer les schemas manquants et remplacer `dict`._

- [ ] **[QUALITÉ] Uniformiser PATCH vs PUT**
  Certains modules utilisent PATCH (modification partielle), d'autres PUT (remplacement complet) sans cohérence sémantique.
  _Fix : auditer module par module et aligner selon la sémantique réelle._

- [ ] **[QUALITÉ] Booléens mal nommés**
  `printed_fiche` devrait être `is_printed`, `interventions` (sur equipement_statuts) devrait être `has_interventions`.
  _Fix : renommer dans schemas + repo + adapter les requêtes SQL si nécessaire._

- [ ] **[CONFIG] Log level non configurable**
  Le niveau de log est conditionné sur `API_ENV` mais pas exposé comme env var.
  _Fix : ajouter `LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")` dans `settings.py`._

---

## 🔵 ROADMAP TESTS (détail)

Structure cible à créer :

```
tests/
├── conftest.py                              # Fixtures, DB de test
├── test_validators/
│   ├── test_intervention_actions.py        # time_spent, complexity_score, complexity_factor
│   ├── test_intervention_status_log.py     # status_from, champs requis
│   └── test_intervention_requests.py       # transitions autorisées, motif rejet
├── test_routes/
│   ├── test_auth.py                        # login, token invalide, token expiré
│   ├── test_equipements.py                 # CRUD basique, pagination, facets
│   └── test_interventions.py              # GET list, GET by id, POST, PATCH
└── test_utils/
    └── test_pagination.py                  # PaginatedResponse, calcul total
```

**Ordre de priorité** : validators → auth → CRUD principal

---

## SUIVI

| Statut | Nombre |
|--------|--------|
| À faire (critique) | 1 |
| Corrigé (critique) | 2 |
| À faire (majeur) | 7 |
| À faire (mineur) | 7 |
| **Total** | **17** |
