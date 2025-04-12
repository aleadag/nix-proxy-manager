#!/usr/bin/env python3
"""
  Nix Proxy Manager - Configure proxy settings for nix-daemon

  This script manages proxy settings for Nix daemon across different operating systems.
  It sets or removes proxy settings based on command line arguments.
  
  Usage:
    nix-proxy-manager set <proxy_url>   # Set proxy
    nix-proxy-manager unset             # Remove proxy
    nix-proxy-manager show              # Show current proxy settings
  
  Requirements:
    - Will auto-elevate to root permissions if needed

  https://github.com/NixOS/nix/issues/1472#issuecomment-1532955973
"""
import os
import platform
import plistlib
import shlex
import subprocess
import sys
import argparse
from pathlib import Path


def get_current_proxy_macos():
    """Get the current nix-daemon proxy settings for macOS"""
    nix_daemon_plist = Path("/Library/LaunchDaemons/org.nixos.nix-daemon.plist")
    
    if not nix_daemon_plist.exists():
        return None
    
    try:
        pl = plistlib.loads(nix_daemon_plist.read_bytes())
        
        if "EnvironmentVariables" not in pl:
            return None
        
        return pl["EnvironmentVariables"].get("http_proxy")
    except Exception as e:
        print(f"Error reading plist file: {e}")
        return None


def get_current_proxy_linux():
    """Get the current nix-daemon proxy settings for Linux"""
    proxy_config = Path("/etc/systemd/system/nix-daemon.service.d/proxy-override.conf")
    
    if not proxy_config.exists():
        return None
    
    try:
        content = proxy_config.read_text()
        for line in content.splitlines():
            if "http_proxy" in line and "=" in line:
                parts = line.split("=", 1)
                if len(parts) == 2:
                    return parts[1].strip().strip('"')
        return None
    except Exception as e:
        print(f"Error reading proxy config: {e}")
        return None


def set_proxy_macos(proxy_url):
    """Set the nix-daemon proxy for macOS"""
    nix_daemon_plist = Path("/Library/LaunchDaemons/org.nixos.nix-daemon.plist")
    
    pl = plistlib.loads(nix_daemon_plist.read_bytes())
    
    # Ensure EnvironmentVariables exists
    if "EnvironmentVariables" not in pl:
        pl["EnvironmentVariables"] = {}
    
    if proxy_url:
        # If proxy URL is provided, set the proxy
        pl["EnvironmentVariables"]["http_proxy"] = proxy_url
        pl["EnvironmentVariables"]["https_proxy"] = proxy_url
        print(f"Setting macOS proxy to {proxy_url}")
    else:
        # Otherwise remove proxy settings
        pl["EnvironmentVariables"].pop("http_proxy", None)
        pl["EnvironmentVariables"].pop("https_proxy", None)
        print("Removing macOS proxy settings")
    
    # Write changes
    os.chmod(nix_daemon_plist, 0o644)
    nix_daemon_plist.write_bytes(plistlib.dumps(pl))
    os.chmod(nix_daemon_plist, 0o444)
    
    # Reload service
    for cmd in (
        f"launchctl unload {nix_daemon_plist}",
        f"launchctl load {nix_daemon_plist}",
    ):
        print(cmd)
        subprocess.run(shlex.split(cmd), capture_output=False)


def set_proxy_linux(proxy_url):
    """Set the nix-daemon proxy for Linux"""
    systemd_dir = Path("/etc/systemd/system/nix-daemon.service.d")
    proxy_config = systemd_dir / "proxy-override.conf"
    
    if proxy_url:
        # If proxy URL is provided, create config file
        systemd_dir.mkdir(parents=True, exist_ok=True)
        
        config_content = f"""[Service]
Environment="http_proxy={proxy_url}"
Environment="https_proxy={proxy_url}"
Environment="all_proxy={proxy_url}"
"""
        proxy_config.write_text(config_content)
        print(f"Setting Linux proxy to {proxy_url}")
    else:
        # Otherwise remove config file
        if proxy_config.exists():
            proxy_config.unlink()
            print("Removing Linux proxy settings")
        else:
            print("No proxy was set, nothing to remove")
    
    # Reload systemd config and restart nix-daemon
    for cmd in (
        "systemctl daemon-reload",
        "systemctl restart nix-daemon",
    ):
        print(cmd)
        subprocess.run(shlex.split(cmd), capture_output=False)


def show_current_proxy(system):
    """Show current proxy settings"""
    if system == "Darwin":
        proxy = get_current_proxy_macos()
    elif system == "Linux":
        proxy = get_current_proxy_linux()
    else:
        print(f"Unsupported operating system: {system}")
        return 1
    
    if proxy:
        print(f"Current proxy: {proxy}")
    else:
        print("No proxy is currently set")
    
    return 0


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Nix Proxy Manager - Configure proxy settings for nix-daemon"
    )
    
    # Create subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Set proxy command
    set_parser = subparsers.add_parser("set", help="Set proxy for nix-daemon")
    set_parser.add_argument("proxy_url", help="Proxy URL (e.g. http://127.0.0.1:7890)")
    
    # Remove proxy command
    subparsers.add_parser("unset", help="Remove proxy settings for nix-daemon")
    
    # Show current proxy settings command
    subparsers.add_parser("show", help="Show current proxy settings")
    
    # Parameters compatible with old version usage
    parser.add_argument("legacy_proxy", nargs="?", help=argparse.SUPPRESS)
    
    args = parser.parse_args()
    
    # Handle compatibility with old version
    if not args.command and args.legacy_proxy:
        args.command = "set"
        args.proxy_url = args.legacy_proxy
    elif not args.command and not args.legacy_proxy:
        # Default to showing help
        parser.print_help()
        sys.exit(0)
    
    return args


def needs_root_for_command(command):
    """Check if the given command requires root privileges"""
    # "show" command doesn't need root privileges
    if command == "show":
        return False
    return True


def run_with_elevated_privileges(args):
    """Run command with elevated privileges"""
    # Convert argument list to command line argument string
    cmd_args = []
    if hasattr(args, 'command') and args.command:
        cmd_args.append(args.command)
        if args.command == "set" and hasattr(args, 'proxy_url'):
            cmd_args.append(args.proxy_url)
    
    # Choose privilege elevation tool
    sudo_cmd = "sudo"
    try:
        # Try to find pkexec
        subprocess.run(["which", "pkexec"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        sudo_cmd = "pkexec"
    except subprocess.CalledProcessError:
        pass
    
    try:
        # Run command with privilege elevation tool
        print(f"Root privileges required, running with {sudo_cmd}...")
        cmd = [sudo_cmd, sys.executable, os.path.abspath(__file__)] + cmd_args
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Privilege elevation failed: {e}")
        return 1
    except Exception as e:
        print(f"Error during execution: {e}")
        return 1


def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # If not root and command requires root privileges, try to run with elevated privileges
    if os.geteuid() != 0 and hasattr(args, 'command') and needs_root_for_command(args.command):
        return run_with_elevated_privileges(args)
    
    # Already have root privileges or command doesn't need root privileges, execute directly
    # Get current operating system
    system = platform.system()
    
    # Execute appropriate action based on command
    if args.command == "set":
        if system == "Darwin":
            set_proxy_macos(args.proxy_url)
        elif system == "Linux":
            set_proxy_linux(args.proxy_url)
        else:
            print(f"Unsupported operating system: {system}")
            return 1
    elif args.command == "unset":
        if system == "Darwin":
            set_proxy_macos(None)
        elif system == "Linux":
            set_proxy_linux(None)
        else:
            print(f"Unsupported operating system: {system}")
            return 1
    elif args.command == "show":
        return show_current_proxy(system)
    
    return 0


if __name__ == "__main__":
    exit(main()) 