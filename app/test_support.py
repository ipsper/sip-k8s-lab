#!/usr/bin/env python3
"""
Test Support Classes
Innehåller klasser och funktioner som används av testerna
"""

import pytest
import time
import subprocess
from typing import Dict, Any
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "sipp-tester"))
from sipp_support import SippTester
from sip_test_utils import get_environment_status


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
        critical_checks = ["docker", "sipp_image", "sipp_container", "sipp_installed", "sipp_scenarios"]
        missing_critical = [check for check in critical_checks if not env_status.get(check, False)]
        
        if missing_critical:
            pytest.skip(f"Kritiska komponenter för SIPp-tester saknas: {', '.join(missing_critical)}")
        
        return env_status
    
    @staticmethod
    def ensure_kamailio_ready() -> Dict[str, bool]:
        """Kontrollera att Kamailio är redo"""
        env_status = get_environment_status()
        
        # Kontrollera kritiska komponenter för Kamailio-tester
        critical_checks = ["docker", "kubernetes_cluster", "kamailio_namespace", "kamailio_deployment", "kamailio_pods", "kamailio_service"]
        missing_critical = [check for check in critical_checks if not env_status.get(check, False)]
        
        if missing_critical:
            pytest.skip(f"Kritiska komponenter för Kamailio-tester saknas: {', '.join(missing_critical)}")
        
        return env_status
    
    @staticmethod
    def start_port_forward() -> subprocess.Popen:
        """Starta port-forward för Kamailio"""
        try:
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