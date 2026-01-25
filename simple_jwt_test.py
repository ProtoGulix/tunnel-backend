#!/usr/bin/env python3
"""Test simple des endpoints JWT sans dépendre de requests library"""
import json
import sys
import urllib.request
import urllib.error
import jwt
from datetime import datetime, timedelta

# Génère le token
payload = {"sub": "user-123", "role": "admin"}
token = jwt.encode(payload, "secret", algorithm="HS256")

print("\n" + "=" * 70)
print(" TEST JWT - API GMAO")
print("=" * 70)
print(f"\nToken généré: {token[:40]}...\n")

base_url = "http://127.0.0.1:8000"

# Test 1: /health
print("[Test 1] GET /health (publique)")
try:
    req = urllib.request.Request(f"{base_url}/health")
    with urllib.request.urlopen(req, timeout=5) as response:
        data = json.loads(response.read().decode())
        print(f"✓ 200 OK - Response: {data}")
except urllib.error.HTTPError as e:
    print(f"✗ {e.code} - {e.reason}")
except Exception as e:
    print(f"✗ Erreur: {e}")

# Test 2: /interventions/1 sans JWT
print("\n[Test 2] GET /interventions/1 (sans JWT - doit échouer)")
try:
    req = urllib.request.Request(f"{base_url}/interventions/1")
    with urllib.request.urlopen(req, timeout=5) as response:
        print(f"✗ Devrait avoir échoué mais a reussi")
except urllib.error.HTTPError as e:
    if e.code == 401:
        data = json.loads(e.read().decode())
        print(f"✓ 401 Unauthorized - {data['detail']}")
    else:
        print(f"✗ Code inattendu {e.code}")
except Exception as e:
    print(f"✗ Erreur: {e}")

# Test 3: /interventions/1 avec JWT
print("\n[Test 3] GET /interventions/1 (avec JWT valide)")
try:
    req = urllib.request.Request(
        f"{base_url}/interventions/1",
        headers={"Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        data = json.loads(response.read().decode())
        print(f"✓ 200 OK - {json.dumps(data, indent=2)[:100]}...")
except urllib.error.HTTPError as e:
    if e.code == 404:
        data = json.loads(e.read().decode())
        print(
            f"✓ 404 Not Found (normal si intervention n'existe pas) - {data['detail']}")
    else:
        data = json.loads(e.read().decode())
        print(f"✗ {e.code} - {data}")
except Exception as e:
    print(f"✗ Erreur: {e}")

print("\n" + "=" * 70)
print(" ✅ TESTS TERMINÉS")
print("=" * 70 + "\n")
