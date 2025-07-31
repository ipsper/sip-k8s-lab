#!/usr/bin/env python3
"""
Pytest-konfiguration för SIPp-tester
"""

import pytest
import subprocess
import time
from pathlib import Path


def pytest_configure(config):
    """Konfigurera pytest"""
    # Lägg till markörer
    config.addinivalue_line("markers", "slow: mark test as slow to run")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "kamailio: mark test as requiring Kamailio")


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
    parser.addoption(
        "--build-docker",
        action="store_true",
        help="Bygg Docker-image innan tester"
    )


@pytest.fixture(scope="session")
def kamailio_host(request):
    """Fixture för Kamailio host"""
    return request.config.getoption("--kamailio-host")


@pytest.fixture(scope="session")
def kamailio_port(request):
    """Fixture för Kamailio port"""
    return int(request.config.getoption("--kamailio-port"))


@pytest.fixture(scope="session")
def docker_image_built(request):
    """Fixture som bygger Docker-image om det behövs"""
    if request.config.getoption("--build-docker"):
        print("Bygger Docker-image...")
        result = subprocess.run(
            ["docker", "build", "-t", "local/sipp-tester:latest", "."],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            pytest.fail(f"Kunde inte bygga Docker-image: {result.stderr}")
        print("Docker-image byggdes framgångsrikt")


@pytest.fixture(scope="session")
def port_forward_process(request):
    """Fixture som startar port-forward om det behövs"""
    if request.config.getoption("--run-with-kamailio"):
        print("Startar port-forward till Kamailio...")
        
        # Kontrollera att kubectl finns
        try:
            subprocess.run(["kubectl", "version", "--client"], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.fail("kubectl hittades inte")
        
        # Starta port-forward
        process = subprocess.Popen([
            "kubectl", "port-forward", "svc/kamailio-service", 
            "5060:5060", "-n", "kamailio"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Vänta lite för att port-forward ska starta
        time.sleep(3)
        
        # Kontrollera att port-forward fungerar
        try:
            subprocess.run(["nc", "-z", "localhost", "5060"], 
                         capture_output=True, check=True, timeout=5)
            print("Port-forward är aktivt")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            process.terminate()
            pytest.fail("Port-forward startade inte korrekt")
        
        yield process
        
        # Stoppa port-forward
        print("Stoppar port-forward...")
        process.terminate()
        process.wait()
    else:
        yield None


def pytest_runtest_setup(item):
    """Setup för varje test"""
    # Hoppa över Kamailio-tester om flaggan inte är satt
    # Men tillåt miljökontroller att köras alltid
    if ("kamailio" in item.name.lower() and 
        "test_environment_only" not in item.module.__name__ and
        not item.config.getoption("--run-with-kamailio")):
        pytest.skip("Kräver --run-with-kamailio flagga")


def pytest_collection_modifyitems(config, items):
    """Modifiera test-samling"""
    for item in items:
        # Lägg till markörer baserat på testnamn
        if "kamailio" in item.name.lower():
            item.add_marker(pytest.mark.kamailio)
        if "integration" in item.name.lower():
            item.add_marker(pytest.mark.integration)
        if any(word in item.name.lower() for word in ["slow", "integration", "kamailio"]):
            item.add_marker(pytest.mark.slow) 