"""Tautulli API client with proper error handling."""

from dataclasses import dataclass
from typing import Any, Optional

import httpx

from .config import Config


class TautulliError(Exception):
    """Base exception for Tautulli API errors."""

    pass


class ConnectionError(TautulliError):
    """Could not connect to Tautulli server."""

    pass


class AuthenticationError(TautulliError):
    """Invalid API key."""

    pass


@dataclass
class Session:
    """Represents an active Plex session."""

    session_id: str
    user: str
    title: str
    media_type: str
    state: str
    view_offset_ms: int
    duration_ms: int
    player: str
    platform: str
    product_version: str
    transcode_decision: str
    video_decision: str
    audio_decision: str
    ip_address: str
    stream_location: str

    @property
    def view_offset_seconds(self) -> int:
        return self.view_offset_ms // 1000

    @property
    def duration_seconds(self) -> int:
        return self.duration_ms // 1000

    @property
    def progress_formatted(self) -> str:
        """Format current progress as HH:MM:SS / HH:MM:SS."""
        current = self._format_time(self.view_offset_seconds)
        total = self._format_time(self.duration_seconds)
        return f"{current} / {total}"

    @property
    def transcode_info(self) -> tuple[str, str]:
        """Return (description, style) for transcode status."""
        if self.transcode_decision == "transcode":
            if self.video_decision == "transcode" and self.audio_decision == "transcode":
                return "Transcode: Audio + Video", "red"
            elif self.video_decision == "transcode":
                return "Transcode: Video only", "yellow"
            elif self.audio_decision == "transcode":
                return "Transcode: Audio only", "yellow"
            else:
                return "Transcode", "yellow"
        elif self.transcode_decision:
            return self.transcode_decision.title(), "green"
        return "Unknown", "dim"

    @staticmethod
    def _format_time(seconds: int) -> str:
        """Format seconds as HH:MM:SS."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Session":
        """Create Session from API response data."""
        return cls(
            session_id=str(data.get("session_id", "")),
            user=data.get("user", "Unknown"),
            title=data.get("full_title", data.get("title", "Unknown")),
            media_type=data.get("media_type", "unknown"),
            state=data.get("state", "unknown"),
            view_offset_ms=int(data.get("view_offset", 0) or 0),
            duration_ms=int(data.get("duration", 0) or 0),
            player=data.get("player", "Unknown"),
            platform=data.get("platform", "Unknown"),
            product_version=data.get("product_version", ""),
            transcode_decision=data.get("transcode_decision", ""),
            video_decision=data.get("video_decision", ""),
            audio_decision=data.get("audio_decision", ""),
            ip_address=data.get("ip_address", ""),
            stream_location=data.get("stream_location", ""),
        )


@dataclass
class Library:
    """Represents a Plex library."""

    section_id: int
    section_name: str
    section_type: str
    count: int

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Library":
        """Create Library from API response data."""
        return cls(
            section_id=int(data.get("section_id", 0)),
            section_name=data.get("section_name", "Unknown"),
            section_type=data.get("section_type", "unknown"),
            count=int(data.get("count", 0)),
        )


class TautulliClient:
    """Client for interacting with Tautulli API."""

    def __init__(self, config: Config):
        if not config.is_configured():
            raise TautulliError("Tautulli is not configured. Run 'now-playing config' first.")

        self.base_url = config.url
        self.api_key = config.api_key
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        """Lazy-initialize HTTP client."""
        if self._client is None:
            self._client = httpx.Client(timeout=30.0)
        return self._client

    def _request(self, cmd: str) -> dict[str, Any]:
        """Make an API request to Tautulli."""
        try:
            response = self.client.get(
                f"{self.base_url}/api/v2",
                params={"apikey": self.api_key, "cmd": cmd},
            )
            response.raise_for_status()
            data = response.json()

            if data.get("response", {}).get("result") == "error":
                message = data.get("response", {}).get("message", "Unknown error")
                if "Invalid apikey" in message:
                    raise AuthenticationError("Invalid API key. Run 'now-playing config' to update.")
                raise TautulliError(message)

            return data.get("response", {}).get("data", {})

        except httpx.ConnectError as e:
            raise ConnectionError(
                f"Could not connect to Tautulli at {self.base_url}. "
                "Is the server running?"
            ) from e
        except httpx.HTTPStatusError as e:
            raise TautulliError(f"HTTP error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise TautulliError(f"Request failed: {e}") from e

    def get_activity(self) -> list[Session]:
        """Get current playback activity."""
        data = self._request("get_activity")
        sessions = data.get("sessions", [])
        return [Session.from_api(s) for s in sessions]

    def get_libraries(self) -> list[Library]:
        """Get Plex library statistics."""
        data = self._request("get_libraries")
        if isinstance(data, list):
            return [Library.from_api(lib) for lib in data]
        return []

    def test_connection(self) -> bool:
        """Test if we can connect to Tautulli."""
        try:
            self._request("get_activity")
            return True
        except TautulliError:
            return False

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None
