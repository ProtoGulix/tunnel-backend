#!/usr/bin/env python
"""Diagnostic du crash lors du startup"""
import traceback

print("=" * 60)
print("DIAGNOSTIC DE CRASH")
print("=" * 60)

try:
    print("\n[1] Import fastapi...")
    from fastapi import FastAPI
    print("✓ FastAPI importé")

    print("[2] Import settings...")
    from api.settings import settings
    print("✓ Settings importé")

    print("[3] Import middleware JWT...")
    from api.auth.middleware import JWTMiddleware
    print("✓ Middleware importé")

    print("[4] Import repo...")
    from api.interventions.repo import InterventionRepository
    print("✓ Repo importé")

    print("[5] Création d'une instance de repo...")
    repo = InterventionRepository()
    print("✓ Repo instancié")

    print("[6] Test connexion base de données...")
    # Essayer une connexion
    conn = repo._get_connection()
    print("✓ Connexion établie")
    conn.close()

    print("[7] Import router...")
    from api.interventions.routes import router as intervention_router
    print("✓ Router importé")

    print("[8] Import handlers d'erreurs...")
    from api.errors.handlers import register_error_handlers
    print("✓ Handlers d'erreurs importés")

    print("[9] Création de l'app...")
    app = FastAPI(
        title="Test",
        version="0.1.0"
    )
    print("✓ App créée")

    print("[10] Enregistrement des handlers...")
    register_error_handlers(app)
    print("✓ Handlers enregistrés")

    print("[11] Inclusion du router...")
    app.include_router(intervention_router)
    print("✓ Router inclus")

    print("[12] Ajout route /health...")

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}
    print("✓ Route /health ajoutée")

    print("[13] Ajout du middleware JWT...")
    app.add_middleware(JWTMiddleware)
    print("✓ Middleware JWT ajouté")

    print("\n✅ TOUS LES IMPORTS RÉUSSIS - L'APP DEVRAIT FONCTIONNER")

except Exception as e:
    print(f"\n❌ ERREUR: {type(e).__name__}: {e}")
    traceback.print_exc()
