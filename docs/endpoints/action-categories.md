# Action Categories & Subcategories

Tables de référence pour la classification des actions d'intervention.

> Voir aussi : [Intervention Actions](intervention-actions.md)

---

## `GET /action_categories`

Liste toutes les catégories d'actions.

### Réponse `200`

```json
[
  {
    "id": 3,
    "name": "Dépannage",
    "code": "DEP",
    "color": "#e53e3e"
  }
]
```

---

## `GET /action_categories/{id}`

Détail d'une catégorie.

---

## `GET /action_categories/{id}/subcategories`

Liste les sous-catégories d'une catégorie.

### Réponse `200`

```json
[
  {
    "id": 30,
    "category_id": 3,
    "name": "Remplacement pièce",
    "code": "DEP_REM"
  }
]
```

---

## `GET /action_subcategories`

Liste toutes les sous-catégories.

---

## `GET /action_subcategories/{id}`

Détail d'une sous-catégorie.
