# Sous-familles de stock

> Endpoints pour les sous-familles d'articles de stock avec hydratation des templates (v1.4.0)

---

## GET /stock-sub-families

Liste toutes les sous-familles avec leurs templates associés.

**Hydratation :** Si la sous-famille a un `template_id`, le template complet est chargé avec tous ses champs et valeurs enum.

### Réponse

```json
[
  {
    "family_code": "FIX",
    "code": "VIS",
    "label": "Vis",
    "template": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "code": "VIS_STANDARD",
      "version": 2,
      "pattern": "{DIAM}x{LONG}-{MAT}",
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
            { "value": "ACIER", "label": "Acier zingué" }
          ]
        }
      ]
    }
  },
  {
    "family_code": "FIX",
    "code": "ECROU",
    "label": "Écrous",
    "template": null
  }
]
```

**Note :** `"template": null` si la sous-famille n'a pas de template associé (mode legacy).

---

## GET /stock-sub-families/{family_code}/{sub_family_code}

Récupère une sous-famille spécifique avec son template.

**Paramètres :**

- `family_code` (path) : Code de la famille
- `sub_family_code` (path) : Code de la sous-famille

### Exemple

```bash
GET /stock-sub-families/FIX/VIS
```

### Réponse

```json
{
  "family_code": "FIX",
  "code": "VIS",
  "label": "Vis",
  "template": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "code": "VIS_STANDARD",
    "version": 2,
    "pattern": "{DIAM}x{LONG}-{MAT}",
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
          { "value": "ACIER", "label": "Acier zingué" }
        ]
      }
    ]
  }
}
```

### Erreur (404)

```json
{
  "detail": "Sous-famille FIX/INVALID non trouvée"
}
```

---

## Utilisation

### 1. Lister les sous-familles pour sélection

```javascript
// Frontend : Afficher dropdown des sous-familles
const response = await fetch("/stock-sub-families");
const subFamilies = await response.json();

subFamilies.forEach((sf) => {
  console.log(`${sf.family_code}/${sf.code} - ${sf.label}`);
  if (sf.template) {
    console.log(`  → Template: ${sf.template.code} v${sf.template.version}`);
  } else {
    console.log(`  → Mode legacy (saisie libre)`);
  }
});
```

### 2. Récupérer template pour formulaire dynamique

```javascript
// Quand l'utilisateur sélectionne une sous-famille
const response = await fetch("/stock-sub-families/FIX/VIS");
const subFamily = await response.json();

if (subFamily.template) {
  // Générer formulaire dynamique basé sur template.fields
  subFamily.template.fields.forEach((field) => {
    if (field.field_type === "number") {
      createNumberInput(field.key, field.label, field.unit, field.required);
    } else if (field.field_type === "enum") {
      createSelectInput(
        field.key,
        field.label,
        field.enum_values,
        field.required,
      );
    } else {
      createTextInput(field.key, field.label, field.required);
    }
  });
} else {
  // Afficher formulaire legacy (dimension manuelle)
  createTextInput("dimension", "Dimension", true);
}
```

---

## Schéma StockSubFamily

| Champ         | Type          | Description                       |
| ------------- | ------------- | --------------------------------- |
| `family_code` | string        | Code de la famille                |
| `code`        | string        | Code de la sous-famille           |
| `label`       | string        | Libellé                           |
| `template`    | PartTemplate? | Template associé (null si legacy) |

Voir [part-templates.md](part-templates.md) pour le schéma `PartTemplate`.

---

## Flux avec création de pièce

```mermaid
sequenceDiagram
    Frontend->>API: GET /stock-sub-families/FIX/VIS
    API->>DB: SELECT template_id FROM stock_sub_family
    API->>DB: SELECT * FROM part_template + fields + enum
    API-->>Frontend: {template avec fields}

    Frontend->>Frontend: Génère formulaire dynamique
    User->>Frontend: Remplit caractéristiques

    Frontend->>API: POST /stock_items {characteristics}
    API->>API: Valide via template
    API->>API: Génère dimension via pattern
    API->>DB: INSERT stock_item + characteristics
    API-->>Frontend: Pièce créée
```

---

## Voir aussi

- [stock-items.md](stock-items.md) — Création pièces avec/sans template
- [part-templates.md](part-templates.md) — Gestion des templates
- [shared-schemas.md](shared-schemas.md) — Schémas partagés
