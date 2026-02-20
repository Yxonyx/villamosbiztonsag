#!/bin/bash
# VBF Jegyzőkönyv Kezelő - Indító script

echo "=== VBF Jegyzőkönyv Kezelő ==="
echo "Alkalmazás indítása..."

# Ellenőrizzük, hogy a docker compose elérhető-e
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    docker compose up -d --build
    echo ""
    echo "✅ Az alkalmazás elindult!"
    echo "🌐 Elérhető: http://localhost:8000"
else
    echo "❌ A Docker vagy Docker Compose nem található."
    echo "Telepítse a Docker-t: https://docs.docker.com/engine/install/"
    exit 1
fi
