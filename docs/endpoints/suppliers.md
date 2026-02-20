# Suppliers

Gestion du répertoire fournisseurs.

> Voir aussi : [Stock Item Suppliers](stock-item-suppliers.md) | [Supplier Orders](supplier-orders.md)

---

## `GET /suppliers`

Liste les fournisseurs avec filtres.

### Query params

| Param       | Type   | Défaut | Description                            |
| ----------- | ------ | ------ | -------------------------------------- |
| `skip`      | int    | 0      | Offset                                 |
| `limit`     | int    | 100    | Max: 1000                              |
| `is_active` | bool   | —      | Filtrer par statut actif               |
| `search`    | string | —      | Recherche nom, code ou contact (ILIKE) |

### Réponse `200` — SupplierListItem

```json
[
  {
    "id": "uuid",
    "name": "PONS & SABOT",
    "code": "PS",
    "contact_name": "M. Martin",
    "email": "commandes@pons.fr",
    "phone": "01 23 45 67 89",
    "is_active": true
  }
]
```

Trié par nom ASC.

---

## `GET /suppliers/{id}`

Détail complet.

### Réponse `200` — SupplierOut

```json
{
  "id": "uuid",
  "name": "PONS & SABOT",
  "code": "PS",
  "contact_name": "M. Martin",
  "email": "commandes@pons.fr",
  "phone": "01 23 45 67 89",
  "address": "12 rue de l'Industrie, 69001 Lyon",
  "notes": "Délai moyen 5 jours",
  "is_active": true,
  "created_at": "2026-01-01T00:00:00",
  "updated_at": "2026-02-10T09:00:00"
}
```

---

## `GET /suppliers/code/{code}`

Recherche par code (ex: `PS`).

---

## `POST /suppliers`

Crée un fournisseur.

### Entrée

```json
{
  "name": "PONS & SABOT",
  "code": "PS",
  "contact_name": "M. Martin",
  "email": "commandes@pons.fr",
  "phone": "01 23 45 67 89",
  "address": "12 rue de l'Industrie, 69001 Lyon",
  "notes": null,
  "is_active": true
}
```

| Champ  | Type   | Requis | Description                           |
| ------ | ------ | ------ | ------------------------------------- |
| `name` | string | oui    | Nom du fournisseur (min 2 caractères) |
| `code` | string | non    | Code court                            |
| Autres | —      | non    | Contact, coordonnées, notes           |

### Règles métier

- `name` doit contenir **au moins 2 caractères** (après trim)
- Le nom doit être **unique** (pas de doublon)
- `updated_at` est mis à jour automatiquement par trigger

### Erreurs

| Code  | Cas             | Message                                      |
| ----- | --------------- | -------------------------------------------- |
| `400` | Nom < 2 chars   | `Le nom doit contenir au moins 2 caractères` |
| `400` | Nom existe déjà | `Le fournisseur '{name}' existe déjà`        |

---

## `DELETE /suppliers/{id}`

Supprime un fournisseur.

### Règle métier

- **Protection des références** : Un fournisseur ne peut être supprimé que s'il n'a **aucune référence** dans `stock_item_supplier`
- Si des références existent, elles doivent être supprimées d'abord

### Erreurs

| Code  | Cas                     | Message                                                               |
| ----- | ----------------------- | --------------------------------------------------------------------- |
| `404` | Fournisseur introuvable | `Fournisseur {id} non trouvé`                                         |
| `400` | Possède références      | `Ce fournisseur possède {count} référence(s). Supprimez-les d'abord.` |

### Réponse `200`

```json
{
  "message": "Fournisseur {id} supprimé"
}
```

Met à jour. Même body, tous champs optionnels.

---

## `DELETE /suppliers/{id}`

Supprime. Réponse `204`.
