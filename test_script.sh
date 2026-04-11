#!/bin/bash

# Basic Bash Test Script
# This script demonstrates common bash operations

echo "=== Bash Script Test ==="
echo "Current directory: $(pwd)"
echo "Current user: $(whoami)"
echo "Current date: $(date)"

# Variables
NAME="Nexthink"
VERSION="1.0"
echo "Script: $NAME v$VERSION"

# Array operations
SERVERS=("server1" "server2" "server3")
echo "Servers: ${SERVERS[@]}"

# Conditional logic
if [ -f "README.md" ]; then
    echo "README.md file exists"
else
    echo "README.md file not found"
fi

# Loop through array
for server in "${SERVERS[@]}"; do
    echo "  - Processing: $server"
done

# Function
greet() {
    echo "Hello, $1!"
}

greet "World"

# Exit successfully
exit 0
