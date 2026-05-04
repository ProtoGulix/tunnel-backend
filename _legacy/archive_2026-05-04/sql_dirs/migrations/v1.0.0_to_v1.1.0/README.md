# Migration v1.0.0 → v1.1.0

**Date** : Février 2026  
**Auteur** : Quentin

## 📋 Description

Ajout de la fonction `derive_pr_status()` pour calculer automatiquement le statut d'une demande d'achat en fonction de l'état des lignes de commande fournisseur associées.

## 🎯 Objectif

Permettre le calcul dynamique du statut d'une purchase request basé sur :

- Les devis reçus (`quote_received`)
- Les lignes sélectionnées (`is_selected`)
- Les réceptions partielles ou complètes (`quantity_received`)

## ✨ Changements

### Nouveautés

1. **Fonction `derive_pr_status(pr_id UUID)`**
   - Retourne le statut calculé : `OPEN`, `QUOTED`, `ORDERED`, `PARTIAL`, `RECEIVED`
   - Logique métier basée sur l'état des lignes de commande

2. **Index d'optimisation**
   - `idx_solpr_pr_id` : Accès rapide par purchase_request_id
   - `idx_sol_quote_received` : Filtre sur devis reçus
   - `idx_sol_is_selected` : Filtre sur lignes sélectionnées

### Statuts possibles

| Statut     | Description                                         |
| ---------- | --------------------------------------------------- |
| `OPEN`     | Aucun devis reçu                                    |
| `QUOTED`   | Au moins un devis reçu, rien de sélectionné         |
| `ORDERED`  | Au moins une ligne sélectionnée, rien de reçu       |
| `PARTIAL`  | Certaines lignes sélectionnées partiellement reçues |
| `RECEIVED` | Toutes les lignes sélectionnées entièrement reçues  |

## 🔧 Impact

### Backend

- Nouvelle fonction disponible pour calculer le statut en temps réel
- À utiliser dans les endpoints qui retournent des purchase requests

### Frontend

- Aucun changement immédiat
- Le statut peut être calculé côté serveur avant l'envoi au frontend

## 📝 Utilisation

```sql
-- Exemple d'utilisation
SELECT
    pr.id,
    pr.description,
    derive_pr_status(pr.id) AS status
FROM purchase_request pr;
```

## ⚠️ Notes

- Les index sont créés avec `IF NOT EXISTS` pour éviter les erreurs en cas de réexécution
- La fonction peut être appelée à la demande ou intégrée dans une vue
- Pas de migration de données nécessaire
