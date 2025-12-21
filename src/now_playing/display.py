"""Rich display helpers for terminal output."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .api import Library, Session

console = Console()


def display_sessions(sessions: list[Session], show_type: bool = True) -> None:
    """Display active sessions in a formatted way."""
    if not sessions:
        console.print("[green]No active sessions.[/green]")
        return

    console.print(
        Panel(
            f"[bold green]{len(sessions)} active session(s)[/bold green]",
            border_style="yellow",
        )
    )

    for session in sessions:
        display_session(session, show_type=show_type)


def display_session(session: Session, show_type: bool = True) -> None:
    """Display a single session."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Label", style="bold", width=10)
    table.add_column("Value")

    table.add_row("[red]User[/red]", session.user)

    if show_type:
        table.add_row("[cyan]Type[/cyan]", session.media_type)

    table.add_row("[white]Title[/white]", session.title)

    # State with color coding
    state_color = "green" if session.state == "playing" else "yellow"
    table.add_row("[red]State[/red]", f"[{state_color}]{session.state}[/{state_color}]")

    # Progress
    if session.duration_ms:
        table.add_row("[magenta]Progress[/magenta]", session.progress_formatted)

    # Player info
    player_info = f"{session.player} - {session.platform}"
    if session.product_version:
        player_info += f" {session.product_version}"
    table.add_row("[green]Player[/green]", player_info)

    # Transcode status
    transcode_desc, transcode_style = session.transcode_info
    table.add_row("[cyan]Stream[/cyan]", f"[{transcode_style}]{transcode_desc}[/{transcode_style}]")

    console.print(table)
    console.print("[yellow]" + "-" * 45 + "[/yellow]")


def display_libraries(libraries: list[Library]) -> None:
    """Display library statistics in a table."""
    if not libraries:
        console.print("[yellow]No libraries found.[/yellow]")
        return

    table = Table(title="Plex Library Statistics", border_style="cyan")
    table.add_column("Library", style="bold green")
    table.add_column("Type", style="cyan")
    table.add_column("Items", justify="right", style="yellow")

    total_items = 0
    for lib in libraries:
        table.add_row(lib.section_name, lib.section_type, str(lib.count))
        total_items += lib.count

    table.add_section()
    table.add_row("[bold]Total[/bold]", "", f"[bold]{total_items}[/bold]")

    console.print(table)


def display_watch_header(session_count: int) -> None:
    """Display header for watch mode."""
    console.print(
        Panel(
            f"[bold green]{session_count} active session(s)[/bold green]",
            border_style="yellow",
            subtitle="[dim]Press Ctrl+C to exit[/dim]",
        )
    )


def display_error(message: str) -> None:
    """Display an error message."""
    console.print(f"[bold red]Error:[/bold red] {message}")


def display_warning(message: str) -> None:
    """Display a warning message."""
    console.print(f"[bold yellow]Warning:[/bold yellow] {message}")


def display_success(message: str) -> None:
    """Display a success message."""
    console.print(f"[bold green]{message}[/bold green]")
