#!/bin/bash

# SIPp Test Runner för Kamailio
# Detta script kör olika SIPp-tester mot Kamailio-servern

set -e

# Konfiguration
KAMAILIO_HOST=${KAMAILIO_HOST:-"localhost"}
KAMAILIO_PORT=${KAMAILIO_PORT:-"5060"}
TEST_TIMEOUT=${TEST_TIMEOUT:-"30"}

echo "🚀 Startar SIPp-tester mot Kamailio..."
echo "📍 Target: $KAMAILIO_HOST:$KAMAILIO_PORT"
echo "⏱️  Timeout: ${TEST_TIMEOUT}s"
echo ""

# Funktion för att vänta på att Kamailio ska vara redo
wait_for_kamailio() {
    echo "⏳ Väntar på att Kamailio ska vara redo..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z $KAMAILIO_HOST $KAMAILIO_PORT 2>/dev/null; then
            echo "✅ Kamailio är redo!"
            return 0
        fi
        
        echo "   Försök $attempt/$max_attempts..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ Kamailio är inte tillgänglig efter $max_attempts försök"
    return 1
}

# Funktion för att köra ett test
run_test() {
    local test_name=$1
    local scenario_file=$2
    local extra_args=$3
    
    echo ""
    echo "🧪 Kör test: $test_name"
    echo "📄 Scenario: $scenario_file"
    
    # Kör SIPp-testet
    sipp -sn $scenario_file \
         -p 5061 \
         -m 1 \
         -timeout $TEST_TIMEOUT \
         -trace_msg \
         -trace_err \
         $extra_args \
         $KAMAILIO_HOST:$KAMAILIO_PORT
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo "✅ Test '$test_name' PASSED"
    else
        echo "❌ Test '$test_name' FAILED (exit code: $exit_code)"
    fi
    
    return $exit_code
}

# Huvudlogik
main() {
    # Vänta på att Kamailio ska vara redo
    if ! wait_for_kamailio; then
        exit 1
    fi
    
    # Kör grundläggande tester
    echo ""
    echo "📋 Kör grundläggande tester..."
    
    # Test 1: Enkel OPTIONS-request
    run_test "OPTIONS Request" "options" "-sf /app/sipp-scenarios/options.xml"
    
    # Test 2: REGISTER-request
    run_test "REGISTER Request" "register" "-sf /app/sipp-scenarios/register.xml"
    
    # Test 3: INVITE-request (utan dialog)
    run_test "INVITE Request" "invite" "-sf /app/sipp-scenarios/invite.xml"
    
    # Test 4: Ping-test
    run_test "Ping Test" "ping" "-sf /app/sipp-scenarios/ping.xml"
    
    echo ""
    echo "🎉 Alla tester slutförda!"
    echo ""
    echo "📊 Testresultat:"
    echo "   - OPTIONS: $(if [ $? -eq 0 ]; then echo "PASSED"; else echo "FAILED"; fi)"
    echo "   - REGISTER: $(if [ $? -eq 0 ]; then echo "PASSED"; else echo "FAILED"; fi)"
    echo "   - INVITE: $(if [ $? -eq 0 ]; then echo "PASSED"; else echo "FAILED"; fi)"
    echo "   - PING: $(if [ $? -eq 0 ]; then echo "PASSED"; else echo "FAILED"; fi)"
}

# Kör huvudfunktionen
main "$@" 