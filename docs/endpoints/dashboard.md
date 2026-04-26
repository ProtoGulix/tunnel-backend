# Dashboard

Compteurs pour les badges du menu. Endpoint instrumental public, optimisé pour affichage des indicateurs de sections principales sans authentification.

## `GET /dashboard/summary`

**Auth** : Public

Retourne un résumé des comptages de chaque section du menu. Conçu pour être cachable côté frontend et mis à jour à intervalles réguliers.

### Réponse `200`

```json
{
  "interventions": {
    "open": 12,
    "label": "Interventions"
  },
  "tasks": {
    "pending": 21,
    "label": "Tâches"
  },
  "equipements": {
    "total": 337,
    "label": "Équipements"
  },
  "preventive": {
    "plans_active": 1,
    "pending": 0,
    "label": "Préventif"
  },
  "stock": {
    "items": 104,
    "label": "Stock"
  },
  "purchase_requests": {
    "open": 22,
    "label": "Demandes d'achat"
  },
  "suppliers": {
    "total": 13,
    "label": "Fournisseurs"
  }
}
```

## Schema de réponse

| Champ                     | Contenu                                                     | Notes                               |
| ------------------------- | ----------------------------------------------------------- | ----------------------------------- |
| `interventions.open`      | Nombre d'interventions au statut "ouvert"                   | Utiliser pour badge "Interventions" |
| `tasks.pending`           | Nombre de tâches en "todo" ou "in_progress"                 | Utiliser pour badge "Tâches"        |
| `equipements.total`       | Total d'équipements en base                                 | Utiliser pour badge "Équipements"   |
| `preventive.plans_active` | Plans préventifs actifs                                     | Utiliser pour affichage plan actif  |
| `preventive.pending`      | Occurrences préventives en attente (générées non acceptées) | Avertissement si > 0                |
| `stock.items`             | Total d'articles en stock                                   | Utiliser pour badge "Stock"         |
| `purchase_requests.open`  | Demandes d'achat aux statuts nouvelle/en_attente/acceptee   | Utiliser pour badge "Demandes"      |
| `suppliers.total`         | Total de fournisseurs                                       | Utiliser pour badge "Fournisseurs"  |

Chaque section contient un champ `label` pour affichage cohérent en UI.

## Exemples d'utilisation

### Frontend (React/Vue)

```javascript
// Récupérer les compteurs et mettre à jour les badges
fetch("/dashboard/summary")
  .then((r) => r.json())
  .then((data) => {
    document.querySelector('[data-badge="tasks"]').textContent =
      data.tasks.pending;
    document.querySelector('[data-badge="interventions"]').textContent =
      data.interventions.open;
    document.querySelector('[data-badge="stock"]').textContent =
      data.stock.items;
  });

// Rafraîchir toutes les 30 secondes
setInterval(async () => {
  const summary = await fetch("/dashboard/summary").then((r) => r.json());
  updateBadges(summary);
}, 30000);
```

### Conditions d'affichage badge

- **Interventions** : Afficher badge si `open > 0`
- **Tâches** : Afficher badge si `pending > 0` (orange ou rouge si > 5)
- **Demandes d'achat** : Afficher badge si `open > 0`
- **Préventif** : Avertissement si `pending > 0` (peut indiquer des occurrences à traiter)

## Cas d'usage

1. **Initialisation page** : Appel au chargement initial pour afficher les badges
2. **Polling** : Mise à jour périodique (30-60s) pour refléter l'état en temps (quasi) réel
3. **Websocket ou SSE** : Push côté serveur vers clients connectés si rechargement temps réel souhaité
4. **Cache local** : Stocker la réponse en localStorage avec TTL pour réduire appels API
