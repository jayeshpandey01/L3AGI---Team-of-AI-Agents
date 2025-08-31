#!/usr/bin/env python3
"""
Test runner script for XAgent integration.
This script provides easy access to different test categories.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n🚀 {description}")
    print(f"Running: {cmd}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=False)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ {description} failed with error: {e}")
        return False


def run_unit_tests():
    """Run unit tests (fast, no external dependencies)"""
    cmd = "python -m pytest tests/unit/ -m unit -v"
    return run_command(cmd, "Unit Tests")


def run_integration_tests():
    """Run integration tests (requires XAgent services)"""
    cmd = "python -m pytest tests/test_xagent_integration.py -m integration -v"
    return run_command(cmd, "Integration Tests")


def run_xagent_tests():
    """Run XAgent-specific tests"""
    cmd = "python -m pytest -m xagent -v"
    return run_command(cmd, "XAgent Tests")


def run_react_tests():
    """Run ReAct-specific tests"""
    cmd = "python -m pytest -m react -v"
    return run_command(cmd, "ReAct Tests")


def run_mock_tests():
    """Run tests that use mocks"""
    cmd = "python -m pytest -m mock -v"
    return run_command(cmd, "Mock Tests")


def run_history_tests():
    """Run history mapping tests"""
    cmd = "python -m pytest -m history -v"
    return run_command(cmd, "History Mapping Tests")


def run_all_tests():
    """Run all tests"""
    cmd = "python -m pytest tests/ -v"
    return run_command(cmd, "All Tests")


def run_specific_test(test_path):
    """Run a specific test file or test function"""
    cmd = f"python -m pytest {test_path} -v"
    return run_command(cmd, f"Specific Test: {test_path}")


def check_xagent_services():
    """Check if XAgent services are running"""
    print("\n🔍 Checking XAgent Services")
    print("-" * 30)
    
    services = [
        ("XAgent Server", "http://localhost:8090/health"),
        ("ToolServer", "http://localhost:8080/health"),
        ("XAgent Web UI", "http://localhost:5173")
    ]
    
    import requests
    
    for service_name, url in services:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name}: Running")
            else:
                print(f"⚠️  {service_name}: Responding but status {response.status_code}")
        except requests.exceptions.RequestException:
            print(f"❌ {service_name}: Not accessible")
    
    print("\n💡 To start services, run: docker-compose -f docker-compose.xagent.yml up -d")


def show_test_summary():
    """Show a summary of available tests"""
    print("\n📋 Available Test Categories")
    print("=" * 40)
    print("1. Unit Tests (fast, no external deps)")
    print("   - Adapter functionality")
    print("   - Mock-based testing")
    print("   - History mapping")
    print()
    print("2. Integration Tests (requires services)")
    print("   - XAgent API calls")
    print("   - ToolServer integration")
    print("   - End-to-end workflows")
    print()
    print("3. Specific Test Types")
    print("   - XAgent functionality")
    print("   - ReAct compatibility")
    print("   - Mock scenarios")
    print("   - History context")
    print()
    print("4. Service Health Check")
    print("   - Verify XAgent services")
    print("   - Check ToolServer status")
    print("   - Validate Web UI")


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="XAgent Integration Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--xagent", action="store_true", help="Run XAgent tests")
    parser.add_argument("--react", action="store_true", help="Run ReAct tests")
    parser.add_argument("--mock", action="store_true", help="Run mock tests")
    parser.add_argument("--history", action="store_true", help="Run history tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--check-services", action="store_true", help="Check XAgent services")
    parser.add_argument("--test", type=str, help="Run specific test file or function")
    parser.add_argument("--summary", action="store_true", help="Show test summary")
    
    args = parser.parse_args()
    
    # Change to the project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    print("🧪 XAgent Integration Test Runner")
    print("=" * 40)
    
    if args.summary:
        show_test_summary()
        return
    
    if args.check_services:
        check_xagent_services()
        return
    
    if args.test:
        success = run_specific_test(args.test)
        sys.exit(0 if success else 1)
    
    # Run requested test categories
    success = True
    
    if args.unit:
        success &= run_unit_tests()
    
    if args.integration:
        success &= run_integration_tests()
    
    if args.xagent:
        success &= run_xagent_tests()
    
    if args.react:
        success &= run_react_tests()
    
    if args.mock:
        success &= run_mock_tests()
    
    if args.history:
        success &= run_history_tests()
    
    if args.all:
        success &= run_all_tests()
    
    # If no specific tests requested, show summary
    if not any([args.unit, args.integration, args.xagent, args.react, args.mock, args.history, args.all]):
        show_test_summary()
        print("\n💡 Use --help to see available options")
        return
    
    # Exit with appropriate code
    if success:
        print("\n🎉 All requested tests completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Please check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
