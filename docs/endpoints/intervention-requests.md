# Intervention Requests

Demandes d'intervention formulées par les opérateurs ou services, avant création d'une intervention formelle. Chaque demande suit un cycle de statuts avec historique complet des transitions.

Lors de l'acceptation, une **intervention est automatiquement créée** et liée à la demande. À la clôture, l'intervention liée est automatiquement fermée (et inversement).

> Voir aussi : [Interventions](interventions.md) | [Équipements](equipements.md) | [Services](services.md)

> **Audit log** : tout `POST`, `PATCH` et `DELETE` sur cette ressource exige un champ `reason_code` dans le body. Voir [Audit Log — règle commune](audit-log.md#règle-commune--reason_code-obligatoire).

---

## Audit log

### Couverture

| Endpoint                              | Loggué par       | `decision_type`         | `is_system` |
| ------------------------------------- | ---------------- | ----------------------- | ----------- |
| `POST /intervention-requests`         | repo (`create`)  | `created`               | selon `is_system` du payload |
| `POST /{id}/transition`               | repo (`transition_status`) | `status_transitioned` | `false` |
| `POST /repair`                        | repo (`repair_orphaned_requests`) | `status_transitioned` | `true` |

> Le middleware `AuditMiddleware` couvre également `POST /{id}/transition` (path avec UUID) et produit un diff `statut_changed` — il peut donc y avoir deux entrées d'audit pour une transition. Le log repo est plus sémantique (`status_transitioned` avec before/after explicites).

### Validation `reason_code`

Le middleware valide la présence et l'existence du `reason_code` **avant** l'exécution de la route pour tous les `POST` avec UUID dans le path. Pour `POST /intervention-requests` (création) et `POST /repair` (pas d'UUID dans le path), la validation est gérée par les validators Pydantic et la fonction DB `fn_audit_log_decision`.

---

## Structure de réponse — enveloppe `audit`

Les endpoints `GET` de cette ressource retournent une enveloppe `{ data, audit }` (ou `{ items, pagination, facets, audit }` pour la liste paginée) :

```json
{
  "items": [ ...demandes... ],
  "pagination": { ... },
  "facets": { "statut": [ ... ] },
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

Le détail (`GET /{id}`) retourne `{ data: {...}, audit: {...} }`.

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
      "intervention": {
        "id": "uuid-de-l-intervention-liee",
        "code": "INT-2026-0042-QC",
        "title": "Bruit anormal au démarrage, vibrations sur le moteur",
        "type_inter": "CUR",
        "priority": "urgent",
        "status_actual": "in_progress",
        "status_label": "Pris en charge",
        "status_color": "#F59E0B",
        "tech_initials": "QC",
        "tech_id": "uuid-du-technicien",
        "reported_by": "Jean Dupont",
        "reported_date": "2026-03-10",
        "next_due_date": null,
        "overdue": false,
        "plan_id": null,
        "printed_fiche": false,
        "created_at": "2026-03-10T09:15:00",
        "updated_at": "2026-03-10T09:15:00",
        "stats": {
          "action_count": 2,
          "total_time": 3.5,
          "avg_complexity": 2.0,
          "purchase_count": 1
        }
      },
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
  },
  "audit": {
    "required": true,
    "reasons": [ "..." ]
  }
}
```

| Champ                       | Description                                                                                            |
| --------------------------- | ------------------------------------------------------------------------------------------------------ |
| `intervention_id`           | UUID de l'intervention GMAO créée lors de l'acceptation. `null` tant que la demande n'est pas acceptée |
| `intervention`              | Objet `InterventionRef` : premier niveau de l'intervention liée, avec ses stats. `null` si pas encore acceptée ou si rejetée |
| `intervention.stats`        | Calculé en une seule requête (LATERAL JOIN) : `action_count`, `total_time` (heures), `avg_complexity`, `purchase_count` |
| `is_system`                 | `true` si la DI a été générée automatiquement (ex : occurrence préventive). `false` par défaut         |
| `suggested_type_inter`      | Type d'intervention suggéré par le système (`CUR`, `PRE`, etc.). `null` pour les DI humaines           |

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
  "intervention": {
    "id": "uuid-de-l-intervention-liee",
    "code": "INT-2026-0042-QC",
    "title": "Bruit anormal au démarrage, vibrations sur le moteur",
    "type_inter": "CUR",
    "priority": "urgent",
    "status_actual": "in_progress",
    "status_label": "Pris en charge",
    "status_color": "#F59E0B",
    "tech_initials": "QC",
    "tech_id": "uuid-du-technicien",
    "reported_by": "Jean Dupont",
    "reported_date": "2026-03-10",
    "next_due_date": null,
    "overdue": false,
    "plan_id": null,
    "printed_fiche": false,
    "created_at": "2026-03-10T09:15:00",
    "updated_at": "2026-03-10T09:15:00",
    "stats": {
      "action_count": 2,
      "total_time": 3.5,
      "avg_complexity": 2.0,
      "purchase_count": 1
    }
  },
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

| Champ                       | Description                                                                                                               |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `code`                      | Auto-généré par trigger DB (format `DI-YYYY-NNNN`)                                                                        |
| `equipement`                | Objet `EquipementListItem` : `id`, `code`, `name`, `health`, `parent_id`, `equipement_class`. `null` si machine supprimée |
| `equipement.health`         | Calculé depuis toutes les interventions ouvertes sur la machine                                                           |
| `intervention_id`           | UUID de l'intervention liée (`null` si pas encore acceptée)                                                               |
| `intervention`              | Objet `InterventionRef` complet. `null` si DI non encore acceptée ou rejetée                                              |
| `intervention.stats`        | `action_count` : nombre d'actions ; `total_time` : heures cumulées ; `avg_complexity` : complexité moyenne ; `purchase_count` : commandes liées |
| `status_log`                | Historique complet trié par date ASC                                                                                      |
| `status_log[].status_from`  | `null` pour la création initiale                                                                                          |
| `status_log[].changed_by`   | UUID Directus de l'utilisateur (`null` si non renseigné ou clôture auto)                                                  |

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
  "description": "Bruit anormal au démarrage, vibrations sur le moteur",
  "reason_code": "EQUIPMENT_FAILURE"
}
```

| Champ                  | Type    | Requis       | Description                                                            |
| ---------------------- | ------- | ------------ | ---------------------------------------------------------------------- |
| `machine_id`           | uuid    | **oui**      | Équipement concerné                                                    |
| `demandeur_nom`        | string  | **oui**      | Nom du demandeur                                                       |
| `description`          | string  | **oui**      | Description de l'intervention souhaitée                                |
| `service_id`           | uuid    | non          | UUID du service/département du demandeur                               |
| `is_system`            | boolean | non          | `true` si DI générée par le système. Défaut : `false`                  |
| `suggested_type_inter` | string  | non          | Type suggéré parmi `CUR`, `PRE`, `REA`, `BAT`, `PRO`, `COF`, `PIL`, `MES`. `null` par défaut |
| `reason_code`          | string  | **oui**      | Code raison obligatoire pour l'audit. Voir `GET /audit/reasons`        |
| `reason_text`          | string  | conditionnel | Texte libre obligatoire si `reason_code = "OTHER"`                     |

### Réponse `201` — `InterventionRequestDetail`

Retourne la demande créée avec son code et son statut initial. Le champ `intervention` est `null` (statut `nouvelle`).

**Audit** : log `created` inséré dans `audit_log` avec `decision_type = "created"`.

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
  "reported_date": "2026-03-10",
  "reason_code": "CLIENT_REQUEST"
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
| `reason_code`   | string | **oui**               | Code raison obligatoire pour l'audit. Voir `GET /audit/reasons`                                                         |
| `reason_text`   | string | conditionnel          | Texte libre obligatoire si `reason_code = "OTHER"`                                                                      |

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

Retourne la demande mise à jour. Si `acceptee`, les champs `intervention_id` et `intervention` sont désormais renseignés.

**Audit** : log `status_transitioned` inséré dans `audit_log` avec `old_value = {"statut": "<ancien>"}` et `new_value = {"statut": "<nouveau>", "notes": "..."}`.

### Erreurs

| Code | Cas                                                                                                |
| ---- | -------------------------------------------------------------------------------------------------- |
| 404  | Demande introuvable                                                                                |
| 422  | Transition non autorisée depuis le statut actuel                                                   |
| 422  | `notes` manquant pour le statut `rejetee`                                                          |
| 422  | `type_inter` ou `tech_initials` manquant pour le statut `acceptee` (DI humaine sans type suggéré)  |
| 400  | DI système sans `suggested_type_inter` et sans `type_inter` dans le payload                        |
| 422  | Code `status_to` inconnu dans le référentiel                                                       |

---

## `POST /intervention-requests/repair`

Outil de maintenance : passe à `cloturee` toutes les DIs en statut `acceptee` dont l'intervention liée est déjà fermée.

Utile pour corriger des données historiques où la cascade de clôture automatique n'a pas été déclenchée (fermeture directe en base, données importées, etc.).

**Idempotent** : peut être appelé plusieurs fois sans effet secondaire.

**Audit** : un log `status_transitioned` (`is_system = true`) est inséré dans `audit_log` pour chaque DI réparée.

### Réponse `200` — `RepairResult`

```json
{
  "repaired_count": 3,
  "details": [
    { "id": "uuid", "code": "DI-2026-0012", "machine_code": "EQ-001" },
    { "id": "uuid", "code": "DI-2026-0018", "machine_code": "EQ-007" },
    { "id": "uuid", "code": "DI-2025-0099", "machine_code": "EQ-003" }
  ]
}
```

| Champ            | Description                                        |
| ---------------- | -------------------------------------------------- |
| `repaired_count` | Nombre de DIs passées à `cloturee`                 |
| `details`        | Liste des DIs réparées avec `id`, `code`, `machine_code` |

> Si aucune DI orpheline n'est trouvée, `repaired_count` vaut `0` et `details` est vide.
