#!/bin/bash

# Activate Virtual Environment Script
# Aktiverar virtuell miljö för SIPp-tester

echo "🔧 Aktiverar virtuell miljö..."

# Kontrollera att venv finns
if [ ! -d "venv" ]; then
    echo "❌ Virtuell miljö hittades inte. Kör setup_venv.sh först."
    exit 1
fi

# Aktivera virtuell miljö
source venv/bin/activate

echo "✅ Virtuell miljö aktiverad!"
echo ""
echo "Nu kan du köra:"
echo "  python run_tests.py"
echo "  python -m pytest test_sipp_pytest.py -v"
echo ""
echo "För att deaktivera: deactivate" 