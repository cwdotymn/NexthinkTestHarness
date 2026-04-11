#!/usr/bin/env python3
"""
Quick start examples for the Nexthink Test Harness
Run this script to see common usage patterns
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}\n")

def run_examples():
    """Run example API calls"""
    
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("Error: Server is not responding. Start the app with: python app.py")
            return
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to server at", BASE_URL)
        print("Start the app with: python app.py")
        return
    
    # Example 1: Health Check
    print_section("1. Health Check")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    
    # Example 2: Get Device Info
    print_section("2. Get Device Information")
    response = requests.get(f"{BASE_URL}/api/nexthink/device")
    print(f"Status: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    
    # Example 3: Get Persona Info
    print_section("3. Get Persona Information")
    persona_id = "persona-001"
    response = requests.get(f"{BASE_URL}/api/nexthink/persona/{persona_id}")
    print(f"Status: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    
    # Example 4: Execute Bash Script
    print_section("4. Execute Bash Script - whoami")
    bash_script = "whoami"
    response = requests.post(
        f"{BASE_URL}/api/execute/bash",
        json={"script": bash_script}
    )
    print(f"Status: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    
    # Example 5: Execute Bash Script with Output
    print_section("5. Execute Bash Script - System Info")
    bash_script = """
echo "System Information:"
echo "Date: $(date)"
echo "Uptime: $(uptime)"
echo "Free Memory: $(free -h | grep Mem)"
"""
    response = requests.post(
        f"{BASE_URL}/api/execute/bash",
        json={"script": bash_script}
    )
    print(f"Status: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    
    # Example 6: Execute Bash Script with Error
    print_section("6. Execute Bash Script - Simulated Error")
    bash_script = "exit 1"
    response = requests.post(
        f"{BASE_URL}/api/execute/bash",
        json={"script": bash_script}
    )
    print(f"Status: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    
    # Example 7: Simulate Nexthink Action (Success)
    print_section("7. Simulate Nexthink Action - Success")
    response = requests.post(
        f"{BASE_URL}/api/nexthink/action",
        json={"action_id": "action-success-001", "success": True}
    )
    print(f"Status: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    
    # Example 8: Simulate Nexthink Action (Failure)
    print_section("8. Simulate Nexthink Action - Failure")
    response = requests.post(
        f"{BASE_URL}/api/nexthink/action",
        json={"action_id": "action-failure-001", "success": False}
    )
    print(f"Status: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    
    # Example 9: Test Invalid Request
    print_section("9. Test Invalid Request - Missing Parameter")
    response = requests.post(
        f"{BASE_URL}/api/execute/bash",
        json={}
    )
    print(f"Status: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    
    print_section("Examples Complete")
    print("For more examples, check the README.md or run:")
    print("  python client.py list-examples")
    print("  python client.py example bash system_info")


if __name__ == "__main__":
    run_examples()
