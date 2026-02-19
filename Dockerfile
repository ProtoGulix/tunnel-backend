FROM python:3.12-slim

WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code de l'application
COPY . .

# Port API
EXPOSE 8000

# Démarrage
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
