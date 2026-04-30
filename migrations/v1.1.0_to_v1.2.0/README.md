# Migration v1.1.0 -> v1.2.0

**Date** : February 2026  
**Auteur** : Quentin

## Description

Add a reference table for equipment classes and link machines to a class (many machines to one class).

## Changes

### New objects

1. Table `equipment_class`
   - `id` UUID primary key
   - `code` unique
   - `label`, `description`

2. Seed data
   - SCIE, EXTRUDEUSE, POMPE, CONVOYEUR

3. Machine relation
   - Column `machine.equipment_class_id`
   - FK `machine_equipment_class_id_fkey`
   - Index on `machine.equipment_class_id`

## Notes

- The FK is created conditionally to allow re-run.
- No data migration required.
