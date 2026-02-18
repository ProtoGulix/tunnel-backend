# API Manifest — GMAO API v2.0.0

> Dernière mise à jour : 2026-02-18

Documentation complète de l'API. Chaque endpoint possède sa propre page avec formats JSON d'entrée/sortie, règles métier et exemples.

## Quick Start

```bash
# Démarrer l'API
uvicorn api.app:app --reload

# Vérifier l'état
curl http://localhost:8000/health

# S'authentifier
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret", "mode": "session"}'

# Lister les interventions (avec JWT)
curl http://localhost:8000/interventions \
  -H "Authorization: Bearer {access_token}"
```

---

## Endpoints

### Système

| Méthode | Endpoint      | Description      | Auth   | Doc                                   |
| ------- | ------------- | ---------------- | ------ | ------------------------------------- |
| GET     | `/health`     | État de l'API    | Public | [health.md](docs/endpoints/health.md) |
| POST    | `/auth/login` | Authentification | Public | [auth.md](docs/endpoints/auth.md)     |

### Interventions

| Méthode | Endpoint                      | Description                         | Doc                                                 |
| ------- | ----------------------------- | ----------------------------------- | --------------------------------------------------- |
| GET     | `/interventions`              | Liste avec filtres, tri, pagination | [interventions.md](docs/endpoints/interventions.md) |
| GET     | `/interventions/{id}`         | Détail avec actions, logs, stats    | [interventions.md](docs/endpoints/interventions.md) |
| GET     | `/interventions/{id}/actions` | Actions d'une intervention          | [interventions.md](docs/endpoints/interventions.md) |
| POST    | `/interventions`              | Créer                               | [interventions.md](docs/endpoints/interventions.md) |
| PUT     | `/interventions/{id}`         | Modifier                            | [interventions.md](docs/endpoints/interventions.md) |
| DELETE  | `/interventions/{id}`         | Supprimer                           | [interventions.md](docs/endpoints/interventions.md) |

### Actions d'intervention

| Méthode | Endpoint                     | Description | Doc                                                               |
| ------- | ---------------------------- | ----------- | ----------------------------------------------------------------- |
| GET     | `/intervention-actions`      | Liste       | [intervention-actions.md](docs/endpoints/intervention-actions.md) |
| GET     | `/intervention-actions/{id}` | Détail      | [intervention-actions.md](docs/endpoints/intervention-actions.md) |
| POST    | `/intervention-actions`      | Créer       | [intervention-actions.md](docs/endpoints/intervention-actions.md) |

### Statuts d'intervention

| Méthode | Endpoint                        | Description            | Doc                                                                     |
| ------- | ------------------------------- | ---------------------- | ----------------------------------------------------------------------- |
| GET     | `/intervention-status`          | Référentiel statuts    | [intervention-status.md](docs/endpoints/intervention-status.md)         |
| GET     | `/intervention-status-log`      | Historique changements | [intervention-status-log.md](docs/endpoints/intervention-status-log.md) |
| GET     | `/intervention-status-log/{id}` | Détail d'un log        | [intervention-status-log.md](docs/endpoints/intervention-status-log.md) |
| POST    | `/intervention-status-log`      | Créer un changement    | [intervention-status-log.md](docs/endpoints/intervention-status-log.md) |

### Référentiels

| Méthode | Endpoint                                | Description                | Doc                                                           |
| ------- | --------------------------------------- | -------------------------- | ------------------------------------------------------------- |
| GET     | `/action-categories`                    | Catégories d'actions       | [action-categories.md](docs/endpoints/action-categories.md)   |
| GET     | `/action-categories/{id}`               | Détail catégorie           | [action-categories.md](docs/endpoints/action-categories.md)   |
| GET     | `/action-categories/{id}/subcategories` | Sous-catégories            | [action-categories.md](docs/endpoints/action-categories.md)   |
| GET     | `/action-subcategories`                 | Toutes les sous-catégories | [action-categories.md](docs/endpoints/action-categories.md)   |
| GET     | `/action-subcategories/{id}`            | Détail sous-catégorie      | [action-categories.md](docs/endpoints/action-categories.md)   |
| GET     | `/complexity-factors`                   | Facteurs de complexité     | [complexity-factors.md](docs/endpoints/complexity-factors.md) |
| GET     | `/complexity-factors/{code}`            | Détail facteur             | [complexity-factors.md](docs/endpoints/complexity-factors.md) |

### Equipements

| Méthode | Endpoint                   | Description              | Doc                                             |
| ------- | -------------------------- | ------------------------ | ----------------------------------------------- |
| GET     | `/equipements`             | Liste avec état de santé | [equipements.md](docs/endpoints/equipements.md) |
| GET     | `/equipements/{id}`        | Détail avec enfants      | [equipements.md](docs/endpoints/equipements.md) |
| POST    | `/equipements`             | Créer                    | [equipements.md](docs/endpoints/equipements.md) |
| PUT     | `/equipements/{id}`        | Modifier                 | [equipements.md](docs/endpoints/equipements.md) |
| DELETE  | `/equipements/{id}`        | Supprimer                | [equipements.md](docs/endpoints/equipements.md) |
| GET     | `/equipements/{id}/stats`  | Statistiques             | [equipements.md](docs/endpoints/equipements.md) |
| GET     | `/equipements/{id}/health` | Santé (polling)          | [equipements.md](docs/endpoints/equipements.md) |

### Classes d'équipement

| Méthode | Endpoint                 | Description | Doc                                                       |
| ------- | ------------------------ | ----------- | --------------------------------------------------------- |
| GET     | `/equipement-class`      | Liste       | [equipement-class.md](docs/endpoints/equipement-class.md) |
| GET     | `/equipement-class/{id}` | Détail      | [equipement-class.md](docs/endpoints/equipement-class.md) |
| POST    | `/equipement-class`      | Créer       | [equipement-class.md](docs/endpoints/equipement-class.md) |
| PATCH   | `/equipement-class/{id}` | Modifier    | [equipement-class.md](docs/endpoints/equipement-class.md) |
| DELETE  | `/equipement-class/{id}` | Supprimer   | [equipement-class.md](docs/endpoints/equipement-class.md) |

### Statistiques & Analyse

| Méthode | Endpoint                  | Description                | Doc                                 |
| ------- | ------------------------- | -------------------------- | ----------------------------------- |
| GET     | `/stats/service-status`   | Santé du service           | [stats.md](docs/endpoints/stats.md) |
| GET     | `/stats/charge-technique` | Charge technique [BETA]    | [stats.md](docs/endpoints/stats.md) |
| GET     | `/stats/anomalies-saisie` | Anomalies de saisie [BETA] | [stats.md](docs/endpoints/stats.md) |
| GET     | `/stats/qualite-donnees`  | Qualité des données        | [stats.md](docs/endpoints/stats.md) |

### Demandes d'achat

| Méthode | Endpoint                                         | Description               | Doc                                                         |
| ------- | ------------------------------------------------ | ------------------------- | ----------------------------------------------------------- |
| GET     | `/purchase-requests`                             | Liste [LEGACY]            | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| GET     | `/purchase-requests/list`                        | Liste optimisée [v1.2.0]  | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| GET     | `/purchase-requests/detail/{id}`                 | Détail enrichi [v1.2.0]   | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| GET     | `/purchase-requests/stats`                       | Dashboard stats [v1.2.0]  | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| GET     | `/purchase-requests/{id}`                        | Détail [LEGACY]           | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| GET     | `/purchase-requests/intervention/{id}`           | Par intervention [LEGACY] | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| GET     | `/purchase-requests/intervention/{id}/optimized` | Par intervention [v1.2.0] | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| POST    | `/purchase-requests`                             | Créer                     | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| PUT     | `/purchase-requests/{id}`                        | Modifier                  | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| DELETE  | `/purchase-requests/{id}`                        | Supprimer                 | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| POST    | `/purchase-requests/dispatch`                    | Dispatch auto [v1.2.12]   | [purchase-requests.md](docs/endpoints/purchase-requests.md) |

### Articles en stock

| Méthode | Endpoint                                 | Description                            | Doc                                             |
| ------- | ---------------------------------------- | -------------------------------------- | ----------------------------------------------- |
| GET     | `/stock-items`                           | Liste avec filtres                     | [stock-items.md](docs/endpoints/stock-items.md) |
| GET     | `/stock-items/{id}`                      | Détail                                 | [stock-items.md](docs/endpoints/stock-items.md) |
| GET     | `/stock-items/{id}/with-characteristics` | Détail avec caractéristiques [v1.11.0] | [stock-items.md](docs/endpoints/stock-items.md) |
| GET     | `/stock-items/ref/{ref}`                 | Par référence                          | [stock-items.md](docs/endpoints/stock-items.md) |
| POST    | `/stock-items`                           | Créer (legacy ou template) [v1.11.0]   | [stock-items.md](docs/endpoints/stock-items.md) |
| PUT     | `/stock-items/{id}`                      | Modifier                               | [stock-items.md](docs/endpoints/stock-items.md) |
| PATCH   | `/stock-items/{id}/quantity`             | Modifier quantité                      | [stock-items.md](docs/endpoints/stock-items.md) |
| DELETE  | `/stock-items/{id}`                      | Supprimer                              | [stock-items.md](docs/endpoints/stock-items.md) |

### Sous-familles de stock

| Méthode | Endpoint                                              | Description                    | Doc                                                           |
| ------- | ----------------------------------------------------- | ------------------------------ | ------------------------------------------------------------- |
| GET     | `/stock-sub-families`                                 | Liste avec templates [v1.11.0] | [stock-sub-families.md](docs/endpoints/stock-sub-families.md) |
| GET     | `/stock-sub-families/{family_code}/{sub_family_code}` | Détail avec template [v1.11.0] | [stock-sub-families.md](docs/endpoints/stock-sub-families.md) |
| PATCH   | `/stock-sub-families/{family_code}/{sub_family_code}` | Modifier                       | [stock-sub-families.md](docs/endpoints/stock-sub-families.md) |

### Templates de pièces (v1.4.0)

| Méthode | Endpoint                         | Description                                  | Doc                                                   |
| ------- | -------------------------------- | -------------------------------------------- | ----------------------------------------------------- |
| GET     | `/part-templates`                | Liste templates (dernière version) [v1.11.0] | [part-templates.md](docs/endpoints/part-templates.md) |
| GET     | `/part-templates/code/{code}`    | Toutes versions d'un template [v1.11.0]      | [part-templates.md](docs/endpoints/part-templates.md) |
| GET     | `/part-templates/{id}?version=X` | Template complet avec champs [v1.11.0]       | [part-templates.md](docs/endpoints/part-templates.md) |
| POST    | `/part-templates`                | Créer template (v1) [v1.11.0]                | [part-templates.md](docs/endpoints/part-templates.md) |
| POST    | `/part-templates/{id}/versions`  | Créer nouvelle version [v1.11.0]             | [part-templates.md](docs/endpoints/part-templates.md) |
| DELETE  | `/part-templates/{id}?version=X` | Supprimer template/version [v1.11.0]         | [part-templates.md](docs/endpoints/part-templates.md) |

### Commandes fournisseurs

| Méthode | Endpoint                             | Description         | Doc                                                     |
| ------- | ------------------------------------ | ------------------- | ------------------------------------------------------- |
| GET     | `/supplier-orders`                   | Liste avec filtres  | [supplier-orders.md](docs/endpoints/supplier-orders.md) |
| GET     | `/supplier-orders/{id}`              | Détail avec lignes  | [supplier-orders.md](docs/endpoints/supplier-orders.md) |
| GET     | `/supplier-orders/number/{n}`        | Par numéro          | [supplier-orders.md](docs/endpoints/supplier-orders.md) |
| POST    | `/supplier-orders`                   | Créer               | [supplier-orders.md](docs/endpoints/supplier-orders.md) |
| PUT     | `/supplier-orders/{id}`              | Modifier            | [supplier-orders.md](docs/endpoints/supplier-orders.md) |
| DELETE  | `/supplier-orders/{id}`              | Supprimer (cascade) | [supplier-orders.md](docs/endpoints/supplier-orders.md) |
| POST    | `/supplier-orders/{id}/export/csv`   | Export CSV          | [supplier-orders.md](docs/endpoints/supplier-orders.md) |
| POST    | `/supplier-orders/{id}/export/email` | Génération email    | [supplier-orders.md](docs/endpoints/supplier-orders.md) |

### Lignes de commande fournisseur

| Méthode | Endpoint                                               | Description      | Doc                                                               |
| ------- | ------------------------------------------------------ | ---------------- | ----------------------------------------------------------------- |
| GET     | `/supplier-order-lines`                                | Liste            | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md) |
| GET     | `/supplier-order-lines/{id}`                           | Détail           | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md) |
| GET     | `/supplier-order-lines/order/{id}`                     | Par commande     | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md) |
| POST    | `/supplier-order-lines`                                | Créer            | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md) |
| PUT     | `/supplier-order-lines/{id}`                           | Modifier         | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md) |
| DELETE  | `/supplier-order-lines/{id}`                           | Supprimer        | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md) |
| POST    | `/supplier-order-lines/{id}/purchase-requests`         | Lier une demande | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md) |
| DELETE  | `/supplier-order-lines/{id}/purchase-requests/{pr_id}` | Délier           | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md) |

### Fournisseurs

| Méthode | Endpoint                 | Description | Doc                                         |
| ------- | ------------------------ | ----------- | ------------------------------------------- |
| GET     | `/suppliers`             | Liste       | [suppliers.md](docs/endpoints/suppliers.md) |
| GET     | `/suppliers/{id}`        | Détail      | [suppliers.md](docs/endpoints/suppliers.md) |
| GET     | `/suppliers/code/{code}` | Par code    | [suppliers.md](docs/endpoints/suppliers.md) |
| POST    | `/suppliers`             | Créer       | [suppliers.md](docs/endpoints/suppliers.md) |
| PUT     | `/suppliers/{id}`        | Modifier    | [suppliers.md](docs/endpoints/suppliers.md) |
| DELETE  | `/suppliers/{id}`        | Supprimer   | [suppliers.md](docs/endpoints/suppliers.md) |

### Références fournisseurs (Stock - Supplier)

| Méthode | Endpoint                                   | Description     | Doc                                                               |
| ------- | ------------------------------------------ | --------------- | ----------------------------------------------------------------- |
| GET     | `/stock-item-suppliers`                    | Liste           | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md) |
| GET     | `/stock-item-suppliers/{id}`               | Détail          | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md) |
| GET     | `/stock-item-suppliers/stock-item/{id}`    | Par article     | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md) |
| GET     | `/stock-item-suppliers/supplier/{id}`      | Par fournisseur | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md) |
| POST    | `/stock-item-suppliers`                    | Créer           | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md) |
| PUT     | `/stock-item-suppliers/{id}`               | Modifier        | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md) |
| POST    | `/stock-item-suppliers/{id}/set-preferred` | Définir préféré | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md) |
| DELETE  | `/stock-item-suppliers/{id}`               | Supprimer       | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md) |

### Exports (PDF / QR)

| Méthode | Endpoint                             | Description | Auth   | Doc                                     |
| ------- | ------------------------------------ | ----------- | ------ | --------------------------------------- |
| GET     | `/exports/interventions/{id}/pdf`    | Rapport PDF | JWT    | [exports.md](docs/endpoints/exports.md) |
| GET     | `/exports/interventions/{id}/qrcode` | QR Code PNG | Public | [exports.md](docs/endpoints/exports.md) |

### Utilisateurs (proxy Directus)

| Méthode | Endpoint      | Description                     | Doc                                 |
| ------- | ------------- | ------------------------------- | ----------------------------------- |
| GET     | `/users`      | Liste avec filtres et recherche | [users.md](docs/endpoints/users.md) |
| GET     | `/users/me`   | Utilisateur courant (JWT)       | [users.md](docs/endpoints/users.md) |
| GET     | `/users/{id}` | Détail par UUID                 | [users.md](docs/endpoints/users.md) |

---

## Schemas partagés

Schemas JSON réutilisés dans plusieurs endpoints : [shared-schemas.md](docs/shared-schemas.md)

- [EquipementHealth](docs/shared-schemas.md#equipementhealth) — Indicateur de santé
- [EquipementClass](docs/shared-schemas.md#equipementclass) — Classification
- [DerivedStatus](docs/shared-schemas.md#derivedstatus) — Statut calculé (demandes d'achat)
- [InterventionInfo](docs/shared-schemas.md#interventioninfo) — Intervention légère (embarqué)
- [StockItemListItem](docs/shared-schemas.md#stockitemlistitem) — Article stock léger
- [LinkedOrderLine](docs/shared-schemas.md#linkedorderline) — Ligne de commande liée
- [LinkedPurchaseRequest](docs/shared-schemas.md#linkedpurchaserequest) — Demande liée

---

## Configuration

| Variable                  | Défaut                                | Description                |
| ------------------------- | ------------------------------------- | -------------------------- |
| `DATABASE_URL`            | `postgresql://...`                    | Connexion PostgreSQL       |
| `DIRECTUS_URL`            | `http://localhost:8055`               | Service d'authentification |
| `AUTH_DISABLED`           | `false`                               | Désactiver JWT (dev)       |
| `FRONTEND_URL`            | `http://localhost:5173`               | URL frontend (CORS)        |
| `EXPORT_TEMPLATE_DIR`     | `config/templates`                    | Dossier templates          |
| `EXPORT_TEMPLATE_FILE`    | `fiche_intervention_v8.html`          | Fichier template           |
| `EXPORT_TEMPLATE_VERSION` | `v8.0`                                | Version template           |
| `EXPORT_TEMPLATE_DATE`    | `2025-10-03`                          | Date version template      |
| `EXPORT_QR_BASE_URL`      | `http://localhost:5173/interventions` | URL QR codes               |
| `EXPORT_QR_LOGO_PATH`     | `config/templates/logo.png`           | Logo QR overlay            |

---

## Conventions

Voir [shared-schemas.md — Conventions communes](docs/shared-schemas.md#conventions-communes) pour : authentification, pagination, formats de date, codes erreur.
