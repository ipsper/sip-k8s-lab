#!/bin/bash

# Run Tests with Virtual Environment Script
# Aktiverar venv och kör SIPp-tester

set -e

echo "🧪 Kör SIPp-tester med virtuell miljö..."

# Kontrollera att venv finns
if [ ! -d "venv" ]; then
    echo "❌ Virtuell miljö hittades inte. Kör setup_venv.sh först."
    exit 1
fi

# Aktivera virtuell miljö
echo "🔧 Aktiverar virtuell miljö..."
source venv/bin/activate

# Kör test-script
echo "🚀 Kör tester..."
python run_tests.py

# Deaktivera virtuell miljö
deactivate

echo "✅ Tester slutförda!" 