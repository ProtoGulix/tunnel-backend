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

Liste les articles avec filtres.

### Query params

| Param             | Type   | Défaut | Description                        |
| ----------------- | ------ | ------ | ---------------------------------- |
| `skip`            | int    | 0      | Offset                             |
| `limit`           | int    | 100    | Max: 1000                          |
| `family_code`     | string | —      | Filtrer par famille                |
| `sub_family_code` | string | —      | Filtrer par sous-famille           |
| `search`          | string | —      | Recherche nom ou référence (ILIKE) |

### Réponse `200` — StockItemListItem

Tableau trié par nom ASC. Schema léger (voir [StockItemListItem](../shared-schemas.md#stockitemlistitem)).

---

## `GET /stock-items/{id}`

Détail complet.

### Réponse `200` — StockItemOut

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
  "supplier_refs_count": 2,
  "manufacturer_item_id": "uuid"
}
```

---

## `GET /stock-items/{id}/with-characteristics`

Récupère un article avec ses caractéristiques (si template-based).

### Réponse `200` — StockItemWithCharacteristics

```json
{
  "id": "uuid",
  "name": "Roulement à billes 6205",
  "family_code": "OUT",
  "sub_family_code": "ROUL",
  "spec": "SKF",
  "dimension": "25x52x15",
  "ref": "OUT-ROUL-SKF-25x52x15",
  "quantity": 10,
  "unit": "pcs",
  "location": "Étagère A3",
  "template_id": "uuid",
  "template_version": 1,
  "characteristics": [
    {
      "field_id": "uuid",
      "key": "DIAM_INT",
      "value_text": null,
      "value_number": 25,
      "value_enum": null
    },
    {
      "field_id": "uuid",
      "key": "DIAM_EXT",
      "value_text": null,
      "value_number": 52,
      "value_enum": null
    },
    {
      "field_id": "uuid",
      "key": "LARG",
      "value_text": null,
      "value_number": 15,
      "value_enum": null
    }
  ]
}
```

> Pour un item legacy (`template_id = null`), `characteristics` est un tableau vide.

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

| Champ                  | Type   | Requis              | Description                                                  |
| ---------------------- | ------ | ------------------- | ------------------------------------------------------------ |
| `name`                 | string | oui                 | Nom de l'article                                             |
| `family_code`          | string | oui                 | Code famille (max 20)                                        |
| `sub_family_code`      | string | oui                 | Code sous-famille (max 20)                                   |
| `dimension`            | string | legacy uniquement   | Dimension (obligatoire en legacy, **interdit** en template)  |
| `spec`                 | string | non                 | Spécification (max 50)                                       |
| `quantity`             | int    | non                 | Défaut: 0                                                    |
| `unit`                 | string | non                 | Unité (max 50)                                               |
| `location`             | string | non                 | Emplacement                                                  |
| `standars_spec`        | uuid   | non                 | ID spec standard                                             |
| `manufacturer_item_id` | uuid   | non                 | Article fabricant lié                                        |
| `characteristics`      | array  | template uniquement | Caractéristiques (obligatoire en template, ignoré en legacy) |

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
  "supplier_refs_count": 0,
  "manufacturer_item_id": null
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
