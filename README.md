# sip-k8s-lab
En lab server för sip i k8s

## Kamailio SIP Server i Kubernetes

Detta projekt innehåller en komplett Kamailio SIP server-konfiguration för Kubernetes.

### Komponenter

- **Kamailio SIP Proxy** - Huvudkomponenten för SIP-trafik
- **MySQL Database** - För användarregistrering och autentisering
- **Kubernetes Services** - För nätverkskommunikation
- **Ingress** - För extern åtkomst
- **Scripts** - Automatiserade deployment- och cleanup-script

### Installation

#### Förberedelse

1. **Kontrollera att du har minikube och Docker:**
```bash
# Starta minikube om det inte är igång
minikube start --driver=docker

# Kontrollera att Docker fungerar
docker ps
```

2. **Bygg Kamailio-containern:**
```bash
# Anslut till minikube's Docker daemon
eval $(minikube docker-env)

# Bygg containern
docker build -t local/kamailio:latest .
```

#### Snabbstart med Script (Rekommenderat)

1. **Kör deployment-scriptet:**
```bash
./scripts/deploy.sh
```

Detta script kommer att:
- Kontrollera att Kubernetes-klustret är tillgängligt
- Skapa alla nödvändiga resurser
- Vänta på att pods ska starta
- Visa status och användningsinstruktioner

#### Manuell Installation

1. **Skapa namespace och resurser:**
```bash
kubectl apply -k k8s/
```

2. **Kontrollera att alla pods är igång:**
```bash
kubectl get pods -n kamailio
```

3. **Kontrollera services:**
```bash
kubectl get svc -n kamailio
```

### Konfiguration

Kamailio är konfigurerad med följande funktioner:
- SIP proxy för UDP/TCP/TLS
- Användarregistrering
- Autentisering
- NAT traversal
- Load balancing

Konfigurationsfilen finns i `k8s/configmap.yaml` och kan redigeras efter behov.

### Portar

- **5060/UDP** - SIP (UDP)
- **5060/TCP** - SIP (TCP)
- **5061/TCP** - SIP (TLS)

För att testa anslutningen lokalt:
```bash
kubectl port-forward svc/kamailio-service 5060:5060 -n kamailio
```

### Databas

MySQL-databasen används för:
- Användarregistrering
- Autentiseringsuppgifter
- ACL (Access Control Lists)

För att ansluta till databasen:
```bash
kubectl exec -it deployment/mysql -n kamailio -- mysql -u kamailio -p kamailio
```

### Monitoring

För att kontrollera Kamailio-status:
```bash
kubectl exec -it deployment/kamailio -n kamailio -- kamcmd core.uptime
```

För att kontrollera om Kamailio lyssnar på port 5060:
```bash
kubectl exec -it deployment/kamailio -n kamailio -- netstat -tlnp | grep 5060
```

För att se alla pods och deras status:
```bash
kubectl get pods -n kamailio
```

För att se services och deras endpoints:
```bash
kubectl get svc -n kamailio
```

### Loggar

För att se loggar:
```bash
kubectl logs deployment/kamailio -n kamailio
```

För att följa loggar i realtid:
```bash
kubectl logs deployment/kamailio -n kamailio -f
```

### Felsökning

#### Vanliga problem:

1. **ImagePullBackOff eller ErrImageNeverPull:**
```bash
# Kontrollera att du är ansluten till minikube's Docker daemon
eval $(minikube docker-env)

# Bygg om containern
docker build -t local/kamailio:latest .
```

2. **CrashLoopBackOff:**
```bash
# Kontrollera loggarna
kubectl logs deployment/kamailio -n kamailio

# Kontrollera att containern startar lokalt
docker run --rm local/kamailio:latest kamailio -f /etc/kamailio/kamailio.cfg -DD -E
```

3. **Kubernetes-kluster inte tillgängligt:**
```bash
# Starta minikube
minikube start --driver=docker

# Kontrollera status
kubectl cluster-info
```

### Rensa

#### Snabbstart med Script (Rekommenderat)

För att ta bort alla resurser:
```bash
./scripts/cleanup.sh
```

#### Manuell Rensning

För att ta bort alla resurser:
```bash
kubectl delete -k k8s/
```

### Uppdatera Containern

Om du gör ändringar i koden eller konfigurationen behöver du bygga om containern:

```bash
# Anslut till minikube's Docker daemon
eval $(minikube docker-env)

# Bygg om containern med ny tag
docker build -t local/kamailio:v2 .

# Uppdatera deployment med ny image
kubectl set image deployment/kamailio kamailio=local/kamailio:v2 -n kamailio

# Eller ta bort och skapa om deployment
kubectl delete deployment kamailio -n kamailio
kubectl apply -f k8s/deployment.yaml
```


sip-k8s-lab/
├── k8s/
│   ├── namespace.yaml          # Namespace för Kamailio
│   ├── configmap.yaml          # Kamailio-konfiguration
│   ├── mysql-deployment.yaml   # MySQL-databas
│   ├── deployment.yaml         # Kamailio-deployment
│   ├── service.yaml            # Services för nätverkskommunikation
│   ├── ingress.yaml            # Ingress för extern åtkomst
│   └── kustomization.yaml      # Kustomize-konfiguration
├── scripts/
│   ├── deploy.sh               # Deployment-script
│   └── cleanup.sh              # Cleanup-script
└── README.md                   # Dokumentation

🚀 Funktioner

Kamailio SIP Server:
SIP proxy för UDP/TCP/TLS (port 5060/5061)
Användarregistrering och autentisering
NAT traversal-stöd
Load balancing med 2 repliker
Health checks och monitoring
MySQL Database:
Persistent storage för användardata
Konfigurerad för Kamailio
Automatisk databas-initiering
Kubernetes Services:
LoadBalancer för extern åtkomst
ClusterIP för intern kommunikation
Ingress för HTTP/HTTPS-åtkomst
