#!/usr/bin/env python3
"""
Test Support Classes
Innehåller klasser och funktioner som används av testerna
"""

import pytest
import time
import subprocess
import json
import os
from typing import Dict, Any, Optional, Tuple
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "sipp-tester"))
from sipp_support import SippTester
from sip_test_utils import get_environment_status, NetworkUtils


class TestEnvironmentSupport:
    """Support-klass för miljötester"""
    
    @staticmethod
    def get_kamailio_config(request) -> Dict[str, Any]:
        """Hämta Kamailio-konfiguration baserad på environment-variabler"""
        # Hämta kommandoradsargument
        cmd_host = request.config.getoption("--kamailio-host")
        cmd_port = request.config.getoption("--kamailio-port")
        cmd_env = request.config.getoption("--environment")
        
        # Använd SippTester med kommandoradsargument om de finns
        if cmd_host or cmd_port or cmd_env:
            sipp_tester = SippTester(
                kamailio_host=cmd_host,
                kamailio_port=int(cmd_port) if cmd_port else 5060,
                environment=cmd_env or "auto"
            )
        else:
            # Använd SippTester för att få rätt konfiguration
            sipp_tester = SippTester()
        
        # Om host redan innehåller port, använd den som den är
        if ":" in sipp_tester.kamailio_host:
            host = sipp_tester.kamailio_host
            port = int(sipp_tester.kamailio_host.split(":")[-1])
        else:
            host = sipp_tester.kamailio_host
            port = sipp_tester.kamailio_port
        
        return {
            'host': host,
            'port': port,
            'environment': sipp_tester.environment
        }


class MetalLBSupport:
    """Support-klass för MetalLB-tester"""
    
    @staticmethod
    def check_metallb_installed() -> bool:
        """Kontrollera om MetalLB är installerat"""
        try:
            result = subprocess.run(
                ["kubectl", "get", "namespace", "metallb-system"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    @staticmethod
    def install_metallb() -> bool:
        """Installera MetalLB"""
        try:
            print("🔧 Installerar MetalLB...")
            
            # Installera MetalLB
            install_result = subprocess.run(
                ["kubectl", "apply", "-f", "https://raw.githubusercontent.com/metallb/metallb/v0.13.12/config/manifests/metallb-native.yaml"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if install_result.returncode != 0:
                print(f"❌ Kunde inte installera MetalLB: {install_result.stderr}")
                return False
            
            print("⏳ Väntar på att MetalLB pods ska starta...")
            time.sleep(30)
            
            # Kontrollera att pods startade
            wait_result = subprocess.run(
                ["kubectl", "wait", "--namespace", "metallb-system", "--for=condition=ready", "pod", "--selector=app=metallb", "--timeout=90s"],
                capture_output=True,
                text=True,
                timeout=100
            )
            
            if wait_result.returncode == 0:
                print("✅ MetalLB installerat och redo")
                return True
            else:
                print("❌ MetalLB pods startade inte inom tidsgränsen")
                return False
                
        except Exception as e:
            print(f"❌ Kunde inte installera MetalLB: {e}")
            return False
    
    @staticmethod
    def check_metallb_config() -> bool:
        """Kontrollera om MetalLB-konfiguration finns"""
        try:
            # Kontrollera om IPAddressPool finns
            result = subprocess.run(
                ["kubectl", "get", "ipaddresspool", "first-pool", "-n", "metallb-system"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return False
            
            # Kontrollera om L2Advertisement finns
            l2_result = subprocess.run(
                ["kubectl", "get", "l2advertisement", "example", "-n", "metallb-system"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return l2_result.returncode == 0
                
        except Exception:
            return False
    
    @staticmethod
    def create_metallb_config() -> bool:
        """Skapa MetalLB-konfiguration"""
        try:
            print("🔧 Skapar MetalLB-konfiguration...")
            
            # Kontrollera om konfigurationsfil finns
            config_file = "../k8s/metallb-config.yaml"
            if not os.path.exists(config_file):
                print(f"❌ MetalLB-konfigurationsfil finns inte: {config_file}")
                return False
            
            # Applicera konfiguration
            apply_result = subprocess.run(
                ["kubectl", "apply", "-f", config_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if apply_result.returncode == 0:
                print("✅ MetalLB-konfiguration skapad")
                return True
            else:
                print(f"❌ Kunde inte skapa MetalLB-konfiguration: {apply_result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Kunde inte skapa MetalLB-konfiguration: {e}")
            return False


class LoadBalancerSupport:
    """Support-klass för LoadBalancer-tester"""
    
    @staticmethod
    def get_loadbalancer_services() -> list:
        """Hämta alla LoadBalancer services"""
        try:
            result = subprocess.run(
                ["kubectl", "get", "svc", "-n", "kamailio", "-o", "json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                services_data = json.loads(result.stdout)
                services = services_data.get("items", [])
                
                loadbalancer_services = []
                for service in services:
                    spec = service.get("spec", {})
                    service_type = spec.get("type")
                    if service_type == "LoadBalancer":
                        service_name = service["metadata"]["name"]
                        loadbalancer_services.append(service_name)
                
                return loadbalancer_services
            
            return []
                
        except Exception:
            return []
    
    @staticmethod
    def get_loadbalancer_ip(service_name: str) -> Optional[str]:
        """Hämta extern IP för LoadBalancer service"""
        try:
            ip_result = subprocess.run(
                ["kubectl", "get", "svc", service_name, "-n", "kamailio", "-o", "jsonpath={.status.loadBalancer.ingress[0].ip}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if ip_result.returncode == 0 and ip_result.stdout.strip():
                return ip_result.stdout.strip()
            
            return None
                
        except Exception:
            return None
    
    @staticmethod
    def get_loadbalancer_port(service_name: str) -> Optional[int]:
        """Hämta port för LoadBalancer service"""
        try:
            port_result = subprocess.run(
                ["kubectl", "get", "svc", service_name, "-n", "kamailio", "-o", "jsonpath={.spec.ports[0].port}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if port_result.returncode == 0 and port_result.stdout.strip():
                return int(port_result.stdout.strip())
            
            return None
                
        except Exception:
            return None
    
    @staticmethod
    def test_loadbalancer_connectivity(service_name: str) -> Tuple[bool, str]:
        """Testa anslutning till LoadBalancer"""
        try:
            external_ip = LoadBalancerSupport.get_loadbalancer_ip(service_name)
            port = LoadBalancerSupport.get_loadbalancer_port(service_name)
            
            if not external_ip or not port:
                return False, f"Kunde inte hämta IP eller port för {service_name}"
            
            print(f"🔍 Testar anslutning till LoadBalancer {service_name}: {external_ip}:{port}")
            
            # Testa UDP-anslutning
            if NetworkUtils.test_udp_connection(external_ip, port):
                return True, f"✅ LoadBalancer {service_name} tillgänglig via UDP: {external_ip}:{port}"
            else:
                return False, f"❌ LoadBalancer {service_name} inte tillgänglig via UDP: {external_ip}:{port}"
                
        except Exception as e:
            return False, f"❌ Kunde inte testa LoadBalancer-anslutning: {e}"


class SippTestSupport:
    """Support-klass för SIPp-tester"""
    
    @staticmethod
    def create_sipp_tester(environment: str) -> SippTester:
        """Skapa SippTester-instans"""
        return SippTester(
            kamailio_host="localhost",
            kamailio_port=5060,
            timeout=30,
            environment=environment
        )
    
    @staticmethod
    def ensure_environment_ready() -> Dict[str, bool]:
        """Kontrollera att miljön är redo för SIPp-tester"""
        env_status = get_environment_status()
        
        # Kontrollera kritiska komponenter för SIPp-tester
        # Ändra från "sipp_installed" till "sipp_container" eftersom SIPp är i Docker
        critical_checks = ["docker", "sipp_image", "sipp_container", "sipp_scenarios"]
        missing_critical = [check for check in critical_checks if not env_status.get(check, False)]
        
        if missing_critical:
            pytest.skip(f"Kritiska komponenter för SIPp-tester saknas: {', '.join(missing_critical)}")
        
        return env_status
    
    @staticmethod
    def ensure_kamailio_ready() -> Dict[str, bool]:
        """Kontrollera att Kamailio är redo"""
        env_status = get_environment_status()
        
        print(f"🔍 Kamailio readiness check:")
        for check, status in env_status.items():
            print(f"  {check}: {status}")
        
        # Kontrollera kritiska komponenter för Kamailio-tester
        critical_checks = ["docker", "kubernetes_cluster", "kamailio_namespace", "kamailio_deployment", "kamailio_pods", "kamailio_service"]
        missing_critical = [check for check in critical_checks if not env_status.get(check, False)]
        
        if missing_critical:
            print(f"❌ Saknade kritiska komponenter: {', '.join(missing_critical)}")
            pytest.skip(f"Kritiska komponenter för Kamailio-tester saknas: {', '.join(missing_critical)}")
        
        print(f"✅ Alla kritiska komponenter finns")
        return env_status
    
    @staticmethod
    def start_port_forward() -> subprocess.Popen:
        """Starta port-forward för Kamailio"""
        try:
            # För Kind-kluster använder vi NodePort istället för port-forward
            # Kontrollera om vi kör i Kind-kluster
            result = subprocess.run(
                ["kubectl", "get", "nodes", "-o", "jsonpath={.items[0].metadata.name}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and "sipp-k8s-lab" in result.stdout:
                print("🔍 Kind-kluster detekterat, använder NodePort istället för port-forward")
                # Returnera en dummy-process för Kind-kluster
                class DummyProcess:
                    def poll(self): return None
                    def terminate(self): pass
                    def wait(self): pass
                return DummyProcess()
            
            # För andra kluster, använd port-forward
            print("🔍 Använder port-forward för Kamailio")
            process = subprocess.Popen(
                ["kubectl", "port-forward", "svc/kamailio-service", "5060:5060", "-n", "kamailio"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Vänta lite för att port-forward ska starta
            time.sleep(2)
            
            if process.poll() is None:
                return process
            else:
                pytest.skip("Kunde inte starta port-forward för Kamailio")
        except Exception as e:
            pytest.skip(f"Kunde inte starta port-forward: {e}")
    
    @staticmethod
    def create_sipp_tester_with_kamailio(environment: str) -> SippTester:
        """Skapa SippTester-instans för Kamailio-tester"""
        return SippTester(
            kamailio_host="localhost",
            kamailio_port=5060,
            timeout=30,
            environment=environment
        ) 


class NetworkRoutingSupport:
    """Support för nätverksrouting-tester"""
    
    @staticmethod
    def test_loadbalancer_connectivity() -> Tuple[bool, str]:
        """Testa LoadBalancer-anslutning"""
        try:
            # Testa UDP-anslutning till LoadBalancer
            result = subprocess.run(
                ["nc", "-zu", "172.18.0.242", "5060"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True, "LoadBalancer UDP-anslutning fungerar"
            else:
                return False, f"LoadBalancer UDP-anslutning misslyckades: {result.stderr}"
        except Exception as e:
            return False, f"LoadBalancer-test fel: {str(e)}"
    
    @staticmethod
    def test_nodeport_connectivity() -> Tuple[bool, str]:
        """Testa NodePort-anslutning"""
        try:
            # Testa UDP-anslutning till NodePort
            result = subprocess.run(
                ["nc", "-zu", "172.18.0.2", "30600"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True, "NodePort UDP-anslutning fungerar"
            else:
                return False, f"NodePort UDP-anslutning misslyckades: {result.stderr}"
        except Exception as e:
            return False, f"NodePort-test fel: {str(e)}"
    
    @staticmethod
    def test_kamailio_pod_connectivity() -> Tuple[bool, str]:
        """Testa direkt anslutning till Kamailio-pods"""
        try:
            # Hämta pod-IP:er
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", "kamailio", "-o", "jsonpath={.items[*].status.podIP}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                return False, "Kunde inte hämta pod-IP:er"
            
            pod_ips = result.stdout.strip().split()
            if not pod_ips:
                return False, "Inga Kamailio-pods hittades"
            
            # Testa anslutning till första pod
            test_ip = pod_ips[0]
            result = subprocess.run(
                ["nc", "-zu", test_ip, "5060"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True, f"Pod-anslutning fungerar till {test_ip}"
            else:
                return False, f"Pod-anslutning misslyckades till {test_ip}: {result.stderr}"
        except Exception as e:
            return False, f"Pod-connectivity test fel: {str(e)}"
    
    @staticmethod
    def test_sipp_to_kamailio_routing() -> Tuple[bool, str]:
        """Testa routing från SIPp till Kamailio"""
        try:
            # Skicka SIP OPTIONS via NodePort (bättre för Kind-kluster)
            sip_message = (
                "OPTIONS sip:kamailio.local SIP/2.0\r\n"
                "Via: SIP/2.0/UDP 172.18.0.2:30600\r\n"
                "From: <sip:test@kamailio.local>\r\n"
                "To: <sip:kamailio.local>\r\n"
                "Call-ID: test-123\r\n"
                "CSeq: 1 OPTIONS\r\n"
                "Contact: <sip:test@172.18.0.2:30600>\r\n"
                "Content-Length: 0\r\n\r\n"
            )
            
            # Skicka meddelande med timeout
            process = subprocess.Popen(
                ["nc", "-u", "172.18.0.2", "30600"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                stdout, stderr = process.communicate(input=sip_message, timeout=3)
                if process.returncode == 0:
                    return True, "SIP-meddelande skickades framgångsrikt via NodePort"
                else:
                    return False, f"SIP-meddelande misslyckades: {stderr}"
            except subprocess.TimeoutExpired:
                process.kill()
                return False, "SIP-meddelande timeout - ingen respons"
                
        except Exception as e:
            return False, f"SIP-routing test fel: {str(e)}"
    
    @staticmethod
    def get_network_status() -> Dict[str, bool]:
        """Hämta nätverksstatus för alla komponenter"""
        status = {}
        
        # Testa LoadBalancer
        success, msg = NetworkRoutingSupport.test_loadbalancer_connectivity()
        status["loadbalancer_connectivity"] = success
        
        # Testa NodePort
        success, msg = NetworkRoutingSupport.test_nodeport_connectivity()
        status["nodeport_connectivity"] = success
        
        # Testa Pod-connectivity
        success, msg = NetworkRoutingSupport.test_kamailio_pod_connectivity()
        status["pod_connectivity"] = success
        
        # Testa SIP-routing
        success, msg = NetworkRoutingSupport.test_sipp_to_kamailio_routing()
        status["sip_routing"] = success
        
        return status 

    @staticmethod
    def fix_loadbalancer_routing() -> Tuple[bool, str]:
        """Försök fixa LoadBalancer-routing-problemet"""
        try:
            # Kontrollera om LoadBalancer har rätt endpoints
            result = subprocess.run(
                ["kubectl", "get", "endpoints", "kamailio-loadbalancer", "-n", "kamailio", "-o", "jsonpath={.subsets[0].addresses[*].ip}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0 or not result.stdout.strip():
                return False, "LoadBalancer har inga endpoints"
            
            # Kontrollera om pods körs
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", "kamailio", "-l", "app=kamailio", "--field-selector=status.phase=Running", "-o", "jsonpath={.items[*].status.podIP}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0 or not result.stdout.strip():
                return False, "Inga Kamailio-pods körs"
            
            # Försök restarta LoadBalancer service
            result = subprocess.run(
                ["kubectl", "delete", "svc", "kamailio-loadbalancer", "-n", "kamailio"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Skapa service igen
            result = subprocess.run(
                ["kubectl", "apply", "-f", "../k8s/service.yaml"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return True, "LoadBalancer service restarted"
            else:
                return False, f"Kunde inte restarta LoadBalancer: {result.stderr}"
                
        except Exception as e:
            return False, f"LoadBalancer fix fel: {str(e)}" 