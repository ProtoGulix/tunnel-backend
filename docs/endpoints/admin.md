# Admin

Tous les endpoints sous `/admin/` nécessitent un Bearer token valide.

**Rôles autorisés :**

- `RESP + ADMIN` : gestion utilisateurs, référentiel
- `ADMIN` seul : rôles/permissions, sécurité, endpoints catalogue

---

## Utilisateurs

| Méthode | Endpoint                           | Rôles       | Description                                   |
| ------- | ---------------------------------- | ----------- | --------------------------------------------- |
| GET     | `/admin/users`                     | RESP, ADMIN | Liste (filtres: search, is_active, role_code) |
| POST    | `/admin/users`                     | RESP, ADMIN | Créer un utilisateur                          |
| GET     | `/admin/users/{id}`                | RESP, ADMIN | Détail                                        |
| PUT     | `/admin/users/{id}`                | RESP, ADMIN | Modifier email/nom/initial                    |
| PATCH   | `/admin/users/{id}/role`           | RESP, ADMIN | Changer le rôle (révoque les tokens)          |
| PATCH   | `/admin/users/{id}/active`         | RESP, ADMIN | Activer/désactiver                            |
| POST    | `/admin/users/{id}/reset-password` | RESP, ADMIN | Génère un mot de passe temporaire             |
| DELETE  | `/admin/users/{id}`                | RESP, ADMIN | Soft delete (obfusque email + hash)           |

### POST `/admin/users` — corps

```json
{
  "email": "user@example.com",
  "password": "motdepasse",
  "first_name": "Jean",
  "last_name": "Dupont",
  "initial": "JD",
  "role_code": "TECH"
}
```

`first_name` et `last_name` sont optionnels.

### PUT `/admin/users/{id}` — corps

```json
{
  "email": "nouveau@example.com",
  "first_name": "Jean",
  "last_name": "Dupont",
  "initial": "JD"
}
```

Tous les champs sont optionnels.

### PATCH `/admin/users/{id}/role` — corps

```json
{ "role_code": "TECH" }
```

Codes valides : `ADMIN`, `RESP`, `TECH`, `OPE` (voir `GET /admin/roles`).  
Révoque automatiquement tous les refresh tokens actifs de l'utilisateur.

### PATCH `/admin/users/{id}/active` — corps

```json
{ "is_active": false }
```

Passer `false` révoque également tous les refresh tokens.

---

## Rôles et permissions

| Méthode | Endpoint                        | Rôles | Description                                          |
| ------- | ------------------------------- | ----- | ---------------------------------------------------- |
| GET     | `/admin/roles`                  | ADMIN | Liste des rôles                                      |
| GET     | `/admin/roles/matrix`           | ADMIN | Matrice complète rôles × endpoints (pour tableau UI) |
| GET     | `/admin/roles/{id}/permissions` | ADMIN | Permissions d'un rôle (liste plate)                  |
| PATCH   | `/admin/permissions/{id}`       | ADMIN | Modifier `allowed` + log audit                       |
| GET     | `/admin/audit/permissions`      | ADMIN | Historique (filtres: role_id, dates)                 |

### GET `/admin/roles/matrix` — réponse

Structure optimisée pour un tableau multi-colonnes :

```json
{
  "roles": [
    {"id": "...", "code": "ADMIN", "label": "Administrateur"},
    {"id": "...", "code": "RESP",  "label": "Responsable"}
  ],
  "modules": {
    "admin": [
      {
        "endpoint_id": "...",
        "code": "GET_admin_users",
        "method": "GET",
        "path": "/admin/users",
        "module": "admin",
        "description": "...",
        "permissions": {
          "ADMIN": {"permission_id": "...", "allowed": true},
          "RESP":  {"permission_id": "...", "allowed": true},
          "TECH":  {"permission_id": "...", "allowed": false}
        }
      }
    ],
    "interventions": [ ... ]
  }
}
```

Chaque `permission_id` peut être passé directement à `PATCH /admin/permissions/{id}`.

### PATCH `/admin/permissions/{id}` — corps

```json
{ "allowed": true }
```

---

## Catalogue des endpoints

| Méthode | Endpoint                   | Rôles | Description                           |
| ------- | -------------------------- | ----- | ------------------------------------- |
| GET     | `/admin/endpoints`         | ADMIN | Liste (filtres: module, method)       |
| GET     | `/admin/endpoints/modules` | ADMIN | Modules distincts                     |
| PATCH   | `/admin/endpoints/{id}`    | ADMIN | Modifier description/module/sensitive |
| POST    | `/admin/endpoints/sync`    | ADMIN | Rescan routes FastAPI + UPSERT        |

### PATCH `/admin/endpoints/{id}` — corps

```json
{
  "description": "Texte libre",
  "module": "interventions",
  "is_sensitive": false
}
```

Tous les champs sont optionnels.

---

## Référentiel actions

| Méthode | Endpoint                                  | Rôles       |
| ------- | ----------------------------------------- | ----------- |
| GET     | `/admin/action-categories`                | RESP, ADMIN |
| PATCH   | `/admin/action-categories/{id}`           | RESP, ADMIN |
| PATCH   | `/admin/action-categories/{id}/active`    | RESP, ADMIN |
| GET     | `/admin/action-subcategories`             | RESP, ADMIN |
| POST    | `/admin/action-subcategories`             | RESP, ADMIN |
| PATCH   | `/admin/action-subcategories/{id}`        | RESP, ADMIN |
| PATCH   | `/admin/action-subcategories/{id}/active` | RESP, ADMIN |
| GET     | `/admin/complexity-factors`               | RESP, ADMIN |
| PATCH   | `/admin/complexity-factors/{id}`          | RESP, ADMIN |
| PATCH   | `/admin/complexity-factors/{id}/active`   | RESP, ADMIN |

### PATCH `/admin/action-categories/{id}` — corps

```json
{ "label": "Nouveau libellé", "color": "#FF5733" }
```

### PATCH `/admin/action-categories/{id}/active` — corps

```json
{ "is_active": false }
```

### POST `/admin/action-subcategories` — corps

```json
{ "code": "CODE", "label": "Libellé", "category_id": 1 }
```

### PATCH `/admin/action-subcategories/{id}` — corps

```json
{ "label": "Nouveau libellé" }
```

### PATCH `/admin/complexity-factors/{id}` — corps

```json
{ "label": "Nouveau libellé", "category": "catégorie" }
```

---

## Référentiel interventions

| Méthode | Endpoint                                | Rôles       |
| ------- | --------------------------------------- | ----------- |
| GET     | `/admin/intervention-types`             | RESP, ADMIN |
| POST    | `/admin/intervention-types`             | RESP, ADMIN |
| PATCH   | `/admin/intervention-types/{id}`        | RESP, ADMIN |
| PATCH   | `/admin/intervention-types/{id}/active` | RESP, ADMIN |
| GET     | `/admin/intervention-statuses`          | RESP, ADMIN |
| PATCH   | `/admin/intervention-statuses/{code}`   | RESP, ADMIN |

### POST `/admin/intervention-types` — corps

```json
{ "code": "CODE", "label": "Libellé" }
```

### PATCH `/admin/intervention-types/{id}` — corps

```json
{ "label": "Nouveau libellé" }
```

### PATCH `/admin/intervention-statuses/{code}` — corps

`{code}` est le code texte du statut (ex : `ouvert`, `en_cours`, `ferme`).

```json
{ "label": "Nouveau libellé", "color": "#3498DB" }
```

---

## Sécurité

| Méthode | Endpoint                         | Description                                           |
| ------- | -------------------------------- | ----------------------------------------------------- |
| GET     | `/admin/security-logs`           | Logs (filtres: event_type, user_id, ip, dates, limit) |
| GET     | `/admin/ip-blocklist`            | Liste des IP bloquées                                 |
| POST    | `/admin/ip-blocklist`            | Bloquer une IP (permanent ou temporaire)              |
| DELETE  | `/admin/ip-blocklist/{id}`       | Débloquer                                             |
| GET     | `/admin/email-domain-rules`      | Règles domaines email                                 |
| POST    | `/admin/email-domain-rules`      | Ajouter une règle                                     |
| DELETE  | `/admin/email-domain-rules/{id}` | Supprimer une règle                                   |

### POST `/admin/ip-blocklist` — corps

```json
{
  "ip_address": "192.168.1.1",
  "reason": "Tentatives de brute force",
  "blocked_until": "2026-06-01T00:00:00Z"
}
```

`reason` et `blocked_until` sont optionnels. Sans `blocked_until`, le blocage est permanent.

### POST `/admin/email-domain-rules` — corps

```json
{ "domain": "example.com", "allowed": false }
```

`allowed` vaut `true` par défaut (whitelist). Passer `false` pour blacklister un domaine.

**Types d'événements security_log :**
`LOGIN_SUCCESS` | `LOGIN_FAIL` | `TOKEN_REVOKED` | `ROLE_CHANGE` |
`USER_DEACTIVATED` | `PERMISSION_CHANGED` | `USER_MIGRATED_V3`

---

## Configuration mail

| Méthode | Endpoint                    | Description                                |
| ------- | --------------------------- | ------------------------------------------ |
| GET     | `/admin/settings/mail`      | Config sans SMTP_PASSWORD                  |
| POST    | `/admin/settings/mail/test` | Email de test à l'adresse du user connecté |
