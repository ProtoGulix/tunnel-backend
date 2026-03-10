# Purchase Requests

Demandes d'achat de matériel, liées aux interventions et aux commandes fournisseurs. Le statut est **calculé automatiquement** ([DerivedStatus](../shared-schemas.md#derivedstatus)).

> Voir aussi : [Interventions](interventions.md) | [Stock Items](stock-items.md) | [Supplier Orders](supplier-orders.md) | [Supplier Order Lines](supplier-order-lines.md)

---

## `GET /purchase-requests`

Liste toutes les demandes d'achat avec filtres. Alias de `/list`.

### Query params

| Param             | Type   | Défaut | Description                  |
| ----------------- | ------ | ------ | ---------------------------- |
| `skip`            | int    | 0      | Offset                       |
| `limit`           | int    | 100    | Max: 1000                    |
| `status`          | string | —      | Filtrer par statut dérivé    |
| `intervention_id` | uuid   | —      | Filtrer par intervention     |
| `urgency`         | string | —      | `normal`, `high`, `critical` |

### Réponse `200` — `List[PurchaseRequestListItem]`

Même structure que `GET /purchase-requests/list`.

---

## `GET /purchase-requests/statuses`

Retourne tous les statuts dérivés possibles avec leur label et couleur. Utile pour construire des filtres et légendes côté frontend sans hardcoder les valeurs.

### Réponse `200`

```json
[
  { "code": "TO_QUALIFY", "label": "À qualifier", "color": "#F59E0B" },
  {
    "code": "NO_SUPPLIER_REF",
    "label": "Sans fournisseur",
    "color": "#F97316"
  },
  { "code": "PENDING_DISPATCH", "label": "À dispatcher", "color": "#A855F7" },
  { "code": "OPEN", "label": "Mutualisation", "color": "#6B7280" },
  { "code": "CONSULTATION", "label": "En chiffrage", "color": "#0EA5E9" },
  { "code": "QUOTED", "label": "Devis reçu", "color": "#FFA500" },
  { "code": "ORDERED", "label": "Commandé", "color": "#3B82F6" },
  { "code": "PARTIAL", "label": "Partiellement reçu", "color": "#8B5CF6" },
  { "code": "RECEIVED", "label": "Reçu", "color": "#10B981" },
  { "code": "REJECTED", "label": "Refusé", "color": "#EF4444" }
]
```

> Source : `api/constants.py` — `DERIVED_STATUS_CONFIG`. Toute modification des labels/couleurs se répercute automatiquement.

---

## Statuts dérivés (`derived_status`)

Le statut d'une demande d'achat est **calculé dynamiquement** à chaque lecture, jamais stocké en base. Il dépend de la présence d'un article stock, des références fournisseurs et de l'avancement des lignes de commande.

| Code               | Label                 | Condition                                                                                       |
| ------------------ | --------------------- | ----------------------------------------------------------------------------------------------- |
| `TO_QUALIFY`       | À qualifier           | `stock_item_id` est null                                                                        |
| `NO_SUPPLIER_REF`  | Sans réf. fournisseur | Article ok, aucun fournisseur référencé                                                         |
| `PENDING_DISPATCH` | À dispatcher          | Réf. fournisseur ok, aucune ligne de commande                                                   |
| `OPEN`             | Mutualisation         | Dans un panier ouvert (`OPEN`), pas de devis                                                    |
| `CONSULTATION`     | En chiffrage          | Panier verrouillé (`SENT`/`ACK`), sans devis ni sélection                                       |
| `QUOTED`           | Devis reçu            | Au moins un devis reçu (`quote_received = true`)                                                |
| `ORDERED`          | Commandé              | Au moins une ligne sélectionnée (`is_selected = true`)                                          |
| `PARTIAL`          | Partiellement reçu    | Livraison partielle                                                                             |
| `RECEIVED`         | Reçu                  | Livraison complète                                                                              |
| `REJECTED`         | Refusé                | Toutes les lignes dans un panier `CANCELLED`/`CLOSED` sans aucune sélection                     |
| `RECEIVED`         | Reçu                  | Toutes les lignes dans un panier terminal (`CLOSED`/`CANCELLED`) avec au moins une sélectionnée |

> **`CONSULTATION`** : Le panier est verrouillé (`SENT` ou `ACK`, devis envoyé au fournisseur) mais aucun devis n'a encore été renseigné. En attente de retour fournisseur. Progresse vers `QUOTED` dès qu'un devis est saisi (`quote_received = true`).

> **`REJECTED`** : Statut calculé automatiquement. Se déclenche quand toutes les lignes de commande liées à la DA appartiennent à des paniers terminaux (`CANCELLED` ou `CLOSED`) et qu'aucune n'a été sélectionnée (`is_selected = false`). Cela couvre aussi le cas des **lignes jumelles** (mode consultation, plusieurs fournisseurs) où aucune offre n'a été retenue.

> Pour filtrer par statut : `GET /purchase-requests/list?status=PENDING_DISPATCH` ou l'endpoint dédié `GET /purchase-requests/status/PENDING_DISPATCH`.

---

## `GET /purchase-requests/list` [v1.2.0]

Liste optimisée légère pour tableaux. Payload ~95% plus léger.

### Réponse `200` — PurchaseRequestListItem

```json
[
  {
    "id": "uuid",
    "item_label": "Roulement SKF 6205",
    "quantity": 2,
    "unit": "pcs",
    "derived_status": {
      "code": "PENDING_DISPATCH",
      "label": "À dispatcher",
      "color": "#f59e0b"
    },
    "stock_item_id": "uuid",
    "stock_item_ref": "OUT-ROUL-SKF-6205",
    "stock_item_name": "Roulement SKF 6205",
    "intervention_code": "CN001-REA-20260113-QC",
    "requester_name": "Jean Dupont",
    "urgency": "high",
    "urgent": true,
    "quotes_count": 0,
    "selected_count": 0,
    "suppliers_count": 2,
    "created_at": "2026-01-13T10:00:00",
    "updated_at": "2026-01-13T10:00:00"
  }
]
```

---

## `GET /purchase-requests/detail/{id}` [v1.2.0]

Détail complet avec contexte enrichi : intervention + machine, stock item avec compteur fournisseurs, order lines avec fournisseur hydraté.

### Réponse `200` — PurchaseRequestDetail

```json
{
  "id": "37eb5da0-220b-4813-a205-36c1da1d02be",
  "item_label": "Roulement SKF 6205",
  "quantity": 2,
  "unit": "pcs",
  "derived_status": {
    "code": "QUOTED",
    "label": "Devis reçu",
    "color": "#FFA500"
  },
  "is_editable": false,

  "stock_item": {
    "id": "uuid",
    "name": "Roulement SKF 6205",
    "ref": "OUT-ROUL-SKF-6205",
    "family_code": "ROUL",
    "sub_family_code": "BILLE",
    "quantity": 5,
    "unit": "pcs",
    "location": "Étagère A3",
    "supplier_refs_count": 2
  },

  "intervention": {
    "id": "uuid",
    "code": "CN001-REA-20260113-QC",
    "title": "Remplacement roulement convoyeur",
    "priority": "urgent",
    "status_actual": "en_cours",
    "equipement": {
      "id": "uuid",
      "code": "CONV-01",
      "name": "Convoyeur principal"
    }
  },

  "order_lines": [
    {
      "id": "uuid",
      "supplier_order_line_id": "uuid",
      "quantity_allocated": 2,
      "created_at": "2026-01-14T08:00:00",
      "supplier_order_id": "uuid",
      "supplier_order_status": "OPEN",
      "supplier_order_number": "CMD-2026-0042",
      "unit_price": 12.5,
      "total_price": 25.0,
      "quantity_received": 0,
      "is_selected": false,
      "quote_received": true,
      "quote_price": 12.5,
      "quote_received_at": "2026-01-15T10:30:00",
      "manufacturer": "SKF",
      "manufacturer_ref": "6205-2RS",
      "lead_time_days": 5,
      "notes": null,
      "supplier": {
        "id": "uuid",
        "name": "PONS & SABOT",
        "code": "PS",
        "contact_name": "Marc Pons",
        "email": "marc@pons-sabot.fr",
        "phone": "04 91 00 00 00"
      }
    }
  ],

  "requested_by": "uuid-user",
  "requester_name": "Jean Dupont",
  "approver_name": null,
  "approved_at": null,
  "urgency": "high",
  "urgent": true,
  "reason": "Remplacement urgent suite panne",
  "notes": null,
  "workshop": "Atelier 1",
  "quantity_requested": 2,
  "quantity_approved": null,
  "created_at": "2026-01-13T10:00:00",
  "updated_at": "2026-01-15T10:30:00"
}
```

| Champ                             | Description                                                                                              |
| --------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `is_editable`                     | `true` si la DA peut encore être modifiée (statut `TO_QUALIFY`, `NO_SUPPLIER_REF` ou `PENDING_DISPATCH`) |
| `stock_item.supplier_refs_count`  | Nombre de fournisseurs référencés pour cet article                                                       |
| `intervention.equipement`         | Machine liée à l'intervention (`null` si aucune)                                                         |
| `order_lines[].supplier`          | Fournisseur complet hydraté depuis `supplier_order`                                                      |
| `order_lines[].quote_received`    | `true` si devis reçu pour cette ligne                                                                    |
| `order_lines[].is_selected`       | `true` si ligne retenue pour commande ferme                                                              |
| `order_lines[].quantity_received` | Quantité livrée (0 = pas encore reçu)                                                                    |

### Erreurs

| Code | Cas                    |
| ---- | ---------------------- |
| 404  | Demande introuvable    |
| 500  | Erreur base de données |

---

## `GET /purchase-requests/stats` [v1.2.0]

Statistiques agrégées pour dashboards.

### Query params

| Param        | Type   | Description               |
| ------------ | ------ | ------------------------- |
| `start_date` | date   | Début (défaut: 3 mois)    |
| `end_date`   | date   | Fin (défaut: aujourd'hui) |
| `group_by`   | string | Regroupement              |

### Réponse `200`

```json
{
  "period": { "start_date": "2025-11-15", "end_date": "2026-02-15" },
  "totals": { "total_requests": 45, "urgent_count": 8 },
  "by_status": [
    {
      "status": "PENDING_DISPATCH",
      "count": 12,
      "label": "À dispatcher",
      "color": "#f59e0b"
    }
  ],
  "by_urgency": [
    { "urgency": "normal", "count": 30 },
    { "urgency": "high", "count": 8 }
  ],
  "top_items": [
    {
      "item_label": "Roulement SKF 6205",
      "stock_item_ref": "OUT-ROUL-SKF-6205",
      "request_count": 5,
      "total_quantity": 12
    }
  ]
}
```

---

## `GET /purchase-requests/{id}`

Détail d'une demande par ID. Alias de `/detail/{id}`.

### Réponse `200` — `PurchaseRequestDetail`

Même structure que `GET /purchase-requests/detail/{id}`.

---

## `GET /purchase-requests/status/{status}`

Liste les demandes filtrées par statut dérivé. Raccourci sémantique vers `GET /purchase-requests/list?status={status}`.

### Path param

| Param    | Valeurs acceptées                                                                                                                            |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `status` | `TO_QUALIFY` · `NO_SUPPLIER_REF` · `PENDING_DISPATCH` · `OPEN` · `CONSULTATION` · `QUOTED` · `ORDERED` · `PARTIAL` · `RECEIVED` · `REJECTED` |

### Query params

| Param     | Type   | Défaut | Description                  |
| --------- | ------ | ------ | ---------------------------- |
| `skip`    | int    | 0      | Offset                       |
| `limit`   | int    | 100    | Max: 1000                    |
| `urgency` | string | —      | `normal`, `high`, `critical` |

### Réponse `200` — `List[PurchaseRequestListItem]`

Même structure que `GET /purchase-requests/list`.

### Erreurs

| Code | Cas            |
| ---- | -------------- |
| 400  | Statut inconnu |

---

## `GET /purchase-requests/intervention/{intervention_id}`

Demandes liées à une intervention. Alias de `/intervention/{id}/optimized?view=list`.

### Réponse `200` — `List[PurchaseRequestListItem]`

Même structure que `GET /purchase-requests/list`.

---

## `GET /purchase-requests/intervention/{intervention_id}/optimized`

Filtre par intervention avec choix de granularité.

### Query params

| Param  | Type   | Description                                                      |
| ------ | ------ | ---------------------------------------------------------------- |
| `view` | string | `list` (léger, défaut) ou `full` (complet avec contexte enrichi) |

---

## `POST /purchase-requests`

Crée une demande d'achat.

### Entrée

```json
{
  "item_label": "Roulement SKF 6205",
  "quantity": 2,
  "stock_item_id": "uuid",
  "unit": "pcs",
  "requested_by": "Jean Dupont",
  "urgency": "high",
  "reason": "Remplacement urgent",
  "notes": null,
  "workshop": "Atelier 1",
  "intervention_id": "uuid",
  "quantity_requested": 2,
  "urgent": true,
  "requester_name": "Jean Dupont"
}
```

| Champ             | Type   | Requis | Description              |
| ----------------- | ------ | ------ | ------------------------ |
| `item_label`      | string | oui    | Libellé de l'article     |
| `quantity`        | int    | oui    | Quantité (> 0)           |
| `stock_item_id`   | uuid   | non    | Article stock normalisé  |
| `unit`            | string | non    | Unité (pcs, m, kg, etc.) |
| `intervention_id` | uuid   | non    | Intervention liée        |
| `urgent`          | bool   | non    | Défaut: false            |
| `requester_name`  | string | non    | Nom du demandeur         |

### Règles métier

- `item_label` et `quantity` sont requis
- `quantity` doit être > 0
- `derived_status` est calculé automatiquement (voir [DerivedStatus](../shared-schemas.md#derivedstatus))
- Si `stock_item_id` est `null`, le statut initial est `TO_QUALIFY` — la demande ne peut pas être dispatchée tant qu'un article du catalogue n'est pas associé

### Réponse `201` — `PurchaseRequestDetail`

Retourne le détail complet de la demande créée (même structure que `GET /detail/{id}`).

---

## `PUT /purchase-requests/{id}`

Met à jour une demande. Champs supplémentaires modifiables : `quantity_approved`, `approver_name`, `approved_at`.

> `status` n'est plus modifiable manuellement.

### Garde métier

La modification est refusée si la DA n'est plus dans un état éditable. Seuls les statuts suivants permettent la mise à jour :

| Statut autorisé    | Label                 |
| ------------------ | --------------------- |
| `TO_QUALIFY`       | À qualifier           |
| `NO_SUPPLIER_REF`  | Sans réf. fournisseur |
| `PENDING_DISPATCH` | À dispatcher          |

### Réponse `200` — `PurchaseRequestDetail`

Retourne le détail complet de la demande mise à jour.

### Erreurs

| Code | Cas                                                                         |
| ---- | --------------------------------------------------------------------------- |
| 404  | Demande introuvable                                                         |
| 422  | DA non modifiable — statut hors plage éditable (ex : `ORDERED`, `RECEIVED`) |

---

## `DELETE /purchase-requests/{id}`

Supprime une demande. Réponse `204`.

---

## `POST /purchase-requests/dispatch` [v1.2.12]

Dispatch automatique des demandes `PENDING_DISPATCH` vers des [Supplier Orders](supplier-orders.md).

### Règles métier

Pour chaque demande `PENDING_DISPATCH` avec un `stock_item_id` :

**Cas 1 — Fournisseur préféré défini (`is_preferred = true`)**

1. Un seul fournisseur ciblé : le préféré
2. Trouve ou crée un `supplier_order` OPEN pour ce fournisseur
3. Crée une `supplier_order_line` liée à cette commande
4. `supplier_ref_snapshot` est renseigné depuis `supplier_ref` du fournisseur préféré

**Cas 2 — Aucun fournisseur préféré (mode consultation)**

1. Tous les fournisseurs référencés sont ciblés
2. Trouve ou crée un `supplier_order` OPEN **par fournisseur**
3. Crée une `supplier_order_line` par commande (1 fournisseur = 1 commande = 1 ligne)
4. Le gestionnaire choisit ensuite la meilleure offre via `is_selected` sur les lignes

**Cas 3 — Aucun fournisseur référencé**

- La demande est ignorée et remontée dans `errors[]`

> **Invariant** : une même `purchase_request` n'est jamais dispatchée deux fois. Si elle est déjà liée à une `supplier_order_line`, elle est ignorée.

### Réponse `200`

```json
{
  "dispatched_count": 5,
  "created_orders": 2,
  "errors": [
    { "purchase_request_id": "uuid", "error": "Aucun fournisseur référencé" }
  ],
  "details": [
    {
      "purchase_request_id": "uuid",
      "mode": "direct",
      "supplier_order_id": "uuid",
      "supplier_name": "PONS & SABOT"
    },
    {
      "purchase_request_id": "uuid",
      "mode": "consultation",
      "supplier_orders": [
        { "supplier_order_id": "uuid", "supplier_name": "PONS & SABOT" },
        { "supplier_order_id": "uuid", "supplier_name": "ACME Industrie" }
      ]
    }
  ]
}
```

| Champ              | Description                                                              |
| ------------------ | ------------------------------------------------------------------------ |
| `dispatched_count` | Nombre de demandes dispatchées avec succès                               |
| `created_orders`   | Nombre de nouvelles `supplier_order` créées                              |
| `errors`           | Demandes non dispatchées avec raison                                     |
| `details[].mode`   | `direct` (fournisseur préféré) ou `consultation` (tous les fournisseurs) |
