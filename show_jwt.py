#!/usr/bin/env python
"""Génère un JWT et affiche les commandes de test"""
import jwt
from datetime import datetime, timedelta

payload = {
    "sub": "user-123",
    "role": "admin",
    "iat": datetime.utcnow(),
    "exp": datetime.utcnow() + timedelta(hours=24)
}

token = jwt.encode(payload, "secret", algorithm="HS256")

print("\n" + "=" * 70)
print(" JWT TOKEN GÉNÉRÉ")
print("=" * 70)
print(f"\nToken: {token}\n")

print("=" * 70)
print(" COMMANDES DE TEST")
print("=" * 70)

print("\n# 1. Test /health (public, pas d'auth)")
print('curl http://127.0.0.1:8000/health')

print("\n# 2. Test /interventions/1 sans JWT (doit échouer)")
print('curl http://127.0.0.1:8000/interventions/1')

print("\n# 3. Test /interventions/1 avec JWT")
print(
    f'curl -H "Authorization: Bearer {token}" http://127.0.0.1:8000/interventions/1')

print("\n# 4. Documentation interactive")
print('# http://127.0.0.1:8000/docs')

print("\n" + "=" * 70 + "\n")
