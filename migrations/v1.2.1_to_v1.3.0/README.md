# Migration v1.2.1 → v1.3.0

## Objectif

Remplacer le champ JSON `intervention_action.complexity_anotation` par une relation propre avec la table `complexity_factor`.

## Changements

### Schéma

1. **Nouvelle table de liaison** : `intervention_action_complexity_factor`
   - Permet de lier plusieurs facteurs de complexité à une action
   - Clés étrangères vers `intervention_action` et `complexity_factor`
   - Contrainte d'unicité pour éviter les doublons

2. **Champ déprécié** : `intervention_action.complexity_anotation`
   - Marqué comme DEPRECATED dans les commentaires
   - Conservé temporairement pour rétrocompatibilité
   - Sera supprimé dans une future version

### Données

La migration Python (`migrate.py`) effectue :

1. **Extraction** des clés de complexité depuis les formats JSON existants :
   - `{"key": "PCE", "collection": "complexity_factor"}` → `PCE`
   - `{"AUT": true}` → `AUT`
   - `{"PCE": true, "AUT": true}` → `PCE`, `AUT`

2. **Insertion** des `complexity_factor` manquants (catégorie: `imported`)

3. **Migration** des données vers la table de liaison

## Exécution

```bash
# Depuis le dossier scripts/
cd scripts

# Installer les dépendances
pip install psycopg2-binary python-dotenv

# Vérifier la connexion
python db_connection.py

# Exécuter la migration
python migration_runner.py --version v1.2.1_to_v1.3.0 --direction up

# Pour rollback
python migration_runner.py --version v1.2.1_to_v1.3.0 --direction down
```

## Analyse préalable

Pour voir les statistiques avant migration :

```bash
cd migrations/v1.2.1_to_v1.3.0
python migrate.py
```

Cela affichera :

- Nombre d'annotations à migrer
- Clés uniques trouvées
- Répartition des formats JSON

## Rétrocompatibilité

Le champ `complexity_anotation` est conservé. L'application peut continuer à l'utiliser
pendant la transition vers la nouvelle structure.

## Rollback

Le rollback (`down.sql` + `migrate_down()`) :

- Supprime la table de liaison
- Restaure le commentaire d'origine
- **Ne supprime pas** les `complexity_factor` ajoutés (données de référence)
