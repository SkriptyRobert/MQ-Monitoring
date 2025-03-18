# IBM MQ Command Cheatsheet

## Table of Contents
1. [Basic Commands](#basic-commands)
2. [Queue Manager Operations](#queue-manager-operations)
3. [Display Commands](#display-commands)
4. [Channel Authentication](#channel-authentication)
5. [Security and Permissions](#security-and-permissions)
6. [Channel Operations](#channel-operations)
7. [Common Scenarios](#common-scenarios)

## Basic Commands

### Queue Manager Status
```bash
# Display all Queue Managers and their status
dspmq

# Example output:
# QMNAME(QM1)                                               STATUS(Running)
# QMNAME(QM2)                                               STATUS(Running)
```

### Queue Manager Control
```bash
# Start Queue Manager
strmqm QM1

# Stop Queue Manager
endmqm -i QM1

# Enter MQSC interactive mode
runmqsc QM1
```

## Display Commands

### Basic Object Display
```bash
# Display all objects (run in runmqsc)
DISPLAY QUEUE(*)
DISPLAY CHANNEL(*)
DISPLAY LISTENER(*)
DISPLAY SERVICE(*)
DISPLAY PROCESS(*)
DISPLAY NAMELIST(*)
DISPLAY AUTHINFO(*)
```

### Detailed Status Checks
```bash
# Check channel status
DISPLAY CHANNEL(DEV.ADMIN.SVRCONN) TYPE(SVRCONN)

# Check queue depth and status
DISPLAY QLOCAL(*) WHERE(CURDEPTH GT 0)
```

## Channel Authentication

### Basic CHLAUTH Rules
```bash
# Allow connections from any IP address
SET CHLAUTH('QM*.SVRCONN') TYPE(ADDRESSMAP) ADDRESS('*') USERSRC(CHANNEL) CHCKCLNT(ASQMGR)

# Map client user to MQ admin user
SET CHLAUTH('QM*.SVRCONN') TYPE(USERMAP) CLNTUSER('pesourob') USERSRC(MAP) MCAUSER('mqm')

# Set authentication to optional
ALTER AUTHINFO(SYSTEM.DEFAULT.AUTHINFO.IDPWOS) AUTHTYPE(IDPWOS) CHCKCLNT(OPTIONAL)
```

### Admin Channel Setup
```bash
# Start admin channel
START CHANNEL(DEV.ADMIN.SVRCONN)

# Set user mapping for admin channel
SET CHLAUTH(DEV.ADMIN.SVRCONN) TYPE(USERMAP) CLNTUSER(pesourob) MCAUSER(mqm)
```

## Security and Permissions

### Permission Checks
```bash
# Check user permissions on Queue Manager
dspmqaut -m QM1 -t qmgr -p pesourob

# Display authentication information
DISPLAY AUTHINFO(*)
```

### Security Configuration
```bash
# Set client channel security
SET CHLAUTH('QM*.SVRCONN') TYPE(ADDRESSMAP) ADDRESS('*') USERSRC(CHANNEL) CHCKCLNT(ASQMGR)

# Modify authentication settings
ALTER AUTHINFO(SYSTEM.DEFAULT.AUTHINFO.IDPWOS) AUTHTYPE(IDPWOS) CHCKCLNT(OPTIONAL)
```

## Channel Operations

### Channel Control
```bash
# Start a channel
START CHANNEL(CHANNEL.NAME)

# Stop a channel
STOP CHANNEL(CHANNEL.NAME)

# Display channel status
DISPLAY CHSTATUS(CHANNEL.NAME)
```

### Channel Security Setup
```bash
# Basic channel authentication
SET CHLAUTH('QM*.SVRCONN') TYPE(ADDRESSMAP) ADDRESS('*') USERSRC(CHANNEL)

# User mapping for channel
SET CHLAUTH('CHANNEL.NAME') TYPE(USERMAP) CLNTUSER('username') MCAUSER('mqm')
```

## Common Scenarios

### Queue Manager Setup
```bash
# 1. Start Queue Manager
strmqm QM1

# 2. Configure basic security
ALTER AUTHINFO(SYSTEM.DEFAULT.AUTHINFO.IDPWOS) AUTHTYPE(IDPWOS) CHCKCLNT(OPTIONAL)

# 3. Set up admin channel
START CHANNEL(DEV.ADMIN.SVRCONN)
SET CHLAUTH(DEV.ADMIN.SVRCONN) TYPE(USERMAP) CLNTUSER(username) MCAUSER(mqm)
```

### Troubleshooting Access
```bash
# 1. Check Queue Manager status
dspmq

# 2. Verify channel status
DISPLAY CHANNEL(DEV.ADMIN.SVRCONN) TYPE(SVRCONN)

# 3. Check user permissions
dspmqaut -m QM1 -t qmgr -p username

# 4. Review authentication settings
DISPLAY AUTHINFO(*)
```

### Quick Reference Notes

- `CHCKCLNT(ASQMGR)` - Client validation follows Queue Manager settings
- `USERSRC(MAP)` - Use mapped user for authentication
- `MCAUSER('mqm')` - Map to MQ administrator user
- `TYPE(USERMAP)` - Define user mapping rules
- `TYPE(ADDRESSMAP)` - Define IP address access rules

### Important Tips
1. Always verify changes with display commands
2. Use `runmqsc` for interactive command mode
3. Restart Queue Manager after significant security changes
4. Keep track of CHLAUTH rules for troubleshooting
5. Monitor channel status after configuration changes 
