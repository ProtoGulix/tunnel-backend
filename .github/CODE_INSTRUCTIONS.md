# Tunnel GMAO Backend - Instructions de Développement

## 📋 Vue d'Ensemble du Projet

**Projet:** API REST Backend GMAO (Gestion de Maintenance Assistée par Ordinateur)
**Version:** 1.0.1
**Licence:** AGPL-3.0
**Stack:** FastAPI + PostgreSQL + Directus (JWT)

### Mission
Système de gestion de maintenance industrielle pour PME (10-100 machines, 1-10 personnes en maintenance). L'objectif est de fournir un outil simple, fiable et pratique qui reflète le travail terrain réel sans bureaucratie excessive.

### Philosophie Core
- **Les actions sont l'unité de travail réelle** (pas les interventions)
- **Field-first design** - conception orientée terrain
- **Simplicité avant tout** - pas de sur-ingénierie
- **Traçabilité fiable** - PostgreSQL comme source unique de vérité
- **Code lisible en 30 secondes** - testabilité et maintenabilité prioritaires

---

## 🎯 Principes de Développement

### YAGNI (You Aren't Gonna Need It)
- Ne jamais ajouter de fonctionnalités "au cas où"
- Implémenter uniquement ce qui est demandé explicitement
- Pas d'abstraction prématurée
- Trois lignes similaires valent mieux qu'une abstraction inutile

### KISS (Keep It Simple, Stupid)
- Solutions simples et directes
- Pas de patterns complexes sans raison claire
- Code auto-documenté (éviter commentaires excessifs)
- Une fonction = une responsabilité claire

### Testabilité First
- Code compréhensible en 30 secondes maximum
- Fonctions courtes et focalisées
- Dépendances explicites
- Pas de magie cachée

### No Backward Compatibility Hacks
- Supprimer le code inutilisé complètement
- Pas de variables `_unused`
- Pas de commentaires `# removed`
- Pas de re-exports inutiles

---

## 🏗️ Architecture Technique

### Stack Technologique

**Backend:**
```python
FastAPI==0.109.0        # Framework web async
uvicorn==0.27.0         # Serveur ASGI
pydantic==2.5.3         # Validation de données
pydantic-settings==2.1.0 # Gestion configuration
```

**Base de Données:**
```python
pg8000==1.31.2          # Driver PostgreSQL pur Python
```

**Authentification:**
```python
python-jose==3.3.0      # JWT handling
PyJWT==2.10.1           # Token processing
cryptography             # Cryptographie
```

**Utilitaires:**
```python
httpx==0.25.2           # HTTP client async
python-dotenv==1.0.0    # Variables d'environnement
```

### Flow de Requête

```
Client (JWT dans Authorization header)
    ↓
JWTMiddleware (validation, extraction user_id/role)
    ↓
request.state enrichi (user_id, role)
    ↓
Route Handler (GET/POST endpoints)
    ↓
Repository Layer (requêtes PostgreSQL via pg8000)
    ↓
Schema Layer (validation Pydantic)
    ↓
JSON Response (avec gestion d'erreurs)
```

### Décisions Architecturales

**✅ À FAIRE:**
- PostgreSQL comme source unique de vérité
- Stateless FastAPI (connection-per-request)
- Stats calculées en SQL (pas en Python)
- Schemas légers pour listes, complets pour détails
- Logging centralisé avec couleurs
- Validation métier dans la couche repository

**❌ À ÉVITER:**
- Pas de cache Redis (YAGNI)
- Pas d'ORM complexe (utiliser pg8000 directement)
- Pas d'agrégations complexes en Python
- Pas de session state côté serveur
- Pas de WebSockets (hors scope)

---

## 📁 Structure des Modules

### Pattern de Module Standard

Chaque domaine fonctionnel suit cette structure:

```
api/<domain>/
├── routes.py          # Endpoints FastAPI (GET/POST/PUT/DELETE)
├── repo.py            # Requêtes SQL et logique base de données
├── schemas.py         # Modèles Pydantic (In/Out)
├── validators.py      # Validations métier (optionnel)
└── __init__.py        # Exports publics
```

### Exemple: Module Intervention Actions

**routes.py** - Endpoints FastAPI:
```python
from fastapi import APIRouter, Depends, HTTPException, Request
from api.intervention_actions.schemas import InterventionActionIn, InterventionActionOut
from api.intervention_actions.repo import InterventionActionsRepository

router = APIRouter(prefix="/intervention_actions", tags=["Intervention Actions"])

@router.get("", response_model=list[InterventionActionOut])
async def list_actions(request: Request):
    """Liste toutes les actions avec pagination."""
    repo = InterventionActionsRepository(request.app.state.db_url)
    return repo.list_actions()

@router.post("", response_model=InterventionActionOut, status_code=201)
async def create_action(
    action: InterventionActionIn,
    request: Request
):
    """Crée une nouvelle action avec validation métier."""
    repo = InterventionActionsRepository(request.app.state.db_url)
    return repo.create_action(action, user_id=request.state.user_id)
```

**repo.py** - Logique base de données:
```python
import pg8000.native
from api.intervention_actions.schemas import InterventionActionIn, InterventionActionOut
from api.errors.exceptions import DatabaseError, NotFoundError

class InterventionActionsRepository:
    def __init__(self, db_url: str):
        self.db_url = db_url

    def _get_connection(self):
        """Crée une connexion PostgreSQL."""
        return pg8000.native.Connection(**parse_db_url(self.db_url))

    def list_actions(self) -> list[InterventionActionOut]:
        """Récupère toutes les actions."""
        try:
            conn = self._get_connection()
            rows = conn.run("""
                SELECT id, intervention_id, description, time_spent_minutes,
                       complexity_score, created_at, user_created
                FROM intervention_actions
                ORDER BY created_at DESC
            """)
            return [InterventionActionOut(**dict(zip(columns, row))) for row in rows]
        except Exception as e:
            raise DatabaseError(f"Failed to list actions: {e}") from e
        finally:
            conn.close()

    def create_action(self, action: InterventionActionIn, user_id: str) -> InterventionActionOut:
        """Crée une action avec validation."""
        # Validation métier
        if action.time_spent_minutes % 15 != 0:
            raise ValidationError("Time must be in 15-minute increments")

        if not (1 <= action.complexity_score <= 10):
            raise ValidationError("Complexity must be between 1 and 10")

        try:
            conn = self._get_connection()
            result = conn.run("""
                INSERT INTO intervention_actions
                (intervention_id, description, time_spent_minutes, complexity_score, user_created)
                VALUES (:intervention_id, :description, :time_spent, :complexity, :user_id)
                RETURNING *
            """, **action.dict(), user_id=user_id)
            return InterventionActionOut(**result[0])
        except Exception as e:
            raise DatabaseError(f"Failed to create action: {e}") from e
        finally:
            conn.close()
```

**schemas.py** - Modèles Pydantic:
```python
from pydantic import BaseModel, Field
from datetime import datetime

class InterventionActionIn(BaseModel):
    """Schéma pour création d'action."""
    intervention_id: int = Field(..., description="ID de l'intervention")
    description: str = Field(..., min_length=1, max_length=5000)
    time_spent_minutes: int = Field(..., ge=0, description="Temps en minutes (multiples de 15)")
    complexity_score: int = Field(..., ge=1, le=10, description="Score de complexité 1-10")
    complexity_annotations: list[str] | None = Field(None, description="Codes facteurs de complexité")

class InterventionActionOut(InterventionActionIn):
    """Schéma pour réponse d'action."""
    id: int
    created_at: datetime
    user_created: str

    class Config:
        from_attributes = True
```

**validators.py** - Validations métier:
```python
from api.errors.exceptions import ValidationError

def validate_time_spent(minutes: int) -> None:
    """Valide que le temps est en quarts d'heure."""
    if minutes < 0:
        raise ValidationError("Time spent cannot be negative")
    if minutes % 15 != 0:
        raise ValidationError("Time must be tracked in 15-minute increments")

def validate_complexity_score(score: int) -> None:
    """Valide le score de complexité."""
    if not (1 <= score <= 10):
        raise ValidationError("Complexity score must be between 1 and 10")

def validate_complexity_annotations(annotations: list[str], valid_codes: set[str]) -> None:
    """Valide les codes d'annotation."""
    invalid = set(annotations) - valid_codes
    if invalid:
        raise ValidationError(f"Invalid complexity codes: {', '.join(invalid)}")
```

---

## ♻️ DRY & Réutilisation de Code

### Principe: Don't Repeat Yourself

**Règle d'or:** Ne jamais dupliquer de la logique existante. Si une fonction existe déjà dans un autre module, la réutiliser plutôt que de réécrire la requête SQL ou la logique métier.

### Réutilisation Entre Repositories

**Exemple concret:** Récupérer une intervention avec ses actions

```python
# ❌ MAUVAIS - Duplication de code
class InterventionsRepository:
    def get_by_id_with_actions(self, intervention_id: int):
        """Récupère intervention avec actions - VERSION DUPLIQUÉE."""
        conn = self._get_connection()
        try:
            # Requête pour l'intervention
            intervention = conn.run(
                "SELECT * FROM interventions WHERE id = :id",
                id=intervention_id
            )[0]

            # ⚠️ ERREUR: On réécrit la logique pour récupérer les actions
            actions = conn.run(
                "SELECT * FROM intervention_actions WHERE intervention_id = :id",
                id=intervention_id
            )

            intervention["actions"] = actions
            return intervention
        finally:
            conn.close()
```

```python
# ✅ BON - Réutilisation de la fonction existante
from api.intervention_actions.repo import InterventionActionsRepository

class InterventionsRepository:
    def __init__(self, db_url: str):
        self.db_url = db_url
        # Instancier le repository d'actions pour réutilisation
        self.actions_repo = InterventionActionsRepository(db_url)

    def get_by_id_with_actions(self, intervention_id: int):
        """Récupère intervention avec actions - VERSION RÉUTILISABLE."""
        conn = self._get_connection()
        try:
            # Requête pour l'intervention
            intervention = conn.run(
                "SELECT * FROM interventions WHERE id = :id",
                id=intervention_id
            )
            if not intervention:
                raise NotFoundError(f"Intervention {intervention_id} not found")

            intervention_data = intervention[0]

            # ✅ Réutiliser la fonction existante du repository actions
            actions = self.actions_repo.get_by_intervention_id(intervention_id)

            intervention_data["actions"] = actions
            return intervention_data
        finally:
            conn.close()
```

### Pattern d'Import et Réutilisation

**1. Import du repository nécessaire:**
```python
from api.intervention_actions.repo import InterventionActionsRepository
from api.equipements.repo import EquipementsRepository
from api.complexity_factors.repo import ComplexityFactorsRepository
```

**2. Instanciation dans __init__:**
```python
class InterventionsRepository:
    def __init__(self, db_url: str):
        self.db_url = db_url
        # Repositories réutilisables
        self.actions_repo = InterventionActionsRepository(db_url)
        self.equipements_repo = EquipementsRepository(db_url)
```

**3. Appel des fonctions existantes:**
```python
def get_full_intervention(self, intervention_id: int):
    """Récupère intervention complète avec toutes relations."""
    # Récupérer l'intervention de base
    intervention = self.get_by_id(intervention_id)

    # Réutiliser les fonctions existantes
    intervention["actions"] = self.actions_repo.get_by_intervention_id(intervention_id)
    intervention["equipement"] = self.equipements_repo.get_by_id(intervention.equipement_id)

    return intervention
```

### Avantages de la Réutilisation

**✅ Cohérence:**
- Même logique de validation partout
- Gestion d'erreurs uniforme
- Même format de réponse

**✅ Maintenabilité:**
- Un seul endroit à modifier si la logique change
- Moins de code à tester
- Réduction des bugs

**✅ Performance:**
- Connexions gérées de manière optimale
- Pas de requêtes redondantes

**✅ Lisibilité:**
```python
# Clair et explicite
actions = self.actions_repo.get_by_intervention_id(intervention_id)

# vs requête SQL brute répétée partout
actions = conn.run("SELECT * FROM intervention_actions WHERE...")
```

### Cas d'Usage Courants

**1. Validation de références (Foreign Keys):**
```python
class InterventionActionsRepository:
    def create_action(self, action: InterventionActionIn, user_id: str):
        """Crée une action en validant l'intervention existe."""
        # Réutiliser la validation d'existence
        from api.interventions.repo import InterventionsRepository
        interventions_repo = InterventionsRepository(self.db_url)

        # Vérifie que l'intervention existe (lève NotFoundError si non)
        interventions_repo.get_by_id(action.intervention_id)

        # Continuer avec la création
        conn = self._get_connection()
        try:
            result = conn.run("""
                INSERT INTO intervention_actions (...)
                VALUES (...)
            """, **action.dict(), user_id=user_id)
            return result[0]
        finally:
            conn.close()
```

**2. Enrichissement de données:**
```python
class EquipementsRepository:
    def get_with_stats(self, equipement_id: int):
        """Récupère équipement avec statistiques d'interventions."""
        equipement = self.get_by_id(equipement_id)

        # Réutiliser le calcul de stats du repository interventions
        from api.interventions.repo import InterventionsRepository
        interventions_repo = InterventionsRepository(self.db_url)

        equipement["intervention_stats"] = interventions_repo.get_stats_by_equipement(
            equipement_id
        )

        return equipement
```

**3. Agrégation multi-domaines:**
```python
class StatsRepository:
    def get_service_status(self):
        """Agrège les stats de plusieurs domaines."""
        from api.interventions.repo import InterventionsRepository
        from api.intervention_actions.repo import InterventionActionsRepository
        from api.equipements.repo import EquipementsRepository

        interventions_repo = InterventionsRepository(self.db_url)
        actions_repo = InterventionActionsRepository(self.db_url)
        equipements_repo = EquipementsRepository(self.db_url)

        return {
            "total_interventions": interventions_repo.count_open(),
            "total_actions": actions_repo.count_this_month(),
            "critical_equipements": equipements_repo.count_critical(),
        }
```

### Attention aux Imports Circulaires

**⚠️ Problème potentiel:**
```python
# api/interventions/repo.py
from api.intervention_actions.repo import InterventionActionsRepository

# api/intervention_actions/repo.py
from api.interventions.repo import InterventionsRepository
# ⚠️ CIRCULAR IMPORT!
```

**✅ Solutions:**

**1. Import local (dans la fonction):**
```python
class InterventionActionsRepository:
    def create_action(self, action: InterventionActionIn):
        # Import local pour éviter circular import
        from api.interventions.repo import InterventionsRepository
        interventions_repo = InterventionsRepository(self.db_url)
        interventions_repo.get_by_id(action.intervention_id)
        # ...
```

**2. Passer les dépendances en paramètres:**
```python
class InterventionActionsRepository:
    def create_action(
        self,
        action: InterventionActionIn,
        interventions_repo: InterventionsRepository = None
    ):
        if interventions_repo is None:
            from api.interventions.repo import InterventionsRepository
            interventions_repo = InterventionsRepository(self.db_url)

        interventions_repo.get_by_id(action.intervention_id)
        # ...
```

**3. Restructurer pour éliminer la dépendance circulaire:**
```python
# Parfois, c'est le signe que la logique devrait être ailleurs
# Exemple: validation d'existence → fonction utilitaire commune
```

### Exemple Complet: GET /interventions/{id}

```python
# api/interventions/routes.py
from api.interventions.repo import InterventionsRepository

@router.get("/{intervention_id}", response_model=InterventionDetailOut)
async def get_intervention(intervention_id: int, request: Request):
    """Récupère une intervention avec détails complets."""
    repo = InterventionsRepository(request.app.state.db_url)
    return repo.get_by_id_with_actions(intervention_id)
```

```python
# api/interventions/repo.py
from api.intervention_actions.repo import InterventionActionsRepository
from api.equipements.repo import EquipementsRepository

class InterventionsRepository:
    def __init__(self, db_url: str):
        self.db_url = db_url
        # Préparer les repositories réutilisables
        self.actions_repo = InterventionActionsRepository(db_url)
        self.equipements_repo = EquipementsRepository(db_url)

    def get_by_id_with_actions(self, intervention_id: int) -> dict:
        """Récupère intervention complète avec actions."""
        conn = self._get_connection()
        try:
            # 1. Récupérer l'intervention de base
            result = conn.run(
                "SELECT * FROM interventions WHERE id = :id",
                id=intervention_id
            )
            if not result:
                raise NotFoundError(f"Intervention {intervention_id} not found")

            intervention = dict(result[0])

            # 2. ✅ Réutiliser get_by_intervention_id au lieu de réécrire la requête
            intervention["actions"] = self.actions_repo.get_by_intervention_id(
                intervention_id
            )

            # 3. ✅ Réutiliser get_by_id pour l'équipement
            if intervention.get("equipement_id"):
                intervention["equipement"] = self.equipements_repo.get_by_id(
                    intervention["equipement_id"]
                )

            return intervention
        finally:
            conn.close()
```

```python
# api/intervention_actions/repo.py
class InterventionActionsRepository:
    def get_by_intervention_id(self, intervention_id: int) -> list[dict]:
        """Récupère toutes les actions d'une intervention.

        Cette fonction est réutilisée par InterventionsRepository.
        """
        conn = self._get_connection()
        try:
            rows = conn.run("""
                SELECT
                    id, intervention_id, description,
                    time_spent_minutes, complexity_score,
                    complexity_annotations, created_at, user_created
                FROM intervention_actions
                WHERE intervention_id = :intervention_id
                ORDER BY created_at DESC
            """, intervention_id=intervention_id)

            return [dict(row) for row in rows]
        except Exception as e:
            raise DatabaseError(f"Failed to get actions: {e}") from e
        finally:
            conn.close()
```

### Checklist Réutilisation

Avant d'écrire une nouvelle fonction de repository:

- [ ] Cette logique existe-t-elle déjà ailleurs ?
- [ ] Puis-je importer et réutiliser un repository existant ?
- [ ] Y a-t-il un risque d'import circulaire ?
- [ ] La réutilisation améliore-t-elle la lisibilité ?
- [ ] La fonction réutilisée gère-t-elle correctement les erreurs ?

---

## 🔐 Authentification & Sécurité

### Middleware JWT

**Configuration:**
```python
# api/settings.py
class Settings(BaseSettings):
    DIRECTUS_URL: str
    DIRECTUS_SECRET: str
    AUTH_DISABLED: bool = False  # Pour tests uniquement
```

**Routes publiques (pas de JWT requis):**
- `/health`
- `/docs`
- `/openapi.json`
- `/redoc`
- `/favicon.ico`
- `/auth/login`

**Utilisation dans les routes:**
```python
@router.post("/intervention_actions")
async def create_action(action: InterventionActionIn, request: Request):
    # request.state.user_id est automatiquement enrichi par le middleware
    user_id = request.state.user_id
    user_role = request.state.get("role")

    # Utiliser pour traçabilité
    return repo.create_action(action, user_id=user_id)
```

### Gestion des Erreurs

**Exceptions personnalisées:**
```python
# api/errors/exceptions.py
class DatabaseError(Exception):
    """Erreur base de données."""
    pass

class NotFoundError(Exception):
    """Ressource non trouvée."""
    pass

class UnauthorizedError(Exception):
    """Non authentifié."""
    pass

class ForbiddenError(Exception):
    """Accès interdit."""
    pass

class ValidationError(Exception):
    """Erreur de validation métier."""
    pass
```

**Handlers centralisés:**
```python
# api/errors/handlers.py
from fastapi import Request, status
from fastapi.responses import JSONResponse

async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error_type": "not_found",
            "message": str(exc)
        }
    )

async def database_error_handler(request: Request, exc: DatabaseError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_type": "database_error",
            "message": "An error occurred while accessing the database"
        }
    )
```

**Enregistrement dans app.py:**
```python
from api.errors.handlers import not_found_handler, database_error_handler
from api.errors.exceptions import NotFoundError, DatabaseError

app.add_exception_handler(NotFoundError, not_found_handler)
app.add_exception_handler(DatabaseError, database_error_handler)
```

---

## 💾 Base de Données

### Conventions SQL

**Naming conventions:**
- Tables: `snake_case`, pluriel (ex: `intervention_actions`)
- Colonnes: `snake_case`
- Primary keys: `id` (serial/integer)
- Foreign keys: `<table>_id` (ex: `intervention_id`)
- Timestamps: `created_at`, `updated_at`, `deleted_at`
- User tracking: `user_created`, `user_updated`

**Exemple de requête optimisée:**
```python
def get_intervention_with_stats(self, intervention_id: int):
    """Récupère une intervention avec stats calculées en SQL."""
    query = """
        SELECT
            i.id,
            i.title,
            i.status,
            i.priority,
            i.equipement_id,
            COUNT(ia.id) as action_count,
            COALESCE(SUM(ia.time_spent_minutes), 0) as total_time_minutes,
            COALESCE(AVG(ia.complexity_score), 0) as avg_complexity
        FROM interventions i
        LEFT JOIN intervention_actions ia ON ia.intervention_id = i.id
        WHERE i.id = :intervention_id
        GROUP BY i.id
    """
    conn = self._get_connection()
    try:
        result = conn.run(query, intervention_id=intervention_id)
        if not result:
            raise NotFoundError(f"Intervention {intervention_id} not found")
        return result[0]
    finally:
        conn.close()
```

### Pattern Connection

**Connection-per-request (recommandé):**
```python
def list_items(self):
    conn = self._get_connection()
    try:
        rows = conn.run("SELECT * FROM table")
        return [ItemOut(**row) for row in rows]
    except Exception as e:
        raise DatabaseError(f"Failed to list items: {e}") from e
    finally:
        conn.close()  # TOUJOURS fermer
```

**Paramètres SQL (prévention injection):**
```python
# ✅ CORRECT - paramètres nommés
conn.run(
    "SELECT * FROM interventions WHERE id = :id AND status = :status",
    id=intervention_id,
    status="open"
)

# ❌ INCORRECT - concatenation de strings
conn.run(f"SELECT * FROM interventions WHERE id = {intervention_id}")
```

---

## 📊 Règles Métier

### Interventions

**Types d'intervention (constantes):**
```python
# api/constants.py
INTERVENTION_TYPES = {
    "CUR": "Curatif",           # Réparation après panne
    "PRE": "Préventif",         # Maintenance planifiée
    "REA": "Réactivité",        # Intervention rapide
    "BAT": "Bâtiment",          # Maintenance bâtiment
    "PRO": "Production",        # Support production
    "COF": "Cofinancement",     # Projet cofinancé
    "PIL": "Pilotage",          # Gestion/coordination
    "MES": "Mesure"             # Relevés/mesures
}
```

**Priorités (ordre croissant):**
1. `faible` - Peut attendre
2. `normal` - Traitement standard
3. `important` - À traiter rapidement
4. `urgent` - Immédiat

**Statuts:**
- Dynamiques (chargés depuis la base)
- Statut fermé: code `ferme`

### Actions d'Intervention

**Règles de validation:**
- **Temps de travail:** multiples de 15 minutes (quart d'heure)
- **Score de complexité:** entier de 1 à 10
- **Annotations de complexité:** codes valides uniquement (AUT, GEO, TEC, etc.)
- **Description:** 1-5000 caractères, HTML sanitizé

**Calculs automatiques:**
```python
# Temps total d'une intervention
total_time = SUM(action.time_spent_minutes for action in actions)

# Complexité moyenne
avg_complexity = AVG(action.complexity_score for action in actions)

# Nombre d'actions
action_count = COUNT(actions)
```

### Équipements

**Calcul de santé (health status):**
```python
def calculate_health(open_interventions: list):
    urgent_count = count(i for i in open_interventions if i.priority == "urgent")
    total_open = len(open_interventions)

    if urgent_count >= 1:
        return "critical"      # 🔴 Au moins 1 urgent
    elif total_open > 5:
        return "warning"       # 🟡 Plus de 5 ouvertes
    elif total_open > 0:
        return "maintenance"   # 🟠 Au moins 1 ouverte
    else:
        return "ok"            # 🟢 Aucune intervention
```

**Endpoints santé:**
- `/equipements` - Liste avec santé (léger)
- `/equipements/{id}/health` - Ultra-rapide (santé uniquement)
- `/equipements/{id}/stats` - Statistiques complètes (plus lourd)

---

## 🎨 Conventions de Code

### Style Python

**Python 3.9+ syntax:**
```python
# ✅ CORRECT - Python 3.9+
def list_items() -> list[ItemOut]:
    data: dict[str, str] = {"key": "value"}
    return items

# ❌ INCORRECT - Ancien style
from typing import List, Dict
def list_items() -> List[ItemOut]:
    data: Dict[str, str] = {"key": "value"}
```

**Type hints obligatoires:**
```python
# ✅ CORRECT
def create_action(action: InterventionActionIn, user_id: str) -> InterventionActionOut:
    pass

# ❌ INCORRECT
def create_action(action, user_id):
    pass
```

**Docstrings (style concis):**
```python
def calculate_stats(intervention_id: int) -> dict:
    """Calcule les statistiques d'une intervention.

    Args:
        intervention_id: ID de l'intervention

    Returns:
        Dictionnaire avec action_count, total_time, avg_complexity

    Raises:
        NotFoundError: Si l'intervention n'existe pas
        DatabaseError: En cas d'erreur base de données
    """
    pass
```

### Logging

**Configuration centralisée:**
```python
import logging

# Couleurs ANSI
COLORS = {
    "DEBUG": "\033[36m",      # Cyan
    "INFO": "\033[32m",       # Vert
    "WARNING": "\033[33m",    # Jaune
    "ERROR": "\033[31m",      # Rouge
    "CRITICAL": "\033[35m",   # Magenta
    "RESET": "\033[0m"
}

logger = logging.getLogger(__name__)
```

**Usage:**
```python
logger.info(f"Creating action for intervention {intervention_id}")
logger.warning(f"Intervention {intervention_id} has {count} pending actions")
logger.error(f"Failed to create action: {error}")
```

### Gestion des Exceptions

**Chaînage d'exceptions (PEP 3134):**
```python
# ✅ CORRECT - préserve la stack trace
try:
    result = conn.run(query)
except Exception as e:
    raise DatabaseError(f"Query failed: {query}") from e

# ❌ INCORRECT - perd le contexte
try:
    result = conn.run(query)
except Exception as e:
    raise DatabaseError(f"Query failed")
```

---

## 🧪 Tests & Qualité

### Outils de Qualité

**Pylint:**
- Objectif: 0 warnings dans les modules core
- Configuration: `.pylintrc` à la racine

**Standards:**
- PEP8 pour le style
- Type hints obligatoires
- Docstrings pour fonctions publiques
- Tests unitaires pour logique métier

### Scripts de Debug

Utiliser les scripts fournis:
```bash
python debug_app.py           # Debug général de l'app
python debug_startup.py       # Diagnostics au démarrage
python diagnostic.py          # Health checks
python generate_jwt.py        # Génération token de test
python simple_jwt_test.py     # Test validation JWT
python show_jwt.py            # Inspection de token
```

---

## 📝 Documentation

### API Manifest

Maintenir [API_MANIFEST.md](../API_MANIFEST.md) à jour avec:
- Tous les endpoints
- Paramètres de requête
- Schémas de réponse
- Codes de statut HTTP
- Exemples de requêtes/réponses

### Changelog

Format dans [CHANGELOG.md](../CHANGELOG.md):
```markdown
## [1.0.1] - 2026-01-26

### Added
- Nouveau module complexity_factors
- Validation métier dans intervention_actions

### Changed
- Amélioration gestion d'erreurs
- Migration Python 3.9+ syntax

### Fixed
- Correction chaînage d'exceptions

### Deprecated
- Aucun

### Removed
- Ancien handler d'erreurs redondant

### Security
- Amélioration validation JWT
```

### Commits

**Format conventionnel:**
```
<type>: <description>

<body optionnel>

<footer optionnel>
```

**Types:**
- `feat`: Nouvelle fonctionnalité
- `fix`: Correction de bug
- `refactor`: Refactoring sans changement fonctionnel
- `docs`: Documentation uniquement
- `test`: Ajout/modification de tests
- `chore`: Maintenance (deps, config, etc.)

**Exemples:**
```
feat: Add complexity factors module

- Create routes, repo, and schemas for complexity_factors
- Add GET /complexity_factors endpoint
- Update API manifest

fix: Correct JWT validation in middleware

Previously, expired tokens were not properly rejected.
Now using proper datetime comparison.

Closes #123
```

---

## 🚀 Déploiement

### Variables d'Environnement

**Fichier .env (development):**
```env
# Base de données
DATABASE_URL=postgresql://gmao_user:password@localhost:5432/gmao_db

# Authentification Directus
DIRECTUS_URL=http://localhost:8055
DIRECTUS_SECRET=your_secret_key_here
DIRECTUS_KEY=your_api_key_here

# Configuration API
API_ENV=development
API_TITLE=GMAO API
API_VERSION=1.0.1

# Frontend CORS
FRONTEND_URL=http://localhost:5173

# Auth (tests uniquement!)
AUTH_DISABLED=false
```

### Scripts de Lancement

**Windows:**
```batch
run.bat
```

**Unix/Linux:**
```bash
chmod +x run.sh
./run.sh
```

**Production (avec uvicorn):**
```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🔄 Workflow de Développement

### 1. Avant de Commencer

```bash
# Créer une branche
git checkout -b feature/nom-fonctionnalite

# Activer l'environnement virtuel
source .venv/bin/activate  # Unix
.venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Développement

1. **Lire le code existant** avant toute modification
2. **Suivre la structure de module standard** (routes, repo, schemas)
3. **Ajouter validations métier** dans validators.py si nécessaire
4. **Tester manuellement** via Swagger UI (`/docs`)
5. **Vérifier Pylint**: `pylint api/<module>/`

### 3. Documentation

1. **Mettre à jour API_MANIFEST.md** si nouveaux endpoints
2. **Ajouter docstrings** aux fonctions publiques
3. **Commenter le code complexe** (SQL, logique métier)

### 4. Commit & Push

```bash
# Ajouter fichiers
git add api/<module>/

# Commit avec message conventionnel
git commit -m "feat: Add new feature X"

# Pousser la branche
git push origin feature/nom-fonctionnalite
```

### 5. Merge

1. Créer Pull Request
2. Vérifier que tous les tests passent
3. Demander review si nécessaire
4. Merger dans main
5. Mettre à jour CHANGELOG.md
6. Tagger la version si release

---

## ❗ Erreurs Courantes à Éviter

### ❌ Sur-ingénierie

```python
# ❌ MAUVAIS - Abstraction prématurée
class AbstractRepository(ABC):
    @abstractmethod
    def get_connection(self): pass

class InterventionRepository(AbstractRepository):
    def get_connection(self): ...

# ✅ BON - Simple et direct
class InterventionRepository:
    def _get_connection(self):
        return pg8000.native.Connection(...)
```

### ❌ Logique Métier dans les Routes

```python
# ❌ MAUVAIS - Logique dans route
@router.post("/actions")
async def create_action(action: ActionIn):
    if action.time_spent % 15 != 0:
        raise HTTPException(400, "Invalid time")
    conn = get_db()
    result = conn.run("INSERT ...")
    return result

# ✅ BON - Logique dans repository
@router.post("/actions")
async def create_action(action: ActionIn, request: Request):
    repo = ActionsRepository(request.app.state.db_url)
    return repo.create_action(action)
```

### ❌ Oublier de Fermer les Connexions

```python
# ❌ MAUVAIS - Fuite de connexion
def get_items(self):
    conn = self._get_connection()
    return conn.run("SELECT * FROM items")

# ✅ BON - Toujours fermer
def get_items(self):
    conn = self._get_connection()
    try:
        return conn.run("SELECT * FROM items")
    finally:
        conn.close()
```

### ❌ Injection SQL

```python
# ❌ DANGEREUX - Injection SQL
query = f"SELECT * FROM users WHERE id = {user_id}"
conn.run(query)

# ✅ SÛR - Paramètres nommés
conn.run("SELECT * FROM users WHERE id = :id", id=user_id)
```

### ❌ Agrégations en Python

```python
# ❌ INEFFICACE - Calcul en Python
actions = repo.get_all_actions(intervention_id)
total_time = sum(a.time_spent_minutes for a in actions)

# ✅ EFFICACE - Calcul en SQL
query = """
    SELECT COALESCE(SUM(time_spent_minutes), 0) as total_time
    FROM intervention_actions
    WHERE intervention_id = :id
"""
```

---

## 📚 Ressources

### Documentation Officielle

- [FastAPI](https://fastapi.tiangolo.com/)
- [Pydantic](https://docs.pydantic.dev/)
- [pg8000](https://github.com/tlocke/pg8000)
- [PostgreSQL](https://www.postgresql.org/docs/)

### Fichiers Clés du Projet

- [README.md](../README.md) - Vue d'ensemble
- [API_MANIFEST.md](../API_MANIFEST.md) - Documentation API complète
- [CHANGELOG.md](../CHANGELOG.md) - Historique des versions
- [copilot-instructions.md](copilot-instructions.md) - Guidelines IA
- [tunnel-backend.instructions.md](tunnel-backend.instructions.md) - Standards techniques

### Scripts Utiles

```bash
# Lancer l'application
./run.sh                    # Unix
run.bat                     # Windows

# Générer un token JWT de test
python generate_jwt.py

# Tester la validation JWT
python simple_jwt_test.py

# Diagnostics complets
python diagnostic.py

# Debug de l'application
python debug_app.py
```

---

## 🎓 Checklist Nouveau Développeur

- [ ] Lire [README.md](../README.md)
- [ ] Configurer `.env` depuis `.env.example`
- [ ] Lancer `run.bat` ou `run.sh`
- [ ] Accéder à `/docs` (Swagger UI)
- [ ] Lire [API_MANIFEST.md](../API_MANIFEST.md)
- [ ] Explorer la structure du code (1 module complet)
- [ ] Lire [copilot-instructions.md](copilot-instructions.md)
- [ ] Lire ce fichier complètement
- [ ] Tester la création d'une action via `/docs`
- [ ] Comprendre le flow JWT (middleware → routes → repo)

---

## 📞 Support

**Issues GitHub:** [github.com/anthropics/claude-code/issues](https://github.com/anthropics/claude-code/issues)

**Questions Architecture:** Consulter les fichiers d'instructions dans `.github/`

---

**Version:** 1.0.0
**Dernière mise à jour:** 2026-01-27
**Auteur:** Équipe Tunnel GMAO
