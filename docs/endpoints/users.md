# Users

Proxy lecture seule vers la table `directus_users`. Expose les informations publiques des utilisateurs (techniciens, responsables) sans les champs sensibles (password, token, tfa_secret, auth_data).

---

## `GET /users`

Liste les utilisateurs avec filtres optionnels.

### Query params

| Param    | Type   | Défaut | Description                                      |
| -------- | ------ | ------ | ------------------------------------------------ |
| `skip`   | int    | 0      | Offset de pagination                             |
| `limit`  | int    | 100    | Nombre max (max: 1000)                           |
| `status` | string | —      | Filtrer par statut (`active`, `suspended`, etc.) |
| `search` | string | —      | Recherche sur nom, prénom, email (ILIKE)         |

### Réponse `200` — UserListItem

```json
[
  {
    "id": "a1b2c3d4-...",
    "first_name": "Jean",
    "last_name": "Dupont",
    "email": "jean.dupont@example.com",
    "initial": "JD",
    "status": "active",
    "role": "uuid"
  }
]
```

Trié par nom ASC, prénom ASC.

---

## `GET /users/me`

Retourne l'utilisateur courant, identifié par le JWT.

### Réponse `200` — UserOut

```json
{
  "id": "a1b2c3d4-...",
  "first_name": "Jean",
  "last_name": "Dupont",
  "email": "jean.dupont@example.com",
  "location": "Atelier principal",
  "title": "Technicien maintenance",
  "description": null,
  "tags": ["maintenance", "scie"],
  "avatar": "uuid|null",
  "status": "active",
  "role": "uuid",
  "initial": "JD",
  "last_access": "2026-02-15T14:30:00+00:00"
}
```

---

## `GET /users/{id}`

Détail d'un utilisateur par UUID.

### Réponse `200` — UserOut

Même structure que `/users/me`.

### Erreurs

| Code | Description            |
| ---- | ---------------------- |
| 404  | Utilisateur non trouvé |

---

## Schémas

### UserListItem

Schema léger pour listes d'utilisateurs (exports, listes techniciens, etc.).

```json
{
  "id": "uuid",
  "first_name": "string|null",
  "last_name": "string|null",
  "email": "string|null",
  "initial": "string|null",
  "status": "string",
  "role": "uuid|null"
}
```

**Utilisé dans :**

- `GET /users` (liste)
- `InterventionActionOut.tech` ([intervention-actions.md](intervention-actions.md))

### UserOut

Schema complet avec tous les champs publics.

```json
{
  "id": "uuid",
  "first_name": "string|null",
  "last_name": "string|null",
  "email": "string|null",
  "location": "string|null",
  "title": "string|null",
  "description": "string|null",
  "tags": "array|null",
  "avatar": "uuid|null",
  "status": "string",
  "role": "uuid|null",
  "initial": "string|null",
  "last_access": "datetime|null"
}
```

**Utilisé dans :**

- `GET /users/me`
- `GET /users/{id}`
