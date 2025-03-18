#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
IBM MQ Diagnostic Script
-------------------------
This script checks the environment and availability of IBM MQ server.
Supports various configurations and can be used for any MQ server.

Developed by: robert.pesout@tietoevry.com
Version: 1.0.0
"""

import os
import sys
import socket
import platform
import subprocess
import argparse
import re
from colorama import init, Fore, Style
from pathlib import Path

# Initialize colorama for colored output
init(autoreset=True)

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="IBM MQ Diagnostic Tool - Developed by robert.pesout@tietoevry.com"
    )
    parser.add_argument("-c", "--config", default="config.yaml",
                       help="Path to configuration file (default: config.yaml)")
    parser.add_argument("-s", "--server",
                       help="Test only specific server from configuration")
    parser.add_argument("--host",
                       help="MQ server hostname or IP (overrides configuration)")
    parser.add_argument("--port", type=int,
                       help="MQ server port (overrides configuration)")
    parser.add_argument("--qm", "--queue-manager",
                       help="Queue Manager name (overrides configuration)")
    parser.add_argument("--channel",
                       help="Channel name (overrides configuration)")
    parser.add_argument("--user",
                       help="Username (overrides configuration)")
    parser.add_argument("--password",
                       help="Password (overrides configuration)")
    parser.add_argument("--no-auth", action="store_true",
                       help="Force connection without authentication")
    parser.add_argument("--ssl", action="store_true",
                       help="Use SSL/TLS connection")
    parser.add_argument("--ssl-cipher",
                       help="SSL cipher specification")
    parser.add_argument("--key-repository",
                       help="Path to SSL key repository")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Show detailed output")
    return parser.parse_args()

def print_header(text):
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"{Fore.CYAN}{text}")
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")

def check_python_version():
    print_header("Checking Python Version")
    version = sys.version.split()[0]
    print(f"Python version: {version}")
    if tuple(map(int, version.split('.'))) >= (3, 6):
        print(f"{Fore.GREEN}✓ Python version is sufficient (>= 3.6)")
    else:
        print(f"{Fore.RED}✗ Python version is too low (required >= 3.6)")

def check_pymqi_installation():
    print_header("Checking pymqi Installation")
    try:
        import pymqi
        print(f"{Fore.GREEN}✓ pymqi library is installed")
        print(f"pymqi version: {pymqi.__version__}")
    except ImportError as e:
        print(f"{Fore.RED}✗ pymqi library is not installed: {e}")
        print(f"{Fore.YELLOW}Tip: Install pymqi using: pip install pymqi")

def check_library_exists(path):
    """Check if MQ library exists in given path."""
    lib_name = "mqic.dll" if platform.system() == "Windows" else "libmqm.so"
    lib_path = os.path.join(path, lib_name)
    
    if os.path.exists(lib_path):
        print(f"{Fore.GREEN}✓ Found library: {lib_path}")
        return True
    return False

def get_mq_installation_path():
    """Get IBM MQ installation path."""
    mq_paths = ["/opt/mqm", "/usr/local/mqm"]
    for path in mq_paths:
        if os.path.exists(path):
            return path
    return None

def get_mq_version():
    """Get IBM MQ version using dspmqver command."""
    mq_path = get_mq_installation_path()
    if not mq_path:
        return "Unknown"
    
    try:
        cmd = f'sudo -u mqm {mq_path}/bin/dspmqver'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            version_match = re.search(r'Version:\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
            if version_match:
                return version_match.group(1)
    except Exception as e:
        print(f"{Fore.RED}Error getting MQ version: {e}")
    return "Unknown"

def check_port_status(host, port, timeout=5):
    """Check if port is open using socket connection."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def get_qmgr_list():
    """Get list of Queue Managers using dspmq command."""
    mq_path = get_mq_installation_path()
    if not mq_path:
        print(f"{Fore.RED}Error: MQ installation path not found")
        return []
    
    try:
        cmd = f'sudo -u mqm {mq_path}/bin/dspmq'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            qmgrs = []
            for line in result.stdout.splitlines():
                match = re.search(r'QMNAME\((.*?)\)\s+STATUS\((.*?)\)', line)
                if match:
                    qmgr_name = match.group(1)
                    qmgr_status = match.group(2)
                    
                    # Get port for this Queue Manager
                    port = get_qmgr_port(qmgr_name, mq_path)
                    
                    # Get permissions
                    perms = check_qmgr_permissions(qmgr_name, mq_path)
                    
                    qmgrs.append({
                        'name': qmgr_name,
                        'status': qmgr_status,
                        'port': port,
                        'permissions': perms
                    })
            return qmgrs
    except FileNotFoundError:
        print(f"{Fore.RED}Error: dspmq command not found")
    except Exception as e:
        print(f"{Fore.RED}Error getting Queue Manager list: {e}")
    return []

def get_qmgr_port(qmgr_name, mq_path):
    """Get Queue Manager listener port using runmqsc command."""
    try:
        # Get port from LSSTATUS
        cmd = f'sudo -u mqm bash -c "echo \\"DISPLAY LSSTATUS(*) PORT\\" | {mq_path}/bin/runmqsc {qmgr_name}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            # Look for line with PORT(number)
            port_match = re.search(r'PORT\((\d+)\)', result.stdout)
            if port_match:
                return int(port_match.group(1))
            
            # If port not found in LSSTATUS, try DISPLAY QMGR
            cmd = f'sudo -u mqm bash -c "echo \\"DISPLAY QMGR PORT\\" | {mq_path}/bin/runmqsc {qmgr_name}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                port_match = re.search(r'PORT\((\d+)\)', result.stdout)
                if port_match:
                    return int(port_match.group(1))
    except Exception as e:
        print(f"{Fore.RED}Error getting port for {qmgr_name}: {e}")
    return None

def check_qmgr_permissions(qmgr_name, mq_path):
    """Check permissions for Queue Manager."""
    try:
        # Check CHLAUTH
        cmd = f'sudo -u mqm bash -c "echo \\"DISPLAY QMGR CHLAUTH\\" | {mq_path}/bin/runmqsc {qmgr_name}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        permissions = {
            'chlauth': 'ENABLED' in result.stdout,
            'can_connect': result.returncode == 0
        }
        
        # Check access to system queue
        cmd = f'sudo -u mqm bash -c "echo \\"DISPLAY Q(SYSTEM.DEFAULT.LOCAL.QUEUE)\\" | {mq_path}/bin/runmqsc {qmgr_name}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        permissions['can_browse'] = result.returncode == 0
        
        # Add additional Queue Manager information
        cmd = f'sudo -u mqm bash -c "echo \\"DISPLAY QMGR ALL\\" | {mq_path}/bin/runmqsc {qmgr_name}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            permissions['details'] = result.stdout
        
        return permissions
    except Exception as e:
        print(f"{Fore.RED}Error checking permissions for {qmgr_name}: {e}")
        return None

def check_mq_client_libraries():
    print_header("Checking IBM MQ Client Libraries")
    
    # List of possible MQ library locations
    mq_paths = [
        "/opt/mqm/lib64",
        "/opt/mqm/lib",
        "C:\\Program Files\\IBM\\MQ\\bin64",
        "C:\\Program Files\\IBM\\MQ\\bin",
        os.environ.get("MQ_LIB_PATH", "")
    ]
    
    # List of key MQ libraries
    mq_libraries = [
        ("libmqic" if platform.system() != "Windows" else "mqic"),
        ("libmqm" if platform.system() != "Windows" else "mqm")
    ]
    
    found_libraries = False
    
    for path in mq_paths:
        if not path or not os.path.exists(path):
            continue
        
        print(f"\nChecking path: {path}")
        for lib in mq_libraries:
            lib_extensions = [".so", ".dll", ".sl", ".a", ""]
            for ext in lib_extensions:
                lib_path = os.path.join(path, f"{lib}{ext}")
                if os.path.exists(lib_path):
                    print(f"{Fore.GREEN}✓ Found library: {lib_path}")
                    found_libraries = True
    
    if not found_libraries:
        print(f"{Fore.RED}✗ No MQ libraries were found")
        print(f"{Fore.YELLOW}Tip: Install IBM MQ client libraries from:")
        print(f"{Fore.YELLOW}https://www.ibm.com/support/pages/downloading-ibm-mq-9x-clients")

def check_mq_installations():
    print_header("Checking IBM MQ Installations")
    installations = []
    
    mq_path = get_mq_installation_path()
    if mq_path:
        try:
            cmd = f'sudo -u mqm {mq_path}/bin/dspmqver'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                version_info = result.stdout
                # Parse version from output
                for line in version_info.splitlines():
                    if "Version:" in line:
                        version = line.split("Version:")[1].strip()
                        installations.append({
                            "version": version,
                            "path": mq_path,
                            "type": "Full" if os.path.exists(os.path.join(mq_path, "bin", "strmqm")) else "Client"
                        })
                        break
        except Exception as e:
            print(f"{Fore.YELLOW}⚠ Error checking MQ version at {mq_path}: {e}")

    if installations:
        print(f"{Fore.GREEN}Found {len(installations)} IBM MQ installation(s):\n")
        for inst in installations:
            print(f"{Fore.CYAN}╔══ Installation Details {'═' * 45}")
            print(f"{Fore.CYAN}║")
            print(f"{Fore.CYAN}║ {Fore.RESET}Version: {inst['version']}")
            print(f"{Fore.CYAN}║ {Fore.RESET}Path: {inst['path']}")
            print(f"{Fore.CYAN}║ {Fore.RESET}Type: {inst['type']}")
            
            # Display additional installation information
            if inst['type'] == "Full":
                try:
                    cmd = f'sudo -u mqm {mq_path}/bin/dspmq -o installation'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"{Fore.CYAN}║")
                        print(f"{Fore.CYAN}║ {Fore.RESET}Queue Managers in this Installation:")
                        print(f"{Fore.CYAN}║ {Fore.RESET}{'─' * 58}")
                        
                        # Split and format each line
                        for line in result.stdout.splitlines():
                            if line.strip():
                                # Split line into parts
                                parts = re.findall(r'(\w+)\((.*?)\)', line)
                                if parts:
                                    print(f"{Fore.CYAN}║ {Fore.RESET}", end="")
                                    for key, value in parts:
                                        if key == "QMNAME":
                                            print(f"{Fore.GREEN}{value:20}", end="")
                                        elif key == "INSTNAME":
                                            print(f"{Fore.YELLOW}{value:15}", end="")
                                        elif key == "INSTPATH":
                                            print(f"{value:20}", end="")
                                        elif key == "INSTVER":
                                            print(f"{Fore.CYAN}{value}", end="")
                                    print()
                except Exception:
                    pass
            print(f"{Fore.CYAN}╚{'═' * 60}")
            print()
    else:
        print(f"{Fore.YELLOW}No IBM MQ installations found in standard locations")
        print(f"{Fore.YELLOW}Note: This might be normal if using standalone client libraries")

def check_network_connectivity(host, port):
    print_header(f"Basic Network Tests for {host}:{port}")
    
    # TCP Port Test (like telnet)
    print(f"{Fore.CYAN}1. Basic TCP Port Test{Style.RESET_ALL}")
    try:
        sock = socket.create_connection((host, port), timeout=5)
        sock.close()
        print(f"{Fore.GREEN}✓ TCP port {port} is open and accepting connections")
        port_available = True
    except socket.error as e:
        print(f"{Fore.RED}✗ Cannot connect to TCP port {port}: {e}")
        port_available = False
        
        # If connection failed, try netstat
        print(f"\n{Fore.YELLOW}Checking local ports with netstat...{Style.RESET_ALL}")
        try:
            if platform.system() == "Windows":
                cmd = f"netstat -an | findstr :{port}"
            else:
                cmd = f"netstat -tuln | grep :{port}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.stdout:
                print(f"{Fore.GREEN}Found port {port} in netstat output:")
                print(result.stdout)
            else:
                print(f"{Fore.YELLOW}Port {port} not found in netstat output")
        except Exception as e:
            print(f"{Fore.RED}Error running netstat: {e}")
    
    return port_available

def test_mq_connection(server_config, args=None):
    print(f"\n{Fore.CYAN}2. IBM MQ Connection Test{Style.RESET_ALL}")
    try:
        import pymqi
        
        # Use command line arguments if available
        host = args.host if args and args.host else server_config['host']
        port = args.port if args and args.port else server_config['port']
        channel = args.channel if args and args.channel else server_config['channel']
        queue_manager = args.qm if args and args.qm else server_config['queue_manager']
        user = args.user if args and args.user else server_config.get('user')
        password = args.password if args and args.password else server_config.get('password')
        
        # SSL configuration
        use_ssl = args.ssl if args and args.ssl else server_config.get('ssl', False)
        ssl_cipher = args.ssl_cipher if args and args.ssl_cipher else server_config.get('cipher_spec')
        key_repo = args.key_repository if args and args.key_repository else server_config.get('key_repository')

        # Convert values to bytes for pymqi
        host_b = host.encode('utf-8')
        port_b = str(port).encode('utf-8')
        channel_b = channel.encode('utf-8')
        queue_manager_b = queue_manager.encode('utf-8')
        conn_info = host_b + b'(' + port_b + b')'
        
        print(f"Attempting to connect to Queue Manager {queue_manager}")
        print(f"Channel: {channel}")
        print(f"Connection info: {host}({port})")
        
        try:
            # Create CD object
            cd = pymqi.CD()
            cd.ChannelName = channel_b
            cd.ConnectionName = conn_info
            cd.ChannelType = pymqi.CMQC.MQCHT_CLNTCONN
            cd.TransportType = pymqi.CMQC.MQXPT_TCP

            # SSL configuration
            if use_ssl:
                print(f"{Fore.CYAN}Using SSL/TLS connection")
                cd.SSLCipherSpec = ssl_cipher.encode('utf-8') if ssl_cipher else None
                if key_repo:
                    cd.SSLKeyRepository = key_repo.encode('utf-8')

            # Connect to Queue Manager
            if not args.no_auth and user and password:
                print(f"Connecting with authentication (user: {user})")
                sco = pymqi.SCO()
                sco.UserIdentifier = user.encode('utf-8')
                sco.Password = password.encode('utf-8')
                qmgr = pymqi.QueueManager(None)
                qmgr.connect_with_options(queue_manager_b, cd, sco)
            else:
                print("Connecting without authentication")
                qmgr = pymqi.QueueManager(None)
                qmgr.connect_with_options(queue_manager_b, cd)

            print(f"{Fore.GREEN}✓ Successfully connected to Queue Manager {queue_manager}")
            
            # Try to get Queue Manager attributes
            attrs = qmgr.inquire(pymqi.CMQC.MQCA_Q_MGR_NAME)
            print(f"{Fore.GREEN}✓ Queue Manager name confirmed: {attrs.strip()}")
            
            # Test access to system queue
            try:
                system_queue = pymqi.Queue(qmgr, 'SYSTEM.DEFAULT.LOCAL.QUEUE', pymqi.CMQC.MQOO_INQUIRE)
                print(f"{Fore.GREEN}✓ Access to system queue OK")
                system_queue.close()
            except pymqi.MQMIError as e:
                print(f"{Fore.YELLOW}⚠ Cannot access system queue: {e}")
            
            qmgr.disconnect()
            print(f"{Fore.GREEN}✓ Successfully disconnected from Queue Manager")
            return True
            
        except pymqi.MQMIError as e:
            print(f"{Fore.RED}✗ MQ Error: {e}")
            print(f"{Fore.YELLOW}Error details:")
            print(f"  Completion Code: {e.comp}")
            print(f"  Reason Code: {e.reason}")
            
            # If authentication fails, try without it
            if e.reason == pymqi.CMQC.MQRC_NOT_AUTHORIZED and user and not args.no_auth:
                print(f"{Fore.YELLOW}Authentication failed, trying without credentials...")
                try:
                    qmgr = pymqi.QueueManager(None)
                    qmgr.connect_with_options(queue_manager_b, cd)
                    print(f"{Fore.GREEN}✓ Successfully connected without authentication")
                    
                    attrs = qmgr.inquire(pymqi.CMQC.MQCA_Q_MGR_NAME)
                    print(f"{Fore.GREEN}✓ Queue Manager name confirmed: {attrs.strip()}")
                    
                    qmgr.disconnect()
                    print(f"{Fore.GREEN}✓ Successfully disconnected from Queue Manager")
                    return True
                except pymqi.MQMIError as e2:
                    print(f"{Fore.RED}✗ Connection without authentication also failed:")
                    print(f"{Fore.RED}  Completion Code: {e2.comp}, Reason: {e2.reason}")
            return False
            
    except Exception as e:
        print(f"{Fore.RED}✗ Error during MQ connection test: {e}")
        return False

def check_mq_server_info(host, port, channel, queue_manager, args=None):
    print_header("MQ Server Configuration Details")
    print(f"Queue Manager: {queue_manager}")
    print(f"Channel: {channel}")
    print(f"Host: {host}")
    print(f"Port: {port}")
    
    if args and args.verbose:
        print("\nAdditional Information:")
        print(f"SSL/TLS: {'Yes' if args.ssl else 'No'}")
        if args.ssl:
            print(f"SSL Cipher: {args.ssl_cipher if args.ssl_cipher else 'Default'}")
            print(f"Key Repository: {args.key_repository if args.key_repository else 'Not set'}")
    
    # Attempt to run MQSC command for testing
    if platform.system() != "Windows":
        try:
            cmd = f"echo 'DISPLAY QMGR' | runmqsc {queue_manager}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"{Fore.GREEN}✓ Queue Manager is available locally")
            else:
                print(f"{Fore.YELLOW}⚠ Queue Manager is not available locally (may not be an issue for remote connections)")
        except Exception as e:
            print(f"{Fore.YELLOW}⚠ Cannot test local Queue Manager availability: {e}")

def display_qmgr_details():
    """Display detailed information about Queue Managers."""
    print_header("Queue Manager Details")
    
    mq_path = get_mq_installation_path()
    if not mq_path:
        print(f"{Fore.RED}Error: MQ installation path not found")
        return
        
    qmgrs = get_qmgr_list()
    
    if not qmgrs:
        print(f"{Fore.YELLOW}⚠ No Queue Managers found or unable to retrieve Queue Manager list")
        return
    
    print(f"Found {len(qmgrs)} Queue Manager(s):\n")
    
    for qmgr in qmgrs:
        print(f"{Fore.CYAN}╔══ Queue Manager: {qmgr['name']} {'═' * 40}")
        print(f"{Fore.CYAN}║")
        print(f"{Fore.CYAN}║ {Fore.RESET}Status: {Fore.GREEN if qmgr['status'] == 'RUNNING' else Fore.RED}{qmgr['status']}")
        
        # Display detailed information about Queue Manager
        try:
            cmd = f'sudo -u mqm bash -c "echo \\"DISPLAY QMGR ALL\\" | {mq_path}/bin/runmqsc {qmgr["name"]}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0 and 'AMQ8408I' in result.stdout:
                print(f"{Fore.CYAN}║")
                print(f"{Fore.CYAN}║ {Fore.RESET}Queue Manager Configuration:")
                for line in result.stdout.splitlines():
                    if any(key in line for key in ['PORT', 'DESCR', 'DEADQ', 'DEFXMITQ']):
                        print(f"{Fore.CYAN}║   {Fore.RESET}{line.strip()}")
        except Exception:
            pass

        # Display listener information
        try:
            # First get listener configuration
            cmd = f'sudo -u mqm bash -c "echo \\"DISPLAY LISTENER(*)\\" | {mq_path}/bin/runmqsc {qmgr["name"]}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            listener_config = {}
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if 'LISTENER(' in line:
                        matches = re.findall(r'(\w+)\((.*?)\)', line)
                        for key, value in matches:
                            listener_config[key] = value

            # Then get listener status
            cmd = f'sudo -u mqm bash -c "echo \\"DISPLAY LSSTATUS(*)\\" | {mq_path}/bin/runmqsc {qmgr["name"]}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0 and ('AMQ8631I' in result.stdout or 'AMQ8630I' in result.stdout):
                print(f"{Fore.CYAN}║")
                print(f"{Fore.CYAN}║ {Fore.RESET}Listener Status:")
                for line in result.stdout.splitlines():
                    if 'LISTENER(' in line:
                        matches = re.findall(r'(\w+)\((.*?)\)', line)
                        listener_info = {}
                        for key, value in matches:
                            listener_info[key] = value
                        
                        # Display detailed information about listener
                        print(f"{Fore.CYAN}║   {Fore.RESET}Listener name: {Fore.GREEN}{listener_info.get('LISTENER', 'N/A')}")
                        print(f"{Fore.CYAN}║   {Fore.RESET}Status: {Fore.GREEN if listener_info.get('STATUS') == 'RUNNING' else Fore.RED}{listener_info.get('STATUS', 'N/A')}")
                        if 'PORT' in listener_config:
                            print(f"{Fore.CYAN}║   {Fore.RESET}Port: {listener_config.get('PORT', 'N/A')}")
                        if 'TRPTYPE' in listener_config:
                            print(f"{Fore.CYAN}║   {Fore.RESET}Transport type: {listener_config.get('TRPTYPE', 'N/A')}")
                        if 'CONTROL' in listener_config:
                            print(f"{Fore.CYAN}║   {Fore.RESET}Control: {listener_config.get('CONTROL', 'N/A')}")
        except Exception as e:
            print(f"{Fore.CYAN}║   {Fore.YELLOW}⚠ Unable to get listener information: {e}")

        # Display information about SVRCONN channels
        try:
            cmd = f'sudo -u mqm bash -c "echo \\"DISPLAY CHANNEL(*) CHLTYPE WHERE(CHLTYPE EQ SVRCONN)\\" | {mq_path}/bin/runmqsc {qmgr["name"]}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"{Fore.CYAN}║")
                print(f"{Fore.CYAN}║ {Fore.RESET}Server-Connection Channels:")
                
                channel_info = {}
                current_channel = None
                
                for line in result.stdout.splitlines():
                    if 'CHANNEL(' in line:
                        matches = re.findall(r'(\w+)\((.*?)\)', line)
                        for key, value in matches:
                            if key == 'CHANNEL':
                                current_channel = value
                                channel_info[current_channel] = {'name': value}
                            elif current_channel:
                                channel_info[current_channel][key] = value
                
                # Get channel status
                cmd = f'sudo -u mqm bash -c "echo \\"DISPLAY CHSTATUS(*) WHERE(CHLTYPE EQ SVRCONN)\\" | {mq_path}/bin/runmqsc {qmgr["name"]}"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        if 'CHANNEL(' in line:
                            matches = re.findall(r'(\w+)\((.*?)\)', line)
                            channel_name = None
                            status_info = {}
                            for key, value in matches:
                                if key == 'CHANNEL':
                                    channel_name = value
                                else:
                                    status_info[key] = value
                            if channel_name and channel_name in channel_info:
                                channel_info[channel_name].update(status_info)
                
                # Display information about each channel
                for channel_name, info in channel_info.items():
                    print(f"{Fore.CYAN}║   {Fore.RESET}Channel: {Fore.GREEN}{channel_name}")
                    if 'STATUS' in info:
                        status_color = Fore.GREEN if info['STATUS'] == 'RUNNING' else Fore.RED
                        print(f"{Fore.CYAN}║   {Fore.RESET}Status: {status_color}{info.get('STATUS', 'N/A')}")
                    if 'MCAUSER' in info:
                        print(f"{Fore.CYAN}║   {Fore.RESET}MCAUSER: {info.get('MCAUSER', 'N/A')}")
                    if 'SSLCIPH' in info:
                        print(f"{Fore.CYAN}║   {Fore.RESET}SSL Cipher: {info.get('SSLCIPH', 'NONE')}")
                    print(f"{Fore.CYAN}║")
                
        except Exception as e:
            print(f"{Fore.CYAN}║   {Fore.YELLOW}⚠ Unable to get SVRCONN channel information: {e}")
        
        if qmgr['port']:
            print(f"{Fore.CYAN}║")
            print(f"{Fore.CYAN}║ {Fore.RESET}Port Status:")
            if check_port_status('localhost', qmgr['port']):
                print(f"{Fore.CYAN}║   {Fore.GREEN}✓ Port {qmgr['port']} is open")
            else:
                print(f"{Fore.CYAN}║   {Fore.RED}✗ Port {qmgr['port']} is not accessible")
        
        if qmgr['permissions']:
            print(f"{Fore.CYAN}║")
            print(f"{Fore.CYAN}║ {Fore.RESET}Security & Permissions:")
            print(f"{Fore.CYAN}║   {Fore.RESET}Channel Authentication: {'Enabled' if qmgr['permissions']['chlauth'] else 'Disabled'}")
            print(f"{Fore.CYAN}║   {Fore.RESET}Can Connect: {Fore.GREEN + '✓' if qmgr['permissions']['can_connect'] else Fore.RED + '✗'}")
            print(f"{Fore.CYAN}║   {Fore.RESET}Can Browse System Queues: {Fore.GREEN + '✓' if qmgr['permissions']['can_browse'] else Fore.RED + '✗'}")
            
            # Display active channels
            try:
                cmd = f'sudo -u mqm bash -c "echo \\"DISPLAY CHSTATUS(*) WHERE(STATUS NE INACTIVE)\\" | {mq_path}/bin/runmqsc {qmgr["name"]}"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0 and 'AMQ8417I' in result.stdout:
                    print(f"{Fore.CYAN}║")
                    print(f"{Fore.CYAN}║ {Fore.RESET}Active Channels:")
                    for line in result.stdout.splitlines():
                        if 'CHANNEL(' in line:
                            print(f"{Fore.CYAN}║   {Fore.RESET}{line.strip()}")
            except Exception:
                pass
        else:
            print(f"{Fore.CYAN}║")
            print(f"{Fore.CYAN}║ {Fore.YELLOW}⚠ Unable to retrieve permissions information")
        
        print(f"{Fore.CYAN}╚{'═' * 60}")
        print()

def main():
    args = parse_arguments()
    print_header("IBM MQ Diagnostic Tool - Developed by robert.pesout@tietoevry.com")
    
    # Check system environment
    check_python_version()
    check_pymqi_installation()
    check_mq_client_libraries()
    check_mq_installations()
    
    # Add Queue Manager details section
    display_qmgr_details()
    
    # Load configuration
    try:
        import yaml
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
            
        # Filter servers by --server argument
        servers = config.get('mq_servers', [])
        if args.server:
            servers = [s for s in servers if s.get('name') == args.server]
            if not servers:
                print(f"{Fore.RED}Server '{args.server}' not found in configuration")
                return
        
        for server in servers:
            name = server.get('name', 'Unknown')
            print_header(f"Testing server: {name}")
            
            # First do basic network connectivity test
            host = args.host if args.host else server.get('host', 'localhost')
            port = args.port if args.port else server.get('port', 1414)
            
            if check_network_connectivity(host, port):
                # If network test passes, try MQ connection
                test_mq_connection(server, args)
                check_mq_server_info(
                    host,
                    port,
                    args.channel if args.channel else server.get('channel', ''),
                    args.qm if args.qm else server.get('queue_manager', ''),
                    args
                )
    
    except Exception as e:
        print(f"{Fore.RED}Error loading configuration: {e}")
        print(f"{Fore.YELLOW}Tip: Make sure config.yaml exists and has the correct format")

if __name__ == "__main__":
    main() 
