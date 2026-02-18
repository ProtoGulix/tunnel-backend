# Stock Families

Gestion des familles de stock. Les familles regroupent des sous-familles d'articles.

> **Note** : Les familles ne sont pas des entités distinctes en base. Ce sont les codes `family_code` présents dans la table `stock_sub_family`.

## Endpoints

| Méthode | Route                    | Description               |
| ------- | ------------------------ | ------------------------- |
| GET     | `/stock-families`        | Liste toutes les familles |
| GET     | `/stock-families/{code}` | Détail d'une famille      |

---

## `GET /stock-families`

Liste toutes les familles de stock avec le nombre de sous-familles associées.

### Réponse `200` — StockFamilyListItem[]

```json
[
  {
    "family_code": "OUT",
    "sub_family_count": 12
  },
  {
    "family_code": "ELE",
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

### Réponse `200` — StockFamilyDetail

```json
{
  "family_code": "OUT",
  "sub_family_count": 12,
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
- `sub_family_count` : Nombre total de sous-familles
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
  "sub_family_count": "int"
}
```

### StockFamilyDetail

```json
{
  "family_code": "string (max 20)",
  "sub_family_count": "int",
  "sub_families": ["StockSubFamily"]
}
```

### StockSubFamily

Voir [Stock Sub-Families](stock-sub-families.md) pour le schéma complet incluant le template.

---

## Notes

- **Lecture seule** : Pas d'opération de création/modification/suppression sur les familles. Elles sont gérées via les sous-familles.
- **Source de données** : Les familles sont extraites des codes `family_code` présents dans `stock_sub_family`.
- Pour gérer les sous-familles, voir [Stock Sub-Families](stock-sub-families.md).
