# Guide de création de migrations

Ce guide explique comment créer une nouvelle migration avec vérifications post-migration intégrées.

## Structure d'une migration

```
migrations/
└── vX.X.X_to_vY.Y.Y/
    ├── up.sql              # Script SQL de migration (requis)
    ├── down.sql            # Script SQL de rollback (requis)
    ├── migrate.py          # Script Python avec vérifications (recommandé)
    └── README.md           # Documentation de la migration
```

## Création d'une migration

### 1. Créer le dossier

```bash
mkdir migrations/v1.4.0_to_v1.5.0
```

### 2. Créer les fichiers SQL

**up.sql** - Migration vers la nouvelle version :

```sql
-- Migration vX.X.X -> vY.Y.Y (UP)

CREATE TABLE ma_nouvelle_table (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    nom varchar(100) NOT NULL
);

ALTER TABLE ma_table_existante
ADD COLUMN nouvelle_colonne varchar(50);
```

**down.sql** - Rollback vers l'ancienne version :

```sql
-- Migration vX.X.X -> vY.Y.Y (DOWN)

DROP TABLE IF EXISTS ma_nouvelle_table CASCADE;

ALTER TABLE ma_table_existante
DROP COLUMN IF EXISTS nouvelle_colonne;
```

### 3. Créer le fichier migrate.py (optionnel mais recommandé)

Copiez le template :

```bash
cp migrations/migrate_template.py migrations/v1.4.0_to_v1.5.0/migrate.py
```

Puis adaptez les fonctions **verify_up()** et **verify_down()** :

```python
def verify_up() -> dict:
    """Vérifie que la migration UP a été correctement appliquée."""
    errors = []

    # Vérifier les tables créées
    print("\n✓ Vérification des tables créées :")
    if not table_exists('ma_nouvelle_table'):
        errors.append("Table ma_nouvelle_table non créée")
        print("  ✗ ma_nouvelle_table")
    else:
        print("  ✓ ma_nouvelle_table")

    # Vérifier les colonnes ajoutées
    print("\n✓ Vérification des colonnes ajoutées :")
    if not column_exists('ma_table_existante', 'nouvelle_colonne'):
        errors.append("Colonne nouvelle_colonne non ajoutée")
        print("  ✗ ma_table_existante.nouvelle_colonne")
    else:
        print("  ✓ ma_table_existante.nouvelle_colonne")

    return {
        'success': len(errors) == 0,
        'errors': errors
    }

def verify_down() -> dict:
    """Vérifie que le rollback DOWN a été correctement effectué."""
    errors = []

    # Vérifier les tables supprimées
    print("\n✓ Vérification des tables supprimées :")
    if table_exists('ma_nouvelle_table'):
        errors.append("Table ma_nouvelle_table non supprimée")
        print("  ✗ ma_nouvelle_table (existe encore)")
    else:
        print("  ✓ ma_nouvelle_table (supprimée)")

    # Vérifier les colonnes supprimées
    print("\n✓ Vérification des colonnes supprimées :")
    if column_exists('ma_table_existante', 'nouvelle_colonne'):
        errors.append("Colonne nouvelle_colonne non supprimée")
        print("  ✗ ma_table_existante.nouvelle_colonne (existe encore)")
    else:
        print("  ✓ ma_table_existante.nouvelle_colonne (supprimée)")

    return {
        'success': len(errors) == 0,
        'errors': errors
    }
```

### 4. Tester les vérifications en standalone

```bash
python migrations/v1.4.0_to_v1.5.0/migrate.py
```

Cela affichera les résultats de verify_up() et verify_down() sans modifier la base.

### 5. Exécuter la migration

```bash
cd scripts
python migration_runner.py --version v1.4.0_to_v1.5.0 --direction up
```

Le système :

1. Exécute le SQL (up.sql)
2. Exécute migrate_up() si présent
3. Exécute verify_up() automatiquement
4. Affiche les résultats des vérifications

### 6. Rollback (si nécessaire)

```bash
python migration_runner.py --version v1.4.0_to_v1.5.0 --direction down
```

## Fonctions utilitaires disponibles

Le template fournit ces fonctions :

```python
table_exists(table_name: str) -> bool
column_exists(table_name: str, column_name: str) -> bool
constraint_exists(table_name: str, constraint_name: str) -> bool
index_exists(index_name: str) -> bool
```

## Migrations avec code Python

Si vous avez besoin de code Python pour transformer des données :

```python
def migrate_up() -> None:
    """Code Python exécuté après up.sql"""
    with get_cursor() as cursor:
        # Exemple: convertir des données
        cursor.execute("SELECT id, old_field FROM ma_table")
        rows = cursor.fetchall()

        for row_id, old_value in rows:
            new_value = transform_data(old_value)
            cursor.execute(
                "UPDATE ma_table SET new_field = %s WHERE id = %s",
                (new_value, row_id)
            )

def migrate_down() -> None:
    """Code Python exécuté après down.sql"""
    # Restaurer l'état précédent si nécessaire
    pass
```

## Exemple complet

Voir :

- **migrations/v1.3.0_to_v1.4.0/** - Migration avec vérifications complètes
- **migrations/migrate_template.py** - Template avec tous les exemples
- **migrations/v1.2.1_to_v1.3.0/** - Migration avec code Python complexe

## Bonnes pratiques

1. ✅ **Toujours créer un down.sql** - Prévoyez le rollback dès le début
2. ✅ **Tester en local** - Exécutez up puis down en local avant prod
3. ✅ **Vérifications complètes** - Vérifiez tables, colonnes, index, contraintes
4. ✅ **Backup avant migration** - Utilisez `scripts/db_backup.py`
5. ✅ **Documentation** - Ajoutez un README.md dans le dossier de migration
6. ✅ **Idempotence** - Les migrations doivent être ré-exécutables (IF EXISTS, etc.)
7. ✅ **Transactions** - Groupez les opérations SQL dans BEGIN/COMMIT

## Commandes utiles

```bash
# Lister les migrations
python migration_runner.py --list

# Exécuter une migration
python migration_runner.py --version vX.X.X_to_vY.Y.Y --direction up

# Rollback
python migration_runner.py --version vX.X.X_to_vY.Y.Y --direction down

# Forcer une ré-exécution
python migration_runner.py --version vX.X.X_to_vY.Y.Y --direction up --force

# Backup de la base avant migration
python db_backup.py
```
