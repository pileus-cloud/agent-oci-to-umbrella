# Oracle FOCUS to Umbrella BYOD Transfer Agent

Automated daemon agent that transfers FOCUS cost report files from Oracle Cloud Infrastructure (OCI) Object Storage to Umbrella's BYOD S3 bucket.

## Features

- **Automated Transfers**: Polls OCI every 10 minutes for new FOCUS files
- **Streaming Transfer**: Efficiently transfers files up to 5GB without loading into memory
- **State Tracking**: Avoids re-transferring unchanged files
- **Parallel Processing**: Configurable concurrent transfers for optimal performance
- **Daemon Mode**: Runs continuously in background with graceful shutdown
- **CLI Interface**: Multiple commands for different operational modes

## Quick Start

### 1. Installation

```bash
pip install -r requirements.txt
pip install -e .
```

### 2. Configuration

Copy the template configuration:
```bash
cp config.template.yaml config.yaml
```

Edit `config.yaml` with your settings or use the pre-configured `config.testing.yaml` for David's testing environment.

### 3. Setup Credentials

**OCI Credentials**: Already configured in `~/.oci/config`

**AWS Credentials**: Set environment variables or use `~/.aws/credentials`
```bash
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
```

Or use AWS CLI:
```bash
aws configure
```

### 4. Test Configuration

```bash
oracle-focus-agent test --config config.yaml
```

### 5. Run Agent

**Foreground (for testing):**
```bash
oracle-focus-agent run --config config.yaml
```

**Background (daemon mode):**
```bash
oracle-focus-agent start --config config.yaml
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `start` | Start daemon in background |
| `stop` | Stop running daemon |
| `run` | Run in foreground (Ctrl+C to stop) |
| `test` | Test configuration and connectivity |
| `sync` | Perform one-time sync and exit |
| `status` | Check daemon status |

## Configuration

See `config.template.yaml` for all available options:

- **OCI Settings**: Namespace, bucket, prefix
- **S3 Settings**: Bucket path, region
- **Agent Settings**: Poll interval, lookback days, concurrency
- **Retry Settings**: Max retries, backoff strategy
- **Logging**: Level, file rotation
- **State Management**: Persistence, retention
- **File Naming**: Date format, separator

## File Naming Convention

Files are transferred with date-prefixed names:

- **Oracle**: `FOCUS Reports/2024/11/28/0001000002103533-00001.csv.gz`
- **S3**: `2024-11-28_0001000002103533-00001.csv.gz`

## Architecture

The agent consists of 9 modular components:

1. **CLI Interface**: Command parsing and routing
2. **Daemon Manager**: Process lifecycle management
3. **Scheduler**: Periodic sync triggering
4. **Transfer Orchestrator**: File discovery and transfer coordination
5. **OCI Client**: Oracle Cloud Infrastructure API
6. **S3 Client**: AWS S3 API
7. **Config Manager**: Configuration loading and validation
8. **State Manager**: Transfer state persistence
9. **Logger**: Centralized logging

## Documentation

- [Requirements](REQUIREMENTS.md)
- [Design Document](DESIGN.md)
- [OCI Setup Guide](docs/OCI_SETUP.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Configuration Reference](docs/CONFIG_REFERENCE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## Development

### Running Tests

```bash
pytest tests/
```

### Project Structure

```
oracle-byod/
├── oracle_focus_agent/    # Main package
│   ├── cli.py            # CLI interface
│   ├── daemon.py         # Daemon management
│   ├── scheduler.py      # Scheduling logic
│   ├── orchestrator.py   # Transfer orchestration
│   ├── oci_client.py     # OCI API client
│   ├── s3_client.py      # S3 API client
│   ├── config.py         # Configuration management
│   ├── state.py          # State management
│   └── logger.py         # Logging setup
├── tests/                # Unit tests
├── docs/                 # Documentation
├── config.template.yaml  # Configuration template
└── config.testing.yaml   # Testing configuration
```

## License

Copyright (c) 2024 Umbrella Cost
