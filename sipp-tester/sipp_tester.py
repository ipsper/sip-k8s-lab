#!/usr/bin/env python3
"""
SIPp Tester - Python wrapper för SIPp-tester
"""

import os
import subprocess
import time
import json
import logging
import socket
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# Konfigurera logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Resultat från ett SIPp-test"""
    scenario: str
    success: bool
    exit_code: int
    output: str
    error: str
    duration: float
    statistics: Dict


class SippTester:
    """Huvudklass för SIPp-testing"""
    
    def __init__(self, 
                 kamailio_host: Optional[str] = None,
                 kamailio_port: int = 5060,
                 timeout: int = 30,
                 docker_image: str = "local/sipp-tester:latest"):
        """
        Initiera SIPp-tester
        
        Args:
            kamailio_host: Kamailio-serverns hostname (auto-detekteras om None)
            kamailio_port: Kamailio-serverns port
            timeout: Timeout för tester i sekunder
            docker_image: Docker-image för SIPp-tester
        """
        self.kamailio_port = kamailio_port
        self.timeout = timeout
        self.docker_image = docker_image
        self.base_path = Path(__file__).parent
        
        # Auto-detektera Kamailio host
        self.kamailio_host = kamailio_host or self._detect_kamailio_host()
        
        # Miljövariabler för Docker
        self.env_vars = {
            'KAMAILIO_HOST': self.kamailio_host,
            'KAMAILIO_PORT': str(self.kamailio_port),
            'TEST_TIMEOUT': str(self.timeout)
        }
        
        logger.info(f"Använder Kamailio host: {self.kamailio_host}:{self.kamailio_port}")
    
    def _detect_kamailio_host(self) -> str:
        """
        Auto-detektera bästa Kamailio host baserat på miljö
        
        Returns:
            Bästa hostname/IP för Kamailio
        """
        # Testa olika alternativ i prioritetsordning
        
        # 1. Testa NodePort service (bästa för UDP)
        try:
            # Hämta minikube IP
            result = subprocess.run(
                ["minikube", "ip"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                minikube_ip = result.stdout.strip()
                if self._test_connection(minikube_ip, 30600):  # NodePort UDP port
                    logger.info(f"Använder NodePort service: {minikube_ip}:30600")
                    return f"{minikube_ip}:30600"
        except Exception as e:
            logger.debug(f"Kunde inte använda NodePort service: {e}")
        
        # 2. Testa om vi kör i Kubernetes-kluster
        if self._is_kubernetes_available():
            try:
                # Testa minikube IP med LoadBalancer port
                minikube_ip = self._get_minikube_ip()
                if minikube_ip and self._test_connection(minikube_ip, 32760):  # LoadBalancer port
                    logger.info(f"Använder LoadBalancer service: {minikube_ip}:32760")
                    return f"{minikube_ip}:32760"
            except Exception as e:
                logger.debug(f"Kunde inte använda LoadBalancer service: {e}")
        
        # 3. Testa localhost med port-forward
        if self._test_connection("localhost", self.kamailio_port):
            logger.info("Använder localhost (port-forward)")
            return "localhost"
        
        # 4. Testa host.docker.internal (för Docker containers)
        if self._test_connection("host.docker.internal", self.kamailio_port):
            logger.info("Använder host.docker.internal")
            return "host.docker.internal"
        
        # 5. Fallback till NodePort service
        try:
            minikube_ip = self._get_minikube_ip()
            if minikube_ip:
                logger.warning("Kunde inte testa anslutning, använder NodePort service som fallback")
                return f"{minikube_ip}:30600"
        except Exception:
            pass
        
        # 6. Fallback till localhost
        logger.warning("Kunde inte detektera Kamailio host, använder localhost")
        return "localhost"
    
    def _is_kubernetes_available(self) -> bool:
        """Kontrollera om Kubernetes är tillgängligt"""
        try:
            result = subprocess.run(
                ["kubectl", "cluster-info"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _get_minikube_ip(self) -> Optional[str]:
        """Hämta minikube IP-adress"""
        try:
            result = subprocess.run(
                ["minikube", "ip"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
    
    def _test_connection(self, host: str, port: int) -> bool:
        """Testa anslutning till host:port"""
        try:
            # Använd nc för att testa anslutning
            result = subprocess.run(
                ["nc", "-z", host, str(port)],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _run_docker_command(self, command: str, timeout: int = 30) -> TestResult:
        """Kör ett Docker-kommando och returnera resultat"""
        try:
            # Bestäm nätverksargument baserat på host
            network_args = []
            if self.kamailio_host == "localhost":
                network_args = ["--network=host"]
            
            # Kör Docker-kommando
            result = subprocess.run([
                "docker", "run", "--rm"
            ] + network_args + [
                self.docker_image,
                "bash", "-c", command
            ], capture_output=True, text=True, timeout=timeout)
            
            return TestResult(
                scenario="docker_command",
                success=result.returncode == 0,
                exit_code=result.returncode,
                output=result.stdout,
                error=result.stderr,
                duration=0,  # Vi mäter inte tid för generella kommandon
                statistics={}
            )
        except subprocess.TimeoutExpired:
            return TestResult(
                scenario="docker_command",
                success=False,
                exit_code=-1,
                output="",
                error="Timeout expired",
                duration=timeout,
                statistics={}
            )
        except Exception as e:
            return TestResult(
                scenario="docker_command",
                success=False,
                exit_code=-1,
                output="",
                error=str(e),
                duration=0,
                statistics={}
            )

    def health_check(self) -> TestResult:
        """
        Kontrollera om Kamailio är tillgänglig
        
        Returns:
            TestResult med health check resultat
        """
        logger.info("🏥 Health Check för Kamailio...")
        start_time = time.time()
        
        # Bestäm Kamailio host
        kamailio_host = self._detect_kamailio_host()
        logger.info(f"📍 Target: {kamailio_host}")
        
        # Testa anslutning med netcat
        test_command = f"nc -z -w 5 {kamailio_host.replace(':', ' ')}"
        
        logger.info("🔍 Kontrollerar port-anslutning...")
        
        # Försök flera gånger
        for attempt in range(5):
            try:
                # Bestäm nätverksargument baserat på host
                network_args = []
                if kamailio_host == "localhost":
                    network_args = ["--network=host"]
                
                result = subprocess.run([
                    "docker", "run", "--rm"
                ] + network_args + [
                    self.docker_image,
                    "bash", "-c", test_command
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    duration = time.time() - start_time
                    logger.info(f"✅ Kamailio är tillgänglig på {kamailio_host}")
                    return TestResult(
                        scenario="health_check",
                        success=True,
                        exit_code=0,
                        output=f"Kamailio tillgänglig på {kamailio_host}",
                        error="",
                        duration=duration,
                        statistics={}
                    )
                else:
                    logger.warning(f"   Försök {attempt + 1}/5 misslyckades")
                    if attempt < 4:
                        logger.info("   Väntar 2s innan nästa försök...")
                        time.sleep(2)
                        
            except Exception as e:
                logger.warning(f"   Försök {attempt + 1}/5 misslyckades: {e}")
                if attempt < 4:
                    logger.info("   Väntar 2s innan nästa försök...")
                    time.sleep(2)
        
        duration = time.time() - start_time
        error_msg = f"Kan inte ansluta till Kamailio på {kamailio_host}"
        logger.error(f"❌ {error_msg}")
        
        return TestResult(
            scenario="health_check",
            success=False,
            exit_code=1,
            output=error_msg,
            error="",
            duration=duration,
            statistics={}
        )
    
    def run_sipp_test(self, scenario: str) -> TestResult:
        """Kör ett SIPp-test"""
        start_time = time.time()
        
        # Bestäm Kamailio host
        kamailio_host = self._detect_kamailio_host()
        
        # SIPp-kommando med lokal port 5061 för att undvika konflikter
        sipp_command = f"sipp -sf /app/sipp-scenarios/{scenario}.xml {kamailio_host} -p 5062 -d 1000 -m 1 -r 1"
        
        logger.info(f"Kör SIPp-test: {scenario}")
        logger.info(f"Target: {kamailio_host}")
        logger.info(f"Command: {sipp_command}")
        
        try:
            # Bestäm nätverksargument baserat på host
            network_args = []
            if kamailio_host == "localhost":
                network_args = ["--network=host"]
            
            # Kör SIPp i Docker
            result = subprocess.run([
                "docker", "run", "--rm"
            ] + network_args + [
                self.docker_image,
                "bash", "-c", sipp_command
            ], capture_output=True, text=True, timeout=30)
            
            duration = time.time() - start_time
            
            # Analysera output för statistik
            statistics = self._parse_sipp_statistics(result.stdout)
            
            return TestResult(
                scenario=scenario,
                success=result.returncode == 0,
                exit_code=result.returncode,
                output=result.stdout,
                error=result.stderr,
                duration=duration,
                statistics=statistics
            )
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            logger.error(f"Timeout efter {duration:.1f} sekunder")
            return TestResult(
                scenario=scenario,
                success=False,
                exit_code=-1,
                output="",
                error="Timeout expired",
                duration=duration,
                statistics={}
            )
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Fel vid körning av SIPp-test: {e}")
            return TestResult(
                scenario=scenario,
                success=False,
                exit_code=-1,
                output="",
                error=str(e),
                duration=duration,
                statistics={}
            )
    
    def run_all_tests(self) -> List[TestResult]:
        """
        Kör alla SIPp-tester
        
        Returns:
            Lista med TestResult
        """
        logger.info("Kör alla SIPp-tester...")
        
        scenarios = ['options', 'register', 'invite', 'ping']
        results = []
        
        # Kör health check först
        health_result = self.health_check()
        results.append(health_result)
        
        if not health_result.success:
            logger.warning("Health check misslyckades, hoppar över SIPp-tester")
            return results
        
        # Kör alla SIPp-scenarios
        for scenario in scenarios:
            result = self.run_sipp_test(scenario)
            results.append(result)
            
            # Kort paus mellan tester
            time.sleep(1)
        
        return results
    
    def _parse_sipp_statistics(self, output: str) -> Dict:
        """
        Parsa SIPp-statistik från output
        
        Args:
            output: SIPp output
            
        Returns:
            Dictionary med statistik
        """
        stats = {}
        
        # Enkel parsing av SIPp-statistik
        lines = output.split('\n')
        for line in lines:
            if 'Total' in line and 'Messages' in line:
                # Exempel: "Total: 1 Messages, 0 Errors, 0 Failures"
                parts = line.split(',')
                for part in parts:
                    if 'Messages' in part:
                        stats['total_messages'] = part.strip().split()[0]
                    elif 'Errors' in part:
                        stats['errors'] = part.strip().split()[0]
                    elif 'Failures' in part:
                        stats['failures'] = part.strip().split()[0]
        
        return stats
    
    def build_docker_image(self) -> bool:
        """
        Bygg Docker-image för SIPp-tester
        
        Returns:
            True om bygget lyckades
        """
        logger.info("Bygger Docker-image för SIPp-tester...")
        
        try:
            result = subprocess.run(
                ['docker', 'build', '-t', self.docker_image, '.'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info("Docker-image byggd framgångsrikt")
                return True
            else:
                logger.error(f"Fel vid byggning av Docker-image: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Fel vid byggning av Docker-image: {e}")
            return False
    
    def check_docker_image(self) -> bool:
        """
        Kontrollera om Docker-image finns
        
        Returns:
            True om image finns
        """
        try:
            result = subprocess.run(
                ['docker', 'images', '-q', self.docker_image],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return result.returncode == 0 and result.stdout.strip() != ""
            
        except Exception:
            return False


def print_test_results(results: List[TestResult]) -> None:
    """
    Skriv ut testresultat
    
    Args:
        results: Lista med TestResult
    """
    print("\n" + "="*60)
    print("TESTRESULTAT")
    print("="*60)
    
    for result in results:
        status = "✅ PASS" if result.success else "❌ FAIL"
        print(f"{status} {result.scenario:15} ({result.duration:.2f}s)")
        
        if not result.success and result.error:
            print(f"    Fel: {result.error.strip()}")
    
    print("="*60)
    
    # Sammanfattning
    total = len(results)
    passed = sum(1 for r in results if r.success)
    failed = total - passed
    
    print(f"Totalt: {total}, Passerade: {passed}, Misslyckades: {failed}")
    
    if failed == 0:
        print("🎉 Alla tester passerade!")
    else:
        print("⚠️  Vissa tester misslyckades")


if __name__ == "__main__":
    # Exempel på användning
    tester = SippTester()
    
    # Kontrollera om Docker-image finns
    if not tester.check_docker_image():
        print("Bygger Docker-image...")
        if not tester.build_docker_image():
            print("Kunde inte bygga Docker-image")
            exit(1)
    
    # Kör alla tester
    results = tester.run_all_tests()
    print_test_results(results) 