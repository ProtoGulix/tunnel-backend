# Journal des mises à jour de l'API

Toutes les modifications importantes de l'API sont documentées ici.

## [2.7.17] - 9 mars 2026

### Corrections

- **Export email — références fabricant et fournisseur toujours à N/A** : la requête d'export ne lisait que les champs `manufacturer` et `manufacturer_ref` directement sur la ligne de commande, qui sont remplis manuellement lors d'un devis et donc vides tant qu'aucun devis n'a été saisi. La requête joint maintenant `stock_item_supplier` (via `stock_item_id + supplier_id` de la commande) et `manufacturer_item` pour récupérer les références du catalogue
  - Priorité : valeur manuelle sur la ligne si présente, sinon référence catalogue
  - Format du corps email : `Article - Fabricant - Réf fabricant - Réf fournisseur - Prix - Qté unité`

## [2.7.16] - 9 mars 2026

### Nouveautés

- **`POST /supplier-orders/{id}/export/email` — lien `mailto:` généré** : la réponse inclut désormais `mailto_url`, un lien cliquable prêt à intégrer dans un `<a href>` côté frontend — ouvre directement le client mail de l’utilisateur avec le destinataire, le sujet et le corps pré-remplis
  - `subject` : `Demande de devis (Réf. {order_number})`
  - `body` : liste numérotée `N. Article - Fabricant - Réf. Fabricant - Prix - Quantité Unité`, avec `N/A` pour les champs absents, suivi du total articles/unités
  - `mailto_url` : `null` si le fournisseur n’a pas d’email renseigné

## [2.7.15] - 9 mars 2026

### Corrections

- **500 sur `POST /auth/login` — corps de requête mal formaté** : quand le frontend envoyait `Content-Type: application/x-www-form-urlencoded` au lieu de `application/json`, Pydantic déclenchait une erreur de validation avec le corps brut (`bytes`) dans le champ `input`. Le handler tentait de sérialiser ces bytes en JSON → crash serveur. Le champ `input` est désormais exclu de la réponse d'erreur (résout aussi une fuite potentielle des données brutes du client vers la réponse)

## [2.7.14] - 9 mars 2026

### Corrections

- **CORS en production** : correction du blocage navigateur sur les appels API cross-origin (ex: `/health` retournait `200` sans en-tête `Access-Control-Allow-Origin`)
  - Nouvelle variable `CORS_ORIGINS` (liste CSV) pour autoriser plusieurs origines frontend en production
  - Normalisation des origines (`sans / final`) pour éviter les faux mismatches entre frontend et backend
  - Suppression d'un doublon `API_ENV` dans la configuration d'environnement

## [2.7.13] - 9 mars 2026

### Améliorations

- **Refactoring — règles métier centralisées dans `SupplierOrderValidator`** (`api/supplier_orders/validators.py`)
  - `validate_received_preconditions()` : les deux règles bloquantes pour le passage en `RECEIVED` sont désormais dans le validator, plus dans le repo
    1. Aucune ligne `is_selected = true` → `400` avec message guidant vers la sélection ou l'annulation
    2. Au moins une consultation non résolue → `400` avec le nombre de lignes concernées
  - Le repo `update()` se réduit à deux appels clairs au validator — toute la logique métier est au même endroit

## [2.7.12] - 8 mars 2026

### Nouveautés

- **Consultations multi-fournisseurs — détection et validation** : quand un article est dispatché sans fournisseur préféré, les lignes créées dans plusieurs paniers sont maintenant identifiables et bloquantes
  - `is_consultation` (bool) sur `SupplierOrderLineListItem` et `SupplierOrderLineOut` : `true` si la ligne partage ses DA avec des lignes dans d'autres paniers fournisseurs (dispatch mode consultation) — calculé dynamiquement, aucune colonne ajoutée en base
  - `consultation_resolved` (bool) : `true` quand une ligne sœur (même DA, autre panier) a `is_selected = true` — `is_selected = null` par défaut, oblige la sélection manuelle
  - **Règles bloquantes** pour le passage en `RECEIVED` (`400`) :
    1. Aucune ligne `is_selected = true` → erreur explicite invitant à sélectionner ou annuler la commande
    2. Au moins une consultation non résolue → erreur avec le nombre de lignes concernées

- **Booleans calculés sur les lignes** (`SupplierOrderLineListItem` et `SupplierOrderLineOut`)
  - `is_fully_received` : `true` si `quantity_received >= quantity` — dynamique, tient compte des modifications de quantité en négociation
  - `is_consultation` et `consultation_resolved` : voir ci-dessus

- **`PATCH /supplier-order-lines/{id}`** : mise à jour partielle d'une ligne — seuls les champs fournis sont modifiés (`is_selected`, `quantity`, `unit_price`, `quantity_received`, etc.). Le `PUT` reste disponible pour un remplacement complet.

## [2.7.11] - 8 mars 2026

### Corrections

- **JWT "token not yet valid (iat)"** : ajout d'un `leeway` de 30 secondes dans `PyJWT` pour tolérer le décalage d'horloge entre le serveur Directus et FastAPI (`api/auth/jwt_handler.py`)

- **`GET /purchase-requests/detail/{id}` — 500 relation inexistante** : la jointure SQL utilisait `LEFT JOIN equipement e` au lieu de `LEFT JOIN machine e ON i.machine_id = e.id` (nom réel de la table PostgreSQL), cohérent avec toutes les autres méthodes du même repository

### Nouveautés

- **`GET /supplier-orders/statuses`** : référentiel enrichi des statuts de commande fournisseur — retourne les 6 statuts avec `code`, `label`, `color`, `description` métier et `is_locked` (indique si le panier est verrouillé aux nouvelles DA)
  - Labels métier revus : `OPEN` → "En mutualisation", `SENT` → "Devis envoyé", `ACK` → "En négociation", `RECEIVED` → "En cours de livraison", `CLOSED` → "Clôturé", `CANCELLED` → "Annulé"
  - Source : `api/constants.py` — `SUPPLIER_ORDER_STATUS_CONFIG`

- **`GET /supplier-orders/` — pagination et facets** : la liste des commandes fournisseur retourne désormais un objet structuré aligné sur le pattern `stock-items`
  - `pagination` : objet `{total, page, page_size, total_pages, offset, count}` via `create_pagination_meta`
  - `facets` : compteurs par statut calculés **sans** le filtre `status` actif (toujours complet)

- **`GET /supplier-orders/{id}/transitions`** : retourne les transitions de statut autorisées depuis le statut actuel, avec description métier de chaque action — permet à l'UI d'afficher uniquement les boutons pertinents sans logique hardcodée

- **Validation des transitions de statut** (`api/supplier_orders/validators.py`) : tout `PUT /supplier-orders/{id}` modifiant le `status` est validé contre le graphe de transitions autorisées. Retourne `400` avec message détaillé en cas de transition invalide ou de tentative de modification d'un état final
  - Graphe : `OPEN → SENT, CANCELLED` | `SENT → ACK, RECEIVED, OPEN, CANCELLED` | `ACK → RECEIVED, CANCELLED` | `RECEIVED → CLOSED` | `CLOSED` et `CANCELLED` = états finaux
  - `SENT → OPEN` : réouverture autorisée, toutes les lignes conservées
  - `SENT → RECEIVED` : commande directe sans négociation (ex : Würth, Fabory)
  - `CLOSED` : déclenché manuellement — état final absolu
  - `CANCELLED` : état final absolu — aucune réouverture

### Documentation

- **`docs/endpoints/supplier-orders.md`** : mise à jour complète — statuts enrichis, pagination, endpoint transitions, section règles métier avec graphe de transitions et exemples d'erreurs
- **`docs/endpoints/purchase-requests.md`** : documentation complète de `GET /purchase-requests/detail/{id}` avec exemple JSON complet

---

## [2.7.10] - 7 mars 2026

### Nouveautés

- **`GET /purchase-requests/statuses`** : référentiel des statuts dérivés — retourne les 9 statuts avec code, label et couleur hex, directement depuis `DERIVED_STATUS_CONFIG`

- **`GET /purchase-requests/status/{status}`** : endpoint dédié pour filtrer les demandes d'achat par statut dérivé
  - Statuts valides : `TO_QUALIFY`, `NO_SUPPLIER_REF`, `PENDING_DISPATCH`, `OPEN`, `QUOTED`, `ORDERED`, `PARTIAL`, `RECEIVED`, `REJECTED`
  - Validation du statut au niveau route → `400` si statut inconnu
  - Query params optionnels : `skip`, `limit`, `urgency`
  - Réponse identique à `GET /purchase-requests/list?status={status}`

### Documentation

- **`docs/endpoints/purchase-requests.md`** : ajout d'un tableau récapitulatif des 9 statuts dérivés avec conditions de déclenchement
- **`docs/endpoints/purchase-requests.md`** : documentation du nouvel endpoint `/status/{status}`

---

### Améliorations

- **`POST /stock-families`** : nouvel endpoint de création d'une famille de stock (code + label optionnel, réponse `201`)
- **Unicité des codes famille et sous-famille** : vérification explicite avant INSERT/UPDATE — retourne `400` avec message clair (`"La famille 'X' existe déjà"` / `"Sous-famille X/Y existe déjà"`) au lieu d'un `500` sur contrainte PostgreSQL
- **`stock_sub_families/repo.py`** : `ValidationError` importé en tête de fichier, `except` dans `create()` corrigé pour re-lever `ValidationError` sans la transformer en `DatabaseError`

---

## [2.7.8] - 7 mars 2026

### Améliorations

- **Erreurs DB sémantiques** : les violations de contraintes PostgreSQL remontent désormais avec le bon code HTTP et un message lisible, sans fuiter de détails techniques
  - Contrainte d'unicité (`23505`) → `409 Conflict` : `"Cette ressource existe déjà (création)"`
  - Contrainte de clé étrangère (`23503`) → `400 Bad Request` : `"Référence invalide : une ressource liée est introuvable"`
  - Autres erreurs DB → `500` avec message générique (inchangé)
  - Nouveau utilitaire centralisé `raise_db_error(e, context)` dans `api/errors/exceptions.py`
  - Nouvelle exception `ConflictError` (409) avec handler dédié dans `api/errors/handlers.py`

- **Nettoyage des routes** : suppression des blocs `try/except` qui wrappaient toutes les exceptions en `HTTPException(400/500, str(e))`, écrasant le status code réel — 13 fichiers de routes corrigés
  - Les exceptions métier (`NotFoundError`, `ValidationError`, `ConflictError`, `DatabaseError`) remontent désormais directement aux handlers FastAPI enregistrés
  - `ValueError` du validator `InterventionStatusLogValidator` converti en `ValidationError(400)` proprement

---

## [2.7.7] - 6 mars 2026

### Corrections

- **`PUT /stock-item-suppliers/{id}` — 422 validation** : le schéma `StockItemSupplierIn` imposait `stock_item_id` et `supplier_id` comme champs requis, alors que le frontend les omet correctement en PUT (ces champs sont immutables après création). Ajout du schéma dédié `StockItemSupplierUpdate` sans ces deux champs, utilisé exclusivement sur la route PUT

---

## [2.7.6] - 6 mars 2026

### Corrections

- **`PUT /stock-items/{id}` — faux 400 sur items template** : la vérification d'immutabilité bloquait la présence de `family_code`, `sub_family_code` etc. dans le body même si la valeur n'avait pas changé — un PUT envoie naturellement tous les champs. La comparaison s'effectue désormais sur la **valeur** : seul un changement réel de valeur déclenche l'erreur

---

## [2.7.5] - 6 mars 2026

### Corrections

- **`PATCH /stock-sub-families/{fc}/{sfc}` — 500** : psycopg2 ne sait pas adapter les objets `UUID` Python nativement — ajout de `register_uuid()` dans `api/db.py` à l'initialisation du pool, ce qui résout l'erreur `can't adapt type 'UUID'` pour toutes les requêtes de l'API

### Améliorations

- **`POST /stock-items` — support du format frontend** : le champ `characteristics` accepte désormais deux formats en entrée :
  - Format liste (existant) : `[{ "key": "DIAM", "value": 12 }, ...]`
  - Format objet plat (frontend) : `{ "DIAM": "12", "MAT": "ACIER", ... }` — converti automatiquement par un validator Pydantic

- **`GET /stock-items/{id}` — fusion avec `with-characteristics`** : l'endpoint détail retourne désormais directement les champs `template_id`, `template_version` et `characteristics` (tableau vide pour les items legacy). L'endpoint `GET /stock-items/{id}/with-characteristics` est supprimé

- **`CharacteristicValue` — ajout du champ `label`** : les caractéristiques retournées dans `GET /stock-items/{id}` incluent maintenant le libellé du champ template (`f.label` ajouté dans le `SELECT` sur `part_template_field`)

---

## [2.7.4] - 6 mars 2026

### Sécurité

- **Injection SQL dans `equipements/repo.py`** : 6 requêtes interpolaient directement l'UUID du statut "fermé" via f-string — remplacé par une sous-requête paramétrée `(SELECT id FROM intervention_status_ref WHERE code = %s LIMIT 1)`

- **XSS dans l'export PDF** : Jinja2 `autoescape` était désactivé dans `pdf_generator.py` — activé (`autoescape=True`)

- **Header injection `Content-Disposition`** : les noms de fichiers PDF et QR code sont désormais sanitisés via `re.sub(r'[^\w\-]', '_', ...)` avant d'être injectés dans les headers HTTP

- **Rate limiting sur les routes lourdes** :
  - `GET /stats/*` (4 routes) : limité à 10 requêtes/minute par IP
  - `GET /exports/{id}/pdf` : limité à 5 requêtes/minute par IP (génération WeasyPrint)

- **Fuite d'informations base de données** : `DatabaseError`, `ExportError` et `RenderError` exposaient le message technique PostgreSQL au client (`str(e)`) — le détail technique est désormais uniquement loggé côté serveur, le client reçoit un message générique

---

## [2.7.3] - 6 mars 2026

### Améliorations

- **Pool de connexions PostgreSQL** : migration de `pg8000` vers `psycopg2` avec `ThreadedConnectionPool`
  - Nouveau module `api/db.py` — pool centralisé (`init_pool`, `get_connection`, `release_connection`, `close_pool`)
  - Tous les repositories migrent de `settings.get_db_connection()` vers `get_connection()` / `release_connection()`
  - Pool configurable via variables d'environnement : `DB_POOL_MIN` (défaut : 2), `DB_POOL_MAX` (défaut : 10)
  - Timeout par requête : 30 secondes (`statement_timeout`)
  - Cycle de vie géré par `lifespan` FastAPI — le pool s'ouvre au démarrage et se ferme proprement à l'arrêt
  - Dépendance `pg8000==1.31.2` remplacée par `psycopg2-binary==2.9.11`

---

## [2.7.2] - 6 mars 2026

### Sécurité

- **Vérification de signature JWT** : les tokens Directus sont désormais validés avec `DIRECTUS_SECRET` (algorithme HS256 + vérification expiration)
  - Si `DIRECTUS_SECRET` n'est pas configuré, un warning est loggé et le token est décodé sans vérification (comportement legacy, dev uniquement)

- **Guards de démarrage** : l'API refuse de démarrer en production si :
  - `AUTH_DISABLED=true` — bloquerait l'authentification entière
  - `DIRECTUS_SECRET` absent — rendrait la vérification JWT impossible

- **Rate limiting sur `POST /auth/login`** : limité à 10 requêtes/minute par IP (protection brute-force)
  - Dépendance ajoutée : `slowapi==0.1.9`

- **Validation du payload login** : `POST /auth/login` accepte désormais uniquement un schéma typé `LoginPayload`
  - `email` : format email validé (`EmailStr`)
  - `password` : taille max 256 caractères
  - Les erreurs Directus (502) ne leakent plus l'URL interne du service
  - Dépendance ajoutée : `email-validator==2.3.0`

- **Headers de sécurité HTTP** : ajoutés sur toutes les réponses
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy: geolocation=(), camera=(), microphone=()`
  - `Strict-Transport-Security` (production uniquement)
  - Suppression de `expose_headers: ["*"]` dans la config CORS

- **Autorisation par authentification** : toutes les routes métier requièrent désormais un JWT valide via `Depends(require_authenticated)`
  - Nouveau module `api/auth/permissions.py` — extensible en V3 lors de la migration vers un système d'auth indépendant de Directus
  - Routes publiques inchangées : `/health`, `/server/ping`, `/docs`, `/auth/login`, `/qrcode`

---

## [2.7.1] - 6 mars 2026

### Améliorations

- **`GET /manufacturer-items`** : pagination standard et recherche unifiée
  - Réponse paginée : `{ items, pagination }` (même format que `stock-items`)
  - Nouveau paramètre `search` : filtre simultané sur `manufacturer_name` et `manufacturer_ref` (insensible à la casse)

---

## [2.7.0] - 6 mars 2026

### Nouveautés

- **Nouvel endpoint `manufacturer-items`** : CRUD complet pour les références fabricants
  - `GET /manufacturer-items` : liste (skip/limit)
  - `GET /manufacturer-items/{id}` : détail
  - `POST /manufacturer-items` : création
  - `PATCH /manufacturer-items/{id}` : mise à jour partielle
  - `DELETE /manufacturer-items/{id}` : suppression
  - Champs : `id`, `manufacturer_name`, `manufacturer_ref`

- **`PATCH /intervention-actions/{id}`** : mise à jour partielle d'une action d'intervention
  - Champs modifiables : `description`, `time_spent`, `action_subcategory`, `tech`, `complexity_score`, `complexity_factor`
  - Validation métier appliquée sur les valeurs finales (règle score > 5 → factor obligatoire)

- **`PATCH /stock-families/{code}`** : mise à jour d'une famille de stock
  - Champs modifiables : `code` (avec cascade sur `stock_sub_family.family_code`), `label`
  - La table `stock_family` est désormais exploitée correctement

### Améliorations

- **`GET /stock-families`** et **`GET /stock-families/{code}`** : le champ `label` est maintenant retourné depuis la table `stock_family`

- **`GET /stock-item-suppliers/*`** : toutes les réponses incluent désormais l'objet `manufacturer_item` embarqué (via JOIN sur `manufacturer_item`)
  - Plus besoin d'une requête supplémentaire pour connaître le fabricant d'une référence fournisseur

### Documentation

- [manufacturer-items.md](docs/endpoints/manufacturer-items.md) : créé
- [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md) : ajout objet `manufacturer_item` embarqué
- [stock-families.md](docs/endpoints/stock-families.md) : ajout `label`, section `PATCH`
- [intervention-actions.md](docs/endpoints/intervention-actions.md) : section `PATCH` ajoutée

---

## [2.5.0] - 27 février 2026

### Améliorations

- **GET /stock-families/{code}** : Réponse enrichie pour améliorer l'UX
  - Ajout de compteurs `with_template_count` et `without_template_count`
  - Permet de connaître rapidement la répartition des sous-familles selon la présence d'un template
  - Nouveau paramètre `search` (optionnel) pour filtrer les sous-familles par code ou libellé
  - Exemple : `/stock-families/OUT?search=roul` filtre sur "roul" dans code ou label
  - Recherche insensible à la casse (ILIKE)
  - Les compteurs reflètent les résultats après filtrage
  - Réduit la charge côté client : plus besoin de filtrer manuellement les sous-familles

### Documentation

- [stock-families.md](docs/endpoints/stock-families.md) : Documentation mise à jour avec exemples de filtrage et nouveaux compteurs

---

## [2.4.0] - 25 février 2026

### Améliorations

- **Schemas partagés** : Nouveau schema `EmbeddedInterventionItem`
  - Utilisé pour embarquer les interventions dans le détail d'un équipement
  - Permet une distinction claire avec `InterventionInfo` (utilisé dans purchases requests)

- **GET /equipements/{id}** : Type d'intervention enrichi
  - `type_inter` passe de string à objet structuré : `{code: "CUR", label: "Curatif"}`
  - Les interventions embarquées incluent code et libellé du type
  - Élimine le besoin d'une requête supplémentaire pour décoder les types
  - Exemples : CUR → Curatif, PRE → Préventif, REA → Réapprovisionnement

### Documentation

- [shared-schemas.md](docs/shared-schemas.md#embeddedinterventionitem) : Nouveau schema `EmbeddedInterventionItem` documenté
- [equipements.md](docs/endpoints/equipements.md) : Exemple d'intervention mis à jour avec structure enrichie

### Technical Details

- Modifié `equipements/schemas.py` : Ajout de `TypeInterventionRef` pour typer `type_inter`
- Modifié `equipements/repo.py` : Enrichissement des interventions via `INTERVENTION_TYPES_MAP`
- Tous les types d'intervention sont maintenant disponibles en code (CUR, PRE, REA, BAT, PRO, COF, PIL, MES)

---

## [2.3.0] - 24 février 2026

### Améliorations

- **GET /action-categories** : Données imbriquées améliorées
  - Retourne maintenant les sous-catégories imbriquées dans chaque catégorie
  - Réponse : `{ "id": ..., "name": ..., "subcategories": [...] }`
  - Simplifie le client (une seule requête pour la hiérarchie complète)

- **GET /action-subcategories** : Données imbriquées améliorées
  - Retourne maintenant la catégorie parent imbriquée dans chaque sous-catégorie
  - Réponse : `{ "id": ..., "name": ..., "category": {...} }`
  - Contexte complet sans appel supplémentaire

- **GET /server/ping** : Nouveau endpoint public
  - Route de health check minimaliste : retourne simplement `"pong"`
  - Public (ne nécessite pas d'authentification)
  - Utile pour vérifier rapidement que l'API répond (monitoring, load balancers)

### Documentation

- [action-categories.md](docs/endpoints/action-categories.md) : Documentation des réponses imbriquées mises à jour

---

## [2.2.1] - 20 février 2026

### Correctifs

- **POST /auth/login** : Correction de la réponse vide
  - Fix : Le JWT est maintenant retourné dans le body sous `data.access_token` en plus du cookie
  - Le cookie `session_token` est toujours configuré automatiquement
  - Améliore la compatibilité avec les clients non-navigateur (mobile, API)

---

## [2.2.0] - 20 février 2026

### ⚠️ BREAKING CHANGES

- **GET /stock-items** : Format de réponse modifié pour supporter la pagination
  - Avant : Retourne directement un tableau `[{...}, {...}]`
  - Maintenant : Retourne un objet `{ "items": [...], "pagination": {...} }`
  - Migration : Remplacer `response` par `response.items` côté client

### Améliorations

- **GET /stock-items** : Pagination standard implémentée
  - Métadonnées : `total`, `page`, `page_size`, `total_pages`, `offset`, `count`
  - Limite par défaut abaissée de 100 à 50 éléments par page
  - Nouveau schéma réutilisable `PaginatedResponse` pour d'autres endpoints

### Documentation

- [stock-items.md](docs/endpoints/stock-items.md) : Documentation de la pagination
- [shared-schemas.md](docs/shared-schemas.md) : Nouveau schéma `PaginatedResponse` réutilisable

---

## [2.1.0] - 18 février 2026

### Nouveautés

- **GET /stock-families** : Nouveau endpoint pour lister les familles de stock
  - Retourne la liste complète des familles avec leurs sous-familles
- **GET /stock-families/{family_code}** : Détail d'une famille avec templates complets
  - Retourne la famille avec toutes ses sous-familles
  - Inclut les templates complets (avec fields et enum_values) pour chaque sous-famille ayant un template

### Améliorations

- **POST /stock-items** : Format d'entrée simplifié pour les caractéristiques
  - Avant : `{ "key": "DIAM", "number_value": 25, "text_value": null, "enum_value": null }`
  - Maintenant : `{ "key": "DIAM", "value": 25 }`
  - Le service route automatiquement la `value` vers le type approprié selon le `field_type` du template
  - Validation : Type checking automatique (number, text, enum) avec messages d'erreur explicites

- **GET /stock-items/{id}/with-characteristics** : Amélioration du format de sortie
  - Tri logique des caractéristiques par ordre défini dans le template
  - Retour enrichi : Inclut `field_id` pour chaque caractéristique
  - Format : `{ "field_id": "uuid", "key": "DIAM", "value_text": null, "value_number": 25, "value_enum": null }`

### Corrections

- **GET /part-templates** : Le `field_id` est maintenant retourné dans les templates
  - Permet au client de référencer précisément les champs lors de la création d'articles

### Documentation

- [stock-families.md](docs/endpoints/stock-families.md) : Documentation du nouveau endpoint stock-families
- [stock-items.md](docs/endpoints/stock-items.md) : Détails complets sur les modes legacy/template
- Clarification du format d'entrée des caractéristiques avec exemples concrets
- Tableau récapitulatif du routing automatique des valeurs selon `field_type`

---

## [2.0.0] - 18 février 2026

### ⚠️ BREAKING CHANGES

- **Convention kebab-case sur toutes les URLs** : Tous les endpoints de l'API utilisent désormais le kebab-case (`-`) au lieu du snake*case (`*`) dans les URLs, conformément aux bonnes pratiques REST (Google API Design Guide, Microsoft REST API Guidelines)

#### Mapping complet des changements d'URLs

| Avant (v1.x)               | Après (v2.0.0)             |
| -------------------------- | -------------------------- |
| `/intervention_actions`    | `/intervention-actions`    |
| `/intervention_status`     | `/intervention-status`     |
| `/intervention_status_log` | `/intervention-status-log` |
| `/action_categories`       | `/action-categories`       |
| `/action_subcategories`    | `/action-subcategories`    |
| `/complexity_factors`      | `/complexity-factors`      |
| `/equipement_class`        | `/equipement-class`        |
| `/purchase_requests`       | `/purchase-requests`       |
| `/stock_items`             | `/stock-items`             |
| `/supplier_orders`         | `/supplier-orders`         |
| `/supplier_order_lines`    | `/supplier-order-lines`    |
| `/stock_item_suppliers`    | `/stock-item-suppliers`    |

#### Sous-routes également migrées

| Avant                                          | Après                                          |
| ---------------------------------------------- | ---------------------------------------------- |
| `/stock_item_suppliers/stock_item/{id}`        | `/stock-item-suppliers/stock-item/{id}`        |
| `/stock_item_suppliers/{id}/set_preferred`     | `/stock-item-suppliers/{id}/set-preferred`     |
| `/supplier_order_lines/{id}/purchase_requests` | `/supplier-order-lines/{id}/purchase-requests` |

#### Endpoints inchangés (déjà conformes)

`/interventions`, `/equipements`, `/suppliers`, `/users`, `/auth`, `/health`, `/stats`, `/exports`, `/stock-sub-families`, `/part-templates`

### Migration

- Toutes les applications clientes doivent mettre à jour leurs URLs d'appels API
- Les tags OpenAPI/Swagger sont également en kebab-case
- Les noms de modules Python restent en snake_case (convention Python)
- Les noms de tables SQL restent en snake_case (convention DB)
- Documentation mise à jour : [API_MANIFEST.md](API_MANIFEST.md) et tous les fichiers `docs/endpoints/*.md`

---

## [1.11.1] - 17 février 2026

### Améliorations

- **GET /part-templates** : Retourne maintenant les templates complets avec fields
  - Avant : Retournait seulement `id`, `code`, `version`, `pattern`
  - Maintenant : Retourne `id`, `code`, `version`, `label`, `pattern`, `is_active` + array `fields[]` complet
  - Optimisation : Plus besoin d'appeler `GET /part-templates/{id}` pour chaque template
  - Utilité : Page de gestion des templates (listing, édition, suppression) en 1 seul appel
  - Chaque field inclut : `key`, `label`, `field_type`, `unit`, `required`, `sort_order`, `enum_values`

### Technique

- `PartTemplateRepository.get_all()` : Refactor pour charger fields + enum_values via JOINs
- Documentation mise à jour : [docs/endpoints/part-templates.md](docs/endpoints/part-templates.md)

---

## [1.11.0] - 15 février 2026

### Nouveautés

- **Système de templates versionnés pour pièces (v1.4.0)** : Support complet du système de caractérisation des pièces de la base de données v1.4.0
  - Nouveaux endpoints `/part-templates` pour gérer les templates de pièces
  - Création de templates avec champs typés (number, text, enum)
  - Versionnement automatique des templates (incrémentation version)
  - Protection : refuse suppression si des pièces utilisent le template

- **Gestion des stock_items avec templates** :
  - Mode **legacy** : Si `template_id IS NULL`, comportement identique à avant v1.4 (saisie libre dimension)
  - Mode **template** : Si sous-famille a template, validation stricte + génération automatique dimension
  - `POST /stock_items` : Détection automatique legacy vs template selon sous-famille
  - `GET /stock_items/{id}/with-characteristics` : Récupération item avec caractéristiques
  - Immutabilité : `template_id` et `template_version` non modifiables après création

- **Hydratation templates dans sous-familles** :
  - `GET /stock-sub-families` : Liste avec templates associés (fields + enum_values)
  - `GET /stock-sub-families/{family_code}/{sub_family_code}` : Détail avec template
  - Retour `"template": null` si sous-famille sans template

### Services & Architecture

- **TemplateService** : Service centralisé pour templates
  - `load_template()` : Charge template avec fields et enum_values
  - `validate_characteristics()` : Validation complète des caractéristiques
  - `generate_dimension()` : Génération automatique via pattern (ex: `{DIAM}x{LONG}-{MAT}`)
  - `load_template_for_sub_family()` : Récupère template par codes famille/sous-famille

- **StockItemService** : Service métier pour stock_items
  - `create_stock_item()` : Création intelligente legacy ou template
  - `update_stock_item()` : Mise à jour avec respect de l'immutabilité
  - `get_item_with_characteristics()` : Récupération enrichie
  - `is_legacy_item()` : Fonction utilitaire de détection

- **PartTemplateRepository** : Gestion CRUD templates
  - Transactions complètes (template + fields + enum_values)
  - Gestion du versionnement
  - Vérification d'utilisation avant suppression

### Règles métier implémentées

- ✅ Validation : Exactement un champ rempli selon `field_type`
- ✅ Enum obligatoire si type enum avec valeurs contrôlées
- ✅ Tous les champs `required` présents
- ✅ Aucun champ hors template accepté
- ✅ Interdiction saisie manuelle dimension pour items template
- ✅ Pattern doit contenir au moins un placeholder `{KEY}`

### Rétrocompatibilité

- ✅ Pièces existantes : Continuent de fonctionner (considérées legacy avec `template_id = NULL`)
- ✅ Aucune migration de données requise
- ✅ Sous-familles sans template : Continuent en mode legacy
- ✅ API backward-compatible : Pas de breaking changes

### Tables supportées (DB v1.4.0)

- `part_template` : Templates versionnés
- `part_template_field` : Champs des templates
- `part_template_field_enum` : Valeurs enum
- `stock_item_characteristic` : Caractéristiques des pièces
- `stock_sub_family.template_id` : Lien template par défaut
- `stock_item.template_id` + `template_version` : Traçabilité version

---

## [1.10.0] - 15 février 2026

### Nouveautés

- **Endpoint Utilisateurs** : Proxy lecture seule vers `directus_users` — expose les données publiques sans champs sensibles
  - `GET /users` — Liste avec filtres (`status`, `search`) et pagination (`skip`, `limit`)
  - `GET /users/me` — Utilisateur courant identifié par JWT (`request.state.user_id`)
  - `GET /users/{id}` — Détail par UUID
  - Champs exposés : id, first_name, last_name, email, location, title, description, tags, avatar, status, role, initial, last_access
  - Champs sensibles exclus : password, token, tfa_secret, auth_data

### Documentation

- **Restructuration complète de la documentation API**
  - `API_MANIFEST.md` refondu en index avec liens vers les pages individuelles
  - 16 fichiers de documentation par endpoint dans `docs/endpoints/`
  - `docs/shared-schemas.md` pour les schémas JSON réutilisés
  - Formats JSON d'entrée/sortie, règles métier et exemples pour chaque endpoint
  - Liens croisés entre endpoints liés pour éviter la duplication
- **Documentation des schémas utilisateur** : Section explicite des schémas `UserListItem` et `UserOut` dans [users.md](docs/endpoints/users.md)

### Refactoring

- **Suppression du schéma dupliqué `TechUserInfo`** : Remplacé par `UserListItem` de [api/users/schemas.py](api/users/schemas.py)
  - Principe DRY : Un seul schéma réutilisable au lieu de deux copies identiques
  - `InterventionActionOut.tech` utilise maintenant `UserListItem`
  - Les champs restent identiques : aucun impact sur l'API

### Correctifs

- **Cache Jinja2 désactivé** : Templates rechargés à chaque génération PDF pour faciliter le développement
  - `auto_reload=True` : Rechargement automatique des templates modifiés
  - `cache_size=0` : Pas de cache en mémoire
- **Logo PDF** : `config/templates/logo.png` ajouté au `.gitignore` (fichier local, pas versionné)
- **Pied de page PDF** : Bordures supérieures supprimées pour un rendu plus épuré

---

## [1.9.0] - 15 février 2026

### Nouveautés

- **Demandes d'achat dans les exports PDF** : Les fiches d'intervention incluent maintenant la liste des demandes d'achat liées
  - 8 colonnes : Quantité, Réf. Interne, Désignation, Fournisseur, Réf. Fournisseur, Fabricant, Réf. Fabricant, Urgence
  - Données enrichies via JOINs SQL : `stock_item`, `stock_item_supplier`, `supplier`, `manufacturer_item`
  - Indicateur visuel d'urgence (⚠ fond rouge)

- **Pied de page PDF complet** : Informations de traçabilité sur chaque page du document
  - Code intervention et numérotation des pages (`Page X / Y`) en bleu, gras, monospace
  - Version API et version template (gauche)
  - Date de génération (droite)
  - Utilisation de CSS Paged Media (`string-set`, `counter(page)`, `counter(pages)`)

- **Version de template configurable** : Nouveau champ de configuration pour gérer le versioning des templates
  - `EXPORT_TEMPLATE_VERSION` : Version du template d'export (défaut: `v8.0`)
  - `EXPORT_TEMPLATE_DATE` : Date de version du template (défaut: `2025-10-03`)

### Changements

- **Déplacement des templates d'export** : Les templates sont déplacés de `api/exports/templates/` vers `config/templates/`
  - Template renommé : `fiche_intervention_v1.html` → `fiche_intervention_v8.html`
  - Logo déplacé : `api/exports/templates/logo.png` → `config/templates/logo.png`
  - Mise à jour des chemins par défaut dans la configuration

- **Logo en base64** : Le logo est converti en data URI base64 pour compatibilité WeasyPrint
  - Résout le problème d'affichage du logo dans les PDF générés

### Corrections

- **Colonne `quantity`** : Correction du nom de colonne (`quantity` au lieu de `quantity_requested`)
- **Colonne `requester_name`** : Utilisation du champ texte direct au lieu d'une jointure sur `directus_users`
- **Table `manufacturer`** : Correction de la jointure - les données fabricant sont dans `manufacturer_item.manufacturer_name` (pas de table `manufacturer` séparée)

### Configuration

Nouvelles variables d'environnement (optionnelles) :

- `EXPORT_TEMPLATE_VERSION` : Version du template (défaut: `v8.0`)
- `EXPORT_TEMPLATE_DATE` : Date de version du template (défaut: `2025-10-03`)

Variables modifiées :

- `EXPORT_TEMPLATE_DIR` : Défaut changé de `api/exports/templates` → `config/templates`
- `EXPORT_TEMPLATE_FILE` : Défaut changé de `fiche_intervention_v1.html` → `fiche_intervention_v8.html`
- `EXPORT_QR_LOGO_PATH` : Défaut changé de `api/exports/templates/logo.png` → `config/templates/logo.png`

---

## [1.8.0] - 12 février 2026

### Nouveautés

- **Export PDF des interventions** : Génération de rapports PDF professionnels pour impression
  - `GET /exports/interventions/{id}/pdf` - Export PDF avec authentification requise
  - Template HTML Jinja2 optimisé pour impression A4
  - Rendu PDF via WeasyPrint pour qualité professionnelle
  - Données complètes : intervention, équipement, actions, logs de statut, statistiques
  - Nom de fichier automatique basé sur le code intervention (ex: "INT-2026-001.pdf")
  - Support ETag pour mise en cache côté client

- **QR Codes pour interventions** : Génération de QR codes pour accès mobile rapide
  - `GET /exports/interventions/{id}/qrcode` - Génération QR code sans authentification (public)
  - QR code pointe vers la page détail intervention dans le frontend
  - Support overlay logo pour branding d'entreprise (optionnel)
  - Format PNG optimisé pour impression sur rapports physiques
  - Correction d'erreur élevée (ERROR_CORRECT_H) pour fiabilité du scan
  - Cache public 1 heure pour meilleures performances

- **Module exports dédié** : Architecture modulaire pour réutilisabilité
  - `api/exports/` : Nouveau module standalone suivant le pattern repository
  - `PDFGenerator` : Classe dédiée pour rendu HTML → PDF avec filtres Jinja2
  - `QRGenerator` : Classe dédiée pour génération QR codes avec logo overlay
  - `ExportRepository` : Repository spécialisé pour requêtes d'export optimisées
  - Templates Jinja2 personnalisables dans `api/exports/templates/`

### Configuration

Nouvelles variables d'environnement (optionnelles) :

- `EXPORT_TEMPLATE_DIR` : Dossier des templates HTML (défaut: `api/exports/templates`)
- `EXPORT_TEMPLATE_FILE` : Fichier template HTML (défaut: `fiche_intervention_v1.html`)
- `EXPORT_QR_BASE_URL` : URL frontend pour QR codes (défaut: `http://localhost:5173/interventions`)
- `EXPORT_QR_LOGO_PATH` : Chemin logo overlay QR (défaut: `api/exports/templates/logo.png`)

### Dépendances

Nouvelles dépendances ajoutées :

- `Jinja2==3.1.6` : Moteur de templates HTML
- `weasyprint==66.0.0` : Génération PDF depuis HTML/CSS
- `qrcode==8.2` : Génération de QR codes
- `Pillow==12.0.0` : Manipulation d'images (overlay logo sur QR)

### Sécurité

- **PDF exports** : Authentification JWT requise (données sensibles : noms techniciens, temps, notes)
- **QR codes** : Public (conçu pour impression sur rapports physiques, QR pointe vers frontend qui nécessite login)

---

## [1.7.0] - 11 février 2026

### Nouveautés

- **Qualité des données** : Nouvel endpoint de détection des problèmes de complétude et cohérence
  - `GET /stats/qualite-donnees` - Identifie les données manquantes ou incohérentes avec les règles métier
  - 13 règles de détection sur 4 entités :
    - **intervention_action** (7 règles) : temps non saisi, complexité sans facteur, sous-catégorie manquante, technicien manquant, description vide, temps suspect (> 8h), action créée après fermeture de l'intervention
    - **intervention** (3 règles) : fermée sans action, sans type, en cours inactive (> 14 jours)
    - **stock_item** (2 règles) : sans seuil minimum, sans fournisseur référencé
    - **purchase_request** (1 règle) : sans article de stock lié
  - Chaque problème remonte avec sévérité (`high` / `medium`), message en français et contexte de navigation
  - Filtrage par `severite`, `entite` ou `code` anomalie via query params
  - Requêtes SQL indépendantes par règle (pas de mega-jointure)

### Changements

- **Passage en beta** : Les endpoints suivants sont considérés beta car ils ne respectent pas encore la philosophie de l'API (requêtes SQL directes indépendantes, pas de chargement mémoire, format de réponse normalisé)
  - `GET /stats/anomalies-saisie` — Détection des anomalies de saisie (beta)
  - `GET /stats/charge-technique` — Analyse de la charge technique (beta)

---

## [1.6.1] - 9 février 2026

### Corrections

- **Exclusion du préventif des anomalies** : Les actions de catégorie PREV sont exclues des détections où elles créaient des faux positifs
  - Type A (répétitives) : les actions préventives récurrentes (nettoyage filtres, etc.) ne remontent plus
  - Type B (fragmentées) : les actions préventives courtes (0.25h, 0.5h) ne remontent plus
  - Type E (back-to-back) : les actions préventives quotidiennes consécutives ne remontent plus

---

## [1.6.0] - 9 février 2026

### Nouveautés

- **Détection des anomalies de saisie** : Nouvel endpoint d'analyse qualité des actions d'intervention
  - `GET /stats/anomalies-saisie` - Analyse la qualité des saisies et détecte 6 types d'anomalies
  - **Actions répétitives** (too_repetitive) : Même sous-catégorie + même machine > 3 fois/mois
  - **Actions fragmentées** (too_fragmented) : Actions courtes (< 1h) apparaissant 5+ fois sur une même sous-catégorie
  - **Actions trop longues** (too_long_for_category) : Actions > 4h sur des catégories normalement rapides (BAT_NET, BAT_RAN, BAT_DIV, LOG_MAG, LOG_REC, LOG_INV)
  - **Mauvaise classification** (bad_classification) : Actions BAT_NET contenant des mots-clés techniques suspects (mécanique, hydraulique, roulement, vérin, etc.)
  - **Retours back-to-back** (back_to_back) : Même technicien + même intervention, deux actions consécutives espacées de moins de 24h
  - **Faible valeur / charge élevée** (low_value_high_load) : Catégories à faible valeur ajoutée avec temps cumulé > 30h
  - Chaque anomalie a une sévérité `high` ou `medium` selon des seuils configurables
  - Messages pré-formatés en français pour affichage direct dans les tableaux
  - Bloc `config` dans la réponse avec les seuils et listes appliqués pour transparence côté frontend

---

## [1.5.2] - 9 février 2026

### Corrections

- **CORS** : Correction des erreurs CORS Missing Allow Origin
  - Ajout de `CORS_ORIGINS` property avec support multi-origines en développement (localhost:5173, localhost:3000, 127.0.0.1:5173, 127.0.0.1:3000)
  - Ajout de `expose_headers=["*"]` dans CORSMiddleware
  - Middleware JWT : bypass des requêtes OPTIONS (CORS preflight) avant vérification d'authentification

### Nouveautés

- **Docker** : Ajout de configuration Docker et docker-compose
  - `Dockerfile` : Image Python 3.12 avec hot-reload pour développement
  - `docker-compose.yml` : Configuration minimaliste pour l'API seule
  - `.dockerignore` : Exclusions optimisées du build
  - Mise à jour du README avec instructions de démarrage Docker

---

## [1.5.1] - 8 février 2026

### Améliorations

- **Guide de lecture charge technique** : Alignement des textes avec les règles métier (REGLES_METIER.md)
  - Seuils du taux évitable : labels et actions corrigés pour correspondre au document de référence
  - Actions par catégorie de complexité : recalées sur le mapping réel des facteurs (PCE→Logistique, ACC→Technique, DOC→Information, OUT→Ressources, ENV→Environnement)

---

## [1.5.0] - 8 février 2026

### Nouveautés

- **Charge technique (pilotage maintenance)** : Nouvel endpoint d'analyse stratégique
  - `GET /stats/charge-technique` - Analyse où passe le temps du service maintenance et quelle part est récupérable
  - Découpage multi-période : `period_type` = `month`, `week`, `quarter` ou `custom`
  - Calcul automatique des charges : totale, dépannage, constructive (FAB+SUP+PREV+BAT)
  - Distinction **dépannage évitable** vs **dépannage subi** :
    - Évitable si `complexity_factor` renseigné (tout facteur est un signal)
    - Évitable si même `action_subcategory` répétée ≥3 fois sur la même classe d'équipement
  - **Taux de dépannage évitable** avec indicateur couleur :
    - Vert (<20%) : Faible levier
    - Orange (20-40%) : Levier de standardisation
    - Rouge (>40%) : Problème systémique
  - Ventilation par facteur de complexité (PCE, ACC, DOC, OUT, ENV, AUT...)
  - Ventilation par classe d'équipement avec taux individuel
  - Analyse toujours par classe d'équipement, jamais par machine isolée ni par technicien
  - **Guide de lecture** intégré dans la réponse (`guide`) : l'API fournit l'objectif, les seuils d'interprétation du taux évitable, et les actions recommandées par catégorie de complexité

---

## [1.4.0] - 8 février 2026

### ⚠️ BREAKING CHANGES

- **Renommage du champ de facteur de complexité** : Le champ `complexity_anotation` devient `complexity_factor`
  - Impact sur les endpoints :
    - `POST /intervention_actions/` - Entrée : utiliser `complexity_factor` au lieu de `complexity_anotation`
    - `GET /interventions/{id}/actions` - Sortie : le champ `complexity_factor` remplace `complexity_anotation`
    - `GET /intervention_actions/{id}` - Sortie : le champ `complexity_factor` remplace `complexity_anotation`
  - Le type de sortie change de `object|null` à `string|null` (c'est maintenant une FK directe vers la table complexity_factor)
  - Migration : les applications clientes doivent mettre à jour leurs appels API

---

## [1.3.1] - 7 février 2026

### Nouveautés

- **CRUD des equipements** : Creation, modification et suppression des equipements
  - `POST /equipements/` - Cree un equipement (ex: ajouter une nouvelle machine dans l'atelier)
  - `PUT /equipements/{id}` - Met a jour un equipement (ex: reassigner a une autre classe)
  - `DELETE /equipements/{id}` - Supprime un equipement

---

## [1.3.0] - 7 février 2026

### ⚠️ BREAKING CHANGES

- **Nouveau module de classes d'équipement** : Ajout d'un système de classification des équipements
  - Les réponses des endpoints `/equipements` incluent maintenant `equipment_class` (objet ou null)
  - Structure du champ ajouté :
    ```json
    {
      "equipment_class": {
        "id": "uuid",
        "code": "SCIE",
        "label": "Scie"
      }
    }
    ```
  - Impact sur les endpoints :
    - `GET /equipements/` - Liste avec champ `equipment_class`
    - `GET /equipements/{id}` - Détail avec champ `equipment_class`
  - Migration : Le champ `equipment_class` sera `null` pour tous les équipements existants jusqu'à assignation

### Nouveautés

- **Module CRUD complet pour les classes d'équipement** : Nouveau module `/equipement_class`
  - `GET /equipement_class/` - Liste toutes les classes d'équipement
  - `GET /equipement_class/{id}` - Récupère une classe par ID
  - `POST /equipement_class/` - Crée une nouvelle classe
    ```json
    {
      "code": "SCIE",
      "label": "Scie",
      "description": "Machines de sciage"
    }
    ```
  - `PATCH /equipement_class/{id}` - Met à jour une classe existante
  - `DELETE /equipement_class/{id}` - Supprime une classe (bloqué si des équipements l'utilisent)

- **Classification hiérarchique des équipements** :
  - Chaque équipement peut être assigné à une classe (SCIE, EXTRUDEUSE, etc.)
  - Relation Many-to-One : plusieurs équipements peuvent partager la même classe
  - Hydratation automatique : une seule requête SQL pour récupérer équipement + classe
  - Validation d'intégrité : impossible de supprimer une classe utilisée par des équipements

### Améliorations techniques

- **Optimisation des requêtes** : Les données de classe sont récupérées via LEFT JOIN (1 seule requête)
- **Performance** : Pas d'impact sur les performances - le LEFT JOIN est sur une table de référence
- **Validation** : Code unique par classe pour éviter les doublons
- **Sécurité** : Protection CASCADE - impossible de supprimer une classe en usage

### Structure de base de données

- Nouvelle table `equipement_class` avec colonnes : id, code (unique), label, description
- Nouvelle colonne `equipement_class_id` (UUID, nullable) dans la table `machine`
- Foreign key avec ON DELETE RESTRICT pour protéger les données

---

## [1.2.14] - 7 février 2026

### Corrections

- **Correction complète quantity_fulfilled → quantity** : Remplacement dans tous les fichiers
  - Correction dans `purchase_requests/repo.py` : SELECT et INSERT/UPDATE des order_lines
  - Correction dans `supplier_order_lines/repo.py` : Tous les INSERT et paramètre de méthode `link_purchase_request`
  - Correction dans `supplier_orders/repo.py` : SELECT des purchase_requests liées
  - Impact : Le dispatch et la liaison purchase_request ↔ order_line fonctionnent correctement

- **Amélioration dispatch** : Gestion du cache orders_cache en cas de rollback
  - Nettoyage du cache si un supplier_order créé dans un savepoint est rollback
  - Évite les erreurs de foreign key sur des orders qui n'existent plus

- **Schema SupplierOrderUpdate** : Nouveau schéma pour updates partiels
  - Tous les champs optionnels (incluant `supplier_id`, `received_at`)
  - Permet de faire des PUT avec seulement les champs à modifier
  - `PUT /supplier_orders/{id}` utilise maintenant `SupplierOrderUpdate` au lieu de `SupplierOrderIn`

---

## [1.2.13] - 6 février 2026

### Corrections

- **Calcul des statuts dérivés** : Correction de bugs critiques dans le calcul des statuts
  - Correction du nom de colonne `quantity_fulfilled` → `quantity` dans la récupération des order_lines
  - Correction de la logique NO_SUPPLIER_REF : statut appliqué même si des order_lines existent
  - Impact : Les demandes affichent maintenant les bons statuts (OPEN, ORDERED, etc.) au lieu de PENDING_DISPATCH
  - Les order_lines étaient silencieusement ignorées à cause d'une erreur SQL masquée par `except Exception: return []`

---

## [1.2.12] - 6 février 2026

### Nouveautés

- **Statistiques interventions enrichies** : Ajout du compteur `purchase_count` dans les stats d'intervention
  - Nombre de demandes d'achat liées à l'intervention (via les actions)
  - Disponible sur `GET /interventions/` et `GET /interventions/{id}`

- **Nouveau statut demandes d'achat `PENDING_DISPATCH`** : Distinction entre "à dispatcher" et "en mutualisation"
  - `PENDING_DISPATCH` (À dispatcher) : Référence fournisseur ok, mais pas encore dans un supplier order
  - `OPEN` (Mutualisation) : Présent dans un supplier order avec des order_lines

- **Dispatch automatique des demandes d'achat** : `POST /purchase_requests/dispatch`
  - Dispatche toutes les demandes en `PENDING_DISPATCH` vers des supplier_orders
  - Pour chaque demande, récupère les fournisseurs liés au stock_item
  - Trouve ou crée un supplier_order ouvert par fournisseur
  - Crée les supplier_order_lines liées aux demandes
  - Retourne un résumé : `dispatched_count`, `created_orders`, `errors`

---

## [1.2.11] - 6 février 2026

### Nouveautés

- **Demandes d'achat liées aux actions** : Les actions d'intervention incluent maintenant les demandes d'achat liées complètes
  - Nouveau champ `purchase_requests` (array de `PurchaseRequestOut`) dans `InterventionActionOut`
  - Utilise `PurchaseRequestRepository.get_by_id()` pour hydrater chaque demande avec toutes ses données
  - Relation M2M via la table de jonction `intervention_action_purchase_request`
  - Permet d'afficher les demandes d'achat associées à chaque action avec leur statut, stock_item, intervention, order_lines

---

## [1.2.10] - 5 février 2026

### Corrections

- **Correction CRUD interventions** : Alignement avec la structure réelle de la table
  - Suppression des colonnes `created_at` et `updated_at` qui n'existent pas dans la table `intervention`
  - Le schéma `InterventionIn` ne contient plus `created_at`

---

## [1.2.9] - 5 février 2026

### Nouveautés

- **CRUD complet pour les interventions** : Ajout des endpoints de création, modification et suppression
  - `POST /interventions/` - Création d'une intervention avec équipement, priorité, type, technicien
  - `PUT /interventions/{id}` - Modification des champs d'une intervention existante
  - `DELETE /interventions/{id}` - Suppression d'une intervention
  - Retourne l'intervention complète avec équipement, stats, actions et status_logs

---

## [1.2.8] - 4 février 2026

### Améliorations

- **Statut “Qualifiée sans référence fournisseur”** : les demandes qualifiées sans référence fournisseur liée sont maintenant distinguées
  - Permet d'identifier rapidement les articles à référencer avant dispatch
  - Cas d'usage : une demande est qualifiée (article stock lié) mais aucun fournisseur n'est encore associé

---

## [1.2.7] - 4 février 2026

### Améliorations

- **Hydratation des interventions dans les demandes d'achat** : Les endpoints de demandes d'achat incluent maintenant les informations complètes de l'intervention liée
  - `GET /purchase_requests/` retourne l'objet `intervention` avec : id, code, title, priority, status_actual
  - L'équipement associé à l'intervention est également inclus (id, code, name)
  - Plus besoin de faire une requête supplémentaire pour avoir le contexte de l'intervention
  - Appliqué aux endpoints : `GET /purchase_requests/`, `GET /purchase_requests/{id}`, `GET /purchase_requests/intervention/{id}`

---

## [1.2.6] - 4 février 2026

### Corrections

- **Export CSV/Email** : Correction du bug qui empêchait l'affichage des lignes de commande
  - Les exports incluent maintenant toutes les lignes de la commande fournisseur
  - Suppression de la jointure incorrecte avec `manufacturer_item` (colonnes inexistantes)
  - Les informations fabricant sont récupérées depuis `supplier_order_line.manufacturer` et `manufacturer_ref`

---

## [1.2.5] - 3 février 2026

### Améliorations

- **Templates d'export configurables** : Séparation des templates dans [config/export_templates.py](config/export_templates.py)
  - Templates CSV : En-têtes, format de ligne, nom de fichier
  - Templates email : Sujet, corps texte, corps HTML
  - Commentaires explicatifs pour faciliter les personnalisations
  - Modification des templates sans toucher au code des routes
  - Contraintes documentées (HTML email, caractères spéciaux, etc.)

---

## [1.2.4] - 3 février 2026

### 📤 Export des commandes fournisseurs

#### Nouveautés

- **Export CSV** : Téléchargez une commande au format tableur
  - Articles sélectionnés avec références, spécifications et quantités
  - Prêt à imprimer ou envoyer par email
  - Demandes d'achat liées visibles pour chaque ligne

- **Génération d'email** : Créez un email de commande en un clic
  - Sujet et corps de l'email pré-remplis
  - Version texte et HTML disponibles
  - Email du fournisseur inclus automatiquement

#### Nouveaux endpoints

- `POST /supplier_orders/{id}/export/csv` - Télécharge le CSV
- `POST /supplier_orders/{id}/export/email` - Génère le contenu email

---

## [1.2.3] - 3 février 2026

### ⏱️ Suivi de l'âge des commandes fournisseurs

#### Nouveautés

- **Indicateurs d'âge** : Les commandes affichent maintenant leur ancienneté
  - `age_days` : nombre de jours depuis la création
  - `age_color` : indicateur visuel (gray < 7j, orange 7-14j, red > 14j)
  - `is_blocking` : commande bloquante si en attente depuis plus de 7 jours

#### Statuts disponibles

- `OPEN` : Commande créée, en attente d'envoi
- `SENT` : Commande envoyée au fournisseur
- `ACK` : Accusé de réception du fournisseur
- `RECEIVED` : Livraison reçue
- `CLOSED` : Commande clôturée
- `CANCELLED` : Commande annulée

---

## [1.2.2] - 3 février 2026

### 📦 Commandes fournisseurs enrichies

#### Nouveauté

- **Informations fournisseur incluses** : Les commandes fournisseurs affichent maintenant les coordonnées du fournisseur
  - Nom, code, contact, email, téléphone
  - Plus besoin de faire une requête supplémentaire pour avoir les infos du fournisseur

---

## [1.2.1] - 3 février 2026

### 🔄 Simplification du statut des demandes d'achat

#### Changement

- **Un seul statut** : Le champ `status` (manuel) a été supprimé au profit de `derived_status` (calculé automatiquement)
  - Évite les incohérences entre deux sources de vérité
  - Le statut reflète toujours l'état réel de la demande
  - Plus besoin de mettre à jour manuellement le statut

#### Impact technique

- `PurchaseRequestOut.status` → supprimé
- `PurchaseRequestOut.derived_status` → obligatoire (non nullable)
- Le champ `status` n'est plus modifiable via `PUT /purchase_requests/{id}`

---

## [1.2.0] - 1er février 2026

### 🚀 Demandes d'achat optimisées

#### Nouveautés

- **Listes plus rapides** : Les tableaux de demandes d'achat se chargent instantanément
  - Affichage du statut calculé automatiquement (En attente, Devis reçu, Commandé, Reçu...)
  - Compteurs visibles : nombre de devis, fournisseurs contactés
  - Plus besoin d'ouvrir chaque demande pour voir son état

- **Détails complets en un clic** : Toutes les informations dans une seule page
  - Intervention associée avec son équipement
  - Article en stock avec ses références
  - Tous les fournisseurs contactés avec leurs coordonnées et prix

- **Nouveau tableau de bord** : Statistiques des demandes d'achat
  - Combien de demandes en attente, en cours, terminées
  - Répartition par urgence
  - Articles les plus demandés

#### Améliorations

- Le statut des demandes est maintenant calculé automatiquement selon l'avancement
- Les tableaux affichent uniquement l'essentiel (chargement 5x plus rapide)
- Une seule requête pour voir tous les détails d'une demande

#### Statuts des demandes

- 🟡 **À qualifier** : Pas de référence stock normalisée (besoin de qualification)
- ⚪ **En attente** : Prête à être dispatchée aux fournisseurs
- 🟠 **Devis reçu** : Au moins un fournisseur a répondu
- 🔵 **Commandé** : Commande passée chez un fournisseur
- 🟣 **Partiellement reçu** : Livraison partielle
- 🟢 **Reçu** : Livraison complète
- 🔴 **Refusé** : Demande annulée

---

## [1.1.7] - 29 janvier 2026

### Nouveautés

- **Module de gestion des commandes fournisseurs**: Ensemble complet d'endpoints pour la gestion des commandes
  - `GET /supplier_orders` - Liste des commandes avec filtres (statut, fournisseur)
  - `GET /supplier_orders/{id}` - Détail d'une commande avec ses lignes
  - `GET /supplier_orders/number/{order_number}` - Recherche par numéro de commande
  - `POST /supplier_orders` - Création d'une nouvelle commande
  - `PUT /supplier_orders/{id}` - Mise à jour d'une commande
  - `DELETE /supplier_orders/{id}` - Suppression d'une commande (cascade sur les lignes)
  - Numéro de commande auto-généré par trigger base de données
  - Calcul automatique du montant total basé sur les lignes

- **Module de lignes de commande fournisseur**: Gestion des articles commandés
  - `GET /supplier_order_lines` - Liste des lignes avec filtres (commande, article, sélection)
  - `GET /supplier_order_lines/order/{supplier_order_id}` - Toutes les lignes d'une commande
  - `GET /supplier_order_lines/{id}` - Détail d'une ligne avec article et demandes d'achat liées
  - `POST /supplier_order_lines` - Création d'une ligne avec liaison optionnelle aux demandes d'achat
  - `PUT /supplier_order_lines/{id}` - Mise à jour d'une ligne
  - `DELETE /supplier_order_lines/{id}` - Suppression d'une ligne
  - `POST /supplier_order_lines/{id}/purchase_requests` - Lier une demande d'achat à une ligne
  - `DELETE /supplier_order_lines/{id}/purchase_requests/{pr_id}` - Délier une demande d'achat
  - Prix total calculé automatiquement (quantité × prix unitaire)
  - Support complet des devis (prix, date réception, fabricant, délai livraison)

- **Module de demandes d'achat**: Suivi des demandes de matériel
  - `GET /purchase_requests` - Liste avec filtres (statut, intervention, urgence)
  - `GET /purchase_requests/{id}` - Détail d'une demande avec lignes de commande liées
  - `GET /purchase_requests/intervention/{id}` - Demandes liées à une intervention
  - `POST /purchase_requests` - Création d'une demande
  - `PUT /purchase_requests/{id}` - Mise à jour d'une demande
  - `DELETE /purchase_requests/{id}` - Suppression d'une demande
  - Liaison bidirectionnelle avec les lignes de commande fournisseur
  - Enrichissement automatique avec les détails de l'article en stock

- **Module de gestion du stock**: Catalogue d'articles
  - `GET /stock_items` - Liste avec filtres (famille, sous-famille, recherche)
  - `GET /stock_items/{id}` - Détail d'un article
  - `GET /stock_items/ref/{ref}` - Recherche par référence
  - `POST /stock_items` - Création d'un article
  - `PUT /stock_items/{id}` - Mise à jour d'un article
  - `PATCH /stock_items/{id}/quantity` - Mise à jour rapide de la quantité
  - `DELETE /stock_items/{id}` - Suppression d'un article
  - Référence auto-générée par trigger (famille-sous_famille-spec-dimension)
  - Compteur automatique des références fournisseurs

### Améliorations techniques

- Relation M2M complète entre lignes de commande fournisseur et demandes d'achat
  - Table de liaison `supplier_order_line_purchase_request` avec quantité allouée
  - Permet de tracer quelle demande d'achat est satisfaite par quelle ligne de commande
  - Une ligne peut satisfaire plusieurs demandes, une demande peut être liée à plusieurs lignes
- Schémas légers (`ListItem`) pour les listes, schémas complets (`Out`) pour les détails
- Conversion automatique des Decimal en float pour la sérialisation JSON
- Enrichissement automatique des relations (stock_item, purchase_requests, order_lines)
- Tous les endpoints respectent les standards de pagination (skip, limit max 1000)
- Gestion cohérente des erreurs avec `DatabaseError` et `NotFoundError`

## [1.1.1] - 29 janvier 2026

### Corrections

- **Support du format de date standard**: Correction de la validation Pydantic pour accepter le format date "YYYY-MM-DD"
  - Utilisation de `Field(default=None)` pour tous les champs optionnels (compatibilité Pydantic v2)
  - Les schémas `InterventionActionIn` et `InterventionStatusLogIn` acceptent maintenant correctement les dates au format "YYYY-MM-DD"
  - Le validateur centralisé `validate_date()` convertit automatiquement les strings en datetime
  - Fix: Erreur "Input should be a valid datetime, invalid datetime separator" résolue

### Améliorations techniques

- Migration complète vers Pydantic v2 avec `Field()` pour les valeurs par défaut
- Tous les schémas utilisent `from_attributes = True` (syntaxe Pydantic v2)
- Meilleure gestion des champs optionnels dans tous les schémas de l'API

---

## [1.1.0] - 27 janvier 2026

### Nouveautés

- **Historique des changements de statut**: Les interventions incluent maintenant leur historique complet de changements de statut via `status_logs`
  - `GET /interventions/{id}` retourne automatiquement tous les changements de statut avec détails enrichis
  - Chaque log inclut le statut source, le statut destination, le technicien, la date et les notes
  - Les détails des statuts sont enrichis avec les informations de la table de référence (code, label, couleur)
- **Filtre d'impression**: Nouveau paramètre `printed` pour `GET /interventions`
  - Permet de filtrer les interventions imprimées (`printed=true`) ou non imprimées (`printed=false`)
  - Omission du paramètre retourne toutes les interventions (comportement par défaut)

### Corrections

- **Validation des status logs**: Correction des erreurs de validation Pydantic
  - `technician_id` est maintenant optionnel (peut être NULL en base de données)
  - Le champ `value` des statuts est correctement converti en integer ou NULL (gère les valeurs textuelles en base)
- **Dépendance circulaire**: Résolution de l'import circulaire entre `InterventionRepository` et `InterventionStatusLogValidator`
  - Utilisation d'un import lazy dans le validator pour éviter le blocage au démarrage

### Améliorations techniques

- Ajout de la méthode `_safe_int_value()` pour gérer proprement la conversion des valeurs de statut
- Les status logs sont chargés automatiquement pour les détails d'intervention mais pas dans les listes (optimisation performance)
- Schéma `InterventionOut` étendu avec le champ `status_logs: List[InterventionStatusLogOut]`
- **Validation des dates**: Nouveau validateur centralisé `validate_date()` dans `api/utils/validators.py`
  - Rejette les dates invalides (ex: 2026-01-36)
  - Vérifie la plage d'années (1900-2100)
  - Support des formats: date seule "YYYY-MM-DD", datetime complet "YYYY-MM-DDTHH:MM:SS", avec timezone "YYYY-MM-DDTHH:MM:SS.microsZ"
  - Réutilisable dans tous les endpoints
- **Validation des actions d'intervention**:
  - `complexity_anotation` est maintenant optionnel par défaut, mais obligatoire si `complexity_score > 5`
  - `created_at` est maintenant optionnel lors de la création - utilise automatiquement `now()` si omis
  - Permet de backdater les actions (un technicien peut saisir une action plusieurs jours après l'intervention)

---

## [1.0.1] - 26 janvier 2026

### Corrections

- Code cleanup interne (suppression de méthodes mortes et imports inutilisés)
- Respect strict de PEP8 (import ordering, docstrings de module)
- Migration vers syntaxe Python 3.9+ (list/dict au lieu de List/Dict, union type | au lieu de Optional)
- Chaînage d'exceptions amélioré (raise ... from e)

### Améliorations techniques

- Réduction de la complexité du code (moins de méthodes inutilisées)
- Meilleure conformité Pylint (zéro avertissements dans les domaines)
- Imports organisés selon PEP8 (stdlib avant third-party)

---

## [1.0.0] - 26 janvier 2026

### Nouveautés

- **Affichage simplifié des équipements**: Les listes et détails d'équipements affichent maintenant seulement l'état de santé (critique, avertissement, maintenance, ok) sans surcharger avec des statistiques complexes
- **Statistiques séparées**: Une nouvelle section dédiée pour voir les détails des interventions (nombre d'interventions ouvertes, par type, par priorité)
- **État de santé ultra-rapide**: Une nouvelle API pour afficher rapidement si un équipement va bien ou a besoin d'attention
- **Filtrer par période**: Possibilité de voir les statistiques sur une période spécifique (ex: interventions du mois dernier)
- **Recherche avancée des interventions**:
  - Par équipement
  - Par statut (ouvert, fermé, en cours...)
  - Par urgence (faible, normal, important, urgent)
  - Tri flexible (par date, urgence, etc.)
  - Voir les statistiques optionnellement
- **Tri par urgence**: Les interventions les plus urgentes apparaissent en premier
- **Code plus propre**: Simplification du code interne avec des constantes réutilisables

### Améliorations

- **Noms plus clairs**: Les modèles de données ont des noms plus simples et directs
- **Pages plus légères**: Les réponses API contiennent moins d'informations inutiles
- **Pas de doublons**: Suppression des données redondantes (status, color) qui apparaissaient partout
- **Moins de requêtes**: Le serveur fait moins de requêtes à la base de données

### Corrections

- Les pages d'équipement ne donnaient plus d'erreurs
- Suppression des messages d'erreur lors du chargement des interventions
- Performance améliorée

### Comment ça marche maintenant

- **État de santé d'un équipement**:
  - 🔴 critique: au moins 1 intervention très urgente
  - 🟡 avertissement: plus de 5 interventions ouvertes
  - 🟠 maintenance: 1 ou plusieurs interventions ouvertes
  - 🟢 ok: aucune intervention en attente
- **Statistiques**: Comptage des interventions par type et urgence
- **Recherche**: Rapide et efficace, sans chercher partout
- **Priorisation**: Les interventions urgentes sont clairement identifiées

---

## Historique des versions

Ce journal suit la convention [Keep a Changelog](https://keepachangelog.com/).
Les versions suivent [Semantic Versioning](https://semver.org/).
