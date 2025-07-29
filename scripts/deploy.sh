#!/bin/bash

# Kamailio Kubernetes Deployment Script
echo "🚀 Deployar Kamailio SIP Server i Kubernetes..."

# Kontrollera att kubectl finns
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl hittades inte. Installera kubectl först."
    exit 1
fi

# Kontrollera att Kubernetes-klustret är tillgängligt
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Kan inte ansluta till Kubernetes-klustret."
    exit 1
fi

echo "✅ Kubernetes-kluster är tillgängligt"

# Skapa namespace och resurser
echo "📦 Skapar namespace och resurser..."
kubectl apply -k k8s/

# Vänta på att pods ska starta
echo "⏳ Väntar på att pods ska starta..."
kubectl wait --for=condition=ready pod -l app=mysql -n kamailio --timeout=300s

# Vänta lite extra för Kamailio eftersom den kan ta tid att starta
echo "⏳ Väntar på att Kamailio ska starta..."
sleep 10
kubectl wait --for=condition=ready pod -l app=kamailio -n kamailio --timeout=300s || echo "⚠️ Kamailio pods tar tid att starta, kontrollera status manuellt"

# Visa status
echo "📊 Status för deployment:"
kubectl get pods -n kamailio
echo ""
echo "🌐 Services:"
kubectl get svc -n kamailio

echo ""
echo "✅ Kamailio SIP Server har deployats framgångsrikt!"
echo ""
echo "För att testa anslutningen:"
echo "kubectl port-forward svc/kamailio-service 5060:5060 -n kamailio"
echo ""
echo "För att se loggar:"
echo "kubectl logs deployment/kamailio -n kamailio -f" 