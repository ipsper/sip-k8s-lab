#!/bin/bash

# Run Local Tests Script
# Kör SIPp-tester från lokal container mot Kamailio i Kubernetes

set -e

echo "🧪 Kör SIPp-tester från lokal container..."

# Konfiguration
KAMAILIO_HOST=${KAMAILIO_HOST:-"localhost"}
KAMAILIO_PORT=${KAMAILIO_PORT:-"5060"}

# Kontrollera att Kamailio är tillgänglig via port-forward
echo "🔍 Kontrollerar Kamailio-tillgänglighet..."

# Starta port-forward i bakgrunden
echo "🔗 Startar port-forward till Kamailio..."
kubectl port-forward svc/kamailio-service 5060:5060 -n kamailio &
PF_PID=$!

# Vänta lite för att port-forward ska starta
sleep 3

# Kontrollera att port-forward fungerar
if ! nc -z localhost 5060 2>/dev/null; then
    echo "❌ Kan inte ansluta till Kamailio via port-forward"
    kill $PF_PID 2>/dev/null || true
    exit 1
fi

echo "✅ Port-forward är aktivt"

# Kör tester
echo ""
echo "🚀 Kör SIPp-tester..."

# Kör health check först
docker run --rm \
    --network host \
    local/sipp-tester:latest \
    /app/test-scripts/health-check.sh

echo ""
echo "📋 Kör SIPp-scenarios..."

# Kör huvudtester
docker run --rm \
    --network host \
    local/sipp-tester:latest \
    /app/test-scripts/run-tests.sh

# Stoppa port-forward
echo ""
echo "🛑 Stoppar port-forward..."
kill $PF_PID 2>/dev/null || true

echo "�� Tester slutförda!" 