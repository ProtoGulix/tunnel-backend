# Stock Items

Catalogue d'articles en stock. La référence (`ref`) est auto-générée par trigger base de données.

La création d'un article fonctionne en **deux modes** selon que la sous-famille possède un template ou non :

- **Mode legacy** : saisie manuelle de la dimension
- **Mode template** : les caractéristiques sont validées et la dimension est générée automatiquement

> Voir aussi : [Stock Item Suppliers](stock-item-suppliers.md) | [Purchase Requests](purchase-requests.md) | [Stock Sub-Families](stock-sub-families.md) | [Part Templates](part-templates.md)
>
> Schema partagé : [StockItemListItem](../shared-schemas.md#stockitemlistitem)

---

## `GET /stock-items`

Liste les articles avec filtres, pagination et facettes.

### Query params

| Param             | Type   | Défaut | Description                                           |
| ----------------- | ------ | ------ | ----------------------------------------------------- |
| `skip`            | int    | 0      | Offset                                                |
| `limit`           | int    | 50     | Max par page: 1000                                    |
| `family_code`     | string | —      | Filtrer par famille                                   |
| `sub_family_code` | string | —      | Filtrer par sous-famille                              |
| `search`          | string | —      | Recherche sur nom, référence interne, référence fournisseur ou référence fabricant (ILIKE) |
| `has_supplier`    | bool   | —      | `true` = articles avec au moins un fournisseur        |
| `sort_by`         | string | `name` | Tri : `name`, `ref`, `family_code`, `sub_family_code` |

### Réponse `200`

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Roulement SKF 6205",
      "family_code": "OUT",
      "sub_family_code": "ROUL",
      "spec": "SKF",
      "dimension": "6205",
      "ref": "OUT-ROUL-SKF-6205",
      "quantity": 15,
      "unit": "pcs",
      "location": "Étagère A3",
      "supplier_refs_count": 2,
      "preferred_supplier": {
        "supplier_id": "uuid",
        "supplier_name": "PONS & SABOT",
        "supplier_ref": "P1115070",
        "unit_price": 12.5,
        "delivery_time_days": 3
      },
      "manufacturer_refs": [
        { "name": "SKF", "ref": "6205-2RS" },
        { "name": "FAG", "ref": "6205-2RS" }
      ]
    }
  ],
  "pagination": {
    "total": 150,
    "page": 1,
    "page_size": 50,
    "total_pages": 3,
    "offset": 0,
    "count": 50
  },
  "facets": {
    "families": [
      {
        "code": "OUT",
        "label": "Outillage",
        "count": 45,
        "sub_families": [
          { "code": "ROUL", "label": "Roulements", "count": 20 },
          { "code": "COUP", "label": "Coupe", "count": 25 }
        ]
      }
    ]
  }
}
```

> `preferred_supplier` est `null` si aucun fournisseur n'est marqué `is_preferred` pour cet article.
>
> `manufacturer_refs` : liste des références fabricants distinctes liées à cet article (toutes entrées `stock_item_supplier` confondues). Tableau vide si aucun fabricant référencé. Chaque entrée contient `name` (fabricant) et `ref` (référence produit), triés par nom fabricant.
>
> Les `facets` sont calculées **en une seule requête SQL** (`GROUP BY`) indépendamment de la pagination — elles reflètent toujours le catalogue complet (sans filtre actif ou avec filtre `search` appliqué).

### Métadonnées de pagination

| Champ         | Description                                    |
| ------------- | ---------------------------------------------- |
| `total`       | Nombre total d'éléments (tous filtres compris) |
| `page`        | Numéro de la page actuelle (commence à 1)      |
| `page_size`   | Nombre d'éléments par page                     |
| `total_pages` | Nombre total de pages                          |
| `offset`      | Position de début dans la liste globale        |
| `count`       | Nombre d'éléments retournés dans cette page    |

### Facettes

Les facettes permettent au front d'afficher les filtres famille/sous-famille avec leurs compteurs sans calcul supplémentaire.

| Champ                            | Description                                    |
| -------------------------------- | ---------------------------------------------- |
| `facets.families`                | Liste des familles avec compteur d'articles    |
| `facets.families[].count`        | Nombre d'articles dans cette famille           |
| `facets.families[].sub_families` | Sous-familles avec leurs compteurs individuels |

---

## `GET /stock-items/{id}`

Détail complet avec fournisseurs, template de sous-famille et caractéristiques.

### Réponse `200` — StockItemOut

```json
{
  "id": "uuid",
  "name": "Roulement à billes 6205",
  "family_code": "OUT",
  "sub_family_code": "ROUL",
  "spec": "SKF",
  "dimension": "25x52x15",
  "ref": "OUT-ROUL-SKF-25x52x15",
  "quantity": 15,
  "unit": "pcs",
  "location": "Étagère A3",
  "standars_spec": null,
  "template_id": "uuid",
  "template_version": 1,
  "supplier_refs_count": 2,
  "suppliers": [
    {
      "id": "uuid",
      "supplier_id": "uuid",
      "supplier_name": "PONS & SABOT",
      "supplier_ref": "P1115070",
      "unit_price": 12.5,
      "min_order_quantity": 5,
      "delivery_time_days": 3,
      "is_preferred": true,
      "manufacturer_item": {
        "id": "uuid",
        "manufacturer_name": "SKF",
        "manufacturer_ref": "6205-2RS"
      }
    },
    {
      "id": "uuid",
      "supplier_id": "uuid",
      "supplier_name": "ACME Industrie",
      "supplier_ref": "ACM-6205",
      "unit_price": 14.0,
      "min_order_quantity": 1,
      "delivery_time_days": 7,
      "is_preferred": false,
      "manufacturer_item": null
    }
  ],
  "sub_family_template": {
    "id": "uuid",
    "code": "ROUL_STANDARD",
    "version": 1,
    "pattern": "{DIAM_INT}x{DIAM_EXT}x{LARG}"
  },
  "characteristics": [
    {
      "field_id": "uuid",
      "key": "DIAM_INT",
      "label": "Diamètre intérieur",
      "value_text": null,
      "value_number": 25,
      "value_enum": null
    },
    {
      "field_id": "uuid",
      "key": "DIAM_EXT",
      "label": "Diamètre extérieur",
      "value_text": null,
      "value_number": 52,
      "value_enum": null
    },
    {
      "field_id": "uuid",
      "key": "LARG",
      "label": "Largeur",
      "value_text": null,
      "value_number": 15,
      "value_enum": null
    }
  ]
}
```

> `suppliers` est trié `is_preferred` DESC, nom fournisseur ASC. Tableau vide si aucun fournisseur référencé.
>
> `suppliers[].manufacturer_item` : objet fabricant complet (`id`, `manufacturer_name`, `manufacturer_ref`) si une référence fabricant est associée à cet achat fournisseur, `null` sinon. Voir [Manufacturer Items](manufacturer-items.md).
>
> `sub_family_template` est `null` pour un item legacy (sous-famille sans template associé).
>
> `characteristics` : liste des caractéristiques enregistrées pour cet article. Tableau vide pour les items legacy (`template_id = null`).

---

## `GET /stock-items/ref/{ref}`

Recherche par référence (ex: `OUT-ROUL-SKF-6205`).

---

## `POST /stock-items`

Crée un article. Le mode de création est déterminé automatiquement par le service.

### Détermination du mode

```
1. Le service charge la sous-famille (family_code + sub_family_code)
2. Si la sous-famille a un template associé → MODE TEMPLATE
3. Sinon → MODE LEGACY
```

### Mode legacy (sans template)

Pour les sous-familles **sans** template. La dimension est saisie manuellement.

```json
{
  "name": "Roulement SKF 6205",
  "family_code": "OUT",
  "sub_family_code": "ROUL",
  "dimension": "6205",
  "spec": "SKF",
  "quantity": 15,
  "unit": "pcs",
  "location": "Étagère A3"
}
```

### Mode template (avec template)

Pour les sous-familles **avec** template. Les caractéristiques sont obligatoires et la dimension est **interdite en saisie** (générée automatiquement via le `pattern` du template).

```json
{
  "name": "Roulement à billes 6205",
  "family_code": "OUT",
  "sub_family_code": "ROUL",
  "spec": "SKF",
  "quantity": 10,
  "unit": "pcs",
  "location": "Étagère A3",
  "characteristics": [
    { "key": "DIAM_INT", "value": 25 },
    { "key": "DIAM_EXT", "value": 52 },
    { "key": "LARG", "value": 15 }
  ]
}
```

> Si le template a un pattern `{DIAM_INT}x{DIAM_EXT}x{LARG}`, la dimension générée sera `25x52x15`.

### Champs d'entrée — StockItemIn

| Champ             | Type   | Requis              | Description                                                  |
| ----------------- | ------ | ------------------- | ------------------------------------------------------------ |
| `name`            | string | oui                 | Nom de l'article                                             |
| `family_code`     | string | oui                 | Code famille (max 20)                                        |
| `sub_family_code` | string | oui                 | Code sous-famille (max 20)                                   |
| `dimension`       | string | legacy uniquement   | Dimension (obligatoire en legacy, **interdit** en template)  |
| `spec`            | string | non                 | Spécification (max 50)                                       |
| `quantity`        | int    | non                 | Défaut: 0                                                    |
| `unit`            | string | non                 | Unité (max 50)                                               |
| `location`        | string | non                 | Emplacement                                                  |
| `standars_spec`   | uuid   | non                 | ID spec standard                                             |
| `characteristics` | array  | template uniquement | Caractéristiques (obligatoire en template, ignoré en legacy) |

### Format des caractéristiques (mode template)

Format simplifié : `{ "key": "...", "value": ... }`

Le service **route automatiquement** la `value` vers le bon type (`text_value`, `number_value`, `enum_value`) en se basant sur le `field_type` défini dans le template.

| `field_type` du template | Type attendu pour `value`      | Contrôle appliqué                          |
| ------------------------ | ------------------------------ | ------------------------------------------ |
| `text`                   | string                         | Doit être non vide après trim              |
| `number`                 | number (ou string convertible) | Cast en `float`, erreur si non numérique   |
| `enum`                   | string                         | Doit appartenir aux `enum_values` du champ |

Exemple avec un template ayant `DIAM` (number), `MAT` (enum), `NOTE` (text) :

```json
"characteristics": [
  { "key": "DIAM", "value": 25 },
  { "key": "MAT", "value": "INOX" },
  { "key": "NOTE", "value": "Standard" }
]
```

### Réponse `201` — StockItemOut

La réponse inclut `ref` calculée immédiatement par le trigger `BEFORE INSERT`.

```json
{
  "id": "uuid",
  "name": "Roulement SKF 6205",
  "family_code": "OUT",
  "sub_family_code": "ROUL",
  "spec": "SKF",
  "dimension": "6205",
  "ref": "OUT-ROUL-SKF-6205",
  "quantity": 15,
  "unit": "pcs",
  "location": "Étagère A3",
  "standars_spec": null,
  "template_id": null,
  "template_version": null,
  "supplier_refs_count": 0,
  "suppliers": [],
  "sub_family_template": null,
  "characteristics": []
}
```

### Règles métier

- `ref` est auto-générée par trigger `BEFORE INSERT` : `{family_code}-{sub_family_code}-{spec}-{dimension}`
- `supplier_refs_count` est géré par trigger
- **Mode legacy** :
  - `dimension` est **obligatoire**
  - `characteristics` est ignoré
  - `template_id` et `template_version` sont `NULL` en base
- **Mode template** :
  - `dimension` est **interdit** en saisie → généré via le `pattern` du template
  - `characteristics` est **obligatoire** → validé contre les champs du template
  - `template_id` et `template_version` sont enregistrés dans `stock_item`
  - Chaque caractéristique est stockée dans la table `stock_item_characteristic`
  - Les champs `required: true` du template doivent tous être présents
  - Aucun champ hors template n'est accepté

### Erreurs spécifiques

| Code  | Cas                                          | Message                                                                       |
| ----- | -------------------------------------------- | ----------------------------------------------------------------------------- |
| `400` | Dimension fournie en mode template           | `dimension ne peut pas être saisi manuellement pour les pièces avec template` |
| `400` | Caractéristiques manquantes en mode template | `Les caractéristiques sont obligatoires pour les pièces avec template`        |
| `400` | Dimension manquante en mode legacy           | `dimension est obligatoire pour les pièces legacy`                            |
| `400` | Champ obligatoire du template absent         | `Champ obligatoire manquant: {key}`                                           |
| `400` | Clé hors template                            | `Champ hors template: {key}`                                                  |
| `400` | Valeur manquante                             | `Aucune valeur fournie pour le champ: {key}`                                  |
| `400` | Texte vide                                   | `Champ {key}: la valeur texte ne peut pas être vide`                          |
| `400` | Nombre invalide                              | `Champ {key}: '{value}' n'est pas un nombre valide`                           |
| `400` | Enum invalide                                | `Valeur '{value}' invalide pour {key}. Valeurs autorisées: ...`               |

### Tables impactées

| Table                       | Mode legacy                                     | Mode template                                  |
| --------------------------- | ----------------------------------------------- | ---------------------------------------------- |
| `stock_item`                | `template_id = NULL`, `template_version = NULL` | `template_id = uuid`, `template_version = int` |
| `stock_item_characteristic` | Aucune insertion                                | 1 ligne par caractéristique                    |

---

## `PUT /stock-items/{id}`

Met à jour un article existant.

### Règles métier

- **Item legacy** : mise à jour normale. Si `family_code`, `sub_family_code`, `spec` ou `dimension` changent, `ref` est régénérée.
- **Item template** : mise à jour **restreinte**. Les champs suivants sont **immutables** :
  - `template_id`, `template_version`
  - `dimension` (générée par template)
  - `family_code`, `sub_family_code`
  - `characteristics`
- **Champs modifiables** pour un item template : `name`, `spec`, `quantity`, `unit`, `location`, `standars_spec`, `manufacturer_item_id`

### Erreur

| Code  | Cas                                                 | Message                                                                |
| ----- | --------------------------------------------------- | ---------------------------------------------------------------------- |
| `400` | Modification d'un champ immutable sur item template | `Le champ {field} ne peut pas être modifié pour un item avec template` |

---

## `PATCH /stock-items/{id}/quantity`

Mise à jour rapide de la quantité uniquement. Fonctionne pour les items legacy et template.

### Entrée

```json
{ "quantity": 20 }
```

---

## `DELETE /stock-items/{id}`

Supprime un article. Réponse `204`.
