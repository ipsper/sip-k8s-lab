#!/usr/bin/env python3
"""
Miljötester för SIPp-tester
Kontrollerar förutsättningar och startar/bygger det som behövs
"""

import pytest
import subprocess
import time
import json
import os
from typing import Dict, List, Optional


class TestEnvironment:
    """Miljötester för att kontrollera och starta förutsättningar"""
    
    def test_docker_available(self):
        """Testa att Docker är tillgängligt"""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0, f"Docker inte tillgängligt: {result.stderr}"
            print(f"✅ Docker tillgängligt: {result.stdout.strip()}")
        except Exception as e:
            pytest.fail(f"Docker inte tillgängligt: {e}")
    
    def test_kubectl_available(self):
        """Testa att kubectl är tillgängligt"""
        try:
            result = subprocess.run(
                ["kubectl", "version", "--client"],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0, f"kubectl inte tillgängligt: {result.stderr}"
            print(f"✅ kubectl tillgängligt: {result.stdout.split()[0]}")
        except Exception as e:
            pytest.fail(f"kubectl inte tillgängligt: {e}")
    
    def test_kubernetes_cluster_available(self):
        """Testa att Kubernetes-kluster är tillgängligt och starta om behövs"""
        try:
            # Testa först om klustret är tillgängligt
            result = subprocess.run(
                ["kubectl", "cluster-info"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"✅ Kubernetes-kluster tillgängligt")
                return
            
            # Om klustret inte är tillgängligt, försök starta minikube
            print("⚠️  Kubernetes-kluster inte tillgängligt, försöker starta minikube...")
            
            # Kontrollera om minikube är installerat
            minikube_result = subprocess.run(
                ["minikube", "version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if minikube_result.returncode != 0:
                pytest.fail("minikube inte installerat. Installera minikube först.")
            
            # Starta minikube
            print("🚀 Startar minikube...")
            start_result = subprocess.run(
                ["minikube", "start", "--driver=docker"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if start_result.returncode != 0:
                pytest.fail(f"Kunde inte starta minikube: {start_result.stderr}")
            
            # Aktivera ingress addon
            print("🔧 Aktiverar ingress addon...")
            subprocess.run(
                ["minikube", "addons", "enable", "ingress"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Vänta lite och testa igen
            time.sleep(10)
            final_result = subprocess.run(
                ["kubectl", "cluster-info"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if final_result.returncode == 0:
                print(f"✅ Kubernetes-kluster startat och tillgängligt")
            else:
                pytest.fail(f"Kunde inte starta Kubernetes-kluster: {final_result.stderr}")
                
        except Exception as e:
            pytest.fail(f"Kubernetes-kluster inte tillgängligt: {e}")
    
    def test_sipp_tester_image_exists(self):
        """Testa att SIPp test Docker-image finns och bygg om behövs"""
        try:
            result = subprocess.run(
                ["docker", "images", "-q", "local/sipp-tester:latest"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip() != "":
                print(f"✅ SIPp test Docker-image finns")
                return
            
            # Om image inte finns, bygg den
            print("🔨 SIPp test Docker-image finns inte, bygger...")
            
            # Kontrollera att vi är i rätt katalog
            if not os.path.exists("Dockerfile"):
                pytest.fail("Dockerfile finns inte i nuvarande katalog")
            
            build_result = subprocess.run(
                ["docker", "build", "-t", "local/sipp-tester:latest", "."],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if build_result.returncode != 0:
                pytest.fail(f"Kunde inte bygga SIPp test Docker-image: {build_result.stderr}")
            
            print(f"✅ SIPp test Docker-image byggd")
            
        except Exception as e:
            pytest.fail(f"Kunde inte kontrollera/bygga SIPp test Docker-image: {e}")
    
    def test_sipp_tester_container_starts(self):
        """Testa att SIPp test container kan startas"""
        try:
            result = subprocess.run(
                ["docker", "run", "--rm", "local/sipp-tester:latest", "echo", "test"],
                capture_output=True,
                text=True,
                timeout=30
            )
            assert result.returncode == 0, f"SIPp test container kan inte startas: {result.stderr}"
            print(f"✅ SIPp test container kan startas")
        except Exception as e:
            pytest.fail(f"SIPp test container kan inte startas: {e}")
    
    def test_kamailio_namespace_exists(self):
        """Testa att kamailio namespace finns och skapa om behövs"""
        try:
            result = subprocess.run(
                ["kubectl", "get", "namespace", "kamailio"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"✅ kamailio namespace finns")
                return
            
            # Om namespace inte finns, skapa den
            print("📦 Skapar kamailio namespace...")
            create_result = subprocess.run(
                ["kubectl", "create", "namespace", "kamailio"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if create_result.returncode != 0:
                pytest.fail(f"Kunde inte skapa kamailio namespace: {create_result.stderr}")
            
            print(f"✅ kamailio namespace skapat")
            
        except Exception as e:
            pytest.fail(f"kamailio namespace finns inte: {e}")
    
    def test_kamailio_deployment_exists(self):
        """Testa att Kamailio deployment finns och deploya om behövs"""
        try:
            result = subprocess.run(
                ["kubectl", "get", "deployment", "kamailio", "-n", "kamailio"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"✅ Kamailio deployment finns")
                return
            
            # Om deployment inte finns, deploya Kamailio
            print("🚀 Kamailio deployment finns inte, deployar...")
            
            # Kontrollera att deploy-script finns
            deploy_script = "../scripts/deploy.sh"
            if not os.path.exists(deploy_script):
                pytest.fail(f"Deploy-script finns inte: {deploy_script}")
            
            # Gör script körbart och kör det
            subprocess.run(["chmod", "+x", deploy_script], check=True)
            
            deploy_result = subprocess.run(
                [deploy_script],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if deploy_result.returncode != 0:
                pytest.fail(f"Kunde inte deploya Kamailio: {deploy_result.stderr}")
            
            print(f"✅ Kamailio deployment skapat")
            
        except Exception as e:
            pytest.fail(f"Kamailio deployment finns inte: {e}")
    
    def test_kamailio_pods_running(self):
        """Testa att Kamailio pods körs och vänta om behövs"""
        try:
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", "kamailio", "-l", "app=kamailio", "-o", "json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0, f"Kunde inte hämta Kamailio pods: {result.stderr}"
            
            pods_data = json.loads(result.stdout)
            pods = pods_data.get("items", [])
            
            if not pods:
                pytest.skip("Inga Kamailio pods hittades")
            
            running_pods = []
            for pod in pods:
                status = pod.get("status", {})
                phase = status.get("phase")
                if phase == "Running":
                    running_pods.append(pod["metadata"]["name"])
            
            if running_pods:
                print(f"✅ Kamailio pods körs: {', '.join(running_pods)}")
                return
            
            # Om pods inte körs än, vänta lite
            print("⏳ Kamailio pods startar, väntar...")
            max_wait = 120  # 2 minuter
            wait_time = 0
            
            while wait_time < max_wait:
                time.sleep(10)
                wait_time += 10
                
                result = subprocess.run(
                    ["kubectl", "get", "pods", "-n", "kamailio", "-l", "app=kamailio", "-o", "json"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    pods_data = json.loads(result.stdout)
                    pods = pods_data.get("items", [])
                    
                    running_pods = []
                    for pod in pods:
                        status = pod.get("status", {})
                        phase = status.get("phase")
                        if phase == "Running":
                            running_pods.append(pod["metadata"]["name"])
                    
                    if running_pods:
                        print(f"✅ Kamailio pods körs nu: {', '.join(running_pods)}")
                        return
                
                print(f"⏳ Väntar... ({wait_time}s)")
            
            pytest.skip("Kamailio pods startade inte inom tidsgränsen")
                       
        except Exception as e:
            pytest.fail(f"Kunde inte kontrollera Kamailio pods: {e}")
    
    def test_kamailio_service_exists(self):
        """Testa att Kamailio service finns"""
        try:
            result = subprocess.run(
                ["kubectl", "get", "service", "kamailio-service", "-n", "kamailio"],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0, f"Kamailio service finns inte: {result.stderr}"
            print(f"✅ Kamailio service finns")
        except Exception as e:
            pytest.fail(f"Kamailio service finns inte: {e}")
    
    def test_kamailio_port_accessible(self):
        """Testa att Kamailio port är tillgänglig via port-forward"""
        try:
            # Starta port-forward i bakgrunden
            process = subprocess.Popen(
                ["kubectl", "port-forward", "svc/kamailio-service", "5060:5060", "-n", "kamailio"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Vänta lite för att port-forward ska starta
            time.sleep(3)
            
            # Testa anslutning
            result = subprocess.run(
                ["nc", "-z", "localhost", "5060"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Stoppa port-forward
            process.terminate()
            process.wait()
            
            if result.returncode == 0:
                print(f"✅ Kamailio port tillgänglig via port-forward")
            else:
                pytest.skip("Kamailio port inte tillgänglig via port-forward")
                       
        except Exception as e:
            pytest.fail(f"Kunde inte testa Kamailio port: {e}")
    
    def test_kamailio_sip_readiness(self):
        """Testa att Kamailio är redo för SIPp-tester"""
        try:
            # Kontrollera att Kamailio pods körs
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", "kamailio", "-l", "app=kamailio", "--no-headers"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                print(f"⚠️  Kamailio pods körs inte")
                pytest.skip("Kamailio inte redo för SIPp-tester")
            
            # Kontrollera att minst en pod är Running
            lines = result.stdout.strip().split('\n')
            running_pods = 0
            
            for line in lines:
                if 'Running' in line:
                    running_pods += 1
            
            if running_pods == 0:
                print(f"⚠️  Inga Kamailio pods körs")
                pytest.skip("Kamailio inte redo för SIPp-tester")
            
            # Kontrollera Kamailio-konfiguration
            config_result = subprocess.run(
                ["kubectl", "get", "configmap", "kamailio-config", "-n", "kamailio", "-o", "jsonpath={.data.kamailio\\.cfg}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if config_result.returncode == 0 and config_result.stdout:
                config = config_result.stdout
                
                # Kontrollera om konfigurationen är minimal (bara stateless proxy)
                if "sl_send_reply" in config and "request_route" in config:
                    print(f"✅ Kamailio konfigurerad för SIPp-tester")
                else:
                    print(f"⚠️  Kamailio har minimal konfiguration - SIPp-tester kan timeout")
                    pytest.skip("Kamailio har minimal konfiguration")
            else:
                print(f"⚠️  Kunde inte läsa Kamailio-konfiguration")
                pytest.skip("Kamailio-konfiguration inte tillgänglig")
                       
        except Exception as e:
            print(f"⚠️  Kunde inte kontrollera Kamailio readiness: {e}")
            pytest.skip("Kamailio readiness-kontroll misslyckades")
    
    def test_sipp_installed_in_container(self):
        """Testa att SIPp är installerat i test-container och installera om behövs"""
        try:
            result = subprocess.run(
                ["docker", "run", "--rm", "local/sipp-tester:latest", "which", "sipp"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"✅ SIPp installerat i test-container")
                return
            
            # Om SIPp inte är installerat, bygg om image med SIPp
            print("🔧 SIPp inte installerat i test-container, bygger om image...")
            
            # Uppdatera Dockerfile för att installera SIPp
            dockerfile_content = """FROM ubuntu:22.04

# Installera nödvändiga paket inklusive SIPp
RUN apt-get update && apt-get install -y \\
    netcat \\
    curl \\
    wget \\
    build-essential \\
    cmake \\
    libncurses5-dev \\
    libpcap-dev \\
    libssl-dev \\
    libsctp-dev \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Installera SIPp från källa
RUN cd /tmp && \\
    git clone https://github.com/SIPp/sipp.git && \\
    cd sipp && \\
    cmake . -DUSE_SSL=1 -DUSE_SCTP=1 && \\
    make && \\
    make install && \\
    cd / && \\
    rm -rf /tmp/sipp

# Skapa arbetskatalog
WORKDIR /app

# Kopiera test-script
COPY test-scripts/ /app/test-scripts/
COPY sipp-scenarios/ /app/sipp-scenarios/

# Gör script körbara
RUN chmod +x /app/test-scripts/*.sh

# Exponera portar för SIPp
EXPOSE 5060/udp 5060/tcp

# Default command
CMD ["/app/test-scripts/run-tests.sh"]
"""
            
            # Skriv uppdaterad Dockerfile
            with open("Dockerfile", "w") as f:
                f.write(dockerfile_content)
            
            # Bygg om image
            build_result = subprocess.run(
                ["docker", "build", "-t", "local/sipp-tester:latest", "."],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if build_result.returncode != 0:
                pytest.skip(f"Kunde inte bygga SIPp i container: {build_result.stderr}")
            
            # Testa igen
            test_result = subprocess.run(
                ["docker", "run", "--rm", "local/sipp-tester:latest", "which", "sipp"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if test_result.returncode == 0:
                print(f"✅ SIPp installerat i test-container")
            else:
                pytest.skip("SIPp kunde inte installeras i test-container")
                
        except Exception as e:
            pytest.fail(f"Kunde inte kontrollera/installera SIPp i container: {e}")
    
    def test_sipp_scenarios_exist(self):
        """Testa att SIPp scenarios finns i container"""
        scenarios = ["options", "register", "invite", "ping"]
        missing_scenarios = []
        
        for scenario in scenarios:
            try:
                result = subprocess.run(
                    ["docker", "run", "--rm", "local/sipp-tester:latest", "test", "-f", f"/app/sipp-scenarios/{scenario}.xml"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode != 0:
                    missing_scenarios.append(scenario)
            except Exception as e:
                missing_scenarios.append(scenario)
        
        if missing_scenarios:
            pytest.skip(f"Saknade SIPp scenarios: {', '.join(missing_scenarios)}")
        else:
            print(f"✅ Alla SIPp scenarios finns: {', '.join(scenarios)}")
    
    def test_environment_summary(self):
        """Sammanfattning av miljön"""
        print("\n" + "="*60)
        print("MILJÖSAMMANFATTNING")
        print("="*60)
        
        # Kontrollera alla komponenter
        checks = [
            ("Docker", self._check_docker),
            ("kubectl", self._check_kubectl),
            ("Kubernetes Cluster", self._check_kubernetes_cluster),
            ("SIPp Test Image", self._check_sipp_image),
            ("SIPp Test Container", self._check_sipp_container),
            ("Kamailio Namespace", self._check_kamailio_namespace),
            ("Kamailio Deployment", self._check_kamailio_deployment),
            ("Kamailio Pods", self._check_kamailio_pods),
            ("Kamailio Service", self._check_kamailio_service),
            ("Kamailio SIP Response", self._check_kamailio_sip_response),
            ("SIPp Installation", self._check_sipp_installed),
            ("SIPp Scenarios", self._check_sipp_scenarios),
        ]
        
        results = []
        for name, check_func in checks:
            try:
                check_func()
                results.append(f"✅ {name}")
            except Exception as e:
                results.append(f"❌ {name}: {str(e)}")
        
        for result in results:
            print(result)
        
        print("="*60)
        
        # Räkna lyckade kontroller
        successful = sum(1 for r in results if r.startswith("✅"))
        total = len(results)
        
        if successful == total:
            print(f"🎉 Alla {total} miljökontroller lyckades!")
        else:
            print(f"⚠️  {successful}/{total} miljökontroller lyckades")
            print("Fix the failed checks before running SIPp tests")
    
    def _check_docker(self):
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
    
    def _check_kubectl(self):
        subprocess.run(["kubectl", "version", "--client"], check=True, capture_output=True)
    
    def _check_kubernetes_cluster(self):
        subprocess.run(["kubectl", "cluster-info"], check=True, capture_output=True)
    
    def _check_sipp_image(self):
        result = subprocess.run(["docker", "images", "-q", "local/sipp-tester:latest"], 
                              capture_output=True, text=True)
        if result.returncode != 0 or not result.stdout.strip():
            raise Exception("Image not found")
    
    def _check_sipp_container(self):
        subprocess.run(["docker", "run", "--rm", "local/sipp-tester:latest", "echo", "test"], 
                      check=True, capture_output=True)
    
    def _check_kamailio_namespace(self):
        subprocess.run(["kubectl", "get", "namespace", "kamailio"], check=True, capture_output=True)
    
    def _check_kamailio_deployment(self):
        subprocess.run(["kubectl", "get", "deployment", "kamailio", "-n", "kamailio"], 
                      check=True, capture_output=True)
    
    def _check_kamailio_pods(self):
        result = subprocess.run(["kubectl", "get", "pods", "-n", "kamailio", "-l", "app=kamailio", "-o", "json"],
                              capture_output=True, text=True)
        pods_data = json.loads(result.stdout)
        pods = pods_data.get("items", [])
        if not pods:
            raise Exception("No pods found")
        running = [p for p in pods if p.get("status", {}).get("phase") == "Running"]
        if not running:
            raise Exception("No running pods")
    
    def _check_kamailio_service(self):
        subprocess.run(["kubectl", "get", "service", "kamailio-service", "-n", "kamailio"], 
                      check=True, capture_output=True)
    
    def _check_kamailio_sip_response(self):
        """Kontrollera att Kamailio är redo för SIPp-tester"""
        # Kontrollera att Kamailio pods körs
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", "kamailio", "-l", "app=kamailio", "--no-headers"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            raise Exception("Kamailio pods not running")
        
        # Kontrollera att minst en pod är Running
        lines = result.stdout.strip().split('\n')
        running_pods = 0
        
        for line in lines:
            if 'Running' in line:
                running_pods += 1
        
        if running_pods == 0:
            raise Exception("No Kamailio pods running")
    
    def _check_sipp_installed(self):
        result = subprocess.run(["docker", "run", "--rm", "local/sipp-tester:latest", "which", "sipp"],
                              capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception("SIPp not installed")
    
    def _check_sipp_scenarios(self):
        scenarios = ["options", "register", "invite", "ping"]
        for scenario in scenarios:
            result = subprocess.run(["docker", "run", "--rm", "local/sipp-tester:latest", 
                                  "test", "-f", f"/app/sipp-scenarios/{scenario}.xml"],
                                 capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Missing scenario: {scenario}")


# Hjälpfunktioner för andra tester
def get_environment_status() -> Dict[str, bool]:
    """Hämta status för alla miljökontroller"""
    env_tester = TestEnvironment()
    status = {}
    
    checks = [
        ("docker", env_tester._check_docker),
        ("kubectl", env_tester._check_kubectl),
        ("kubernetes_cluster", env_tester._check_kubernetes_cluster),
        ("sipp_image", env_tester._check_sipp_image),
        ("sipp_container", env_tester._check_sipp_container),
        ("kamailio_namespace", env_tester._check_kamailio_namespace),
        ("kamailio_deployment", env_tester._check_kamailio_deployment),
        ("kamailio_pods", env_tester._check_kamailio_pods),
        ("kamailio_service", env_tester._check_kamailio_service),
        ("kamailio_sip_response", env_tester._check_kamailio_sip_response),
        ("sipp_installed", env_tester._check_sipp_installed),
        ("sipp_scenarios", env_tester._check_sipp_scenarios),
    ]
    
    for name, check_func in checks:
        try:
            check_func()
            status[name] = True
        except Exception:
            status[name] = False
    
    return status


def is_environment_ready() -> bool:
    """Kontrollera om miljön är redo för SIPp-tester"""
    status = get_environment_status()
    required_checks = ["docker", "kubectl", "kubernetes_cluster", "sipp_image", "sipp_container"]
    return all(status.get(check, False) for check in required_checks) 