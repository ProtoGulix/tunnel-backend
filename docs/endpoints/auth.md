# Auth

Proxy d'authentification vers Directus. Retourne un JWT et configure un cookie de session.

## `POST /auth/login`

**Auth** : Public

### Entrée

```json
{
  "email": "user@example.com",
  "password": "secret",
  "mode": "session"
}
```

| Champ | Type | Requis | Description |
|---|---|---|---|
| `email` | string | oui | Email de l'utilisateur |
| `password` | string | oui | Mot de passe |
| `mode` | string | oui | Toujours `"session"` |

### Réponse `200`

```json
{
  "data": {
    "access_token": "eyJhbG...",
    "refresh_token": "abc123...",
    "expires": 900000
  }
}
```

| Champ | Type | Description |
|---|---|---|
| `access_token` | string | JWT Bearer token |
| `refresh_token` | string | Token de rafraîchissement |
| `expires` | int | Durée de validité en millisecondes |
