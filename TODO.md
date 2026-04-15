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

- [ ] **`_auto_accept_occurrence` contourne `transition_status`** *(preventive_occurrences/repo.py)* :
  La méthode crée l'intervention via `InterventionRepository.add()` directement, sans passer par `transition_status`. Résultat : la DI reste à `nouvelle` au lieu de passer à `acceptee`, aucun log `request_status_log` n'est créé.
  **Action** : remplacer l'appel direct par un appel à `InterventionRequestRepository().transition_status(di_id, "acceptee", ...)`.

- [ ] **`skip_occurrence` bloqué à `pending`** *(preventive_occurrences/repo.py)* :
  Seules les occurrences `pending` peuvent être ignorées. Une occurrence `in_progress` (DI acceptée, intervention en cours) ne peut plus être skippée.
  **Action** : élargir à `status IN ('pending', 'in_progress')` avec une règle métier à définir (faut-il aussi fermer l'intervention liée ?).

- [ ] **Double trigger redondant sur `intervention_status_log`** *(web.tunnel-db)* :
  L'ancien trigger `trg_sync_status_from_log` (qui synchronise uniquement `status_actual`) coexiste avec le nouveau `trg_sync_status_log_to_intervention` (qui fait la même chose + cascade occurrence). Double `UPDATE` inutile sur chaque INSERT de log.
  **Action** : supprimer `trg_sync_status_from_log` via migration  — ✅ migration `i4d5e6f7a8b9` ajoutée dans `web.tunnel-db`.

- [ ] **`python-jose` inutilisé** : Présent dans `requirements.txt` mais jamais importé. **Action** : supprimer.

- [ ] **`DIRECTUS_KEY` inutilisé** : Défini dans `settings.py` mais jamais utilisé. **Action** : supprimer ou documenter si futur.

- [ ] **Magic numbers** : Seuils éparpillés dans le code :
  - `supplier_orders/repo.py` : âges de commande (7j, 14j)
  - `constants.py` : capacité équipe (400h/mois)
  - `equipements/repo.py` : limites pagination (50 défaut, 500 max)
  - **Action** : externaliser en `api/config.py` ou `constants.py`

- [ ] **Decimal incohérent** : `supplier_orders/repo.py` convertit Decimal→float, `purchase_requests/repo.py` non.
  **Action** : uniformiser (probablement garder Decimal pour les montants)

- [ ] **Timezone incohérente** : Certains repos utilisent `datetime.now()` sans timezone. **Action** : standardiser sur UTC.

- [ ] **`get_active_status_ids()` jamais appelée** : Fonction dans `constants.py` (lignes ~99-103) non utilisée. **Action** : supprimer.

---

## 🟠 Mineurs

- [ ] **`_fetch_steps_batch` réutilise le curseur appelant** *(preventive_occurrences/repo.py)* :
  La méthode reçoit un `cur` ouvert et l'exécute directement. Si le curseur est dans un état intermédiaire, `fetchall()` peut retourner des données résiduelles.
  **Action** : créer un curseur dédié dans `_fetch_steps_batch` avec `conn.cursor()`.

- [ ] **`di_id` fantôme si commit échoue après INSERT DI** *(preventive_occurrences/repo.py, `_generate_for_machine`)* :
  Si le commit échoue après l'INSERT de la DI, `di_id` est une valeur locale qui ne correspond à rien en DB. L'appel à `_auto_accept_occurrence` avalera l'erreur silencieusement (`logger.warning`).
  **Action** : vérifier que le `di_id` est valide avant d'appeler `_auto_accept_occurrence`, ou déplacer l'auto-accept dans la même transaction.

- [ ] **Logging dupliqué** : Exceptions loggées à la fois dans `__init__` ET dans le handler global. **Action** : choisir un seul point de log.

- [ ] **Rate limit manquant** : Endpoint public `/equipements/{id}/qrcode` sans limite. **Action** : ajouter rate limit basic (ex. `10/minute`).

- [ ] **Architecture.md absent** : Créer un diagramme flux système dans `docs/`.

---

## 📋 Roadmap Futures Features

- [ ] **Export PDF enrichi** : Les exports devraient intégrer les blocs contextuels d'équipement (plans, occurrences, demandes)
- [ ] **Notifications en temps réel** : WebSocket pour les changements de statut d'intervention
- [ ] **Analytics avancés** : Métriques par catégorie, technician, équipement, SLA tracking
- [ ] **Intégration ERP** : Synchro bidirectionnelle avec le futur ERP LaraNDEavel/Symfony

---

## 🚀 Version 2.19.0+ (TBD)

- **Recommandé** : Écrire tests pour validators (InterventionActionValidator, etc.)
- **Recommandé** : Supprimer python-jose et DIRECTUS_KEY
- **Recommandé** : Unifier Decimal/float et timezone handling
