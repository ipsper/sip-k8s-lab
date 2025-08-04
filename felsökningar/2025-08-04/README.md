# Felsökning 2025-08-04: Nätverksrouting mellan Docker och Kubernetes

## 🎯 Problembeskrivning

**Huvudproblem:** SIPp-tester misslyckades eftersom SIPp inte kunde nå Kamailio
- SIPp kör i Docker på `172.18.0.2`
- Kamailio kör i K8s på `10.244.2.15`
- Ingen direkt routing mellan Docker-nätverket och K8s-nätverket

## 🔍 Rotorsak identifierad

**Nätverksrouting-problem:**
```
SIPp (Docker) 172.18.0.2 → Kamailio (K8s) 10.244.2.15
```

### Vad som inte fungerade:
1. **NodePort (172.18.0.2:30600):** SIPp kunde ansluta men traffic når inte Kamailio
2. **Port-forward:** Fungerade lokalt men inte för Docker-containrar
3. **Direkt pod IP:** Kunde inte nås från Docker-nätverket

## ✅ Lösning implementerad

### 1. MetalLB LoadBalancer
```bash
# Installera MetalLB för Kind
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.13.12/config/manifests/metallb-native.yaml

# Konfigurera IP-pool
kubectl apply -f k8s/metallb-config.yaml
```

### 2. LoadBalancer Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: kamailio-loadbalancer
  namespace: kamailio
spec:
  type: LoadBalancer
  selector:
    app: kamailio
  ports:
    - name: sip-udp
      protocol: UDP
      port: 5060
      targetPort: 5060
```

### 3. Resultat
- **LoadBalancer IP:** `172.18.0.242:5060`
- **Nätverksrouting:** ✅ Fungerar
- **SIPp kan nå Kamailio:** ✅ Via LoadBalancer

## 🔧 Tekniska detaljer

### Nätverksarkitektur före:
```
SIPp (Docker) 172.18.0.2
    ↓ (ingen routing)
Kamailio (K8s) 10.244.2.15
```

### Nätverksarkitektur efter:
```
SIPp (Docker) 172.18.0.2
    ↓ (via LoadBalancer)
LoadBalancer 172.18.0.242:5060
    ↓ (K8s routing)
Kamailio (K8s) 10.244.2.15:5060
```

### MetalLB-konfiguration:
```yaml
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: first-pool
  namespace: metallb-system
spec:
  addresses:
  - 172.18.0.240-172.18.0.250
```

## 🧪 Tester utförda

### 1. Nätverksanslutning
```bash
# Testa LoadBalancer
nc -zu 172.18.0.242 5060
# ✅ Fungerar

# Testa NodePort
nc -zu 172.18.0.2 30600
# ✅ Fungerar
```

### 2. SIPp-tester
```bash
# Testa med LoadBalancer
docker run --rm -v $(pwd)/sipp-scenarios:/scenarios \
  local/sipp-tester:latest sipp 172.18.0.242:5060 \
  -sf /scenarios/options.xml -p 5062 -m 1 -timeout 5s
```

### 3. Manuella SIP-requests
```bash
# Testa direkt till LoadBalancer
echo -e "OPTIONS sip:kamailio.local SIP/2.0\r\n..." | nc -u 172.18.0.242 5060
```

## 📊 Resultat

### ✅ Vad som fungerar:
1. **LoadBalancer skapad:** `172.18.0.242:5060`
2. **MetalLB installerat:** För Kind-kluster
3. **Nätverksrouting:** SIPp kan nå Kamailio via LoadBalancer
4. **Anslutning:** UDP-anslutning fungerar

### 🔍 Vad som fortfarande inte fungerar:
**Kamailio tar inte emot requests** - detta verkar vara ett problem med Kamailio-konfigurationen, inte nätverket.

## 🚀 Nästa steg

### Prioriterade uppgifter:
1. **Debugga Kamailio-konfigurationen** - varför tar den inte emot requests?
2. **Testa med enklare Kamailio-konfiguration** - bara loggning utan svar
3. **Kontrollera SIPp-scenariot** - är SIP-messaget korrekt formaterat?

### Långsiktiga förbättringar:
1. **Automatisera LoadBalancer-setup** i deployment-script
2. **Dokumentera nätverksarkitektur** för framtida referens
3. **Skapa monitoring** för LoadBalancer-trafik

## 📝 Lärdomar

### Viktiga insikter:
1. **Kind vs Minikube:** Kind använder Docker-nätverk, vilket skapar routing-problem
2. **LoadBalancer vs NodePort:** LoadBalancer ger bättre routing för Docker-containrar
3. **MetalLB:** Nödvändigt för LoadBalancer i Kind-kluster

### Best practices:
1. **Använd LoadBalancer** för Docker-till-K8s kommunikation
2. **Installera MetalLB** i Kind-kluster
3. **Testa nätverksanslutning** innan SIPp-tester

## 🔗 Relaterade filer

- `k8s/metallb-config.yaml` - MetalLB-konfiguration
- `k8s/service.yaml` - LoadBalancer service
- `sipp-tester/sipp-scenarios/options.xml` - SIPp-testscenario

---

**Datum:** 2025-08-04  
**Status:** Nätverksrouting löst, Kamailio-konfiguration kvar  
**Nästa:** Debugga Kamailio-konfiguration 