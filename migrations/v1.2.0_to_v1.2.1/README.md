# Migration v1.2.0 -> v1.2.1

**Date** : February 2026  
**Auteur** : Quentin

## Description

Align the `machine` table with the production DDL.

## Changes

1. Column adjustments
   - `code` length to 50
   - `name` length to 200 and NOT NULL
   - `no_machine` to INTEGER
   - `affectation` to VARCHAR(255)
   - `fabricant` and `numero_serie` to VARCHAR

2. Remove deprecated column
   - Drop `machine.type_equipement`

3. Add FK
   - `machine_equipement_mere_foreign` on `equipement_mere`

## Notes

- Null `name` values are backfilled from `code` before applying NOT NULL.
