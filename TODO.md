# TODO — Problèmes connus et améliorations futures

Voir aussi [CLAUDE.md](CLAUDE.md) pour les patterns et conventions du projet.

---

## 🔴 Critiques

- [ ] **Doublon `get_facets()` dans equipements** : `api/equipements/routes.py` appelle `repo.get_facets()` deux fois (lignes ~44-45). **Action** : supprimer le doublon.

- [ ] **Docs Swagger (OpenAPI) expose en production** : `PUBLIC_ROUTES` expose `/docs` et `/openapi.json` même en production. **Action** : conditionner sur `API_ENV`.

- [ ] **Zéro tests dans le projet** : Aucun test unitaire/d'intégration. **Priorité haute** pour validators et routes critiques. **Structure** :
  ```
  tests/
  ├── conftest.py
  ├── test_validators/
  │   ├── test_intervention_actions.py
  │   ├── test_intervention_status_log.py
  │   └── test_intervention_requests.py
  ├── test_routes/
  │   └── test_equipements.py
  └── test_utils/
      └── test_pagination.py
  ```

---

## 🟡 Majeurs

- [ ] **`python-jose` inutilisé** : Présent dans `requirements.txt` mais jamais importé. **Action** : supprimer.

- [ ] **`DIRECTUS_KEY` inutilisé** : Défini dans `settings.py` mais jamais utilisé. **Action** : supprimer ou documenter si futur.

- [ ] **Magic numbers** : Seuils éparpillés dans le code :
  - `supplier_orders/repo.py` : âges de commande (7j, 14j)
  - `constants.py` : capacité équipe (400h/mois)
  - `equipements/repo.py` : limites pagination (50 défaut, 500 max)
  - **Action** : externaliser en `api/config.py` ou `constants.py`

- [ ] **Decimal incohérent** : `supplier_orders/repo.py` convertit Decimal→float, `purchase_requests/repo.py` non.
  - **Action** : uniformiser (probablement garder Decimal pour les montants)

- [ ] **Timezone incohérente** : Certains repos utilisent `datetime.now()` sans timezone. **Action** : standardiser sur UTC.

- [ ] **`get_active_status_ids()` jamais appelée** : Fonction dans `constants.py` (lignes ~99-103) non utilisée. **Action** : supprimer.

---

## 🟠 Mineurs

- [ ] **Logging dupliqué** : Exceptions loggées à la fois dans `__init__` ET dans le handler global. **Action** : choisir un seul point de log.

- [ ] **Rate limit manquant** : Endpoint public `/equipements/{id}/qrcode` sans limite. **Action** : ajouter rate limit basic (ex. `10/minute`).

- [ ] **Architecture.md absent** : Créer un diagramme flux système dans `docs/`.

- [ ] **Gamme steps diagnostic** : Scripts de diagnostic créés (`diagnostic_gamme_steps.py`, etc.). À documenter/automatiser dans CI.

---

## 📋 Roadmap Futures Features

- [ ] **Export PDF enrichi** : Les exports devraient intégrer les blocs contextuels d'équipement (plans, occurrences, demandes)
- [ ] **Notifications en temps réel** : WebSocket pour les changements de statut d'intervention
- [ ] **Analytics avancés** : Métriques par catégorie, technician, équipement, SLA tracking
- [ ] **Intégration ERP** : Synchro bidirectionnelle avec le futur ERP LaraNDEavel/Symfony

---

## 🚀 Version 2.18.0 (mai 2026)

**Status** : Release complétée

- ✅ Enrichissement GET /equipements/{id} avec 3 blocs contextuels
- ✅ Scripts de diagnostic gamme_steps
- ⏳ Prochaine : Corriger doublon facets et zéro tests

---

## 🚀 Version 2.19.0+ (TBD)

- **Recommandé** : Écrire tests pour validators (InterventionActionValidator, etc.)
- **Recommandé** : Supprimer python-jose et DIRECTUS_KEY
- **Recommandé** : Unifier Decimal/float et timezone handling
