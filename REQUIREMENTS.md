# Oracle FOCUS to Umbrella BYOD Transfer Agent - Requirements

## Executive Summary
Build a daemon agent that automatically transfers FOCUS cost report files from Oracle Cloud Infrastructure (OCI) Object Storage to Umbrella's BYOD S3 bucket, running continuously with 10-minute polling intervals.

## Functional Requirements

### FR-1: File Discovery and Transfer
- **FR-1.1**: Agent SHALL poll OCI Object Storage every 10 minutes
- **FR-1.2**: Agent SHALL identify all FOCUS files for the current day from the Oracle bucket
- **FR-1.3**: Agent SHALL transfer identified files to the Umbrella S3 bucket AS IS (no decompression)
- **FR-1.4**: Agent SHALL override existing files in S3 if they already exist (supporting file updates)
- **FR-1.5**: Agent SHALL preserve the gzip compression format during transfer

### FR-2: Oracle OCI Source Configuration
- **FR-2.1**: Source namespace: `bling` (Oracle billing namespace)
- **FR-2.2**: Source bucket: Tenancy OCID (e.g., `ocid1.tenancy.oc1..aaaaaaaatjusogdqicpfl5vfvl7q474vm2ao7lzffenavtmwkc4p6olszjoq`)
- **FR-2.3**: Source prefix structure: `FOCUS Reports/<YEAR>/<MONTH>/<DAY>/`
  - Example: `FOCUS Reports/2024/11/28/0001000002103533-00001.csv.gz`
- **FR-2.4**: Files are gzip-compressed CSV files (.csv.gz) and SHALL be transferred in compressed format

### FR-3: Target S3 Configuration
- **FR-3.1**: Destination bucket: `s3://anodot-47e09447-83c0-jnfwjyne837mwc8rjrqyu6fr85856use1b-s3alias/47e09447-83c0-43f7-ba26-4e9a189c8824/0/DavidO-e0f365`
- **FR-3.2**: Files SHALL be stored in flat structure (no subdirectories)
- **FR-3.3**: File naming convention: `<YYYY-MM-DD>_<original-filename>`
  - Example: `2024-11-28_0001000002103533-00001.csv.gz`
  - Note: Underscore separator to ensure no spaces
- **FR-3.4**: Files MUST NOT contain spaces in names (Umbrella BYOD requirement)
- **FR-3.5**: Files MUST remain gzip-compressed (.csv.gz)
- **FR-3.6**: Files MUST conform to FOCUS v1.0 format (content validation is Umbrella's responsibility)
- **FR-3.7**: Maximum file size: 5GB per file

### FR-4: Daemon Operation
- **FR-4.1**: Agent SHALL run as a persistent daemon process
- **FR-4.2**: Agent SHALL wake up every 10 minutes to check for new files
- **FR-4.3**: Agent SHALL log all operations (discoveries, transfers, errors)
- **FR-4.4**: Agent SHALL handle network failures gracefully and retry
- **FR-4.5**: Agent SHALL support graceful shutdown via signal handling (SIGTERM, SIGINT)

### FR-5: Configuration Management
- **FR-5.1**: ALL operational parameters SHALL be configurable via external config file (YAML format)
- **FR-5.2**: Configuration SHALL include:
  - OCI authentication settings (config file path, profile name)
  - OCI namespace, bucket, prefix
  - S3 bucket path and credentials
  - Polling interval (default: 10 minutes)
  - Logging level and output path
  - Retry settings (max retries, backoff strategy)
  - Date range (default: current day only)
  - File naming conventions
  - Advanced settings (chunk size, validation, etc.)
- **FR-5.3**: Project SHALL provide two config files:
  - `config.template.yaml`: Template with placeholders for general use
  - `config.testing.yaml`: Pre-filled with David's testing environment settings

### FR-6: Command-Line Interface
- **FR-6.1**: Agent SHALL support command-line mode with following commands:
  - `start`: Start daemon in background
  - `stop`: Stop running daemon
  - `run`: Run in foreground (for testing/debugging)
  - `test`: Test configuration and connectivity
  - `sync`: Perform one-time sync and exit
  - `status`: Check daemon status
- **FR-6.2**: Agent SHALL accept config file path as command-line argument
- **FR-6.3**: Agent SHALL support `--help` flag for usage information
- **FR-6.4**: Agent SHALL support `--config` flag to specify config file path

### FR-7: Error Handling and Resilience
- **FR-7.1**: Agent SHALL handle OCI API rate limits with exponential backoff
- **FR-7.2**: Agent SHALL handle S3 API errors gracefully
- **FR-7.3**: Agent SHALL continue operation if individual file transfer fails
- **FR-7.4**: Agent SHALL maintain a transfer state file to track processed files
- **FR-7.5**: Agent SHALL support resuming from last known state after restart
- **FR-7.6**: Agent SHALL validate file integrity using size/checksum before marking as complete

### FR-8: Monitoring and Observability
- **FR-8.1**: Agent SHALL log all file transfers with timestamps
- **FR-8.2**: Agent SHALL log errors with full context
- **FR-8.3**: Agent SHALL maintain metrics:
  - Files discovered per run
  - Files transferred successfully
  - Files failed
  - Transfer duration
  - Last successful run timestamp
  - Data volume transferred

## Non-Functional Requirements

### NFR-1: Security
- **NFR-1.1**: Agent SHALL use OCI config file authentication (~/.oci/config)
- **NFR-1.2**: Agent SHALL use AWS credentials from environment or AWS credential chain
- **NFR-1.3**: Agent SHALL NOT store credentials in plaintext in config file
- **NFR-1.4**: Agent SHALL set appropriate file permissions (600) on state files

### NFR-2: Performance
- **NFR-2.1**: Agent SHALL handle files up to 5GB efficiently (streaming transfer)
- **NFR-2.2**: Agent SHALL support parallel transfers (configurable concurrency)
- **NFR-2.3**: Agent SHALL minimize memory footprint during transfers
- **NFR-2.4**: Agent SHALL use streaming I/O to avoid loading entire files into memory

### NFR-3: Maintainability
- **NFR-3.1**: Code SHALL be written in Python 3.8+
- **NFR-3.2**: Code SHALL follow PEP 8 style guidelines
- **NFR-3.3**: Code SHALL include comprehensive logging
- **NFR-3.4**: Code SHALL be modular and testable

### NFR-4: Documentation
- **NFR-4.1**: Project SHALL include OCI setup guide
- **NFR-4.2**: Project SHALL include deployment guide
- **NFR-4.3**: Project SHALL include configuration reference
- **NFR-4.4**: Project SHALL include troubleshooting guide

## Oracle OCI Configuration Prerequisites

### OCI-1: API Key Setup
1. Navigate to OCI Console → User Settings → API Keys
2. Click "Add API Key"
3. Download the private key (.pem file)
4. Note the fingerprint shown in the console
5. Set permissions: `chmod 600 ~/.oci/<your-key>.pem`

### OCI-2: OCI Config File
- Location: `~/.oci/config`
- Required fields:
  ```ini
  [DEFAULT]
  user=ocid1.user.oc1..aaaaaaaa4eygdejtbvucn4xed6ndmdt4xnycaba6f5c5zpdnm6bn3or4saaa
  fingerprint=66:f4:ea:72:e7:80:f4:73:8e:1d:76:82:58:7f:94:44
  tenancy=ocid1.tenancy.oc1..aaaaaaaatjusogdqicpfl5vfvl7q474vm2ao7lzffenavtmwkc4p6olszjoq
  region=us-ashburn-1
  key_file=/Users/david/.oci/david@umbrellacost.com-2025-11-24T12_25_50.063Z.pem
  ```

### OCI-3: IAM Permissions
- User must have permissions to read from Object Storage
- Minimum required policy:
  ```
  Allow user <username> to read objects in tenancy where target.bucket.name='<tenancy_ocid>'
  ```

### OCI-4: Key Discoveries
- **Namespace**: Use `bling` (NOT your tenancy namespace)
- **Bucket**: Use your tenancy OCID as the bucket name (NOT `oci-usage-reports`)
- **Prefix**: `FOCUS Reports/` (with capital letters and space)
- **Testing**: Use `oci os object list --namespace-name bling --bucket-name <tenancy-ocid> --prefix "FOCUS Reports/" --all`

## AWS S3 Configuration Prerequisites

### S3-1: AWS Credentials
- AWS Access Key ID
- AWS Secret Access Key
- Configure via:
  - Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
  - AWS credentials file: `~/.aws/credentials`
  - IAM role (if running on EC2)

### S3-2: IAM Permissions
- User must have permissions to write to specified S3 bucket
- Minimum required policy:
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ],
        "Resource": [
          "arn:aws:s3:::anodot-47e09447-83c0-jnfwjyne837mwc8rjrqyu6fr85856use1b-s3alias",
          "arn:aws:s3:::anodot-47e09447-83c0-jnfwjyne837mwc8rjrqyu6fr85856use1b-s3alias/*"
        ]
      }
    ]
  }
  ```

## Known Constraints

1. **Oracle FOCUS Structure**: Files are nested by year/month/day in Oracle
2. **Umbrella Structure**: Files must be flat (no subdirectories) with date-prefixed names
3. **File Updates**: Oracle may update files for a given day multiple times; agent must handle overwrites
4. **Compression**: Files MUST remain gzip-compressed (.csv.gz) throughout transfer - NO decompression
5. **FOCUS Format**: Files must conform to FOCUS v1.0 specification (validated by Umbrella)
6. **File Size**: Maximum 5GB per file (Umbrella limit)
7. **No Spaces**: File names must not contain spaces (Umbrella BYOD requirement)

## Data Flow

```
Oracle OCI Object Storage                    Umbrella S3 Bucket
========================                    ==================

bling/                                      s3://bucket/org/customer/account/
  <tenancy-ocid>/                              ├─ 2024-11-28_0001000002103533-00001.csv.gz
    FOCUS Reports/                             ├─ 2024-11-28_0001000002103533-00002.csv.gz
      2024/                                    └─ 2024-11-29_0001000002711630-00001.csv.gz
        11/
          28/
            ├─ 0001000002103533-00001.csv.gz
            └─ 0001000002103533-00002.csv.gz
          29/
            └─ 0001000002711630-00001.csv.gz

Transfer: Stream .csv.gz directly with renamed filename
No decompression - preserve gzip format throughout
```

## Reference Implementation

Based on existing `../testoci/download_latest_focus.py`:
- Uses `oci.config.from_file()` for authentication
- Lists objects with pagination support
- Streams downloads without loading into memory
- Successfully tested with namespace `bling` and tenancy OCID as bucket

## Success Criteria

1. Agent runs continuously for 24+ hours without manual intervention
2. All FOCUS files for current day are transferred within 15 minutes of appearance in Oracle
3. File naming follows specified convention consistently (YYYY-MM-DD_filename.csv.gz)
4. Files remain gzip-compressed during entire transfer process
5. Agent recovers from transient network failures automatically
6. All operations are logged with sufficient detail for troubleshooting
7. Agent can be deployed and configured by DevOps without code changes
8. No decompression/recompression occurs during transfer
9. Configuration can be changed without modifying code
