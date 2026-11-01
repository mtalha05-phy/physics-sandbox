"""
Configuration, read from environment variables.

``python-dotenv`` is optional: the Vercel edition injects variables itself and does not need it,
while ``run.py`` (self-hosted live mode) loads a local ``.env`` if the package is installed.
"""

import os
from dataclasses import dataclass

try:  # optional dependency
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # pragma: no cover
    pass


def _flag(name: str, default: str) -> bool:
    return os.getenv(name, default).strip().lower() in ("true", "1", "yes")


@dataclass
class Settings:
    app_host: str = os.getenv("APP_HOST", "127.0.0.1")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    debug: bool = _flag("DEBUG", "false")

    # Live mode only: protects control endpoints. If empty, control endpoints accept loopback clients only.
    admin_token: str = os.getenv("ADMIN_TOKEN", "")
    # Live mode only: extra WebSocket origins allowed besides the server's own host (comma separated).
    allowed_origins: str = os.getenv("ALLOWED_ORIGINS", "")

    # Twitch (live mode only)
    simulation_mode: bool = _flag("SIMULATION_MODE", "true")
    twitch_channel: str = os.getenv("TWITCH_CHANNEL", "")
    twitch_bot_nickname: str = os.getenv("TWITCH_BOT_NICKNAME", "ScienceQuestBot")
    twitch_oauth_token: str = os.getenv("TWITCH_OAUTH_TOKEN", "")
    twitch_client_id: str = os.getenv("TWITCH_CLIENT_ID", "")
    twitch_client_secret: str = os.getenv("TWITCH_CLIENT_SECRET", "")
    twitch_redirect_uri: str = os.getenv("TWITCH_REDIRECT_URI", "http://localhost:8000/auth/twitch/callback")

    # Optional OpenAI-backed Quark. Leave empty to use the curated, offline explanations.
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


settings = Settings()
