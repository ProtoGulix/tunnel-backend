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
- **Statistiques** : vue d'ensemble des interventions par type et statut

## 🎯 Pour qui ?

PME industrielles avec 10 à 100 machines et équipes de maintenance de 1 à 10 personnes qui veulent structurer leur maintenance sans logiciel lourd et coûteux.

## 📄 Licence

**AGPL-3.0** - Conformément au projet Tunnel GMAO

- Le code est libre d'utilisation
- Les modifications doivent être redistribuées sous la même licence
- Les données appartiennent à l'entreprise qui les génère
- Aucune collecte ou transmission de données vers l'extérieur

Voir [LICENSE](LICENSE) pour le texte complet.
