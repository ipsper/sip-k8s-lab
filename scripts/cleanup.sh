#!/bin/bash

# Kamailio Kubernetes Cleanup Script
echo "🧹 Rensar Kamailio SIP Server från Kubernetes..."

# Kontrollera att kubectl finns
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl hittades inte."
    exit 1
fi

# Ta bort alla resurser
echo "🗑️ Tar bort alla resurser..."
kubectl delete -k k8s/

# Vänta på att allt ska tas bort
echo "⏳ Väntar på att resurser ska tas bort..."
kubectl wait --for=delete namespace/kamailio --timeout=300s 2>/dev/null || true

echo "✅ Alla Kamailio-resurser har tagits bort!" 