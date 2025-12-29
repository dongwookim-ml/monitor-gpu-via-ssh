# gpu-monitor

A beautiful CLI tool to monitor GPU usage across multiple SSH servers in real-time.

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)

## Features

- Real-time GPU monitoring across multiple servers via SSH
- Beautiful TUI with colored progress bars
- Three display modes: **essentials**, **full**, and **compact**
- Configurable refresh rate
- Concurrent SSH connections for fast updates
- Automatic SSH config support (`~/.ssh/config`)

## Installation

```bash
# Clone the repository
git clone https://github.com/dongwookim-ml/monitor-gpu-via-ssh.git
cd monitor-gpu-via-ssh

# Install with pip
pip install -e .
```

## Usage

```bash
# Basic usage (essentials mode, 2s refresh, servers a-i)
gpu-monitor

# Full mode with temperature, power, and processes
gpu-monitor --full

# Custom refresh rate (5 seconds)
gpu-monitor --refresh 5

# Monitor specific servers
gpu-monitor --servers a,b,c

# Combine options
gpu-monitor --full --refresh 3 --servers a,b,c,d

# Compact mode for small screens
gpu-monitor --compact
```

## Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--refresh` | `-r` | Refresh interval in seconds | 2.0 |
| `--full` | `-f` | Show full details (temp, power, processes) | Off |
| `--essentials` | `-e` | Show essentials only (utilization, memory) | On |
| `--compact` | `-c` | Compact multi-column mode for small screens | Off |
| `--servers` | `-s` | Comma-separated list of servers | a,b,c,d,e,f,g,h,i |
| `--timeout` | `-t` | SSH connection timeout in seconds | 10.0 |
| `--version` | | Show version | |
| `--help` | | Show help message | |

## Display Modes

### Essentials Mode (default)
Shows GPU utilization and memory usage with colored progress bars.

```
╭─────────────────── GPU Monitor ───────────────────╮
│  Servers: 9 │ Refresh: 2s │ Mode: essentials      │
╰───────────────────────────────────────────────────╯

┏━━━━━━━━┳━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Server ┃ GPU ┃ Name               ┃ Utilization      ┃ Memory                 ┃
┡━━━━━━━━╇━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
│ a      │ 0   │ NVIDIA A100        │ ████████░░ 80.0% │ ██████░░░░ 12.0/24.0G  │
│ a      │ 1   │ NVIDIA A100        │ ██░░░░░░░░ 20.0% │ ████░░░░░░  8.0/24.0G  │
│ b      │ 0   │ NVIDIA A100        │ ██████████ 100%  │ ████████░░ 20.0/24.0G  │
└────────┴─────┴────────────────────┴──────────────────┴────────────────────────┘
```

### Full Mode (`--full`)
Adds temperature, power consumption, and running processes.

### Compact Mode (`--compact`)
Multi-column layout optimized for small screens (e.g., 13" laptops with ~30 lines).
Displays servers in a grid layout to minimize vertical space.

```
GPU Monitor │ 9 srv │ 2.0s │ 20:52:15
[a]                         [b]                        [c]
0:█░░░░ 20% █░░░░ 7.8G      0:█░░░░ 20% █░░░░ 7.8G     0:█░░░░ 20% █░░░░ 7.8G
1:█░░░░ 30% █░░░░ 8.8G      1:█░░░░ 30% █░░░░ 8.8G     1:█░░░░ 30% █░░░░ 8.8G
2:██░░░ 40% ██░░░ 9.8G      2:██░░░ 40% ██░░░ 9.8G     2:██░░░ 40% ██░░░ 9.8G
3:██░░░ 50% ██░░░10.7G      3:██░░░ 50% ██░░░10.7G     3:██░░░ 50% ██░░░10.7G
[d]                         [e] OFF                    [f]
0:█░░░░ 20% █░░░░ 7.8G                                 0:█░░░░ 20% █░░░░ 7.8G
...
```

## Prerequisites

- Python 3.10 or higher
- SSH access to target servers (via `~/.ssh/config` or direct hostname)
- NVIDIA GPUs with `nvidia-smi` installed on target servers

## SSH Configuration

The tool uses your `~/.ssh/config` for host resolution. Example configuration:

```ssh-config
Host a
    HostName server-a.example.com
    User myuser
    IdentityFile ~/.ssh/id_rsa

Host b
    HostName server-b.example.com
    User myuser
    IdentityFile ~/.ssh/id_rsa
```

## License

MIT
