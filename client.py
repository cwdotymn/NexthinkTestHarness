#!/usr/bin/env python3
"""
Client script for testing the Nexthink Test Harness
Use this to easily test endpoints without curl
"""

import requests
import json
import argparse
import sys
from examples import get_example_scripts

BASE_URL = "http://localhost:5000"


def print_response(response):
    """Pretty print API response"""
    print(f"Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)


def execute_powershell(script, args=None):
    """Execute a PowerShell script"""
    payload = {"script": script}
    if args:
        payload["args"] = args
    
    response = requests.post(f"{BASE_URL}/api/execute/powershell", json=payload)
    print_response(response)


def execute_bash(script, args=None):
    """Execute a bash script"""
    payload = {"script": script}
    if args:
        payload["args"] = args
    
    response = requests.post(f"{BASE_URL}/api/execute/bash", json=payload)
    print_response(response)


def get_device_info():
    """Get device information"""
    response = requests.get(f"{BASE_URL}/api/nexthink/device")
    print_response(response)


def get_persona_info(persona_id):
    """Get persona information"""
    response = requests.get(f"{BASE_URL}/api/nexthink/persona/{persona_id}")
    print_response(response)


def simulate_action(action_id, success=True):
    """Simulate a Nexthink action"""
    payload = {"action_id": action_id, "success": success}
    response = requests.post(f"{BASE_URL}/api/nexthink/action", json=payload)
    print_response(response)


def run_example(shell, example_name):
    """Run a pre-built example script"""
    examples = get_example_scripts()
    
    if shell not in examples:
        print(f"Error: Unknown shell '{shell}'. Use 'powershell' or 'bash'")
        return
    
    if example_name not in examples[shell]:
        print(f"Error: Unknown example '{example_name}'")
        print(f"\nAvailable {shell} examples:")
        for name, info in examples[shell].items():
            print(f"  - {name}: {info['description']}")
        return
    
    script = examples[shell][example_name]["script"]
    
    if shell == "powershell":
        execute_powershell(script)
    else:
        execute_bash(script)


def main():
    parser = argparse.ArgumentParser(description="Nexthink Test Harness Client")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # PowerShell command
    ps_parser = subparsers.add_parser("powershell", help="Execute PowerShell script")
    ps_parser.add_argument("script", help="PowerShell script to execute")
    ps_parser.add_argument("--args", nargs="+", help="Arguments to pass to script")
    
    # Bash command
    bash_parser = subparsers.add_parser("bash", help="Execute bash script")
    bash_parser.add_argument("script", help="Bash script to execute")
    bash_parser.add_argument("--args", nargs="+", help="Arguments to pass to script")
    
    # Device info command
    subparsers.add_parser("device", help="Get device information")
    
    # Persona info command
    persona_parser = subparsers.add_parser("persona", help="Get persona information")
    persona_parser.add_argument("persona_id", help="Persona ID")
    
    # Action simulation command
    action_parser = subparsers.add_parser("action", help="Simulate Nexthink action")
    action_parser.add_argument("action_id", help="Action ID")
    action_parser.add_argument("--fail", action="store_true", help="Simulate failure")
    
    # Example command
    example_parser = subparsers.add_parser("example", help="Run a pre-built example")
    example_parser.add_argument("shell", choices=["powershell", "bash"], help="Shell type")
    example_parser.add_argument("name", help="Example name")
    
    # List examples command
    subparsers.add_parser("list-examples", help="List all available examples")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "powershell":
            execute_powershell(args.script, args.args)
        elif args.command == "bash":
            execute_bash(args.script, args.args)
        elif args.command == "device":
            get_device_info()
        elif args.command == "persona":
            get_persona_info(args.persona_id)
        elif args.command == "action":
            simulate_action(args.action_id, success=not args.fail)
        elif args.command == "example":
            run_example(args.shell, args.name)
        elif args.command == "list-examples":
            examples = get_example_scripts()
            print("Available Examples:\n")
            for shell, scripts in examples.items():
                print(f"{shell.upper()}:")
                for name, info in scripts.items():
                    print(f"  {name}: {info['description']}")
            print("\nRun with: python client.py example <shell> <name>")
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to test harness at", BASE_URL)
        print("Make sure the app is running: python app.py")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
