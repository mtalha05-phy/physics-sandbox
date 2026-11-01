"""
Entry point to run ScienceQuest Live application server.
Run with: python run.py
"""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print("=" * 70)
    print("  SCIENCEQUEST LIVE — Two Worlds. Different Rules. One Curious Universe.")
    print("=" * 70)
    print(f"  Starting server at: http://{settings.app_host}:{settings.app_port}")
    print(f"  Stream Overlay at:  http://{settings.app_host}:{settings.app_port}/overlay")
    print(f"  Simulation Mode:    {settings.simulation_mode}")
    print(f"  Admin token:        {'Set' if settings.admin_token else 'NOT SET (control endpoints: localhost only; set ADMIN_TOKEN before exposing this server)'}")
    print(f"  Twitch Channel:     {settings.twitch_channel or 'None (Simulation Mode Active)'}")
    print(f"  Quark AI Model:     {settings.openai_model} (API Key: {'Set' if settings.openai_api_key else 'Not set - using local scientific knowledge'})")
    print("=" * 70)

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=False,
        log_level="info",
    )
