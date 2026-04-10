# Equipement Statuts

Référentiel des statuts du cycle de vie d'un équipement (En service, À l'arrêt, Rebut, etc.).
Le statut d'un équipement détermine notamment si des interventions peuvent lui être créées.

> Voir aussi : [Equipements](equipements.md) | [Equipement Classes](equipement-class.md)

---

## `GET /equipement-statuts`

Liste tous les statuts actifs (`est_actif = true`), triés par `ordre_affichage` ASC.

### Auth

JWT requis.

### Réponse `200`

```json
[
  {
    "id": 1,
    "code": "EN_PROJET",
    "label": "En projet",
    "interventions": false,
    "couleur": "#8B5CF6"
  },
  {
    "id": 2,
    "code": "EN_CONSTRUCTION",
    "label": "En construction",
    "interventions": true,
    "couleur": "#F59E0B"
  },
  {
    "id": 3,
    "code": "EN_SERVICE",
    "label": "En service",
    "interventions": true,
    "couleur": "#10B981"
  },
  {
    "id": 4,
    "code": "ARRET",
    "label": "À l'arrêt",
    "interventions": true,
    "couleur": "#EF4444"
  },
  {
    "id": 5,
    "code": "REBUT",
    "label": "Rebut",
    "interventions": false,
    "couleur": "#6B7280"
  }
]
```

### Champs

| Champ           | Type         | Description                                                                  |
| --------------- | ------------ | ---------------------------------------------------------------------------- |
| `id`            | int          | Identifiant technique                                                        |
| `code`          | string       | Code unique (ex : `EN_SERVICE`)                                              |
| `label`         | string       | Libellé affiché dans l'interface                                             |
| `interventions` | bool         | `true` si des interventions peuvent être créées sur un équipement ce statut |
| `couleur`       | string\|null | Code couleur hexadécimal pour les badges UI (ex : `#10B981`)                 |

> Seuls les statuts `est_actif = true` sont retournés. Les statuts désactivés ne sont pas exposés par l'API.

---

## Règle métier — création bloquée

`POST /interventions` et `POST /intervention-requests` vérifient le statut de l'équipement cible avant insertion.

Si `interventions = false` sur le statut de l'équipement → réponse `422` :

```json
{ "detail": "equipement_statut_bloque" }
```

Statuts bloquants par défaut : `EN_PROJET`, `REBUT`, `INCONNU`.

> Si l'équipement n'a pas de statut assigné (`statut = null`), la création est autorisée (compatibilité ascendante).
