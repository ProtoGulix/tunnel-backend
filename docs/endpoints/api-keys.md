# Clés d'API

Endpoints de gestion des clés d'API machine-to-machine (serveur MCP, intégrations externes).

**Auth requise :** Bearer token JWT avec rôle `ADMIN`.

**Authentification par clé d'API :** header `X-API-Key: gmao_xxxxx` sur tous les endpoints de l'API.

---

## Endpoints

| Méthode | Endpoint           | Rôle  | Description                                   |
| ------- | ------------------ | ----- | --------------------------------------------- |
| GET     | `/api-keys`        | ADMIN | Liste toutes les clés (sans secret ni hash)   |
| POST    | `/api-keys`        | ADMIN | Crée une clé — secret retourné **une seule fois** |
| PATCH   | `/api-keys/{id}`   | ADMIN | Activer / désactiver / modifier expiration    |
| DELETE  | `/api-keys/{id}`   | ADMIN | Révoquer définitivement                       |

---

## POST `/api-keys` — corps

```json
{
  "name": "Serveur MCP production"
}
```

### Réponse 201

Le champ `secret` est retourné **une seule fois** et n'est jamais stocké. À conserver immédiatement.

```json
{
  "id": "uuid",
  "name": "Serveur MCP production",
  "key_prefix": "gmao_a1b2c",
  "secret": "gmao_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "role_code": "MCP",
  "created_at": "2026-05-03T12:00:00Z"
}
```

---

## GET `/api-keys` — réponse

```json
[
  {
    "id": "uuid",
    "name": "Serveur MCP production",
    "key_prefix": "gmao_a1b2c",
    "role_code": "MCP",
    "is_active": true,
    "expires_at": null,
    "last_used_at": "2026-05-03T12:30:00Z",
    "created_at": "2026-05-03T12:00:00Z"
  }
]
```

---

## PATCH `/api-keys/{id}` — corps

Tous les champs sont optionnels.

```json
{
  "is_active": false,
  "expires_at": "2027-01-01T00:00:00Z"
}
```

---

## Utilisation (côté MCP)

Toutes les requêtes doivent inclure le header :

```
X-API-Key: gmao_xxxxx...
```

Le rôle `MCP` donne accès en lecture seule (`GET`) à tous les endpoints non-sensibles. Les endpoints `/admin/*` et les opérations d'écriture sont refusés (403).

---

## Sécurité

- Le secret n'est **jamais stocké** en clair — seul le SHA-256 est en base.
- `last_used_at` est mis à jour de façon asynchrone à chaque appel.
- Une clé expirée (`expires_at` dépassé) est rejetée avec 401.
- Une clé inactive (`is_active: false`) est rejetée avec 401.
- Délai aléatoire anti-timing sur les 401 (identique au comportement JWT).
