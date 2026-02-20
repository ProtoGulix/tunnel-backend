# Schemas partagés

Schemas réutilisés dans plusieurs endpoints. Référencés par lien depuis les docs d'endpoints.

---

## PaginatedResponse

Réponse standard pour les endpoints paginés.

```json
{
  "items": [...],
  "pagination": {
    "total": 150,
    "page": 1,
    "page_size": 50,
    "total_pages": 3,
    "offset": 0,
    "count": 50
  }
}
```

### Structure

- `items` : Liste des éléments de la page (type variable selon l'endpoint)
- `pagination` : Métadonnées de pagination

### Métadonnées de pagination

| Champ         | Type | Description                                    |
| ------------- | ---- | ---------------------------------------------- |
| `total`       | int  | Nombre total d'éléments (tous filtres compris) |
| `page`        | int  | Numéro de la page actuelle (commence à 1)      |
| `page_size`   | int  | Nombre d'éléments par page                     |
| `total_pages` | int  | Nombre total de pages                          |
| `offset`      | int  | Position de début dans la liste globale        |
| `count`       | int  | Nombre d'éléments retournés dans cette page    |

### Calcul de la page

```
page = (offset / page_size) + 1
```

Exemple : avec `offset=50` et `page_size=50`, on est à la page 2.

---

## EquipementHealth

Indicateur de santé calculé automatiquement selon les interventions ouvertes.

| Règle                      | Niveau        |
| -------------------------- | ------------- |
| Intervention urgente >= 1  | `critical`    |
| Interventions ouvertes > 5 | `warning`     |
| Interventions ouvertes > 0 | `maintenance` |
| Aucune intervention        | `ok`          |

```json
{
  "level": "ok|maintenance|warning|critical",
  "reason": "string",
  "rules_triggered": ["string"]
}
```

> `rules_triggered` est inclus uniquement dans le détail (`GET /equipements/{id}`), pas dans les listes.

---

## EquipementClass

Classification hiérarchique des équipements (SCIE, EXTRUDEUSE, etc.).

```json
{
  "id": "uuid",
  "code": "string",
  "label": "string"
}
```

> Peut être `null` si aucune classe assignée à l'équipement.

---

## DerivedStatus

Statut calculé automatiquement pour les demandes d'achat, basé sur l'avancement.

| Code               | Condition                            | Label                 |
| ------------------ | ------------------------------------ | --------------------- |
| `TO_QUALIFY`       | `stock_item_id` is null              | À qualifier           |
| `NO_SUPPLIER_REF`  | Stock ok, aucune réf. fournisseur    | Sans réf. fournisseur |
| `PENDING_DISPATCH` | Réf. fournisseur ok, pas de commande | À dispatcher          |
| `OPEN`             | Dans un supplier order, pas de devis | En attente            |
| `QUOTED`           | Au moins un devis reçu               | Devis reçu            |
| `ORDERED`          | Au moins une ligne sélectionnée      | Commandé              |
| `PARTIAL`          | Livraison partielle                  | Partiellement reçu    |
| `RECEIVED`         | Livraison complète                   | Reçu                  |
| `REJECTED`         | Annulée                              | Refusé                |

```json
{
  "code": "TO_QUALIFY|NO_SUPPLIER_REF|PENDING_DISPATCH|OPEN|QUOTED|ORDERED|PARTIAL|RECEIVED|REJECTED",
  "label": "string",
  "color": "string (hex)"
}
```

---

## InterventionInfo

Objet intervention léger, embarqué dans d'autres réponses (purchase requests, etc.).

```json
{
  "id": "uuid",
  "code": "string|null",
  "title": "string",
  "priority": "string|null",
  "status_actual": "string|null",
  "equipement": {
    "id": "uuid",
    "code": "string|null",
    "name": "string"
  }
}
```

---

## StockItemListItem

Schema léger pour articles en stock, embarqué dans les réponses enrichies.

```json
{
  "id": "uuid",
  "name": "string",
  "ref": "string|null",
  "family_code": "string",
  "sub_family_code": "string",
  "quantity": "int|null",
  "unit": "string|null",
  "location": "string|null"
}
```

---

## LinkedOrderLine

Ligne de commande liée à une demande d'achat, embarquée dans `PurchaseRequestOut`.

Champs utilisés pour le calcul du [DerivedStatus](#derivedstatus) :

- `quote_received` : devis reçu
- `is_selected` : ligne sélectionnée pour commande
- `supplier_order_status` : statut de la commande parent

```json
{
  "id": "uuid",
  "supplier_order_line_id": "uuid",
  "quantity_allocated": "int",
  "supplier_order_id": "uuid",
  "supplier_order_status": "string|null",
  "supplier_order_number": "string|null",
  "stock_item_id": "uuid",
  "stock_item_name": "string|null",
  "stock_item_ref": "string|null",
  "quantity": "int",
  "unit_price": "float|null",
  "total_price": "float|null",
  "quote_received": "boolean|null",
  "quote_price": "float|null",
  "quantity_received": "int|null",
  "is_selected": "boolean|null",
  "created_at": "datetime|null"
}
```

---

## LinkedPurchaseRequest

Demande d'achat liée à une ligne de commande, embarquée dans `SupplierOrderLineOut`.

```json
{
  "id": "uuid",
  "purchase_request_id": "uuid",
  "quantity": "int",
  "item_label": "string|null",
  "requester_name": "string|null",
  "intervention_id": "uuid|null",
  "created_at": "datetime|null"
}
```

---

## Conventions communes

### Authentification

Tous les endpoints nécessitent un JWT Bearer token sauf mention contraire (`Public`).

Si `AUTH_DISABLED=true` dans `.env`, l'authentification est désactivée (mode développement).

### Pagination

Tous les endpoints de liste supportent :

- `skip` (default: 0)
- `limit` (default: 100, max: 1000)

### Dates

Formats acceptés :

- `YYYY-MM-DD` (date seule)
- `YYYY-MM-DDTHH:MM:SS` (datetime)
- `YYYY-MM-DDTHH:MM:SS.microZ` (avec timezone)

Les dates invalides (ex: `2026-01-36`) sont rejetées.

### Erreurs

| Code | Signification                                         |
| ---- | ----------------------------------------------------- |
| 400  | Validation échouée (format UUID, champs requis, etc.) |
| 401  | JWT manquant ou invalide                              |
| 404  | Ressource non trouvée                                 |
| 409  | Conflit (contrainte d'unicité, suppression bloquée)   |
| 500  | Erreur serveur                                        |
