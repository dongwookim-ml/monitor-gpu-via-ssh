"""Parser for nvidia-smi output."""

from dataclasses import dataclass, field


@dataclass
class GPUProcess:
    """Information about a process running on a GPU."""

    pid: int
    name: str
    memory_used: float  # MiB


@dataclass
class GPUInfo:
    """Information about a single GPU."""

    index: int
    name: str
    utilization: float  # percentage
    memory_used: float  # MiB
    memory_total: float  # MiB
    temperature: float  # Celsius
    power_draw: float  # Watts
    power_limit: float  # Watts
    processes: list[GPUProcess] = field(default_factory=list)

    @property
    def memory_percent(self) -> float:
        """Memory usage as percentage."""
        if self.memory_total == 0:
            return 0.0
        return (self.memory_used / self.memory_total) * 100

    @property
    def power_percent(self) -> float:
        """Power usage as percentage of limit."""
        if self.power_limit == 0:
            return 0.0
        return (self.power_draw / self.power_limit) * 100


@dataclass
class ServerGPUData:
    """GPU data for a server."""

    server: str
    online: bool
    gpus: list[GPUInfo] = field(default_factory=list)
    error: str | None = None


def parse_nvidia_smi_output(server: str, output: str, error: str | None = None) -> ServerGPUData:
    """
    Parse nvidia-smi CSV output.

    Expected format (per line):
    index, name, utilization.gpu, memory.used, memory.total, temperature.gpu, power.draw, power.limit

    Args:
        server: Server hostname
        output: nvidia-smi CSV output
        error: Error message if command failed

    Returns:
        ServerGPUData with parsed GPU information
    """
    if error or not output.strip():
        return ServerGPUData(server=server, online=False, error=error or "No output")

    gpus = []
    for line in output.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 8:
            continue

        try:
            gpu = GPUInfo(
                index=int(parts[0]),
                name=parts[1],
                utilization=_parse_float(parts[2]),
                memory_used=_parse_float(parts[3]),
                memory_total=_parse_float(parts[4]),
                temperature=_parse_float(parts[5]),
                power_draw=_parse_float(parts[6]),
                power_limit=_parse_float(parts[7]),
            )
            gpus.append(gpu)
        except (ValueError, IndexError):
            continue

    if not gpus:
        return ServerGPUData(server=server, online=False, error="No GPUs found")

    return ServerGPUData(server=server, online=True, gpus=gpus)


def parse_process_output(output: str) -> dict[str, list[GPUProcess]]:
    """
    Parse nvidia-smi process output.

    Expected format (per line):
    gpu_uuid, pid, process_name, used_memory

    Args:
        output: nvidia-smi process CSV output

    Returns:
        Dictionary mapping GPU UUID to list of processes
    """
    processes: dict[str, list[GPUProcess]] = {}

    for line in output.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 4:
            continue

        try:
            gpu_uuid = parts[0]
            process = GPUProcess(
                pid=int(parts[1]),
                name=parts[2],
                memory_used=_parse_float(parts[3]),
            )
            if gpu_uuid not in processes:
                processes[gpu_uuid] = []
            processes[gpu_uuid].append(process)
        except (ValueError, IndexError):
            continue

    return processes


def _parse_float(value: str) -> float:
    """Parse a float value, handling special cases."""
    value = value.strip()
    if value in ("[N/A]", "N/A", "[Not Supported]", ""):
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0
