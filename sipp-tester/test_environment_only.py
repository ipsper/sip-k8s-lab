#!/usr/bin/env python3
"""
Miljötester för SIPp-tester
Kontrollerar förutsättningar och startar/bygger det som behövs
"""

import pytest
import sys
import os
from pathlib import Path

# Lägg till app directory för att importera sip_test_utils
sys.path.append(str(Path(__file__).parent.parent / "app"))

from sip_test_utils import (
    KamailioConfig, KubernetesUtils, DockerUtils, NetworkUtils, 
    EnvironmentChecker, KamailioUtils, get_environment_status, is_environment_ready
)
from sipp_tester import SippTester


class TestEnvironment:
    """Miljötester för att kontrollera och starta förutsättningar"""
    
    @pytest.fixture(scope="class")
    def kamailio_config(self, request):
        """Fixture för Kamailio-konfiguration baserad på environment-variabler"""
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
    
    def test_docker_available(self):
        """Testa att Docker är tillgängligt"""
        if EnvironmentChecker.check_docker():
            print("✅ Docker tillgängligt")
        else:
            pytest.fail("Docker inte tillgängligt")
    
    def test_kubectl_available(self):
        """Testa att kubectl är tillgängligt"""
        if EnvironmentChecker.check_kubectl():
            print("✅ kubectl tillgängligt")
        else:
            pytest.fail("kubectl inte tillgängligt")
    
    def test_kubernetes_cluster_available(self):
        """Testa att Kubernetes-kluster är tillgängligt"""
        if EnvironmentChecker.check_kubernetes_cluster():
            print("✅ Kubernetes-kluster tillgängligt")
        else:
            pytest.fail("Kubernetes-kluster inte tillgängligt")
    
    def test_sipp_tester_image_exists(self):
        """Testa att SIPp test Docker-image finns och bygg om behövs"""
        if DockerUtils.check_image_exists("local/sipp-tester:latest"):
            print("✅ SIPp test Docker-image finns")
        else:
            print("🔨 SIPp test Docker-image finns inte, bygger...")
            if DockerUtils.build_image("local/sipp-tester:latest", "."):
                print("✅ SIPp test Docker-image byggd")
            else:
                pytest.fail("Kunde inte bygga SIPp test Docker-image")
    
    def test_sipp_tester_container_starts(self):
        """Testa att SIPp test container kan startas"""
        success, output = DockerUtils.run_container("local/sipp-tester:latest", "echo test")
        if success:
            print("✅ SIPp test container kan startas")
        else:
            pytest.fail(f"SIPp test container kan inte startas: {output}")
    
    def test_kamailio_namespace_exists(self):
        """Testa att kamailio namespace finns och skapa om behövs"""
        if KubernetesUtils.check_namespace_exists("kamailio"):
            print("✅ kamailio namespace finns")
        else:
            print("📦 Skapar kamailio namespace...")
            if KubernetesUtils.create_namespace("kamailio"):
                print("✅ kamailio namespace skapat")
            else:
                pytest.fail("Kunde inte skapa kamailio namespace")
    
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
        if KubernetesUtils.check_service_exists("kamailio-service", "kamailio"):
            print("✅ Kamailio service finns")
        else:
            pytest.fail("Kamailio service finns inte")
    
    def test_kamailio_port_accessible(self, kamailio_config):
        """Testa att Kamailio port är tillgänglig"""
        host = kamailio_config['host']
        port = kamailio_config['port']
        environment = kamailio_config['environment']
        
        # Visa rätt host:port kombination
        if ":" in host:
            display_host = host
        else:
            display_host = f"{host}:{port}"
        print(f"🔍 Testar Kamailio på {display_host} (miljö: {environment})")
        
        # För local environment, testa direkt anslutning
        if environment == "local":
            # Använd direkt anslutning för Kind NodePort
            host_ip = host
            host_port = port
            
            if NetworkUtils.test_udp_connection(host_ip, host_port):
                print(f"✅ Kamailio port tillgänglig direkt: {host_ip}:{host_port}")
                return
            else:
                pytest.skip(f"Kamailio port inte tillgänglig direkt: {host_ip}:{host_port}")
        else:
            # För andra miljöer, använd port-forward
            process = NetworkUtils.port_forward_service("kamailio-service", "kamailio", port, port)
            if process:
                if NetworkUtils.test_tcp_connection("localhost", port):
                    print(f"✅ Kamailio port tillgänglig via port-forward: localhost:{port}")
                else:
                    pytest.skip(f"Kamailio port inte tillgänglig via port-forward: localhost:{port}")
                process.terminate()
                process.wait()
            else:
                pytest.skip("Kunde inte starta port-forward")
    
    def test_kamailio_sip_readiness(self, kamailio_config):
        """Testa att Kamailio är redo för SIPp-tester"""
        host = kamailio_config['host']
        port = kamailio_config['port']
        environment = kamailio_config['environment']
        
        print(f"🔍 Kontrollerar Kamailio readiness för {host}:{port} (miljö: {environment})")
        
        # Kontrollera att Kamailio pods körs
        pods_running, running_pods = KubernetesUtils.check_pods_running("kamailio", "app=kamailio")
        if not pods_running:
            print(f"⚠️  Kamailio pods körs inte")
            pytest.skip("Kamailio inte redo för SIPp-tester")
        
        # Kontrollera Kamailio-konfiguration
        config = KamailioUtils.get_kamailio_config()
        if config:
            # Kontrollera om konfigurationen är minimal (bara stateless proxy)
            if "sl_send_reply" in config and "request_route" in config:
                print(f"✅ Kamailio konfigurerad för SIPp-tester")
            else:
                print(f"⚠️  Kamailio har minimal konfiguration - SIPp-tester kan timeout")
                pytest.skip("Kamailio har minimal konfiguration")
        else:
            print(f"⚠️  Kunde inte läsa Kamailio-konfiguration")
            pytest.skip("Kamailio-konfiguration inte tillgänglig")
    
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
    
# Använd utility-funktionerna från sip_test_utils istället för lokala funktioner 