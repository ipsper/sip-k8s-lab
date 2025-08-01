#!/usr/bin/env python3
"""
SIP Test Utilities
Gemensamma funktioner för SIP-tester
"""

import subprocess
import time
import json
import os
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path


# Konfigurera logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KamailioConfig:
    """Konfiguration för Kamailio-anslutning"""
    
    def __init__(self, host: str, port: int, environment: str):
        self.host = host
        self.port = port
        self.environment = environment
    
    def __str__(self):
        if ":" in self.host:
            return f"{self.host}"
        else:
            return f"{self.host}:{self.port}"
    
    @classmethod
    def from_environment(cls) -> 'KamailioConfig':
        """Skapa konfiguration från environment-variabler"""
        host = os.getenv('KAMAILIO_HOST', 'localhost')
        port = int(os.getenv('KAMAILIO_PORT', '5060'))
        environment = os.getenv('KAMAILIO_ENVIRONMENT', 'auto')
        return cls(host, port, environment)


class KubernetesUtils:
    """Utility-funktioner för Kubernetes"""
    
    @staticmethod
    def check_namespace_exists(namespace: str) -> bool:
        """Kontrollera om namespace finns"""
        try:
            result = subprocess.run(
                ["kubectl", "get", "namespace", namespace],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    def create_namespace(namespace: str) -> bool:
        """Skapa namespace"""
        try:
            result = subprocess.run(
                ["kubectl", "create", "namespace", namespace],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    def check_deployment_exists(name: str, namespace: str) -> bool:
        """Kontrollera om deployment finns"""
        try:
            result = subprocess.run(
                ["kubectl", "get", "deployment", name, "-n", namespace],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    def check_pods_running(namespace: str, label_selector: str) -> Tuple[bool, List[str]]:
        """Kontrollera om pods körs"""
        try:
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", namespace, "-l", label_selector, "-o", "json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return False, []
            
            pods_data = json.loads(result.stdout)
            running_pods = []
            
            for pod in pods_data.get('items', []):
                pod_name = pod['metadata']['name']
                status = pod['status']['phase']
                if status == 'Running':
                    running_pods.append(pod_name)
            
            return len(running_pods) > 0, running_pods
        except Exception:
            return False, []
    
    @staticmethod
    def check_service_exists(name: str, namespace: str) -> bool:
        """Kontrollera om service finns"""
        try:
            result = subprocess.run(
                ["kubectl", "get", "service", name, "-n", namespace],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    def get_node_ip(node_name: str) -> Optional[str]:
        """Hämta node IP-adress"""
        try:
            result = subprocess.run(
                ["kubectl", "get", "nodes", node_name, "-o", "jsonpath={.status.addresses[?(@.type=='InternalIP')].address}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
        return None
    
    @staticmethod
    def get_service_nodeport(service_name: str, namespace: str, port: int) -> Optional[int]:
        """Hämta NodePort för service"""
        try:
            result = subprocess.run(
                ["kubectl", "get", "svc", service_name, "-n", namespace, "-o", f"jsonpath={{.spec.ports[?(@.port=={port})].nodePort}}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip())
        except Exception:
            pass
        return None


class DockerUtils:
    """Utility-funktioner för Docker"""
    
    @staticmethod
    def check_image_exists(image_name: str) -> bool:
        """Kontrollera om Docker-image finns"""
        try:
            result = subprocess.run(
                ["docker", "images", "-q", image_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            return bool(result.stdout.strip())
        except Exception:
            return False
    
    @staticmethod
    def build_image(image_name: str, dockerfile_path: str) -> bool:
        """Bygg Docker-image"""
        try:
            result = subprocess.run(
                ["docker", "build", "-t", image_name, dockerfile_path],
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    def run_container(image_name: str, command: str, timeout: int = 30) -> Tuple[bool, str]:
        """Kör Docker-container"""
        try:
            result = subprocess.run(
                ["docker", "run", "--rm", image_name] + command.split(),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout
        except Exception as e:
            return False, str(e)


class NetworkUtils:
    """Utility-funktioner för nätverkstestning"""
    
    @staticmethod
    def test_udp_connection(host: str, port: int, timeout: int = 5) -> bool:
        """Testa UDP-anslutning"""
        try:
            result = subprocess.run(
                ["nc", "-zu", host, str(port)],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    def test_tcp_connection(host: str, port: int, timeout: int = 5) -> bool:
        """Testa TCP-anslutning"""
        try:
            result = subprocess.run(
                ["nc", "-z", host, str(port)],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    def port_forward_service(service_name: str, namespace: str, local_port: int, remote_port: int) -> Optional[subprocess.Popen]:
        """Starta port-forward för service"""
        try:
            process = subprocess.Popen(
                ["kubectl", "port-forward", f"svc/{service_name}", f"{local_port}:{remote_port}", "-n", namespace],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(3)  # Vänta lite för att port-forward ska starta
            return process
        except Exception:
            return None


class EnvironmentChecker:
    """Kontrollera miljöförutsättningar"""
    
    @staticmethod
    def check_docker() -> bool:
        """Kontrollera att Docker är tillgängligt"""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    def check_kubectl() -> bool:
        """Kontrollera att kubectl är tillgängligt"""
        try:
            result = subprocess.run(
                ["kubectl", "version", "--client"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    def check_kubernetes_cluster() -> bool:
        """Kontrollera att Kubernetes-kluster är tillgängligt"""
        try:
            result = subprocess.run(
                ["kubectl", "cluster-info"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    def check_sipp_installed() -> bool:
        """Kontrollera att SIPp är installerat"""
        try:
            result = subprocess.run(
                ["which", "sipp"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False


class KamailioUtils:
    """Utility-funktioner för Kamailio"""
    
    @staticmethod
    def check_kamailio_readiness(config: KamailioConfig) -> Dict[str, bool]:
        """Kontrollera Kamailio readiness"""
        results = {}
        
        # Kontrollera pods
        pods_running, running_pods = KubernetesUtils.check_pods_running("kamailio", "app=kamailio")
        results['pods_running'] = pods_running
        
        # Kontrollera service
        service_exists = KubernetesUtils.check_service_exists("kamailio-service", "kamailio")
        results['service_exists'] = service_exists
        
        # Kontrollera port-anslutning
        if config.environment == "local":
            # För local environment, testa direkt anslutning
            host_ip = config.host
            host_port = config.port
            port_accessible = NetworkUtils.test_udp_connection(host_ip, host_port)
        else:
            # För andra miljöer, använd port-forward
            process = NetworkUtils.port_forward_service("kamailio-service", "kamailio", config.port, config.port)
            if process:
                port_accessible = NetworkUtils.test_tcp_connection("localhost", config.port)
                process.terminate()
                process.wait()
            else:
                port_accessible = False
        results['port_accessible'] = port_accessible
        
        return results
    
    @staticmethod
    def get_kamailio_config() -> Optional[str]:
        """Hämta Kamailio-konfiguration"""
        try:
            result = subprocess.run(
                ["kubectl", "get", "configmap", "kamailio-config", "-n", "kamailio", "-o", "jsonpath={.data.kamailio\\.cfg}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout
        except Exception:
            pass
        return None


def get_environment_status() -> Dict[str, bool]:
    """Hämta status för hela miljön"""
    env_tester = EnvironmentChecker()
    
    checks = [
        ("docker", env_tester.check_docker),
        ("kubectl", env_tester.check_kubectl),
        ("kubernetes_cluster", env_tester.check_kubernetes_cluster),
        ("sipp_installed", env_tester.check_sipp_installed),
    ]
    
    status = {}
    for name, check_func in checks:
        try:
            status[name] = check_func()
        except Exception:
            status[name] = False
    
    # Lägg till Docker-specifika kontroller
    try:
        status["sipp_image"] = DockerUtils.check_image_exists("local/sipp-tester:latest")
    except Exception:
        status["sipp_image"] = False
    
    try:
        success, _ = DockerUtils.run_container("local/sipp-tester:latest", "echo test")
        status["sipp_container"] = success
    except Exception:
        status["sipp_container"] = False
    
    # Lägg till SIPp scenarios kontroll
    try:
        scenarios = ["options", "register", "invite", "ping"]
        missing_scenarios = []
        
        for scenario in scenarios:
            result = subprocess.run(
                ["docker", "run", "--rm", "local/sipp-tester:latest", "test", "-f", f"/app/sipp-scenarios/{scenario}.xml"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                missing_scenarios.append(scenario)
        
        status["sipp_scenarios"] = len(missing_scenarios) == 0
    except Exception:
        status["sipp_scenarios"] = False
    
    # Lägg till Kamailio-specifika kontroller
    try:
        status["kamailio_namespace"] = KubernetesUtils.check_namespace_exists("kamailio")
    except Exception:
        status["kamailio_namespace"] = False
    
    try:
        status["kamailio_deployment"] = KubernetesUtils.check_deployment_exists("kamailio", "kamailio")
    except Exception:
        status["kamailio_deployment"] = False
    
    try:
        pods_running, _ = KubernetesUtils.check_pods_running("kamailio", "app=kamailio")
        status["kamailio_pods"] = pods_running
    except Exception:
        status["kamailio_pods"] = False
    
    try:
        status["kamailio_service"] = KubernetesUtils.check_service_exists("kamailio-service", "kamailio")
    except Exception:
        status["kamailio_service"] = False
    
    return status


def is_environment_ready() -> bool:
    """Kontrollera om miljön är redo"""
    status = get_environment_status()
    required_checks = ["docker", "kubectl", "kubernetes_cluster"]
    return all(status.get(check, False) for check in required_checks)


def parse_kamailio_address(host: str, port: int) -> tuple[str, int]:
    """
    Parsa Kamailio host och port
    
    Args:
        host: Host (kan innehålla port)
        port: Standard port
        
    Returns:
        Tuple med (host_ip, port)
    """
    # Om host redan innehåller port, använd den
    if ":" in host:
        host_ip = host.split(":")[0]
        host_port = int(host.split(":")[1])
        return host_ip, host_port
    else:
        return host, port


def format_kamailio_address(host: str, port: int) -> str:
    """
    Formatera Kamailio adress för visning
    
    Args:
        host: Host (kan innehålla port)
        port: Standard port
        
    Returns:
        Formaterad adress (host:port)
    """
    host_ip, host_port = parse_kamailio_address(host, port)
    return f"{host_ip}:{host_port}"


def get_kamailio_connection_info(host: str, port: int) -> dict:
    """
    Hämta information för anslutning till Kamailio
    
    Args:
        host: Host (kan innehålla port)
        port: Standard port
        
    Returns:
        Dict med connection info
    """
    host_ip, host_port = parse_kamailio_address(host, port)
    
    return {
        'host': host_ip,
        'port': host_port,
        'address': f"{host_ip}:{host_port}",
        'display': f"{host_ip}:{host_port}"
    }


def get_kamailio_config_from_environment() -> dict:
    """
    Hämta Kamailio-konfiguration från miljövariabler
    
    Returns:
        Dict med host och port
    """
    import os
    
    # Standard-värden för olika miljöer
    default_configs = {
        "local": {"host": "localhost", "port": 30600},  # Kind NodePort
        "prod": {"host": "kamailio-service", "port": 5060},  # Kubernetes service
        "test": {"host": "localhost", "port": 5061},  # Test port
    }
    
    # Hämta från miljövariabler
    environment = os.getenv("KAMAILIO_ENVIRONMENT", "auto")
    host = os.getenv("KAMAILIO_HOST")
    port = os.getenv("KAMAILIO_PORT")
    
    # Om miljövariabler finns, använd dem
    if host and port:
        return {
            "host": host,
            "port": int(port),
            "environment": environment
        }
    
    # Annars använd standard för miljö
    if environment in default_configs:
        config = default_configs[environment].copy()
        config["environment"] = environment
        return config
    
    # Fallback till local
    config = default_configs["local"].copy()
    config["environment"] = environment
    return config


def create_kamailio_connection_string(host: str = None, port: int = None, environment: str = None) -> str:
    """
    Skapa Kamailio-anslutningssträng
    
    Args:
        host: Host (optional, hämtas från miljö om None)
        port: Port (optional, hämtas från miljö om None)
        environment: Miljö (optional, hämtas från miljö om None)
        
    Returns:
        Anslutningssträng (host:port)
    """
    if host is None or port is None or environment is None:
        config = get_kamailio_config_from_environment()
        host = host or config["host"]
        port = port or config["port"]
        environment = environment or config["environment"]
    
    # Använd den faktiska IP-adressen från KAMAILIO_HOST
    
    return f"{host}:{port}"


if __name__ == "__main__":
    """Testa utility-funktioner"""
    print("🔍 Kontrollerar miljö...")
    status = get_environment_status()
    
    for check, result in status.items():
        status_icon = "✅" if result else "❌"
        print(f"{status_icon} {check}: {result}")
    
    if is_environment_ready():
        print("✅ Miljön är redo!")
    else:
        print("❌ Miljön är inte redo!") 