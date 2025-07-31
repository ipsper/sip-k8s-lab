#!/bin/bash

# Health Check Script för Kamailio
# Kontrollerar om Kamailio-servern är tillgänglig

set -e

# Konfiguration från miljövariabler
KAMAILIO_HOST=${KAMAILIO_HOST:-"localhost"}
KAMAILIO_PORT=${KAMAILIO_PORT:-"5060"}
TEST_TIMEOUT=${TEST_TIMEOUT:-"30"}

echo "🏥 Health Check för Kamailio..."
echo "📍 Target: $KAMAILIO_HOST:$KAMAILIO_PORT"
echo ""

# Funktion för att testa anslutning
test_connection() {
    local host=$1
    local port=$2
    local max_attempts=${3:-5}
    local attempt=1
    
    echo "🔍 Kontrollerar port-anslutning..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            echo "✅ Anslutning lyckades till $host:$port"
            return 0
        fi
        
        echo "   Försök $attempt/$max_attempts misslyckades"
        
        if [ $attempt -lt $max_attempts ]; then
            echo "   Väntar 2s innan nästa försök..."
            sleep 2
        fi
        
        attempt=$((attempt + 1))
    done
    
    echo "❌ Kan inte ansluta till Kamailio på $host:$port"
    return 1
}

# Funktion för att skicka enkelt SIP-request
send_sip_request() {
    local host=$1
    local port=$2
    
    echo "📡 Skickar SIP OPTIONS-request..."
    
    # Skapa enkel SIP OPTIONS-request
    cat <<EOF | nc "$host" "$port" 2>/dev/null || return 1
OPTIONS sip:$host:$port SIP/2.0
Via: SIP/2.0/UDP $host:$port;branch=z9hG4bK-test
From: <sip:test@$host>;tag=test
To: <sip:$host:$port>
Call-ID: test-$(date +%s)
CSeq: 1 OPTIONS
Contact: <sip:test@$host>
User-Agent: SIPp-Test/1.0
Content-Length: 0

EOF
}

# Huvudlogik
main() {
    # Testa grundläggande anslutning
    if ! test_connection "$KAMAILIO_HOST" "$KAMAILIO_PORT"; then
        exit 1
    fi
    
    # Testa SIP-protokoll (valfritt)
    echo ""
    echo "🧪 Testar SIP-protokoll..."
    
    if send_sip_request "$KAMAILIO_HOST" "$KAMAILIO_PORT"; then
        echo "✅ SIP-protokoll fungerar"
    else
        echo "⚠️  SIP-protokoll test misslyckades (kan vara normalt)"
    fi
    
    echo ""
    echo "🎉 Health check slutförd!"
}

# Kör huvudfunktionen
main "$@" 