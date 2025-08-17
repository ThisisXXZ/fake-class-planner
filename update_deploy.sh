#!/bin/bash

# Update deployment script for Class Planner application
# Run with: sudo bash update_deploy.sh

echo "Class Planner Update Deployment Script"
echo "======================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
   echo "Please run as root (use sudo)"
   exit 1
fi

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Working directory: $SCRIPT_DIR"

# Step 1: Pull latest code from GitHub
echo ""
echo "Step 1: Pulling latest code from GitHub..."
sudo -u ubuntu git pull origin main
if [ $? -ne 0 ]; then
    echo "Error: Failed to pull from GitHub"
    exit 1
fi
echo "✓ Code updated successfully"

# Step 2: Install/update dependencies
echo ""
echo "Step 2: Installing/updating dependencies..."
if command -v uv &> /dev/null; then
    sudo -u ubuntu uv sync
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies"
        exit 1
    fi
    echo "✓ Dependencies updated successfully"
else
    echo "Warning: uv not found, skipping dependency update"
fi

# Step 3: Restart the service
echo ""
echo "Step 3: Restarting Class Planner service..."
systemctl restart class-planner
if [ $? -ne 0 ]; then
    echo "Error: Failed to restart service"
    exit 1
fi

# Wait a moment for service to start
sleep 2

# Step 4: Check service status
echo ""
echo "Step 4: Checking service status..."
if systemctl is-active --quiet class-planner; then
    echo "✓ Class Planner service is running"
else
    echo "✗ Class Planner service failed to start"
    echo "Check logs with: journalctl -u class-planner -n 50"
    exit 1
fi

# Step 5: Reload nginx (in case of config changes)
echo ""
echo "Step 5: Reloading nginx..."
nginx -t && systemctl reload nginx
if [ $? -eq 0 ]; then
    echo "✓ nginx reloaded successfully"
else
    echo "Warning: nginx reload failed, but service is running"
fi

# Display status
echo ""
echo "======================================="
echo "Update Deployment Complete!"
echo "======================================="
echo ""
echo "Changes have been deployed successfully."
echo "The application should be accessible at:"
echo "http://YOUR_DOMAIN_OR_IP/class-planner"
echo ""
echo "Recent logs:"
journalctl -u class-planner -n 10 --no-pager