# Journal des mises à jour de l'API

Toutes les modifications importantes de l'API sont documentées ici.

## [1.1.1] - 29 janvier 2026

### Corrections

- **Support du format de date standard**: Correction de la validation Pydantic pour accepter le format date "YYYY-MM-DD"
  - Utilisation de `Field(default=None)` pour tous les champs optionnels (compatibilité Pydantic v2)
  - Les schémas `InterventionActionIn` et `InterventionStatusLogIn` acceptent maintenant correctement les dates au format "YYYY-MM-DD"
  - Le validateur centralisé `validate_date()` convertit automatiquement les strings en datetime
  - Fix: Erreur "Input should be a valid datetime, invalid datetime separator" résolue

### Améliorations techniques

- Migration complète vers Pydantic v2 avec `Field()` pour les valeurs par défaut
- Tous les schémas utilisent `from_attributes = True` (syntaxe Pydantic v2)
- Meilleure gestion des champs optionnels dans tous les schémas de l'API

---

## [1.1.0] - 27 janvier 2026

### Nouveautés

- **Historique des changements de statut**: Les interventions incluent maintenant leur historique complet de changements de statut via `status_logs`
  - `GET /interventions/{id}` retourne automatiquement tous les changements de statut avec détails enrichis
  - Chaque log inclut le statut source, le statut destination, le technicien, la date et les notes
  - Les détails des statuts sont enrichis avec les informations de la table de référence (code, label, couleur)
- **Filtre d'impression**: Nouveau paramètre `printed` pour `GET /interventions`
  - Permet de filtrer les interventions imprimées (`printed=true`) ou non imprimées (`printed=false`)
  - Omission du paramètre retourne toutes les interventions (comportement par défaut)

### Corrections

- **Validation des status logs**: Correction des erreurs de validation Pydantic
  - `technician_id` est maintenant optionnel (peut être NULL en base de données)
  - Le champ `value` des statuts est correctement converti en integer ou NULL (gère les valeurs textuelles en base)
- **Dépendance circulaire**: Résolution de l'import circulaire entre `InterventionRepository` et `InterventionStatusLogValidator`
  - Utilisation d'un import lazy dans le validator pour éviter le blocage au démarrage

### Améliorations techniques

- Ajout de la méthode `_safe_int_value()` pour gérer proprement la conversion des valeurs de statut
- Les status logs sont chargés automatiquement pour les détails d'intervention mais pas dans les listes (optimisation performance)
- Schéma `InterventionOut` étendu avec le champ `status_logs: List[InterventionStatusLogOut]`
- **Validation des dates**: Nouveau validateur centralisé `validate_date()` dans `api/utils/validators.py`
  - Rejette les dates invalides (ex: 2026-01-36)
  - Vérifie la plage d'années (1900-2100)
  - Support des formats: date seule "YYYY-MM-DD", datetime complet "YYYY-MM-DDTHH:MM:SS", avec timezone "YYYY-MM-DDTHH:MM:SS.microsZ"
  - Réutilisable dans tous les endpoints
- **Validation des actions d'intervention**:
  - `complexity_anotation` est maintenant optionnel par défaut, mais obligatoire si `complexity_score > 5`
  - `created_at` est maintenant optionnel lors de la création - utilise automatiquement `now()` si omis
  - Permet de backdater les actions (un technicien peut saisir une action plusieurs jours après l'intervention)

---

## [1.0.1] - 26 janvier 2026

### Corrections

- Code cleanup interne (suppression de méthodes mortes et imports inutilisés)
- Respect strict de PEP8 (import ordering, docstrings de module)
- Migration vers syntaxe Python 3.9+ (list/dict au lieu de List/Dict, union type | au lieu de Optional)
- Chaînage d'exceptions amélioré (raise ... from e)

### Améliorations techniques

- Réduction de la complexité du code (moins de méthodes inutilisées)
- Meilleure conformité Pylint (zéro avertissements dans les domaines)
- Imports organisés selon PEP8 (stdlib avant third-party)

---

## [1.0.0] - 26 janvier 2026

### Nouveautés

- **Affichage simplifié des équipements**: Les listes et détails d'équipements affichent maintenant seulement l'état de santé (critique, avertissement, maintenance, ok) sans surcharger avec des statistiques complexes
- **Statistiques séparées**: Une nouvelle section dédiée pour voir les détails des interventions (nombre d'interventions ouvertes, par type, par priorité)
- **État de santé ultra-rapide**: Une nouvelle API pour afficher rapidement si un équipement va bien ou a besoin d'attention
- **Filtrer par période**: Possibilité de voir les statistiques sur une période spécifique (ex: interventions du mois dernier)
- **Recherche avancée des interventions**:
  - Par équipement
  - Par statut (ouvert, fermé, en cours...)
  - Par urgence (faible, normal, important, urgent)
  - Tri flexible (par date, urgence, etc.)
  - Voir les statistiques optionnellement
- **Tri par urgence**: Les interventions les plus urgentes apparaissent en premier
- **Code plus propre**: Simplification du code interne avec des constantes réutilisables

### Améliorations

- **Noms plus clairs**: Les modèles de données ont des noms plus simples et directs
- **Pages plus légères**: Les réponses API contiennent moins d'informations inutiles
- **Pas de doublons**: Suppression des données redondantes (status, color) qui apparaissaient partout
- **Moins de requêtes**: Le serveur fait moins de requêtes à la base de données

### Corrections

- Les pages d'équipement ne donnaient plus d'erreurs
- Suppression des messages d'erreur lors du chargement des interventions
- Performance améliorée

### Comment ça marche maintenant

- **État de santé d'un équipement**:
  - 🔴 critique: au moins 1 intervention très urgente
  - 🟡 avertissement: plus de 5 interventions ouvertes
  - 🟠 maintenance: 1 ou plusieurs interventions ouvertes
  - 🟢 ok: aucune intervention en attente
- **Statistiques**: Comptage des interventions par type et urgence
- **Recherche**: Rapide et efficace, sans chercher partout
- **Priorisation**: Les interventions urgentes sont clairement identifiées

---

## Historique des versions

Ce journal suit la convention [Keep a Changelog](https://keepachangelog.com/).
Les versions suivent [Semantic Versioning](https://semver.org/).
