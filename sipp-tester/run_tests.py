#!/usr/bin/env python3
"""
Enkelt script för att köra SIPp-tester
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Huvudfunktion"""
    print("🧪 SIPp Test Runner")
    print("=" * 40)
    
    # Kontrollera att vi är i rätt katalog
    if not Path("../app/sipp_support.py").exists():
        print("❌ Kör detta script från sipp-tester-mappen")
        sys.exit(1)
    
    # Visa alternativ
    print("\nVälj test-alternativ:")
    print("1) Kör alla tester (utan Kamailio)")
    print("2) Kör tester med Kamailio (port-forward)")
    print("3) Kör specifikt test")
    print("4) Bygg Docker-image")
    print("5) Visa hjälp")
    
    choice = input("\nVälj alternativ (1-5): ").strip()
    
    if choice == "1":
        run_basic_tests()
    elif choice == "2":
        run_with_kamailio()
    elif choice == "3":
        run_specific_test()
    elif choice == "4":
        build_docker_image()
    elif choice == "5":
        show_help()
    else:
        print("❌ Ogiltigt val")
        sys.exit(1)


def run_basic_tests():
    """Kör grundläggande tester"""
    print("\n🚀 Kör grundläggande tester...")
    
    cmd = [
        "python", "-m", "pytest",
        "test_sipp_pytest.py::TestSippTester",
        "-v",
        "--tb=short"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Grundläggande tester slutförda!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tester misslyckades: {e}")
        sys.exit(1)


def run_with_kamailio():
    """Kör tester med Kamailio"""
    print("\n🚀 Kör tester med Kamailio...")
    
    cmd = [
        "python", "-m", "pytest",
        "test_sipp_pytest.py::TestSippTesterWithKamailio",
        "--run-with-kamailio",
        "-v",
        "--tb=short"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Tester med Kamailio slutförda!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tester misslyckades: {e}")
        sys.exit(1)


def run_specific_test():
    """Kör specifikt test"""
    print("\nVälj test:")
    print("1) Health check")
    print("2) OPTIONS scenario")
    print("3) REGISTER scenario")
    print("4) INVITE scenario")
    print("5) PING scenario")
    
    test_choice = input("Välj test (1-5): ").strip()
    
    test_map = {
        "1": "test_health_check",
        "2": "test_options_scenario",
        "3": "test_register_scenario",
        "4": "test_invite_scenario",
        "5": "test_ping_scenario"
    }
    
    if test_choice not in test_map:
        print("❌ Ogiltigt val")
        return
    
    test_name = test_map[test_choice]
    print(f"\n🚀 Kör {test_name}...")
    
    cmd = [
        "python", "-m", "pytest",
        f"test_sipp_pytest.py::TestSippTester::{test_name}",
        "-v",
        "-s"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n✅ {test_name} slutförd!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Test misslyckades: {e}")


def build_docker_image():
    """Bygg Docker-image"""
    print("\n🔨 Bygger Docker-image...")
    
    cmd = ["docker", "build", "-t", "local/sipp-tester:latest", "."]
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Docker-image byggdes framgångsrikt!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Kunde inte bygga Docker-image: {e}")
        sys.exit(1)


def show_help():
    """Visa hjälp"""
    print("\n📖 Hjälp för SIPp Test Runner")
    print("=" * 40)
    print("\nKommandoradsanvändning:")
    print("  python run_tests.py                    # Interaktiv meny")
    print("  python -m pytest test_sipp_pytest.py   # Kör alla tester")
    print("  python -m pytest --run-with-kamailio   # Kör med Kamailio")
    print("  python -m pytest -k 'health'           # Kör specifikt test")
    print("\nExempel:")
    print("  # Kör grundläggande tester")
    print("  python -m pytest test_sipp_pytest.py::TestSippTester")
    print("\n  # Kör tester med Kamailio")
    print("  python -m pytest test_sipp_pytest.py::TestSippTesterWithKamailio --run-with-kamailio")
    print("\n  # Kör endast health check")
    print("  python -m pytest test_sipp_pytest.py::TestSippTester::test_health_check")
    print("\n  # Bygg Docker-image")
    print("  python -m pytest --build-docker")


if __name__ == "__main__":
    main() 