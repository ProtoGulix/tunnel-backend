# Auth — JWT natif Tunnel v3

Authentification souveraine Tunnel. Plus de dépendance à Directus.
Tokens JWT HS256, refresh token rotatif stocké hashé en BDD.

---

## `POST /auth/login`

**Auth** : Public  
**Rate limit** : 10/minute (slowapi)

Délai aléatoire 50-200 ms appliqué avant toute réponse (anti timing-attack).

### Entrée

```json
{
  "email": "user@example.com",
  "password": "secret"
}
```

### Réponse `200`

```json
{
  "access_token": "eyJ...",
  "refresh_token": "a3f9...",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "Jean",
    "last_name": "Dupont",
    "initial": "JD",
    "role": "TECH"
  }
}
```

### Erreurs

| Code  | Cas                                    |
|-------|----------------------------------------|
| `401` | Email ou mot de passe incorrect        |
| `429` | Flood email (≥5 échecs / 15 min) ou flood IP (≥20 / h) ou IP bloquée |

---

## `POST /auth/refresh`

**Auth** : Public

Rotation du refresh token. L'ancien token est révoqué, un nouveau est émis.

Détection de vol : si un token déjà révoqué est présenté, **tous** les tokens
de l'utilisateur sont révoqués immédiatement.

### Entrée

```json
{ "refresh_token": "a3f9..." }
```

### Réponse `200`

```json
{
  "access_token": "eyJ...",
  "refresh_token": "b7e2...",
  "expires_in": 900
}
```

---

## `POST /auth/logout`

**Auth** : Bearer token requis

Révoque le refresh token présenté.

### Entrée

```json
{ "refresh_token": "b7e2..." }
```

### Réponse `200`

```json
{ "message": "Déconnecté" }
```

---

## `GET /auth/me`

**Auth** : Bearer token requis

Retourne le profil complet de l'utilisateur connecté avec ses permissions.

### Réponse `200`

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "Jean",
  "last_name": "Dupont",
  "initial": "JD",
  "role": "TECH",
  "permissions": ["interventions:list", "interventions:create", "actions:create"]
}
```

---

## Mode développement

Quand `AUTH_DISABLED=true` dans `.env` :

- Les requêtes sans Authorization passent (user_id = null)
- Les JWT valides sont décodés et loggés
- Ne jamais utiliser en production (guard au démarrage)

## Durées de vie

| Token         | Durée          | Variable env                    |
|---------------|----------------|---------------------------------|
| Access token  | 15 min         | `ACCESS_TOKEN_EXPIRE_MINUTES`   |
| Refresh token | 8 h            | `REFRESH_TOKEN_EXPIRE_HOURS`    |
