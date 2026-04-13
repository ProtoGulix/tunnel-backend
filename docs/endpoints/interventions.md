# Interventions

Gestion des interventions de maintenance. Chaque intervention est liée à un équipement et possède des actions, des logs de statut et des statistiques.

Une intervention peut être créée manuellement via `POST /interventions`, ou **automatiquement depuis une demande d'intervention** lors de la transition vers `acceptee`. Dans ce cas, le champ `request` contient les informations de la demande d'origine.

Une intervention peut aussi être liée à un **plan de maintenance préventive** (`plan_id` non null). Dans ce cas, le champ `gamme_progress` est hydraté sur `GET /interventions/{id}`.

> Voir aussi : [Actions](intervention-actions.md) | [Status Logs](intervention-status-log.md) | [Purchase Requests](purchase-requests.md) | [Intervention Requests](intervention-requests.md) | [Preventive Plans](preventive-plans.md) | [Gamme Step Validations](gamme-step-validations.md)

---

## `GET /interventions`

Liste les interventions avec filtres, tri et pagination.

### Query params

| Param           | Type   | Défaut | Description                                                             |
| --------------- | ------ | ------ | ----------------------------------------------------------------------- |
| `skip`          | int    | 0      | Offset de pagination                                                    |
| `limit`         | int    | 100    | Nombre max (max: 1000)                                                  |
| `search`        | string | —      | Recherche insensible à la casse sur code, titre, code et nom équipement |
| `equipement_id` | uuid   | —      | Filtrer par équipement (`machine_id`)                                   |
| `status`        | csv    | —      | Filtrer par codes statut (ex: `ouvert,ferme,en_cours`)                  |
| `priority`      | csv    | —      | Filtrer par priorité (`faible,normale,important,urgent`)                |
| `printed`       | bool   | —      | `true` : imprimées, `false` : non imprimées, omis : toutes              |
| `sort`          | csv    | —      | Tri avec `-` pour DESC (ex: `-priority,-reported_date`)                 |
| `include`       | csv    | —      | Données optionnelles (`stats`). Stats incluses par défaut               |

> Pour lister les interventions ouvertes d'un équipement (ex: sélecteur planning) : `GET /interventions?equipement_id=<uuid>&status=ouvert,en_cours`

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
    "request": {
      "id": "uuid-de-la-demande",
      "code": "DI-2026-0042",
      "demandeur_nom": "Jean Dupont",
      "demandeur_service": "Production",
      "description": "Bruit anormal sur la scie principale",
      "statut": "acceptee",
      "statut_label": "Acceptée",
      "statut_color": "#48BB78",
      "intervention_id": "5ecf60d5-8471-4739-8ba8-0fdad7b51781",
      "created_at": "2026-01-12T09:00:00",
      "updated_at": "2026-01-13T08:00:00",
      "equipement": null
    },
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

| Champ     | Description                                                                                                            |
| --------- | ---------------------------------------------------------------------------------------------------------------------- |
| `request` | Demande d'intervention à l'origine de cette intervention (`InterventionRequestListItem`). `null` si création manuelle. |

> **Note** : `actions` et `status_logs` sont toujours `[]` en liste. Utilisez `GET /interventions/{id}` pour les obtenir.

### Champs `equipements` en liste

| Champ              | Description                                                                                                |
| ------------------ | ---------------------------------------------------------------------------------------------------------- |
| `health`           | Calculé depuis le compte réel des interventions ouvertes sur l'équipement (toutes, pas seulement filtrées) |
| `health.level`     | `ok`, `maintenance` (≥ 1 ouverte), `critical` (≥ 1 urgente)                                                |
| `equipement_class` | Classe d'équipement (`null` si non renseignée)                                                             |

---

## `GET /interventions/types`

Retourne la liste des types d'intervention disponibles.

### Réponse `200`

```json
[
  { "id": "CUR", "title": "Curatif", "color": "red" },
  { "id": "PRE", "title": "Préventif", "color": "green" },
  { "id": "REA", "title": "Réapprovisionnement", "color": "blue" },
  { "id": "BAT", "title": "Batiment", "color": "gray" },
  { "id": "PRO", "title": "Projet", "color": "blue" },
  { "id": "COF", "title": "Remise en conformité", "color": "amber" },
  { "id": "PIL", "title": "Pilotage", "color": "blue" },
  { "id": "MES", "title": "Mise en service", "color": "amber" }
]
```

> Utiliser `id` comme valeur du champ `type_inter` lors de la création d'une intervention.

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
  "request": {
    "id": "uuid-de-la-demande",
    "code": "DI-2026-0042",
    "demandeur_nom": "Jean Dupont",
    "demandeur_service": "Production",
    "description": "Bruit anormal sur la scie principale",
    "statut": "acceptee",
    "statut_label": "Acceptée",
    "statut_color": "#48BB78",
    "intervention_id": "5ecf60d5-8471-4739-8ba8-0fdad7b51781",
    "created_at": "2026-01-12T09:00:00",
    "updated_at": "2026-01-13T08:00:00",
    "equipement": null
  },
  "stats": {
    "action_count": 3,
    "total_time": 4.5,
    "avg_complexity": 6.2,
    "purchase_count": 1
  },
  "plan_id": null,
  "gamme_progress": null,
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
      "action_start": "08:00:00",
      "action_end": "09:30:00",
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
| `request`              | Objet `InterventionRequestListItem` (`null` si création manuelle)       | Idem                                                                                                                                                        |
| `actions`              | Toujours `[]`                                                           | Tableau de [InterventionActionOut](intervention-actions.md) complet avec `subcategory`, `tech`, `purchase_requests`                                         |
| `status_logs`          | Toujours `[]`                                                           | Tableau de [InterventionStatusLogOut](intervention-status-log.md)                                                                                           |
| `plan_id`              | Absent (non retourné en liste)                                          | UUID du plan préventif si l'intervention provient de la maintenance préventive, `null` sinon                                                                |
| `gamme_progress`       | Absent (non retourné en liste)                                          | Objet [GammeProgressOut](gamme-step-validations.md) (`total`, `validated`, `skipped`, `pending`, `is_complete`). `null` si `plan_id` est null               |
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
  "machine_id": "uuid",
  "type_inter": "curatif",
  "tech_initials": "QC",
  "title": "Remplacement roulement principal",
  "priority": "urgent",
  "reported_by": "Jean Dupont",
  "status_actual": "ouvert",
  "printed_fiche": false,
  "reported_date": "2026-01-13"
}
```

> **Note** : `machine_id`, `type_inter` et `tech_initials` sont requis par le trigger PostgreSQL `trg_interv_code` qui génère le code d'intervention (`{machine.code}-{type_inter}-{YYYYMMDD}-{tech_initials}`). Une erreur DB est levée si l'un d'eux est absent ou si la machine est inconnue.

| Champ           | Type   | Requis  | Défaut   | Description                                                                                                                                                                                                                                                 |
| --------------- | ------ | ------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `machine_id`    | uuid   | **oui** | —        | Équipement concerné (trigger exige une machine existante)                                                                                                                                                                                                   |
| `type_inter`    | string | **oui** | —        | Type d'intervention (`CUR`, `PRE`, `REA`, `BAT`, `PRO`, `COF`, `PIL`, `MES`) — voir `GET /interventions/types`                                                                                                                                              |
| `tech_initials` | string | **oui** | —        | Initiales du technicien — intégrées dans le code                                                                                                                                                                                                            |
| `title`         | string | non     | null     | Titre de l'intervention                                                                                                                                                                                                                                     |
| `priority`      | string | non     | null     | `faible`, `normale`, `important`, `urgent`                                                                                                                                                                                                                  |
| `reported_by`   | string | non     | null     | Nom du signaleur                                                                                                                                                                                                                                            |
| `status_actual` | string | non     | `ouvert` | Code statut initial (géré par trigger)                                                                                                                                                                                                                      |
| `printed_fiche` | bool   | non     | `false`  | Fiche imprimée ?                                                                                                                                                                                                                                            |
| `reported_date` | date   | non     | null     | Date de signalement                                                                                                                                                                                                                                         |
| `request_id`    | uuid   | non     | null     | UUID d'une demande existante à lier (statuts `nouvelle` ou `en_attente`). La demande passe automatiquement à `acceptee`. La liaison est **verrouillée** : la demande et l'intervention ne peuvent ensuite plus être liées à d'autres entités (`400` sinon). |

### Réponse `201`

Intervention complète avec equipement, `request` (objet demande si liée), stats, actions, status_logs.

---

## `PUT /interventions/{id}`

Met à jour une intervention. Même body que POST, tous les champs sont optionnels.

> **Clôture automatique de la demande liée** : si `status_actual` est mis à jour vers le code `ferme` et qu'une demande d'intervention est liée (`request` non null), cette demande passe automatiquement à `cloturee`.

> **Gamme incomplète** : si l'intervention a un plan préventif (`plan_id` non null) et que des étapes de gamme sont encore en statut `pending`, un trigger DB bloque la clôture et retourne `409` avec `"Des étapes de gamme sont en attente de validation"`. Utiliser `PATCH /gamme-step-validations` pour traiter les étapes avant de clôturer.

### Réponse `200`

Intervention complète mise à jour.

---

## `DELETE /interventions/{id}`

Supprime une intervention. La suppression est **interdite** si l'intervention possède des actions ou des demandes d'achat liées.

### Réponse `200`

```json
{ "detail": "Intervention supprimée" }
```

### Erreurs

| Code | Cas                                             |
| ---- | ----------------------------------------------- |
| 404  | Intervention introuvable                        |
| 400  | Intervention possède des actions liées          |
| 400  | Intervention possède des demandes d'achat liées |
