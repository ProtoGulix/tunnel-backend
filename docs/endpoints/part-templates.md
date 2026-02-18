# Templates de pièces

> Endpoints de gestion des templates versionnés pour la caractérisation des pièces (DB v1.4.0)

Les templates définissent la structure des caractéristiques techniques des pièces. Chaque template est versionné pour permettre l'évolution sans casser les pièces existantes.

---

## GET /part-templates

Liste tous les templates (dernière version de chaque) avec leurs champs.

**Retour :** Liste complète avec fields (optimisé pour pages de gestion).

### Réponse

```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "code": "VIS_STANDARD",
    "version": 2,
    "label": "Vis standard",
    "pattern": "{DIAM}x{LONG}-{MAT}-{TETE}",
    "is_active": true,
    "fields": [
      {
        "key": "DIAM",
        "label": "Diamètre",
        "field_type": "number",
        "unit": "mm",
        "required": true,
        "sort_order": 1,
        "enum_values": null
      },
      {
        "key": "LONG",
        "label": "Longueur",
        "field_type": "number",
        "unit": "mm",
        "required": true,
        "sort_order": 2,
        "enum_values": null
      },
      {
        "key": "MAT",
        "label": "Matériau",
        "field_type": "enum",
        "unit": null,
        "required": true,
        "sort_order": 3,
        "enum_values": [
          { "value": "INOX", "label": "Inox A2" },
          { "value": "ACIER", "label": "Acier zingué" }
        ]
      }
    ]
  },
  {
    "id": "223e4567-e89b-12d3-a456-426614174001",
    "code": "ECROU_HEXAGONAL",
    "version": 1,
    "label": "Écrou hexagonal",
    "pattern": "M{DIAM}-{MAT}",
    "is_active": true,
    "fields": [
      {
        "key": "DIAM",
        "label": "Diamètre",
        "field_type": "number",
        "unit": "mm",
        "required": true,
        "sort_order": 1,
        "enum_values": null
      }
    ]
  }
]
```

---

## GET /part-templates/code/{code}

Récupère toutes les versions d'un template par son code.

**Paramètres :**

- `code` (path) : Code du template

### Exemple

```bash
GET /part-templates/code/VIS_STANDARD
```

### Réponse

```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "code": "VIS_STANDARD",
    "version": 2,
    "pattern": "{DIAM}x{LONG}-{MAT}-{TETE}"
  },
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "code": "VIS_STANDARD",
    "version": 1,
    "pattern": "{DIAM}x{LONG}-{MAT}"
  }
]
```

---

## GET /part-templates/{template_id}

Récupère un template complet avec tous ses champs et valeurs enum.

**Paramètres :**

- `template_id` (path) : UUID du template
- `version` (query, optionnel) : Version spécifique (dernière si omis)

### Exemple

```bash
GET /part-templates/123e4567-e89b-12d3-a456-426614174000?version=2
```

### Réponse

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "code": "VIS_STANDARD",
  "version": 2,
  "pattern": "{DIAM}x{LONG}-{MAT}-{TETE}",
  "fields": [
    {
      "key": "DIAM",
      "label": "Diamètre",
      "field_type": "number",
      "unit": "mm",
      "required": true,
      "enum_values": null
    },
    {
      "key": "LONG",
      "label": "Longueur",
      "field_type": "number",
      "unit": "mm",
      "required": true,
      "enum_values": null
    },
    {
      "key": "MAT",
      "label": "Matériau",
      "field_type": "enum",
      "unit": null,
      "required": true,
      "enum_values": [
        { "value": "INOX", "label": "Inox A2" },
        { "value": "ACIER", "label": "Acier zingué" },
        { "value": "LAITON", "label": "Laiton" }
      ]
    },
    {
      "key": "TETE",
      "label": "Type de tête",
      "field_type": "enum",
      "unit": null,
      "required": false,
      "enum_values": [
        { "value": "FH", "label": "Fraisée" },
        { "value": "CY", "label": "Cylindrique" },
        { "value": "BT", "label": "Bouton" }
      ]
    }
  ]
}
```

### Schéma TemplateField

| Champ         | Type    | Description                              |
| ------------- | ------- | ---------------------------------------- |
| `key`         | string  | Clé du champ (utilisée dans pattern)     |
| `label`       | string  | Libellé affiché                          |
| `field_type`  | enum    | Type : `"text"`, `"number"`, `"enum"`    |
| `unit`        | string? | Unité (ex: `"mm"`, `"kg"`) si applicable |
| `required`    | boolean | Champ obligatoire                        |
| `enum_values` | array?  | Valeurs si `field_type="enum"`           |

---

## POST /part-templates

Crée un nouveau template (version 1).

**Body :** `PartTemplateIn`

### Exemple

```json
{
  "code": "ROULEMENT_BILLES",
  "pattern": "{TYPE}{DIAM_INT}x{DIAM_EXT}x{LARG}",
  "fields": [
    {
      "key": "TYPE",
      "label": "Type de roulement",
      "field_type": "enum",
      "required": true,
      "enum_values": [
        { "value": "6", "label": "Rigide à billes (6xxx)" },
        { "value": "7", "label": "À contact oblique (7xxx)" }
      ]
    },
    {
      "key": "DIAM_INT",
      "label": "Diamètre intérieur",
      "field_type": "number",
      "unit": "mm",
      "required": true
    },
    {
      "key": "DIAM_EXT",
      "label": "Diamètre extérieur",
      "field_type": "number",
      "unit": "mm",
      "required": true
    },
    {
      "key": "LARG",
      "label": "Largeur",
      "field_type": "number",
      "unit": "mm",
      "required": true
    }
  ]
}
```

### Réponse (201)

```json
{
  "id": "323e4567-e89b-12d3-a456-426614174002",
  "code": "ROULEMENT_BILLES",
  "version": 1,
  "pattern": "{TYPE}{DIAM_INT}x{DIAM_EXT}x{LARG}"
}
```

### Règles de validation

- ✅ `pattern` doit contenir au moins un placeholder `{KEY}`
- ✅ `enum_values` obligatoire si `field_type="enum"`
- ✅ `enum_values` interdit si `field_type != "enum"`
- ✅ Au moins 1 champ requis

---

## POST /part-templates/{template_id}/versions

Crée une nouvelle version d'un template existant.

**Body :** `PartTemplateUpdate`

**Paramètres :**

- `template_id` (path) : UUID du template

### Exemple : Ajouter un champ à un template existant

```json
{
  "pattern": "{TYPE}{DIAM_INT}x{DIAM_EXT}x{LARG}-{ETANCHE}",
  "fields": [
    {
      "key": "TYPE",
      "label": "Type de roulement",
      "field_type": "enum",
      "required": true,
      "enum_values": [
        { "value": "6", "label": "Rigide à billes (6xxx)" },
        { "value": "7", "label": "À contact oblique (7xxx)" }
      ]
    },
    {
      "key": "DIAM_INT",
      "label": "Diamètre intérieur",
      "field_type": "number",
      "unit": "mm",
      "required": true
    },
    {
      "key": "DIAM_EXT",
      "label": "Diamètre extérieur",
      "field_type": "number",
      "unit": "mm",
      "required": true
    },
    {
      "key": "LARG",
      "label": "Largeur",
      "field_type": "number",
      "unit": "mm",
      "required": true
    },
    {
      "key": "ETANCHE",
      "label": "Étanchéité",
      "field_type": "enum",
      "required": false,
      "enum_values": [
        { "value": "2RS", "label": "Double flasque caoutchouc" },
        { "value": "ZZ", "label": "Double flasque métallique" },
        { "value": "OPEN", "label": "Ouvert" }
      ]
    }
  ]
}
```

### Réponse (201)

```json
{
  "id": "323e4567-e89b-12d3-a456-426614174002",
  "code": "ROULEMENT_BILLES",
  "version": 2,
  "pattern": "{TYPE}{DIAM_INT}x{DIAM_EXT}x{LARG}-{ETANCHE}"
}
```

**Note :** Le numéro de version est incrémenté automatiquement.

---

## DELETE /part-templates/{template_id}

Supprime un template ou une version spécifique.

**Paramètres :**

- `template_id` (path) : UUID du template
- `version` (query, optionnel) : Version à supprimer (toutes si omis)

### Exemples

```bash
# Supprimer uniquement la version 2
DELETE /part-templates/323e4567-e89b-12d3-a456-426614174002?version=2

# Supprimer toutes les versions
DELETE /part-templates/323e4567-e89b-12d3-a456-426614174002
```

### Réponse (200)

```json
{
  "message": "Template 323e4567-e89b-12d3-a456-426614174002 version 2 supprimé"
}
```

### Erreur (400) : Template utilisé

```json
{
  "detail": "Impossible de supprimer: 12 pièce(s) utilise(nt) ce template"
}
```

**Protection :** La suppression est refusée si des `stock_item` utilisent ce template/version.

---

## Utilisation avec stock_items

Voir [stock-items.md](stock-items.md) pour :

- Créer une pièce avec template
- Générer automatiquement la dimension
- Récupérer les caractéristiques

---

## Flux de travail recommandé

### 1. Créer un template

```bash
POST /part-templates
```

### 2. Associer à une sous-famille

Mettre à jour `stock_sub_family.template_id` en base (pas d'endpoint dédié pour l'instant).

### 3. Créer des pièces

```bash
POST /stock-items
# Si la sous-famille a un template, validation automatique + génération dimension
```

### 4. Faire évoluer le template

```bash
POST /part-templates/{id}/versions
# Les pièces existantes gardent leur version, nouvelles pièces utilisent v2
```

---

## Concepts clés

### Versionnement

- Chaque modification crée une nouvelle version
- Les pièces existantes restent sur leur version d'origine
- Immutabilité : `template_id` + `template_version` figés après création pièce

### Pattern de génération

Le pattern utilise des placeholders `{KEY}` remplacés par les valeurs des caractéristiques :

```
Pattern: "{DIAM}x{LONG}-{MAT}"
Caractéristiques:
  - DIAM: 10
  - LONG: 50
  - MAT: "INOX"

Dimension générée: "10x50-INOX"
```

### Types de champs

| Type     | Description      | Exemple valeur         |
| -------- | ---------------- | ---------------------- |
| `text`   | Texte libre      | `"A2-70"`              |
| `number` | Numérique        | `12.5`                 |
| `enum`   | Valeur contrôlée | `"INOX"` (parmi liste) |

---

## Voir aussi

- [stock-items.md](stock-items.md) — Création pièces avec template
- [stock-sub-families.md](stock-sub-families.md) — Hydratation templates
- [shared-schemas.md](shared-schemas.md) — Schémas partagés
