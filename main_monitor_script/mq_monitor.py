#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
IBM MQ Monitoring Script v2
--------------------------
This script is used for monitoring IBM MQ servers, queue managers, channels and queues.
Includes support for monitoring rules and thresholds.

Author: robert.pesout@tietoevry.com
Version: 3.0.0
"""

import os
import sys
import time
import yaml
import json
import argparse
import platform
import tempfile
from pathlib import Path
from datetime import datetime
from tabulate import tabulate
from colorama import init, Fore, Style
import logging
import logging.config
import locale
import codecs
from logging.handlers import RotatingFileHandler

# Initialize colorama for proper color display on all platforms
init(strip=not sys.stdout.isatty())

# Set default encoding for file operations
if sys.stdout.encoding is None or sys.stdout.encoding == 'ascii':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

try:
    import pymqi
except ImportError:
    print(f"{Fore.RED}Error: pymqi library is not installed.")
    print(f"{Fore.YELLOW}Install it using: pip install pymqi")
    print(f"{Fore.YELLOW}Note: IBM MQ client libraries must be installed for pymqi to work.")
    sys.exit(1)

# Status constants
STATUS_OK = "OK"
STATUS_WARNING = "WARNING"
STATUS_CRITICAL = "CRITICAL"
STATUS_UNKNOWN = "UNKNOWN"

# System information detection
SYSTEM_INFO = {
    'system': platform.system(),
    'release': platform.release(),
    'version': platform.version(),
    'machine': platform.machine(),
    'processor': platform.processor()
}

def setup_logging(config, args):
    """Set up logging with respect to platform and configuration."""
    # Basic logging configuration
    log_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '%(asctime)s [%(levelname)s] %(message)s'
            },
            'simple': {
                'format': '[%(levelname)s] %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
                'level': 'WARNING'  # Console shows only WARNING and higher
            }
        },
        'root': {
            'handlers': ['console'],
            'level': 'DEBUG' if args.verbose else 'INFO',
        }
    }

    # Check if logging is enabled
    logging_config = config['output'].get('logging', {})
    if logging_config.get('enabled', False):
        try:
            # Determine log directory
            log_dir = logging_config.get('directory')
            if log_dir is None:
                # Use platform-specific directory
                if platform.system() == 'Windows':
                    log_dir = config['platform_specific']['windows']['log_dir']
                    # Expand environment variables in Windows path
                    log_dir = os.path.expandvars(log_dir)
                else:
                    log_dir = config['platform_specific']['unix']['log_dir']

            # Create log directory
            log_path = Path(log_dir)
            try:
                log_path.mkdir(parents=True, exist_ok=True)
                # Only logging, no output to console
                logging.debug(f"Log directory created/exists: {log_dir}")
            except PermissionError:
                print(f"{Fore.YELLOW}Warning: I don't have permission to create log directory: {log_dir}{Style.RESET_ALL}")
                # Use temporary directory as backup
                log_dir = tempfile.gettempdir()
                log_path = Path(log_dir)
                print(f"{Fore.YELLOW}Using temporary directory: {log_dir}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.YELLOW}Warning: Cannot create log directory: {e}{Style.RESET_ALL}")
                log_dir = tempfile.gettempdir()
                log_path = Path(log_dir)
                print(f"{Fore.YELLOW}Using temporary directory: {log_dir}{Style.RESET_ALL}")
            
            # Build log file path
            log_file = log_path / logging_config.get('filename', 'mq_monitor.log')
            
            # Check if it's possible to write to the file
            try:
                # Try to open file for writing
                with open(log_file, 'a'):
                    pass
            except PermissionError:
                print(f"{Fore.YELLOW}Warning: I don't have permission to write to file: {log_file}{Style.RESET_ALL}")
                # Use temporary file as backup
                log_file = Path(tempfile.gettempdir()) / logging_config.get('filename', 'mq_monitor.log')
                print(f"{Fore.YELLOW}Using temporary file: {log_file}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.YELLOW}Warning: Cannot write to file: {e}{Style.RESET_ALL}")
                log_file = Path(tempfile.gettempdir()) / logging_config.get('filename', 'mq_monitor.log')
                print(f"{Fore.YELLOW}Using temporary file: {log_file}{Style.RESET_ALL}")
            
            # Set rotating handler
            max_size = logging_config.get('max_size', 10485760)  # 10MB default
            backup_count = logging_config.get('backup_count', 5)
            
            try:
                file_handler = RotatingFileHandler(
                    str(log_file),
                    maxBytes=max_size,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
                file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
                log_config['handlers']['file'] = {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': str(log_file),
                    'maxBytes': max_size,
                    'backupCount': backup_count,
                    'formatter': 'verbose',
                    'encoding': 'utf-8',
                    'level': 'DEBUG' if args.verbose else 'INFO'  # File log everything
                }
                log_config['root']['handlers'].append('file')
                
                # Only logging, no output to console
                logging.debug(f"Logging set up to: {log_file}")
                
            except Exception as e:
                print(f"{Fore.YELLOW}Warning: Cannot set up logging to file: {e}{Style.RESET_ALL}")
                # Use temporary directory as backup
                temp_log = Path(tempfile.gettempdir()) / 'mq_monitor.log'
                print(f"{Fore.YELLOW}Using temporary log file: {temp_log}{Style.RESET_ALL}")
                log_config['handlers']['file'] = {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': str(temp_log),
                    'maxBytes': 10485760,
                    'backupCount': 5,
                    'formatter': 'verbose',
                    'encoding': 'utf-8',
                    'level': 'DEBUG' if args.verbose else 'INFO'  # File log everything
                }
                log_config['root']['handlers'].append('file')
        
        except Exception as e:
            print(f"{Fore.YELLOW}Warning: Cannot set up logging: {e}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Using only console logging{Style.RESET_ALL}")

    # Apply logging configuration
    logging.config.dictConfig(log_config)
    
    # These messages will only be logged, not to console
    logging.info(f"Running on system: {SYSTEM_INFO['system']} {SYSTEM_INFO['release']}")
    
    # Log absolute path to config file
    try:
        config_path = os.path.abspath(args.config)
        logging.info(f"Using config file: {config_path}")
    except Exception:
        logging.info(f"Using config file: {args.config}")
        
    # Log information about log directory
    if logging_config.get('enabled', False):
        try:
            log_dir_abs = os.path.abspath(log_dir)
            logging.info(f"Log directory: {log_dir_abs}")
            logging.info(f"Log file: {os.path.abspath(str(log_file))}")
        except Exception:
            logging.info("Cannot determine absolute path to log directory")

def safe_encode(text, encoding='utf-8'):
    """Safely encode text for MQ with platform support."""
    if isinstance(text, bytes):
        return text
    try:
        return text.encode(encoding)
    except UnicodeEncodeError:
        return text.encode(encoding, errors='replace')

def safe_decode(text, encoding='utf-8'):
    """Safely decode text from MQ with platform support."""
    if isinstance(text, str):
        return text
    try:
        return text.decode(encoding)
    except UnicodeDecodeError:
        return text.decode(encoding, errors='replace')

# Channel status mapping
CHANNEL_STATUS_MAP = {
    pymqi.CMQCFC.MQCHS_INACTIVE: "INACTIVE",
    pymqi.CMQCFC.MQCHS_BINDING: "BINDING",
    pymqi.CMQCFC.MQCHS_STARTING: "STARTING",
    pymqi.CMQCFC.MQCHS_RUNNING: "RUNNING",
    pymqi.CMQCFC.MQCHS_STOPPING: "STOPPING",
    pymqi.CMQCFC.MQCHS_RETRYING: "RETRYING",
    pymqi.CMQCFC.MQCHS_STOPPED: "STOPPED",
    pymqi.CMQCFC.MQCHS_REQUESTING: "REQUESTING",
    pymqi.CMQCFC.MQCHS_PAUSED: "PAUSED",
    pymqi.CMQCFC.MQCHS_DISCONNECTED: "DISCONNECTED",
    pymqi.CMQCFC.MQCHS_INITIALIZING: "INITIALIZING",
    pymqi.CMQCFC.MQCHS_SWITCHING: "SWITCHING",
}

# Queue type mapping
QUEUE_TYPE_MAP = {
    pymqi.CMQC.MQQT_LOCAL: "LOCAL",
    pymqi.CMQC.MQQT_MODEL: "MODEL",
    pymqi.CMQC.MQQT_ALIAS: "ALIAS",
    pymqi.CMQC.MQQT_REMOTE: "REMOTE",
    pymqi.CMQC.MQQT_CLUSTER: "CLUSTER",
}

def get_queue_usage(usage):
    """Converts numeric queue usage value to text."""
    usage_map = {
        pymqi.CMQC.MQUS_NORMAL: "NORMAL",
        pymqi.CMQC.MQUS_TRANSMISSION: "TRANSMISSION"
    }
    return usage_map.get(usage, "UNKNOWN")

def get_persistence_status(persistence):
    """Converts numeric persistence value to text."""
    persistence_map = {
        pymqi.CMQC.MQPER_PERSISTENT: "PERSISTENT",
        pymqi.CMQC.MQPER_NOT_PERSISTENT: "NOT_PERSISTENT"
    }
    return persistence_map.get(persistence, "UNKNOWN")

def get_queue_type_name(queue_type):
    """Converts numeric queue type to text description."""
    return QUEUE_TYPE_MAP.get(queue_type, "UNKNOWN")

class MQMonitor:
    def __init__(self, config):
        self.config = config
        self.channel_thresholds = config.get('channels_monitoring', {})
        self.queue_thresholds = config.get('queues_monitoring', {})
        self.system_info = SYSTEM_INFO
        
        # Set default encoding for MQ communication
        self.encoding = config.get('global', {}).get('encoding', 'utf-8')
        logging.debug(f"Using encoding for MQ communication: {self.encoding}")
        
        # Detect SSL/TLS environment
        self.ssl_env = self._setup_ssl_environment()
        logging.debug(f"SSL/TLS environment: {self.ssl_env}")
        
        # Log information about configuration
        logging.info(f"Initializing MQ monitor with {len(config.get('mq_servers', []))} servers")

    def _setup_ssl_environment(self):
        """Sets up SSL/TLS environment according to platform."""
        ssl_env = {}
        try:
            if self.system_info['system'] == 'Windows':
                ssl_key_repo = self.config.get('platform_specific', {}).get('windows', {}).get('ssl_key_repository', '%MQDATA%\\ssl\\key')
                # Expand environment variables in Windows path
                ssl_key_repo = os.path.expandvars(ssl_key_repo)
            else:
                ssl_key_repo = self.config.get('platform_specific', {}).get('unix', {}).get('ssl_key_repository', '/var/mqm/ssl/key')
            
            ssl_env['SSL_KEY_REPOSITORY'] = ssl_key_repo
            logging.debug(f"Set SSL_KEY_REPOSITORY: {ssl_key_repo}")
        except Exception as e:
            logging.warning(f"Cannot set up SSL environment: {e}")
            if self.system_info['system'] == 'Windows':
                ssl_env['SSL_KEY_REPOSITORY'] = '%MQDATA%\\ssl\\key'
            else:
                ssl_env['SSL_KEY_REPOSITORY'] = '/var/mqm/ssl/key'
        
        return ssl_env

    def connect_to_qm(self, server_config):
        """Connects to Queue Manager with respect to platform."""
        try:
            host = server_config.get('host', 'localhost')
            port = server_config.get('port', 1414)
            channel = server_config.get('channel', 'SYSTEM.DEF.SVRCONN')
            queue_manager = server_config.get('queue_manager')
            user = server_config.get('user')
            password = server_config.get('password')

            # Safely encode values
            host_b = safe_encode(host, self.encoding)
            port_b = safe_encode(str(port), self.encoding)
            channel_b = safe_encode(channel, self.encoding)
            queue_manager_b = safe_encode(queue_manager, self.encoding)
            conn_info = host_b + b'(' + port_b + b')'

            logging.debug(f"Connecting to {queue_manager} on {host}:{port}")
            
            cd = pymqi.CD()
            cd.ChannelName = channel_b
            cd.ConnectionName = conn_info
            cd.ChannelType = pymqi.CMQC.MQCHT_CLNTCONN
            cd.TransportType = pymqi.CMQC.MQXPT_TCP

            # SSL/TLS configuration with respect to platform
            if server_config.get('ssl', False):
                ssl_config = server_config.get('ssl_config', {})
                cd.SSLCipherSpec = safe_encode(ssl_config.get('cipher_spec', ''), self.encoding)
                
                # Set SSL keys according to platform
                key_repo = ssl_config.get('key_repository', self.ssl_env['SSL_KEY_REPOSITORY'])
                os.environ['MQSSLKEYR'] = key_repo
                
                logging.debug(f"SSL configuration: cipher_spec={cd.SSLCipherSpec}, key_repo={key_repo}")

            # Connect with authentication
            if user and password:
                logging.debug(f"Connecting with authentication (user: {user})")
                sco = pymqi.SCO()
                sco.UserIdentifier = safe_encode(user, self.encoding)
                sco.Password = safe_encode(password, self.encoding)
                qmgr = pymqi.QueueManager(None)
                qmgr.connectWithOptions(queue_manager_b, cd=cd, sco=sco)
                logging.info(f"Successfully connected to {queue_manager} with authentication")
            else:
                logging.debug("Connecting without authentication")
                qmgr = pymqi.QueueManager(None)
                qmgr.connectWithOptions(queue_manager_b, cd=cd)
                logging.info(f"Successfully connected to {queue_manager} without authentication")

            return qmgr

        except pymqi.MQMIError as e:
            error_msg = self._format_mq_error(e, host, queue_manager, channel)
            logging.error(f"MQ error during connection: {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            logging.error(f"Unexpected error during connection: {e}", exc_info=True)
            raise

    def _format_mq_error(self, e, host, queue_manager, channel):
        """Formats MQ errors with respect to platform and localization."""
        if e.comp == pymqi.CMQC.MQCC_FAILED:
            if e.reason == pymqi.CMQC.MQRC_HOST_NOT_AVAILABLE:
                return f"Server {host} is not available"
            elif e.reason == pymqi.CMQC.MQRC_Q_MGR_NOT_AVAILABLE:
                return f"Queue Manager {queue_manager} is not available"
            elif e.reason == pymqi.CMQC.MQRC_UNKNOWN_CHANNEL_NAME:
                return f"Channel {channel} does not exist"
            elif e.reason == pymqi.CMQC.MQRC_NOT_AUTHORIZED:
                return "Insufficient permissions for connection"
        return f"MQ server connection error: {e}"

    def get_queue_manager_status(self, qmgr, qmgr_name):
        """Gets Queue Manager status."""
        try:
            pcf = pymqi.PCFExecute(qmgr)
            
            # First, get basic information about Queue Manager
            status_info = {
                "name": qmgr_name,
                "status": STATUS_OK,
                "start_time": "Running",  # Simplified status
                "command_level": "Unknown"
            }
            
            # Query for Queue Manager information
            qmgr_response = pcf.MQCMD_INQUIRE_Q_MGR([])
            
            if qmgr_response:
                for item in qmgr_response:
                    if pymqi.CMQC.MQCA_Q_MGR_NAME in item:
                        status_info["name"] = item[pymqi.CMQC.MQCA_Q_MGR_NAME].strip().decode()
                    if pymqi.CMQC.MQIA_COMMAND_LEVEL in item:
                        status_info["command_level"] = str(item[pymqi.CMQC.MQIA_COMMAND_LEVEL])
            
            return status_info
            
        except pymqi.MQMIError as e:
            if e.comp == pymqi.CMQC.MQCC_FAILED:
                if e.reason == pymqi.CMQC.MQRC_SELECTOR_ERROR:
                    return {
                        "name": qmgr_name,
                        "status": STATUS_OK,
                        "start_time": "Running",
                        "command_level": "Unknown"
                    }
                else:
                    return {
                        "name": qmgr_name,
                        "status": STATUS_CRITICAL,
                        "start_time": "Unknown",
                        "command_level": "Unknown",
                        "error": str(e)
                    }
            logging.error(f"Error getting Queue Manager status: {e}")
            return {
                "name": qmgr_name,
                "status": STATUS_CRITICAL,
                "start_time": "Unknown",
                "command_level": "Unknown",
                "error": str(e)
            }

    def check_channel_status(self, channel_name, channel_info):
        """Checks channel status according to configured rules."""
        status = {
            "status": STATUS_OK,
            "messages": []
        }

        # Get specific configuration for channel or use global
        channel_config = self.channel_thresholds.get('specific', {}).get(channel_name, 
                                                                       self.channel_thresholds.get('global', {}))
        
        messages_config = channel_config.get('messages', {})

        # Check channel status
        if channel_config.get('required_status'):
            if channel_info['status'] != channel_config['required_status']:
                msg_config = messages_config.get('wrong_status', {
                    'severity': 'WARNING',
                    'text': f"Channel is not in required status (is {channel_info['status']}, required {channel_config['required_status']})"
                })
                status["status"] = msg_config['severity']
                status["messages"].append(msg_config['text'])

        # Check connection count
        connections = channel_info.get('connections', 0)
        if channel_config.get('max_connections'):
            if connections >= channel_config['max_connections']:
                msg_config = messages_config.get('max_connections', {
                    'severity': 'CRITICAL',
                    'text': f"Max connection count exceeded ({connections}/{channel_config['max_connections']})"
                })
                status["status"] = msg_config['severity']
                status["messages"].append(msg_config['text'])
            elif connections >= channel_config.get('warning_connections', 0):
                msg_config = messages_config.get('high_connections', {
                    'severity': 'WARNING',
                    'text': f"High connection count ({connections}/{channel_config['warning_connections']})"
                })
                status["status"] = msg_config['severity']
                status["messages"].append(msg_config['text'])

        # Check inactivity
        if channel_config.get('inactive_warning') and channel_info['status'] == "INACTIVE":
            msg_config = messages_config.get('inactive', {
                'severity': 'WARNING',
                'text': "Channel is inactive"
            })
            status["status"] = msg_config['severity']
            status["messages"].append(msg_config['text'])

        return status

    def check_queue_status(self, queue_name, queue_info):
        """Checks queue status according to configured rules."""
        status = {
            "status": STATUS_OK,
            "messages": []
        }

        # Use milder rules for system queues
        is_system_queue = queue_name.startswith("SYSTEM.")
        
        # Get specific configuration for queue or use global
        queue_config = self.queue_thresholds.get('specific', {}).get(queue_name, 
                                                                    self.queue_thresholds.get('global', {}))
        
        messages_config = queue_config.get('messages', {})

        # Check queue depth
        depth = queue_info['depth']
        if 'max_depth' in queue_config and not is_system_queue:
            if depth >= queue_config['max_depth']:
                msg_config = messages_config.get('max_depth', {
                    'severity': 'CRITICAL',
                    'text': f"Max queue depth exceeded ({depth}/{queue_config['max_depth']})"
                })
                status["status"] = msg_config['severity']
                status["messages"].append(msg_config['text'])
            elif depth >= queue_config.get('warning_depth', 0):
                msg_config = messages_config.get('high_depth', {
                    'severity': 'WARNING',
                    'text': f"High queue depth ({depth}/{queue_config['warning_depth']})"
                })
                status["status"] = msg_config['severity']
                status["messages"].append(msg_config['text'])

        # Check depth percentage
        depth_percent = queue_info['depth_percent']
        if not is_system_queue:
            if depth_percent >= queue_config.get('max_depth_percent', 100):
                msg_config = messages_config.get('max_depth_percent', {
                    'severity': 'CRITICAL',
                    'text': f"Max queue utilization exceeded ({depth_percent:.1f}%)"
                })
                status["status"] = msg_config['severity']
                status["messages"].append(msg_config['text'])
            elif depth_percent >= queue_config.get('warning_depth_percent', 80):
                msg_config = messages_config.get('high_depth_percent', {
                    'severity': 'WARNING',
                    'text': f"High queue utilization ({depth_percent:.1f}%)"
                })
                status["status"] = msg_config['severity']
                status["messages"].append(msg_config['text'])

        # Check "stuck" queue (queue with messages but no consumers)
        if queue_config.get('stuck_queue_warning') and not is_system_queue:
            if depth > 0 and queue_info['open_input'] == 0:
                msg_config = messages_config.get('stuck_messages', {
                    'severity': 'WARNING',
                    'text': f"Queue contains messages ({depth}) but has no active consumers"
                })
                status["status"] = msg_config['severity']
                status["messages"].append(msg_config['text'])

        # Check consumer count - only for non-system queues
        if 'required_consumers' in queue_config and not is_system_queue:
            if queue_info['open_input'] < queue_config['required_consumers']:
                msg_config = messages_config.get('no_consumers', {
                    'severity': 'WARNING',
                    'text': f"Insufficient consumer count ({queue_info['open_input']}/{queue_config['required_consumers']})"
                })
                status["status"] = msg_config['severity']
                status["messages"].append(msg_config['text'])

        return status

    def get_channel_status(self, qmgr, channel_pattern):
        """Gets channel status."""
        try:
            pcf = pymqi.PCFExecute(qmgr)
            
            # Query for channel status
            args = {
                pymqi.CMQCFC.MQCACH_CHANNEL_NAME: channel_pattern.encode() if isinstance(channel_pattern, str) else channel_pattern
            }
            
            try:
                response = pcf.MQCMD_INQUIRE_CHANNEL_STATUS(args)
            except pymqi.MQMIError as e:
                if e.comp == pymqi.CMQC.MQCC_FAILED and e.reason == pymqi.CMQCFC.MQRCCF_CHL_STATUS_NOT_FOUND:
                    # Channel exists, but has no status (not active)
                    channel_info = pcf.MQCMD_INQUIRE_CHANNEL(args)[0]
                    return {
                        "name": channel_info[pymqi.CMQCFC.MQCACH_CHANNEL_NAME].strip().decode(),
                        "type": channel_info.get(pymqi.CMQCFC.MQIACH_CHANNEL_TYPE, "Unknown"),
                        "status": "INACTIVE",
                        "last_msg_time": "Never",
                        "messages": 0,
                        "connections": 0
                    }
                raise
            
            if response:
                channel_info = response[0]  # Take first response
                status = channel_info.get(pymqi.CMQCFC.MQIACH_CHANNEL_STATUS, 0)
                status_text = CHANNEL_STATUS_MAP.get(status, "UNKNOWN")
                
                channel = {
                    "name": channel_info[pymqi.CMQCFC.MQCACH_CHANNEL_NAME].strip().decode(),
                    "type": channel_info.get(pymqi.CMQCFC.MQIACH_CHANNEL_TYPE, "Unknown"),
                    "status": status_text,
                    "last_msg_time": "Unknown",
                    "messages": channel_info.get(pymqi.CMQCFC.MQIACH_MSGS, 0),
                    "connections": 0  # Set to 0, as this attribute is not available
                }
                
                # Try to get last message time
                if pymqi.CMQCFC.MQCACH_LAST_MSG_TIME in channel_info:
                    channel["last_msg_time"] = channel_info[pymqi.CMQCFC.MQCACH_LAST_MSG_TIME].strip().decode()
                elif pymqi.CMQCFC.MQCACH_LAST_MSG_DATE in channel_info and pymqi.CMQCFC.MQCACH_LAST_MSG_TIME in channel_info:
                    last_date = channel_info[pymqi.CMQCFC.MQCACH_LAST_MSG_DATE].strip().decode()
                    last_time = channel_info[pymqi.CMQCFC.MQCACH_LAST_MSG_TIME].strip().decode()
                    channel["last_msg_time"] = f"{last_date} {last_time}"
                
                return channel
        
        except pymqi.MQMIError as e:
            if e.comp == pymqi.CMQC.MQCC_FAILED and e.reason == pymqi.CMQC.MQRC_UNKNOWN_OBJECT_NAME:
                return None
            logging.error(f"Error getting channel status {channel_pattern}: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error getting channel status {channel_pattern}: {e}")
            return None

    def get_queue_status(self, qmgr, queue_pattern):
        """Gets queue status."""
        try:
            pcf = pymqi.PCFExecute(qmgr)
            
            # Query for queue information
            pattern_bytes = queue_pattern if isinstance(queue_pattern, bytes) else queue_pattern.encode()
            args = {
                pymqi.CMQC.MQCA_Q_NAME: pattern_bytes
            }
            
            # First, get queue information
            queue_response = pcf.MQCMD_INQUIRE_Q(args)
            
            if queue_response:
                queue_info = queue_response[0]  # Take first response
                queue_name = queue_info[pymqi.CMQC.MQCA_Q_NAME].strip()
                queue_type = queue_info.get(pymqi.CMQC.MQIA_Q_TYPE, 0)
                
                # Skip system queues if not explicitly requested
                if queue_pattern == '*' and queue_name.startswith(b'SYSTEM.') and not queue_name.startswith(b'SYSTEM.ADMIN'):
                    return None
                
                # Then get queue status
                status_args = {
                    pymqi.CMQC.MQCA_Q_NAME: queue_name
                }
                
                try:
                    status_response = pcf.MQCMD_INQUIRE_Q_STATUS(status_args)
                    
                    if status_response:
                        status = status_response[0]
                        max_depth = queue_info.get(pymqi.CMQC.MQIA_MAX_Q_DEPTH, 0)
                        current_depth = status.get(pymqi.CMQC.MQIA_CURRENT_Q_DEPTH, 0)
                        
                        queue = {
                            "name": queue_name.decode() if isinstance(queue_name, bytes) else queue_name,
                            "type": get_queue_type_name(queue_type),
                            "depth": current_depth,
                            "max_depth": max_depth,
                            "depth_percent": (current_depth / max_depth * 100) if max_depth > 0 else 0,
                            "open_input": status.get(pymqi.CMQC.MQIA_OPEN_INPUT_COUNT, 0),
                            "open_output": status.get(pymqi.CMQC.MQIA_OPEN_OUTPUT_COUNT, 0),
                            "description": queue_info.get(pymqi.CMQC.MQCA_Q_DESC, b'').strip().decode(),
                            "cluster": queue_info.get(pymqi.CMQC.MQCA_CLUSTER_NAME, b'').strip().decode(),
                            "usage": get_queue_usage(queue_info.get(pymqi.CMQC.MQIA_USAGE, 0)),
                            "persistence": get_persistence_status(queue_info.get(pymqi.CMQC.MQIA_DEF_PERSISTENCE, 0))
                        }
                        
                        return queue
                        
                except pymqi.MQMIError as e:
                    if e.comp == pymqi.CMQC.MQCC_FAILED and e.reason == pymqi.CMQC.MQRC_SELECTOR_ERROR:
                        # Some queues do not support all attributes
                        return None
                    raise
                
        except pymqi.MQMIError as e:
            if e.comp == pymqi.CMQC.MQCC_FAILED and e.reason == pymqi.CMQC.MQRC_UNKNOWN_OBJECT_NAME:
                return None
            logging.error(f"Error getting queue status {queue_pattern}: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error getting queue status {queue_pattern}: {e}")
            return None

    def monitor_server(self, server_config):
        """Monitors MQ server according to configuration."""
        server_name = server_config["name"]
        print(f"{Fore.CYAN}Monitoring server {server_name}...{Style.RESET_ALL}")
        logging.info(f"Connecting to server {server_name}...")
        
        # Get list of Queue Managers to monitor
        queue_managers = server_config.get("queue_managers", [])
        if not queue_managers:
            logging.warning(f"No Queue Managers configured for server {server_name}")
            return
            
        logging.info(f"Found {len(queue_managers)} Queue Managers to monitor on server {server_name}")
        
        for qm_config in queue_managers:
            qm_name = qm_config["name"]
            logging.info(f"Monitoring Queue Manager {qm_name} on server {server_name}")
            
            try:
                # Create a copy of server config and update it with QM specific settings
                qm_server_config = server_config.copy()
                qm_server_config.update({
                    "queue_manager": qm_name,
                    "channel": qm_config["channel"],
                    "port": qm_config.get("port", server_config.get("port", 1414)),
                    "user": qm_config.get("user"),
                    "password": qm_config.get("password"),
                    "ssl": qm_config.get("ssl", False),
                    "ssl_config": qm_config.get("ssl_config", {})
                })
                
                qmgr = self.connect_to_qm(qm_server_config)
                logging.info(f"Successfully connected to Queue Manager {qm_name} on server {server_name}")
                
                # Get Queue Manager status
                qmgr_status = self.get_queue_manager_status(qmgr, qm_name)
                logging.info(f"Got Queue Manager status: {qmgr_status['name']}, status: {qmgr_status['status']}")
                
                # Monitor channels
                channels_status = []
                pcf = pymqi.PCFExecute(qmgr)
                
                # Get channel list according to QM specific configuration
                channels_to_monitor = qm_config.get('channels_to_monitor', ['*'])
                logging.debug(f"Monitoring channels with patterns: {channels_to_monitor}")
                for channel_pattern in channels_to_monitor:
                    try:
                        args = {pymqi.CMQCFC.MQCACH_CHANNEL_NAME: channel_pattern.encode()}
                        channels = pcf.MQCMD_INQUIRE_CHANNEL(args)
                        
                        for channel_info in channels:
                            channel_name = channel_info[pymqi.CMQCFC.MQCACH_CHANNEL_NAME].strip()
                            channel = self.get_channel_status(qmgr, channel_name)
                            if channel:
                                status = self.check_channel_status(channel["name"], channel)
                                channel["check_status"] = status
                                channels_status.append(channel)
                                
                                # Log channel status only for non-system channels or if debug is enabled
                                if not channel['name'].startswith('SYSTEM.') or logging.getLogger().getEffectiveLevel() == logging.DEBUG:
                                    log_msg = f"Channel: {channel['name']}, Status: {channel['status']}, Check Status: {status['status']}"
                                    if status['messages']:
                                        log_msg += f", Messages: {', '.join(status['messages'])}"
                                    logging.info(log_msg)
                    except pymqi.MQMIError as e:
                        error_msg = f"Error getting channel list for pattern {channel_pattern}: {e}"
                        logging.error(error_msg)
                        # Print to console only if it's not a system channel pattern
                        if not channel_pattern.startswith('SYSTEM.'):
                            print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
                
                # Monitor queues
                queues_status = []
                
                # Get queue list according to QM specific configuration
                queues_to_monitor = qm_config.get('queues_to_monitor', ['*'])
                logging.debug(f"Monitoring queues with patterns: {queues_to_monitor}")
                for queue_pattern in queues_to_monitor:
                    try:
                        args = {pymqi.CMQC.MQCA_Q_NAME: queue_pattern.encode()}
                        queues = pcf.MQCMD_INQUIRE_Q(args)
                        
                        for queue_info in queues:
                            queue_name = queue_info[pymqi.CMQC.MQCA_Q_NAME].strip()
                            # Skip system queues if not explicitly requested
                            if queue_name.startswith(b'SYSTEM.') and not queue_name.startswith(b'SYSTEM.ADMIN'):
                                continue
                            
                            queue = self.get_queue_status(qmgr, queue_name)
                            if queue:
                                status = self.check_queue_status(queue["name"], queue)
                                queue["check_status"] = status
                                queues_status.append(queue)
                                
                                # Log queue status only for non-system queues or if debug is enabled
                                if not queue['name'].startswith('SYSTEM.') or logging.getLogger().getEffectiveLevel() == logging.DEBUG:
                                    log_msg = f"Queue: {queue['name']}, Type: {queue['type']}, Depth: {queue['depth']}/{queue['max_depth']} ({queue['depth_percent']:.1f}%), Consumers: {queue['open_input']}, Status: {status['status']}"
                                    if status['messages']:
                                        log_msg += f", Messages: {', '.join(status['messages'])}"
                                    logging.info(log_msg)
                    except pymqi.MQMIError as e:
                        error_msg = f"Error getting queue list for pattern {queue_pattern}: {e}"
                        logging.error(error_msg)
                        # Print to console only if it's not a system queue pattern
                        if not queue_pattern.startswith('SYSTEM.'):
                            print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
                
                # Generate output for this Queue Manager
                logging.info(f"Generating output for Queue Manager {qm_name} on server {server_name}")
                self.format_and_send_output(server_name, qmgr_status, channels_status, queues_status)
                
            except Exception as e:
                error_msg = f"Error monitoring Queue Manager {qm_name} on server {server_name}: {e}"
                logging.error(error_msg, exc_info=True)
                print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
            
            finally:
                if 'qmgr' in locals():
                    try:
                        qmgr.disconnect()
                        logging.info(f"Disconnected from Queue Manager {qm_name} on server {server_name}")
                    except Exception as e:
                        logging.error(f"Error disconnecting from Queue Manager {qm_name} on server {server_name}: {e}")
                        
        logging.info(f"Finished monitoring all Queue Managers on server {server_name}")

    def format_and_send_output(self, server_name, qmgr_status, channels_status, queues_status):
        """Formats and sends output according to configuration."""
        output_format = self.config["output"]["format"]
        colored = self.config["output"].get("colored", True)
        
        if output_format == "json":
            output = self.format_json_output(server_name, qmgr_status, channels_status, queues_status)
        elif output_format == "csv":
            output = self.format_csv_output(server_name, qmgr_status, channels_status, queues_status)
        elif output_format == "table":
            output = self.format_table_output(server_name, qmgr_status, channels_status, queues_status)
        else:  # simple line format
            output = self.format_console_output(server_name, qmgr_status, channels_status, queues_status, colored)
        
        print(output)
        
        # Write to log
        if "log_file" in self.config["output"]:
            with open(self.config["output"]["log_file"], "a") as f:
                f.write(output + "\n\n")
        
        # Write monitoring results to log, if logging is enabled
        logging_config = self.config["output"].get("logging", {})
        if logging_config.get("enabled", False):
            # Create non-colored version of output for log
            if output_format not in ["json", "csv"]:
                log_output = self.format_console_output(server_name, qmgr_status, channels_status, queues_status, colored=False)
            else:
                log_output = output
            
            # Split output into lines and write to log
            for line in log_output.split('\n'):
                if line.strip():  # Skip empty lines
                    logging.info(line)
            
            # Add separator for better readability
            logging.info("=" * 80)

    def format_console_output(self, server_name, qmgr_status, channels_status, queues_status, colored=True):
        """Formats output for console in new format."""
        output = []
        current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        
        # Queue Manager output
        qm_status_text = f"{current_time} - {qmgr_status['status']} - QueueManagerState - "
        qm_status_text += f"IBM MQ Queue Manager {qmgr_status['name']} is {qmgr_status['status'].lower()} on {server_name}"
        output.append(self.colorize_line(qm_status_text, qmgr_status['status'], colored))
        
        # Channels output
        if channels_status:
            for channel in channels_status:
                # Skip system channels unless explicitly requested
                if channel['name'].startswith('SYSTEM.') and not channel['name'].startswith('SYSTEM.ADMIN'):
                    continue
                
                channel_text = f"{current_time} - {channel['check_status']['status']} - ChannelState - "
                channel_text += f"Channel {channel['name']} is {channel['status'].lower()} on {qmgr_status['name']}"
                if channel['check_status'].get('messages'):
                    channel_text += f" ({', '.join(channel['check_status']['messages'])})"
                output.append(self.colorize_line(channel_text, channel['check_status']['status'], colored))
        
        # Queues output
        if queues_status:
            for queue in queues_status:
                # Skip system queues unless explicitly requested
                if queue['name'].startswith('SYSTEM.') and not queue['name'].startswith('SYSTEM.ADMIN'):
                    continue
                
                queue_status = queue['check_status']['status']
                queue_text = f"{current_time} - {queue_status} - QueueState - "
                queue_text += f"Queue {queue['name']} on {qmgr_status['name']} - "
                queue_text += f"depth: {queue['depth']}/{queue['max_depth']} ({queue['depth_percent']:.1f}%), "
                queue_text += f"consumers: {queue['open_input']}"
                if queue['check_status'].get('messages'):
                    queue_text += f" ({', '.join(queue['check_status']['messages'])})"
                output.append(self.colorize_line(queue_text, queue_status, colored))
        
        return "\n".join(output)

    def colorize_line(self, text, status, colored=True):
        """Colors the entire line according to status."""
        if not colored:
            return text
        
        if status == STATUS_OK:
            return f"{Fore.GREEN}{text}{Style.RESET_ALL}"
        elif status == STATUS_WARNING:
            return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"
        elif status == STATUS_CRITICAL:
            return f"{Fore.RED}{text}{Style.RESET_ALL}"
        else:
            return f"{Fore.WHITE}{text}{Style.RESET_ALL}"

    def format_json_output(self, server_name, qmgr_status, channels_status, queues_status):
        """Formats output to JSON format."""
        return json.dumps({
            "server": server_name,
            "timestamp": datetime.now().isoformat(),
            "queue_manager": qmgr_status,
            "channels": channels_status,
            "queues": queues_status
        }, indent=2)

    def format_table_output(self, server_name, qmgr_status, channels_status, queues_status):
        """Formátuje výstup do tabulkového formátu."""
        output = []
        
        # Hlavička serveru
        output.append(f"=== Server: {server_name} - {qmgr_status['name']} ===\n")
        
        # Queue Manager tabulka
        output.append("Queue Manager:")
        qm_headers = ["NAME", "STATUS", "START TIME", "COMMAND LEVEL"]
        qm_data = [[
            qmgr_status['name'],
            qmgr_status['status'],
            qmgr_status['start_time'],
            qmgr_status.get('command_level', 'Unknown')
        ]]
        output.append(tabulate(qm_data, headers=qm_headers, tablefmt='grid'))
        output.append("")
        
        # Channels tabulka
        if channels_status:
            output.append("Channels:")
            ch_headers = ["NAME", "TYPE", "STATUS", "MESSAGES", "LAST MSG TIME", "CHECK STATUS"]
            ch_data = []
            for channel in channels_status:
                if not channel['name'].startswith('SYSTEM.') or channel['name'].startswith('SYSTEM.ADMIN'):
                    ch_data.append([
                        channel['name'],
                        channel.get('type', 'Unknown'),
                        channel['status'],
                        channel.get('messages', 0),
                        channel.get('last_msg_time', 'Never'),
                        channel['check_status']['status']
                    ])
            output.append(tabulate(ch_data, headers=ch_headers, tablefmt='grid'))
            output.append("")
        
        # Queues tabulka
        if queues_status:
            output.append("Queues:")
            q_headers = ["NAME", "TYPE", "DEPTH", "%FULL", "CONSUMERS", "CHECK STATUS", "MESSAGES"]
            q_data = []
            for queue in queues_status:
                if not queue['name'].startswith('SYSTEM.') or queue['name'].startswith('SYSTEM.ADMIN'):
                    messages = ', '.join(queue['check_status'].get('messages', [])) if queue['check_status'].get('messages') else ''
                    q_data.append([
                        queue['name'],
                        queue['type'],
                        f"{queue['depth']}/{queue['max_depth']}",
                        f"{queue['depth_percent']:.1f}%",
                        f"{queue['open_input']}/1",
                        queue['check_status']['status'],
                        messages
                    ])
            output.append(tabulate(q_data, headers=q_headers, tablefmt='grid'))
        
        return "\n".join(output)

    def format_csv_output(self, server_name, qmgr_status, channels_status, queues_status):
        """Formátuje výstup do CSV formátu."""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Queue Manager info
        writer.writerow(["Type", "Server", "QM Name", "Status", "Start Time", "Command Level"])
        writer.writerow(["QueueManager", server_name, qmgr_status['name'], qmgr_status['status'], 
                        qmgr_status['start_time'], qmgr_status.get('command_level', 'Unknown')])
        
        # Channels info
        if channels_status:
            writer.writerow([])
            writer.writerow(["Type", "Name", "Status", "Messages", "Last Message Time", "Check Status", "Check Messages"])
            for channel in channels_status:
                if not channel['name'].startswith('SYSTEM.') or channel['name'].startswith('SYSTEM.ADMIN'):
                    writer.writerow([
                        "Channel",
                        channel['name'],
                        channel['status'],
                        channel.get('messages', 0),
                        channel.get('last_msg_time', 'Never'),
                        channel['check_status']['status'],
                        '; '.join(channel['check_status'].get('messages', []))
                    ])
        
        # Queues info
        if queues_status:
            writer.writerow([])
            writer.writerow(["Type", "Name", "Queue Type", "Depth", "Max Depth", "Depth %", "Consumers", "Check Status", "Check Messages"])
            for queue in queues_status:
                if not queue['name'].startswith('SYSTEM.') or queue['name'].startswith('SYSTEM.ADMIN'):
                    writer.writerow([
                        "Queue",
                        queue['name'],
                        queue['type'],
                        queue['depth'],
                        queue['max_depth'],
                        f"{queue['depth_percent']:.1f}",
                        queue['open_input'],
                        queue['check_status']['status'],
                        '; '.join(queue['check_status'].get('messages', []))
                    ])
        
        return output.getvalue()

def validate_config(config):
    """Validates config file and checks all required mappings."""
    required_fields = {
        "mq_servers": list,
        "output": dict,
        "channels_monitoring": dict,
        "queues_monitoring": dict
    }

    # Check basic structure
    for field, field_type in required_fields.items():
        if field not in config:
            raise ValueError(f"Missing required section '{field}' in config file")
        if not isinstance(config[field], field_type):
            raise ValueError(f"Section '{field}' has wrong type, expected {field_type.__name__}")

    # Check output configuration
    output_config = config["output"]
    if "format" not in output_config:
        raise ValueError("Missing required field 'format' in output section")
    if output_config["format"] not in ["console", "json", "csv", "table"]:
        raise ValueError("Invalid output format, allowed values are: console, json, csv, table")

    # Check server configuration
    for server in config["mq_servers"]:
        required_server_fields = {
            "name": str,
            "host": str,
            "port": int,  # Port is required at server level
            "queue_managers": list
        }
        for field, field_type in required_server_fields.items():
            if field not in server:
                raise ValueError(f"Missing required field '{field}' in server configuration {server.get('name', 'UNKNOWN')}")
            if not isinstance(server[field], field_type):
                raise ValueError(f"Field '{field}' has wrong type in server configuration {server.get('name', 'UNKNOWN')}")
        
        # Validate Queue Manager configurations
        for qm in server["queue_managers"]:
            required_qm_fields = {
                "name": str,
                "channel": str
            }
            for field, field_type in required_qm_fields.items():
                if field not in qm:
                    raise ValueError(f"Missing required field '{field}' in Queue Manager configuration for server {server.get('name', 'UNKNOWN')}")
                if not isinstance(qm[field], field_type):
                    raise ValueError(f"Field '{field}' has wrong type in Queue Manager configuration for server {server.get('name', 'UNKNOWN')}")
                
            # Check port if specified at QM level
            if "port" in qm and not isinstance(qm["port"], int):
                raise ValueError(f"Field 'port' has wrong type in Queue Manager configuration for server {server.get('name', 'UNKNOWN')}")

    # Check channel monitoring
    channels_config = config["channels_monitoring"]
    if "global" not in channels_config:
        raise ValueError("Missing 'global' section in channel monitoring configuration")
    
    required_channel_fields = {
        "required_status": str,
        "inactive_warning": bool,
        "max_connections": int,
        "warning_connections": int
    }
    
    for field, field_type in required_channel_fields.items():
        if field not in channels_config["global"]:
            raise ValueError(f"Missing required field '{field}' in global channel configuration")
        if not isinstance(channels_config["global"][field], field_type):
            raise ValueError(f"Field '{field}' has wrong type in global channel configuration")

    # Check queue monitoring
    queues_config = config["queues_monitoring"]
    if "global" not in queues_config:
        raise ValueError("Missing 'global' section in queue monitoring configuration")
    
    required_queue_fields = {
        "max_depth": int,
        "warning_depth": int,
        "max_depth_percent": int,
        "warning_depth_percent": int,
        "stuck_queue_warning": bool,
        "required_consumers": int
    }
    
    for field, field_type in required_queue_fields.items():
        if field not in queues_config["global"]:
            raise ValueError(f"Missing required field '{field}' in global queue configuration")
        if not isinstance(queues_config["global"][field], field_type):
            raise ValueError(f"Field '{field}' has wrong type in global queue configuration")

    # Check message configuration
    for monitoring in [channels_config, queues_config]:
        if "messages" in monitoring.get("global", {}):
            for msg_type, msg_config in monitoring["global"]["messages"].items():
                if not isinstance(msg_config, dict):
                    raise ValueError(f"Invalid message configuration for type '{msg_type}'")
                if "severity" not in msg_config or "text" not in msg_config:
                    raise ValueError(f"Missing required field 'severity' or 'text' for message type '{msg_type}'")
                if msg_config["severity"] not in [STATUS_OK, STATUS_WARNING, STATUS_CRITICAL]:
                    raise ValueError(f"Invalid severity value for message type '{msg_type}'")

    return True

def main():
    """Main function of the program."""
    parser = argparse.ArgumentParser(description="IBM MQ Monitoring Script v2")
    parser.add_argument("-c", "--config", default="config.yaml", 
                      help="Path to config file (default: config.yaml)")
    parser.add_argument("-s", "--server", help="Monitor only specific server from config")
    parser.add_argument("-o", "--output", choices=["console", "json", "csv", "table"], 
                      help="Output format")
    parser.add_argument("-v", "--verbose", action="store_true", 
                      help="Show detailed output")
    args = parser.parse_args()
    
    # Basic logging setup (will be overwritten after loading config)
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    try:
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
            
        # Validate config
        try:
            validate_config(config)
            logging.info("Config was successfully validated")
            # Get absolute path to config file
            config_abs_path = os.path.abspath(args.config)
            print(f"{Fore.GREEN}Config was successfully loaded from: {config_abs_path}{Style.RESET_ALL}")
        except ValueError as e:
            print(f"{Fore.RED}Config error: {e}{Style.RESET_ALL}")
            sys.exit(1)
            
        # Set up logging according to config
        setup_logging(config, args)
        logging.info(f"Script started with config: {args.config}")
        
        # Add separator for start of new run
        logging.info("=" * 80)
        logging.info("START MONITORING")
        logging.info("=" * 80)
            
    except Exception as e:
        print(f"{Fore.RED}Error loading config: {e}{Style.RESET_ALL}")
        sys.exit(1)
    
    # Override output format from command line
    if args.output:
        config["output"]["format"] = args.output
        logging.info(f"Output format set to: {args.output}")
    
    # Create monitor
    monitor = MQMonitor(config)
    
    # Filter servers
    servers = config["mq_servers"]
    if args.server:
        servers = [s for s in servers if s["name"] == args.server]
        if not servers:
            print(f"{Fore.RED}Error: Server '{args.server}' not found in config.{Style.RESET_ALL}")
            logging.error(f"Server '{args.server}' not found in config")
            sys.exit(1)
        logging.info(f"Monitoring only server: {args.server}")
    
    # Monitor servers
    start_time = time.time()
    print(f"{Fore.CYAN}Starting IBM MQ server monitoring...{Style.RESET_ALL}")
    for server in servers:
        monitor.monitor_server(server)
    end_time = time.time()
    
    # Log end of monitoring
    duration = end_time - start_time
    logging.info("=" * 80)
    logging.info(f"END MONITORING - Duration: {duration:.2f} seconds")
    logging.info("=" * 80)
    print(f"{Fore.GREEN}Monitoring completed in {duration:.2f} seconds{Style.RESET_ALL}")

if __name__ == "__main__":
    main() 
