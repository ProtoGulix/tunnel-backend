#!/usr/bin/env python
"""Script pour tester l'app avec logging verbeux du cycle de vie"""
import logging
import sys

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)

print('=' * 60)
print('DÉBUT DU TEST D\'APP')
print('=' * 60)

try:
    print('\n[1/5] Import de l\'app...')
    from api.app import app
    print('[2/5] ✓ App importée avec succès')

    # Ajouter des hooks pour voir le cycle de vie
    print('[3/5] Ajout des hooks de cycle de vie...')

    @app.on_event("startup")
    async def startup_event():
        print('[HOOK] Événement STARTUP détecté')

    @app.on_event("shutdown")
    async def shutdown_event():
        print('[HOOK] Événement SHUTDOWN détecté')

    print('[4/5] ✓ Hooks enregistrés')

    # Lancer uvicorn
    print('[5/5] Lancement d\'uvicorn...')
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="debug"
    )

except Exception as e:
    print(f'\n❌ ERREUR: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
