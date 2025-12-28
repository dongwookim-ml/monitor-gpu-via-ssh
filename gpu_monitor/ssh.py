"""SSH connection and command execution module."""

import asyncio
from dataclasses import dataclass
from pathlib import Path

import asyncssh


@dataclass
class SSHResult:
    """Result of an SSH command execution."""

    server: str
    success: bool
    output: str
    error: str | None = None


async def run_nvidia_smi(server: str, timeout: float = 10.0) -> SSHResult:
    """
    Run nvidia-smi on a remote server via SSH.

    Args:
        server: Hostname or SSH alias to connect to
        timeout: Connection timeout in seconds

    Returns:
        SSHResult with command output or error
    """
    try:
        # Use SSH config file for host resolution
        ssh_config_path = Path.home() / ".ssh" / "config"
        config = str(ssh_config_path) if ssh_config_path.exists() else None

        async with asyncssh.connect(
            server,
            config=config,
            known_hosts=None,  # Use system known_hosts
            connect_timeout=timeout,
        ) as conn:
            # Get XML output for easier parsing
            result = await conn.run(
                "nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw,power.limit --format=csv,noheader,nounits",
                timeout=timeout,
            )

            if result.exit_status == 0:
                return SSHResult(
                    server=server,
                    success=True,
                    output=result.stdout,
                )
            else:
                return SSHResult(
                    server=server,
                    success=False,
                    output="",
                    error=result.stderr or f"Exit code: {result.exit_status}",
                )

    except asyncssh.DisconnectError as e:
        return SSHResult(server=server, success=False, output="", error=f"Disconnected: {e}")
    except asyncssh.PermissionDenied as e:
        return SSHResult(server=server, success=False, output="", error=f"Permission denied: {e}")
    except asyncssh.HostKeyNotVerifiable as e:
        return SSHResult(server=server, success=False, output="", error=f"Host key error: {e}")
    except asyncio.TimeoutError:
        return SSHResult(server=server, success=False, output="", error="Connection timeout")
    except OSError as e:
        return SSHResult(server=server, success=False, output="", error=f"Connection failed: {e}")
    except Exception as e:
        return SSHResult(server=server, success=False, output="", error=str(e))


async def run_nvidia_smi_processes(server: str, timeout: float = 10.0) -> SSHResult:
    """
    Get running processes on GPUs via nvidia-smi.

    Args:
        server: Hostname or SSH alias to connect to
        timeout: Connection timeout in seconds

    Returns:
        SSHResult with process information
    """
    try:
        ssh_config_path = Path.home() / ".ssh" / "config"
        config = str(ssh_config_path) if ssh_config_path.exists() else None

        async with asyncssh.connect(
            server,
            config=config,
            known_hosts=None,
            connect_timeout=timeout,
        ) as conn:
            result = await conn.run(
                "nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader,nounits 2>/dev/null || echo ''",
                timeout=timeout,
            )

            return SSHResult(
                server=server,
                success=True,
                output=result.stdout,
            )

    except Exception as e:
        return SSHResult(server=server, success=False, output="", error=str(e))


async def fetch_all_servers(
    servers: list[str], timeout: float = 10.0, include_processes: bool = False
) -> dict[str, tuple[SSHResult, SSHResult | None]]:
    """
    Fetch GPU data from all servers concurrently.

    Args:
        servers: List of server hostnames
        timeout: Connection timeout per server
        include_processes: Whether to fetch process information

    Returns:
        Dictionary mapping server names to their results
    """
    tasks = []
    for server in servers:
        tasks.append(run_nvidia_smi(server, timeout))
        if include_processes:
            tasks.append(run_nvidia_smi_processes(server, timeout))

    results = await asyncio.gather(*tasks)

    output = {}
    if include_processes:
        for i, server in enumerate(servers):
            output[server] = (results[i * 2], results[i * 2 + 1])
    else:
        for i, server in enumerate(servers):
            output[server] = (results[i], None)

    return output
