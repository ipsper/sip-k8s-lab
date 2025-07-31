# Kind Installation och Användning

Kind (Kubernetes in Docker) är ett verktyg för att köra lokala Kubernetes-kluster med Docker. Det är ett alternativ till minikube med bättre nätverkshantering.

## Varför Kind?

### Problem med Minikube
- Port-forward misslyckas: `Connection refused`
- Extra nätverkslager (VM) som orsakar problem
- Instabil anslutning till pods

### Fördelar med Kind
- **Direkt Docker-nätverk** - Ingen VM-lager
- **Stabilare port-forward** - Samma nätverksnamnrymd
- **Bättre debugging** - Enklare att felsöka nätverksproblem
- **Snabbare** - Ingen VM-overhead

## Installation

### 1. Installera Kind

```bash
# macOS (med Homebrew)
brew install kind

# Verifiera installation
kind version
```

### 2. Installera kubectl (om inte redan installerat)

```bash
# macOS (med Homebrew)
brew install kubectl

# Verifiera installation
kubectl version --client
```

## Användning

### 1. Skapa Kind-kluster

```bash
# Använd vårt setup-script
./scripts/setup-kind.sh

# Eller manuellt
kind create cluster --name sipp-k8s-lab --config kind-config.yaml
```

### 2. Kontrollera klustret

```bash
# Visa klusterinfo
kubectl cluster-info

# Visa noder
kubectl get nodes

# Visa alla namespaces
kubectl get namespaces
```

### 3. Deploya Kamailio

```bash
# Skapa namespace
kubectl create namespace kamailio

# Deploya Kamailio
kubectl apply -f k8s/

# Kontrollera deployment
kubectl get pods -n kamailio
```

### 4. Testa SIPp

```bash
# Gå till sipp-tester katalogen
cd sipp-tester

# Aktivera virtual environment
source venv/bin/activate

# Kör tester
python -m pytest test_sipp_pytest.py::TestSippTester::test_options_scenario -v -s
```

## Konfiguration

### Kind-konfiguration (`kind-config.yaml`)

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 5060
    hostPort: 5060
    protocol: UDP
  - containerPort: 5060
    hostPort: 5060
    protocol: TCP
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
- role: worker
- role: worker
```

### Viktiga portar
- **5060/UDP** - SIP-protokoll
- **5060/TCP** - SIP-protokoll (alternativ)
- **80/TCP** - HTTP (för ingress)
- **443/TCP** - HTTPS (för ingress)

## Hantering av Kluster

### Starta klustret
```bash
# Klustret startar automatiskt när det skapas
# Om det inte körs:
kind start cluster --name sipp-k8s-lab
```

### Stoppa klustret
```bash
kind stop cluster --name sipp-k8s-lab
```

### Ta bort klustret
```bash
kind delete cluster --name sipp-k8s-lab
```

### Lista kluster
```bash
kind get clusters
```

## Felsökning

### 1. Port-forward problem

**Problem:** `Connection refused` vid port-forward
```bash
# Kontrollera att klustret körs
kind get clusters

# Kontrollera pods
kubectl get pods -n kamailio

# Testa port-forward manuellt
kubectl port-forward svc/kamailio-service 5060:5060 -n kamailio
```

### 2. Nätverksproblem

**Problem:** Kan inte ansluta till pods
```bash
# Kontrollera nätverkskonfiguration
kubectl get nodes -o wide

# Kontrollera services
kubectl get svc -n kamailio

# Testa anslutning
nc -z localhost 5060
```

### 3. Docker-problem

**Problem:** Kind kan inte starta
```bash
# Kontrollera Docker
docker version
docker ps

# Starta Docker om det inte körs
open -a Docker
```

## Kommandon för Snabbstart

```bash
# 1. Installera Kind
brew install kind

# 2. Skapa kluster
./scripts/setup-kind.sh

# 3. Deploya Kamailio
kubectl apply -f k8s/

# 4. Testa SIPp
cd sipp-tester
source venv/bin/activate
python -m pytest test_sipp_pytest.py::TestSippTester::test_options_scenario -v -s
```

## Jämförelse: Kind vs Minikube

| Funktion | Kind | Minikube |
|----------|------|----------|
| Nätverkshantering | Docker direkt | VM-lager |
| Port-forward | Stabil | Instabil |
| Prestanda | Snabb | Långsammare |
| Resursanvändning | Låg | Hög |
| Debugging | Enkel | Komplex |

## Nästa Steg

Efter att Kind-klustret är uppsatt:

1. **Deploya Kamailio** - `kubectl apply -f k8s/`
2. **Testa SIPp** - Kör testerna i `sipp-tester/`
3. **Felsök** - Använd loggarna för debugging
4. **Optimera** - Justera konfiguration efter behov

## Support

Om du stöter på problem:

1. Kontrollera [felsökningar/](felsökningar/) för dokumenterade problem
2. Använd `kubectl logs` för att se pod-loggar
3. Kontrollera Kind-dokumentationen: https://kind.sigs.k8s.io/ 