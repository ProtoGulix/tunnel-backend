# Journal des mises à jour de l'API

Toutes les modifications importantes de l'API sont documentées ici.

## [1.9.0] - 15 février 2026

### Nouveautés

- **Demandes d'achat dans les exports PDF** : Les fiches d'intervention incluent maintenant la liste des demandes d'achat liées
  - 8 colonnes : Quantité, Réf. Interne, Désignation, Fournisseur, Réf. Fournisseur, Fabricant, Réf. Fabricant, Urgence
  - Données enrichies via JOINs SQL : `stock_item`, `stock_item_supplier`, `supplier`, `manufacturer_item`
  - Indicateur visuel d'urgence (⚠ fond rouge)

- **Pied de page PDF complet** : Informations de traçabilité sur chaque page du document
  - Code intervention et numérotation des pages (`Page X / Y`) en bleu, gras, monospace
  - Version API et version template (gauche)
  - Date de génération (droite)
  - Utilisation de CSS Paged Media (`string-set`, `counter(page)`, `counter(pages)`)

- **Version de template configurable** : Nouveau champ de configuration pour gérer le versioning des templates
  - `EXPORT_TEMPLATE_VERSION` : Version du template d'export (défaut: `v8.0`)
  - `EXPORT_TEMPLATE_DATE` : Date de version du template (défaut: `2025-10-03`)

### Changements

- **Déplacement des templates d'export** : Les templates sont déplacés de `api/exports/templates/` vers `config/templates/`
  - Template renommé : `fiche_intervention_v1.html` → `fiche_intervention_v8.html`
  - Logo déplacé : `api/exports/templates/logo.png` → `config/templates/logo.png`
  - Mise à jour des chemins par défaut dans la configuration

- **Logo en base64** : Le logo est converti en data URI base64 pour compatibilité WeasyPrint
  - Résout le problème d'affichage du logo dans les PDF générés

### Corrections

- **Colonne `quantity`** : Correction du nom de colonne (`quantity` au lieu de `quantity_requested`)
- **Colonne `requester_name`** : Utilisation du champ texte direct au lieu d'une jointure sur `directus_users`
- **Table `manufacturer`** : Correction de la jointure - les données fabricant sont dans `manufacturer_item.manufacturer_name` (pas de table `manufacturer` séparée)

### Configuration

Nouvelles variables d'environnement (optionnelles) :
- `EXPORT_TEMPLATE_VERSION` : Version du template (défaut: `v8.0`)
- `EXPORT_TEMPLATE_DATE` : Date de version du template (défaut: `2025-10-03`)

Variables modifiées :
- `EXPORT_TEMPLATE_DIR` : Défaut changé de `api/exports/templates` → `config/templates`
- `EXPORT_TEMPLATE_FILE` : Défaut changé de `fiche_intervention_v1.html` → `fiche_intervention_v8.html`
- `EXPORT_QR_LOGO_PATH` : Défaut changé de `api/exports/templates/logo.png` → `config/templates/logo.png`

---

## [1.8.0] - 12 février 2026

### Nouveautés

- **Export PDF des interventions** : Génération de rapports PDF professionnels pour impression
  - `GET /exports/interventions/{id}/pdf` - Export PDF avec authentification requise
  - Template HTML Jinja2 optimisé pour impression A4
  - Rendu PDF via WeasyPrint pour qualité professionnelle
  - Données complètes : intervention, équipement, actions, logs de statut, statistiques
  - Nom de fichier automatique basé sur le code intervention (ex: "INT-2026-001.pdf")
  - Support ETag pour mise en cache côté client

- **QR Codes pour interventions** : Génération de QR codes pour accès mobile rapide
  - `GET /exports/interventions/{id}/qrcode` - Génération QR code sans authentification (public)
  - QR code pointe vers la page détail intervention dans le frontend
  - Support overlay logo pour branding d'entreprise (optionnel)
  - Format PNG optimisé pour impression sur rapports physiques
  - Correction d'erreur élevée (ERROR_CORRECT_H) pour fiabilité du scan
  - Cache public 1 heure pour meilleures performances

- **Module exports dédié** : Architecture modulaire pour réutilisabilité
  - `api/exports/` : Nouveau module standalone suivant le pattern repository
  - `PDFGenerator` : Classe dédiée pour rendu HTML → PDF avec filtres Jinja2
  - `QRGenerator` : Classe dédiée pour génération QR codes avec logo overlay
  - `ExportRepository` : Repository spécialisé pour requêtes d'export optimisées
  - Templates Jinja2 personnalisables dans `api/exports/templates/`

### Configuration

Nouvelles variables d'environnement (optionnelles) :
- `EXPORT_TEMPLATE_DIR` : Dossier des templates HTML (défaut: `api/exports/templates`)
- `EXPORT_TEMPLATE_FILE` : Fichier template HTML (défaut: `fiche_intervention_v1.html`)
- `EXPORT_QR_BASE_URL` : URL frontend pour QR codes (défaut: `http://localhost:5173/interventions`)
- `EXPORT_QR_LOGO_PATH` : Chemin logo overlay QR (défaut: `api/exports/templates/logo.png`)

### Dépendances

Nouvelles dépendances ajoutées :
- `Jinja2==3.1.6` : Moteur de templates HTML
- `weasyprint==66.0.0` : Génération PDF depuis HTML/CSS
- `qrcode==8.2` : Génération de QR codes
- `Pillow==12.0.0` : Manipulation d'images (overlay logo sur QR)

### Sécurité

- **PDF exports** : Authentification JWT requise (données sensibles : noms techniciens, temps, notes)
- **QR codes** : Public (conçu pour impression sur rapports physiques, QR pointe vers frontend qui nécessite login)

---

## [1.7.0] - 11 février 2026

### Nouveautés

- **Qualité des données** : Nouvel endpoint de détection des problèmes de complétude et cohérence
  - `GET /stats/qualite-donnees` - Identifie les données manquantes ou incohérentes avec les règles métier
  - 13 règles de détection sur 4 entités :
    - **intervention_action** (7 règles) : temps non saisi, complexité sans facteur, sous-catégorie manquante, technicien manquant, description vide, temps suspect (> 8h), action créée après fermeture de l'intervention
    - **intervention** (3 règles) : fermée sans action, sans type, en cours inactive (> 14 jours)
    - **stock_item** (2 règles) : sans seuil minimum, sans fournisseur référencé
    - **purchase_request** (1 règle) : sans article de stock lié
  - Chaque problème remonte avec sévérité (`high` / `medium`), message en français et contexte de navigation
  - Filtrage par `severite`, `entite` ou `code` anomalie via query params
  - Requêtes SQL indépendantes par règle (pas de mega-jointure)

### Changements

- **Passage en beta** : Les endpoints suivants sont considérés beta car ils ne respectent pas encore la philosophie de l'API (requêtes SQL directes indépendantes, pas de chargement mémoire, format de réponse normalisé)
  - `GET /stats/anomalies-saisie` — Détection des anomalies de saisie (beta)
  - `GET /stats/charge-technique` — Analyse de la charge technique (beta)

---

## [1.6.1] - 9 février 2026

### Corrections

- **Exclusion du préventif des anomalies** : Les actions de catégorie PREV sont exclues des détections où elles créaient des faux positifs
  - Type A (répétitives) : les actions préventives récurrentes (nettoyage filtres, etc.) ne remontent plus
  - Type B (fragmentées) : les actions préventives courtes (0.25h, 0.5h) ne remontent plus
  - Type E (back-to-back) : les actions préventives quotidiennes consécutives ne remontent plus

---

## [1.6.0] - 9 février 2026

### Nouveautés

- **Détection des anomalies de saisie** : Nouvel endpoint d'analyse qualité des actions d'intervention
  - `GET /stats/anomalies-saisie` - Analyse la qualité des saisies et détecte 6 types d'anomalies
  - **Actions répétitives** (too_repetitive) : Même sous-catégorie + même machine > 3 fois/mois
  - **Actions fragmentées** (too_fragmented) : Actions courtes (< 1h) apparaissant 5+ fois sur une même sous-catégorie
  - **Actions trop longues** (too_long_for_category) : Actions > 4h sur des catégories normalement rapides (BAT_NET, BAT_RAN, BAT_DIV, LOG_MAG, LOG_REC, LOG_INV)
  - **Mauvaise classification** (bad_classification) : Actions BAT_NET contenant des mots-clés techniques suspects (mécanique, hydraulique, roulement, vérin, etc.)
  - **Retours back-to-back** (back_to_back) : Même technicien + même intervention, deux actions consécutives espacées de moins de 24h
  - **Faible valeur / charge élevée** (low_value_high_load) : Catégories à faible valeur ajoutée avec temps cumulé > 30h
  - Chaque anomalie a une sévérité `high` ou `medium` selon des seuils configurables
  - Messages pré-formatés en français pour affichage direct dans les tableaux
  - Bloc `config` dans la réponse avec les seuils et listes appliqués pour transparence côté frontend

---

## [1.5.2] - 9 février 2026

### Corrections

- **CORS** : Correction des erreurs CORS Missing Allow Origin
  - Ajout de `CORS_ORIGINS` property avec support multi-origines en développement (localhost:5173, localhost:3000, 127.0.0.1:5173, 127.0.0.1:3000)
  - Ajout de `expose_headers=["*"]` dans CORSMiddleware
  - Middleware JWT : bypass des requêtes OPTIONS (CORS preflight) avant vérification d'authentification

### Nouveautés

- **Docker** : Ajout de configuration Docker et docker-compose
  - `Dockerfile` : Image Python 3.12 avec hot-reload pour développement
  - `docker-compose.yml` : Configuration minimaliste pour l'API seule
  - `.dockerignore` : Exclusions optimisées du build
  - Mise à jour du README avec instructions de démarrage Docker

---

## [1.5.1] - 8 février 2026

### Améliorations

- **Guide de lecture charge technique** : Alignement des textes avec les règles métier (REGLES_METIER.md)
  - Seuils du taux évitable : labels et actions corrigés pour correspondre au document de référence
  - Actions par catégorie de complexité : recalées sur le mapping réel des facteurs (PCE→Logistique, ACC→Technique, DOC→Information, OUT→Ressources, ENV→Environnement)

---

## [1.5.0] - 8 février 2026

### Nouveautés

- **Charge technique (pilotage maintenance)** : Nouvel endpoint d'analyse stratégique
  - `GET /stats/charge-technique` - Analyse où passe le temps du service maintenance et quelle part est récupérable
  - Découpage multi-période : `period_type` = `month`, `week`, `quarter` ou `custom`
  - Calcul automatique des charges : totale, dépannage, constructive (FAB+SUP+PREV+BAT)
  - Distinction **dépannage évitable** vs **dépannage subi** :
    - Évitable si `complexity_factor` renseigné (tout facteur est un signal)
    - Évitable si même `action_subcategory` répétée ≥3 fois sur la même classe d'équipement
  - **Taux de dépannage évitable** avec indicateur couleur :
    - Vert (<20%) : Faible levier
    - Orange (20-40%) : Levier de standardisation
    - Rouge (>40%) : Problème systémique
  - Ventilation par facteur de complexité (PCE, ACC, DOC, OUT, ENV, AUT...)
  - Ventilation par classe d'équipement avec taux individuel
  - Analyse toujours par classe d'équipement, jamais par machine isolée ni par technicien
  - **Guide de lecture** intégré dans la réponse (`guide`) : l'API fournit l'objectif, les seuils d'interprétation du taux évitable, et les actions recommandées par catégorie de complexité

---

## [1.4.0] - 8 février 2026

### ⚠️ BREAKING CHANGES

- **Renommage du champ de facteur de complexité** : Le champ `complexity_anotation` devient `complexity_factor`
  - Impact sur les endpoints :
    - `POST /intervention_actions/` - Entrée : utiliser `complexity_factor` au lieu de `complexity_anotation`
    - `GET /interventions/{id}/actions` - Sortie : le champ `complexity_factor` remplace `complexity_anotation`
    - `GET /intervention_actions/{id}` - Sortie : le champ `complexity_factor` remplace `complexity_anotation`
  - Le type de sortie change de `object|null` à `string|null` (c'est maintenant une FK directe vers la table complexity_factor)
  - Migration : les applications clientes doivent mettre à jour leurs appels API

---

## [1.3.1] - 7 février 2026

### Nouveautés

- **CRUD des equipements** : Creation, modification et suppression des equipements
  - `POST /equipements/` - Cree un equipement (ex: ajouter une nouvelle machine dans l'atelier)
  - `PUT /equipements/{id}` - Met a jour un equipement (ex: reassigner a une autre classe)
  - `DELETE /equipements/{id}` - Supprime un equipement

---

## [1.3.0] - 7 février 2026

### ⚠️ BREAKING CHANGES

- **Nouveau module de classes d'équipement** : Ajout d'un système de classification des équipements
  - Les réponses des endpoints `/equipements` incluent maintenant `equipment_class` (objet ou null)
  - Structure du champ ajouté :
    ```json
    {
      "equipment_class": {
        "id": "uuid",
        "code": "SCIE",
        "label": "Scie"
      }
    }
    ```
  - Impact sur les endpoints :
    - `GET /equipements/` - Liste avec champ `equipment_class`
    - `GET /equipements/{id}` - Détail avec champ `equipment_class`
  - Migration : Le champ `equipment_class` sera `null` pour tous les équipements existants jusqu'à assignation

### Nouveautés

- **Module CRUD complet pour les classes d'équipement** : Nouveau module `/equipement_class`
  - `GET /equipement_class/` - Liste toutes les classes d'équipement
  - `GET /equipement_class/{id}` - Récupère une classe par ID
  - `POST /equipement_class/` - Crée une nouvelle classe
    ```json
    {
      "code": "SCIE",
      "label": "Scie",
      "description": "Machines de sciage"
    }
    ```
  - `PATCH /equipement_class/{id}` - Met à jour une classe existante
  - `DELETE /equipement_class/{id}` - Supprime une classe (bloqué si des équipements l'utilisent)

- **Classification hiérarchique des équipements** :
  - Chaque équipement peut être assigné à une classe (SCIE, EXTRUDEUSE, etc.)
  - Relation Many-to-One : plusieurs équipements peuvent partager la même classe
  - Hydratation automatique : une seule requête SQL pour récupérer équipement + classe
  - Validation d'intégrité : impossible de supprimer une classe utilisée par des équipements

### Améliorations techniques

- **Optimisation des requêtes** : Les données de classe sont récupérées via LEFT JOIN (1 seule requête)
- **Performance** : Pas d'impact sur les performances - le LEFT JOIN est sur une table de référence
- **Validation** : Code unique par classe pour éviter les doublons
- **Sécurité** : Protection CASCADE - impossible de supprimer une classe en usage

### Structure de base de données

- Nouvelle table `equipement_class` avec colonnes : id, code (unique), label, description
- Nouvelle colonne `equipement_class_id` (UUID, nullable) dans la table `machine`
- Foreign key avec ON DELETE RESTRICT pour protéger les données

---

## [1.2.14] - 7 février 2026

### Corrections

- **Correction complète quantity_fulfilled → quantity** : Remplacement dans tous les fichiers
  - Correction dans `purchase_requests/repo.py` : SELECT et INSERT/UPDATE des order_lines
  - Correction dans `supplier_order_lines/repo.py` : Tous les INSERT et paramètre de méthode `link_purchase_request`
  - Correction dans `supplier_orders/repo.py` : SELECT des purchase_requests liées
  - Impact : Le dispatch et la liaison purchase_request ↔ order_line fonctionnent correctement

- **Amélioration dispatch** : Gestion du cache orders_cache en cas de rollback
  - Nettoyage du cache si un supplier_order créé dans un savepoint est rollback
  - Évite les erreurs de foreign key sur des orders qui n'existent plus

- **Schema SupplierOrderUpdate** : Nouveau schéma pour updates partiels
  - Tous les champs optionnels (incluant `supplier_id`, `received_at`)
  - Permet de faire des PUT avec seulement les champs à modifier
  - `PUT /supplier_orders/{id}` utilise maintenant `SupplierOrderUpdate` au lieu de `SupplierOrderIn`

---

## [1.2.13] - 6 février 2026

### Corrections

- **Calcul des statuts dérivés** : Correction de bugs critiques dans le calcul des statuts
  - Correction du nom de colonne `quantity_fulfilled` → `quantity` dans la récupération des order_lines
  - Correction de la logique NO_SUPPLIER_REF : statut appliqué même si des order_lines existent
  - Impact : Les demandes affichent maintenant les bons statuts (OPEN, ORDERED, etc.) au lieu de PENDING_DISPATCH
  - Les order_lines étaient silencieusement ignorées à cause d'une erreur SQL masquée par `except Exception: return []`

---

## [1.2.12] - 6 février 2026

### Nouveautés

- **Statistiques interventions enrichies** : Ajout du compteur `purchase_count` dans les stats d'intervention
  - Nombre de demandes d'achat liées à l'intervention (via les actions)
  - Disponible sur `GET /interventions/` et `GET /interventions/{id}`

- **Nouveau statut demandes d'achat `PENDING_DISPATCH`** : Distinction entre "à dispatcher" et "en mutualisation"
  - `PENDING_DISPATCH` (À dispatcher) : Référence fournisseur ok, mais pas encore dans un supplier order
  - `OPEN` (Mutualisation) : Présent dans un supplier order avec des order_lines

- **Dispatch automatique des demandes d'achat** : `POST /purchase_requests/dispatch`
  - Dispatche toutes les demandes en `PENDING_DISPATCH` vers des supplier_orders
  - Pour chaque demande, récupère les fournisseurs liés au stock_item
  - Trouve ou crée un supplier_order ouvert par fournisseur
  - Crée les supplier_order_lines liées aux demandes
  - Retourne un résumé : `dispatched_count`, `created_orders`, `errors`

---

## [1.2.11] - 6 février 2026

### Nouveautés

- **Demandes d'achat liées aux actions** : Les actions d'intervention incluent maintenant les demandes d'achat liées complètes
  - Nouveau champ `purchase_requests` (array de `PurchaseRequestOut`) dans `InterventionActionOut`
  - Utilise `PurchaseRequestRepository.get_by_id()` pour hydrater chaque demande avec toutes ses données
  - Relation M2M via la table de jonction `intervention_action_purchase_request`
  - Permet d'afficher les demandes d'achat associées à chaque action avec leur statut, stock_item, intervention, order_lines

---

## [1.2.10] - 5 février 2026

### Corrections

- **Correction CRUD interventions** : Alignement avec la structure réelle de la table
  - Suppression des colonnes `created_at` et `updated_at` qui n'existent pas dans la table `intervention`
  - Le schéma `InterventionIn` ne contient plus `created_at`

---

## [1.2.9] - 5 février 2026

### Nouveautés

- **CRUD complet pour les interventions** : Ajout des endpoints de création, modification et suppression
  - `POST /interventions/` - Création d'une intervention avec équipement, priorité, type, technicien
  - `PUT /interventions/{id}` - Modification des champs d'une intervention existante
  - `DELETE /interventions/{id}` - Suppression d'une intervention
  - Retourne l'intervention complète avec équipement, stats, actions et status_logs

---

## [1.2.8] - 4 février 2026

### Améliorations

- **Statut “Qualifiée sans référence fournisseur”** : les demandes qualifiées sans référence fournisseur liée sont maintenant distinguées
  - Permet d'identifier rapidement les articles à référencer avant dispatch
  - Cas d'usage : une demande est qualifiée (article stock lié) mais aucun fournisseur n'est encore associé

---

## [1.2.7] - 4 février 2026

### Améliorations

- **Hydratation des interventions dans les demandes d'achat** : Les endpoints de demandes d'achat incluent maintenant les informations complètes de l'intervention liée
  - `GET /purchase_requests/` retourne l'objet `intervention` avec : id, code, title, priority, status_actual
  - L'équipement associé à l'intervention est également inclus (id, code, name)
  - Plus besoin de faire une requête supplémentaire pour avoir le contexte de l'intervention
  - Appliqué aux endpoints : `GET /purchase_requests/`, `GET /purchase_requests/{id}`, `GET /purchase_requests/intervention/{id}`

---

## [1.2.6] - 4 février 2026

### Corrections

- **Export CSV/Email** : Correction du bug qui empêchait l'affichage des lignes de commande
  - Les exports incluent maintenant toutes les lignes de la commande fournisseur
  - Suppression de la jointure incorrecte avec `manufacturer_item` (colonnes inexistantes)
  - Les informations fabricant sont récupérées depuis `supplier_order_line.manufacturer` et `manufacturer_ref`

---

## [1.2.5] - 3 février 2026

### Améliorations

- **Templates d'export configurables** : Séparation des templates dans [config/export_templates.py](config/export_templates.py)
  - Templates CSV : En-têtes, format de ligne, nom de fichier
  - Templates email : Sujet, corps texte, corps HTML
  - Commentaires explicatifs pour faciliter les personnalisations
  - Modification des templates sans toucher au code des routes
  - Contraintes documentées (HTML email, caractères spéciaux, etc.)

---

## [1.2.4] - 3 février 2026

### 📤 Export des commandes fournisseurs

#### Nouveautés

- **Export CSV** : Téléchargez une commande au format tableur
  - Articles sélectionnés avec références, spécifications et quantités
  - Prêt à imprimer ou envoyer par email
  - Demandes d'achat liées visibles pour chaque ligne

- **Génération d'email** : Créez un email de commande en un clic
  - Sujet et corps de l'email pré-remplis
  - Version texte et HTML disponibles
  - Email du fournisseur inclus automatiquement

#### Nouveaux endpoints

- `POST /supplier_orders/{id}/export/csv` - Télécharge le CSV
- `POST /supplier_orders/{id}/export/email` - Génère le contenu email

---

## [1.2.3] - 3 février 2026

### ⏱️ Suivi de l'âge des commandes fournisseurs

#### Nouveautés

- **Indicateurs d'âge** : Les commandes affichent maintenant leur ancienneté
  - `age_days` : nombre de jours depuis la création
  - `age_color` : indicateur visuel (gray < 7j, orange 7-14j, red > 14j)
  - `is_blocking` : commande bloquante si en attente depuis plus de 7 jours

#### Statuts disponibles

- `OPEN` : Commande créée, en attente d'envoi
- `SENT` : Commande envoyée au fournisseur
- `ACK` : Accusé de réception du fournisseur
- `RECEIVED` : Livraison reçue
- `CLOSED` : Commande clôturée
- `CANCELLED` : Commande annulée

---

## [1.2.2] - 3 février 2026

### 📦 Commandes fournisseurs enrichies

#### Nouveauté

- **Informations fournisseur incluses** : Les commandes fournisseurs affichent maintenant les coordonnées du fournisseur
  - Nom, code, contact, email, téléphone
  - Plus besoin de faire une requête supplémentaire pour avoir les infos du fournisseur

---

## [1.2.1] - 3 février 2026

### 🔄 Simplification du statut des demandes d'achat

#### Changement

- **Un seul statut** : Le champ `status` (manuel) a été supprimé au profit de `derived_status` (calculé automatiquement)
  - Évite les incohérences entre deux sources de vérité
  - Le statut reflète toujours l'état réel de la demande
  - Plus besoin de mettre à jour manuellement le statut

#### Impact technique

- `PurchaseRequestOut.status` → supprimé
- `PurchaseRequestOut.derived_status` → obligatoire (non nullable)
- Le champ `status` n'est plus modifiable via `PUT /purchase_requests/{id}`

---

## [1.2.0] - 1er février 2026

### 🚀 Demandes d'achat optimisées

#### Nouveautés

- **Listes plus rapides** : Les tableaux de demandes d'achat se chargent instantanément
  - Affichage du statut calculé automatiquement (En attente, Devis reçu, Commandé, Reçu...)
  - Compteurs visibles : nombre de devis, fournisseurs contactés
  - Plus besoin d'ouvrir chaque demande pour voir son état

- **Détails complets en un clic** : Toutes les informations dans une seule page
  - Intervention associée avec son équipement
  - Article en stock avec ses références
  - Tous les fournisseurs contactés avec leurs coordonnées et prix

- **Nouveau tableau de bord** : Statistiques des demandes d'achat
  - Combien de demandes en attente, en cours, terminées
  - Répartition par urgence
  - Articles les plus demandés

#### Améliorations

- Le statut des demandes est maintenant calculé automatiquement selon l'avancement
- Les tableaux affichent uniquement l'essentiel (chargement 5x plus rapide)
- Une seule requête pour voir tous les détails d'une demande

#### Statuts des demandes

- 🟡 **À qualifier** : Pas de référence stock normalisée (besoin de qualification)
- ⚪ **En attente** : Prête à être dispatchée aux fournisseurs
- 🟠 **Devis reçu** : Au moins un fournisseur a répondu
- 🔵 **Commandé** : Commande passée chez un fournisseur
- 🟣 **Partiellement reçu** : Livraison partielle
- 🟢 **Reçu** : Livraison complète
- 🔴 **Refusé** : Demande annulée

---

## [1.1.7] - 29 janvier 2026

### Nouveautés

- **Module de gestion des commandes fournisseurs**: Ensemble complet d'endpoints pour la gestion des commandes
  - `GET /supplier_orders` - Liste des commandes avec filtres (statut, fournisseur)
  - `GET /supplier_orders/{id}` - Détail d'une commande avec ses lignes
  - `GET /supplier_orders/number/{order_number}` - Recherche par numéro de commande
  - `POST /supplier_orders` - Création d'une nouvelle commande
  - `PUT /supplier_orders/{id}` - Mise à jour d'une commande
  - `DELETE /supplier_orders/{id}` - Suppression d'une commande (cascade sur les lignes)
  - Numéro de commande auto-généré par trigger base de données
  - Calcul automatique du montant total basé sur les lignes

- **Module de lignes de commande fournisseur**: Gestion des articles commandés
  - `GET /supplier_order_lines` - Liste des lignes avec filtres (commande, article, sélection)
  - `GET /supplier_order_lines/order/{supplier_order_id}` - Toutes les lignes d'une commande
  - `GET /supplier_order_lines/{id}` - Détail d'une ligne avec article et demandes d'achat liées
  - `POST /supplier_order_lines` - Création d'une ligne avec liaison optionnelle aux demandes d'achat
  - `PUT /supplier_order_lines/{id}` - Mise à jour d'une ligne
  - `DELETE /supplier_order_lines/{id}` - Suppression d'une ligne
  - `POST /supplier_order_lines/{id}/purchase_requests` - Lier une demande d'achat à une ligne
  - `DELETE /supplier_order_lines/{id}/purchase_requests/{pr_id}` - Délier une demande d'achat
  - Prix total calculé automatiquement (quantité × prix unitaire)
  - Support complet des devis (prix, date réception, fabricant, délai livraison)

- **Module de demandes d'achat**: Suivi des demandes de matériel
  - `GET /purchase_requests` - Liste avec filtres (statut, intervention, urgence)
  - `GET /purchase_requests/{id}` - Détail d'une demande avec lignes de commande liées
  - `GET /purchase_requests/intervention/{id}` - Demandes liées à une intervention
  - `POST /purchase_requests` - Création d'une demande
  - `PUT /purchase_requests/{id}` - Mise à jour d'une demande
  - `DELETE /purchase_requests/{id}` - Suppression d'une demande
  - Liaison bidirectionnelle avec les lignes de commande fournisseur
  - Enrichissement automatique avec les détails de l'article en stock

- **Module de gestion du stock**: Catalogue d'articles
  - `GET /stock_items` - Liste avec filtres (famille, sous-famille, recherche)
  - `GET /stock_items/{id}` - Détail d'un article
  - `GET /stock_items/ref/{ref}` - Recherche par référence
  - `POST /stock_items` - Création d'un article
  - `PUT /stock_items/{id}` - Mise à jour d'un article
  - `PATCH /stock_items/{id}/quantity` - Mise à jour rapide de la quantité
  - `DELETE /stock_items/{id}` - Suppression d'un article
  - Référence auto-générée par trigger (famille-sous_famille-spec-dimension)
  - Compteur automatique des références fournisseurs

### Améliorations techniques

- Relation M2M complète entre lignes de commande fournisseur et demandes d'achat
  - Table de liaison `supplier_order_line_purchase_request` avec quantité allouée
  - Permet de tracer quelle demande d'achat est satisfaite par quelle ligne de commande
  - Une ligne peut satisfaire plusieurs demandes, une demande peut être liée à plusieurs lignes
- Schémas légers (`ListItem`) pour les listes, schémas complets (`Out`) pour les détails
- Conversion automatique des Decimal en float pour la sérialisation JSON
- Enrichissement automatique des relations (stock_item, purchase_requests, order_lines)
- Tous les endpoints respectent les standards de pagination (skip, limit max 1000)
- Gestion cohérente des erreurs avec `DatabaseError` et `NotFoundError`

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
