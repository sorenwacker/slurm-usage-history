#!/bin/bash
set -e

# SLURM Usage History Exporter - Installation Script
# This script installs the SLURM usage history exporter tool on a cluster node

INSTALL_DIR="/opt/slurm-usage-history-exporter"
CONFIG_DIR="/etc/slurm-usage-history-exporter"
BIN_DIR="/usr/local/bin"
SERVICE_DIR="/etc/systemd/system"

echo "========================================="
echo "SLURM Usage History Exporter - Installation"
echo "========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root"
    echo "Please run: sudo $0"
    exit 1
fi

# Check if SLURM is installed
if ! command -v sacct &> /dev/null; then
    echo "WARNING: sacct command not found"
    echo "Please ensure SLURM client tools are installed"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Found Python version: $PYTHON_VERSION"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "ERROR: pip3 is not installed"
    echo "Please install pip3"
    exit 1
fi

echo ""
echo "Step 1: Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
echo "  - Created $INSTALL_DIR"
echo "  - Created $CONFIG_DIR"

echo ""
echo "Step 2: Installing Python dependencies..."
pip3 install -r requirements.txt --quiet
echo "  - Dependencies installed"

echo ""
echo "Step 3: Installing exporter script..."
cp slurm-usage-history-exporter.py "$INSTALL_DIR/slurm-usage-history-exporter.py"
chmod +x "$INSTALL_DIR/slurm-usage-history-exporter.py"
ln -sf "$INSTALL_DIR/slurm-usage-history-exporter.py" "$BIN_DIR/slurm-usage-history-exporter"
echo "  - Installed to $INSTALL_DIR"
echo "  - Created symlink in $BIN_DIR"

echo ""
echo "Step 4: Setting up configuration..."
if [ ! -f "$CONFIG_DIR/config.json" ]; then
    cp config.json.example "$CONFIG_DIR/config.json"
    echo "  - Created $CONFIG_DIR/config.json from template"
    echo ""
    echo "  ⚠️  IMPORTANT: You must edit the configuration file!"
    echo "     Edit: $CONFIG_DIR/config.json"
    echo "     Set your dashboard URL and API key"
else
    echo "  - Configuration file already exists, skipping"
fi

echo ""
echo "Step 5: Installing systemd service and timer..."
if [ -f "slurm-usage-history-exporter.service" ]; then
    cp slurm-usage-history-exporter.service "$SERVICE_DIR/slurm-usage-history-exporter.service"
    cp slurm-usage-history-exporter.timer "$SERVICE_DIR/slurm-usage-history-exporter.timer"
    systemctl daemon-reload
    echo "  - Service installed to $SERVICE_DIR"
    echo ""
    echo "  To enable automatic collection:"
    echo "    systemctl enable slurm-usage-history-exporter.timer"
    echo "    systemctl start slurm-usage-history-exporter.timer"
    echo ""
    echo "  To run manually:"
    echo "    systemctl start slurm-usage-history-exporter.service"
else
    echo "  - Systemd files not found, skipping"
fi

echo ""
echo "Step 6: Setting permissions..."
chmod 600 "$CONFIG_DIR/config.json"
chown root:root "$CONFIG_DIR/config.json"
echo "  - Configuration secured"

echo ""
echo "========================================="
echo "Installation complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Edit configuration: $CONFIG_DIR/config.json"
echo "     Set your dashboard URL and API key"
echo ""
echo "  2. Test the exporter:"
echo "     slurm-usage-history-exporter --dry-run --verbose"
echo ""
echo "  3. Submit data manually:"
echo "     slurm-usage-history-exporter"
echo ""
echo "  4. Enable automatic collection (optional):"
echo "     systemctl enable slurm-usage-history-exporter.timer"
echo "     systemctl start slurm-usage-history-exporter.timer"
echo ""
echo "  5. Check service status:"
echo "     systemctl status slurm-usage-history-exporter.timer"
echo "     journalctl -u slurm-usage-history-exporter.service -f"
echo ""
echo "For more information, see README.md"
