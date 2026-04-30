# BACKLOG — Corrections & Améliorations

Dernière mise à jour : 2026-04-30. Inclut l'audit complet du module préventif / occurrences / tâches / actions.

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

- [x] **[BUG] Changement de statut DI ne synchronise pas `status_actual` ni l'occurrence préventive**
  Trigger `trg_sync_status_log_to_intervention` ajouté via migration `20260414_h3c4d5e6f7a8`.
  _Fix : trigger AFTER INSERT ON intervention_status_log → update intervention.status_actual + preventive_occurrence.status + clôture DI._

- [x] **[BUG] `repair_orphaned_data` — étape 3 référençait l'ancienne table**
  Fichier : `api/preventive_occurrences/repo.py` (Bug 6)
  Le UPDATE dans l'étape 3 ciblait `gamme_step_validation` (table supprimée le 2026-04-25).
  Les `intervention_task` orphelines n'étaient jamais rattachées par cette branche de repair.
  _Fix : remplacer par `intervention_task`. Corrigé en session 2026-04-30._

- [x] **[BUG] Occurrence reste `in_progress` quand la DI est clôturée — critère borgne**
  Fichiers : `api/intervention_requests/repo.py`
  Deux chemins de fermeture utilisaient chacun un seul critère :
  — clôture directe DI : `WHERE di_id = %s` → rate si `di_id = NULL` sur l'occurrence
  — fermeture intervention : `WHERE intervention_id = %s` → rate si `intervention_id = NULL`
  _Fix : double critère `di_id OR intervention_id` dans les deux chemins. Corrigé 2026-04-30._

- [ ] **[BUG] `skip_reason` NULL provoque une erreur 500 au lieu de 400 lors d'un skip de tâche**
  Fichier : `api/intervention_actions/repo.py` lignes 559-571 (`add`) et 726-738 (`update`)
  Quand `task_req_data.get('skip') == True` et `skip_reason` est absent/null,
  la contrainte DB `CHECK (status != 'skipped' OR skip_reason IS NOT NULL)` rejette
  l'UPDATE → exception PostgreSQL remonte en 500.
  _Fix : valider Python en amont — lever `ValidationError(400)` si skip et skip_reason absent._

- [ ] **[BUG] `patch()` tâche avec `status='skipped'` sans `skip_reason` → 500**
  Fichier : `api/intervention_tasks/repo.py` lignes 346-354
  Aucune validation Python préalable sur la cohérence status/skip_reason.
  Même contrainte DB que ci-dessus → 500.
  _Fix : vérifier avant le UPDATE : si `data.status == 'skipped'` et `data.skip_reason` absent → `ValidationError`._

- [ ] **[QUALITÉ] Zéro tests dans le projet**
  Aucun fichier `test_*.py`. Les validators métier critiques (time_spent, status_from, transitions DI) ne sont pas couverts.
  _Fix : créer la structure `tests/` et commencer par `test_validators/`._

---

## 🟠 MAJEUR

- [x] **[NETTOYAGE] Supprimer `python-jose` des dépendances**
  Fichier : `requirements.txt`
  `python-jose` est listé mais jamais importé. `PyJWT` fait le travail.
  _Fix : retirer la ligne `python-jose` de `requirements.txt`._

- [x] **[NETTOYAGE] Supprimer `DIRECTUS_KEY` inutilisée**
  Fichier : `api/settings.py`
  Variable définie mais jamais utilisée dans la codebase.
  _Fix : supprimer ou documenter l'usage prévu._

- [x] **[NETTOYAGE] Supprimer `get_active_status_ids()` morte**
  Fichier : `api/constants.py` lignes ~99-103
  Fonction avec import lazy jamais appelée dans le projet.
  _Fix : supprimer la fonction._

- [x] **[BUG] `optional` désynchronisé entre `intervention_task` et `preventive_plan_gamme_step`**
  Fichier : `api/preventive_occurrences/repo.py` (Bug 5 ajouté 2026-04-30)
  Si un step de plan est modifié (obligatoire ↔ optionnel) après la génération des tâches,
  les `intervention_task origin='plan'` conservent l'ancienne valeur et bloquent à tort la fermeture.
  _Fix : resync `optional` depuis `preventive_plan_gamme_step` dans `repair_orphaned_data`. Corrigé 2026-04-30._

- [ ] **[BUG] `_notify_if_closed` avale toutes les exceptions silencieusement**
  Fichier : `api/interventions/repo.py` lignes 645-650
  ```python
  except Exception:
      pass  # silencieux
  ```
  Si `on_intervention_closed` échoue (DB, rollback), l'erreur est perdue.
  L'intervention est fermée, mais l'occurrence reste `in_progress` et la DI reste `acceptee`
  sans aucun log permettant de diagnostiquer.
  _Fix : remplacer `pass` par `logger.error(..., exc_info=True)` pour tracer le stacktrace complet._

- [ ] **[BUG] `on_intervention_closed` rate le cas DI déjà `cloturee`**
  Fichier : `api/intervention_requests/repo.py` lignes 743-763
  `closed_request_id` vaut `None` si la DI n'est plus en statut `acceptee`.
  La condition `OR (di_id = %s AND %s IS NOT NULL)` est alors désactivée.
  Si l'occurrence a en plus `intervention_id = NULL` (bug de liaison antérieur),
  elle ne sera jamais complétée par ce chemin.
  _Fix : SELECT séparée sans filtre sur le statut pour trouver l'ID de la DI liée à l'intervention,
  puis l'utiliser dans l'UPDATE `preventive_occurrence`._

- [ ] **[BUG] Schéma relation action ↔ tâche ambigu — double modèle en production**
  Migrations successives (i4d5→j5e6→k6f7→p1k2) ont inversé la relation 4 fois en 3 jours.
  État final incohérent :
  — `k6f7` supprime `action_id` sur `intervention_task`, ajoute `task_id` sur `intervention_action`
  — `p1k2` ré-ajoute `action_id` sur `intervention_task` sans supprimer `task_id` sur `intervention_action`
  Les deux colonnes coexistent. Le code Python écrit via `action_id` (sur la tâche).
  Les requêtes batch lisent via `COALESCE(it.action_id, ia_legacy.task_id)` — deux sources de vérité.
  _Fix : décider du modèle canonique, supprimer la colonne abandonnée, purger le COALESCE legacy._
  **Bloquant pour P2-B, P2-C, P2-D.**

- [ ] **[BUG] `_TASK_SELECT` — `action_count` et `time_spent` toujours 0 ou 1**
  Fichier : `api/intervention_tasks/repo.py` lignes 32-38
  La LATERAL join calcule `WHERE ia.id = it.action_id` — au plus un enregistrement.
  Le modèle réel est many-to-one (plusieurs tâches → une action).
  `action_count` ne reflète jamais le nombre réel d'actions ayant touché cette tâche.
  _Fix (selon modèle retenu) : compter via `WHERE ia.task_id = it.id` si task_id est le modèle retenu._

- [ ] **[BUG] `delete()` vérifie le mauvais champ de liaison action ↔ tâche**
  Fichier : `api/intervention_tasks/repo.py` lignes 392-428
  La garde lit `action_id` (colonne 3 du SELECT) sur la tâche pour bloquer la suppression.
  Si le modèle canonique est `task_id` sur `intervention_action`, une tâche peut avoir des actions
  liées sans que `action_id` ne soit renseigné → suppression autorisée à tort.
  _Fix : vérifier via `SELECT COUNT(*) FROM intervention_action WHERE task_id = %s`._

- [ ] **[BUG] Double vérification `_check_closable` Python + trigger DB `check_intervention_closable`**
  Fichiers : `api/interventions/repo.py` lignes 608-635 + migration `o0j1k2l3m4n5`
  Les deux font exactement la même requête `COUNT(*) WHERE optional = FALSE AND status IN ('todo','in_progress')`.
  Si le trigger DB est actif : deux connexions, deux requêtes, deux messages d'erreur possibles différents.
  Si le trigger est inactif (tests, maintenance) : Python prend le relais sans le savoir.
  _Fix : choisir une seule autorité. Option recommandée : supprimer `_check_closable()` Python
  et parser le message `GAMME_INCOMPLETE` du trigger pour retourner une `ValidationError` 400 propre._

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

- [ ] **[BUG] `is_complete` incohérent quand une occurrence n'a aucune tâche**
  Fichier : `api/intervention_tasks/repo.py` lignes 193 et 233
  `is_complete = blocking_pending == 0 and total > 0` retourne `False` si `total = 0`.
  Or `_check_closable` ne bloque pas si `blocking = 0` — la fermeture est autorisée.
  Le frontend voit `is_complete = False` alors que la fermeture est possible.
  _Fix : `is_complete = (blocking_pending == 0)` — retirer la condition `total > 0`,
  ou documenter explicitement que "pas de tâches = pas complet"._

- [ ] **[BUG] Resync `optional` (Bug 5 repair) écrase les overrides intentionnels**
  Fichier : `api/preventive_occurrences/repo.py`
  Le resync update toutes les tâches `origin='plan'` dont `optional` diffère du plan courant,
  sans distinguer un bug de liaison d'une surcharge intentionnelle par un responsable.
  _Fix : ajouter `optional_locked BOOLEAN DEFAULT FALSE` sur `intervention_task` (nouvelle migration),
  filtrer `AND optional_locked = FALSE` dans le resync. Écrire la migration alembic correspondante._

- [ ] **[BUG] Tâches `in_progress` dont l'action liée a été supprimée (statut fantôme)**
  Fichier : `api/preventive_occurrences/repo.py`
  Si une `intervention_action` est supprimée, les tâches liées via `action_id` conservent
  `status = 'in_progress'` avec un `action_id` qui pointe vers une ligne inexistante (ON DELETE SET NULL
  remet `action_id = NULL` mais pas le statut).
  _Fix : ajouter Bug 7 dans `repair_orphaned_data` — détecter les tâches `in_progress`
  avec `action_id IS NULL` (ou `task_id` sur action supprimée) et les remettre à `todo`._

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

- [ ] **[QUALITÉ] `repair_orphaned_data` non idempotent sur le Bug 5**
  Si le plan est modifié entre deux appels repair, chaque appel peut inverser le précédent.
  Aucun log indiquant l'ancienne valeur avant écrasement.
  _Fix : logguer l'ancienne valeur `it.optional` pour chaque ligne modifiée (RETURNING it.id, it.optional, pgs.optional)._

---

## 🔵 ROADMAP TESTS (détail)

Structure cible à créer :

```
tests/
├── conftest.py                                  # Fixtures, DB de test
├── test_validators/
│   ├── test_intervention_actions.py             # time_spent, complexity_score, complexity_factor
│   ├── test_intervention_status_log.py          # status_from, champs requis
│   ├── test_intervention_requests.py            # transitions autorisées, motif rejet
│   └── test_preventive_occurrences.py           # génération, skip, repair idempotence
├── test_routes/
│   ├── test_auth.py                             # login, token invalide, token expiré
│   ├── test_equipements.py                      # CRUD basique, pagination, facets
│   ├── test_interventions.py                    # GET list, GET by id, POST, PATCH, fermeture
│   ├── test_intervention_tasks.py               # patch statut, skip avec/sans reason, delete
│   ├── test_intervention_actions.py             # add avec tasks, skip task, close_task
│   └── test_preventive_occurrences.py           # generate, repair, cascade completed
└── test_utils/
    └── test_pagination.py                       # PaginatedResponse, calcul total
```

**Cas critiques à couvrir en priorité :**
- Skip tâche sans skip_reason → doit retourner 400 (pas 500)
- Fermeture intervention avec tâche non-optionnelle `todo` → doit être bloquée
- Fermeture intervention sans aucune tâche → doit être autorisée
- Clôture DI → occurrence doit passer à `completed`
- `repair` deux fois de suite → résultat identique (idempotence)

---

## SUIVI

| Statut | Critique | Majeur | Mineur | Total |
|--------|----------|--------|--------|-------|
| ✅ Corrigé | 5 | 3 | 0 | **8** |
| 🔲 À faire | 3 | 9 | 11 | **23** |
| **Total** | **8** | **12** | **11** | **31** |

---

## HISTORIQUE DES CORRECTIONS

| Date | ID | Description |
|------|----|-------------|
| 2026-04-12 | — | Audit initial, génération du backlog v1 |
| 2026-04-12 | C | Fix doublon `get_facets()` |
| 2026-04-12 | C | Fix docs API exposés en prod |
| 2026-04-14 | C | Trigger sync statut DI → occurrence préventive |
| 2026-04-30 | C | Fix `repair` Bug 6 — table `gamme_step_validation` → `intervention_task` |
| 2026-04-30 | C | Fix cascade fermeture — occurrence reste `in_progress` (double critère di_id/intervention_id) |
| 2026-04-30 | M | Fix `repair` Bug 5 — resync `optional` depuis `preventive_plan_gamme_step` |
