# Admin

Tous les endpoints sous `/admin/` nécessitent un Bearer token valide.

**Rôles autorisés :**
- `RESP + ADMIN` : gestion utilisateurs, référentiel
- `ADMIN` seul : rôles/permissions, sécurité, endpoints catalogue

---

## Utilisateurs

| Méthode | Endpoint                          | Rôles       | Description                         |
|---------|-----------------------------------|-------------|-------------------------------------|
| GET     | `/admin/users`                    | RESP, ADMIN | Liste (filtres: search, is_active, role_code) |
| POST    | `/admin/users`                    | RESP, ADMIN | Créer un utilisateur                |
| GET     | `/admin/users/{id}`               | RESP, ADMIN | Détail                              |
| PUT     | `/admin/users/{id}`               | RESP, ADMIN | Modifier email/nom/initial          |
| PATCH   | `/admin/users/{id}/role`          | RESP, ADMIN | Changer le rôle (révoque les tokens)|
| PATCH   | `/admin/users/{id}/active`        | RESP, ADMIN | Activer/désactiver                  |
| POST    | `/admin/users/{id}/reset-password`| RESP, ADMIN | Génère un mot de passe temporaire   |
| DELETE  | `/admin/users/{id}`               | RESP, ADMIN | Soft delete (obfusque email + hash) |

---

## Rôles et permissions

| Méthode | Endpoint                          | Rôles | Description                    |
|---------|-----------------------------------|-------|--------------------------------|
| GET     | `/admin/roles`                    | ADMIN | Liste des 4 rôles              |
| GET     | `/admin/roles/{id}/permissions`   | ADMIN | Matrice complète du rôle       |
| PATCH   | `/admin/permissions/{id}`         | ADMIN | Modifier `allowed` + log audit |
| GET     | `/admin/audit/permissions`        | ADMIN | Historique (filtres: role_id, dates) |

---

## Catalogue des endpoints

| Méthode | Endpoint                  | Rôles | Description                          |
|---------|---------------------------|-------|--------------------------------------|
| GET     | `/admin/endpoints`        | ADMIN | Liste (filtres: module, method)      |
| GET     | `/admin/endpoints/modules`| ADMIN | Modules distincts                    |
| PATCH   | `/admin/endpoints/{id}`   | ADMIN | Modifier description/module/sensitive|
| POST    | `/admin/endpoints/sync`   | ADMIN | Rescan routes FastAPI + UPSERT       |

---

## Référentiel actions

| Méthode | Endpoint                                    | Rôles       |
|---------|---------------------------------------------|-------------|
| GET     | `/admin/action-categories`                  | RESP, ADMIN |
| PATCH   | `/admin/action-categories/{id}`             | RESP, ADMIN |
| PATCH   | `/admin/action-categories/{id}/active`      | RESP, ADMIN |
| GET     | `/admin/action-subcategories`               | RESP, ADMIN |
| POST    | `/admin/action-subcategories`               | RESP, ADMIN |
| PATCH   | `/admin/action-subcategories/{id}`          | RESP, ADMIN |
| PATCH   | `/admin/action-subcategories/{id}/active`   | RESP, ADMIN |
| GET     | `/admin/complexity-factors`                 | RESP, ADMIN |
| PATCH   | `/admin/complexity-factors/{id}`            | RESP, ADMIN |
| PATCH   | `/admin/complexity-factors/{id}/active`     | RESP, ADMIN |

---

## Référentiel interventions

| Méthode | Endpoint                                  | Rôles       |
|---------|-------------------------------------------|-------------|
| GET     | `/admin/intervention-types`               | RESP, ADMIN |
| POST    | `/admin/intervention-types`               | RESP, ADMIN |
| PATCH   | `/admin/intervention-types/{id}`          | RESP, ADMIN |
| PATCH   | `/admin/intervention-types/{id}/active`   | RESP, ADMIN |
| GET     | `/admin/intervention-statuses`            | RESP, ADMIN |
| PATCH   | `/admin/intervention-statuses/{id}`       | RESP, ADMIN |

---

## Sécurité

| Méthode | Endpoint                          | Description                            |
|---------|-----------------------------------|----------------------------------------|
| GET     | `/admin/security-logs`            | Logs (filtres: event_type, user_id, ip, dates, limit) |
| GET     | `/admin/ip-blocklist`             | Liste des IP bloquées                  |
| POST    | `/admin/ip-blocklist`             | Bloquer une IP (permanent ou temporaire)|
| DELETE  | `/admin/ip-blocklist/{id}`        | Débloquer                              |
| GET     | `/admin/email-domain-rules`       | Règles domaines email                  |
| POST    | `/admin/email-domain-rules`       | Ajouter une règle                      |
| DELETE  | `/admin/email-domain-rules/{id}`  | Supprimer une règle                    |

**Types d'événements security_log :**
`LOGIN_SUCCESS` | `LOGIN_FAIL` | `TOKEN_REVOKED` | `ROLE_CHANGE` |
`USER_DEACTIVATED` | `PERMISSION_CHANGED` | `USER_MIGRATED_V3`

---

## Configuration mail

| Méthode | Endpoint                    | Description                              |
|---------|-----------------------------|------------------------------------------|
| GET     | `/admin/settings/mail`      | Config sans SMTP_PASSWORD                |
| POST    | `/admin/settings/mail/test` | Email de test à l'adresse du user connecté |
