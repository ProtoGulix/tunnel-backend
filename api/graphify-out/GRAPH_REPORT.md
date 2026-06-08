# Graph Report - /home/tunnel/DEV/tunnel-backend/api  (2026-06-08)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1896 nodes · 4257 edges · 133 communities (124 shown, 9 thin omitted)
- Extraction: 68% EXTRACTED · 32% INFERRED · 0% AMBIGUOUS · INFERRED: 1362 edges (avg confidence: 0.71)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2bd82e24`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 77|Community 77]]
- [[_COMMUNITY_Community 78|Community 78]]
- [[_COMMUNITY_Community 79|Community 79]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 81|Community 81]]
- [[_COMMUNITY_Community 82|Community 82]]
- [[_COMMUNITY_Community 83|Community 83]]
- [[_COMMUNITY_Community 84|Community 84]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 86|Community 86]]
- [[_COMMUNITY_Community 87|Community 87]]
- [[_COMMUNITY_Community 88|Community 88]]
- [[_COMMUNITY_Community 89|Community 89]]
- [[_COMMUNITY_Community 90|Community 90]]
- [[_COMMUNITY_Community 91|Community 91]]
- [[_COMMUNITY_Community 92|Community 92]]
- [[_COMMUNITY_Community 93|Community 93]]
- [[_COMMUNITY_Community 94|Community 94]]
- [[_COMMUNITY_Community 95|Community 95]]
- [[_COMMUNITY_Community 96|Community 96]]
- [[_COMMUNITY_Community 97|Community 97]]
- [[_COMMUNITY_Community 98|Community 98]]
- [[_COMMUNITY_Community 99|Community 99]]
- [[_COMMUNITY_Community 100|Community 100]]
- [[_COMMUNITY_Community 101|Community 101]]
- [[_COMMUNITY_Community 102|Community 102]]
- [[_COMMUNITY_Community 103|Community 103]]
- [[_COMMUNITY_Community 104|Community 104]]
- [[_COMMUNITY_Community 105|Community 105]]
- [[_COMMUNITY_Community 106|Community 106]]

## God Nodes (most connected - your core abstractions)
1. `release_connection()` - 242 edges
2. `DatabaseError` - 197 edges
3. `NotFoundError` - 150 edges
4. `ValidationError` - 127 edges
5. `raise_db_error()` - 95 edges
6. `get_connection()` - 94 edges
7. `single()` - 77 edges
8. `InterventionRepository` - 64 edges
9. `StatsRepository` - 51 edges
10. `SupplierOrderRepository` - 44 edges

## Surprising Connections (you probably didn't know these)
- `Request` --uses--> `AuditMiddleware`  [INFERRED]
  app.py → audits/middleware.py
- `Any` --uses--> `NotFoundError`  [INFERRED]
  equipement_statuts/repo.py → errors/exceptions.py
- `PreventivePlanIn` --uses--> `NotFoundError`  [INFERRED]
  preventive_plans/repo.py → errors/exceptions.py
- `PreventivePlanUpdate` --uses--> `NotFoundError`  [INFERRED]
  preventive_plans/repo.py → errors/exceptions.py
- `AnomaliesSaisieResponse` --uses--> `DatabaseError`  [INFERRED]
  stats/repo.py → errors/exceptions.py

## Import Cycles
- 1-file cycle: `admin/routes.py -> admin/routes.py`
- 1-file cycle: `app.py -> app.py`
- 1-file cycle: `audits/repo.py -> audits/repo.py`
- 1-file cycle: `audits/routes.py -> audits/routes.py`
- 1-file cycle: `errors/handlers.py -> errors/handlers.py`
- 1-file cycle: `intervention_actions/routes.py -> intervention_actions/routes.py`
- 1-file cycle: `intervention_requests/routes.py -> intervention_requests/routes.py`
- 1-file cycle: `stock_items/template_service.py -> stock_items/template_service.py`
- 1-file cycle: `stock_sub_families/repo.py -> stock_sub_families/repo.py`
- 1-file cycle: `utils/validators.py -> utils/validators.py`

## Communities (133 total, 9 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (43): AuditRepository, Any, datetime, UUID, Repository d'accès aux tables audit_log et audit_reason_code., Retourne une raison par son code, ou None si inexistante/inactive., Appelle fn_audit_log_decision() en base.         La DB valide la raison, les con, Requête paginée sur audit_log avec filtres optionnels et facettes optionnelles. (+35 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (53): Config, EquipementChildItem, EquipementClassFacetItem, EquipementDetail, EquipementHealth, EquipementListItem, EquipementPatch, EquipementStatsDetailed (+45 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (47): get_mail_settings(), Retourne la config mail sans le mot de passe SMTP., ActionCategoryActivePatch, ActionCategoryPatch, ActionSubcategoryActivePatch, ActionSubcategoryCreate, ActionSubcategoryPatch, AdminUserActivePatch (+39 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (47): AdminEndpointRepository, AdminRoleRepository, AdminSecurityRepository, AdminUserRepository, Accès BDD pour la gestion admin des utilisateurs tunnel_user., Accès BDD pour les rôles et permissions., Accès BDD pour le catalogue des endpoints., Accès BDD pour les logs et outils sécurité. (+39 more)

### Community 4 - "Community 4"
Cohesion: 0.11
Nodes (24): ActionSubcategoryCreate, Any, _raise(), Génère un mot de passe temporaire, met à jour le hash, retourne le mot de passe, Désactive, obfusque l'email et efface le hash., Retourne la matrice complète rôles × endpoints groupée par module., create_action_subcategory(), list_action_categories() (+16 more)

### Community 5 - "Community 5"
Cohesion: 0.06
Nodes (42): AnomaliesSaisieResponse, QualiteDonneesResponse, Détecte les problèmes de complétude et cohérence des données, Détecte les 6 types d'anomalies de saisie sur la période, AnomaliesBySeverity, AnomaliesByType, AnomaliesConfig, AnomaliesDetail (+34 more)

### Community 6 - "Community 6"
Cohesion: 0.09
Nodes (22): Construit le détail complet d'une intervention parente pour l'analyse IA., Intervention légère embarquée dans une action (utilisée dans get_all), _audit_request(), Any, Insère un log d'audit pour une DI via fn_audit_log_decision().     Les erreurs s, Construit l'objet equipement (EquipementListItem) depuis les colonnes préfixées, Construit l'objet intervention (InterventionRef) depuis les colonnes préfixées i, Désérialise la colonne di_tasks (json agrégé) en liste de tâches. (+14 more)

### Community 7 - "Community 7"
Cohesion: 0.08
Nodes (30): PreventivePlanRepository, Any, GammeStepIn, PreventivePlanIn, PreventivePlanUpdate, Liste tous les plans préventifs avec leur classe d'équipement et leurs steps, Récupère un plan préventif par ID avec ses steps, Requêtes pour le domaine plans de maintenance préventive (+22 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (26): Config, InterventionStatusLogIn, Schéma d'entrée pour créer un log de changement de statut, Schéma de sortie pour un log de changement de statut, Détail d'un statut d'intervention, StatusDetail, Any, Valide que tous les champs obligatoires sont présents (+18 more)

### Community 9 - "Community 9"
Cohesion: 0.10
Nodes (26): Any, Récupère une référence fournisseur par ID, Récupère toutes les références fournisseurs d'un article, Convertit les Decimal en float pour la sérialisation JSON, Crée une nouvelle référence fournisseur, Extrait les colonnes mi_* en objet manufacturer_item imbriqué, Met à jour une référence fournisseur existante, Supprime une référence fournisseur (+18 more)

### Community 10 - "Community 10"
Cohesion: 0.08
Nodes (27): ManufacturerItemRepository, Any, Crée une nouvelle référence fabricant, Requêtes pour le domaine manufacturer_item, Met à jour partiellement une référence fabricant, Liste les références fabricants avec recherche optionnelle, Supprime une référence fabricant, Compte les références fabricants avec filtre optionnel (+19 more)

### Community 11 - "Community 11"
Cohesion: 0.08
Nodes (20): check_equipement_statut_allows_interventions(), Vérifie que l'équipement peut recevoir des interventions selon son statut.     S, ConflictError, Conflit — ressource déjà existante (409), Any, Valide que time_spent est un quart d'heure (0.25, 0.5, 0.75, 1.0, etc.) >= 0.25, Valide que complexity_score est entre 1 et 10, Valide que tous les champs obligatoires sont présents.         complexity_factor (+12 more)

### Community 12 - "Community 12"
Cohesion: 0.09
Nodes (22): NotFoundError, Ressource non trouvée (404), Any, Récupère données complètes pour export PDF v9.          Compatible legacy : les, date, Bloque toute écriture sur une intervention fermée., _audit_task(), Any (+14 more)

### Community 13 - "Community 13"
Cohesion: 0.08
Nodes (29): get_equipement_class(), list_equipement_classes(), Routes API pour les classes d'équipement, Liste toutes les classes d'équipement, Récupère une classe d'équipement par ID, Crée une nouvelle classe d'équipement, Met à jour une classe d'équipement, Supprime une classe d'équipement (+21 more)

### Community 14 - "Community 14"
Cohesion: 0.11
Nodes (20): PartTemplateRepository, Any, PartTemplateUpdate, Requêtes pour le domaine part_template, Récupère tous les templates (dernière version de chaque) avec leurs champs, Récupère un template par ID         Si version est None, retourne la version la, Récupère toutes les versions d'un template par code, Crée un nouveau template (version 1)         Transaction complète avec fields et (+12 more)

### Community 15 - "Community 15"
Cohesion: 0.12
Nodes (22): get_template(), create_stock_family(), StockFamilyIn, Crée une nouvelle famille de stock, Requêtes pour le domaine stock_item, Sous-famille de stock avec template associé, UUID, Récupère une sous-famille par ses codes avec son template associé (si existant) (+14 more)

### Community 16 - "Community 16"
Cohesion: 0.15
Nodes (15): Any, Récupère toutes les lignes de commande avec filtres optionnels, Convertit les Decimal en float pour la sérialisation JSON, Récupère une ligne par ID avec stock_item et purchase_requests, Enrichit une ligne avec les détails du stock_item, Crée une nouvelle ligne de commande, Met à jour une ligne de commande existante, Lie une demande d'achat à une ligne de commande (+7 more)

### Community 17 - "Community 17"
Cohesion: 0.16
Nodes (20): CharacteristicValue, Erreur de validation (400), ValidationError, PartTemplateIn, PartTemplateUpdate, TemplateFieldEnumIn, TemplateFieldIn, PartTemplate (+12 more)

### Community 18 - "Community 18"
Cohesion: 0.15
Nodes (15): EquipementRepository, Any, Requêtes pour le domaine equipement avec statistiques interventions, Récupère un équipement par ID avec tous les champs, children_count et interventi, Assigne une liste d'équipements comme enfants de parent_id, Crée un nouvel équipement, Met à jour un équipement existant, Récupère uniquement le health d'un équipement (ultra-léger) (+7 more)

### Community 19 - "Community 19"
Cohesion: 0.10
Nodes (17): FragmentedAnomaly, LowValueHighLoadAnomaly, RepetitiveAnomaly, ServiceStatusResponse, SiteConsumption, date, Retourne des métriques vides quand pas de données, Formate les causes de fragmentation avec pourcentages (+9 more)

### Community 20 - "Community 20"
Cohesion: 0.14
Nodes (12): InterventionRepository, Any, Requêtes pour le domaine interventions, Résout tech_initials depuis tunnel_user.initial si tech_id est fourni., Crée une nouvelle intervention, Lie une demande d'intervention à l'intervention créée :         - Vérifie que la, Met à jour une intervention existante, Récupère interventions avec filtres/sort et stats calculées en SQL (sans actions (+4 more)

### Community 21 - "Community 21"
Cohesion: 0.12
Nodes (22): ServiceCreate, Requêtes pour le domaine services, create_service(), get_service(), list_services(), Routes API pour les services, Liste tous les services actifs, Récupère un service par ID (+14 more)

### Community 22 - "Community 22"
Cohesion: 0.14
Nodes (16): QuantityUpdate, Schéma pour la mise à jour de quantité, is_legacy_item(), Any, Crée un item basé sur un template          Règles :         - Les caractéristiqu, Service de gestion des stock_items avec support templates, Met à jour un stock_item          Règles d'immutabilité :         - template_id, Récupère un item par ID (+8 more)

### Community 23 - "Community 23"
Cohesion: 0.24
Nodes (5): QualiteDonneesContexte, QualiteDonneesProbleme, Any, Requêtes pour les statistiques du service, StatsRepository

### Community 24 - "Community 24"
Cohesion: 0.08
Nodes (22): Config, EmbeddedSupplier, FamilyFacet, FamilyFacetSubFamily, ManufacturerRef, PreferredSupplierInfo, Référence fabricant légère pour la liste des articles, Schéma léger pour la liste des articles (+14 more)

### Community 25 - "Community 25"
Cohesion: 0.17
Nodes (11): Any, Récupère toutes les commandes avec filtres, pagination et facets par statut, Convertit les Decimal en float pour la sérialisation JSON, Mappe les colonnes supplier en objet imbriqué, Crée une nouvelle commande fournisseur, Met à jour une commande existante, Supprime une commande (cascade sur les lignes), Récupère les lignes enrichies pour l'export (+3 more)

### Community 26 - "Community 26"
Cohesion: 0.14
Nodes (15): InterventionStatusLogRepository, Any, Récupère un log par ID avec détails enrichis, Repository pour les logs de changement de statut d'intervention, Récupère tous les logs d'une intervention, triés par date DESC, Convertit une valeur en int, retourne None si impossible, Crée un nouveau log de changement de statut.          Le trigger trg_sync_status, Liste tous les logs avec filtres optionnels (+7 more)

### Community 27 - "Community 27"
Cohesion: 0.11
Nodes (18): get_category(), get_category_subcategories(), list_categories(), Request, Liste toutes les catégories d'actions, Récupère une catégorie par ID, Récupère les sous-catégories d'une catégorie, ActionCategoryOut (+10 more)

### Community 28 - "Community 28"
Cohesion: 0.12
Nodes (14): ApiKeyRepository, _generate_secret(), _hash_secret(), Vérifie un secret brut, retourne {role_code, key_id} ou None., Met à jour last_used_at de façon best-effort (appelé en fire-and-forget)., Accès DB pour les clés d'API machine-to-machine., Crée une clé avec le rôle MCP. Retourne le secret brut une seule fois., create_api_key() (+6 more)

### Community 29 - "Community 29"
Cohesion: 0.10
Nodes (13): Génération PDF avec WeasyPrint et Jinja2, Rend le template Jinja2 avec les données, Convertit HTML en PDF avec WeasyPrint, Filtre Jinja2: formate date ISO en YYYY-MM-DD, Filtre Jinja2: traduit codes priorité, QRGenerator, Génère QR code pointant vers intervention          Args:             interventio, Génération QR codes avec overlay logo optionnel (+5 more)

### Community 30 - "Community 30"
Cohesion: 0.16
Nodes (11): _audit_task_from_action(), Any, Récupère les demandes d'achat liées à une action (PurchaseRequestListItem), Récupère les tâches liées à cette action via la table de jonction M2M., Récupère les actions groupées par date (created_at::date), triées du plus récent, Audite une transition de statut de tâche déclenchée par une action., Récupère une action avec détail de sous-catégorie et couleur, Ajoute une nouvelle action à une intervention.          Si tasks est fourni, cha (+3 more)

### Community 31 - "Community 31"
Cohesion: 0.09
Nodes (21): InterventionIn, Config, DerivedStatus, DispatchError, DispatchResult, EquipementInfo, LinkedOrderLineDetail, PurchaseRequestDetail (+13 more)

### Community 32 - "Community 32"
Cohesion: 0.19
Nodes (10): Any, Récupère les articles avec fournisseur préféré embarqué, Retourne les compteurs famille/sous-famille en une seule requête GROUP BY., Construit la clause WHERE et les paramètres associés, Récupère un article par ID avec ses fournisseurs et le template de sous-famille, Crée un nouvel article en stock, Met à jour un article existant, Met à jour uniquement la quantité d'un article (+2 more)

### Community 33 - "Community 33"
Cohesion: 0.12
Nodes (20): create_intervention_type(), InterventionCreate, add_stats_to_intervention(), delete_intervention(), force_close_linked_request(), get_intervention_actions(), list_intervention_types(), list_interventions() (+12 more)

### Community 34 - "Community 34"
Cohesion: 0.14
Nodes (16): PasswordChange, ProfileUpdate, Any, Met à jour prénom, nom et/ou initiales de l'utilisateur., UserRepository, change_my_password(), get_current_user(), get_user() (+8 more)

### Community 35 - "Community 35"
Cohesion: 0.10
Nodes (19): Config, Schémas Pydantic pour les familles de stock, Schéma de création d'une famille de stock, Schéma de mise à jour d'une famille de stock, Schéma détaillé d'une famille avec ses sous-familles, Réponse standard enveloppée pour un détail de famille., Schéma léger pour la liste des familles, StockFamilyDetail (+11 more)

### Community 36 - "Community 36"
Cohesion: 0.11
Nodes (17): InterventionsStats, Statistiques interventions pour endpoint /stats, InterventionActionDetail, InterventionActionIn, InterventionActionPatch, InterventionActionsByDate, InterventionDetail, InterventionTaskValidationRequest (+9 more)

### Community 37 - "Community 37"
Cohesion: 0.17
Nodes (11): Récupère les actions d'une intervention avec détail de sous-catégorie et couleur, Récupère toutes les tâches d'une intervention, triées par sort_order., Any, Met à jour une demande d'achat existante, Mappe un code statut vers objet DerivedStatus, Liste optimisée avec statut dérivé et compteurs agrégés.         Retourne Purcha, Détail complet avec contexte enrichi.         Retourne PurchaseRequestDetail ave, Récupère les order_lines enrichis avec fournisseur, ref catalogue et fabricant (+3 more)

### Community 38 - "Community 38"
Cohesion: 0.19
Nodes (12): DatabaseError, Erreur de base de données (500), StockFamilyIn, Repository pour les familles de stock, Met à jour une famille de stock (code et/ou label).         Si le code change, m, Crée une nouvelle famille de stock.          Raises:             ValidationError, Liste toutes les familles de stock avec le nombre de sous-familles          Retu, Récupère une famille par son code avec ses sous-familles et templates          A (+4 more)

### Community 39 - "Community 39"
Cohesion: 0.11
Nodes (17): Config, Schéma d'entrée pour modifier une référence fournisseur (stock_item_id et suppli, Schéma léger pour la liste, Schéma d'entrée pour créer une référence fournisseur, StockItemSupplierIn, StockItemSupplierListItem, StockItemSupplierUpdate, StockItemSupplierIn (+9 more)

### Community 40 - "Community 40"
Cohesion: 0.12
Nodes (17): delete_purchase_request(), dispatch_pending_requests(), get_purchase_request(), list_purchase_requests(), list_purchase_requests_optimized(), Any, date, Liste les demandes d'achat filtrées par statut dérivé.      Statuts valides : TO (+9 more)

### Community 41 - "Community 41"
Cohesion: 0.18
Nodes (8): ActionCategoryRepository, Any, Récupère toutes les catégories avec leurs sous-catégories, Récupère une catégorie par ID, Requêtes pour le domaine action_category, Any, Récupère une sous-catégorie par ID, Récupère les sous-catégories d'une catégorie

### Community 42 - "Community 42"
Cohesion: 0.15
Nodes (8): Compte le nombre total d'équipements avec les mêmes filtres que get_all., Retourne le nombre d'équipements par classe., Retourne un placeholder pour le code du statut fermé (comparaison directe sur st, Construit la clause WHERE et les params associés pour les filtres de liste., Supprime un équipement, Récupère les sous-équipements d'un équipement parent avec health, Récupère les statistiques détaillées d'un équipement, avec filtre période option, Récupère les équipements paginés - liste légère avec health

### Community 43 - "Community 43"
Cohesion: 0.14
Nodes (16): create_task(), delete_task(), get_progress(), get_task(), list_tasks(), patch_task(), Any, InterventionTaskIn (+8 more)

### Community 44 - "Community 44"
Cohesion: 0.12
Nodes (16): Liste toutes les lignes de commande avec filtres optionnels, Met à jour une ligne de commande existante, Liste les commandes fournisseur avec pagination et facets par statut, Met à jour une commande fournisseur existante, SupplierIn, SupplierOrderUpdate, create_supplier(), get_supplier() (+8 more)

### Community 45 - "Community 45"
Cohesion: 0.12
Nodes (16): Config, LinkedPurchaseRequest, ManufacturerInfo, PurchaseRequestLink, Demande d'achat liée à la ligne de commande, Référence de l'article dans le catalogue du fournisseur, Informations fabricant de l'article, Schéma léger pour la liste (+8 more)

### Community 46 - "Community 46"
Cohesion: 0.21
Nodes (9): Any, Requêtes pour le domaine supplier, Crée un nouveau fournisseur, Met à jour un fournisseur existant, Supprime un fournisseur, Récupère tous les fournisseurs avec filtres optionnels, Récupère un fournisseur par ID, Récupère un fournisseur par code (+1 more)

### Community 47 - "Community 47"
Cohesion: 0.14
Nodes (15): Récupère une action par ID avec contexte complet de l'intervention parente, add_action(), get_action(), list_actions(), patch_action(), Any, date, UUID (+7 more)

### Community 48 - "Community 48"
Cohesion: 0.20
Nodes (14): AuditLogCreate, AuditRepository, create_log(), get_briefing(), get_logs(), list_reasons(), datetime, Request (+6 more)

### Community 49 - "Community 49"
Cohesion: 0.17
Nodes (10): EquipementStatutRepository, Any, Requêtes pour le domaine statuts d'équipement, Récupère tous les statuts actifs, triés par ordre_affichage, Routes API pour les statuts d'équipement, Config, Schémas Pydantic pour les statuts d'équipement, Statut d'équipement (référentiel) (+2 more)

### Community 50 - "Community 50"
Cohesion: 0.13
Nodes (14): Récupère une ligne par ID avec stock_item et purchase_requests, Crée une nouvelle ligne de commande fournisseur, Récupère une commande par ID avec ses lignes et fournisseur, Récupère une commande par numéro avec fournisseur, create_supplier_order(), export_supplier_order_csv(), export_supplier_order_email(), get_supplier_order() (+6 more)

### Community 51 - "Community 51"
Cohesion: 0.21
Nodes (13): check_email_flood(), check_ip_blocklist(), check_ip_flood(), Lève 429 si l'IP est dans ip_blocklist (permanente ou non expirée)., Lève 429 si ≥ 5 échecs pour cet email dans les 15 dernières minutes., Lève 429 si ≥ 20 tentatives depuis cette IP dans la dernière heure., Enregistre une tentative de connexion., record_attempt() (+5 more)

### Community 52 - "Community 52"
Cohesion: 0.22
Nodes (12): _handle_api_key(), _is_public(), JWTMiddleware, Request, _random_delay(), Branche d'authentification par clé d'API (X-API-Key)., Fire-and-forget : met à jour last_used_at., Vérifie en BDD que l'utilisateur existe, est actif,     et que son rôle correspo (+4 more)

### Community 53 - "Community 53"
Cohesion: 0.31
Nodes (4): check_permission(), PermissionCache, Cache mémoire de la matrice role_code → {endpoint_code}.     Chargé depuis tunne, reload_permissions()

### Community 54 - "Community 54"
Cohesion: 0.19
Nodes (9): ComplexityFactorRepository, Any, Récupère tous les facteurs de complexité, Récupère un facteur de complexité par code, Requêtes pour le domaine complexity_factor, get_factor(), list_factors(), Liste tous les facteurs de complexité (+1 more)

### Community 55 - "Community 55"
Cohesion: 0.24
Nodes (8): EquipementClassRepository, Any, Met à jour une classe d'équipement, Requêtes pour le domaine classes d'équipement, Supprime une classe d'équipement, Récupère toutes les classes d'équipement, Récupère une classe d'équipement par ID, Crée une nouvelle classe d'équipement

### Community 56 - "Community 56"
Cohesion: 0.14
Nodes (13): Liste tous les statuts d'équipement actifs, triés par ordre d'affichage, EquipementPatch, get_equipement(), get_equipement_health(), get_equipement_stats(), list_equipements(), patch_equipement(), Routes pour les équipements (+5 more)

### Community 57 - "Community 57"
Cohesion: 0.15
Nodes (8): InterventionRequestValidator, Any, Validation des règles métier pour les demandes d'intervention.      Règles de li, Valide les règles métier avant création d'une demande d'intervention., Retourne les transitions autorisées depuis un statut donné, avec descriptions., Validation des règles métier pour les commandes fournisseur, Valide qu'une transition de statut est autorisée.          Transitions autorisée, SupplierOrderValidator

### Community 58 - "Community 58"
Cohesion: 0.19
Nodes (13): Récupère un article par référence, create_stock_item(), delete_stock_item(), get_stock_item(), get_stock_item_by_ref(), Récupère un article par ID avec ses fournisseurs, template et caractéristiques, Crée un nouvel article en stock (legacy ou template-based), Met à jour un article existant (respect immutabilité template) (+5 more)

### Community 59 - "Community 59"
Cohesion: 0.29
Nodes (12): _get_client_ip(), get_me(), _hash_token(), _log_security_event(), logout(), LogoutPayload, Request, Rotation du refresh token.     Détection de vol : si le token est déjà révoqué, (+4 more)

### Community 60 - "Community 60"
Cohesion: 0.19
Nodes (9): ExportError, ForbiddenError, Erreur lors de la génération d'export (500), Erreur rendu PDF/QR (500), RenderError, FastAPI, Gestion centralisée des erreurs et exceptions, Enregistre tous les handlers d'erreur personnalisés (+1 more)

### Community 61 - "Community 61"
Cohesion: 0.21
Nodes (12): Passe à 'cloturee' toutes les DIs en statut 'acceptee' dont l'intervention, create_request(), get_request(), list_requests(), Any, UUID, Liste les demandes d'intervention avec filtres.     Retourne une réponse paginée, Détail d'une demande d'intervention avec son historique de statuts (+4 more)

### Community 62 - "Community 62"
Cohesion: 0.19
Nodes (7): PurchaseRequestRepository, Requêtes pour le domaine purchase_request, Supprime une demande d'achat, Vérifie qu'une demande existe, lève NotFoundError sinon., Calcule le statut dérivé basé sur les compteurs agrégés.          Règles métier, Calcule le statut dérivé basé sur les order_lines.         Wrapper autour de _de, Bloque les écritures DA si la demande est liée à une intervention fermée.

### Community 63 - "Community 63"
Cohesion: 0.17
Nodes (11): Récupère toutes les lignes d'une commande avec détails, Supprime une ligne de commande (cascade sur M2M), get_lines_by_order(), patch_supplier_order_line(), Retire le lien avec une demande d'achat, Met à jour partiellement une ligne (seuls les champs fournis sont modifiés), unlink_purchase_request(), Supprime une commande fournisseur (+3 more)

### Community 64 - "Community 64"
Cohesion: 0.17
Nodes (9): Config, PasswordChange, ProfileUpdate, Schema complet pour détail utilisateur, Mise à jour du profil : prénom, nom, initiales, Changement de mot de passe, Schema léger pour listes d'utilisateurs, UserListItem (+1 more)

### Community 65 - "Community 65"
Cohesion: 0.24
Nodes (10): health_endpoint(), Route publique: vérification de santé de l'API avec état des dépendances, check_auth_service(), check_database_connection(), health_check(), HealthCheckResponse, Vérifie la connexion à PostgreSQL via le pool., Vérifie que le système d'auth JWT natif est opérationnel. (+2 more)

### Community 66 - "Community 66"
Cohesion: 0.24
Nodes (9): _compute_diff(), _extract_entity(), Any, Request, Middleware d'audit log.  Interceptionne PATCH/POST/DELETE sur les entités métier, Appelle fn_audit_log_decision() ; les erreurs n'interrompent pas la réponse., Retourne (entity_type, entity_id_str) ou None., Retourne {champ: (ancienne_valeur, nouvelle_valeur)} pour les champs modifiés. (+1 more)

### Community 67 - "Community 67"
Cohesion: 0.25
Nodes (10): create_access_token(), create_refresh_token(), decode_access_token(), extract_user_from_token(), Any, Émet un access token JWT HS256 valide ACCESS_TOKEN_EXPIRE_MINUTES minutes., Génère un refresh token aléatoire 32 bytes.     Retourne (token_clair, token_has, Décode et vérifie un access token.     Rejette explicitement alg:none.     Lève (+2 more)

### Community 68 - "Community 68"
Cohesion: 0.25
Nodes (8): ChargeTechniquePeriod, ComplexityFactorBreakdown, Calcule la charge technique pour une seule période, Formate la ventilation par facteur de complexité, Retourne une période vide quand pas de données, ChargeBreakdown, Period, TauxDepannageEvitable

### Community 69 - "Community 69"
Cohesion: 0.22
Nodes (7): DashboardRepository, Any, Repository pour les données de dashboard/menu., Retourne un résumé des comptages pour les badges du menu.          Endpoint lége, Requêtes pour agrégations de dashboard (compteurs pour badges menu), get_dashboard_summary(), Endpoints pour le dashboard et les badges de menu.

### Community 70 - "Community 70"
Cohesion: 0.20
Nodes (9): list_statuses(), Référentiel des statuts de demande d'intervention, list_stock_items(), Liste les articles avec filtres, pagination et facettes famille/sous-famille, paginated(), Any, Retourne { items, pagination, facets?, audit? } pour une liste paginée., Passe-travers explicite pour les listes plates de référentiel (statuts, types…). (+1 more)

### Community 71 - "Community 71"
Cohesion: 0.33
Nodes (6): Any, Récupère tous les services actifs, Récupère un service par ID, Crée un nouveau service, Met à jour un service, ServiceRepository

### Community 72 - "Community 72"
Cohesion: 0.25
Nodes (6): Calcule statut de charge, Calcule statut de fragmentation, Calcule statut capacité de pilotage, Statut couleur du taux de dépannage évitable, StatusLabel, Retourne le label lisible d'un code statut.

### Community 73 - "Community 73"
Cohesion: 0.22
Nodes (9): lifespan(), ping_endpoint(), FastAPI, Route publique: ping rapide pour vérifier que l'API répond, Initialise le pool DB, charge les permissions et synchronise le catalogue d'endp, close_pool(), init_pool(), Ferme toutes les connexions du pool (arrêt de l'application). (+1 more)

### Community 74 - "Community 74"
Cohesion: 0.20
Nodes (9): Config, InterventionCreate, InterventionIn, InterventionRef, InterventionStats, Schéma d'entrée pour créer une intervention (champs requis par le trigger), Schéma d'entrée pour modifier une intervention (tous les champs optionnels), Stats calculées pour une intervention (+1 more)

### Community 75 - "Community 75"
Cohesion: 0.31
Nodes (9): get_anomalies_saisie(), get_charge_technique(), get_qualite_donnees(), get_service_status(), date, Request, Calcule les métriques de santé du service de maintenance., [BETA] Analyse de la charge technique: où va le temps de maintenance et quelle p (+1 more)

### Community 76 - "Community 76"
Cohesion: 0.22
Nodes (8): ApiKeyCreate, ApiKeyListItem, ApiKeyPatch, Réponse unique à la création — contient le secret brut (une seule fois)., Clé d'API dans la liste — sans secret ni hash., Modification partielle d'une clé d'API., Payload de création d'une clé d'API., ApiKeyCreate

### Community 77 - "Community 77"
Cohesion: 0.18
Nodes (12): _is_authenticated(), Request, Dépendance FastAPI : vérifie qu'un endpoint_code est autorisé pour le rôle., Retourne True si la requête est authentifiée par JWT (user_id) ou clé API (api_k, Vérifie que la requête est authentifiée (JWT ou clé API).     Retourne user_id (, Dépendance FastAPI : restreint l'accès aux rôles listés.     Accepte JWT et clés, require_authenticated(), require_permission() (+4 more)

### Community 78 - "Community 78"
Cohesion: 0.22
Nodes (8): get_stock_family(), list_stock_families(), patch_stock_family(), Routes pour les familles de stock, Liste toutes les familles de stock      Retourne la liste des codes de famille a, Récupère une famille par son code avec ses sous-familles      Args:         fami, Renomme une famille de stock (met à jour family_code sur toutes les sous-famille, StockFamilyPatch

### Community 79 - "Community 79"
Cohesion: 0.29
Nodes (7): ColoredFormatter, Ajoute les headers de sécurité HTTP sur toutes les réponses., Custom formatter with colors for log levels, SecurityHeadersMiddleware, AuditMiddleware, Trace les mutations métier en appelant fn_audit_log_decision() après chaque succ, BaseHTTPMiddleware

### Community 80 - "Community 80"
Cohesion: 0.29
Nodes (4): Request, Trouve ou crée un supplier_order OPEN pour un fournisseur.         Retourne (ord, Crée ou fusionne la ligne de commande et lie la purchase_request., Dispatch toutes les demandes PENDING_DISPATCH vers des supplier_orders.

### Community 81 - "Community 81"
Cohesion: 0.29
Nodes (5): BaseSettings, Config, Configuration globale de l'API, Liste des origines autorisées pour CORS, Settings

### Community 82 - "Community 82"
Cohesion: 0.33
Nodes (5): ExportRepository, Récupère uniquement le code intervention (lightweight pour QR), Repository spécialisé pour données d'export, Récupère une intervention par ID avec équipement et stats calculées depuis les a, get_intervention()

### Community 83 - "Community 83"
Cohesion: 0.29
Nodes (4): _map_task(), Liste les tâches avec filtres optionnels., Tâches groupées par intervention avec pagination offset sur les interventions., Mappe les colonnes assigned_* en objet assigned_to imbriqué.     Convertit aussi

### Community 84 - "Community 84"
Cohesion: 0.29
Nodes (4): InterventionTaskDelete, InterventionTaskIn, InterventionTaskPatch, TaskProgressOut

### Community 85 - "Community 85"
Cohesion: 0.29
Nodes (5): GenerateOccurrencesResult, OccurrenceSkipIn, PreventiveOccurrenceOut, Résultat de la procédure de réparation des occurrences corrompues., RepairOccurrencesResult

### Community 86 - "Community 86"
Cohesion: 0.33
Nodes (5): GammeStepIn, GammeStepOut, PreventivePlanIn, PreventivePlanOut, PreventivePlanUpdate

### Community 87 - "Community 87"
Cohesion: 0.33
Nodes (4): ChargeTechniqueResponse, Analyse de la charge technique sur une ou plusieurs périodes, Découpe la plage en sous-périodes selon le type, ChargeTechniqueParams

### Community 88 - "Community 88"
Cohesion: 0.40
Nodes (5): check_connection(), db_connection(), Pool de connexions PostgreSQL (psycopg2 ThreadedConnectionPool).  Usage dans les, Context manager pour utilisation avec `with` :          with db_connection() as, Vérifie que le pool fonctionne. Retourne 'connected' ou message d'erreur.

### Community 89 - "Community 89"
Cohesion: 0.33
Nodes (5): ExportMetadata, PDFExportInfo, QRExportInfo, Info export PDF (pour docs OpenAPI), Info export QR (pour docs OpenAPI)

### Community 90 - "Community 90"
Cohesion: 0.33
Nodes (6): create_purchase_request(), Crée une nouvelle demande d'achat.      **Audit obligatoire** : le champ `reason, Met à jour une demande d'achat existante.      Modification autorisée uniquement, update_purchase_request(), Statistiques agrégées, PurchaseRequestIn

### Community 91 - "Community 91"
Cohesion: 0.33
Nodes (3): Formate la ventilation par classe d'équipement, Génère une explication du diagnostic pour cette classe, Génère une recommandation d'action pour cette classe

### Community 92 - "Community 92"
Cohesion: 0.40
Nodes (4): AuditRules, get_audit_rules(), Utilitaire pour charger les règles d'audit d'une entité., Retourne les règles d'audit pour une entité.      - Catégories manual + user → a

### Community 93 - "Community 93"
Cohesion: 0.40
Nodes (5): get_purchase_requests_by_intervention(), [v1.2.0] Filtre par intervention avec choix de granularité.     - view=list : re, Demandes liées à une intervention. Alias de /intervention/{id}/optimized?view=li, PurchaseRequestDetail, PurchaseRequestListItem

### Community 95 - "Community 95"
Cohesion: 0.50
Nodes (3): ComplexityFactorOut, Config, Schéma de sortie pour un facteur de complexité

### Community 96 - "Community 96"
Cohesion: 0.50
Nodes (3): Utilitaires de nettoyage et sécurité, Supprime les balises HTML et décode les entités HTML.          Exemples:     - ", strip_html()

### Community 97 - "Community 97"
Cohesion: 0.67
Nodes (3): ActionCategoryActivePatch, ActionCategoryPatch, patch_action_category()

### Community 99 - "Community 99"
Cohesion: 0.67
Nodes (3): patch_complexity_factor(), ComplexityFactorActivePatch, ComplexityFactorPatch

## Knowledge Gaps
- **60 isolated node(s):** `Config`, `AdminUserCreate`, `AdminUserUpdate`, `AdminUserRolePatch`, `AdminUserActivePatch` (+55 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `release_connection()` connect `Community 4` to `Community 0`, `Community 3`, `Community 6`, `Community 7`, `Community 8`, `Community 9`, `Community 10`, `Community 11`, `Community 12`, `Community 14`, `Community 15`, `Community 16`, `Community 18`, `Community 19`, `Community 20`, `Community 22`, `Community 23`, `Community 25`, `Community 26`, `Community 28`, `Community 30`, `Community 32`, `Community 33`, `Community 34`, `Community 37`, `Community 38`, `Community 41`, `Community 42`, `Community 46`, `Community 49`, `Community 51`, `Community 52`, `Community 53`, `Community 54`, `Community 55`, `Community 59`, `Community 62`, `Community 68`, `Community 69`, `Community 71`, `Community 80`, `Community 82`, `Community 83`, `Community 88`, `Community 94`, `Community 97`, `Community 98`, `Community 99`?**
  _High betweenness centrality (0.179) - this node is a cross-community bridge._
- **Why does `DatabaseError` connect `Community 38` to `Community 0`, `Community 3`, `Community 4`, `Community 5`, `Community 6`, `Community 8`, `Community 9`, `Community 10`, `Community 12`, `Community 13`, `Community 14`, `Community 15`, `Community 16`, `Community 17`, `Community 18`, `Community 19`, `Community 20`, `Community 22`, `Community 23`, `Community 25`, `Community 26`, `Community 30`, `Community 32`, `Community 34`, `Community 37`, `Community 41`, `Community 42`, `Community 46`, `Community 51`, `Community 54`, `Community 55`, `Community 60`, `Community 61`, `Community 62`, `Community 68`, `Community 71`, `Community 72`, `Community 73`, `Community 80`, `Community 82`, `Community 87`, `Community 94`?**
  _High betweenness centrality (0.177) - this node is a cross-community bridge._
- **Why does `NotFoundError` connect `Community 12` to `Community 0`, `Community 3`, `Community 4`, `Community 6`, `Community 7`, `Community 8`, `Community 9`, `Community 10`, `Community 11`, `Community 14`, `Community 15`, `Community 16`, `Community 17`, `Community 18`, `Community 20`, `Community 22`, `Community 25`, `Community 26`, `Community 28`, `Community 30`, `Community 32`, `Community 34`, `Community 37`, `Community 38`, `Community 41`, `Community 42`, `Community 46`, `Community 49`, `Community 51`, `Community 54`, `Community 55`, `Community 60`, `Community 61`, `Community 62`, `Community 71`, `Community 82`?**
  _High betweenness centrality (0.141) - this node is a cross-community bridge._
- **Are the 238 inferred relationships involving `release_connection()` (e.g. with `.get_all()` and `.get_by_id()`) actually correct?**
  _`release_connection()` has 238 INFERRED edges - model-reasoned connections that need verification._
- **Are the 193 inferred relationships involving `DatabaseError` (e.g. with `ActionCategoryRepository` and `.get_all()`) actually correct?**
  _`DatabaseError` has 193 INFERRED edges - model-reasoned connections that need verification._
- **Are the 147 inferred relationships involving `NotFoundError` (e.g. with `ActionCategoryRepository` and `.get_by_id()`) actually correct?**
  _`NotFoundError` has 147 INFERRED edges - model-reasoned connections that need verification._
- **Are the 122 inferred relationships involving `ValidationError` (e.g. with `CharacteristicValue` and `EquipementClassRepository`) actually correct?**
  _`ValidationError` has 122 INFERRED edges - model-reasoned connections that need verification._