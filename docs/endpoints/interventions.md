# Interventions

Gestion des interventions de maintenance. Chaque intervention est liée à un équipement et possède des actions, des logs de statut et des statistiques.

> Voir aussi : [Actions](intervention-actions.md) | [Status Logs](intervention-status-log.md) | [Purchase Requests](purchase-requests.md)

---

## `GET /interventions`

Liste les interventions avec filtres, tri et pagination.

### Query params

| Param           | Type | Défaut | Description                                                |
| --------------- | ---- | ------ | ---------------------------------------------------------- |
| `skip`          | int  | 0      | Offset de pagination                                       |
| `limit`         | int  | 100    | Nombre max (max: 1000)                                     |
| `equipement_id` | uuid | —      | Filtrer par équipement (`machine_id`)                      |
| `status`        | csv  | —      | Filtrer par codes statut (ex: `ouvert,ferme,en_cours`)     |
| `priority`      | csv  | —      | Filtrer par priorité (`faible,normale,important,urgent`)   |
| `printed`       | bool | —      | `true` : imprimées, `false` : non imprimées, omis : toutes |
| `sort`          | csv  | —      | Tri avec `-` pour DESC (ex: `-priority,-reported_date`)    |
| `include`       | csv  | —      | Données optionnelles (`stats`). Stats incluses par défaut  |

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
      "health": {
        "level": "maintenance",
        "reason": "1 intervention(s) ouverte(s)",
        "rules_triggered": null
      },
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

### Champs `equipements` en liste

| Champ              | Description                                                                                                |
| ------------------ | ---------------------------------------------------------------------------------------------------------- |
| `health`           | Calculé depuis le compte réel des interventions ouvertes sur l'équipement (toutes, pas seulement filtrées) |
| `health.level`     | `ok`, `maintenance` (≥ 1 ouverte), `critical` (≥ 1 urgente)                                                |
| `equipement_class` | Classe d'équipement (`null` si non renseignée)                                                             |

---

## `GET /interventions/{id}`

Détail complet d'une intervention. **La structure est différente de la liste** : l'équipement est chargé via son propre repository (détail complet), et les actions/logs sont hydratés.

### Réponse `200`

```json
{
  "id": "5ecf60d5-8471-4739-8ba8-0fdad7b51781",
  "code": "CN001-REA-20260113-QC",
  "title": "Remplacement roulement principal",
  "equipements": {
    "id": "uuid",
    "code": "EQ-001",
    "name": "Scie principale",
    "no_machine": "42",
    "affectation": "Atelier usinage",
    "is_mere": false,
    "fabricant": "Felder",
    "numero_serie": "SN-2019-001",
    "date_mise_service": "2019-04-01",
    "notes": null,
    "health": {
      "level": "maintenance",
      "reason": "1 intervention(s) ouverte(s)",
      "rules_triggered": null
    },
    "parent_id": null,
    "equipement_class": { "id": "uuid", "code": "SCIE", "label": "Scie" },
    "children_count": 2,
    "interventions": {
      "total": 5,
      "page": 1,
      "page_size": 20,
      "total_pages": 1,
      "items": [
        {
          "id": "uuid",
          "code": "CN001-REA-...",
          "title": "...",
          "type_inter": { "code": "curatif", "label": "Curatif" },
          "status_actual": "en_cours",
          "priority": "urgent",
          "reported_date": "2026-01-13"
        }
      ]
    }
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
  "actions": [
    {
      "id": "uuid",
      "intervention_id": "uuid",
      "description": "Remplacement du roulement SKF 6205",
      "time_spent": 1.5,
      "subcategory": {
        "id": 30,
        "name": "Remplacement pièce",
        "code": "DEP_REM",
        "category": {
          "id": 3,
          "name": "Dépannage",
          "code": "DEP",
          "color": "#e53e3e"
        }
      },
      "tech": {
        "id": "uuid",
        "first_name": "Jean",
        "last_name": "Dupont",
        "email": "jean.dupont@example.com",
        "initial": "JD",
        "status": "active",
        "role": "uuid"
      },
      "complexity_score": 7,
      "complexity_factor": "PCE",
      "purchase_requests": [
        {
          "id": "uuid",
          "item_label": "Roulement SKF 6205",
          "quantity": 2,
          "derived_status": {
            "code": "ORDERED",
            "label": "Commandé",
            "color": "#3B82F6"
          },
          "stock_item_ref": "OUT-ROUL-SKF-6205",
          "quotes_count": 1,
          "selected_count": 1,
          "suppliers_count": 1,
          "created_at": "2026-01-13T10:00:00",
          "updated_at": "2026-01-14T08:00:00"
        }
      ],
      "created_at": "2026-01-13T14:30:00",
      "updated_at": "2026-01-13T15:00:00"
    }
  ],
  "status_logs": [
    {
      "id": "uuid",
      "status_code": "en_cours",
      "label": "En cours",
      "changed_at": "2026-01-13T08:00:00",
      "changed_by": "Jean Dupont"
    }
  ]
}
```

### Différences avec la liste

| Champ                  | Liste                                                                   | Détail                                                                                                                                                      |
| ---------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `equipements`          | Léger : `id`, `code`, `name`, `health`, `parent_id`, `equipement_class` | Complet : + `no_machine`, `affectation`, `is_mere`, `fabricant`, `numero_serie`, `date_mise_service`, `notes`, `children_count`, `interventions` (paginées) |
| `actions`              | Toujours `[]`                                                           | Tableau de [InterventionActionOut](intervention-actions.md) complet avec `subcategory`, `tech`, `purchase_requests`                                         |
| `status_logs`          | Toujours `[]`                                                           | Tableau de [InterventionStatusLogOut](intervention-status-log.md)                                                                                           |
| `stats.purchase_count` | Calculé en SQL (agrégat)                                                | Calculé depuis les `purchase_requests` chargées dans les actions                                                                                            |

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

| Champ           | Type   | Requis | Défaut   | Description                                |
| --------------- | ------ | ------ | -------- | ------------------------------------------ |
| `title`         | string | non    | null     | Titre de l'intervention                    |
| `machine_id`    | uuid   | non    | null     | Équipement concerné                        |
| `type_inter`    | string | non    | null     | Type (curatif, preventif, etc.)            |
| `priority`      | string | non    | null     | `faible`, `normale`, `important`, `urgent` |
| `reported_by`   | string | non    | null     | Nom du signaleur                           |
| `tech_initials` | string | non    | null     | Initiales du technicien                    |
| `status_actual` | string | non    | `ouvert` | Code statut initial                        |
| `printed_fiche` | bool   | non    | false    | Fiche imprimée ?                           |
| `reported_date` | date   | non    | null     | Date de signalement                        |

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
