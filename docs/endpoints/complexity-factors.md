# Complexity Factors

Facteurs de complexité attribuables aux actions d'intervention lorsque le score de complexité est > 5.

> Voir aussi : [Intervention Actions](intervention-actions.md) — champ `complexity_factor`

---

## `GET /complexity_factors`

Liste tous les facteurs, triés par catégorie puis code.

### Réponse `200`

```json
[
  {
    "code": "PCE",
    "label": "Pièce manquante ou inadaptée",
    "category": "Logistique"
  },
  {
    "code": "ACC",
    "label": "Accès difficile",
    "category": "Technique"
  },
  {
    "code": "DOC",
    "label": "Documentation manquante",
    "category": "Information"
  }
]
```

---

## `GET /complexity_factors/{code}`

Détail d'un facteur par son code (ex: `PCE`, `ACC`, `DOC`).
