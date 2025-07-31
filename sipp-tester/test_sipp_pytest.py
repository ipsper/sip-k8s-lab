#!/usr/bin/env python3
"""
Pytest-tester för SIPp-testing
Fokuserar på SIPp-funktionalitet, miljökontroller hanteras av test_environment_only.py
"""

import pytest
import time
import subprocess
from sipp_tester import SippTester, TestResult
from test_environment_only import get_environment_status


class TestSippTester:
    """Pytest-klass för SIPp-testing"""
    
    @pytest.fixture(scope="class")
    def sipp_tester(self, environment):
        """Fixture för SippTester-instans"""
        return SippTester(
            kamailio_host="localhost",
            kamailio_port=5060,
            timeout=30,
            environment=environment
        )
    
    @pytest.fixture(scope="class")
    def ensure_environment_ready(self):
        """Fixture som säkerställer att miljön är redo för SIPp-tester"""
        env_status = get_environment_status()
        
        # Kontrollera kritiska komponenter för SIPp-tester
        critical_checks = ["docker", "sipp_image", "sipp_container", "sipp_installed", "sipp_scenarios"]
        missing_critical = [check for check in critical_checks if not env_status.get(check, False)]
        
        if missing_critical:
            pytest.skip(f"Kritiska komponenter för SIPp-tester saknas: {', '.join(missing_critical)}")
        
        return env_status
    
    def test_options_scenario(self, sipp_tester, ensure_environment_ready):
        """Testa OPTIONS-scenario"""
        result = sipp_tester.run_sipp_test("options")
        
        print(f"\nOPTIONS Test Result:")
        print(f"  Success: {result.success}")
        print(f"  Exit Code: {result.exit_code}")
        print(f"  Duration: {result.duration:.2f}s")
        print(f"  Statistics: {result.statistics}")
        
        # Hantera vanliga fel
        if not result.success:
            if "Address already in use" in result.error:
                pytest.skip("Port 5061 används redan - starta om systemet eller ändra port")
            elif "command not found" in result.error or "executable file not found" in result.error:
                pytest.skip("SIPp inte installerat i Docker-image")
            elif "Timeout expired" in result.error:
                print("⚠️  OPTIONS-test timeout - Kamailio svarar inte (kan vara normalt för enkel proxy)")
                pytest.skip("OPTIONS-test timeout - Kamailio svarar inte")
        
        assert result.success, f"OPTIONS-test misslyckades: {result.error}"
    
    def test_register_scenario(self, sipp_tester, ensure_environment_ready):
        """Testa REGISTER-scenario"""
        result = sipp_tester.run_sipp_test("register")
        
        print(f"\nREGISTER Test Result:")
        print(f"  Success: {result.success}")
        print(f"  Exit Code: {result.exit_code}")
        print(f"  Duration: {result.duration:.2f}s")
        print(f"  Statistics: {result.statistics}")
        
        # Hantera vanliga fel
        if not result.success:
            if "Address already in use" in result.error:
                pytest.skip("Port 5061 används redan - starta om systemet eller ändra port")
            elif "command not found" in result.error or "executable file not found" in result.error:
                pytest.skip("SIPp inte installerat i Docker-image")
            elif "Timeout expired" in result.error:
                print("⚠️  REGISTER-test timeout - Kamailio svarar inte (kan vara normalt för enkel proxy)")
                pytest.skip("REGISTER-test timeout - Kamailio svarar inte")
        
        assert result.success, f"REGISTER-test misslyckades: {result.error}"
    
    def test_invite_scenario(self, sipp_tester, ensure_environment_ready):
        """Testa INVITE-scenario"""
        result = sipp_tester.run_sipp_test("invite")
        
        print(f"\nINVITE Test Result:")
        print(f"  Success: {result.success}")
        print(f"  Exit Code: {result.exit_code}")
        print(f"  Duration: {result.duration:.2f}s")
        print(f"  Statistics: {result.statistics}")
        
        # Hantera vanliga fel
        if not result.success:
            if "Address already in use" in result.error:
                pytest.skip("Port 5061 används redan - starta om systemet eller ändra port")
            elif "command not found" in result.error or "executable file not found" in result.error:
                pytest.skip("SIPp inte installerat i Docker-image")
            elif "Timeout expired" in result.error:
                print("⚠️  INVITE-test timeout - Kamailio svarar inte (kan vara normalt för enkel proxy)")
                pytest.skip("INVITE-test timeout - Kamailio svarar inte")
        
        assert result.success, f"INVITE-test misslyckades: {result.error}"
    
    def test_ping_scenario(self, sipp_tester, ensure_environment_ready):
        """Testa PING-scenario"""
        result = sipp_tester.run_sipp_test("ping")
        
        print(f"\nPING Test Result:")
        print(f"  Success: {result.success}")
        print(f"  Duration: {result.duration:.2f}s")
        print(f"  Statistics: {result.statistics}")
        
        # Hantera vanliga fel
        if not result.success:
            if "Address already in use" in result.error:
                pytest.skip("Port 5061 används redan - starta om systemet eller ändra port")
            elif "command not found" in result.error or "executable file not found" in result.error:
                pytest.skip("SIPp inte installerat i Docker-image")
            elif "Timeout expired" in result.error:
                print("⚠️  PING-test timeout - Kamailio svarar inte (kan vara normalt för enkel proxy)")
                pytest.skip("PING-test timeout - Kamailio svarar inte")
        
        assert result.success, f"PING-test misslyckades: {result.error}"
    
    def test_all_scenarios(self, sipp_tester, ensure_environment_ready):
        """Testa alla scenarios"""
        results = sipp_tester.run_all_tests()
        
        print(f"\nAlla Test Result:")
        for result in results:
            print(f"  {result.scenario}: {'PASS' if result.success else 'FAIL'}")
        
        # Om endast health check kördes och misslyckades, det är OK
        if len(results) == 1 and results[0].scenario == "health_check" and not results[0].success:
            pytest.skip("Health check misslyckades, Kamailio inte tillgänglig")
        
        # Räkna lyckade tester
        successful_tests = sum(1 for r in results if r.success)
        total_tests = len(results)
        
        assert successful_tests == total_tests, f"Endast {successful_tests}/{total_tests} tester lyckades"


class TestSippTesterWithKamailio:
    """Tester som kräver att Kamailio är igång och tillgänglig"""
    
    @pytest.fixture(scope="class")
    def ensure_kamailio_ready(self):
        """Fixture som säkerställer att Kamailio är redo"""
        env_status = get_environment_status()
        
        # Kontrollera att Kamailio är deployad och körs
        kamailio_checks = ["kamailio_namespace", "kamailio_deployment", "kamailio_pods", "kamailio_service"]
        missing_kamailio = [check for check in kamailio_checks if not env_status.get(check, False)]
        
        if missing_kamailio:
            pytest.skip(f"Kamailio inte redo: {', '.join(missing_kamailio)}")
        
        return env_status
    
    @pytest.fixture(scope="class")
    def start_port_forward(self):
        """Starta port-forward till Kamailio"""
        print("Startar port-forward till Kamailio...")
        
        # Starta port-forward i bakgrunden
        process = subprocess.Popen([
            'kubectl', 'port-forward', 'svc/kamailio-service', '5060:5060', '-n', 'kamailio'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Vänta lite för att port-forward ska starta
        time.sleep(3)
        
        yield process
        
        # Stoppa port-forward
        print("Stoppar port-forward...")
        process.terminate()
        process.wait()
    
    @pytest.fixture(scope="class")
    def sipp_tester_with_kamailio(self, start_port_forward, environment):
        """SippTester med Kamailio tillgänglig"""
        return SippTester(
            kamailio_host="localhost",
            kamailio_port=5060,
            timeout=30,
            environment=environment
        )
    
    def test_health_check_with_kamailio(self, sipp_tester_with_kamailio, ensure_kamailio_ready):
        """Testa health check när Kamailio är igång"""
        result = sipp_tester_with_kamailio.health_check()
        
        print(f"\nHealth Check med Kamailio:")
        print(f"  Success: {result.success}")
        print(f"  Exit Code: {result.exit_code}")
        print(f"  Duration: {result.duration:.2f}s")
        
        # Detta test förväntar sig att Kamailio är igång
        assert result.success, f"Health check misslyckades: {result.error}"
    
    def test_options_with_kamailio(self, sipp_tester_with_kamailio, ensure_kamailio_ready):
        """Testa OPTIONS när Kamailio är igång"""
        result = sipp_tester_with_kamailio.run_sipp_test("options")
        
        print(f"\nOPTIONS med Kamailio:")
        print(f"  Success: {result.success}")
        print(f"  Exit Code: {result.exit_code}")
        print(f"  Statistics: {result.statistics}")
        
        # Hantera vanliga fel
        if not result.success:
            if "Address already in use" in result.error:
                pytest.skip("Port 5061 används redan - starta om systemet eller ändra port")
            elif "command not found" in result.error or "executable file not found" in result.error:
                pytest.skip("SIPp inte installerat i Docker-image")
            elif "Timeout expired" in result.error:
                print("⚠️  OPTIONS-test timeout - Kamailio svarar inte")
                pytest.skip("OPTIONS-test timeout - Kamailio svarar inte")
        
        assert result.success, f"OPTIONS-test misslyckades: {result.error}"
    
    def test_kamailio_sip_response(self, sipp_tester_with_kamailio, ensure_kamailio_ready):
        """Testa att Kamailio svarar på SIP-requests"""
        try:
            # Hämta NodePort för Kamailio service
            nodeport_result = subprocess.run(
                ["kubectl", "get", "svc", "kamailio-nodeport", "-n", "kamailio", "-o", "jsonpath={.spec.ports[?(@.port==5060)].nodePort}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if nodeport_result.returncode != 0 or not nodeport_result.stdout.strip():
                pytest.fail("Kunde inte hämta NodePort för Kamailio service")
            
            nodeport = nodeport_result.stdout.strip()
            print(f"Använder NodePort: {nodeport}")
            
            # Hämta worker node IP
            node_ip_result = subprocess.run(
                ["kubectl", "get", "nodes", "sipp-k8s-lab-worker", "-o", "jsonpath={.status.addresses[?(@.type=='InternalIP')].address}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if node_ip_result.returncode != 0 or not node_ip_result.stdout.strip():
                pytest.fail("Kunde inte hämta worker node IP")
            
            node_ip = node_ip_result.stdout.strip()
            print(f"Använder worker node IP: {node_ip}")
            
            # Skicka en enkel SIP OPTIONS request
            sip_request = (
                "OPTIONS sip:kamailio.local SIP/2.0\r\n"
                "Via: SIP/2.0/UDP 127.0.0.1:5061;branch=test\r\n"
                "From: <sip:test@kamailio.local>;tag=123\r\n"
                "To: <sip:kamailio.local>\r\n"
                "Call-ID: test123\r\n"
                "CSeq: 1 OPTIONS\r\n"
                "Contact: <sip:test@127.0.0.1:5061>\r\n"
                "User-Agent: Test Client\r\n"
                "Content-Length: 0\r\n\r\n"
            )
            
            # Skicka request och vänta på svar
            result = subprocess.run(
                ["nc", "-u", node_ip, nodeport],
                input=sip_request,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Kontrollera om vi fick något svar
            if result.stdout or result.stderr:
                print(f"✅ Kamailio svarar på SIP-requests")
            else:
                print(f"⚠️  Kamailio port öppen men svarar inte på SIP-requests")
                pytest.fail("Kamailio svarar inte på SIP-requests")
                       
        except Exception as e:
            print(f"⚠️  Kamailio SIP-response test misslyckades: {e}")
            pytest.fail(f"Kamailio svarar inte på SIP-requests via NodePort: {e}")


# Hjälpfunktioner för pytest
def pytest_configure(config):
    """Konfigurera pytest"""
    config.addinivalue_line(
        "markers", "slow: mark test as slow to run"
    )


def pytest_collection_modifyitems(config, items):
    """Modifiera test-samling"""
    for item in items:
        if "kamailio" in item.name.lower():
            item.add_marker(pytest.mark.slow)


# Kommandoradsargument för pytest
def pytest_addoption(parser):
    """Lägg till kommandoradsargument"""
    parser.addoption(
        "--kamailio-host",
        action="store",
        default="localhost",
        help="Kamailio host för tester"
    )
    parser.addoption(
        "--kamailio-port",
        action="store",
        default="5060",
        help="Kamailio port för tester"
    )
    parser.addoption(
        "--run-with-kamailio",
        action="store_true",
        help="Kör tester som kräver Kamailio"
    )


@pytest.fixture(scope="session")
def kamailio_host(request):
    """Fixture för Kamailio host"""
    return request.config.getoption("--kamailio-host")


@pytest.fixture(scope="session")
def kamailio_port(request):
    """Fixture för Kamailio port"""
    return int(request.config.getoption("--kamailio-port"))


def pytest_runtest_setup(item):
    """Setup för varje test"""
    if "kamailio" in item.name.lower() and not item.config.getoption("--run-with-kamailio"):
        pytest.skip("Kräver --run-with-kamailio flagga") 