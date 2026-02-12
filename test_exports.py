"""Script de test pour les endpoints d'export"""

import sys
print("=== Test de l'intégration des exports ===\n")

# Test 1: Import des modules
print("1. Test des imports...")
try:
    from api.exports.routes import router
    from api.exports.qr_generator import QRGenerator
    from api.exports.pdf_generator import PDFGenerator
    from api.exports.repo import ExportRepository
    print("   OK Tous les modules s'importent correctement")
except Exception as e:
    print(f"   ERREUR Erreur d'import: {e}")
    sys.exit(1)

# Test 2: Configuration
print("\n2. Test de la configuration...")
try:
    from api.settings import settings
    print(f"   OK API Version: {settings.API_VERSION}")
    print(f"   OK Template dir: {settings.EXPORT_TEMPLATE_DIR}")
    print(f"   OK Template file: {settings.EXPORT_TEMPLATE_FILE}")
    print(f"   OK QR base URL: {settings.EXPORT_QR_BASE_URL}")
except Exception as e:
    print(f"   ERREUR Erreur configuration: {e}")
    sys.exit(1)

# Test 3: Router
print("\n3. Test du router...")
try:
    print(f"   OK Prefix: {router.prefix}")
    print(f"   OK Nombre de routes: {len(router.routes)}")
    for route in router.routes:
        print(f"     - {route.methods} {route.path}")
except Exception as e:
    print(f"   ERREUR Erreur router: {e}")
    sys.exit(1)

# Test 4: QR Generator
print("\n4. Test du générateur QR...")
try:
    from io import BytesIO
    gen = QRGenerator()
    qr_img = gen.generate_qr_code('test-intervention-id')
    buffer = BytesIO()
    qr_img.save(buffer, format='PNG')
    print(f"   OK QR code généré: {len(buffer.getvalue())} bytes")
except Exception as e:
    print(f"   ERREUR Erreur QR: {e}")
    sys.exit(1)

# Test 5: PDF Generator
print("\n5. Test du générateur PDF...")
try:
    gen = PDFGenerator()
    test_data = {
        'code': 'TEST-001',
        'title': 'Test intervention',
        'priority': 'normale',
        'status_actual': 'ouvert',
        'reported_date': '2026-02-12',
        'reported_by': 'Test User',
        'type_inter': 'Curatif',
        'observations': 'Test',
        'equipements': {'code': 'EQP-001', 'name': 'Test Equipment'},
        'actions': [],
        'status_logs': [],
        'stats': {'action_count': 0, 'total_time': 0}
    }
    html = gen.render_html(test_data)
    pdf_bytes = gen.generate_pdf(html)
    print(f"   OK HTML rendu: {len(html)} chars")
    print(f"   OK PDF généré: {len(pdf_bytes)} bytes")
except Exception as e:
    print(f"   ERREUR Erreur PDF: {e}")
    sys.exit(1)

# Test 6: App registration
print("\n6. Test de l'enregistrement dans l'app...")
try:
    from api.app import app
    routes = [r for r in app.routes if '/exports' in str(r.path)]
    print(f"   OK Routes exports enregistrées: {len(routes)}")
    for route in routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            print(f"     - {route.methods} {route.path}")
except Exception as e:
    print(f"   ERREUR Erreur app: {e}")
    sys.exit(1)

print("\n=== OK Tous les tests réussis! ===")
print("\nL'intégration est complète. Vous pouvez maintenant:")
print("1. Démarrer l'API: uvicorn api.app:app --reload")
print("2. Tester PDF: GET /exports/interventions/{id}/pdf (avec JWT)")
print("3. Tester QR: GET /exports/interventions/{id}/qrcode (public)")
