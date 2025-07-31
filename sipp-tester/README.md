# SIPp Tester för Kamailio

Detta bibliotek innehåller SIPp-baserade tester för att verifiera Kamailio SIP-servern i Kubernetes.

## 📁 Struktur

```
sipp-tester/
├── Dockerfile                    # SIPp test-container
├── test-scripts/
│   ├── run-tests.sh             # Huvudtest-script
│   ├── health-check.sh          # Health check-script
│   └── build-and-test.sh        # Build och test-script
├── scripts/
│   ├── run-local-tests.sh       # Testa mot lokal Kamailio
│   └── test-remote.sh           # Testa mot extern server
├── sipp-scenarios/
│   ├── options.xml              # OPTIONS-test scenario
│   ├── register.xml             # REGISTER-test scenario
│   ├── invite.xml               # INVITE-test scenario
│   └── ping.xml                 # Ping-test scenario
├── sipp_tester.py               # Python wrapper för SIPp-tester
├── test_sipp_pytest.py          # Pytest-tester för SIPp
├── test_environment_only.py     # Miljötester (separat fil)
├── conftest.py                  # Pytest-konfiguration
├── pytest.ini                  # Pytest-inställningar
├── run_tests.py                 # Enkelt test-script
├── requirements.txt             # Python-dependencies
├── setup_venv.sh               # Skapa virtuell miljö
├── activate_venv.sh            # Aktivera virtuell miljö
├── run_tests_venv.sh           # Kör tester med venv
├── .gitignore                  # Git ignore-fil
└── README.md                    # Denna fil
```

## 🐍 Virtual Environment

Detta projekt använder Python virtual environment för att isolera dependencies.

### Skapa virtuell miljö

```bash
# Skapa och konfigurera virtuell miljö
./setup_venv.sh
```

### Aktivera virtuell miljö

```bash
# Aktivera miljön
source venv/bin/activate

# Eller använd hjälpscript
./activate_venv.sh
```

### Deaktivera virtuell miljö

```bash
deactivate
```

### Hantera dependencies

```bash
# Installera nya paket
pip install paketnamn

# Uppdatera requirements.txt
pip freeze > requirements.txt

# Installera från requirements.txt
pip install -r requirements.txt
```

## 🚀 Snabbstart

### 1. Python-tester med Virtual Environment (Rekommenderat)

```bash
# Skapa och aktivera virtuell miljö
./setup_venv.sh

# Aktivera virtuell miljö (om den redan finns)
source venv/bin/activate

# Kör miljötester först
python -m pytest test_environment_only.py -v

# Kör interaktiv test-meny
python run_tests.py

# Eller kör direkt med pytest
python -m pytest test_sipp_pytest.py -v

# Kör med Kamailio (port-forward)
python -m pytest test_sipp_pytest.py::TestSippTesterWithKamailio --run-with-kamailio -v

# Kör tester med venv (enklaste sättet)
./run_tests_venv.sh
```

### 2. Python-tester utan Virtual Environment

```bash
# Installera dependencies globalt
pip install -r requirements.txt

# Kör tester
python run_tests.py
python -m pytest test_sipp_pytest.py -v
```

### 3. Shell-script (Alternativ)

```bash
# Bygg och kör tester
./scripts/build-and-test.sh

# Testa mot lokal Kamailio (port-forward)
./scripts/run-local-tests.sh

# Testa mot extern server
KAMAILIO_HOST=192.168.1.100 KAMAILIO_PORT=5060 ./scripts/test-remote.sh
```

### 4. Manuell körning

```bash
# Bygg containern
docker build -t local/sipp-tester:latest .

# Kör health check
docker run --rm local/sipp-tester:latest /app/test-scripts/health-check.sh

# Kör alla tester
docker run --rm local/sipp-tester:latest /app/test-scripts/run-tests.sh
```

## 🧪 Tester

### Miljötester (test_environment_only.py)

#### TestEnvironment
- **test_docker_available**: Kontrollerar att Docker är tillgängligt
- **test_kubectl_available**: Kontrollerar att kubectl är tillgängligt
- **test_kubernetes_cluster_available**: Kontrollerar att Kubernetes-kluster är tillgängligt
- **test_sipp_tester_image_exists**: Kontrollerar att SIPp test Docker-image finns
- **test_sipp_tester_container_starts**: Kontrollerar att SIPp test container kan startas
- **test_kamailio_namespace_exists**: Kontrollerar att kamailio namespace finns
- **test_kamailio_deployment_exists**: Kontrollerar att Kamailio deployment finns
- **test_kamailio_pods_running**: Kontrollerar att Kamailio pods körs
- **test_kamailio_service_exists**: Kontrollerar att Kamailio service finns
- **test_kamailio_port_accessible**: Kontrollerar att Kamailio port är tillgänglig
- **test_sipp_installed_in_container**: Kontrollerar att SIPp är installerat i container
- **test_sipp_scenarios_exist**: Kontrollerar att SIPp scenarios finns
- **test_environment_summary**: Sammanfattning av alla miljökontroller

### SIPp-tester (test_sipp_pytest.py)

#### TestSippTester (Grundläggande)
- **test_docker_image_exists**: Kontrollerar att Docker-image finns
- **test_health_check**: Kör health check (kan misslyckas om Kamailio inte är igång)
- **test_options_scenario**: Testar OPTIONS-scenario (hoppas över om Kamailio inte är igång)
- **test_register_scenario**: Testar REGISTER-scenario (hoppas över om Kamailio inte är igång)
- **test_invite_scenario**: Testar INVITE-scenario (hoppas över om Kamailio inte är igång)
- **test_ping_scenario**: Testar PING-scenario (hoppas över om Kamailio inte är igång)
- **test_all_scenarios**: Kör alla scenarios

#### TestSippTesterWithKamailio (Integration)
- **test_health_check_with_kamailio**: Health check när Kamailio är igång
- **test_options_with_kamailio**: OPTIONS-test när Kamailio är igång

### Shell-script tester

#### Health Check
- **Syfte**: Kontrollerar att Kamailio-servern är tillgänglig
- **Metod**: Använder `nc` för att testa port-anslutning och skickar en enkel OPTIONS-request
- **Förväntat resultat**: 200 OK eller 405 Method Not Allowed

#### OPTIONS Test
- **Syfte**: Testar SIP OPTIONS-funktionalitet
- **Metod**: Skickar OPTIONS-request och förväntar 200 OK
- **Förväntat resultat**: 200 OK

#### REGISTER Test
- **Syfte**: Testar SIP REGISTER-funktionalitet
- **Metod**: Skickar REGISTER-request
- **Förväntat resultat**: 200 OK eller 401 Unauthorized

#### INVITE Test
- **Syfte**: Testar SIP INVITE-funktionalitet
- **Metod**: Skickar INVITE-request
- **Förväntat resultat**: 200 OK, 404 Not Found, eller 486 Busy Here

#### PING Test
- **Syfte**: Testar SIP MESSAGE-funktionalitet som ping
- **Metod**: Skickar MESSAGE-request
- **Förväntat resultat**: 200 OK eller 202 Accepted

## ⚙️ Konfiguration

### Miljövariabler

- `KAMAILIO_HOST` - Kamailio-serverns hostname (default: localhost)
- `KAMAILIO_PORT` - Kamailio-serverns port (default: 5060)
- `TEST_TIMEOUT` - Timeout för tester i sekunder (default: 30)

### Exempel

```bash
# Kör tester mot specifik server
KAMAILIO_HOST=192.168.1.100 KAMAILIO_PORT=5060 \
docker run --rm local/sipp-tester:latest /app/test-scripts/run-tests.sh
```

## 📊 Resultat

Testerna ger följande resultat:

- **PASSED** - Testet lyckades
- **FAILED** - Testet misslyckades
- **TIMEOUT** - Testet tog för lång tid

## 🔧 Felsökning

### Vanliga problem:

1. **Kan inte ansluta till Kamailio:**
   - Kontrollera att Kamailio är igång
   - Verifiera hostname och port
   - Kontrollera nätverksanslutning

2. **SIPp kan inte starta:**
   - Kontrollera att containern byggdes korrekt
   - Verifiera att SIPp är installerat

3. **Tester timeout:**
   - Öka TEST_TIMEOUT-värdet
   - Kontrollera Kamailio-prestanda

4. **Virtual Environment-problem:**
   - Kontrollera att Python 3 är installerat
   - Ta bort `venv/`-mappen och kör `./setup_venv.sh` igen
   - Verifiera att `source venv/bin/activate` kördes

## 📝 Lägga till nya tester

### Python-tester

1. Lägg till ny test-metod i `test_sipp_pytest.py`
2. Uppdatera `sipp_tester.py` om det behövs
3. Uppdatera dokumentation

### Shell-script tester

1. Skapa nytt scenario i `sipp-scenarios/`
2. Lägg till test i `run-tests.sh`
3. Uppdatera dokumentation

### Exempel på nytt scenario:

```xml
<?xml version="1.0" encoding="ISO-8859-1" ?>
<!DOCTYPE scenario SYSTEM "sipp.dtd">

<scenario name="Custom Test">
  <send>
    <![CDATA[
      CUSTOM sip:kamailio.local SIP/2.0
      Via: SIP/2.0/UDP [local_ip]:[local_port];branch=[branch]
      From: <sip:test@kamailio.local>;tag=[call_number]
      To: <sip:kamailio.local>
      Call-ID: [call_id]
      CSeq: 1 CUSTOM
      Content-Length: 0
    ]]>
  </send>
  
  <recv response="200" optional="true">
  </recv>
</scenario>
```

### Exempel på nytt Python-test:

```python
def test_custom_scenario(self, ensure_docker_image):
    """Testa custom scenario"""
    result = ensure_docker_image.run_sipp_test("custom")
    
    print(f"\nCustom Test Result:")
    print(f"  Success: {result.success}")
    print(f"  Exit Code: {result.exit_code}")
    print(f"  Statistics: {result.statistics}")
    
    assert result.success, f"Custom test misslyckades: {result.error}"
```

## 🤝 Bidrag

För att bidra till detta projekt:

1. Skapa en fork
2. Lägg till dina tester
3. Uppdatera dokumentation
4. Skicka pull request

## 📄 Licens

Detta projekt är öppen källkod och tillgängligt under MIT-licensen. 