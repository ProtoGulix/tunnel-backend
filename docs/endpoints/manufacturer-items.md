# Manufacturer Items

Références fabricants/constructeurs. Chaque référence fournisseur (`stock-item-suppliers`) peut être liée à une référence fabricant.

> Voir aussi : [Stock Item Suppliers](stock-item-suppliers.md) | [Stock Items](stock-items.md)

---

## `GET /manufacturer-items`

Liste toutes les références fabricants.

### Query params

| Param   | Type | Défaut | Description |
| ------- | ---- | ------ | ----------- |
| `skip`  | int  | 0      | Offset      |
| `limit` | int  | 100    | Max: 1000   |

### Réponse `200` — ManufacturerItemOut[]

```json
[
  {
    "id": "uuid",
    "manufacturer_name": "SKF",
    "manufacturer_ref": "6205-2RS"
  }
]
```

Trié par `manufacturer_name` ASC.

---

## `GET /manufacturer-items/{id}`

Détail d'une référence fabricant.

### Réponse `200` — ManufacturerItemOut

```json
{
  "id": "uuid",
  "manufacturer_name": "SKF",
  "manufacturer_ref": "6205-2RS"
}
```

### Erreurs

| Code | Cas                   |
| ---- | --------------------- |
| 404  | Référence introuvable |

---

## `POST /manufacturer-items`

Crée une nouvelle référence fabricant.

### Entrée

```json
{
  "manufacturer_name": "SKF",
  "manufacturer_ref": "6205-2RS",
  "notes": "Roulement à billes rangée simple"
}
```

| Champ               | Type   | Requis | Description                      |
| ------------------- | ------ | ------ | -------------------------------- |
| `manufacturer_name` | string | oui    | Nom du fabricant/constructeur    |
| `manufacturer_ref`  | string | non    | Référence catalogue du fabricant |

### Réponse `201` — ManufacturerItemOut

---

## `PATCH /manufacturer-items/{id}`

Met à jour partiellement une référence fabricant.

### Entrée — champs modifiables

| Champ               | Type   | Description                      |
| ------------------- | ------ | -------------------------------- |
| `manufacturer_name` | string | Nom du fabricant                 |
| `manufacturer_ref`  | string | Référence catalogue du fabricant |

### Réponse `200` — ManufacturerItemOut

---

## `DELETE /manufacturer-items/{id}`

Supprime une référence fabricant.

### Réponse `204`

Pas de contenu.

### Erreurs

| Code | Cas                   |
| ---- | --------------------- |
| 404  | Référence introuvable |

---

## Schéma — ManufacturerItemOut

```json
{
  "id": "uuid",
  "manufacturer_name": "string",
  "manufacturer_ref": "string | null"
}
```
