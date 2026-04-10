# Equipements

Gestion du parc d'équipements avec état de santé calculé, classification et hiérarchie parent/enfants.

> Voir aussi : [Equipement Classes](equipement-class.md) | [Equipement Statuts](equipement-statuts.md) | [Interventions](interventions.md)
>
> Schemas partagés : [EquipementHealth](../shared-schemas.md#equipementhealth) | [EquipementClass](../shared-schemas.md#equipementclass) | [EmbeddedInterventionItem](../shared-schemas.md#embeddedinterventionitem)

---

## `GET /equipements`

Liste les équipements avec leur état de santé, paginée, avec facettes par classe.

Tri par défaut : urgents DESC, ouverts DESC, nom ASC.

### Query params

| Param           | Type   | Défaut | Description                                                                      |
| --------------- | ------ | ------ | -------------------------------------------------------------------------------- |
| `search`        | string | —      | Recherche insensible à la casse sur `code`, `name`, `affectation`                |
| `skip`          | int    | 0      | Nombre d'éléments à ignorer (offset)                                             |
| `limit`         | int    | 50     | Nombre d'éléments par page (max 500)                                             |
| `select_class`  | string | —      | Codes de classes à inclure (filtre exclusif), séparés par virgule. Ex: `POM,SCI` |
| `exclude_class` | string | —      | Codes de classes à exclure, séparés par virgule. Ex: `POM,SCI`                   |
| `select_mere`   | uuid   | —      | UUID de l'équipement parent : retourne uniquement ses enfants directs            |

### Réponse `200`

```json
{
  "items": [
    {
      "id": "5e6b5a20-5d7f-4f6b-9a1f-4ccfb0b7a2a1",
      "code": "EQ-001",
      "name": "Scie principale",
      "health": {
        "level": "ok",
        "reason": "Aucune intervention ouverte",
        "open_interventions_count": 0,
        "urgent_count": 0,
        "new_requests_count": 0
      },
      "parent": null,
      "equipement_class": {
        "id": "b28f1f4f-...",
        "code": "SCIE",
        "label": "Scie"
      },
      "statut": {
        "id": 3,
        "code": "EN_SERVICE",
        "label": "En service",
        "interventions": true,
        "couleur": "#10B981"
      }
    }
  ],
  "pagination": {
    "total": 142,
    "page": 1,
    "page_size": 50,
    "total_pages": 3,
    "offset": 0,
    "count": 50
  },
  "facets": {
    "equipement_class": [
      { "code": "SCIE", "label": "Scie", "count": 12 },
      { "code": null, "label": null, "count": 5 }
    ]
  }
}
```

> `equipement_class` dans les items est `null` si aucune classe assignée.
> `statut` est `null` si aucun statut assigné à l'équipement (compatibilité ascendante).
> Les facettes comptent les équipements **sans** tenir compte du filtre `exclude_class`, pour permettre l'affichage des compteurs même sur les classes exclues.

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
    "open_interventions_count": 3,
    "urgent_count": 1,
    "new_requests_count": 2,
    "rules_triggered": ["URGENT_OPEN >= 1", "NEW_REQUESTS > 0"]
  },
  "parent": {
    "id": "uuid-parent",
    "code": "EQ-000",
    "name": "Machine mère"
  },
  "equipement_class": { "id": "uuid", "code": "SCIE", "label": "Scie" },
  "statut": {
    "id": 3,
    "code": "EN_SERVICE",
    "label": "En service",
    "interventions": true,
    "couleur": "#10B981"
  },
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
  "reason": "Aucune intervention ouverte",
  "open_interventions_count": 0,
  "urgent_count": 0,
  "new_requests_count": 0
}
```
