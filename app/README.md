# SIP K8s Lab App

Detta är en Python-app som innehåller utility-funktioner för SIP-testning i Kubernetes-miljöer.

## Innehåll

### `sip_test_utils.py`

Huvudmodulen som innehåller utility-klasser och funktioner för:

- **KamailioConfig**: Konfigurationshantering för Kamailio
- **KubernetesUtils**: Kubernetes-operationer (namespace, deployment, service, etc.)
- **DockerUtils**: Docker-operationer (image, container)
- **NetworkUtils**: Nätverkstestning (UDP/TCP-anslutningar, port-forward)
- **EnvironmentChecker**: Miljökontroller (Docker, kubectl, Kubernetes)
- **KamailioUtils**: Kamailio-specifika operationer

### Globala funktioner

- `get_environment_status()`: Ger en sammanfattning av miljöns hälsa
- `is_environment_ready()`: Kontrollerar om miljön är redo för tester

## Användning

### Direkt körning

```bash
cd app
python sip_test_utils.py
```

### Som modul

```python
import sys
sys.path.append('app')
from sip_test_utils import EnvironmentChecker, KubernetesUtils

# Kontrollera miljö
if EnvironmentChecker.check_docker():
    print("Docker är tillgängligt")

# Hämta Kubernetes-information
if KubernetesUtils.check_namespace_exists("kamailio"):
    print("kamailio namespace finns")
```

## Struktur

```
app/
├── __init__.py          # Paket-initialisering
├── README.md           # Denna fil
└── sip_test_utils.py   # Huvudmodul med utility-funktioner
```

## Version

Version 1.0.0 - Del av SIP K8s Lab-projektet 