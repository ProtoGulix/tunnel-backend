# Audit Log

Système de traçabilité centralisée de toutes les mutations métier.

> Voir aussi : [Interventions](interventions.md) | [Intervention Requests](intervention-requests.md) | [Purchase Requests](purchase-requests.md) | [Intervention Tasks](intervention-tasks.md) | [Intervention Actions](intervention-actions.md)

---

## Règle commune — `reason_code` obligatoire

**Toute mutation** (`POST`, `PUT`, `PATCH`, `DELETE`) sur les entités suivantes **doit** inclure un `reason_code` dans le body JSON :

| Entité | Routes concernées |
|--------|------------------|
| Intervention | `POST /interventions`, `PUT /interventions/{id}`, `DELETE /interventions/{id}` |
| Demande d'intervention (DI) | `POST /intervention-requests`, `POST /intervention-requests/{id}/transition`, `DELETE /intervention-requests/{id}` |
| Demande d'achat (DA) | `POST /purchase-requests`, `PUT /purchase-requests/{id}`, `DELETE /purchase-requests/{id}` |
| Tâche | `POST /intervention-tasks`, `PATCH /intervention-tasks/{id}`, `DELETE /intervention-tasks/{id}` |
| Action | `POST /intervention-actions`, `PATCH /intervention-actions/{id}` |

### Champs audit dans le body

```json
{
  "reason_code": "CLIENT_REQUEST",
  "reason_text": "Texte libre optionnel (obligatoire si reason_code = OTHER)"
}
```

| Champ | Type | Requis | Description |
|-------|------|--------|-------------|
| `reason_code` | string | **oui** | Code raison depuis `GET /audit/reasons` |
| `reason_text` | string | conditionnel | Obligatoire si `reason_code = "OTHER"`, optionnel sinon |

### Erreurs

| Code | Cas |
|------|-----|
| `400` | `reason_code` absent du body |
| `400` | `reason_code` inconnu ou inactif |
| `400` | `reason_code = "OTHER"` sans `reason_text` |

---

## `GET /audit/reasons`

Liste les raisons d'audit disponibles.

### Query params

| Param | Type | Description |
|-------|------|-------------|
| `category` | string | Filtre : `system`, `manual`, `user` |
| `entity_type` | string | Filtre par entité compatible : `intervention`, `request`, `purchase_request`, `task`, `action` |
| `active_only` | bool | Défaut `true` — masque les raisons désactivées |

### Réponse `200`

```json
[
  {
    "id": 1,
    "code": "CLIENT_REQUEST",
    "label": "Demande client",
    "category": "manual",
    "color": "#8b5cf6",
    "description": "Client demande priorité"
  },
  {
    "id": 10,
    "code": "OTHER",
    "label": "Autre raison",
    "category": "user",
    "color": "#9ca3af",
    "description": "À justifier en texte libre"
  }
]
```

### Raisons disponibles (seed initial)

| Code | Label | Catégorie | Entités compatibles |
|------|-------|-----------|-------------------|
| `PURCHASE_RECEIVED` | Demande d'achat reçue | system | intervention |
| `HEALTH_THRESHOLD` | Seuil santé atteint | system | intervention |
| `TASK_CREATED` | Tâche créée | system | task |
| `TASK_UPDATED` | Tâche modifiée | system | task |
| `TASK_STATUS` | Changement statut tâche | system | task |
| `TASK_DELETED` | Tâche supprimée | system | task |
| `EQUIPMENT_FAILURE` | Panne équipement | manual | intervention |
| `CLIENT_REQUEST` | Demande client | manual | intervention, task |
| `RECLASSIFICATION` | Reclassification | manual | intervention |
| `TECHNICIAN_UNAVAILABLE` | Technicien indisponible | manual | task |
| `SUPPLIER_DELAY` | Délai fournisseur | manual | purchase_request |
| `PRIORITY_BOOST` | Accélération demandée | manual | intervention, task |
| `RESOURCE_CONSTRAINT` | Contrainte ressource | manual | task, intervention |
| `OTHER` | Autre raison | user | toutes |

> Les raisons de catégorie `system` sont réservées aux mutations automatiques (triggers DB, repositories). Ne pas les utiliser depuis le frontend.

---

## `GET /audit/logs`

Requête fine sur les entrées d'audit.

### Query params

| Param | Type | Description |
|-------|------|-------------|
| `from_dt` | datetime | Début de fenêtre (ISO 8601) |
| `to_dt` | datetime | Fin de fenêtre |
| `entity_type` | string | `intervention`, `request`, `purchase_request`, `task`, `action` |
| `entity_id` | uuid | UUID de l'entité spécifique |
| `reason_code` | string | Filtrer par code raison |
| `exclude_system` | bool | Exclure les mutations système (défaut `false`) |
| `limit` | int | Max 1000, défaut 200 |
| `offset` | int | Pagination |

### Réponse `200`

```json
[
  {
    "id": "uuid",
    "entity_type": "intervention",
    "entity_id": "uuid",
    "decision_type": "status_actual_changed",
    "old_value": { "status_actual": "ouvert" },
    "new_value": { "status_actual": "en_cours" },
    "reason": {
      "id": 4,
      "code": "CLIENT_REQUEST",
      "label": "Demande client",
      "category": "manual",
      "color": "#8b5cf6",
      "description": "Client demande priorité"
    },
    "reason_text": null,
    "changed_by": {
      "id": "uuid-utilisateur",
      "first_name": "Jean",
      "last_name": "DUPONT",
      "initials": "JD"
    },
    "is_system": false,
    "logged_at": "2026-05-12T10:30:00Z"
  }
]
```

---

## `GET /audit/briefing`

Rapport synthétique de toutes les décisions sur une fenêtre temporelle. Usage typique : bilan de prise de poste, réunion de briefing.

### Query params

| Param | Type | Requis | Description |
|-------|------|--------|-------------|
| `from_dt` | datetime | **oui** | Début (ISO 8601) |
| `to_dt` | datetime | **oui** | Fin |
| `exclude_system` | bool | non | Exclure les mutations automatiques (défaut `false`) |

### Réponse `200`

```json
{
  "session_start": "2026-05-12T06:00:00Z",
  "session_end": "2026-05-12T14:00:00Z",
  "duration_minutes": 480.0,
  "decisions": [
    {
      "timestamp": "2026-05-12T08:15:00Z",
      "entity_type": "intervention",
      "entity_id": "uuid",
      "decision_type": "status_actual_changed",
      "from_value": "ouvert",
      "to_value": "en_cours",
      "reason_code": "CLIENT_REQUEST",
      "reason_label": "Demande client",
      "reason_color": "#8b5cf6",
      "reason_text": null,
      "changed_by": "uuid-utilisateur",
      "is_system": false
    }
  ],
  "summary": {
    "total_decisions": 12,
    "by_entity_type": {
      "intervention": 7,
      "task": 3,
      "request": 2
    },
    "by_decision_type": {
      "status_actual_changed": 5,
      "priority_changed": 4,
      "assigned_to_changed": 3
    }
  }
}
```

---

## `POST /audit/log`

Crée manuellement une entrée d'audit pour les cas non interceptés par le middleware (mutations système, scripts de migration, etc.).

### Body

```json
{
  "entity_type": "intervention",
  "entity_id": "uuid",
  "decision_type": "status_actual_changed",
  "old_value": { "status_actual": "ouvert" },
  "new_value": { "status_actual": "en_cours" },
  "reason_code": "CLIENT_REQUEST",
  "reason_text": null
}
```

### Réponse `201`

```json
{ "id": "uuid-du-log-créé" }
```
