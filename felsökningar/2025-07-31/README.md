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