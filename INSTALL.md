# Oracle FOCUS Agent - Installation Package

Complete installation package for deploying the Oracle FOCUS to Umbrella BYOD Transfer Agent on any Linux system.

## Package Contents

```
oracle-focus-agent/
├── dist/
│   ├── oracle_focus_agent-1.0.0-py3-none-any.whl    # Python wheel package
│   └── oracle_focus_agent-1.0.0.tar.gz              # Source distribution
├── systemd/
│   └── oracle-focus-agent.service                    # Systemd service file
├── install.sh                                        # Automated installation script
├── config.template.yaml                              # Configuration template
├── INSTALL.md                                        # This file
└── README.md                                         # Project documentation
```

## Quick Installation

### Prerequisites

- Linux system (Ubuntu, RHEL, CentOS, Debian, Fedora)
- Python 3.8 or higher
- Root/sudo access
- Internet connection

### Automated Installation (Recommended)

1. **Extract the package:**
   ```bash
   tar -xzf oracle-focus-agent-1.0.0.tar.gz
   cd oracle-focus-agent
   ```

2. **Run the installation script:**
   ```bash
   sudo ./install.sh
   ```

   This script will:
   - Check Python version (requires 3.8+)
   - Install pip3 if needed
   - Create service user (`oracle-agent`)
   - Create required directories
   - Install the Python package
   - Copy configuration template
   - Install systemd service
   - Test the installation

3. **Configure credentials and settings:**
   ```bash
   # Edit main configuration
   sudo nano /etc/oracle-focus-agent/config.yaml

   # Setup OCI credentials
   sudo mkdir -p /root/.oci
   sudo nano /root/.oci/config

   # Setup AWS credentials
   sudo mkdir -p /root/.aws
   sudo nano /root/.aws/credentials
   ```

4. **Test configuration:**
   ```bash
   sudo oracle-focus-agent test --config /etc/oracle-focus-agent/config.yaml
   ```

5. **Enable and start the service:**
   ```bash
   sudo systemctl enable oracle-focus-agent
   sudo systemctl start oracle-focus-agent
   ```

6. **Verify it's running:**
   ```bash
   sudo systemctl status oracle-focus-agent
   ```

## Manual Installation

If you prefer manual installation or the automated script doesn't work on your system:

### 1. Install Python Package

```bash
# Using wheel (recommended)
sudo pip3 install dist/oracle_focus_agent-1.0.0-py3-none-any.whl

# Or using source distribution
sudo pip3 install dist/oracle_focus_agent-1.0.0.tar.gz

# Verify installation
oracle-focus-agent --help
```

### 2. Create Service User

```bash
sudo useradd --system --no-create-home --shell /bin/false oracle-agent
```

### 3. Create Directories

```bash
sudo mkdir -p /opt/oracle-focus-agent
sudo mkdir -p /etc/oracle-focus-agent
sudo mkdir -p /var/log/oracle-focus-agent
sudo mkdir -p /var/lib/oracle-focus-agent

sudo chown oracle-agent:oracle-agent /opt/oracle-focus-agent
sudo chown oracle-agent:oracle-agent /var/log/oracle-focus-agent
sudo chown oracle-agent:oracle-agent /var/lib/oracle-focus-agent
```

### 4. Setup Configuration

```bash
# Copy template
sudo cp config.template.yaml /etc/oracle-focus-agent/config.yaml
sudo chmod 600 /etc/oracle-focus-agent/config.yaml

# Edit configuration
sudo nano /etc/oracle-focus-agent/config.yaml
```

**Important:** Update these settings in config.yaml:

```yaml
oci:
  namespace: "bling"                    # Oracle billing namespace
  bucket: "ocid1.tenancy.oc1..YOUR_TENANCY_OCID"
  prefix: "FOCUS Reports/"

s3:
  bucket_path: "s3://your-umbrella-bucket/your-path"
  region: "us-east-1"

agent:
  poll_interval: 600                    # 10 minutes
  lookback_days: 1

logging:
  file: "/var/log/oracle-focus-agent/agent.log"

state:
  file: "/var/lib/oracle-focus-agent/state.json"
```

### 5. Configure OCI Credentials

Create `/root/.oci/config`:

```ini
[DEFAULT]
user=ocid1.user.oc1..YOUR_USER_OCID
fingerprint=aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99
tenancy=ocid1.tenancy.oc1..YOUR_TENANCY_OCID
region=us-ashburn-1
key_file=/root/.oci/oci_api_key.pem
```

Copy your private key:
```bash
sudo cp /path/to/your/oci_api_key.pem /root/.oci/
sudo chmod 600 /root/.oci/oci_api_key.pem
```

### 6. Configure AWS Credentials

Create `/root/.aws/credentials`:

```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
```

```bash
sudo chmod 600 /root/.aws/credentials
```

### 7. Install Systemd Service

```bash
sudo cp systemd/oracle-focus-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### 8. Test and Start

```bash
# Test configuration
sudo oracle-focus-agent test --config /etc/oracle-focus-agent/config.yaml

# Enable auto-start
sudo systemctl enable oracle-focus-agent

# Start service
sudo systemctl start oracle-focus-agent

# Check status
sudo systemctl status oracle-focus-agent
```

## Installation Locations

After installation, files are located at:

| Component | Location |
|-----------|----------|
| Binary | `/usr/local/bin/oracle-focus-agent` |
| Configuration | `/etc/oracle-focus-agent/config.yaml` |
| OCI Credentials | `/root/.oci/config` |
| AWS Credentials | `/root/.aws/credentials` |
| Logs | `/var/log/oracle-focus-agent/agent.log` |
| State | `/var/lib/oracle-focus-agent/state.json` |
| Systemd Service | `/etc/systemd/system/oracle-focus-agent.service` |
| PID File | `/tmp/oracle-focus-agent.pid` |

## Testing the Installation

### 1. Test Configuration
```bash
sudo oracle-focus-agent test --config /etc/oracle-focus-agent/config.yaml
```

Expected output:
```
✓ OCI connectivity: OK
✓ S3 connectivity: OK
✓ All tests passed!
```

### 2. Test Manual Sync
```bash
sudo oracle-focus-agent sync --config /etc/oracle-focus-agent/config.yaml
```

### 3. Check Service Status
```bash
# View service status
sudo systemctl status oracle-focus-agent

# View real-time logs
sudo journalctl -u oracle-focus-agent -f

# View agent logs
sudo tail -f /var/log/oracle-focus-agent/agent.log
```

## Service Management

### Start/Stop/Restart
```bash
sudo systemctl start oracle-focus-agent
sudo systemctl stop oracle-focus-agent
sudo systemctl restart oracle-focus-agent
```

### Enable/Disable Auto-Start
```bash
sudo systemctl enable oracle-focus-agent   # Start on boot
sudo systemctl disable oracle-focus-agent  # Don't start on boot
```

### View Logs
```bash
# Systemd journal
sudo journalctl -u oracle-focus-agent -f

# Agent log file
sudo tail -f /var/log/oracle-focus-agent/agent.log

# View last 100 lines
sudo journalctl -u oracle-focus-agent -n 100
```

## Upgrading

To upgrade to a newer version:

```bash
# Stop the service
sudo systemctl stop oracle-focus-agent

# Install new version
sudo pip3 install --upgrade dist/oracle_focus_agent-1.0.1-py3-none-any.whl

# Restart service
sudo systemctl start oracle-focus-agent

# Verify
sudo systemctl status oracle-focus-agent
```

## Uninstalling

```bash
# Stop and disable service
sudo systemctl stop oracle-focus-agent
sudo systemctl disable oracle-focus-agent

# Remove systemd service
sudo rm /etc/systemd/system/oracle-focus-agent.service
sudo systemctl daemon-reload

# Uninstall Python package
sudo pip3 uninstall oracle-focus-agent

# Remove directories (optional - removes logs and state)
sudo rm -rf /opt/oracle-focus-agent
sudo rm -rf /var/log/oracle-focus-agent
sudo rm -rf /var/lib/oracle-focus-agent
sudo rm -rf /etc/oracle-focus-agent

# Remove user (optional)
sudo userdel oracle-agent
```

## Troubleshooting

### Installation Issues

**Problem:** Python version too old
```bash
# Check Python version
python3 --version

# Install Python 3.8+ on Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3.8 python3.8-pip

# Install Python 3.8+ on RHEL/CentOS
sudo yum install python38 python38-pip
```

**Problem:** pip3 not found
```bash
# Ubuntu/Debian
sudo apt-get install python3-pip

# RHEL/CentOS
sudo yum install python3-pip
```

**Problem:** Permission denied during installation
```bash
# Make sure you're running with sudo
sudo ./install.sh
```

### Service Issues

**Problem:** Service fails to start
```bash
# Check detailed error
sudo journalctl -u oracle-focus-agent -n 50

# Check configuration
sudo oracle-focus-agent test --config /etc/oracle-focus-agent/config.yaml

# Verify file permissions
sudo ls -la /etc/oracle-focus-agent/
sudo ls -la /root/.oci/
sudo ls -la /root/.aws/
```

**Problem:** Permission denied accessing credentials
```bash
# Fix OCI credentials permissions
sudo chmod 600 /root/.oci/config
sudo chmod 600 /root/.oci/oci_api_key.pem

# Fix AWS credentials permissions
sudo chmod 600 /root/.aws/credentials
```

**Problem:** No files discovered
```bash
# Verify OCI namespace is "bling" (not your tenancy namespace)
# Verify bucket name is your tenancy OCID
# Check config.yaml settings
sudo cat /etc/oracle-focus-agent/config.yaml | grep -A5 "oci:"
```

## Security Considerations

1. **Credentials:** Store credentials securely with proper permissions (600)
2. **Service User:** Runs as dedicated `oracle-agent` user (not root)
3. **File Permissions:** Config files readable only by root
4. **Network:** Ensure firewall allows outbound HTTPS to OCI and AWS
5. **Logs:** Contain no sensitive information, safe to share for debugging

## Support

For issues or questions:
1. Check logs: `/var/log/oracle-focus-agent/agent.log`
2. Test configuration: `sudo oracle-focus-agent test --config /etc/oracle-focus-agent/config.yaml`
3. Review documentation: `README.md`, `QUICKSTART.md`
4. Check GitHub issues: https://github.com/pileus-cloud/oracle-focus-agent/issues

## Additional Resources

- **Full Documentation:** README.md
- **Quick Start Guide:** QUICKSTART.md
- **Requirements:** REQUIREMENTS.md
- **Architecture:** DESIGN.md
- **HTML Installation Guide:** INSTALLATION_GUIDE.html
