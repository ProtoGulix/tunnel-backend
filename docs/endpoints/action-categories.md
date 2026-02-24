# Action Categories & Subcategories

Tables de référence pour la classification des actions d'intervention.

> Voir aussi : [Intervention Actions](intervention-actions.md)

---

## `GET /action-categories`

Liste toutes les catégories d'actions avec leurs sous-catégories imbriquées.

### Réponse `200`

```json
[
  {
    "id": 3,
    "name": "Dépannage",
    "code": "DEP",
    "color": "#e53e3e",
    "subcategories": [
      {
        "id": 30,
        "category_id": 3,
        "name": "Remplacement pièce",
        "code": "DEP_REM"
      },
      {
        "id": 31,
        "category_id": 3,
        "name": "Réparation",
        "code": "DEP_REP"
      }
    ]
  }
]
```

---

## `GET /action-categories/{id}`

Détail d'une catégorie.

---

## `GET /action-categories/{id}/subcategories`

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

## `GET /action-subcategories`

Liste toutes les sous-catégories avec leur catégorie imbriquée.

### Réponse `200`

```json
[
  {
    "id": 30,
    "category_id": 3,
    "name": "Remplacement pièce",
    "code": "DEP_REM",
    "category": {
      "id": 3,
      "name": "Dépannage",
      "code": "DEP",
      "color": "#e53e3e"
    }
  }
]
```

---

## `GET /action-subcategories/{id}`

Détail d'une sous-catégorie.
