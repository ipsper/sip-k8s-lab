#!/bin/bash

# Build and Test Script för SIPp Tester
# Bygger containern och kör tester mot Kamailio

set -e

echo "🔨 Bygger SIPp test-container..."

# Kontrollera att vi är i rätt katalog
if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile hittades inte. Kör detta script från sipp-tester-mappen."
    exit 1
fi

# Anslut till minikube's Docker daemon
echo "🔗 Ansluter till minikube's Docker daemon..."
eval $(minikube docker-env)

# Bygg containern
echo "🏗️ Bygger SIPp test-container..."
docker build -t local/sipp-tester:latest .

echo "✅ SIPp test-container byggd!"

# Fråga användaren om de vill köra tester
echo ""
echo "Välj test-alternativ:"
echo "1) Testa mot lokal Kamailio (port-forward)"
echo "2) Testa mot extern server"
echo "3) Hoppa över tester"
echo ""
read -p "Välj alternativ (1-3): " -n 1 -r
echo ""

case $REPLY in
    1)
        echo "🧪 Kör tester mot lokal Kamailio..."
        ./scripts/run-local-tests.sh
        ;;
    2)
        echo "🧪 Kör tester mot extern server..."
        echo "Ange KAMAILIO_HOST och KAMAILIO_PORT:"
        read -p "Host (t.ex. 192.168.1.100): " host
        read -p "Port (t.ex. 5060): " port
        KAMAILIO_HOST=$host KAMAILIO_PORT=$port ./scripts/test-remote.sh
        ;;
    3)
        echo "ℹ️  Tester hoppades över. Kör manuellt med:"
        echo "   ./scripts/run-local-tests.sh"
        echo "   KAMAILIO_HOST=server KAMAILIO_PORT=5060 ./scripts/test-remote.sh"
        ;;
    *)
        echo "❌ Ogiltigt val"
        exit 1
        ;;
esac 