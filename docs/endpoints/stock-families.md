# Stock Families

Gestion des familles de stock. Les familles regroupent des sous-familles d'articles.

> **Note** : Les familles sont stockées dans la table `stock_family` (`code`, `label`). Les sous-familles référencent leur famille via `family_code`.

## Endpoints

| Méthode | Route                    | Description                       |
| ------- | ------------------------ | --------------------------------- |
| GET     | `/stock-families`        | Liste toutes les familles         |
| GET     | `/stock-families/{code}` | Détail d'une famille              |
| PATCH   | `/stock-families/{code}` | Met à jour le code et/ou le label |

---

## `GET /stock-families`

Liste toutes les familles de stock avec le nombre de sous-familles associées.

### Réponse `200` — StockFamilyListItem[]

```json
[
  {
    "family_code": "OUT",
    "label": "Outillage",
    "sub_family_count": 12
  },
  {
    "family_code": "ELE",
    "label": "Électrique",
    "sub_family_count": 8
  }
]
```

**Tri** : Par `family_code` ASC

---

## `GET /stock-families/{family_code}`

Récupère une famille par son code avec la liste de toutes ses sous-familles et leurs templates.

### Paramètres

- **family_code** (path, string, requis) : Code de la famille (ex: `OUT`, `ELE`)
- **search** (query, string, optionnel) : Filtre sur code ou label des sous-familles (recherche insensible à la casse)

### Exemples d'utilisation

- `/stock-families/OUT` : Toutes les sous-familles de la famille OUT
- `/stock-families/OUT?search=roul` : Uniquement les sous-familles contenant "roul" dans leur code ou label

### Réponse `200` — StockFamilyDetail

```json
{
  "family_code": "OUT",
  "label": "Outillage",
  "sub_family_count": 12,
  "with_template_count": 5,
  "without_template_count": 7,
  "sub_families": [
    {
      "family_code": "OUT",
      "code": "ROUL",
      "label": "Roulements",
      "template": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "code": "ROUL_STANDARD",
        "version": 1,
        "label": "Roulement standard",
        "pattern": "{DIAM_INT}x{DIAM_EXT}x{LARG}",
        "is_active": true,
        "fields": [
          {
            "id": "uuid",
            "key": "DIAM_INT",
            "label": "Diamètre intérieur",
            "field_type": "number",
            "unit": "mm",
            "required": true,
            "sort_order": 1,
            "enum_values": null
          },
          {
            "id": "uuid",
            "key": "DIAM_EXT",
            "label": "Diamètre extérieur",
            "field_type": "number",
            "unit": "mm",
            "required": true,
            "sort_order": 2,
            "enum_values": null
          }
        ]
      }
    },
    {
      "family_code": "OUT",
      "code": "VIS",
      "label": "Visserie",
      "template": null
    }
  ]
}
```

**Champs** :

- `family_code` : Code de la famille
- `sub_family_count` : Nombre total de sous-familles (après filtrage si `search` utilisé)
- `with_template_count` : Nombre de sous-familles avec template
- `without_template_count` : Nombre de sous-familles sans template
- `sub_families` : Liste complète des sous-familles avec templates
  - `family_code` : Code de la famille
  - `code` : Code de la sous-famille
  - `label` : Libellé de la sous-famille
  - `template` : Template complet avec tous ses champs et enum_values, ou `null` si pas de template

**Tri** : Sous-familles triées par `code` ASC

### Réponse `404`

Famille inexistante.

```json
{
  "detail": "Famille XXX non trouvée"
}
```

---

## Schémas

### StockFamilyListItem

```json
{
  "family_code": "string (max 20)",
  "label": "string | null",
  "sub_family_count": "int"
}
```

### StockFamilyDetail

```json
{
  "family_code": "string (max 20)",
  "label": "string | null",
  "sub_family_count": "int",
  "with_template_count": "int",
  "without_template_count": "int",
  "sub_families": ["StockSubFamily"]
}
```

### StockSubFamily

Voir [Stock Sub-Families](stock-sub-families.md) pour le schéma complet incluant le template.

---

## `PATCH /stock-families/{family_code}`

Met à jour le code et/ou le label d'une famille. Si le code change, `family_code` est mis à jour en cascade sur toutes les sous-familles.

### Entrée — `StockFamilyPatch`

```json
{
  "code": "CHAPE_NEW",
  "label": "Chappe male / Vis à œil"
}
```

| Champ   | Type   | Requis | Description                |
| ------- | ------ | ------ | -------------------------- |
| `code`  | string | oui    | Nouveau code (max 20 car.) |
| `label` | string | non    | Nouveau libellé            |

### Réponse `200` — StockFamilyDetail

La famille avec le nouveau code et toutes ses sous-familles.

### Erreurs

| Code | Cas                                       |
| ---- | ----------------------------------------- |
| 404  | Famille `{family_code}` introuvable       |
| 400  | Nouveau code déjà utilisé (contrainte DB) |

---

## Notes

- Pour gérer les sous-familles, voir [Stock Sub-Families](stock-sub-families.md).
