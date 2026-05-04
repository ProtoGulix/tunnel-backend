# Migration v1.5.0 → v1.6.0

**Date** : 10 mars 2026  
**Auteur** : Quentin  
**Type** : Correctif schéma

## Description

Suppression des colonnes redondantes dans `purchase_request`, accumulées lors des itérations successives du schéma.

## Colonnes supprimées

| Colonne supprimée | Doublon conservé | Raison |
|---|---|---|
| `requester_name` | `requested_by` | `requested_by` est le champ effectivement utilisé côté applicatif |
| `quantity_requested` | `quantity` | `quantity` porte la contrainte `NOT NULL` et le `CHECK (quantity > 0)` |
| `urgent` (boolean) | `urgency` (varchar) | `urgency` est plus expressif (normal / high / critical) |

## Sécurité données

Avant la suppression de `requester_name`, un `UPDATE` copie les valeurs non nulles vers `requested_by` pour éviter toute perte si des lignes avaient été insérées via l'ancien champ.

## Rollback

Le `down.sql` recrée les trois colonnes et réhydrate `requester_name` depuis `requested_by`.
