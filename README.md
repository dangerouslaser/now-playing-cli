# Now Playing CLI

A modern CLI tool to monitor Plex activity via the Tautulli API.

![now-playing](now-playing-latest.png)

## Features

- **Real-time monitoring** - Watch active streams with live progress updates
- **Library statistics** - View item counts across all Plex libraries
- **Secure configuration** - API keys stored in system keychain (or config file with restricted permissions)
- **Beautiful output** - Rich terminal formatting with colors and tables
- **Safe reboot** - Check for active streams before rebooting your server

## Installation

### Using pipx (recommended)

```bash
pipx install now-playing-cli
```

### Using pip

```bash
pip install now-playing-cli
```

### From source

```bash
git clone https://github.com/dangerouslaser/now-playing-cli.git
cd now-playing-cli
pip install .
```

### Optional: Secure credential storage

For storing your API key in the system keychain instead of a config file:

```bash
pip install now-playing-cli[keyring]
```

## Configuration

Run the interactive setup to configure your Tautulli connection:

```bash
now-playing config
```

You'll be prompted for:
- **Tautulli URL** - e.g., `http://localhost:8181` or `https://tautulli.example.com`
- **API Key** - Found in Tautulli: Settings > Web Interface > API Key

The configuration is stored in `~/.config/now-playing/config.json` with restricted permissions (readable only by you). If the `keyring` package is installed, your API key is stored in the system keychain instead.

### Configuration commands

```bash
# View current configuration
now-playing config --show

# Remove all configuration
now-playing config --clear
```

## Usage

### Show current activity

```bash
now-playing
```

Displays all active Plex streams with user, title, progress, player info, and transcode status.

### Monitor in real-time

```bash
now-playing watch
```

![watch mode](now-playing-watch.png)

Live-updating display that shows stream progress in real-time. Press `Ctrl+C` to exit.

Options:
- `--interval, -i` - Refresh interval in seconds (default: 10)

### Library statistics

```bash
now-playing library
```

![library stats](now-playing-library.png)

Shows a table of all Plex libraries with item counts.

### Reboot with safety check

```bash
now-playing reboot
```

![reboot check](now-playing-reboot.png)

Checks for active streams and warns before rebooting. Useful for server maintenance.

## Requirements

- Python 3.9+
- A running [Tautulli](https://tautulli.com/) instance connected to your Plex server

## Upgrading from v1 (bash script)

The Python version is a complete rewrite with several improvements:

| Feature | v1 (bash) | v2 (Python) |
|---------|-----------|-------------|
| Configuration | Edit script directly | Interactive setup with `now-playing config` |
| Credential storage | Plaintext in script | System keychain or config file with restricted permissions |
| Error handling | Limited | Comprehensive with helpful messages |
| Dependencies | curl, jq | Self-contained Python package |
| Installation | Manual copy to /usr/local/bin | pip/pipx install |

To upgrade:
1. Remove the old script: `sudo rm /usr/local/bin/now-playing`
2. Install the new version: `pipx install now-playing-cli`
3. Run setup: `now-playing config`

## License

MIT
