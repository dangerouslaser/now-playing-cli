"""Configuration management with secure credential storage."""

import json
import os
import stat
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Prompt

console = Console()

CONFIG_DIR = Path.home() / ".config" / "now-playing"
CONFIG_FILE = CONFIG_DIR / "config.json"
KEYRING_SERVICE = "now-playing-cli"


class Config:
    """Manages Tautulli configuration with secure API key storage."""

    def __init__(self):
        self.url: Optional[str] = None
        self.api_key: Optional[str] = None
        self._load()

    def _load(self) -> None:
        """Load configuration from disk."""
        if not CONFIG_FILE.exists():
            return

        try:
            with open(CONFIG_FILE) as f:
                data = json.load(f)
                self.url = data.get("url")

            # Try keyring first for API key
            self.api_key = self._get_api_key_from_keyring()

            # Fall back to config file if keyring not available
            if not self.api_key:
                with open(CONFIG_FILE) as f:
                    data = json.load(f)
                    self.api_key = data.get("api_key")
        except (json.JSONDecodeError, OSError) as e:
            console.print(f"[yellow]Warning: Could not load config: {e}[/yellow]")

    def _get_api_key_from_keyring(self) -> Optional[str]:
        """Try to get API key from system keyring."""
        try:
            import keyring

            return keyring.get_password(KEYRING_SERVICE, "api_key")
        except ImportError:
            return None
        except Exception:
            return None

    def _store_api_key_in_keyring(self, api_key: str) -> bool:
        """Try to store API key in system keyring."""
        try:
            import keyring

            keyring.set_password(KEYRING_SERVICE, "api_key", api_key)
            return True
        except ImportError:
            return False
        except Exception:
            return False

    def save(self) -> None:
        """Save configuration to disk with secure permissions."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # Try to store API key in keyring
        use_keyring = False
        if self.api_key:
            use_keyring = self._store_api_key_in_keyring(self.api_key)

        # Save config file
        config_data = {"url": self.url}

        # Only store API key in file if keyring is not available
        if not use_keyring and self.api_key:
            config_data["api_key"] = self.api_key

        with open(CONFIG_FILE, "w") as f:
            json.dump(config_data, f, indent=2)

        # Set restrictive permissions (owner read/write only)
        os.chmod(CONFIG_FILE, stat.S_IRUSR | stat.S_IWUSR)

        if use_keyring:
            console.print(
                "[green]API key stored securely in system keyring.[/green]"
            )
        else:
            console.print(
                "[yellow]Note: Install 'keyring' package for more secure credential storage.[/yellow]"
            )
            console.print(
                f"[dim]Config saved to {CONFIG_FILE} with restricted permissions.[/dim]"
            )

    def is_configured(self) -> bool:
        """Check if configuration is complete."""
        return bool(self.url and self.api_key)

    def clear(self) -> None:
        """Remove all configuration."""
        # Clear keyring
        try:
            import keyring

            keyring.delete_password(KEYRING_SERVICE, "api_key")
        except Exception:
            pass

        # Remove config file
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()

        self.url = None
        self.api_key = None


def get_config() -> Config:
    """Get the current configuration."""
    return Config()


def setup_interactive() -> Config:
    """Run interactive configuration setup."""
    console.print("\n[bold cyan]Now Playing CLI Setup[/bold cyan]\n")

    config = Config()

    # Get Tautulli URL
    default_url = config.url or "http://localhost:8181"
    url = Prompt.ask(
        "[bold]Tautulli URL[/bold]",
        default=default_url,
    )

    # Normalize URL
    url = url.rstrip("/")
    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"

    # Warn about HTTP
    if url.startswith("http://") and "localhost" not in url and "127.0.0.1" not in url:
        console.print(
            "[yellow]Warning: Using HTTP over network exposes your API key. "
            "Consider using HTTPS.[/yellow]"
        )

    # Get API key
    console.print(
        "\n[dim]Find your API key in Tautulli: Settings > Web Interface > API Key[/dim]"
    )
    api_key = Prompt.ask("[bold]Tautulli API Key[/bold]", password=True)

    if not api_key:
        console.print("[red]API key is required.[/red]")
        raise SystemExit(1)

    config.url = url
    config.api_key = api_key
    config.save()

    console.print("\n[green]Configuration saved successfully![/green]")
    return config
