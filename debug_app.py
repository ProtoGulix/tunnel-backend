#!/usr/bin/env python
"""Script de debug pour tester l'importation de l'app et comportement au startup"""
import sys
import traceback

print('1. Début du script debug')

try:
    from api.app import app
    print('2. App importée avec succès')
    print(f'3. Type app: {type(app)}')

    # Routes
    routes = [r.path for r in app.routes if hasattr(r, 'path')]
    print(f'4. App routes: {routes}')

    # Test avec TestClient
    from fastapi.testclient import TestClient
    print('5. Création TestClient...')
    client = TestClient(app)
    print('6. TestClient créé')

    # Test /health
    print('7. Test GET /health...')
    response = client.get("/health")
    print(f'8. Status: {response.status_code}, Body: {response.json()}')

except Exception as e:
    print(f'ERREUR: {type(e).__name__}: {e}')
    traceback.print_exc()
