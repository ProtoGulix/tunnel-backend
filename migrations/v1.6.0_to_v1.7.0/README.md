# Migration v1.6.0 → v1.7.0

**Date** : 11 mars 2026  
**Auteur** : Quentin  
**Type** : Mineure

## Description

Introduction du module **Demandes d'Intervention**. Un acteur externe (operateur, service, demandeur public) peut soumettre une demande de maintenance qui suit un cycle de vie traçé avant d'être convertie en intervention GMAO.

## Architecture

```
📁 02_ref/ (Référentiels)
└── request_status_ref         → Statuts de demande (nouvelle → acceptee/rejetee → cloturee)

📁 01_core/ (Transactionnel)
├── intervention_request       → Demande principale, liée à machine + intervention
└── request_status_log         → Historique complet des transitions de statut

📁 05_triggers/ (Fonctions & Triggers)
├── fn_generate_request_code   → Code DI-YYYY-NNNN (BEFORE INSERT)
├── fn_init_request_status_log → Insertion initiale du log + statut (AFTER INSERT)
├── fn_apply_request_status    → Synchronise statut depuis log (AFTER INSERT log)
└── fn_log_request_status_change → Trace les transitions applicatives (AFTER UPDATE statut)
```

## Nouvelles tables

### `request_status_ref` (02_ref)

Référentiel des statuts de demande d'intervention.

| Colonne      | Type                | Description             |
| ------------ | ------------------- | ----------------------- |
| `code`       | VARCHAR(50) PK      | Identifiant technique   |
| `label`      | TEXT NOT NULL       | Libellé affiché         |
| `color`      | VARCHAR(7) NOT NULL | Couleur hexadécimale UI |
| `sort_order` | INTEGER NOT NULL    | Ordre d'affichage       |

**Données initiales :** `nouvelle`, `en_attente`, `acceptee`, `rejetee`, `cloturee`

### `intervention_request` (01_core)

Table principale des demandes.

| Colonne                     | Type                         | Description                          |
| --------------------------- | ---------------------------- | ------------------------------------ |
| `id`                        | UUID PK                      | Identifiant unique                   |
| `code`                      | VARCHAR(255) UNIQUE NOT NULL | DI-YYYY-NNNN (trigger)               |
| `machine_id`                | UUID FK NOT NULL             | Machine concernée                    |
| `demandeur_nom`             | TEXT NOT NULL                | Nom du demandeur                     |
| `demandeur_service`         | TEXT                         | Service émetteur (nullable)          |
| `description`               | TEXT NOT NULL                | Description du problème              |
| `statut`                    | VARCHAR(50) FK NOT NULL      | Statut courant (via log)             |
| `intervention_id`           | UUID FK UNIQUE               | Intervention créée depuis la demande |
| `created_at` / `updated_at` | TIMESTAMPTZ                  | Horodatage convention Tunnel         |

> `statut` est positionné exclusivement par trigger via `request_status_log`. Il n'a pas de `DEFAULT`.  
> `motif_rejet` n'existe pas en colonne : il vit dans `request_status_log.notes` lors de la transition vers `rejetee`.

### `request_status_log` (01_core)

Log immuable de toutes les transitions de statut.

| Colonne       | Type                    | Description                                 |
| ------------- | ----------------------- | ------------------------------------------- |
| `id`          | UUID PK                 | Identifiant unique                          |
| `request_id`  | UUID FK NOT NULL        | Demande concernée (CASCADE DELETE)          |
| `status_from` | VARCHAR(50) FK          | Statut précédent (NULL à la création)       |
| `status_to`   | VARCHAR(50) FK NOT NULL | Nouveau statut                              |
| `changed_by`  | UUID                    | UUID Directus (nullable = demande publique) |
| `notes`       | TEXT                    | Commentaire libre (motif rejet, etc.)       |
| `date`        | TIMESTAMPTZ NOT NULL    | Horodatage de la transition                 |

## Triggers

### Cycle vie complet (INSERT demande)

```
INSERT intervention_request
  → trg_request_code            (BEFORE)  : génère DI-YYYY-NNNN
  → trg_init_request_status_log (AFTER)   : insère log {NULL → 'nouvelle'}
      → trg_apply_request_status (AFTER log) : SET statut = 'nouvelle'
         (trg_log_request_status_change désactivé via flag session)
```

### Transition applicative (UPDATE statut)

```
UPDATE intervention_request SET statut = 'acceptee'
  → trg_log_request_status_change (AFTER)
      : vérifie cohérence status_from vs dernier log
      : insère log {old → new}
          → trg_apply_request_status (AFTER log) : confirme SET statut
```

### Anti-boucle

Le flag de session `app.skip_request_status_log` (via `set_config`) court-circuite `trg_log_request_status_change` pendant l'initialisation interne, évitant la boucle infinie :  
`apply_status → UPDATE statut → log_status_change → apply_status → …`

## Rollback

```bash
python scripts/migration_runner.py down v1.6.0_to_v1.7.0
```

Le `down.sql` supprime dans l'ordre : triggers → fonctions → `request_status_log` → `intervention_request` → `request_status_ref`.
