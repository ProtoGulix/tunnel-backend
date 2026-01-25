#!/bin/bash
# Script de démarrage de l'API en développement (Linux/Mac)

echo ""
echo "🚀 Démarrage API GMAO..."
echo ""

# Vérifier Python 3.12
if ! command -v python3.12 &> /dev/null; then
    echo "❌ Python 3.12 n'est pas installé"
    exit 1
fi

# Créer venv si absent
if [ ! -d ".venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python3.12 -m venv .venv
fi

# Activer venv
source .venv/bin/activate

# Installer dépendances
echo "📥 Installation des dépendances..."
pip install -r requirements.txt --quiet

# Démarrer l'API
echo ""
echo "✅ API en cours de démarrage sur http://localhost:8000"
echo "📖 Docs Swagger: http://localhost:8000/docs"
echo ""

python -m uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
