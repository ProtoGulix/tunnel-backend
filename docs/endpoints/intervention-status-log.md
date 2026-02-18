# Intervention Status Log

Historique des changements de statut des interventions. Chaque entrée trace la transition d'un statut à un autre, avec le technicien et la date.

> Voir aussi : [Interventions](interventions.md) | [Intervention Status](intervention-status.md)

---

## `GET /intervention-status-log`

Liste les logs de changement de statut.

### Query params

| Param | Type | Défaut | Description |
|---|---|---|---|
| `intervention_id` | uuid | — | Filtrer par intervention |
| `skip` | int | 0 | Offset |
| `limit` | int | 100 | Max: 1000 |

### Réponse `200`

Tableau trié par date DESC.

---

## `GET /intervention-status-log/{id}`

Détail d'un log de changement de statut.

### Réponse `200` — InterventionStatusLogOut

```json
{
  "id": "uuid",
  "intervention_id": "uuid",
  "status_from": "ouvert",
  "status_to": "en_cours",
  "status_from_detail": {
    "id": "uuid",
    "code": "ouvert",
    "label": "Ouvert",
    "color": "#22c55e",
    "value": 1
  },
  "status_to_detail": {
    "id": "uuid",
    "code": "en_cours",
    "label": "En cours",
    "color": "#3b82f6",
    "value": 2
  },
  "technician_id": "uuid",
  "date": "2026-01-13T08:30:00",
  "notes": "Prise en charge par QC"
}
```

---

## `POST /intervention-status-log`

Crée un changement de statut.

### Entrée

```json
{
  "intervention_id": "5ecf60d5-8471-4739-8ba8-0fdad7b51781",
  "status_from": "ouvert",
  "status_to": "en_cours",
  "technician_id": "a1b2c3d4-...",
  "date": "2026-01-13T08:30:00",
  "notes": "Prise en charge par QC"
}
```

| Champ | Type | Requis | Description |
|---|---|---|---|
| `intervention_id` | uuid | oui | Intervention concernée |
| `status_from` | string | non | Doit correspondre au statut actuel (null pour le premier changement) |
| `status_to` | string | oui | Nouveau statut |
| `technician_id` | uuid | oui | Technicien responsable |
| `date` | datetime | oui | Date du changement |
| `notes` | string | non | Notes (HTML nettoyé) |

### Règles métier

- `status_from` doit correspondre au `status_actual` de l'intervention (sauf si null pour le premier changement)
- Toutes les transitions de statut sont autorisées
- Un trigger base de données met automatiquement à jour `intervention.status_actual` avec `status_to`

### Réponse `201`

Log complet avec détails enrichis des statuts.
