# IBM MQ Monitoring - Configuration Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Working with Configuration](#working-with-configuration)
3. [Templates and Examples](#templates-and-examples)
4. [Security and SSL/TLS](#security-and-ssl/tls)
5. [Monitoring](#monitoring)
6. [Output Formats](#output-formats)
7. [Troubleshooting](#troubleshooting)

## Introduction

This IBM MQ monitoring tool uses a YAML configuration file to define all settings. Main advantages:
- Centralized monitoring management
- Flexible configuration for different environments
- Support for multiple servers and Queue Managers
- Custom threshold definitions and alerts
- Secure communication using SSL/TLS

## Working with Configuration

### Basic Structure
The configuration file `config_v3.yaml` is divided into logical sections:

```yaml
global:                   # Global settings
platform_specific:        # Settings for different OS
mq_servers:               # List of MQ servers
output:                   # Output configuration
channels_monitoring:      # Channel monitoring settings
queues_monitoring:        # Queue monitoring settings
```

### Configuration Steps

1. **Basic Settings**
```yaml
global:
  encoding: "utf-8"        # Communication encoding
  temp_dir: "./temp"       # Working directory (null = system)

platform_specific:
  windows:                 # Windows settings
    ssl_key_repository: "%MQDATA%\\ssl\\key"
    log_dir: "%PROGRAMDATA%\\MQMonitor\\logs"
```

2. **Server Definitions**
```yaml
mq_servers:
  - name: "prod_server"    # Unique server name
    host: "mq.company.com" # Hostname or IP
    port: 1414            # Port (default 1414)
    ssl: true             # Enable SSL/TLS
    queue_managers:       # List of Queue Managers
      - name: "QM1"
        channel: "SYSTEM.ADMIN.SVRCONN"
        user: "${MQ_USER}"     # Using environment variable
        password: "${MQ_PASS}" # Using environment variable
```

## Templates and Examples

### 1. Application Queue Monitoring
```yaml
queues_monitoring:
  specific:
    APP.PRIORITY.*:           # Pattern for priority queues
      max_depth: 1000
      warning_depth: 500
      required_consumers: 2
      messages:
        max_depth:
          severity: "CRITICAL"
          text: "Priority queue {queue_name} is full! Contact XYZ team."
```

### 2. System Queue Monitoring
```yaml
specific:
  SYSTEM.DEAD.LETTER.QUEUE:
    max_depth: 100
    warning_depth: 50
    check_interval: 300      # Check every 5 minutes
    messages:
      high_depth:
        severity: "WARNING"
        text: "DLQ contains {current} messages. Analyze using dmpmqmsg."
```

### 3. Custom Templates for Different Queue Types
```yaml
templates:
  high_priority:
    max_depth: 1000
    warning_depth: 500
    required_consumers: 2
  batch_processing:
    max_depth: 10000
    warning_depth: 8000
    check_interval: 600
  system_queues:
    max_depth: 5000
    warning_depth: 4000
    exclude_monitoring: ["depth", "consumers"]
```

## Security and SSL/TLS

### Basic SSL/TLS Configuration
```yaml
ssl_config:
  # Basic settings
  enabled: true
  cipher_spec: "TLS_RSA_WITH_AES_128_CBC_SHA256"
  cert_label: "ibmwebspheremq"
  
  # Certificate paths
  key_repository: "/var/mqm/ssl/keys"
  cert_file: "/var/mqm/ssl/certs/client.crt"
  key_file: "/var/mqm/ssl/keys/client.key"
  
  # Additional settings
  ssl_validate_client: true
  ssl_cipher_suite: "ECDHE_RSA_AES_128_CBC_SHA256"
```

### Security Best Practices
1. **Password Management**
   ```yaml
   queue_managers:
     - name: "QM1"
       user: "${MQ_USER}"        # Using environment variables
       password: "${MQ_PASS}"    # Never store passwords directly
   ```

2. **Certificates**
   ```yaml
   ssl_config:
     cert_validation: true
     trusted_certs: 
       - "/etc/ssl/certs/ca-certificates.crt"
     crl_check: true            # Certificate Revocation List check
   ```

## Monitoring

### Advanced Monitoring Features

1. **Dynamic Thresholds**
```yaml
queues_monitoring:
  dynamic_thresholds:
    enabled: true
    learning_period: 7d      # Learning period
    adjustment_interval: 1h   # Threshold adjustment interval
```

2. **Conditional Monitoring**
```yaml
conditions:
  business_hours:
    - days: [1,2,3,4,5]     # Monday-Friday
      hours: [8-17]         # 8:00-17:00
      thresholds:
        warning_depth: 1000
        critical_depth: 5000
    - default:              # Outside business hours
      thresholds:
        warning_depth: 5000
        critical_depth: 10000
```

### Complex Configuration Examples

1. **High-Availability Environment**
```yaml
mq_servers:
  - name: "ha_cluster"
    hosts: 
      - "mq1.company.com"
      - "mq2.company.com"
    failover: true
    check_interval: 30
```

2. **Production Monitoring**
```yaml
monitoring_profiles:
  production:
    queue_patterns:
      - include: "PROD.*"
      - exclude: "PROD.TEST.*"
    thresholds:
      depth_warning_percent: 70
      depth_critical_percent: 90
    notifications:
      email: "team@company.com"
      slack: "#prod-alerts"
```

## Troubleshooting

### Configuration Diagnostics
```bash
# Configuration verification
python mq_monitor_v3.py --validate-config

# Connection test
python mq_monitor_v3.py --test-connection QM1

# Debug mode
python mq_monitor_v3.py -c config_v3.yaml --debug
```

### Common Problems and Solutions

1. **SSL/TLS Issues**
   ```bash
   # SSL configuration verification
   python mq_monitor_v3.py --ssl-verify QM1
   
   # List used certificates
   python mq_monitor_v3.py --show-certs
   ```

2. **Permission Issues**
   ```bash
   # Permission test
   python mq_monitor_v3.py --check-permissions QM1
   ```

## Support and Documentation

### Useful Commands
```bash
# Generate sample configuration
python mq_monitor_v3.py --generate-config

# Export current configuration
python mq_monitor_v3.py --export-config

# Validate configuration file
python mq_monitor_v3.py --validate config_v3.yaml
```

For technical support contact:
- Email: robert.pesout@tietoevry.com
