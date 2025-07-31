# SIPp Tester

SIPp-tester för att validera Kamailio-konfigurationer i olika miljöer.

## Konfiguration

### Environment-variabler

Du kan konfigurera tester via environment-variabler:

```bash
# Sätt Kamailio host
export KAMAILIO_HOST="192.168.1.100"

# Sätt Kamailio port
export KAMAILIO_PORT="5060"

# Sätt miljö (local/prod/auto)
export KAMAILIO_ENVIRONMENT="local"
```

### Kommandoradsargument

Du kan också använda kommandoradsargument som override environment-variabler:

```bash
# Override environment-variabler med kommandoradsargument
python -m pytest test_sipp_pytest.py --kamailio-host="192.168.1.100" --kamailio-port="5060" --environment="local"
```

### Prioritering

1. **Kommandoradsargument** (högst prioritet)
2. **Environment-variabler**
3. **Auto-detektering** (lägst prioritet)

## Environment-flaggor

Testerna stöder olika miljöer via `--environment` flaggan:

### `--environment=local` (Kind-kluster)
Används för lokala Kind-kluster:
- Använder Kind NodePort service (`172.18.0.2:30600`)
- Optimerad för UDP-tester
- Automatisk detektering av worker node IP

```bash
# Kör tester med Kind-kluster
python -m pytest test_sipp_pytest.py -v -s --run-with-kamailio --environment=local
```

### `--environment=prod` (Hårdvaru-kluster)
Används för produktionsmiljöer:
- Använder LoadBalancer eller ClusterIP
- Optimerad för produktionsnätverk
- Automatisk detektering av LoadBalancer IP

```bash
# Kör tester med produktionskluster
python -m pytest test_sipp_pytest.py -v -s --run-with-kamailio --environment=prod
```

### `--environment=auto` (Auto-detektering)
Standard som automatiskt väljer bästa miljö:
- Testar Kind NodePort först
- Fallback till localhost
- Flexibel för olika miljöer

```bash
# Kör tester med auto-detektering
python -m pytest test_sipp_pytest.py -v -s --run-with-kamailio --environment=auto
```

## Exempel

### Environment-variabler

#### Kind-kluster (lokal utveckling)
```bash
# Sätt environment-variabler
export KAMAILIO_ENVIRONMENT="local"

# Kör tester
python -m pytest test_sipp_pytest.py -v -s --run-with-kamailio
```

#### Produktionskluster
```bash
# Sätt environment-variabler
export KAMAILIO_HOST="prod-kamailio.example.com"
export KAMAILIO_PORT="5060"
export KAMAILIO_ENVIRONMENT="prod"

# Kör tester
python -m pytest test_sipp_pytest.py -v -s --run-with-kamailio
```

#### Extern server
```bash
# Sätt environment-variabler
export KAMAILIO_HOST="192.168.1.100"
export KAMAILIO_PORT="5060"
export KAMAILIO_ENVIRONMENT="auto"

# Kör tester
python -m pytest test_sipp_pytest.py -v -s --run-with-kamailio
```

### Kommandoradsargument

#### Kind-kluster (lokal utveckling)
```bash
# Miljökontroller
python -m pytest test_environment_only.py -v -s

# SIPp-tester med Kind
python -m pytest test_sipp_pytest.py -v -s --run-with-kamailio --environment=local
```

#### Produktionskluster
```bash
# SIPp-tester med produktionskluster
python -m pytest test_sipp_pytest.py -v -s --run-with-kamailio --environment=prod
```

#### Extern server
```bash
# SIPp-tester mot extern server
python -m pytest test_sipp_pytest.py -v -s --run-with-kamailio --kamailio-host="192.168.1.100" --kamailio-port="5060"
```

## Host-detektering

### Local Environment
- **Primary:** Kind NodePort (`172.18.0.2:30600`)
- **Fallback:** localhost:30600
- **Final:** localhost

### Production Environment
- **Primary:** LoadBalancer IP
- **Fallback:** ClusterIP service
- **Final:** `kamailio-service.kamailio.svc.cluster.local`

### Auto Environment
- **Primary:** Kind NodePort
- **Secondary:** localhost:30600
- **Tertiary:** host.docker.internal
- **Final:** localhost

## Fördelar

1. **Enkel konfiguration** - En flagga för hela miljön
2. **Automatisk detektering** - Väljer rätt host automatiskt
3. **Flexibilitet** - Fungerar i olika miljöer
4. **Tydlighet** - Vet exakt vilken miljö som används

## Environment-variabler

### KAMAILIO_HOST
Sätt Kamailio-serverns hostname/IP:
```bash
export KAMAILIO_HOST="192.168.1.100"
export KAMAILIO_HOST="kamailio.example.com"
export KAMAILIO_HOST="172.18.0.2"  # Kind worker node
```

### KAMAILIO_PORT
Sätt Kamailio-serverns port:
```bash
export KAMAILIO_PORT="5060"     # Standard SIP-port
export KAMAILIO_PORT="30600"    # Kind NodePort
export KAMAILIO_PORT="5061"     # Alternativ port
```

### KAMAILIO_ENVIRONMENT
Sätt miljö för auto-detektering:
```bash
export KAMAILIO_ENVIRONMENT="local"  # Kind-kluster
export KAMAILIO_ENVIRONMENT="prod"   # Produktionskluster
export KAMAILIO_ENVIRONMENT="auto"   # Auto-detektering (standard)
```

### Exempel på kombinationer

#### Kind-kluster med NodePort
```bash
export KAMAILIO_HOST="172.18.0.2"
export KAMAILIO_PORT="30600"
export KAMAILIO_ENVIRONMENT="local"
```

#### Produktionskluster med LoadBalancer
```bash
export KAMAILIO_HOST="prod-kamailio.example.com"
export KAMAILIO_PORT="5060"
export KAMAILIO_ENVIRONMENT="prod"
```

#### Extern server
```bash
export KAMAILIO_HOST="192.168.1.100"
export KAMAILIO_PORT="5060"
export KAMAILIO_ENVIRONMENT="auto"
```

## Troubleshooting

### Kind-kluster problem
```bash
# Kontrollera att Kind-kluster körs
kubectl cluster-info

# Kontrollera NodePort
kubectl get svc kamailio-nodeport -n kamailio

# Testa anslutning
nc -zu 172.18.0.2 30600
```

### Produktionskluster problem
```bash
# Kontrollera LoadBalancer
kubectl get svc kamailio-service -n kamailio

# Kontrollera pods
kubectl get pods -n kamailio
``` 