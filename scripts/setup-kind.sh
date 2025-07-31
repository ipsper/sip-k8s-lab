#!/bin/bash

# Setup Kind cluster för SIPp K8s Lab
# Ersätter minikube med bättre nätverkshantering

set -e

echo "🚀 Setting up Kind cluster..."

# Kontrollera om kind är installerat
if ! command -v kind &> /dev/null; then
    echo "❌ Kind är inte installerat. Installera först:"
    echo "   brew install kind"
    exit 1
fi

# Stoppa minikube om det körs
if command -v minikube &> /dev/null; then
    echo "🛑 Stoppar minikube..."
    minikube stop 2>/dev/null || true
fi

# Skapa Kind cluster
echo "📦 Skapar Kind cluster..."
kind create cluster --name sipp-k8s-lab --config kind-config.yaml

# Vänta lite för att klustret ska starta
echo "⏳ Väntar på att klustret ska starta..."
sleep 10

# Kontrollera att klustret fungerar
echo "🔍 Kontrollerar kluster..."
kubectl cluster-info
kubectl get nodes

# Installera nödvändiga komponenter
echo "🔧 Installerar komponenter..."

# Installera ingress controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Vänta på ingress controller
echo "⏳ Väntar på ingress controller..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s

echo "✅ Kind cluster är redo!"
echo ""
echo "Kommandon:"
echo "  kubectl cluster-info"
echo "  kubectl get nodes"
echo "  kind delete cluster --name sipp-k8s-lab  # för att ta bort" 