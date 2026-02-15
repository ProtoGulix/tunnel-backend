# Health

Vérification de l'état de l'API, de la base de données et du service d'authentification.

## `GET /health`

**Auth** : Public

### Réponse `200`

```json
{
  "status": "ok",
  "database": "connected",
  "auth_service": "reachable"
}
```
