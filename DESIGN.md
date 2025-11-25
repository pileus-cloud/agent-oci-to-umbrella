# Oracle FOCUS to Umbrella BYOD Transfer Agent - Design Document

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Component Design](#component-design)
3. [Data Flow](#data-flow)
4. [File Processing Logic](#file-processing-logic)
5. [State Management](#state-management)
6. [Error Handling](#error-handling)
7. [Configuration](#configuration)
8. [CLI Interface](#cli-interface)
9. [Implementation Plan](#implementation-plan)

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Oracle FOCUS Agent                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────┐      ┌──────────────┐      ┌──────────────┐      │
│  │    CLI     │─────▶│   Daemon     │─────▶│   Scheduler  │      │
│  │  Interface │      │   Manager    │      │              │      │
│  └────────────┘      └──────────────┘      └──────┬───────┘      │
│                                                     │              │
│                                                     ▼              │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    Transfer Orchestrator                     │ │
│  │  - Discovers files from OCI                                  │ │
│  │  - Filters by date range                                     │ │
│  │  - Manages transfer queue                                    │ │
│  │  - Tracks state                                              │ │
│  └──────────┬──────────────────────────────────────┬────────────┘ │
│             │                                       │              │
│             ▼                                       ▼              │
│  ┌────────────────────┐                 ┌────────────────────┐   │
│  │  OCI Client        │                 │  S3 Client         │   │
│  │  - List objects    │                 │  - Upload files    │   │
│  │  - Download files  │                 │  - Stream upload   │   │
│  │  - Stream data     │                 │  - Validate        │   │
│  └────────────────────┘                 └────────────────────┘   │
│                                                                    │
│  ┌────────────────────┐  ┌────────────────────┐  ┌─────────────┐ │
│  │ Config Manager     │  │  State Manager     │  │  Logger     │ │
│  └────────────────────┘  └────────────────────┘  └─────────────┘ │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

1. **CLI Interface**: Parse command-line arguments, dispatch commands
2. **Daemon Manager**: Process lifecycle management (start/stop/status)
3. **Scheduler**: Wake up on interval, trigger sync operations
4. **Transfer Orchestrator**: Core logic for file discovery and transfer
5. **OCI Client**: Oracle Cloud Infrastructure API interactions
6. **S3 Client**: AWS S3 API interactions
7. **Config Manager**: Load and validate configuration
8. **State Manager**: Track processed files, manage state persistence
9. **Logger**: Centralized logging with rotation

## Component Design

### 1. CLI Interface (`cli.py`)

```python
class OracleFocusAgentCLI:
    """
    Command-line interface for the Oracle FOCUS agent.

    Commands:
    - start: Start daemon in background
    - stop: Stop running daemon
    - run: Run in foreground
    - test: Test configuration and connectivity
    - sync: Perform one-time sync
    - status: Check daemon status
    """

    def parse_args() -> argparse.Namespace
    def execute_command(args) -> int
```

**Key Features**:
- Argument parsing with `argparse`
- Help documentation
- Config file path specification
- Command routing

### 2. Daemon Manager (`daemon.py`)

```python
class DaemonManager:
    """
    Manages daemon lifecycle using PID files and signal handling.
    """

    def start() -> bool
    def stop() -> bool
    def status() -> Dict[str, Any]
    def is_running() -> bool
    def get_pid() -> Optional[int]
```

**Key Features**:
- PID file management (`/var/run/oracle-focus-agent.pid`)
- Signal handling (SIGTERM, SIGINT)
- Graceful shutdown
- Status reporting

### 3. Scheduler (`scheduler.py`)

```python
class Scheduler:
    """
    Schedules periodic sync operations.
    """

    def __init__(interval_seconds: int)
    def start()
    def stop()
    def run_forever()
    def trigger_sync()
```

**Key Features**:
- Configurable polling interval
- Non-blocking sleep with early wakeup on shutdown
- Error isolation (failures don't stop scheduler)

### 4. Transfer Orchestrator (`orchestrator.py`)

```python
class TransferOrchestrator:
    """
    Orchestrates file discovery, filtering, and transfer.
    """

    def __init__(config, oci_client, s3_client, state_manager)
    def discover_files(date_range: List[datetime]) -> List[FileInfo]
    def filter_files(files: List[FileInfo]) -> List[FileInfo]
    def transfer_files(files: List[FileInfo]) -> TransferStats
    def sync() -> TransferStats
```

**Key Features**:
- Date-based file discovery
- State-based filtering (skip already transferred)
- Parallel transfer support
- Progress tracking
- Metrics collection

### 5. OCI Client (`oci_client.py`)

```python
class OCIClient:
    """
    Oracle Cloud Infrastructure Object Storage client.
    """

    def __init__(config)
    def list_objects(prefix: str) -> List[ObjectSummary]
    def download_object(object_name: str, target_stream: IO) -> int
    def get_object_metadata(object_name: str) -> Dict[str, Any]
```

**Key Features**:
- Uses `oci` Python SDK
- Pagination support for large listings
- Streaming downloads
- Retry with exponential backoff
- Connection pooling

### 6. S3 Client (`s3_client.py`)

```python
class S3Client:
    """
    AWS S3 client for uploading files.
    """

    def __init__(config)
    def upload_stream(key: str, source_stream: IO, size: int) -> bool
    def object_exists(key: str) -> bool
    def get_object_metadata(key: str) -> Dict[str, Any]
```

**Key Features**:
- Uses `boto3` SDK
- Multipart upload for large files
- Streaming upload (no disk buffering)
- Checksum validation
- Retry logic

### 7. Config Manager (`config.py`)

```python
class Config:
    """
    Configuration management with validation.
    """

    @staticmethod
    def load(config_path: str) -> Config

    def validate() -> List[str]
    def get_oci_config() -> Dict[str, Any]
    def get_s3_config() -> Dict[str, Any]
```

**Key Features**:
- YAML parsing
- Schema validation
- Environment variable expansion
- Default values
- Error reporting

### 8. State Manager (`state.py`)

```python
class StateManager:
    """
    Manages transfer state persistence.
    """

    def __init__(state_file: str)
    def load() -> Dict[str, FileState]
    def save()
    def mark_transferred(file_info: FileInfo, stats: TransferStats)
    def is_transferred(file_info: FileInfo) -> bool
    def cleanup_old_records(retention_days: int)
```

**Key Features**:
- JSON-based state file
- File locking for concurrent safety
- Atomic writes
- Record expiration
- Metadata tracking (size, timestamp, checksum)

### 9. Logger (`logger.py`)

```python
def setup_logging(config: Config) -> logging.Logger:
    """
    Configure logging with file rotation.
    """
```

**Key Features**:
- Log level configuration
- File rotation by size
- Console and file output
- Structured logging format
- Correlation IDs for tracking

## Data Flow

### File Discovery and Transfer Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. Scheduler triggers sync every 10 minutes                        │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. Orchestrator calculates date range (current day + lookback)     │
│    Example: 2024-11-28 (current day only)                          │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. For each date, construct OCI prefix:                            │
│    "FOCUS Reports/2024/11/28/"                                      │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. OCIClient lists all objects under prefix                        │
│    Returns: List[ObjectSummary] with name, size, time_created      │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. Filter files:                                                    │
│    - Only .csv.gz files                                             │
│    - Size <= 5GB                                                    │
│    - Not already in state (or state shows older version)           │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 6. For each file (up to max_concurrent_transfers in parallel):     │
│    a. Generate S3 key: "2024-11-28_0001000002103533-00001.csv.gz"  │
│    b. Stream from OCI to S3 (no disk buffering)                    │
│    c. Validate checksum if enabled                                 │
│    d. Update state on success                                      │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 7. Log transfer statistics:                                        │
│    - Files discovered: 5                                            │
│    - Files transferred: 3                                           │
│    - Files skipped: 2 (already transferred)                        │
│    - Data transferred: 125 MB                                       │
│    - Duration: 45 seconds                                           │
└─────────────────────────────────────────────────────────────────────┘
```

### Streaming Transfer Detail

```
OCI Object Storage          Agent Memory         AWS S3
==================         ==============        ======

┌────────────┐
│            │             ┌──────────┐
│ File.csv.gz│────────────▶│  8MB     │─────────▶ Upload
│   (500MB)  │  Stream     │  Buffer  │  Stream   Part 1
│            │  Chunk 1    │          │
└────────────┘             └──────────┘
                                │
                           Immediately
                           flush & reuse
                                │
                                ▼
                           ┌──────────┐
                Stream     │  8MB     │─────────▶ Upload
                Chunk 2    │  Buffer  │  Stream   Part 2
                           │          │
                           └──────────┘

Result: Transfer 500MB file using only 8MB of memory
```

## File Processing Logic

### Date Range Calculation

```python
def calculate_date_range(lookback_days: int) -> List[datetime]:
    """
    Calculate date range to process.

    lookback_days=0: [today]
    lookback_days=1: [yesterday, today]
    lookback_days=2: [day-before-yesterday, yesterday, today]
    """
    today = datetime.now().date()
    dates = []
    for i in range(lookback_days, -1, -1):
        dates.append(today - timedelta(days=i))
    return dates
```

### File Naming Logic

```python
def generate_s3_key(oci_object_name: str, date: datetime, config: Config) -> str:
    """
    Generate S3 key from OCI object name.

    Input:  "FOCUS Reports/2024/11/28/0001000002103533-00001.csv.gz"
    Output: "2024-11-28_0001000002103533-00001.csv.gz"
    """
    basename = os.path.basename(oci_object_name)
    date_prefix = date.strftime(config.naming.date_format)
    separator = config.naming.separator
    return f"{date_prefix}{separator}{basename}"
```

### State Comparison Logic

```python
def should_transfer(file_info: FileInfo, state: Dict[str, FileState]) -> bool:
    """
    Determine if file should be transferred.

    Transfer if:
    1. File not in state (never transferred)
    2. File size changed (updated in OCI)
    3. File timestamp newer (updated in OCI)
    """
    if file_info.s3_key not in state:
        return True

    existing = state[file_info.s3_key]

    # Size changed
    if existing.size != file_info.size:
        return True

    # Timestamp newer
    if file_info.time_created > existing.time_created:
        return True

    return False
```

## State Management

### State File Format

```json
{
  "version": "1.0",
  "last_sync": "2024-11-28T15:30:00Z",
  "files": {
    "2024-11-28_0001000002103533-00001.csv.gz": {
      "oci_object_name": "FOCUS Reports/2024/11/28/0001000002103533-00001.csv.gz",
      "s3_key": "2024-11-28_0001000002103533-00001.csv.gz",
      "size": 218153,
      "time_created": "2024-11-28T10:00:00Z",
      "time_transferred": "2024-11-28T15:30:00Z",
      "checksum_md5": "abc123...",
      "duration_seconds": 12.5
    }
  }
}
```

### State Operations

1. **Load State**: Read state file on startup, handle missing/corrupt files
2. **Check State**: Before each transfer, check if file already processed
3. **Update State**: After successful transfer, add/update file record
4. **Cleanup State**: Periodically remove old records (based on retention_days)
5. **Save State**: Atomic write with temp file + rename

## Error Handling

### Retry Strategy

```python
def transfer_with_retry(file_info: FileInfo, max_retries: int) -> bool:
    """
    Transfer file with exponential backoff retry.
    """
    attempt = 0
    delay = initial_delay

    while attempt < max_retries:
        try:
            transfer_file(file_info)
            return True
        except RetryableError as e:
            attempt += 1
            if attempt >= max_retries:
                raise

            logger.warning(f"Transfer failed (attempt {attempt}), retrying in {delay}s: {e}")
            time.sleep(delay)
            delay = min(delay * backoff_multiplier, max_delay)

    return False
```

### Error Categories

1. **Retryable Errors**:
   - Network timeouts
   - Rate limit errors (429)
   - Temporary service unavailability (503)
   - Connection errors

2. **Non-Retryable Errors**:
   - Authentication failures (401, 403)
   - File not found (404)
   - Invalid configuration
   - File size exceeds limit

3. **Partial Failures**:
   - Continue processing remaining files if one fails
   - Log failed files for manual investigation
   - Include failure count in metrics

### Graceful Shutdown

```python
class GracefulShutdown:
    """
    Handle shutdown signals gracefully.
    """

    def __init__(self):
        self.shutdown_requested = False
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _handle_signal(self, signum, frame):
        logger.info("Shutdown signal received, finishing current transfers...")
        self.shutdown_requested = True

    def should_continue(self) -> bool:
        return not self.shutdown_requested
```

## Configuration

### Configuration Schema

See `config.template.yaml` for full schema with defaults.

### Configuration Validation

```python
def validate_config(config: Config) -> List[str]:
    """
    Validate configuration and return list of errors.
    """
    errors = []

    # OCI validation
    if not config.oci.bucket.startswith("ocid1.tenancy."):
        errors.append("OCI bucket must be a valid tenancy OCID")

    # S3 validation
    if not config.s3.bucket_path.startswith("s3://"):
        errors.append("S3 bucket_path must start with s3://")

    # Agent validation
    if config.agent.poll_interval < 60:
        errors.append("poll_interval must be at least 60 seconds")

    # File validation
    if config.advanced.max_file_size_gb < 1:
        errors.append("max_file_size_gb must be at least 1")

    return errors
```

## CLI Interface

### Command Reference

#### `start`
```bash
oracle-focus-agent start --config config.yaml
```
Start daemon in background. Creates PID file, detaches from terminal.

#### `stop`
```bash
oracle-focus-agent stop
```
Stop running daemon gracefully. Sends SIGTERM, waits for completion.

#### `run`
```bash
oracle-focus-agent run --config config.yaml
```
Run in foreground. Useful for testing and debugging. Logs to console.

#### `test`
```bash
oracle-focus-agent test --config config.yaml
```
Test configuration and connectivity:
- Load and validate config
- Test OCI authentication
- Test S3 authentication
- Attempt to list objects (dry run)

#### `sync`
```bash
oracle-focus-agent sync --config config.yaml
```
Perform one-time sync and exit. Useful for manual triggers or cron jobs.

#### `status`
```bash
oracle-focus-agent status
```
Check daemon status:
- Running/stopped
- PID
- Uptime
- Last sync time
- Recent statistics

### Exit Codes

- `0`: Success
- `1`: General error
- `2`: Configuration error
- `3`: Authentication error
- `4`: Already running (for start command)
- `5`: Not running (for stop command)

## Implementation Plan

### Phase 1: Core Infrastructure (Day 1)
1. **Project Structure**
   - Create directory structure
   - Setup `requirements.txt`
   - Create `setup.py` for installation

2. **Configuration Management**
   - Implement `config.py`
   - YAML parsing
   - Validation logic
   - Unit tests

3. **Logging Setup**
   - Implement `logger.py`
   - File rotation
   - Console output
   - Test logging

### Phase 2: Client Implementations (Day 1-2)
1. **OCI Client**
   - Implement `oci_client.py`
   - List objects with pagination
   - Streaming download
   - Error handling
   - Unit tests with mocking

2. **S3 Client**
   - Implement `s3_client.py`
   - Streaming upload
   - Multipart upload support
   - Error handling
   - Unit tests with mocking

### Phase 3: State Management (Day 2)
1. **State Manager**
   - Implement `state.py`
   - JSON persistence
   - File locking
   - Atomic writes
   - Record cleanup
   - Unit tests

### Phase 4: Transfer Logic (Day 2-3)
1. **Transfer Orchestrator**
   - Implement `orchestrator.py`
   - File discovery
   - Filtering logic
   - Parallel transfers
   - Metrics collection
   - Integration tests

### Phase 5: Daemon and Scheduler (Day 3)
1. **Daemon Manager**
   - Implement `daemon.py`
   - PID management
   - Signal handling
   - Process forking
   - Tests

2. **Scheduler**
   - Implement `scheduler.py`
   - Interval-based execution
   - Graceful shutdown
   - Tests

### Phase 6: CLI Interface (Day 3)
1. **CLI Implementation**
   - Implement `cli.py`
   - Command parsing
   - Help text
   - Command routing
   - Tests

### Phase 7: Integration and Testing (Day 4)
1. **End-to-End Tests**
   - Test with real OCI credentials
   - Test with real S3 bucket
   - Test all CLI commands
   - Test error scenarios

2. **Documentation**
   - OCI setup guide
   - Deployment guide
   - Configuration reference
   - Troubleshooting guide

### Phase 8: Production Readiness (Day 4)
1. **Deployment Artifacts**
   - systemd service file
   - Docker support (optional)
   - Installation script
   - Log rotation config

2. **Monitoring**
   - Health check endpoint (optional)
   - Metrics export (optional)
   - Alert templates

## File Structure

```
oracle-byod/
├── README.md
├── REQUIREMENTS.md
├── DESIGN.md
├── setup.py
├── requirements.txt
├── config.template.yaml
├── config.testing.yaml
├── oracle_focus_agent/
│   ├── __init__.py
│   ├── cli.py
│   ├── daemon.py
│   ├── scheduler.py
│   ├── orchestrator.py
│   ├── oci_client.py
│   ├── s3_client.py
│   ├── config.py
│   ├── state.py
│   └── logger.py
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_oci_client.py
│   ├── test_s3_client.py
│   ├── test_state.py
│   ├── test_orchestrator.py
│   └── test_integration.py
├── docs/
│   ├── OCI_SETUP.md
│   ├── DEPLOYMENT.md
│   ├── CONFIG_REFERENCE.md
│   └── TROUBLESHOOTING.md
└── systemd/
    └── oracle-focus-agent.service
```

## Dependencies

### Python Packages

```
oci>=2.100.0              # Oracle Cloud Infrastructure SDK
boto3>=1.26.0             # AWS SDK
PyYAML>=6.0               # YAML configuration parsing
python-daemon>=3.0.0      # Daemon process management (optional)
```

### System Requirements

- Python 3.8+
- OCI CLI configured with valid credentials
- AWS credentials configured (environment or ~/.aws/credentials)
- Write permissions to log and state directories

## Security Considerations

1. **Credential Management**
   - Never store credentials in config file
   - Use OCI config file for Oracle authentication
   - Use AWS credential chain for S3 authentication
   - Set restrictive permissions on config files (600)

2. **State File Security**
   - Store state file with restricted permissions (600)
   - Include checksums to detect tampering
   - Use file locking to prevent concurrent access

3. **Network Security**
   - Use HTTPS for all API calls
   - Validate SSL certificates
   - Support proxy configuration

4. **Logging Security**
   - Never log credentials
   - Redact sensitive information
   - Rotate logs to prevent disk filling

## Performance Considerations

1. **Memory Usage**
   - Stream files without loading into memory
   - Use configurable chunk size (default 8MB)
   - Limit concurrent transfers

2. **Network Efficiency**
   - Use connection pooling
   - Support multipart uploads for large files
   - Implement retry with exponential backoff

3. **I/O Optimization**
   - Stream directly from OCI to S3
   - No intermediate disk storage
   - Minimize state file writes (batch updates)

## Monitoring and Observability

### Metrics to Track

1. **Transfer Metrics**
   - Files discovered
   - Files transferred
   - Files skipped
   - Files failed
   - Data volume transferred
   - Transfer duration

2. **Performance Metrics**
   - Average transfer speed
   - Peak memory usage
   - CPU usage
   - Network bandwidth

3. **Reliability Metrics**
   - Success rate
   - Retry count
   - Error types and frequency
   - Uptime

### Log Examples

```
2024-11-28 15:30:00 - INFO - Sync started
2024-11-28 15:30:02 - INFO - Discovered 5 files for 2024-11-28
2024-11-28 15:30:03 - INFO - Transferring 2024-11-28_0001000002103533-00001.csv.gz (218153 bytes)
2024-11-28 15:30:15 - INFO - Transfer complete (12.5s, 17.4 KB/s)
2024-11-28 15:30:15 - INFO - Skipping 2024-11-28_0001000002103533-00002.csv.gz (already transferred)
2024-11-28 15:30:45 - INFO - Sync complete: 3 transferred, 2 skipped, 0 failed, 125 MB total
```

## Future Enhancements

1. **Enhanced Monitoring**
   - Prometheus metrics export
   - Health check HTTP endpoint
   - Alert integration (email, Slack)

2. **Advanced Features**
   - Compression/decompression on-the-fly
   - File transformation pipeline
   - Multi-region support
   - Multiple source/destination pairs

3. **Performance Improvements**
   - Adaptive concurrency based on network conditions
   - Differential sync (only changed bytes)
   - Compression-aware transfer optimization

4. **Operational Improvements**
   - Web UI for configuration and monitoring
   - Automated testing in CI/CD
   - Docker container with health checks
   - Kubernetes deployment manifests
