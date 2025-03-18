# IBM MQ Diagnostic Tool

## Table of Contents
1. [Introduction](#introduction)
2. [Features](#features)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Usage](#usage)
6. [Configuration](#configuration)
7. [Testing Process](#testing-process)
8. [Installation Detection](#installation-detection)
9. [Queue Manager Details](#queue-manager-details)
10. [Diagnostic Process](#diagnostic-process)
11. [Troubleshooting](#troubleshooting)

## Introduction

The IBM MQ Diagnostic Tool is a comprehensive utility designed to check and verify IBM MQ server connections and environment configurations. Developed by robert.pesout@tietoevry.com, this tool helps diagnose common connectivity issues and validate MQ server setups.

## Features

- Python and pymqi version verification
- IBM MQ client libraries detection
- Detection of IBM MQ installations and their versions
- Identification of installation types (Full/Client)
- Network connectivity testing
- MQ server connection testing with/without authentication
- SSL/TLS connection support
- System queue access verification
- Detailed Queue Manager status monitoring
- Listener status and configuration checks
- SVRCONN channel monitoring
- Port availability testing
- Security and permissions verification
- Detailed error reporting and diagnostics

## Prerequisites

- Python 3.6 or higher
- pymqi library (1.12.11 or higher recommended)
- IBM MQ Client libraries installed
- PyYAML library
- Colorama library

## Installation

1. Ensure Python 3.6+ is installed
2. Install required Python packages:
```bash
pip install pymqi==1.12.0 pyyaml colorama
   ```
3. Install IBM MQ Client libraries from:
   https://www.ibm.com/support/pages/downloading-ibm-mq-9x-clients

## Usage

### Basic Usage
```bash
python mq_check.py
```

### With Specific Configuration
```bash
python mq_check.py -c my_config.yaml
```

### Test Specific Server
```bash
python mq_check.py -s server_name
```

### Direct Connection Test
```bash
python mq_check.py --host 10.14.43.201 --port 1414 --channel QM1.SVRCONN --qm QM1
```

### Command Line Options
```
-h, --help            Show help message
-c CONFIG             Path to configuration file (default: config.yaml)
-s SERVER             Test specific server from configuration
--host HOST           MQ server hostname or IP
--port PORT           MQ server port
--qm QM               Queue Manager name
--channel CHANNEL     Channel name
--user USER           Username for authentication
--password PASSWORD   Password for authentication
--no-auth            Force connection without authentication
--ssl                Use SSL/TLS connection
--ssl-cipher CIPHER   SSL cipher specification
--key-repository PATH Path to SSL key repository
-v, --verbose         Show detailed output
```

## Configuration

### Configuration File Format (config.yaml)
```yaml
mq_servers:
  - name: "server1"
    host: "localhost"
    port: 1414
    channel: "SYSTEM.DEF.SVRCONN"
    queue_manager: "QM1"
    user: "mquser"       # optional
    password: "mqpass"   # optional
    ssl: false           # optional
    cipher_spec: ""      # optional
    key_repository: ""   # optional
```

## Testing Process

The tool performs the following checks in sequence:
1. Verifies Python version and required libraries
2. Checks for IBM MQ client libraries
3. Detects and lists all IBM MQ installations on the system:
   - Installation versions
   - Installation paths
   - Installation types (Full/Client)
4. Tests basic network connectivity
5. Attempts MQ server connection
6. Verifies Queue Manager access
7. Tests system queue accessibility
8. Provides detailed diagnostic information

## Installation Detection

### Windows
- Checks Windows Registry for IBM MQ installations
- Identifies both 32-bit and 64-bit installations
- Determines installation type (Full/Client)
- Shows installation paths and versions

### Unix/Linux
- Checks standard installation paths (/opt/mqm, /usr/local/mqm)
- Uses dspmqver command to get version information
- Identifies installation type based on available components
- Shows installation paths and versions

Example output:
```
================================================================================
Checking IBM MQ Installations
================================================================================
Found 2 IBM MQ installation(s):

Installation Details:
  Version: 9.2.5.0
  Path: C:\Program Files\IBM\MQ
  Type: Full

Installation Details:
  Version: 9.3.0.0
  Path: C:\Program Files\IBM\MQ_2
  Type: Client
```

## Queue Manager Details

### Information Categories

1. **Basic Information:**
   - Queue Manager name and status
   - Configuration details (PORT, DESCR, DEADQ, DEFXMITQ)

2. **Listener Information:**
   - Listener name and status
   - Port configuration
   - Transport type
   - Control settings

3. **SVRCONN Channels:**
   - Channel name and status
   - MCAUSER settings
   - SSL/TLS configuration
   - Active connections

4. **Security & Permissions:**
   - Channel Authentication status
   - Connection capabilities
   - System queue access rights
   - Active channel listing

Example output:
```
╔══ Queue Manager: QM1 ═════════════════════════════════
║
║ Status: RUNNING
║
║ Queue Manager Configuration:
║   PORT(1414)
║   DESCR(Default Queue Manager)
║   DEADQ(SYSTEM.DEAD.LETTER.QUEUE)
║
║ Listener Status:
║   Listener name: SYSTEM.LISTENER.TCP.1
║   Status: RUNNING
║   Port: 1414
║   Transport type: TCP
║
║ Server-Connection Channels:
║   Channel: SYSTEM.DEF.SVRCONN
║   Status: RUNNING
║   MCAUSER: mqm
║   SSL Cipher: NONE
║
║ Security & Permissions:
║   Channel Authentication: Enabled
║   Can Connect: ✓
║   Can Browse System Queues: ✓
╚════════════════════════════════════════════════════════
```

## Diagnostic Process

### 1. Environment Verification
- Python version check
- Required libraries verification
- MQ client libraries detection

### 2. Installation Analysis
- MQ installation detection
- Version identification
- Installation type determination
- Queue Manager inventory

### 3. Queue Manager Diagnostics
- Status monitoring
- Configuration validation
- Listener status check
- Channel availability
- Port accessibility

### 4. Security Assessment
- Authentication settings
- Channel security
- Permission verification
- Active connection monitoring

### 5. Connectivity Testing
- Network availability
- Port status
- MQ connection verification
- System queue access

## Troubleshooting

### Common Issues and Solutions

1. **MQ Libraries not found:**
   - Install IBM MQ Client libraries
   - Set MQ_LIB_PATH environment variable

2. **Connection failures:**
   - Verify network connectivity
   - Check firewall settings
   - Confirm channel and queue manager names
   - Verify authentication credentials

3. **SSL/TLS issues:**
   - Verify SSL cipher specifications
   - Check key repository path
   - Ensure certificates are properly configured

###Diagnostic Commands

# Check Queue Manager status
python mq_monitor_v3.py --check qmgr QM1

# Verify channel status
python mq_monitor_v3.py --check channel SYSTEM.DEF.SVRCONN

# Check queue depths
python mq_monitor_v3.py --check queue APP.* --depth

# Verify permissions
python mq_monitor_v3.py --check auth --user mquser


Common Issues

Connection Problems

# Test connectivity
python mq_monitor_v3.py --ping QM1

# Check SSL/TLS configuration
python mq_monitor_v3.py --check ssl QM1

# Verify network settings
python mq_monitor_v3.py --check network QM1


Performance Issues

# Check resource usage
python mq_monitor_v3.py --check resources QM1

# Monitor message rates
python mq_monitor_v3.py --check rates QM1

# Analyze queue statistics
python mq_monitor_v3.py --check stats APP.*

Logging and Debug

# Enable debug logging
python mq_monitor_v3.py --debug --check all QM1

# Export check results
python mq_monitor_v3.py --export-checks QM1

# Generate health report
python mq_monitor_v3.py --health-report QM1

Quick Reference

# List available checks
python mq_monitor_v3.py --list-checks

# Show check details
python mq_monitor_v3.py --help-check qmgr

# Display version information
python mq_monitor_v3.py --version

### Best Practices
1. Start with basic connectivity test without authentication
2. Use verbose mode (-v) for detailed diagnostics
3. Check configuration file syntax before running
4. Keep IBM MQ client libraries updated
5. Document any custom configurations

### Error Handling
- Displays clear error messages with completion and reason codes
- Automatically attempts connection without authentication if authenticated connection fails
- Shows detailed diagnostic information in verbose mode
- Provides suggestions for common issues

## Support and Version Information

### Support
For issues or questions, contact:
- Email: robert.pesout@tietoevry.com
- Alternative Email: robert.pesout@gmail.com

### Version Information
- Current Version: 1.1.0
- Last Updated: March 2025 
