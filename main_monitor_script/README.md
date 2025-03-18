# IBM MQ Monitoring Script v3

## Table of Contents
1. [Introduction](#introduction)
2. [Features](#features)
3. [Requirements](#requirements)
4. [Installation](#installation)
5. [Usage](#usage)
6. [Configuration](#configuration)
7. [Monitoring Capabilities](#monitoring-capabilities)
8. [Output Formats](#output-formats)
9. [Alert System](#alert-system)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)
12. [Support and Version History](#support-and-version-history)

## Introduction

MQ Monitor v3 is a comprehensive monitoring solution for IBM MQ environments. It provides real-time monitoring of Queue Managers, Channels, and Queues with configurable thresholds and alert system.

## Features

- Multi-server and Queue Manager monitoring
- SSL/TLS support for secure connections
- Flexible queue and channel pattern monitoring
- Configurable thresholds and alerts
- Multiple output formats (table, console, JSON, CSV)
- Log file rotation support
- Platform independence (Windows/Unix)
- Color-coded status outputs

## Requirements

- Python 3.6 or higher
- pymqi library
- IBM MQ Client libraries
- PyYAML for configuration parsing
- colorama for colored output
- tabulate for table formatting

## Installation

1. Install required Python packages:
```bash
pip install pymqi pyyaml colorama tabulate
```
2. Install IBM MQ Client libraries
3. Copy the script and configuration files to your preferred location
4. Configure config_v3.yaml according to your environment

## Usage

### Basic Usage
```bash
python mq_monitor_v3.py -c config_v3.yaml
```

### Command Line Parameters
```
-c, --config : Path to configuration file (default: config.yaml)
-s, --server : Monitor specific server from configuration
-o, --output : Output format (console, json, csv, table)
-v, --verbose : Show detailed output
```

## Configuration

### Configuration File Structure
```yaml
# Global settings
global:
  encoding: "utf-8"
  temp_dir: "./temp"

# Platform-specific settings
platform_specific:
  windows:
    ssl_key_repository: "%MQDATA%\\ssl\\key"
    log_dir: "%PROGRAMDATA%\\MQMonitor\\logs"
  unix:
    ssl_key_repository: "/var/mqm/ssl/key"
    log_dir: "/var/log/mqmonitor"

# MQ Servers Configuration
mq_servers:
  - name: "PROD_SERVER"
    host: "mq.company.com"
    port: 1414
    channel: "SYSTEM.ADMIN.SVRCONN"
    queue_manager: "QM1"
    ssl: true
    cipher_spec: "TLS_RSA_WITH_AES_128_CBC_SHA256"

# Monitoring Settings
monitoring:
  channels:
    patterns:
      - "TO.*"
      - "FROM.*"
    exclude:
      - "SYSTEM.*"
  queues:
    patterns:
      - "APP.*"
    thresholds:
      depth_warning: 1000
      depth_critical: 5000
```

## Monitoring Capabilities

### 1. Queue Manager Monitoring
- Connection status
- Command levels
- Overall health check

### 2. Channel Monitoring
- Status check
- Connection count
- Inactivity warnings
- Custom thresholds

### 3. Queue Monitoring
- Queue depth monitoring
- Consumer count check
- Utilization percentage
- Stuck message detection
- System and application queue differentiation

## Output Formats

### 1. Table Format
```
+----------------+---------+------------------+
| Component      | Status  | Message         |
+----------------+---------+------------------+
| QM1            | OK      | Running         |
| APP.QUEUE.1    | WARNING | High depth (80%)|
```

### 2. Console Format
```
2024-03-15 10:30:15 [OK] QM1: Queue Manager is running
2024-03-15 10:30:15 [WARNING] APP.QUEUE.1: Queue depth at 80%
```

### 3. JSON Format
```json
{
  "timestamp": "2024-03-15T10:30:15",
  "components": [
    {
      "name": "QM1",
      "type": "qmgr",
      "status": "OK",
      "message": "Running"
    }
  ]
}
```

## Logs Example / monitoring output

### Real-time Monitoring Output
The script provides detailed real-time monitoring information about Queue Managers, Channels, and Queues. Here's an example of the monitoring output:

```
2025-03-02 11:10:52,960 [INFO] Monitoring Queue Manager QM2 on server myplayground_mq
2025-03-02 11:10:52,967 [INFO] Successfully connected to QM2 without authentication
2025-03-02 11:10:52,968 [INFO] Successfully connected to Queue Manager QM2 on server myplayground_mq
2025-03-02 11:10:52,981 [INFO] Got Queue Manager status: QM2, status: OK
```

### Channel Status Monitoring
```
2025-03-02 11:10:53,026 [INFO] Channel: MON.ADMIN.SVRCONN, Status: INACTIVE, Check Status: WARNING, Messages: Channel is not in required state, Channel is inactive
2025-03-02 11:10:53,034 [INFO] Channel: QM2.SVRCONN, Status: RUNNING, Check Status: OK
```

### Queue Status Monitoring
```
2025-03-02 11:10:53,270 [INFO] Queue: PYMQPCF.67C2E3C622C09102, Type: LOCAL, Depth: 0/5000 (0.0%), Consumers: 1, Status: OK
```

### Summary Output
```
2025-03-02 11:10:53,393 [INFO] 02-03-2025 11:10:53 - OK - QueueManagerState - IBM MQ Queue Manager QM2 is ok on myplayground_mq
2025-03-02 11:10:53,393 [INFO] 02-03-2025 11:10:53 - WARNING - ChannelState - Channel MON.ADMIN.SVRCONN is inactive on QM2
2025-03-02 11:10:53,393 [INFO] 02-03-2025 11:10:53 - OK - ChannelState - Channel QM2.SVRCONN is running on QM2
2025-03-02 11:10:53,393 [INFO] 02-03-2025 11:10:53 - OK - QueueState - Queue PYMQPCF.67C2E3C622C09102 on QM2 - depth: 0/5000 (0.0%), consumers: 1
```

### System Queues Status
```
2025-03-02 11:10:53,393 [INFO] 02-03-2025 11:10:53 - OK - QueueState - Queue SYSTEM.ADMIN.ACCOUNTING.QUEUE on QM2 - depth: 0/3000 (0.0%), consumers: 0
2025-03-02 11:10:53,393 [INFO] 02-03-2025 11:10:53 - OK - QueueState - Queue SYSTEM.ADMIN.ACTIVITY.QUEUE on QM2 - depth: 0/5000 (0.0%), consumers: 0
2025-03-02 11:10:53,394 [INFO] 02-03-2025 11:10:53 - OK - QueueState - Queue SYSTEM.ADMIN.CHANNEL.EVENT on QM2 - depth: 0/3000 (0.0%), consumers: 0
2025-03-02 11:10:53,394 [INFO] 02-03-2025 11:10:53 - OK - QueueState - Queue SYSTEM.ADMIN.COMMAND.EVENT on QM2 - depth: 0/5000 (0.0%), consumers: 0
2025-03-02 11:10:53,394 [INFO] 02-03-2025 11:10:53 - OK - QueueState - Queue SYSTEM.ADMIN.COMMAND.QUEUE on QM2 - depth: 0/3000 (0.0%), consumers: 1
```

The monitoring output provides:
- Real-time connection and status information
- Channel state monitoring with warnings for inactive channels
- Queue depth and consumer monitoring
- System queues status overview
- Clear status indicators (OK, WARNING, CRITICAL)
- Timestamp for each monitoring event
- Detailed metrics including queue depths and consumer counts

## Alert System

### Alert Levels
- **OK**: Component is functioning normally
- **WARNING**: Requires attention but not critical
- **CRITICAL**: Requires immediate attention
- **UNKNOWN**: Status cannot be determined

### Alert Configuration
```yaml
alerts:
  queue_depth:
    warning_percent: 70
    critical_percent: 90
  channel_status:
    inactive_warning: 300
    retry_count: 3
```

## Best Practices

### 1. Security
- Use environment variables for passwords
- Enable SSL/TLS for secure connections
- Implement proper access controls

### 2. Monitoring
- Set appropriate thresholds for your environment
- Monitor system queues separately
- Use specific patterns instead of wildcards

### 3. Performance
- Monitor only necessary queues and channels
- Use appropriate logging levels
- Implement log rotation

## Troubleshooting

### Diagnostic Commands
```bash
# Check Queue Manager status
python mq_monitor_v3.py --check qmgr QM1

# Verify channel status
python mq_monitor_v3.py --check channel SYSTEM.DEF.SVRCONN

# Check queue depths
python mq_monitor_v3.py --check queue APP.* --depth

# Verify permissions
python mq_monitor_v3.py --check auth --user mquser
```

### Connection Problems
```bash
# Test connectivity
python mq_monitor_v3.py --ping QM1

# Check SSL/TLS configuration
python mq_monitor_v3.py --check ssl QM1

# Verify network settings
python mq_monitor_v3.py --check network QM1
```

### Performance Issues
```bash
# Check resource usage
python mq_monitor_v3.py --check resources QM1

# Monitor message rates
python mq_monitor_v3.py --check rates QM1

# Analyze queue statistics
python mq_monitor_v3.py --check stats APP.*
```

### Logging and Debug
```bash
# Enable debug logging
python mq_monitor_v3.py --debug --check all QM1

# Export check results
python mq_monitor_v3.py --export-checks QM1

# Generate health report
python mq_monitor_v3.py --health-report QM1
```

## Support and Version History

### Quick Reference
```bash
# List available checks
python mq_monitor_v3.py --list-checks

# Show check details
python mq_monitor_v3.py --help-check qmgr

# Display version information
python mq_monitor_v3.py --version
```

### Support
For issues and feature requests, please contact:
- Email: robert.pesout@tietoevry.com

### Version History
**v3.0.0** - Current version
- Added multiple output formats
- Enhanced SSL/TLS support
- Improved error handling
- Added specific queue configurations
- Enhanced logging capabilities 
