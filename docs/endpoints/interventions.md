# Interventions

Gestion des interventions de maintenance. Chaque intervention est liée à un équipement et possède des actions, des logs de statut et des statistiques.

> Voir aussi : [Actions](intervention-actions.md) | [Status Logs](intervention-status-log.md) | [Purchase Requests](purchase-requests.md)

---

## `GET /interventions`

Liste les interventions avec filtres, tri et pagination.

### Query params

| Param | Type | Défaut | Description |
|---|---|---|---|
| `skip` | int | 0 | Offset de pagination |
| `limit` | int | 100 | Nombre max (max: 1000) |
| `equipement_id` | uuid | — | Filtrer par équipement (`machine_id`) |
| `status` | csv | — | Filtrer par codes statut (ex: `ouvert,ferme,en_cours`) |
| `priority` | csv | — | Filtrer par priorité (`faible,normale,important,urgent`) |
| `printed` | bool | — | `true` : imprimées, `false` : non imprimées, omis : toutes |
| `sort` | csv | — | Tri avec `-` pour DESC (ex: `-priority,-reported_date`) |
| `include` | csv | — | Données optionnelles (`stats`). Stats incluses par défaut |

### Réponse `200`

```json
[
  {
    "id": "5ecf60d5-8471-4739-8ba8-0fdad7b51781",
    "code": "CN001-REA-20260113-QC",
    "title": "Remplacement roulement principal",
    "equipements": {
      "id": "uuid",
      "code": "EQ-001",
      "name": "Scie principale",
      "health": { "level": "maintenance", "reason": "1 intervention ouverte" },
      "parent_id": null,
      "equipement_class": { "id": "uuid", "code": "SCIE", "label": "Scie" }
    },
    "type_inter": "curatif",
    "priority": "urgent",
    "reported_by": "Jean Dupont",
    "tech_initials": "QC",
    "status_actual": "en_cours",
    "updated_by": "uuid",
    "printed_fiche": false,
    "reported_date": "2026-01-13",
    "stats": {
      "action_count": 3,
      "total_time": 4.5,
      "avg_complexity": 6.2,
      "purchase_count": 1
    },
    "actions": [],
    "status_logs": []
  }
]
```

> **Note** : `actions` et `status_logs` sont toujours `[]` en liste. Utilisez `GET /interventions/{id}` pour les obtenir.

---

## `GET /interventions/{id}`

Détail complet d'une intervention avec actions, status logs et stats.

### Réponse `200`

Même structure que la liste, mais avec :
- `actions` : tableau de [InterventionActionOut](intervention-actions.md#interventionactionout)
- `status_logs` : tableau de [InterventionStatusLogOut](intervention-status-log.md#interventionstatuslogout)

---

## `GET /interventions/{id}/actions`

Raccourci vers les actions d'une intervention. Voir [Intervention Actions](intervention-actions.md).

---

## `POST /interventions`

Crée une nouvelle intervention.

### Entrée

```json
{
  "title": "Remplacement roulement principal",
  "machine_id": "uuid",
  "type_inter": "curatif",
  "priority": "urgent",
  "reported_by": "Jean Dupont",
  "tech_initials": "QC",
  "status_actual": "ouvert",
  "printed_fiche": false,
  "reported_date": "2026-01-13"
}
```

| Champ | Type | Requis | Défaut | Description |
|---|---|---|---|---|
| `title` | string | non | null | Titre de l'intervention |
| `machine_id` | uuid | non | null | Équipement concerné |
| `type_inter` | string | non | null | Type (curatif, preventif, etc.) |
| `priority` | string | non | null | `faible`, `normale`, `important`, `urgent` |
| `reported_by` | string | non | null | Nom du signaleur |
| `tech_initials` | string | non | null | Initiales du technicien |
| `status_actual` | string | non | `ouvert` | Code statut initial |
| `printed_fiche` | bool | non | false | Fiche imprimée ? |
| `reported_date` | date | non | null | Date de signalement |

### Réponse `201`

Intervention complète avec equipement, stats, actions, status_logs.

---

## `PUT /interventions/{id}`

Met à jour une intervention. Même body que POST, tous les champs sont optionnels.

### Réponse `200`

Intervention complète mise à jour.

---

## `DELETE /interventions/{id}`

Supprime une intervention.

### Réponse `204`

Pas de contenu.
