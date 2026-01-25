#!/usr/bin/env python
"""Génère un JWT de test et teste l'API"""
import jwt
from datetime import datetime, timedelta
import json

print("=" * 60)
print("GÉNÉRATION JWT DE TEST")
print("=" * 60)

# Générer un token JWT
payload = {
    "sub": "user-123",  # user_id
    "role": "admin",
    "iat": datetime.utcnow(),
    "exp": datetime.utcnow() + timedelta(hours=24)
}

# Note: Pas de signature (comme dans notre implémentation)
token = jwt.encode(payload, "secret", algorithm="HS256")

print(f"\n✓ Token généré: {token}")
print(f"\n✓ Payload:")
print(json.dumps(payload, indent=2, default=str))

print("\n" + "=" * 60)
print("COMMANDES DE TEST")
print("=" * 60)

print(f"""
# Test /health (route publique, pas d'auth)
curl http://127.0.0.1:8000/health

# Test /interventions/1 (protégée, avec JWT)
curl -H "Authorization: Bearer {token}" http://127.0.0.1:8000/interventions/1

# Test /docs (Swagger interactive)
# http://127.0.0.1:8000/docs
""")

print("=" * 60)
print(f"\nToken à utiliser: {token}")
print("=" * 60)
