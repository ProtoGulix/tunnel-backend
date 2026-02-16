# Tunnel GMAO - Backend API

API backend pour [Tunnel GMAO](https://github.com/ProtoGulix/tunnel-gmao), solution open-source de gestion de maintenance industrielle.

## 🎯 Philosophie

Ce backend suit les principes du projet Tunnel GMAO :

- **L'action est l'unité de travail réel** : temps, complexité et pièces sont tracés au niveau des actions, pas des interventions
- **Terrain first** : l'API reflète la réalité du travail terrain sans imposer de méthode
- **Sobriété** : pas de complexité inutile, pas d'ERP déguisé, juste ce qui est nécessaire
- **Traçabilité fiable** : enregistrer ce qui se passe réellement, sans bureaucratie excessive

## 📋 Responsabilités

Cette API fournit les données pour l'interface Tunnel GMAO :

- **Équipements** : liste, état, statistiques d'interventions
- **Interventions** : gestion du cycle de vie, statuts, priorités
- **Actions** : traçabilité du travail réel (temps, complexité, pièces)
- **Demandes d'achat** : suivi des demandes et de leurs statuts (qualification, références fournisseurs, commandes)
- **Templates de pièces** : caractérisation structurée des pièces avec versionnement (v1.4.0)
- **Statistiques** : vue d'ensemble des interventions par type et statut

> **Nouveauté v1.11.0** : Support complet du système de templates versionnés pour la caractérisation des pièces. Voir [docs/TEMPLATES_V1.4.0_IMPLEMENTATION.md](docs/TEMPLATES_V1.4.0_IMPLEMENTATION.md)

## 🎯 Pour qui ?

PME industrielles avec 10 à 100 machines et équipes de maintenance de 1 à 10 personnes qui veulent structurer leur maintenance sans logiciel lourd et coûteux.

## � Démarrage

### Option 1 : Docker (Recommandé)

```bash
# Démarrer tous les services (PostgreSQL + Directus + API)
docker-compose up -d

# Accès
# API: http://localhost:8000/docs
# Directus: http://localhost:8055 (admin@tunnel.local / admin)
```

### Option 2 : Local (Python 3.12)

```bash
# Windows
.\run.bat

# Linux/Mac
./run.sh

# Accès
# API: http://localhost:8000/docs
```

**Note** : En local, PostgreSQL et Directus doivent être démarrés séparément ou via Docker.

## �📄 Licence

**AGPL-3.0** - Conformément au projet Tunnel GMAO

- Le code est libre d'utilisation
- Les modifications doivent être redistribuées sous la même licence
- Les données appartiennent à l'entreprise qui les génère
- Aucune collecte ou transmission de données vers l'extérieur

Voir [LICENSE](LICENSE) pour le texte complet.
