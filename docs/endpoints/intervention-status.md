# Intervention Status

Table de référence des statuts d'intervention disponibles en base de données.

---

## `GET /intervention_status`

Liste tous les statuts disponibles.

### Réponse `200`

```json
[
  {
    "id": "uuid",
    "code": "ouvert",
    "label": "Ouvert",
    "color": "#22c55e",
    "value": 1
  },
  {
    "id": "uuid",
    "code": "en_cours",
    "label": "En cours",
    "color": "#3b82f6",
    "value": 2
  }
]
```
