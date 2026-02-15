# Equipements

Gestion du parc d'équipements avec état de santé calculé, classification et hiérarchie parent/enfants.

> Voir aussi : [Equipement Classes](equipement-class.md) | [Interventions](interventions.md)
>
> Schemas partagés : [EquipementHealth](../shared-schemas.md#equipementhealth) | [EquipementClass](../shared-schemas.md#equipementclass)

---

## `GET /equipements`

Liste tous les équipements avec leur état de santé (léger, cacheable).

Tri par défaut : urgents DESC, ouverts DESC, nom ASC.

### Réponse `200`

```json
[
  {
    "id": "5e6b5a20-5d7f-4f6b-9a1f-4ccfb0b7a2a1",
    "code": "EQ-001",
    "name": "Scie principale",
    "health": {
      "level": "ok",
      "reason": "Aucune anomalie détectée"
    },
    "parent_id": null,
    "equipement_class": {
      "id": "b28f1f4f-...",
      "code": "SCIE",
      "label": "Scie"
    }
  }
]
```

> `equipement_class` est `null` si aucune classe assignée.

---

## `GET /equipements/{id}`

Détail d'un équipement avec `children_ids` et `rules_triggered` dans le health.

### Réponse `200`

```json
{
  "id": "5e6b5a20-...",
  "code": "EQ-001",
  "name": "Scie principale",
  "health": {
    "level": "warning",
    "reason": "Maintenance planifiée dépassée",
    "rules_triggered": ["maintenance_overdue"]
  },
  "parent_id": null,
  "equipement_class": { "id": "uuid", "code": "SCIE", "label": "Scie" },
  "children_ids": ["7f2cda3c-..."]
}
```

---

## `POST /equipements`

Crée un équipement.

### Entrée

```json
{
  "name": "Scie principale",
  "code": "EQ-001",
  "parent_id": null,
  "equipement_class_id": "b28f1f4f-..."
}
```

| Champ | Type | Requis | Description |
|---|---|---|---|
| `name` | string | oui | Nom de l'équipement |
| `code` | string | non | Code unique |
| `parent_id` | uuid | non | Équipement parent (hiérarchie) |
| `equipement_class_id` | uuid | non | Classe d'équipement |

### Réponse `201`

Équipement complet avec health, children_ids, equipement_class.

---

## `PUT /equipements/{id}`

Met à jour un équipement. Même body que POST, tous champs optionnels.

---

## `DELETE /equipements/{id}`

Supprime un équipement. Réponse `204`.

---

## `GET /equipements/{id}/stats`

Statistiques détaillées pour un équipement.

### Query params

| Param | Type | Défaut | Description |
|---|---|---|---|
| `start_date` | date | null (tout l'historique) | Début de période |
| `end_date` | date | now | Fin de période |

### Réponse `200`

```json
{
  "interventions": {
    "open": 2,
    "closed": 5,
    "by_status": { "ouvert": 2, "ferme": 5 },
    "by_priority": { "faible": 1, "normale": 4, "urgent": 2 }
  }
}
```

---

## `GET /equipements/{id}/health`

État de santé uniquement (ultra-léger, polling-friendly).

### Réponse `200`

```json
{
  "level": "ok",
  "reason": "Aucune anomalie détectée"
}
```
