# Felsökning 2025-08-04: Nätverksrouting och NodePort vs LoadBalancer

## Problembeskrivning
SIPp-tester misslyckas med "Failed call" och "0 Successful call" trots att Kamailio är igång och nätverksanslutningar fungerar.

## Diagnostik

### 1. Nätverksrouting-problem identifierade
- **LoadBalancer UDP-anslutning**: ✅ Fungerar (`nc -zu 172.18.0.242 5060`)
- **NodePort UDP-anslutning**: ✅ Fungerar (`nc -zu 172.18.0.2 30600`)
- **Pod-anslutning**: ✅ Fungerar (`nc -zu 10.244.2.23 5060`)
- **SIP-routing**: ❌ Timeout - ingen respons

### 2. SIPp-testresultat
```bash
# LoadBalancer test
docker run --rm --network=host local/sipp-tester:latest bash -c "sipp -sf /app/sipp-scenarios/options.xml 172.18.0.242:5060 -p 5068 -d 1000 -m 1 -r 1 -timeout 10"
# Resultat: 0 Successful call, 1 Failed call

# NodePort test  
docker run --rm --network=host local/sipp-tester:latest bash -c "sipp -sf /app/sipp-scenarios/options.xml 172.18.0.2:30600 -p 5069 -d 1000 -m 1 -r 1 -timeout 10"
# Resultat: 0 Successful call, 1 Failed call
```

### 3. Kamailio-loggar
Inga "Received SIP request" loggar visas i Kamailio, vilket betyder att SIP-meddelanden inte når Kamailio-pods.

### 4. Manuella nätverkstester
```bash
# Test från host till NodePort
echo -e "OPTIONS sip:kamailio.local SIP/2.0\r\n..." | nc -u 172.18.0.2 30600
# Resultat: Hänger (väntar på svar som aldrig kommer)

# Test från host till LoadBalancer  
echo -e "OPTIONS sip:kamailio.local SIP/2.0\r\n..." | nc -u 172.18.0.242 5060
# Resultat: Hänger (väntar på svar som aldrig kommer)

# Test från host direkt till pod
echo -e "OPTIONS sip:kamailio.local SIP/2.0\r\n..." | nc -u 10.244.1.14 5060
# Resultat: Hänger (väntar på svar som aldrig kommer)
```

## Rotorsak
**Nätverksrouting-problem i Kind-kluster**: Trots att grundläggande UDP-anslutningar fungerar (`nc -zu`), når SIP-meddelanden inte Kamailio-pods. Detta indikerar ett djupare problem med UDP-routing i Kind/MetalLB.

## Lösningsförsök

### 1. Uppdaterat SIPp-support för NodePort-prioritet
```python
# app/sipp_support.py - _detect_auto_host()
# Ändrat prioritet från LoadBalancer -> NodePort -> Fallback
# till NodePort -> LoadBalancer -> Fallback
```

### 2. Uppdaterat nätverkstester
```python
# app/test_support.py - NetworkRoutingSupport
# test_sipp_to_kamailio_routing() nu använder NodePort (172.18.0.2:30600)
```

### 3. Kamailio-konfiguration kontrollerad
```yaml
# k8s/configmap.yaml
listen=udp:0.0.0.0:5060
listen=tcp:0.0.0.0:5060
# Konfiguration ser korrekt ut
```

## Slutsats
Problemet är **inte** Kamailio-konfigurationen eller SIPp-inställningarna, utan ett **nätverksrouting-problem i Kind-kluster**. 

### Rekommenderad lösning
1. **Använd NodePort istället för LoadBalancer** för SIPp-tester i Kind
2. **Implementera port-forward** som alternativ till LoadBalancer/NodePort
3. **Överväg Minikube** för bättre nätverksrouting om problemet kvarstår

## Tekniska detaljer

### Kubernetes Services
```bash
# NodePort service
kubectl get svc -n kamailio kamailio-nodeport
# Ports: 30600/UDP, 30601/TCP -> 5060

# LoadBalancer service  
kubectl get svc -n kamailio kamailio-loadbalancer
# IP: 172.18.0.242:5060
```

### Pod-topologi
```bash
kubectl get pods -n kamailio -o wide
# kamailio-7fd7c67566-hb4rn: 10.244.2.23 (worker)
# kamailio-7fd7c67566-vnmjp: 10.244.1.14 (worker2)
```

### Endpoints
```bash
kubectl get endpoints -n kamailio kamailio-nodeport
# 10.244.1.14:5060, 10.244.2.23:5060
```

## Nästa steg
1. Implementera port-forward som fallback
2. Testa med Minikube för jämförelse
3. Dokumentera lösning i README 