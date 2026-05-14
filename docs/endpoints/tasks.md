# ~~Endpoint `/tasks/workspace`~~ — Supprimé

> **⚠️ Endpoint supprimé en v3.6.0 (2026-05-14)**
>
> L'endpoint `/tasks/workspace` n'existe plus. Utiliser [`GET /intervention-tasks`](intervention-tasks.md) à la place.

## Migration

| Ancien paramètre | Nouveau paramètre |
|-----------------|-------------------|
| `assignee_id`   | `assigned_to`     |
| `include_closed` | `include_done`   |

Les tâches ne sont plus groupées par intervention dans la réponse. Le front doit regrouper par `intervention_id` si nécessaire, ou utiliser `GET /interventions?include=stats` pour les compteurs agrégés par intervention.

> Voir : [Intervention Tasks](intervention-tasks.md) | [Interventions — stats](interventions.md#get-interventions)
