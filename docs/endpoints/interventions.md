# Interventions

Gestion des interventions de maintenance. Chaque intervention est liée à un équipement et possède des actions, des logs de statut et des statistiques.

Une intervention peut être créée manuellement via `POST /interventions`, ou **automatiquement depuis une demande d'intervention** lors de la transition vers `acceptee`. Dans ce cas, le champ `request` contient les informations de la demande d'origine.

Une intervention peut aussi être liée à un **plan de maintenance préventive** (`plan_id` non null). Dans ce cas, le champ `task_progress` est hydraté sur `GET /interventions/{id}`.

> Voir aussi : [Actions](intervention-actions.md) | [Status Logs](intervention-status-log.md) | [Purchase Requests](purchase-requests.md) | [Intervention Requests](intervention-requests.md) | [Preventive Plans](preventive-plans.md) | [Intervention Tasks](intervention-tasks.md)

> **Audit log** : tout `POST`, `PUT` et `DELETE` sur cette ressource exige un champ `reason_code` dans le body. Voir [Audit Log — règle commune](audit-log.md#règle-commune--reason_code-obligatoire).

---

## Structure de réponse — enveloppe `audit`

Tous les endpoints `GET` de cette ressource retournent une enveloppe `{ data, audit }` :

```json
{
  "data": [ ...interventions... ],
  "audit": {
    "required": true,
    "reasons": [
      { "code": "EQUIPMENT_FAILURE", "label": "Panne équipement", "color": "...", "requires_text": false },
      { "code": "CLIENT_REQUEST", "label": "Demande client", "color": "#8b5cf6", "requires_text": false },
      { "code": "OTHER", "label": "Autre raison", "color": "#9ca3af", "requires_text": true }
    ]
  }
}
```

Le champ `audit` est identique en liste et en détail — le front le charge une seule fois au montage du composant.

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
| `tech_id`       | uuid   | —      | Filtrer par UUID du technicien pilote (`intervention.tech_id`)          |
| `sort`          | csv    | —      | Tri avec `-` pour DESC (ex: `-priority,-reported_date,-next_due_date`)  |
| `include`       | csv    | —      | Données optionnelles (`stats`). Stats incluses par défaut               |

> Pour lister les interventions ouvertes d'un équipement (ex: sélecteur planning) : `GET /interventions?equipement_id=<uuid>&status=ouvert,en_cours`

> Valeurs de `sort` supportées : `reported_date`, `priority`, `next_due_date`. Préfixer `-` pour DESC. `next_due_date` utilise `NULLS LAST` — les interventions sans tâche due apparaissent en dernier.

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
        "reason": "2 tâches non clôturées",
        "open_interventions_count": 1,
        "urgent_count": 0,
        "open_requests_count": 2,
        "new_requests_count": 1,
        "request_status_counts": {"nouvelle": 1, "en_attente": 1},
        "open_tasks_count": 2,
        "overdue_tasks_count": 1,
        "unassigned_tasks_count": 1,
        "open_purchase_requests_count": 1,
        "purchase_request_status_counts": {"OPEN": 1},
        "has_affectation": true,
        "rules_triggered": ["OPEN_TOTAL > 0", "OVERDUE_TASKS > 0", "OPEN_REQUESTS > 0", "OPEN_TASKS > 0", "OPEN_PURCHASE_REQUESTS > 0"]
      }
      "parent": { "id": "uuid", "code": "VLT", "name": "Site des villettes" },
      "equipement_class": { "id": "uuid", "code": "SCIE", "label": "Scie" },
      "statut": {
        "id": 3,
        "code": "EN_SERVICE",
        "label": "En service",
        "interventions": true,
        "couleur": "#10B981"
      }
    },
    "type_inter": "curatif",
    "priority": "urgent",
    "reported_by": "Jean Dupont",
    "tech_initials": "QC",
    "tech_id": "uuid-utilisateur",
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
    "next_due_date": "2026-06-20",
    "overdue": false,
    "stats": {
      "action_count": 3,
      "total_time": 4.5,
      "avg_complexity": 6.2,
      "purchase_count": 3,
      "tasks": {
        "total": 5,
        "todo": 2,
        "in_progress": 1,
        "done": 2,
        "skipped": 0,
        "blocking_pending": 3
      },
      "purchase_requests": {
        "total": 3,
        "received": 1,
        "to_qualify": 0,
        "no_supplier_ref": 0,
        "pending_dispatch": 1,
        "rejected": 0,
        "consultation": 0,
        "partial": 0,
        "ordered": 1,
        "quoted": 0,
        "open": 0
      }
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

| Champ                                   | Description                                                                                            |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `health`                                | Exactement le même objet que `GET /equipements/{id}/health` (même logique, mêmes règles, mêmes champs) |
| `health.level`                          | `ok`, `maintenance`, `warning`, `critical`                                                             |
| `health.open_interventions_count`       | Nombre d'interventions ouvertes                                                                        |
| `health.urgent_count`                   | Nombre d'interventions urgentes ouvertes                                                               |
| `health.open_requests_count`            | Nombre de DI ouvertes (hors `rejetee` et `cloturee`)                                                   |
| `health.new_requests_count`             | Nombre de DI en statut `nouvelle`                                                                      |
| `health.request_status_counts`          | Répartition des DI ouvertes par statut                                                                 |
| `health.open_tasks_count`               | Nombre de tâches non clôturées (`status != done/skipped`)                                              |
| `health.overdue_tasks_count`            | Nombre de tâches en retard (`due_date < aujourd'hui`)                                                  |
| `health.unassigned_tasks_count`         | Nombre de tâches ouvertes non affectées                                                                |
| `health.open_purchase_requests_count`   | Nombre de DA ouvertes (hors `closed`, `cloturee`, `cancelled`, `annulee`)                              |
| `health.purchase_request_status_counts` | Répartition des DA ouvertes par statut                                                                 |
| `health.has_affectation`                | `true` si `affectation` est renseignée sur l'équipement                                                |
| `health.rules_triggered`                | Règles ayant déclenché le niveau de santé                                                              |
| `parent`                                | Équipement parent `{id, code, name}`. `null` si racine                                                 |
| `statut`                                | Statut opérationnel `{id, code, label, interventions, couleur}`. `null` si non renseigné               |
| `equipement_class`                      | Classe d'équipement `{id, code, label}`. `null` si non renseignée                                      |

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
      "reason": "2 tâches non clôturées",
      "open_interventions_count": 1,
      "urgent_count": 0,
      "open_requests_count": 2,
      "new_requests_count": 1,
      "request_status_counts": {"nouvelle": 1, "en_attente": 1},
      "open_tasks_count": 2,
      "overdue_tasks_count": 1,
      "unassigned_tasks_count": 1,
      "open_purchase_requests_count": 1,
      "purchase_request_status_counts": {"OPEN": 1},
      "has_affectation": true,
      "rules_triggered": ["OPEN_TOTAL > 0", "OVERDUE_TASKS > 0", "OPEN_REQUESTS > 0", "OPEN_TASKS > 0", "OPEN_PURCHASE_REQUESTS > 0"]
    }
    "parent": { "id": "uuid", "code": "VLT", "name": "Site des villettes" },
    "equipement_class": { "id": "uuid", "code": "SCIE", "label": "Scie" },
    "statut": {
      "id": 3,
      "code": "EN_SERVICE",
      "label": "En service",
      "interventions": true,
      "couleur": "#10B981"
    },
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
    },
    "preventive_plans": [
      {
        "id": "uuid",
        "code": "PLAN-CODE",
        "label": "Libellé du plan",
        "trigger_type": "periodicity",
        "periodicity_days": 15,
        "hours_threshold": null,
        "active": true,
        "next_occurrence": null
      }
    ],
    "preventive_occurrences_summary": {
      "pending_count": 0,
      "generated_count": 0,
      "skipped_count": 0,
      "next_scheduled": null,
      "last_skipped_reason": null
    },
    "open_requests": [
      {
        "id": "uuid",
        "code": "DI-2026-0024",
        "description": "Description de la demande",
        "statut": "acceptee",
        "statut_label": "Acceptée",
        "statut_color": "#22c55e",
        "is_system": true,
        "created_at": "2026-04-13T16:59:34Z"
      }
    ]
  },
  "type_inter": "curatif",
  "priority": "urgent",
  "reported_by": "Jean Dupont",
  "tech_initials": "QC",
  "tech_id": "uuid-utilisateur",
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
    "purchase_count": 3,
    "tasks": {
      "total": 5,
      "todo": 2,
      "in_progress": 1,
      "done": 2,
      "skipped": 0,
      "blocking_pending": 3
    },
    "purchase_requests": {
      "total": 3,
      "received": 1,
      "to_qualify": 0,
      "no_supplier_ref": 0,
      "pending_dispatch": 1,
      "rejected": 0,
      "consultation": 0,
      "partial": 0,
      "ordered": 1,
      "quoted": 0,
      "open": 0
    }
  },
  "plan_id": null,
  "task_progress": null,
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
      "task": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "label": "Diagnostic initial",
        "status": "done",
        "origin": "plan"
      },
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

| Champ                  | Liste                                                                          | Détail                                                                                                                                                                                                                             |
| ---------------------- | ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `equipements`          | Léger : `id`, `code`, `name`, `health`, `parent`, `equipement_class`, `statut` | Complet : + `no_machine`, `affectation`, `is_mere`, `fabricant`, `numero_serie`, `date_mise_service`, `notes`, `children_count`, `interventions` (paginées), `preventive_plans`, `preventive_occurrences_summary`, `open_requests` |
| `request`              | Objet `InterventionRequestListItem` (`null` si création manuelle)              | Idem                                                                                                                                                                                                                               |
| `actions`              | Toujours `[]`                                                                  | Tableau de [InterventionActionOut](intervention-actions.md) complet avec `subcategory`, `tech`, `purchase_requests`, **`task`**                                                                                                    |
| `status_logs`          | Toujours `[]`                                                                  | Tableau de [InterventionStatusLogOut](intervention-status-log.md)                                                                                                                                                                  |
| `plan_id`              | Absent (non retourné en liste)                                                 | UUID du plan préventif si l'intervention provient de la maintenance préventive, `null` sinon                                                                                                                                       |
| `task_progress`        | Absent (non retourné en liste)                                                 | Objet [TaskProgressOut](intervention-tasks.md#get-intervention-tasksprogress) (`total`, `todo`, `in_progress`, `done`, `skipped`, `is_complete`). `null` si `plan_id` est null                                                     |
| `tasks`                | Absent (non retourné en liste)                                                 | Tableau de [InterventionTaskOut](intervention-tasks.md) — tâches de l'intervention. `[]` si `plan_id` est null                                                                                                                     |
| `next_due_date`        | `date\|null` — MIN des `due_date` des tâches. `null` si aucune tâche avec due_date | Idem                                                                                                                                                                                                                          |
| `overdue`              | `bool` — `true` si `next_due_date < aujourd'hui`                               | Idem                                                                                                                                                                                                                               |
| `stats.purchase_count` | Égal à `stats.purchase_requests.total` (même source)                          | Égal à `stats.purchase_requests.total` (même source)                                                                                                                                                                              |
| `stats.tasks`          | Calculé en SQL (LATERAL subquery)                                              | Calculé en SQL (query dédiée). Champs : `total`, `todo`, `in_progress`, `done`, `skipped`, `blocking_pending` (non-optionnelles en todo/in_progress — bloque la clôture)                                                          |
| `stats.purchase_requests` | Calculé en SQL (LATERAL sur la VIEW `purchase_request_derived_status`)     | Calculé en SQL (query dédiée sur la VIEW). Même structure : `total`, `received`, `to_qualify`, `no_supplier_ref`, `pending_dispatch`, `rejected`, `consultation`, `partial`, `ordered`, `quoted`, `open`                          |

### Actions avec tâche liée

Chaque action dans `actions` inclut un champ `task` (optionnel) : la **tâche liée à cette action**.

| Champ         | Type   | Description                              |
| ------------- | ------ | ---------------------------------------- |
| `task.id`     | uuid   | ID de la tâche                           |
| `task.label`  | string | Intitulé de la tâche                     |
| `task.status` | string | `todo`, `in_progress`, `done`, `skipped` |
| `task.origin` | string | `plan`, `resp`, `tech`                   |

Voir [Intervention Actions — task](intervention-actions.md) pour le détail complet.

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
  "type_inter": "CUR",
  "tech_id": "uuid-utilisateur",
  "title": "Remplacement roulement principal",
  "priority": "urgent",
  "reported_by": "Jean Dupont",
  "status_actual": "ouvert",
  "printed_fiche": false,
  "reported_date": "2026-01-13",
  "reason_code": "EQUIPMENT_FAILURE",
  "reason_text": null
}
```

> **Note** : `machine_id`, `type_inter` et `tech_id` sont requis. L'API résout automatiquement les initiales du technicien depuis `directus_users.initial` pour alimenter le trigger PostgreSQL `trg_interv_code` qui génère le code (`{machine.code}-{type_inter}-{YYYYMMDD}-{initiales}`).

| Champ           | Type   | Requis  | Défaut   | Description                                                                                                                                                                                                                                                 |
| --------------- | ------ | ------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `machine_id`    | uuid   | **oui** | —        | Équipement concerné (trigger exige une machine existante)                                                                                                                                                                                                   |
| `type_inter`    | string | **oui** | —        | Type d'intervention (`CUR`, `PRE`, `REA`, `BAT`, `PRO`, `COF`, `PIL`, `MES`) — voir `GET /interventions/types`                                                                                                                                              |
| `tech_id`       | uuid   | **oui** | —        | UUID du technicien pilote (`directus_users.id`). L'API résout les initiales en interne pour le trigger de génération de code                                                                                                                                |
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

> **`reason_code` obligatoire** — voir [Audit Log](audit-log.md#règle-commune--reason_code-obligatoire).

> **Clôture automatique de la demande liée** : si `status_actual` est mis à jour vers le code `ferme` et qu'une demande d'intervention est liée (`request` non null), cette demande passe automatiquement à `cloturee`. En cas d'échec de la cascade (demande restée en `acceptee`), utiliser `POST /interventions/{id}/force-close-request`.

> **Tâches incomplètes** : si l'intervention a des tâches non-optionnelles en `todo` ou `in_progress`, la mise à jour vers le statut `ferme` est bloquée et retourne `400` avec `"Impossible de fermer : X tâche(s) non-optionnelle(s) en attente."`. Utiliser `PATCH /intervention-tasks/{id}` pour traiter les tâches avant de clôturer.

### Réponse `200`

Intervention complète mise à jour.

---

## `POST /interventions/{id}/force-close-request`

Force la clôture de la demande d'intervention liée quand la cascade automatique a échoué (bug corrigé le 2026-04-27 : la comparaison du code statut était fausse, les demandes restaient bloquées en `acceptee` après fermeture de l'intervention).

### Conditions requises

- L'intervention doit être au statut `ferme`
- Une demande liée doit être encore en statut `acceptee`

### Réponse `200`

Intervention complète mise à jour. La demande liée (`request`) est désormais au statut `cloturee`.

### Erreurs

| Code | Cas                                            |
| ---- | ---------------------------------------------- |
| 404  | Intervention introuvable                       |
| 400  | L'intervention n'est pas au statut `ferme`     |
| 400  | Aucune demande en statut `acceptee` n'est liée |

---

## `DELETE /interventions/{id}`

Supprime une intervention. La suppression est **interdite** si l'intervention possède des actions ou des demandes d'achat liées.

> **`reason_code` obligatoire** — voir [Audit Log](audit-log.md#règle-commune--reason_code-obligatoire).

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
