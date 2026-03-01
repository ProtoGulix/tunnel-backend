# Changelog

---

## [2.6.0] — 2026-03-01

### Stock Items — `GET /stock-items`

- Ajout du paramètre `has_supplier` (bool) : filtre les articles avec (`true`) ou sans (`false`) fournisseur référencé
- Ajout du paramètre `sort_by` : tri configurable (`name`, `ref`, `family_code`, `sub_family_code`)
- Ajout du champ `preferred_supplier` dans chaque item de la liste — fournisseur préféré embarqué (`null` si aucun), évite un appel supplémentaire
- Ajout de la clé `facets.families[]` dans la réponse : compteurs famille/sous-famille calculés en une seule requête SQL, indépendamment de la pagination

### Stock Items — `GET /stock-items/{id}`

- Ajout du tableau `suppliers[]` : fournisseurs complets embarqués, triés `is_preferred` DESC — évite l'appel `/stock-item-suppliers/stock-item/{id}`
- Ajout du champ `sub_family_template` : template de la sous-famille embarqué (`null` pour item legacy)
- `suppliers[].manufacturer_item_id` : référence fabricant telle que référencée par ce fournisseur

### Stock Items — modèle de données

- **Suppression** de `manufacturer_item_id` sur `stock_item` — la référence fabricant appartient uniquement à `stock_item_supplier` (combinaison fournisseur + article)

### Stock Item Suppliers

- Ajout du `PUT /stock-item-suppliers/{id}` documenté avec champs modifiables et immutables (`stock_item_id`, `supplier_id` non modifiables après création)
- Correction : `DELETE /stock-item-suppliers/{id}` retourne désormais `204` (doublon supprimé)
- Clarification de `manufacturer_item_id` : référence fabricant telle que référencée par ce fournisseur, peut différer selon le canal d'achat

### Purchase Requests — dispatch

- **Nouvelle règle métier** sur `POST /purchase-requests/dispatch` :
  - **Mode direct** : si un fournisseur `is_preferred = true` existe, dispatch uniquement vers lui
  - **Mode consultation** : si aucun préféré, dispatch vers tous les fournisseurs référencés (1 commande par fournisseur)
  - **Erreur** : aucun fournisseur référencé → demande remontée dans `errors[]`
  - **Invariant** : une demande déjà liée à une `supplier_order_line` est ignorée (anti-doublon)
- Réponse enrichie avec `details[]` : mode (`direct`/`consultation`) et commandes créées par demande

### Purchase Requests — création

- Règle explicite : `stock_item_id = null` → statut initial `TO_QUALIFY`, non dispatchable tant qu'un article du catalogue n'est pas associé

---

## [2.5.0] — précédent

- Mise à jour endpoint stock families avec filtrage par search et compteurs
- Voir commits git pour détail
