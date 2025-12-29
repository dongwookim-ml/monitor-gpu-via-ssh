"""Rich TUI display module for GPU monitoring."""

from datetime import datetime

from rich.columns import Columns
from rich.console import Console, Group, RenderableType
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text

from .parser import GPUInfo, ServerGPUData


def get_color_for_percent(percent: float) -> str:
    """Get color based on percentage value."""
    if percent < 50:
        return "green"
    elif percent < 80:
        return "yellow"
    else:
        return "red"


def create_bar(percent: float, width: int = 10) -> Text:
    """Create a colored progress bar."""
    filled = int(percent / 100 * width)
    empty = width - filled
    color = get_color_for_percent(percent)

    bar = Text()
    bar.append("█" * filled, style=color)
    bar.append("░" * empty, style="dim")
    return bar


def create_header_panel(
    server_count: int, refresh_rate: float, mode: str, last_update: datetime | None = None
) -> Panel:
    """Create the header panel with status information."""
    status_text = Text()
    status_text.append("  Servers: ", style="dim")
    status_text.append(str(server_count), style="cyan bold")
    status_text.append("  │  Refresh: ", style="dim")
    status_text.append(f"{refresh_rate}s", style="cyan bold")
    status_text.append("  │  Mode: ", style="dim")
    status_text.append(mode, style="cyan bold")

    if last_update:
        status_text.append("  │  Updated: ", style="dim")
        status_text.append(last_update.strftime("%H:%M:%S"), style="cyan")

    return Panel(
        status_text,
        title="[bold magenta]GPU Monitor[/bold magenta]",
        border_style="magenta",
        padding=(0, 1),
    )


def create_server_block(data: ServerGPUData) -> RenderableType:
    """Create a compact block for a single server."""
    lines = []

    # Server header
    header = Text()
    header.append(f"[{data.server}]", style="bold cyan")

    if not data.online:
        header.append(" ", style="dim")
        header.append("OFF", style="red bold")
        lines.append(header)
    else:
        lines.append(header)
        for gpu in data.gpus:
            line = Text()
            line.append(f"{gpu.index}:", style="dim")

            # Utilization bar
            util_bar = create_bar(gpu.utilization, width=5)
            line.append_text(util_bar)
            line.append(f"{gpu.utilization:3.0f}%", style=get_color_for_percent(gpu.utilization))

            line.append(" ", style="dim")

            # Memory bar
            mem_bar = create_bar(gpu.memory_percent, width=5)
            line.append_text(mem_bar)
            line.append(f"{gpu.memory_used/1024:4.1f}G", style=get_color_for_percent(gpu.memory_percent))

            lines.append(line)

    return Group(*lines)


def create_compact_multicolumn(server_data: list[ServerGPUData], num_columns: int = 3) -> Columns:
    """Create a multi-column compact display for small screens."""
    sorted_data = sorted(server_data, key=lambda x: x.server)
    blocks = [create_server_block(data) for data in sorted_data]

    return Columns(blocks, equal=True, expand=True)


def create_compact_header(
    server_count: int, refresh_rate: float, last_update: datetime | None = None
) -> Text:
    """Create a compact header for small screens."""
    header = Text()
    header.append("GPU Monitor", style="bold magenta")
    header.append(f" │ {server_count} srv │ {refresh_rate}s", style="dim")
    if last_update:
        header.append(f" │ {last_update.strftime('%H:%M:%S')}", style="dim cyan")
    return header


def create_essentials_table(server_data: list[ServerGPUData]) -> Table:
    """Create the essentials mode table."""
    table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="blue",
        expand=True,
        padding=(0, 1),
    )

    table.add_column("Server", style="bold white", width=8)
    table.add_column("GPU", justify="center", width=5)
    table.add_column("Name", width=20, overflow="ellipsis")
    table.add_column("Utilization", width=20)
    table.add_column("Memory", width=24)

    for data in sorted(server_data, key=lambda x: x.server):
        if not data.online:
            table.add_row(
                data.server,
                "-",
                Text("OFFLINE", style="red bold"),
                Text(data.error or "Connection failed", style="dim red"),
                "",
            )
            continue

        for i, gpu in enumerate(data.gpus):
            server_name = data.server if i == 0 else ""

            # Utilization bar
            util_bar = create_bar(gpu.utilization)
            util_text = Text()
            util_text.append_text(util_bar)
            util_text.append(f" {gpu.utilization:5.1f}%", style=get_color_for_percent(gpu.utilization))

            # Memory bar
            mem_bar = create_bar(gpu.memory_percent)
            mem_text = Text()
            mem_text.append_text(mem_bar)
            mem_text.append(
                f" {gpu.memory_used/1024:4.1f}/{gpu.memory_total/1024:4.1f}G",
                style=get_color_for_percent(gpu.memory_percent),
            )

            table.add_row(
                server_name,
                str(gpu.index),
                gpu.name[:20],
                util_text,
                mem_text,
            )

    return table


def create_full_table(server_data: list[ServerGPUData]) -> Table:
    """Create the full mode table with all details."""
    table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="blue",
        expand=True,
        padding=(0, 1),
    )

    table.add_column("Server", style="bold white", width=8)
    table.add_column("GPU", justify="center", width=4)
    table.add_column("Utilization", width=18)
    table.add_column("Memory", width=20)
    table.add_column("Temp", justify="center", width=7)
    table.add_column("Power", width=16)

    for data in sorted(server_data, key=lambda x: x.server):
        if not data.online:
            table.add_row(
                data.server,
                "-",
                Text("OFFLINE", style="red bold"),
                Text(data.error or "Connection failed", style="dim red"),
                "",
                "",
            )
            continue

        for i, gpu in enumerate(data.gpus):
            server_name = data.server if i == 0 else ""

            # Utilization bar
            util_bar = create_bar(gpu.utilization, width=8)
            util_text = Text()
            util_text.append_text(util_bar)
            util_text.append(f" {gpu.utilization:5.1f}%", style=get_color_for_percent(gpu.utilization))

            # Memory bar
            mem_bar = create_bar(gpu.memory_percent, width=8)
            mem_text = Text()
            mem_text.append_text(mem_bar)
            mem_text.append(
                f" {gpu.memory_used/1024:4.1f}/{gpu.memory_total/1024:4.1f}G",
                style=get_color_for_percent(gpu.memory_percent),
            )

            # Temperature
            temp_color = get_color_for_percent(gpu.temperature / 100 * 100)  # Assume 100C as max
            if gpu.temperature < 50:
                temp_color = "green"
            elif gpu.temperature < 75:
                temp_color = "yellow"
            else:
                temp_color = "red"
            temp_text = Text(f"{gpu.temperature:4.0f}°C", style=temp_color)

            # Power
            power_bar = create_bar(gpu.power_percent, width=6)
            power_text = Text()
            power_text.append_text(power_bar)
            power_text.append(f" {gpu.power_draw:3.0f}W", style=get_color_for_percent(gpu.power_percent))

            table.add_row(
                server_name,
                str(gpu.index),
                util_text,
                mem_text,
                temp_text,
                power_text,
            )

    return table


def create_process_panel(server_data: list[ServerGPUData]) -> Panel | None:
    """Create a panel showing running processes."""
    processes_found = False
    process_table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="green",
        expand=True,
        padding=(0, 1),
    )

    process_table.add_column("Server", style="bold white", width=8)
    process_table.add_column("GPU", justify="center", width=4)
    process_table.add_column("PID", justify="right", width=8)
    process_table.add_column("Process", width=30, overflow="ellipsis")
    process_table.add_column("Memory", justify="right", width=10)

    for data in sorted(server_data, key=lambda x: x.server):
        if not data.online:
            continue

        for gpu in data.gpus:
            for proc in gpu.processes:
                processes_found = True
                process_table.add_row(
                    data.server,
                    str(gpu.index),
                    str(proc.pid),
                    proc.name,
                    f"{proc.memory_used/1024:.1f}G",
                )

    if not processes_found:
        return None

    return Panel(
        process_table,
        title="[bold green]Running Processes[/bold green]",
        border_style="green",
        padding=(0, 1),
    )


def create_display(
    server_data: list[ServerGPUData],
    refresh_rate: float,
    full_mode: bool,
    last_update: datetime | None = None,
    compact_mode: bool = False,
) -> Group:
    """Create the complete display layout."""
    if compact_mode:
        header = create_compact_header(len(server_data), refresh_rate, last_update)
        columns = create_compact_multicolumn(server_data)
        return Group(header, "", columns)

    mode = "full" if full_mode else "essentials"
    header = create_header_panel(len(server_data), refresh_rate, mode, last_update)

    if full_mode:
        table = create_full_table(server_data)
        process_panel = create_process_panel(server_data)
        if process_panel:
            return Group(header, "", table, "", process_panel)
        return Group(header, "", table)
    else:
        table = create_essentials_table(server_data)
        return Group(header, "", table)


def create_loading_display(servers: list[str]) -> Panel:
    """Create a loading display while fetching data."""
    text = Text()
    text.append("  Connecting to servers: ", style="dim")
    text.append(", ".join(servers), style="cyan")
    text.append("...", style="dim")

    return Panel(
        text,
        title="[bold magenta]GPU Monitor[/bold magenta]",
        border_style="magenta",
        padding=(1, 2),
    )
