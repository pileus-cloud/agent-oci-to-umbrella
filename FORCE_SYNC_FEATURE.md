# Force Sync Feature

## Overview

The `--force` (or `-f`) flag allows you to re-transfer all files, ignoring the state tracking. This is useful when Oracle updates files and you need to copy them again to S3.

## Usage

```bash
oracle-focus-agent sync --config config.yaml --force
```

Or using the short form:
```bash
oracle-focus-agent sync --config config.yaml -f
```

## How It Works

### Normal Sync (without --force)
```bash
oracle-focus-agent sync --config config.testing.yaml
```

**Behavior:**
- Discovers files from OCI
- Checks `state.json` to see which files were already transferred
- Only transfers NEW files or files that changed (size/timestamp)
- Skips files already transferred

**Example Output:**
```
Discovered: 8 total files
Files to transfer: 2
Files skipped (already transferred): 6
✓ Transferred: 2025-11-25_0001000002713240-00001.csv.gz
✓ Transferred: 2025-11-24_0001000002713240-00001.csv.gz
```

### Force Sync (with --force)
```bash
oracle-focus-agent sync --config config.testing.yaml --force
```

**Behavior:**
- Discovers files from OCI
- **IGNORES state.json** completely
- Transfers ALL discovered files (even if already transferred)
- Overwrites existing files in S3

**Example Output:**
```
Starting sync operation (FORCED - ignoring state)
Discovered: 8 total files
Force mode enabled: transferring all files regardless of state
Files to transfer: 8
Files skipped: 0 (force mode: re-transferring all)
✓ Transferred: 2025-11-24_0001000002711283-00001.csv.gz
✓ Transferred: 2025-11-24_0001000002711630-00001.csv.gz
✓ Transferred: 2025-11-24_0001000002711992-00001.csv.gz
✓ Transferred: 2025-11-24_0001000002712454-00001.csv.gz
✓ Transferred: 2025-11-24_0001000002712696-00001.csv.gz
✓ Transferred: 2025-11-24_0001000002712916-00001.csv.gz
✓ Transferred: 2025-11-24_0001000002713240-00001.csv.gz
✓ Transferred: 2025-11-25_0001000002713240-00001.csv.gz
```

## When to Use --force

Use the `--force` flag when:

1. **Oracle updates FOCUS files**: Oracle regenerates files for a specific day with corrected data
2. **Data correction**: You need to re-process files that were already transferred
3. **S3 data loss**: Files were deleted from S3 and need to be re-uploaded
4. **Testing**: You want to verify the transfer process works correctly
5. **Backfill**: You need to re-sync historical data

## Comparison

| Scenario | Normal Sync | Force Sync |
|----------|-------------|------------|
| **New file appears** | ✅ Transfers | ✅ Transfers |
| **File already transferred (unchanged)** | ⏭️ Skips | ✅ Re-transfers |
| **File updated (size changed)** | ✅ Transfers | ✅ Transfers |
| **File updated (timestamp newer)** | ✅ Transfers | ✅ Transfers |
| **Uses state.json** | ✅ Yes | ❌ No (ignores) |
| **Updates state.json** | ✅ Yes | ✅ Yes |

## Real-World Example

### Scenario: Oracle Updates Yesterday's Files

Oracle discovers an error in yesterday's FOCUS reports and regenerates them at 2 PM today.

**Without --force:**
```bash
$ oracle-focus-agent sync --config config.yaml

Discovered: 6 files from yesterday
Files to transfer: 0
Files skipped: 6 (already transferred)
# Problem: Updated files are NOT re-transferred!
```

**With --force:**
```bash
$ oracle-focus-agent sync --config config.yaml --force

Discovered: 6 files from yesterday
Force mode enabled: transferring all files regardless of state
Files to transfer: 6
Files skipped: 0
✓ All 6 files re-transferred with updated data
# Success: Updated files ARE re-transferred!
```

## Important Notes

1. **State is still updated**: Even with `--force`, the state file is updated after transfers
2. **Parallel transfers**: Still uses `max_concurrent_transfers` setting (default: 3)
3. **Overwrites S3**: Files in S3 are overwritten with new data
4. **Bandwidth**: Re-transferring all files uses more bandwidth and time
5. **Lookback days**: Respects `lookback_days` config setting

## Advanced Usage

### Force sync for specific date range

Edit `config.yaml` temporarily:
```yaml
agent:
  lookback_days: 7  # Last 7 days
```

Then force sync:
```bash
oracle-focus-agent sync --config config.yaml --force
# Re-transfers all files from last 7 days
```

### Force sync in scripts

```bash
#!/bin/bash
# Daily force sync script for data corrections

echo "Running forced sync..."
oracle-focus-agent sync --config /etc/oracle-focus-agent/config.yaml --force

if [ $? -eq 0 ]; then
    echo "Force sync completed successfully"
else
    echo "Force sync failed!"
    exit 1
fi
```

## Performance Impact

Based on test results:

| Files | Size | Normal Sync | Force Sync | Difference |
|-------|------|-------------|------------|------------|
| 8 files | 1.26 MB | ~1s (2 new) | ~4.5s (8 all) | 4x slower |

**Recommendation**: Only use `--force` when necessary, not as default.

## Help Documentation

```bash
$ oracle-focus-agent --help

options:
  --force, -f           Force re-transfer all files, ignoring state (useful
                        when files are updated)

Examples:
  oracle-focus-agent sync --config config.yaml --force  # Force re-transfer all files
```

## Implementation Details

The `--force` flag:
1. Is passed from CLI → `execute_sync()` → `orchestrator.sync()` → `_filter_files()`
2. When `force=True`, `_filter_files()` returns ALL discovered files
3. State checking (`is_transferred()`) is completely bypassed
4. Files are transferred and state is updated normally
5. Logs clearly indicate "FORCED" mode in operation

## Summary

✅ **Added Feature**: `--force` / `-f` flag for sync command
✅ **Purpose**: Re-transfer all files ignoring state tracking
✅ **Use Case**: When Oracle updates files and you need fresh copies
✅ **Testing**: Successfully tested with 8 files (re-transferred all)
✅ **Documentation**: Fully documented with examples

**Quick Command:**
```bash
oracle-focus-agent sync --config config.testing.yaml --force
```
