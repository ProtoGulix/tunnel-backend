# API Manifest — GMAO API v1.9.0

> Dernière mise à jour : 2026-02-15

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

| Méthode | Endpoint | Description | Auth | Doc |
|---|---|---|---|---|
| GET | `/health` | État de l'API | Public | [health.md](docs/endpoints/health.md) |
| POST | `/auth/login` | Authentification | Public | [auth.md](docs/endpoints/auth.md) |

### Interventions

| Méthode | Endpoint | Description | Doc |
|---|---|---|---|
| GET | `/interventions` | Liste avec filtres, tri, pagination | [interventions.md](docs/endpoints/interventions.md) |
| GET | `/interventions/{id}` | Détail avec actions, logs, stats | [interventions.md](docs/endpoints/interventions.md) |
| GET | `/interventions/{id}/actions` | Actions d'une intervention | [interventions.md](docs/endpoints/interventions.md) |
| POST | `/interventions` | Créer | [interventions.md](docs/endpoints/interventions.md) |
| PUT | `/interventions/{id}` | Modifier | [interventions.md](docs/endpoints/interventions.md) |
| DELETE | `/interventions/{id}` | Supprimer | [interventions.md](docs/endpoints/interventions.md) |

### Actions d'intervention

| Méthode | Endpoint | Description | Doc |
|---|---|---|---|
| GET | `/intervention_actions` | Liste | [intervention-actions.md](docs/endpoints/intervention-actions.md) |
| GET | `/intervention_actions/{id}` | Détail | [intervention-actions.md](docs/endpoints/intervention-actions.md) |
| POST | `/intervention_actions` | Créer | [intervention-actions.md](docs/endpoints/intervention-actions.md) |

### Statuts d'intervention

| Méthode | Endpoint | Description | Doc |
|---|---|---|---|
| GET | `/intervention_status` | Référentiel statuts | [intervention-status.md](docs/endpoints/intervention-status.md) |
| GET | `/intervention_status_log` | Historique changements | [intervention-status-log.md](docs/endpoints/intervention-status-log.md) |
| GET | `/intervention_status_log/{id}` | Détail d'un log | [intervention-status-log.md](docs/endpoints/intervention-status-log.md) |
| POST | `/intervention_status_log` | Créer un changement | [intervention-status-log.md](docs/endpoints/intervention-status-log.md) |

### Référentiels

| Méthode | Endpoint | Description | Doc |
|---|---|---|---|
| GET | `/action_categories` | Catégories d'actions | [action-categories.md](docs/endpoints/action-categories.md) |
| GET | `/action_categories/{id}` | Détail catégorie | [action-categories.md](docs/endpoints/action-categories.md) |
| GET | `/action_categories/{id}/subcategories` | Sous-catégories | [action-categories.md](docs/endpoints/action-categories.md) |
| GET | `/action_subcategories` | Toutes les sous-catégories | [action-categories.md](docs/endpoints/action-categories.md) |
| GET | `/action_subcategories/{id}` | Détail sous-catégorie | [action-categories.md](docs/endpoints/action-categories.md) |
| GET | `/complexity_factors` | Facteurs de complexité | [complexity-factors.md](docs/endpoints/complexity-factors.md) |
| GET | `/complexity_factors/{code}` | Détail facteur | [complexity-factors.md](docs/endpoints/complexity-factors.md) |

### Equipements

| Méthode | Endpoint | Description | Doc |
|---|---|---|---|
| GET | `/equipements` | Liste avec état de santé | [equipements.md](docs/endpoints/equipements.md) |
| GET | `/equipements/{id}` | Détail avec enfants | [equipements.md](docs/endpoints/equipements.md) |
| POST | `/equipements` | Créer | [equipements.md](docs/endpoints/equipements.md) |
| PUT | `/equipements/{id}` | Modifier | [equipements.md](docs/endpoints/equipements.md) |
| DELETE | `/equipements/{id}` | Supprimer | [equipements.md](docs/endpoints/equipements.md) |
| GET | `/equipements/{id}/stats` | Statistiques | [equipements.md](docs/endpoints/equipements.md) |
| GET | `/equipements/{id}/health` | Santé (polling) | [equipements.md](docs/endpoints/equipements.md) |

### Classes d'équipement

| Méthode | Endpoint | Description | Doc |
|---|---|---|---|
| GET | `/equipement_class` | Liste | [equipement-class.md](docs/endpoints/equipement-class.md) |
| GET | `/equipement_class/{id}` | Détail | [equipement-class.md](docs/endpoints/equipement-class.md) |
| POST | `/equipement_class` | Créer | [equipement-class.md](docs/endpoints/equipement-class.md) |
| PATCH | `/equipement_class/{id}` | Modifier | [equipement-class.md](docs/endpoints/equipement-class.md) |
| DELETE | `/equipement_class/{id}` | Supprimer | [equipement-class.md](docs/endpoints/equipement-class.md) |

### Statistiques & Analyse

| Méthode | Endpoint | Description | Doc |
|---|---|---|---|
| GET | `/stats/service-status` | Santé du service | [stats.md](docs/endpoints/stats.md) |
| GET | `/stats/charge-technique` | Charge technique [BETA] | [stats.md](docs/endpoints/stats.md) |
| GET | `/stats/anomalies-saisie` | Anomalies de saisie [BETA] | [stats.md](docs/endpoints/stats.md) |
| GET | `/stats/qualite-donnees` | Qualité des données | [stats.md](docs/endpoints/stats.md) |

### Demandes d'achat

| Méthode | Endpoint | Description | Doc |
|---|---|---|---|
| GET | `/purchase_requests` | Liste [LEGACY] | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| GET | `/purchase_requests/list` | Liste optimisée [v1.2.0] | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| GET | `/purchase_requests/detail/{id}` | Détail enrichi [v1.2.0] | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| GET | `/purchase_requests/stats` | Dashboard stats [v1.2.0] | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| GET | `/purchase_requests/{id}` | Détail [LEGACY] | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| GET | `/purchase_requests/intervention/{id}` | Par intervention [LEGACY] | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| GET | `/purchase_requests/intervention/{id}/optimized` | Par intervention [v1.2.0] | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| POST | `/purchase_requests` | Créer | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| PUT | `/purchase_requests/{id}` | Modifier | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| DELETE | `/purchase_requests/{id}` | Supprimer | [purchase-requests.md](docs/endpoints/purchase-requests.md) |
| POST | `/purchase_requests/dispatch` | Dispatch auto [v1.2.12] | [purchase-requests.md](docs/endpoints/purchase-requests.md) |

### Articles en stock

| Méthode | Endpoint | Description | Doc |
|---|---|---|---|
| GET | `/stock_items` | Liste avec filtres | [stock-items.md](docs/endpoints/stock-items.md) |
| GET | `/stock_items/{id}` | Détail | [stock-items.md](docs/endpoints/stock-items.md) |
| GET | `/stock_items/ref/{ref}` | Par référence | [stock-items.md](docs/endpoints/stock-items.md) |
| POST | `/stock_items` | Créer | [stock-items.md](docs/endpoints/stock-items.md) |
| PUT | `/stock_items/{id}` | Modifier | [stock-items.md](docs/endpoints/stock-items.md) |
| PATCH | `/stock_items/{id}/quantity` | Modifier quantité | [stock-items.md](docs/endpoints/stock-items.md) |
| DELETE | `/stock_items/{id}` | Supprimer | [stock-items.md](docs/endpoints/stock-items.md) |

### Commandes fournisseurs

| Méthode | Endpoint | Description | Doc |
|---|---|---|---|
| GET | `/supplier_orders` | Liste avec filtres | [supplier-orders.md](docs/endpoints/supplier-orders.md) |
| GET | `/supplier_orders/{id}` | Détail avec lignes | [supplier-orders.md](docs/endpoints/supplier-orders.md) |
| GET | `/supplier_orders/number/{n}` | Par numéro | [supplier-orders.md](docs/endpoints/supplier-orders.md) |
| POST | `/supplier_orders` | Créer | [supplier-orders.md](docs/endpoints/supplier-orders.md) |
| PUT | `/supplier_orders/{id}` | Modifier | [supplier-orders.md](docs/endpoints/supplier-orders.md) |
| DELETE | `/supplier_orders/{id}` | Supprimer (cascade) | [supplier-orders.md](docs/endpoints/supplier-orders.md) |
| POST | `/supplier_orders/{id}/export/csv` | Export CSV | [supplier-orders.md](docs/endpoints/supplier-orders.md) |
| POST | `/supplier_orders/{id}/export/email` | Génération email | [supplier-orders.md](docs/endpoints/supplier-orders.md) |

### Lignes de commande fournisseur

| Méthode | Endpoint | Description | Doc |
|---|---|---|---|
| GET | `/supplier_order_lines` | Liste | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md) |
| GET | `/supplier_order_lines/{id}` | Détail | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md) |
| GET | `/supplier_order_lines/order/{id}` | Par commande | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md) |
| POST | `/supplier_order_lines` | Créer | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md) |
| PUT | `/supplier_order_lines/{id}` | Modifier | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md) |
| DELETE | `/supplier_order_lines/{id}` | Supprimer | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md) |
| POST | `/supplier_order_lines/{id}/purchase_requests` | Lier une demande | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md) |
| DELETE | `/supplier_order_lines/{id}/purchase_requests/{pr_id}` | Délier | [supplier-order-lines.md](docs/endpoints/supplier-order-lines.md) |

### Fournisseurs

| Méthode | Endpoint | Description | Doc |
|---|---|---|---|
| GET | `/suppliers` | Liste | [suppliers.md](docs/endpoints/suppliers.md) |
| GET | `/suppliers/{id}` | Détail | [suppliers.md](docs/endpoints/suppliers.md) |
| GET | `/suppliers/code/{code}` | Par code | [suppliers.md](docs/endpoints/suppliers.md) |
| POST | `/suppliers` | Créer | [suppliers.md](docs/endpoints/suppliers.md) |
| PUT | `/suppliers/{id}` | Modifier | [suppliers.md](docs/endpoints/suppliers.md) |
| DELETE | `/suppliers/{id}` | Supprimer | [suppliers.md](docs/endpoints/suppliers.md) |

### Références fournisseurs (Stock - Supplier)

| Méthode | Endpoint | Description | Doc |
|---|---|---|---|
| GET | `/stock_item_suppliers` | Liste | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md) |
| GET | `/stock_item_suppliers/{id}` | Détail | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md) |
| GET | `/stock_item_suppliers/stock_item/{id}` | Par article | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md) |
| GET | `/stock_item_suppliers/supplier/{id}` | Par fournisseur | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md) |
| POST | `/stock_item_suppliers` | Créer | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md) |
| PUT | `/stock_item_suppliers/{id}` | Modifier | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md) |
| POST | `/stock_item_suppliers/{id}/set_preferred` | Définir préféré | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md) |
| DELETE | `/stock_item_suppliers/{id}` | Supprimer | [stock-item-suppliers.md](docs/endpoints/stock-item-suppliers.md) |

### Exports (PDF / QR)

| Méthode | Endpoint | Description | Auth | Doc |
|---|---|---|---|---|
| GET | `/exports/interventions/{id}/pdf` | Rapport PDF | JWT | [exports.md](docs/endpoints/exports.md) |
| GET | `/exports/interventions/{id}/qrcode` | QR Code PNG | Public | [exports.md](docs/endpoints/exports.md) |

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

| Variable | Défaut | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://...` | Connexion PostgreSQL |
| `DIRECTUS_URL` | `http://localhost:8055` | Service d'authentification |
| `AUTH_DISABLED` | `false` | Désactiver JWT (dev) |
| `FRONTEND_URL` | `http://localhost:5173` | URL frontend (CORS) |
| `EXPORT_TEMPLATE_DIR` | `config/templates` | Dossier templates |
| `EXPORT_TEMPLATE_FILE` | `fiche_intervention_v8.html` | Fichier template |
| `EXPORT_TEMPLATE_VERSION` | `v8.0` | Version template |
| `EXPORT_TEMPLATE_DATE` | `2025-10-03` | Date version template |
| `EXPORT_QR_BASE_URL` | `http://localhost:5173/interventions` | URL QR codes |
| `EXPORT_QR_LOGO_PATH` | `config/templates/logo.png` | Logo QR overlay |

---

## Conventions

Voir [shared-schemas.md — Conventions communes](docs/shared-schemas.md#conventions-communes) pour : authentification, pagination, formats de date, codes erreur.
