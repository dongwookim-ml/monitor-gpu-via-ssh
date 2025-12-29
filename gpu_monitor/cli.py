"""CLI entry point for GPU Monitor."""

import asyncio
import signal
import sys
from datetime import datetime

import click
from rich.console import Console
from rich.live import Live

from .display import create_display, create_loading_display
from .parser import parse_nvidia_smi_output, ServerGPUData
from .ssh import fetch_all_servers

DEFAULT_SERVERS = ["a", "b", "c", "d", "e", "f", "g", "h", "i"]

console = Console()


async def fetch_and_parse(
    servers: list[str], timeout: float, full_mode: bool
) -> list[ServerGPUData]:
    """Fetch GPU data from all servers and parse results."""
    results = await fetch_all_servers(servers, timeout=timeout, include_processes=full_mode)

    server_data = []
    for server, (gpu_result, process_result) in results.items():
        data = parse_nvidia_smi_output(
            server=server,
            output=gpu_result.output if gpu_result.success else "",
            error=gpu_result.error if not gpu_result.success else None,
        )
        server_data.append(data)

    return server_data


async def monitor_loop(
    servers: list[str],
    refresh: float,
    full_mode: bool,
    timeout: float,
    compact_mode: bool = False,
) -> None:
    """Main monitoring loop with live display."""
    stop_event = asyncio.Event()

    def signal_handler(sig, frame):
        stop_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    with Live(
        create_loading_display(servers),
        console=console,
        refresh_per_second=4,
        screen=True,
    ) as live:
        while not stop_event.is_set():
            try:
                # Fetch data
                server_data = await fetch_and_parse(servers, timeout, full_mode)
                last_update = datetime.now()

                # Update display
                display = create_display(server_data, refresh, full_mode, last_update, compact_mode)
                live.update(display)

                # Wait for refresh interval or stop signal
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=refresh)
                except asyncio.TimeoutError:
                    pass  # Normal timeout, continue loop

            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                await asyncio.sleep(refresh)

    console.print("\n[dim]GPU Monitor stopped.[/dim]")


@click.command()
@click.option(
    "-r",
    "--refresh",
    default=2.0,
    type=float,
    help="Refresh interval in seconds (default: 2.0)",
)
@click.option(
    "-f",
    "--full",
    is_flag=True,
    default=False,
    help="Show full details including temperature, power, and processes",
)
@click.option(
    "-e",
    "--essentials",
    is_flag=True,
    default=False,
    help="Show essentials only (utilization and memory) - this is the default",
)
@click.option(
    "-s",
    "--servers",
    default=None,
    type=str,
    help="Comma-separated list of servers (default: a,b,c,d,e,f,g,h,i)",
)
@click.option(
    "-t",
    "--timeout",
    default=10.0,
    type=float,
    help="SSH connection timeout in seconds (default: 10.0)",
)
@click.option(
    "-c",
    "--compact",
    is_flag=True,
    default=False,
    help="Compact mode for small screens (minimal columns, no GPU names)",
)
@click.version_option(package_name="gpu-monitor")
def main(
    refresh: float,
    full: bool,
    essentials: bool,
    servers: str | None,
    timeout: float,
    compact: bool,
) -> None:
    """
    Monitor GPU usage across SSH servers.

    Displays real-time GPU utilization, memory usage, temperature,
    and power consumption from multiple servers in a beautiful TUI.

    \b
    Examples:
        gpu-monitor                     # Default: essentials mode, 2s refresh
        gpu-monitor --full              # Full mode with all details
        gpu-monitor -r 5 --full         # Full mode with 5s refresh
        gpu-monitor -s a,b,c            # Monitor specific servers
    """
    # Parse servers
    if servers:
        server_list = [s.strip() for s in servers.split(",") if s.strip()]
    else:
        server_list = DEFAULT_SERVERS

    # Determine mode (full takes precedence, compact overrides both)
    full_mode = full and not essentials

    # Determine display mode string
    if compact:
        mode_str = "compact"
    elif full_mode:
        mode_str = "full"
    else:
        mode_str = "essentials"

    # Print startup message
    console.print(f"[bold magenta]GPU Monitor[/bold magenta] starting...")
    console.print(f"[dim]Servers: {', '.join(server_list)}[/dim]")
    console.print(f"[dim]Refresh: {refresh}s | Mode: {mode_str}[/dim]")
    console.print(f"[dim]Press Ctrl+C to exit[/dim]\n")

    # Run the monitor
    try:
        asyncio.run(monitor_loop(server_list, refresh, full_mode, timeout, compact))
    except KeyboardInterrupt:
        console.print("\n[dim]GPU Monitor stopped.[/dim]")
        sys.exit(0)


if __name__ == "__main__":
    main()
