# Intervention Requests

Demandes d'intervention formulées par les opérateurs ou services, avant création d'une intervention formelle. Chaque demande suit un cycle de statuts avec historique complet des transitions.

Lors de l'acceptation, une **intervention est automatiquement créée** et liée à la demande. À la clôture, l'intervention liée est automatiquement fermée (et inversement).

> Voir aussi : [Interventions](interventions.md) | [Équipements](equipements.md) | [Services](services.md)

---

## Cycle de vie et logique métier

```
nouvelle → en_attente → acceptee → cloturee
nouvelle → rejetee
en_attente → rejetee
```

| Code         | Label      | Terminal | Effet métier                                                         |
| ------------ | ---------- | -------- | -------------------------------------------------------------------- |
| `nouvelle`   | Nouvelle   | non      | —                                                                    |
| `en_attente` | En attente | non      | —                                                                    |
| `acceptee`   | Acceptée   | non      | Crée une intervention GMAO (`status_actual = in_progress`) et la lie |
| `rejetee`    | Rejetée    | **oui**  | Motif (`notes`) obligatoire                                          |
| `cloturee`   | Clôturée   | **oui**  | Ferme l'intervention liée (`status_actual = ferme`)                  |

### Verrouillage de la liaison

Une fois qu'une demande est liée à une intervention (statut `acceptee`), **la liaison est verrouillée dans les deux sens** :

- La demande ne peut plus être liée à une autre intervention (erreur `400`).
- L'intervention ne peut plus être liée à une autre demande (erreur `400`).

### Clôture automatique depuis l'intervention

Quand une intervention liée est fermée via `PUT /interventions/{id}`, la demande associée passe automatiquement à `cloturee`.

---

## `GET /intervention-requests/statuses`

Référentiel des statuts avec labels et couleurs. Utiliser pour construire les badges et filtres côté frontend.

### Réponse `200` — `List[RequestStatusRef]`

```json
[
  {
    "code": "nouvelle",
    "label": "Nouvelle",
    "color": "#6B7280",
    "sort_order": 1
  },
  {
    "code": "en_attente",
    "label": "En attente",
    "color": "#F59E0B",
    "sort_order": 2
  },
  {
    "code": "acceptee",
    "label": "Acceptée",
    "color": "#10B981",
    "sort_order": 3
  },
  {
    "code": "rejetee",
    "label": "Rejetée",
    "color": "#EF4444",
    "sort_order": 4
  },
  {
    "code": "cloturee",
    "label": "Clôturée",
    "color": "#3B82F6",
    "sort_order": 5
  }
]
```

> Source : table `request_status_ref`.

---

## `GET /intervention-requests`

Liste paginée des demandes avec filtres.

### Query params

| Param              | Type    | Défaut | Description                                                    |
| ------------------ | ------- | ------ | -------------------------------------------------------------- |
| `skip`             | int     | 0      | Offset                                                         |
| `limit`            | int     | 50     | Max: 500                                                       |
| `statut`           | string  | —      | Filtrer par code statut (`nouvelle`, `acceptee`, etc.)         |
| `exclude_statuses` | csv     | —      | Statuts à exclure, séparés par virgule. Ex: `rejetee,cloturee` |
| `machine_id`       | uuid    | —      | Filtrer par équipement                                         |
| `search`           | string  | —      | Recherche sur `code`, `demandeur_nom`, `description` (ILIKE)   |
| `is_system`        | boolean | —      | `true` : DI générées automatiquement. `false` : DI humaines    |

### Réponse `200`

```json
{
  "items": [
    {
      "id": "uuid",
      "code": "DI-2026-0042",
      "equipement": {
        "id": "uuid",
        "code": "EQ-001",
        "name": "Convoyeur principal",
        "health": {
          "level": "maintenance",
          "reason": "1 intervention(s) ouverte(s)",
          "rules_triggered": null
        },
        "parent_id": null,
        "equipement_class": {
          "id": "uuid",
          "code": "CONV",
          "label": "Convoyeur"
        }
      },
      "demandeur_nom": "Jean Dupont",
      "service": {
        "id": "uuid",
        "code": "PROD",
        "label": "Production",
        "is_active": true
      },
      "demandeur_service": "Production",
      "description": "Bruit anormal au démarrage, vibrations sur le moteur",
      "statut": "acceptee",
      "statut_label": "Acceptée",
      "statut_color": "#10B981",
      "intervention_id": "uuid-de-l-intervention-liee",
      "is_system": false,
      "suggested_type_inter": null,
      "created_at": "2026-03-10T08:00:00",
      "updated_at": "2026-03-10T09:15:00"
    }
  ],
  "pagination": {
    "total": 87,
    "page": 1,
    "page_size": 50,
    "total_pages": 2,
    "offset": 0,
    "count": 50
  },
  "facets": {
    "statut": [
      {
        "code": "nouvelle",
        "label": "Nouvelle",
        "color": "#6B7280",
        "sort_order": 1,
        "count": 12
      },
      {
        "code": "en_attente",
        "label": "En attente",
        "color": "#F59E0B",
        "sort_order": 2,
        "count": 5
      },
      {
        "code": "acceptee",
        "label": "Acceptée",
        "color": "#10B981",
        "sort_order": 3,
        "count": 3
      },
      {
        "code": "rejetee",
        "label": "Rejetée",
        "color": "#EF4444",
        "sort_order": 4,
        "count": 7
      },
      {
        "code": "cloturee",
        "label": "Clôturée",
        "color": "#3B82F6",
        "sort_order": 5,
        "count": 60
      }
    ]
  }
}
```

| Champ                  | Description                                                                                            |
| ---------------------- | ------------------------------------------------------------------------------------------------------ |
| `intervention_id`      | UUID de l'intervention GMAO créée lors de l'acceptation. `null` tant que la demande n'est pas acceptée |
| `is_system`            | `true` si la DI a été générée automatiquement (ex : occurrence préventive). `false` par défaut         |
| `suggested_type_inter` | Type d'intervention suggéré par le système (`CUR`, `PRE`, etc.). `null` pour les DI humaines           |

> `facets.statut` : tous les statuts avec leur compteur. Les filtres `machine_id` et `search` sont appliqués, mais pas `statut` — permet d'afficher tous les onglets même quand un est sélectionné.

---

## `GET /intervention-requests/{id}`

Détail complet avec historique des transitions de statut.

### Réponse `200` — `InterventionRequestDetail`

```json
{
  "id": "uuid",
  "code": "DI-2026-0042",
  "equipement": {
    "id": "uuid",
    "code": "EQ-001",
    "name": "Convoyeur principal",
    "health": {
      "level": "maintenance",
      "reason": "1 intervention(s) ouverte(s)",
      "rules_triggered": null
    },
    "parent_id": null,
    "equipement_class": { "id": "uuid", "code": "CONV", "label": "Convoyeur" }
  },
  "demandeur_nom": "Jean Dupont",
  "service": {
    "id": "uuid",
    "code": "PROD",
    "label": "Production",
    "is_active": true
  },
  "demandeur_service": "Production",
  "description": "Bruit anormal au démarrage, vibrations sur le moteur",
  "statut": "acceptee",
  "statut_label": "Acceptée",
  "statut_color": "#10B981",
  "intervention_id": "uuid-de-l-intervention-liee",
  "is_system": false,
  "suggested_type_inter": null,
  "created_at": "2026-03-10T08:00:00",
  "updated_at": "2026-03-10T09:15:00",
  "status_log": [
    {
      "id": "uuid",
      "status_from": null,
      "status_to": "nouvelle",
      "status_from_label": null,
      "status_to_label": "Nouvelle",
      "status_to_color": "#6B7280",
      "changed_by": null,
      "notes": null,
      "date": "2026-03-10T08:00:00"
    },
    {
      "id": "uuid",
      "status_from": "nouvelle",
      "status_to": "acceptee",
      "status_from_label": "Nouvelle",
      "status_to_label": "Acceptée",
      "status_to_color": "#10B981",
      "changed_by": "uuid-user",
      "notes": "Prise en charge atelier maintenance",
      "date": "2026-03-10T09:15:00"
    }
  ]
}
```

| Champ                      | Description                                                                                                               |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `code`                     | Auto-généré par trigger DB (format `DI-YYYY-NNNN`)                                                                        |
| `equipement`               | Objet `EquipementListItem` : `id`, `code`, `name`, `health`, `parent_id`, `equipement_class`. `null` si machine supprimée |
| `equipement.health`        | Calculé depuis toutes les interventions ouvertes sur la machine                                                           |
| `intervention_id`          | UUID de l'intervention liée (`null` si pas encore acceptée)                                                               |
| `status_log`               | Historique complet trié par date ASC                                                                                      |
| `status_log[].status_from` | `null` pour la création initiale                                                                                          |
| `status_log[].changed_by`  | UUID Directus de l'utilisateur (`null` si non renseigné ou clôture auto)                                                  |

### Backward compatibility

- **`demandeur_service`** (champ legacy) : Ancienne façon de stocker le service en texte libre. Toujours exposé en sortie pour compatibilité frontend, mais ne reflète pas les changements — utiliser `service` pour accéder au service référentiel
- **`service`** (nouveau) : Référence vers le service via `service_id`. Apparaît en réponse si la demande est liée à un service

### Erreurs

| Code | Cas                 |
| ---- | ------------------- |
| 404  | Demande introuvable |

---

## `POST /intervention-requests`

Crée une nouvelle demande d'intervention. Le code (`DI-YYYY-NNNN`) et le statut initial (`nouvelle`) sont générés automatiquement par trigger.

### Entrée

```json
{
  "machine_id": "uuid",
  "demandeur_nom": "Jean Dupont",
  "service_id": "uuid-du-service",
  "description": "Bruit anormal au démarrage, vibrations sur le moteur"
}
```

| Champ                  | Type    | Requis  | Description                                                            |
| ---------------------- | ------- | ------- | ---------------------------------------------------------------------- |
| `machine_id`           | uuid    | **oui** | Équipement concerné                                                    |
| `demandeur_nom`        | string  | **oui** | Nom du demandeur                                                       |
| `description`          | string  | **oui** | Description de l'intervention souhaitée                                |
| `service_id`           | uuid    | non     | UUID du service/département du demandeur                               |
| `is_system`            | boolean | non     | `true` si DI générée par le système. Défaut : `false`                  |
| `suggested_type_inter` | string  | non     | Type suggéré parmi `CUR`, `PRE`, `REA`, `BAT`, `PRO`, `COF`, `PIL`, `MES`. `null` par défaut |

### Réponse `201` — `InterventionRequestDetail`

Retourne la demande créée avec son code et son statut initial.

### Erreurs

| Code | Cas                                                     |
| ---- | ------------------------------------------------------- |
| 422  | `machine_id`, `demandeur_nom` ou `description` manquant |

---

## `POST /intervention-requests/{id}/transition`

Effectue une transition de statut sur une demande. Chaque transition est tracée dans `status_log`.

Pour la transition vers `acceptee`, une intervention GMAO est automatiquement créée et liée à la demande. Les champs `type_inter` et `tech_initials` sont alors obligatoires.

### Entrée

```json
{
  "status_to": "acceptee",
  "notes": "Prise en charge atelier maintenance",
  "changed_by": "uuid-user",
  "type_inter": "CUR",
  "tech_initials": "QC",
  "priority": "urgent",
  "reported_date": "2026-03-10"
}
```

| Champ           | Type   | Requis                | Description                                                                                                             |
| --------------- | ------ | --------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `status_to`     | string | **oui**               | Code du statut cible                                                                                                    |
| `notes`         | string | conditionnel          | **Obligatoire** si `status_to = "rejetee"`                                                                              |
| `changed_by`    | uuid   | non                   | UUID de l'utilisateur Directus                                                                                          |
| `type_inter`    | string | conditionnel          | Type d'intervention. **Obligatoire** si `acceptee` et DI humaine sans `suggested_type_inter`. Ignoré pour les DI système |
| `tech_initials` | string | **oui si** `acceptee` | Initiales du technicien. Intégrées dans le code de l'intervention                                                       |
| `priority`      | string | non (si `acceptee`)   | `faible`, `normale`, `important`, `urgent`. Défaut : `normale`                                                          |
| `reported_date` | date   | non (si `acceptee`)   | Date de signalement (`YYYY-MM-DD`). Défaut : null                                                                       |

> **Résolution du `type_inter` pour les DI système** : si `is_system=true`, le type est résolu automatiquement depuis `suggested_type_inter`. Le champ `type_inter` du payload est ignoré. Si `suggested_type_inter` est aussi absent, une erreur `400` est levée.

### Transitions autorisées

| Depuis       | Vers                                | Effet                                 |
| ------------ | ----------------------------------- | ------------------------------------- |
| `nouvelle`   | `en_attente`, `acceptee`, `rejetee` | `acceptee` : crée l'intervention GMAO |
| `en_attente` | `acceptee`, `rejetee`               | `acceptee` : crée l'intervention GMAO |
| `acceptee`   | `cloturee`                          | Ferme l'intervention GMAO liée        |
| `rejetee`    | — (état final)                      | —                                     |
| `cloturee`   | — (état final)                      | —                                     |

### Réponse `200` — `InterventionRequestDetail`

Retourne la demande mise à jour. Si `acceptee`, le champ `intervention_id` est désormais renseigné.

### Erreurs

| Code | Cas                                                                                                |
| ---- | -------------------------------------------------------------------------------------------------- |
| 404  | Demande introuvable                                                                                |
| 422  | Transition non autorisée depuis le statut actuel                                                   |
| 422  | `notes` manquant pour le statut `rejetee`                                                          |
| 422  | `type_inter` ou `tech_initials` manquant pour le statut `acceptee` (DI humaine sans type suggéré)  |
| 400  | DI système sans `suggested_type_inter` et sans `type_inter` dans le payload                        |
| 422  | Code `status_to` inconnu dans le référentiel                                                       |
