# Equipements

Gestion du parc d'équipements avec état de santé calculé, classification et hiérarchie parent/enfants.

> Voir aussi : [Equipement Classes](equipement-class.md) | [Interventions](interventions.md)
>
> Schemas partagés : [EquipementHealth](../shared-schemas.md#equipementhealth) | [EquipementClass](../shared-schemas.md#equipementclass) | [EmbeddedInterventionItem](../shared-schemas.md#embeddedinterventionitem)

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

Détail complet d'un équipement avec tous les champs de la base, `children_count` et les interventions directement liées, paginées.

### Query params

| Param                 | Type | Défaut | Description              |
| --------------------- | ---- | ------ | ------------------------ |
| `interventions_page`  | int  | 1      | Page des interventions   |
| `interventions_limit` | int  | 20     | Taille de page (max 100) |

### Réponse `200`

```json
{
  "id": "5e6b5a20-...",
  "code": "EQ-001",
  "name": "Scie principale",
  "no_machine": "M-042",
  "affectation": "Atelier A",
  "is_mere": true,
  "fabricant": "Bosch",
  "numero_serie": "SN-99887",
  "date_mise_service": "2019-03-15",
  "notes": "Révision annuelle prévue",
  "health": {
    "level": "critical",
    "reason": "1 intervention urgente ouverte",
    "rules_triggered": ["URGENT_OPEN >= 1"]
  },
  "parent_id": null,
  "equipement_class": { "id": "uuid", "code": "SCIE", "label": "Scie" },
  "children_count": 233,
  "interventions": {
    "total": 47,
    "page": 1,
    "page_size": 20,
    "total_pages": 3,
    "items": [
      {
        "id": "uuid",
        "code": "INT-0091",
        "title": "Remplacement lame",
        "type_inter": {
          "code": "CUR",
          "label": "Curatif"
        },
        "status_actual": "ouvert",
        "priority": "urgent",
        "reported_date": "2026-02-10"
      }
    ]
  }
}
```

> Les interventions retournées sont uniquement celles **directement liées** à cet équipement (`machine_id`), triées par `reported_date DESC`.

---

## `GET /equipements/{id}/children`

Liste paginée des enfants d'un équipement avec leur état de santé. Utile pour naviguer dans l'arborescence.

### Query params

| Param    | Type   | Défaut | Description                                         |
| -------- | ------ | ------ | --------------------------------------------------- |
| `page`   | int    | 1      | Page                                                |
| `limit`  | int    | 20     | Taille de page (max 100)                            |
| `search` | string | —      | Filtre sur `code` ou `name` (insensible à la casse) |

### Réponse `200`

```json
{
  "total": 233,
  "page": 1,
  "page_size": 20,
  "total_pages": 12,
  "items": [
    {
      "id": "7f2cda3c-...",
      "code": "EQ-042",
      "name": "Lame #1",
      "health": {
        "level": "ok",
        "reason": "Aucune intervention ouverte",
        "rules_triggered": []
      }
    }
  ]
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

| Champ                 | Type   | Requis | Description                    |
| --------------------- | ------ | ------ | ------------------------------ |
| `name`                | string | oui    | Nom de l'équipement            |
| `code`                | string | non    | Code unique                    |
| `parent_id`           | uuid   | non    | Équipement parent (hiérarchie) |
| `equipement_class_id` | uuid   | non    | Classe d'équipement            |

### Réponse `201`

Équipement complet (même format que `GET /equipements/{id}`, interventions vides, children_count à 0).

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

| Param        | Type | Défaut                   | Description      |
| ------------ | ---- | ------------------------ | ---------------- |
| `start_date` | date | null (tout l'historique) | Début de période |
| `end_date`   | date | now                      | Fin de période   |

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
