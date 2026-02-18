# Equipement Classes

Classification des équipements par type (SCIE, EXTRUDEUSE, etc.). Relation Many-to-One avec les [Equipements](equipements.md).

> Schema partagé : [EquipementClass](../shared-schemas.md#equipementclass)

---

## `GET /equipement-class`

Liste toutes les classes, triées par code ASC.

### Réponse `200`

```json
[
  {
    "id": "b28f1f4f-...",
    "code": "SCIE",
    "label": "Scie",
    "description": "Machines de sciage"
  }
]
```

---

## `GET /equipement-class/{id}`

Détail d'une classe.

---

## `POST /equipement-class`

Crée une classe.

### Entrée

```json
{
  "code": "SCIE",
  "label": "Scie",
  "description": "Machines de sciage"
}
```

| Champ | Type | Requis | Description |
|---|---|---|---|
| `code` | string | oui | Code unique |
| `label` | string | oui | Libellé |
| `description` | string | non | Description |

### Règles métier

- `code` doit être unique

---

## `PATCH /equipement-class/{id}`

Met à jour une classe. Même body, tous champs optionnels. Si `code` change, l'unicité est vérifiée.

---

## `DELETE /equipement-class/{id}`

Supprime une classe.

### Règles métier

- **Impossible de supprimer** une classe utilisée par un équipement → Retourne `409 Conflict`

### Réponse `204`

Pas de contenu.
