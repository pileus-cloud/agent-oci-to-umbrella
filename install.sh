#!/bin/bash
set -e

# Oracle FOCUS Agent Installation Script
# For Linux systems (Ubuntu, RHEL, CentOS, etc.)

AGENT_USER="oracle-agent"
AGENT_GROUP="oracle-agent"
INSTALL_DIR="/opt/oracle-focus-agent"
CONFIG_DIR="/etc/oracle-focus-agent"
LOG_DIR="/var/log/oracle-focus-agent"
STATE_DIR="/var/lib/oracle-focus-agent"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================================="
echo "Oracle FOCUS to Umbrella BYOD Transfer Agent"
echo "Installation Script v1.0.0"
echo "=================================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root${NC}"
    echo "Please run: sudo ./install.sh"
    exit 1
fi

# Detect Linux distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    OS_VERSION=$VERSION_ID
else
    echo -e "${RED}Error: Cannot detect Linux distribution${NC}"
    exit 1
fi

echo -e "${GREEN}Detected OS: $OS $OS_VERSION${NC}"
echo ""

# Check Python version
echo "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo -e "${GREEN}Found Python $PYTHON_VERSION${NC}"

    # Check if version is >= 3.8
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        echo -e "${RED}Error: Python 3.8 or higher is required${NC}"
        echo "Current version: $PYTHON_VERSION"
        exit 1
    fi
else
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    echo "Please install Python 3.8 or higher first"
    exit 1
fi

# Check pip
echo "Checking pip installation..."
if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}pip3 is installed${NC}"
else
    echo -e "${YELLOW}Installing pip3...${NC}"
    if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        apt-get update
        apt-get install -y python3-pip
    elif [ "$OS" = "rhel" ] || [ "$OS" = "centos" ] || [ "$OS" = "fedora" ]; then
        yum install -y python3-pip
    else
        echo -e "${RED}Error: Cannot install pip3 automatically${NC}"
        exit 1
    fi
fi
echo ""

# Create user and group
echo "Creating service user..."
if ! id -u $AGENT_USER > /dev/null 2>&1; then
    useradd --system --no-create-home --shell /bin/false $AGENT_USER
    echo -e "${GREEN}Created user: $AGENT_USER${NC}"
else
    echo -e "${YELLOW}User $AGENT_USER already exists${NC}"
fi
echo ""

# Create directories
echo "Creating directories..."
mkdir -p $INSTALL_DIR
mkdir -p $CONFIG_DIR
mkdir -p $LOG_DIR
mkdir -p $STATE_DIR

# Set ownership
chown -R $AGENT_USER:$AGENT_GROUP $INSTALL_DIR
chown -R $AGENT_USER:$AGENT_GROUP $LOG_DIR
chown -R $AGENT_USER:$AGENT_GROUP $STATE_DIR
chown -R root:root $CONFIG_DIR
chmod 755 $CONFIG_DIR

echo -e "${GREEN}Directories created:${NC}"
echo "  - $INSTALL_DIR"
echo "  - $CONFIG_DIR"
echo "  - $LOG_DIR"
echo "  - $STATE_DIR"
echo ""

# Install the package
echo "Installing Oracle FOCUS Agent..."
if [ -f "dist/oracle_focus_agent-1.0.0-py3-none-any.whl" ]; then
    pip3 install --upgrade dist/oracle_focus_agent-1.0.0-py3-none-any.whl
    echo -e "${GREEN}Package installed successfully${NC}"
else
    echo -e "${RED}Error: Package file not found${NC}"
    echo "Please ensure dist/oracle_focus_agent-1.0.0-py3-none-any.whl exists"
    exit 1
fi
echo ""

# Copy config template
echo "Setting up configuration..."
if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
    if [ -f "config.template.yaml" ]; then
        cp config.template.yaml $CONFIG_DIR/config.yaml
        chmod 600 $CONFIG_DIR/config.yaml
        chown root:root $CONFIG_DIR/config.yaml
        echo -e "${GREEN}Configuration template copied to $CONFIG_DIR/config.yaml${NC}"
        echo -e "${YELLOW}IMPORTANT: Edit $CONFIG_DIR/config.yaml with your settings${NC}"
    else
        echo -e "${YELLOW}Warning: config.template.yaml not found${NC}"
    fi
else
    echo -e "${YELLOW}Configuration file already exists at $CONFIG_DIR/config.yaml${NC}"
fi
echo ""

# Install systemd service
echo "Installing systemd service..."
if [ -f "systemd/oracle-focus-agent.service" ]; then
    # Update service file with actual paths
    sed -e "s|/opt/oracle-focus-agent|$INSTALL_DIR|g" \
        -e "s|/etc/oracle-focus-agent/config.yaml|$CONFIG_DIR/config.yaml|g" \
        systemd/oracle-focus-agent.service > /etc/systemd/system/oracle-focus-agent.service

    chmod 644 /etc/systemd/system/oracle-focus-agent.service
    systemctl daemon-reload
    echo -e "${GREEN}Systemd service installed${NC}"
else
    echo -e "${YELLOW}Warning: systemd service file not found${NC}"
fi
echo ""

# Test installation
echo "Testing installation..."
if command -v oracle-focus-agent &> /dev/null; then
    echo -e "${GREEN}oracle-focus-agent command is available${NC}"
    oracle-focus-agent --help > /dev/null 2>&1
    echo -e "${GREEN}Installation test passed${NC}"
else
    echo -e "${RED}Error: oracle-focus-agent command not found${NC}"
    exit 1
fi
echo ""

echo "=================================================="
echo -e "${GREEN}Installation completed successfully!${NC}"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Edit configuration:"
echo "   sudo nano $CONFIG_DIR/config.yaml"
echo ""
echo "2. Configure OCI credentials:"
echo "   sudo mkdir -p /root/.oci"
echo "   sudo nano /root/.oci/config"
echo ""
echo "3. Configure AWS credentials:"
echo "   sudo mkdir -p /root/.aws"
echo "   sudo nano /root/.aws/credentials"
echo ""
echo "4. Update log and state paths in config.yaml:"
echo "   logs:"
echo "     file: \"$LOG_DIR/agent.log\""
echo "   state:"
echo "     file: \"$STATE_DIR/state.json\""
echo ""
echo "5. Test configuration:"
echo "   sudo oracle-focus-agent test --config $CONFIG_DIR/config.yaml"
echo ""
echo "6. Enable and start service:"
echo "   sudo systemctl enable oracle-focus-agent"
echo "   sudo systemctl start oracle-focus-agent"
echo ""
echo "7. Check service status:"
echo "   sudo systemctl status oracle-focus-agent"
echo ""
echo "8. View logs:"
echo "   sudo journalctl -u oracle-focus-agent -f"
echo "   tail -f $LOG_DIR/agent.log"
echo ""
echo "=================================================="
