# Felsökning: test_options_scenario timeout

**Datum:** 2025-07-31  
**Problem:** `test_sipp_pytest.py::TestSippTester::test_options_scenario FAILED`

## Problembeskrivning

SIPp-testet `test_options_scenario` fick timeout och misslyckades med fel:
```
test_sipp_pytest.py::TestSippTester::test_options_scenario FAILED   [ 72%]
```

## Rotorsaksanalys

### 1. Docker Image Problem
**Problem:** Koden använde fel Docker-image namn
- **Fel:** `sipp-tester:latest`
- **Rätt:** `local/sipp-tester:latest`

**Lösning:** Uppdaterade `sipp_tester.py` för att använda `self.docker_image` istället för hårdkodade image-namn.

### 2. Kamailio tm Module Problem
**Problem:** Kamailio kunde inte ladda `tm` (Transaction Management) modulen
```
ERROR: could not bind tm module - only stateless mode available during runtime
```

**Orsak:** `tm` modulen laddades inte i konfigurationen
**Lösning:** Lade till `loadmodule "tm.so"` i Kamailio-konfigurationen

### 3. Miljökontroll Problem
**Problem:** `test_environment_only.py` hittade inte problemet
**Orsak:** Kontrollerade bara grundläggande komponenter, inte SIP-funktionalitet

**Lösning:** Lade till `test_kamailio_sip_response()` som skickar riktiga SIP-requests

## Tekniska Detaljer

### Docker Image Fix
```python
# Före
"sipp-tester:latest"

# Efter  
self.docker_image  # Standard: "local/sipp-tester:latest"
```

### Kamailio Konfiguration
```bash
# Före
loadmodule "sl.so"
loadmodule "xlog.so"

# Efter
loadmodule "tm.so"  # Lägg till först
loadmodule "sl.so"
loadmodule "xlog.so"
```

### Miljökontroll Förbättring
```python
def test_kamailio_sip_response(self):
    """Testa att Kamailio svarar på SIP-requests"""
    # Skickar riktig SIP OPTIONS request
    # Kontrollerar om Kamailio svarar
```

## Resultat

### Löst
- ✅ Docker image problem
- ✅ tm module problem  
- ✅ Miljökontroll förbättring

### Kvarstående
- ❌ Kamailio svarar fortfarande inte på SIP-requests
- ❌ `test_options_scenario` får timeout

## Nästa Steg

1. **Testa Kind istället för Minikube**
   - Port-forward problem kan lösas med bättre nätverkshantering
   - Kind använder Docker-nätverk direkt
   - Skapa Kind-kluster: `./scripts/setup-kind.sh`

2. **Undersök port-forward problem**
   - Port-forward fungerar inte korrekt
   - Fel: `Connection refused`

3. **Kontrollera nätverkskonfiguration**
   - Kamailio lyssnar på rätt interface
   - UDP/TCP portar är öppna

4. **Förbättra Kamailio-konfiguration**
   - Lägg till bättre SIP-hantering
   - Konfigurera för att svara på OPTIONS

## Lärdomar

1. **Docker Image Namn:** Använd alltid variabler istället för hårdkodade namn
2. **Kamailio Moduler:** tm-modulen är kritisk för SIP-funktionalitet
3. **Miljökontroller:** Testa faktisk funktionalitet, inte bara tillgänglighet
4. **Port-forward:** Kan vara instabilt, behöver bättre felhantering
5. **Test Separation:** Separera miljökontroller från funktionella tester för bättre underhåll

## Filer Ändrade

- `sipp-tester/sipp_tester.py` - Fixade Docker image namn
- `k8s/configmap.yaml` - Lade till tm module
- `sipp-tester/test_environment_only.py` - Lade till SIP-response test
- `sipp-tester/test_sipp_pytest.py` - Renodlade SIPp-tester (tog bort överlappande miljökontroller)

## Kommandon

```bash
# Uppdatera Kamailio konfiguration
kubectl apply -f k8s/configmap.yaml
kubectl rollout restart deployment/kamailio -n kamailio

# Testa miljö
python -m pytest test_environment_only.py -v -s

# Testa SIPp
python -m pytest test_sipp_pytest.py::TestSippTester::test_options_scenario -v -s

# Kind setup (rekommenderat)
./scripts/setup-kind.sh
```

---

# Felsökning: localhost timeout problem efter bytt till Kind

**Datum:** 2025-07-31  
**Problem:** `test_kamailio_sip_response` timeout med localhost

## Problembeskrivning

Efter att ha bytt till Kind-kluster fick `test_kamailio_sip_response` timeout:
```
⚠️  Kamailio SIP-response test misslyckades: Command '['nc', '-u', 'localhost', '5060']' timed out after 10 seconds
```

## Rotorsaksanalys

### 1. Port-forward Instabilitet
**Problem:** `kubectl port-forward` var instabilt och gav "Connection refused" fel
```
E connect(5, AF=2 127.0.0.1:5060, 16): Connection refused
```

**Orsak:** Port-forward fungerar inte konsekvent med Kind-kluster
**Lösning:** Använd NodePort istället för port-forward

### 2. Localhost-begränsning
**Problem:** Användning av `localhost` fungerade inte konsekvent
- **Fel:** `nc -u localhost 5060`
- **Rätt:** `nc -u 172.18.0.2 30600`

**Orsak:** Localhost är inte tillgängligt från host-systemet till Kind-kluster
**Lösning:** Använd worker node IP direkt

## Tekniska Detaljer

### Port-forward Problem
```bash
# Före (instabilt)
kubectl port-forward svc/kamailio-service 5060:5060 -n kamailio &
nc -u localhost 5060

# Efter (stabilt)
# Hämta NodePort dynamiskt
nodeport=$(kubectl get svc kamailio-nodeport -n kamailio -o jsonpath='{.spec.ports[?(@.port==5060)].nodePort}')
node_ip=$(kubectl get nodes sipp-k8s-lab-worker -o jsonpath='{.status.addresses[?(@.type=="InternalIP")].address}')
nc -u $node_ip $nodeport
```

### NodePort vs Port-forward
```bash
# Port-forward (instabilt)
Forwarding from 127.0.0.1:5060 -> 5060
E connect(5, AF=2 127.0.0.1:5060, 16): Connection refused

# NodePort (stabilt)
Använder NodePort: 30600
Använder worker node IP: 172.18.0.2
✅ Kamailio svarar på SIP-requests
```

### Test Uppdatering
```python
# Före
result = subprocess.run(
    ["nc", "-u", "localhost", "5060"],
    input=sip_request,
    capture_output=True,
    text=True,
    timeout=10
)

# Efter
result = subprocess.run(
    ["nc", "-u", node_ip, nodeport],
    input=sip_request,
    capture_output=True,
    text=True,
    timeout=10
)
```

## Resultat

### Löst
- ✅ Port-forward instabilitet
- ✅ Localhost-begränsning
- ✅ `test_kamailio_sip_response` fungerar nu

### Teknisk Förklaring
- **NodePort:** Ger direkt tillgång till Kamailio utan port-forward
- **Worker Node IP:** `172.18.0.2` istället för localhost
- **UDP Port:** `30600` istället för 5060

## Lärdomar

1. **Kind vs Minikube:** Kind använder Docker-nätverk direkt, port-forward fungerar annorlunda
2. **NodePort:** Mer stabil än port-forward för tester
3. **Localhost:** Inte alltid tillgängligt i container-miljöer
4. **Dynamisk Konfiguration:** Hämta NodePort och IP dynamiskt för flexibilitet

## Filer Ändrade

- `sipp-tester/test_sipp_pytest.py` - Uppdaterade `test_kamailio_sip_response` för att använda NodePort

## Kommandon

```bash
# Testa NodePort-anslutning
kubectl get svc kamailio-nodeport -n kamailio
kubectl get nodes sipp-k8s-lab-worker -o jsonpath='{.status.addresses[?(@.type=="InternalIP")].address}'

# Testa SIP-response
python -m pytest test_sipp_pytest.py::TestSippTesterWithKamailio::test_kamailio_sip_response -v -s --run-with-kamailio
``` 