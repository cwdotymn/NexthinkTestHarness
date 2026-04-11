#!/usr/bin/env bash

set -e

echo "================================"
echo "Nexthink Test Harness Setup"
echo "================================"
echo ""

# Check Python version
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $PYTHON_VERSION"
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "Dependencies installed"
echo ""

# Install pytest for testing
echo "Installing test dependencies..."
pip install pytest
echo ""

# Create test scripts directory
mkdir -p test_scripts
echo "Created test_scripts directory"
echo ""

echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "To start the application, run:"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
echo "In another terminal, you can test with:"
echo "  python client.py list-examples"
echo "  python client.py device"
echo "  python client.py example bash system_info"
echo ""
echo "Or run the test suite with:"
echo "  pytest -v"
echo ""
