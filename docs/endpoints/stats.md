# Stats

Endpoints d'analyse et de pilotage de la maintenance. Certains sont en BETA.

> Voir aussi : [Interventions](interventions.md) | [Equipement Classes](equipement-class.md) | [Complexity Factors](complexity-factors.md)

---

## `GET /stats/service-status`

Indicateurs de santé du service maintenance : charge, fragmentation, capacité de pilotage, top causes.

### Query params

| Param | Type | Défaut |
|---|---|---|
| `start_date` | date | 3 mois avant |
| `end_date` | date | aujourd'hui |

### Réponse `200`

```json
{
  "period": { "start_date": "2025-11-15", "end_date": "2026-02-15", "days": 92 },
  "capacity": {
    "total_hours": 450.5,
    "capacity_hours": 600,
    "charge_percent": 75.1,
    "status": { "color": "orange", "text": "Charge élevée" }
  },
  "breakdown": {
    "prod_hours": 200.0,
    "dep_hours": 150.5,
    "pilot_hours": 50.0,
    "frag_hours": 50.0,
    "total_hours": 450.5
  },
  "fragmentation": {
    "action_count": 340,
    "short_action_count": 85,
    "short_action_percent": 25.0,
    "frag_percent": 11.1,
    "status": { "color": "green", "text": "OK" },
    "top_causes": [
      { "name": "Nettoyage", "total_hours": 15.0, "action_count": 60, "percent": 30.0 }
    ]
  },
  "pilotage": {
    "pilot_hours": 50.0,
    "pilot_percent": 11.1,
    "status": { "color": "green", "text": "OK" }
  },
  "site_consumption": [
    {
      "site_name": "Atelier principal",
      "total_hours": 300.0,
      "frag_hours": 35.0,
      "percent_total": 66.6,
      "percent_frag": 11.7
    }
  ]
}
```

---

## `GET /stats/charge-technique` [BETA]

Analyse de la charge technique par classe d'équipement. Identifie le dépannage évitable vs subi.

### Query params

| Param | Type | Défaut | Description |
|---|---|---|---|
| `start_date` | date | 3 mois avant | Début de période |
| `end_date` | date | aujourd'hui | Fin de période |
| `period_type` | string | `custom` | Découpage : `month`, `week`, `quarter`, `custom` |

### Règles métier

- Analyse **par classe d'équipement** (jamais par machine, jamais par technicien)
- Une action DEP est **évitable** si :
  - `complexity_factor IS NOT NULL` (facteur renseigné = signal)
  - OU action répétée >= 3 fois (même `action_subcategory` + même `equipement_class`) sur la période
- Taux de dépannage évitable :
  - **< 20%** (vert) : Faible levier
  - **20-40%** (orange) : Levier de standardisation
  - **> 40%** (rouge) : Problème systémique

### Réponse `200`

```json
{
  "params": { "start_date": "2025-11-15", "end_date": "2026-02-15", "period_type": "custom" },
  "guide": {
    "objectif": "Identifier où passe le temps maintenance et quelle part est récupérable",
    "seuils_taux_evitable": [
      { "min": 0, "max": 20, "color": "green", "label": "Faible levier", "action": "..." },
      { "min": 20, "max": 40, "color": "orange", "label": "Levier de standardisation", "action": "..." },
      { "min": 40, "max": null, "color": "red", "label": "Problème systémique", "action": "..." }
    ],
    "actions_par_categorie": [
      { "category": "Logistique", "color": "#3b82f6", "action": "Optimiser les flux de pièces" }
    ]
  },
  "periods": [
    {
      "period": { "start_date": "2025-11-15", "end_date": "2026-02-15", "days": 92 },
      "charges": {
        "charge_totale": 450.5,
        "charge_depannage": 150.5,
        "charge_constructive": 300.0,
        "charge_depannage_evitable": 45.0,
        "charge_depannage_subi": 105.5
      },
      "taux_depannage_evitable": {
        "taux": 29.9,
        "status": { "color": "orange", "text": "Levier de standardisation" }
      },
      "cause_breakdown": [
        { "code": "PCE", "label": "Pièce", "category": "Logistique", "hours": 20.0, "action_count": 12, "percent": 44.4 }
      ],
      "by_equipement_class": [
        {
          "equipement_class_id": "uuid",
          "equipement_class_code": "SCIE",
          "equipement_class_label": "Scie",
          "charge_totale": 120.0,
          "charge_depannage": 60.0,
          "charge_constructive": 60.0,
          "charge_depannage_evitable": 25.0,
          "taux_depannage_evitable": 41.7,
          "status": { "color": "red", "text": "Problème systémique" },
          "evitable_breakdown": {
            "hours_with_factor": 15.0,
            "hours_systemic": 18.0,
            "hours_both": 8.0,
            "total_evitable": 25.0
          },
          "explanation": "25h évitables sur 60h de dépannage...",
          "top_causes": [
            { "code": "PCE", "label": "Pièce", "category": "Logistique", "hours": 15.0, "percent": 60.0 }
          ],
          "recommended_action": "Créer un stock tampon de pièces pour les scies"
        }
      ]
    }
  ]
}
```

---

## `GET /stats/anomalies-saisie` [BETA]

Détection des anomalies de saisie des actions d'intervention. 6 types de détection.

### Query params

| Param | Type | Défaut |
|---|---|---|
| `start_date` | date | 3 mois avant |
| `end_date` | date | aujourd'hui |

### Types d'anomalies

| Type | Sévérité | Détection |
|---|---|---|
| `too_repetitive` | high/medium | Même sous-catégorie + même machine > 3 fois/mois |
| `too_fragmented` | high/medium | Actions courtes (< 1h) apparaissant 5+ fois |
| `too_long_for_category` | high/medium | Actions > 4h sur catégories rapides (BAT_NET, BAT_RAN, etc.) |
| `bad_classification` | high/medium | Actions BAT_NET avec mots-clés techniques suspects |
| `back_to_back` | high/medium | Même tech + même intervention, < 24h d'écart |
| `low_value_high_load` | high/medium | Catégories faible valeur avec > 30h cumulées |

### Réponse `200`

```json
{
  "params": { "start_date": "2025-11-15", "end_date": "2026-02-15" },
  "summary": {
    "total_anomalies": 15,
    "by_type": { "too_repetitive": 5, "too_fragmented": 3, "too_long_for_category": 2, "bad_classification": 1, "back_to_back": 3, "low_value_high_load": 1 },
    "by_severity": { "high": 6, "medium": 9 }
  },
  "anomalies": {
    "too_repetitive": [
      {
        "category": "DEP_REM", "categoryName": "Remplacement pièce",
        "machine": "Scie 01", "machineId": "uuid",
        "month": "2026-01", "count": 5, "interventionCount": 3,
        "severity": "high",
        "message": "5 actions DEP_REM sur Scie 01 en janvier 2026"
      }
    ]
  },
  "config": {
    "thresholds": {
      "repetitive": { "monthly_count": 3, "high_severity_count": 6 },
      "fragmented": { "max_duration": 1.0, "min_occurrences": 5, "high_severity_count": 10 },
      "too_long": { "max_duration": 4.0, "high_severity_duration": 8.0 },
      "bad_classification": { "high_severity_keywords": 2 },
      "back_to_back": { "max_days_diff": 1.0, "high_severity_days": 0.5 },
      "low_value_high_load": { "min_total_hours": 30.0, "high_severity_hours": 60.0 }
    },
    "simple_categories": ["BAT_NET", "BAT_RAN", "BAT_DIV", "LOG_MAG", "LOG_REC", "LOG_INV"],
    "low_value_categories": ["BAT_NET", "BAT_RAN", "BAT_DIV", "LOG_MAG", "LOG_REC"],
    "suspicious_keywords": ["mécanique", "hydraulique", "électrique", "..."]
  }
}
```

---

## `GET /stats/qualite-donnees`

Détection des problèmes de complétude et cohérence des données. 13 règles sur 4 entités.

### Query params

| Param | Type | Description |
|---|---|---|
| `severite` | string | Filtrer : `high`, `medium` |
| `entite` | string | Filtrer : `intervention_action`, `intervention`, `stock_item`, `purchase_request` |
| `code` | string | Filtrer par code anomalie spécifique |

### Règles de détection

| Entité | Code | Sévérité | Description |
|---|---|---|---|
| intervention_action | `action_time_null` | high | Temps non saisi |
| intervention_action | `action_complexity_sans_facteur` | high | Complexité sans facteur |
| intervention_action | `action_subcategory_null` | high | Sous-catégorie manquante |
| intervention_action | `action_tech_null` | medium | Technicien manquant |
| intervention_action | `action_description_vide` | medium | Description vide |
| intervention_action | `action_time_suspect` | medium | Temps > 8h suspect |
| intervention_action | `action_sur_intervention_fermee` | high | Action après fermeture |
| intervention | `intervention_fermee_sans_action` | high | Fermée sans action |
| intervention | `intervention_sans_type` | medium | Sans type |
| intervention | `intervention_en_cours_inactive` | medium | En cours > 14 jours |
| stock_item | `stock_sans_seuil_min` | medium | Sans seuil minimum |
| stock_item | `stock_sans_fournisseur` | medium | Sans fournisseur |
| purchase_request | `demande_sans_stock_item` | medium | Sans article stock lié |

### Réponse `200`

```json
{
  "total": 42,
  "par_severite": { "high": 12, "medium": 30 },
  "problemes": [
    {
      "code": "action_time_null",
      "severite": "high",
      "entite": "intervention_action",
      "entite_id": "uuid",
      "message": "Temps non saisi sur l'action",
      "contexte": {
        "intervention_id": "uuid",
        "intervention_code": "CN001-REA-20260113-QC",
        "created_at": "2026-01-13T14:30:00",
        "stock_item_ref": null,
        "stock_item_name": null,
        "purchase_request_id": null
      }
    }
  ]
}
```

> Tri : high d'abord, puis medium, puis par entité, puis `created_at` DESC.
