#!/bin/bash

# Setup Virtual Environment Script
# Skapar och konfigurerar virtuell miljö för SIPp-tester

set -e

echo "🐍 Skapar virtuell miljö för SIPp-tester..."

# Kontrollera att Python 3 finns
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 hittades inte. Installera Python 3 först."
    exit 1
fi

# Skapa virtuell miljö
echo "📦 Skapar virtuell miljö..."
python3 -m venv venv

# Aktivera virtuell miljö
echo "🔧 Aktiverar virtuell miljö..."
source venv/bin/activate

# Uppdatera pip
echo "⬆️ Uppdaterar pip..."
pip install --upgrade pip

# Installera dependencies
echo "📚 Installerar Python-dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Virtuell miljö skapad framgångsrikt!"
echo ""
echo "För att aktivera miljön:"
echo "  source venv/bin/activate"
echo ""
echo "För att köra tester:"
echo "  python run_tests.py"
echo "  python -m pytest test_sipp_pytest.py -v"
echo ""
echo "För att deaktivera miljön:"
echo "  deactivate" 