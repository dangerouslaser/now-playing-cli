"""Main CLI application using Typer."""

import subprocess
import sys
import time
from typing import Optional

import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from . import __version__
from .api import Session, TautulliClient, TautulliError
from .config import get_config, setup_interactive
from .display import (
    console,
    display_error,
    display_libraries,
    display_sessions,
    display_success,
    display_warning,
)

app = typer.Typer(
    name="now-playing",
    help="Monitor Plex activity via Tautulli API.",
    no_args_is_help=False,
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"now-playing version {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """Show current Plex activity (default command)."""
    # Only run default behavior if no subcommand was invoked
    if ctx.invoked_subcommand is None:
        show_activity()


def show_activity() -> None:
    """Display current playback activity."""
    config = get_config()

    if not config.is_configured():
        display_error("Not configured. Run 'now-playing config' to set up.")
        raise typer.Exit(1)

    try:
        client = TautulliClient(config)
        sessions = client.get_activity()
        display_sessions(sessions)
    except TautulliError as e:
        display_error(str(e))
        raise typer.Exit(1)


@app.command()
def config(
    clear: bool = typer.Option(False, "--clear", help="Remove all configuration."),
    show: bool = typer.Option(False, "--show", help="Show current configuration."),
) -> None:
    """Configure Tautulli connection settings."""
    cfg = get_config()

    if clear:
        if Confirm.ask("Remove all configuration?", default=False):
            cfg.clear()
            display_success("Configuration cleared.")
        return

    if show:
        if cfg.is_configured():
            console.print(f"[bold]URL:[/bold] {cfg.url}")
            console.print("[bold]API Key:[/bold] [dim]••••••••[/dim] (hidden)")
        else:
            console.print("[yellow]Not configured.[/yellow]")
        return

    # Interactive setup
    cfg = setup_interactive()

    # Test connection
    console.print("\n[dim]Testing connection...[/dim]")
    try:
        client = TautulliClient(cfg)
        if client.test_connection():
            display_success("Connection successful!")
        else:
            display_warning("Could not verify connection.")
    except TautulliError as e:
        display_error(f"Connection test failed: {e}")


@app.command()
def library() -> None:
    """Show Plex library statistics."""
    config = get_config()

    if not config.is_configured():
        display_error("Not configured. Run 'now-playing config' to set up.")
        raise typer.Exit(1)

    console.print("[cyan]Fetching Plex library stats...[/cyan]\n")

    try:
        client = TautulliClient(config)
        libraries = client.get_libraries()
        display_libraries(libraries)
    except TautulliError as e:
        display_error(str(e))
        raise typer.Exit(1)


@app.command()
def watch(
    interval: int = typer.Option(10, "--interval", "-i", help="Refresh interval in seconds."),
) -> None:
    """Monitor sessions in real-time."""
    config = get_config()

    if not config.is_configured():
        display_error("Not configured. Run 'now-playing config' to set up.")
        raise typer.Exit(1)

    try:
        client = TautulliClient(config)
    except TautulliError as e:
        display_error(str(e))
        raise typer.Exit(1)

    # Track sessions for progress interpolation
    sessions_cache: dict[str, Session] = {}
    last_sync = 0.0

    def generate_display() -> Table:
        """Generate the display table."""
        nonlocal sessions_cache, last_sync

        current_time = time.time()

        # Refresh from API if interval has passed
        if current_time - last_sync >= interval:
            try:
                sessions = client.get_activity()
                sessions_cache = {s.session_id: s for s in sessions}
                last_sync = current_time
            except TautulliError:
                pass  # Keep showing cached data on error

        # Build display
        table = Table(show_header=False, box=None, expand=True)

        # Header
        table.add_row(
            Panel(
                f"[bold green]{len(sessions_cache)} active session(s)[/bold green]",
                border_style="yellow",
                subtitle="[dim]Press Ctrl+C to exit[/dim]",
            )
        )

        for session in sessions_cache.values():
            # Interpolate progress for playing sessions
            offset = session.view_offset_seconds
            if session.state == "playing":
                elapsed = int(current_time - last_sync)
                offset = min(offset + elapsed, session.duration_seconds)

            progress = Session._format_time(offset)
            total = Session._format_time(session.duration_seconds)

            session_table = Table(show_header=False, box=None, padding=(0, 1))
            session_table.add_column("Label", style="bold", width=10)
            session_table.add_column("Value")

            session_table.add_row("[red]User[/red]", session.user)
            session_table.add_row("[white]Title[/white]", session.title)

            state_color = "green" if session.state == "playing" else "yellow"
            session_table.add_row(
                "[red]State[/red]",
                f"[{state_color}]{session.state}[/{state_color}]",
            )

            session_table.add_row("[magenta]Progress[/magenta]", f"{progress} / {total}")

            player_info = f"{session.player} - {session.platform}"
            if session.product_version:
                player_info += f" {session.product_version}"
            session_table.add_row("[green]Player[/green]", player_info)

            transcode_desc, transcode_style = session.transcode_info
            session_table.add_row(
                "[cyan]Stream[/cyan]",
                f"[{transcode_style}]{transcode_desc}[/{transcode_style}]",
            )

            table.add_row(session_table)
            table.add_row("[yellow]" + "-" * 45 + "[/yellow]")

        return table

    try:
        with Live(generate_display(), refresh_per_second=1, console=console) as live:
            while True:
                time.sleep(1)
                live.update(generate_display())
    except KeyboardInterrupt:
        console.print("\n[dim]Watch mode stopped.[/dim]")


@app.command()
def reboot() -> None:
    """Check for active sessions and optionally reboot the system."""
    config = get_config()

    if not config.is_configured():
        display_error("Not configured. Run 'now-playing config' to set up.")
        raise typer.Exit(1)

    try:
        client = TautulliClient(config)
        sessions = client.get_activity()
    except TautulliError as e:
        display_error(str(e))
        raise typer.Exit(1)

    # Show current activity
    display_sessions(sessions)
    console.print()

    # Warn about active sessions
    if sessions:
        display_warning(f"Rebooting now will kill {len(sessions)} active Plex stream(s)!")
    else:
        console.print("[yellow]No active sessions. Safe to reboot.[/yellow]")

    # Confirm reboot
    if Confirm.ask("\nWould you like to reboot the system now?", default=False):
        console.print("[red]Rebooting...[/red]")
        try:
            subprocess.run(["sudo", "reboot"], check=True)
        except subprocess.CalledProcessError:
            display_error("Failed to initiate reboot. Do you have sudo access?")
            raise typer.Exit(1)
        except FileNotFoundError:
            display_error("'reboot' command not found.")
            raise typer.Exit(1)
    else:
        console.print("[cyan]Reboot cancelled.[/cyan]")


if __name__ == "__main__":
    app()
