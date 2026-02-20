# Auth

Authentification via proxy Directus. Configure un cookie de session pour l'API.

> Voir aussi : [Users](users.md) pour `/users/me`

---

## `POST /auth/login`

Authentification via Directus. Retourne la réponse Directus telle quelle + configure un cookie.

**Auth** : Public

### Entrée

```json
{
  "email": "user@example.com",
  "password": "secret",
  "mode": "session"
}
```

| Champ      | Type   | Requis | Description                                 |
| ---------- | ------ | ------ | ------------------------------------------- |
| `email`    | string | oui    | Email de l'utilisateur                      |
| `password` | string | oui    | Mot de passe                                |
| `mode`     | string | non    | Mode d'authentification (défaut: `session`) |

### Réponse `200`

```json
{
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "abc123...",
    "expires": 900000
  }
}
```

| Champ           | Type   | Description                                    |
| --------------- | ------ | ---------------------------------------------- |
| `access_token`  | string | JWT Bearer token (contenu identique au cookie) |
| `refresh_token` | string | Token de rafraîchissement                      |
| `expires`       | int    | Durée de validité en millisecondes             |

### Cookie de session

Un cookie `session_token` est automatiquement configuré :

| Propriété | Valeur                           |
| --------- | -------------------------------- |
| Nom       | `session_token`                  |
| Valeur    | JWT (identique à `access_token`) |
| HttpOnly  | `true`                           |
| SameSite  | `Lax`                            |
| Path      | `/`                              |
| Domain    | Domaine de l'API tunnel          |
| Max-Age   | 86400 secondes (24h)             |

### Utilisation du cookie

**Option 1 : Cookie automatique** (recommandé pour navigateur)

```bash
# Le cookie est envoyé automatiquement par le navigateur
GET /users/me
# Cookie: session_token=eyJhbGci...
```

**Option 2 : Header Authorization** (recommandé pour mobile/API)

```bash
GET /users/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Erreurs

| Code  | Cas                   | Message                      |
| ----- | --------------------- | ---------------------------- |
| `401` | Credentials invalides | Erreur Directus              |
| `502` | Directus indisponible | `Directus indisponible: ...` |

---

## Mode développement

Quand `AUTH_DISABLED=true` dans `.env` :

- Les requêtes **sans** Authorization passent (pour tests rapides)
- Les JWT valides sont quand même décodés et loggés
- `/users/me` requiert toujours un JWT valide (retourne 401 sinon)

**⚠️ Ne jamais utiliser en production**
