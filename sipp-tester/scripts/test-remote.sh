#!/bin/bash

# Test Remote Kamailio Script
# Kör SIPp-tester mot extern Kamailio-server

set -e

# Kontrollera att host och port är angivna
if [ -z "$KAMAILIO_HOST" ] || [ -z "$KAMAILIO_PORT" ]; then
    echo "❌ Ange KAMAILIO_HOST och KAMAILIO_PORT"
    echo ""
    echo "Exempel:"
    echo "  KAMAILIO_HOST=192.168.1.100 KAMAILIO_PORT=5060 ./scripts/test-remote.sh"
    echo "  KAMAILIO_HOST=kamailio.example.com KAMAILIO_PORT=5060 ./scripts/test-remote.sh"
    exit 1
fi

echo "🧪 Kör SIPp-tester mot extern Kamailio-server..."
echo "📍 Target: $KAMAILIO_HOST:$KAMAILIO_PORT"
echo ""

# Kontrollera att containern är byggd
if ! docker images | grep -q "local/sipp-tester"; then
    echo "🔨 Bygger SIPp test-container..."
    docker build -t local/sipp-tester:latest .
fi

# Kör health check
echo "🏥 Kör health check..."
docker run --rm \
    local/sipp-tester:latest \
    /app/test-scripts/health-check.sh

echo ""
echo "📋 Kör SIPp-scenarios..."

# Kör huvudtester
docker run --rm \
    local/sipp-tester:latest \
    /app/test-scripts/run-tests.sh

echo "�� Tester slutförda!" 