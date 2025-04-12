# Nix Proxy Manager

A simple command-line tool for managing proxy settings for the Nix daemon.

## Features

- Supports macOS and Linux systems
- Simple command-line interface
- Easily set, view, or remove proxy configurations for the Nix daemon

## Installation

### Method 1: Run directly with Nix

```bash
nix run github:aleadag/nix-proxy-manager
```

### Method 2: Clone the repository

```bash
git clone https://github.com/aleadag/nix-proxy-manager.git
cd nix-proxy-manager
```

### Method 3: Copy to system path

```bash
sudo cp main.py /usr/local/bin/nix-proxy-manager
sudo chmod +x /usr/local/bin/nix-proxy-manager
```

### Method 4: Using symbolic link

```bash
sudo ln -s "$(pwd)/main.py" /usr/local/bin/nix-proxy-manager
sudo chmod +x main.py
```

## Usage

### Set proxy

```bash
sudo nix-proxy-manager set http://127.0.0.1:7890
```

### Remove proxy

```bash
sudo nix-proxy-manager unset
```

### Show current proxy settings

```bash
sudo nix-proxy-manager show
```

## Requirements

- Python 3
- Root privileges (needs to be run with sudo)
- Supported operating systems: macOS or Linux

## How it works

- On macOS, the tool modifies the `/Library/LaunchDaemons/org.nixos.nix-daemon.plist` file
- On Linux, the tool manages the `/etc/systemd/system/nix-daemon.service.d/proxy-override.conf` file

## License

[MIT](LICENSE)

## Contributing

Pull Requests and Issues are welcome!

## Related Projects

This project is based on the solution discussed in [NixOS issue #1472](https://github.com/NixOS/nix/issues/1472#issuecomment-1532955973). 