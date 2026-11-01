"""
Twitch integration manager for ScienceQuest Live.
Supports live Twitch IRC over WebSocket and built-in simulation mode.
"""

import asyncio
import logging
import random
import re
from typing import Optional, Callable, Dict, Any, List

import websockets

from app.twitch.parser import TwitchCommandParser

logger = logging.getLogger("sciencequest.twitch")

MOCK_VIEWERS = [
    "QuantumAlice",
    "CosmicBob",
    "WavefunctionSam",
    "NeutrinoNed",
    "SchrodingersCat",
    "CuriousClara",
    "PhotonPhil",
    "DecoherenceDan",
    "PlanckPolly",
]


class TwitchService:
    """Manages Twitch IRC connection and simulated chat generator."""

    def __init__(
        self,
        channel: Optional[str] = None,
        bot_nick: Optional[str] = None,
        oauth_token: Optional[str] = None,
        simulation_mode: bool = True,
        on_command_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_chat_callback: Optional[Callable[[str, str, bool], None]] = None,
    ):
        self.channel = (channel or "").lower().lstrip("#")
        self.bot_nick = bot_nick or "ScienceQuestBot"
        self.oauth_token = oauth_token or ""
        self.simulation_mode = simulation_mode
        self.on_command = on_command_callback
        self.on_chat = on_chat_callback

        self.parser = TwitchCommandParser()
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self._sim_task: Optional[asyncio.Task] = None

    def is_live_configured(self) -> bool:
        return bool(self.channel and self.oauth_token and not self.simulation_mode)

    async def start(self):
        self.is_running = True
        if self.is_live_configured():
            logger.info(f"Connecting to Twitch IRC for channel #{self.channel}...")
            self._task = asyncio.create_task(self._twitch_irc_loop())
        else:
            logger.info("Running Twitch service in SIMULATION MODE.")
            self._sim_task = asyncio.create_task(self._simulation_loop())

    async def stop(self):
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        if self._sim_task and not self._sim_task.done():
            self._sim_task.cancel()

    async def _twitch_irc_loop(self):
        uri = "wss://irc-ws.chat.twitch.tv:443"
        while self.is_running:
            try:
                async with websockets.connect(uri) as ws:
                    token = self.oauth_token if self.oauth_token.startswith("oauth:") else f"oauth:{self.oauth_token}"
                    await ws.send(f"PASS {token}")
                    await ws.send(f"NICK {self.bot_nick}")
                    await ws.send(f"JOIN #{self.channel}")
                    logger.info(f"Connected and joined #{self.channel}")

                    async for message in ws:
                        if not self.is_running:
                            break
                        # Handle Keep-alive Ping
                        if message.startswith("PING"):
                            await ws.send("PONG :tmi.twitch.tv")
                            continue

                        # Parse PRIVMSG
                        # Format: :username!username@username.tmi.twitch.tv PRIVMSG #channel :message
                        match = re.match(r"^:([^!]+)![^@]+@[^\s]+\s+PRIVMSG\s+#[^\s]+\s+:(.*)$", message.strip())
                        if match:
                            user, text = match.groups()
                            is_mod = (user.lower() == self.channel.lower())
                            if self.on_chat:
                                self.on_chat(user, text, False)
                            action = self.parser.parse_message(user, text, is_mod_or_streamer=is_mod)
                            if action and self.on_command:
                                self.on_command(action)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Twitch IRC connection error: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)

    async def _simulation_loop(self):
        """Generates mock audience interaction in simulation mode."""
        while self.is_running:
            try:
                # Random interval between mock chats
                await asyncio.sleep(random.uniform(4.0, 9.0))
                if not self.is_running:
                    break

                viewer = random.choice(MOCK_VIEWERS)
                # Random actions: vote, ask question, or adjust parameter
                action_type = random.choices(["vote", "ask", "param", "chat"], weights=[0.45, 0.25, 0.15, 0.15])[0]

                if action_type == "vote":
                    opt = random.choices(["A", "B", "C", "D"], weights=[0.6, 0.2, 0.1, 0.1])[0]
                    text = f"!vote {opt}"
                elif action_type == "ask":
                    sample_questions = [
                        "Why does quantum tunneling only happen at microscopic scales?",
                        "What is the difference between classical waves and probability waves?",
                        "Does observing the particle change its trajectory?",
                        "Why can't the classical particle borrow energy from the future?",
                    ]
                    q = random.choice(sample_questions)
                    text = f"!ask {q}"
                elif action_type == "param":
                    p = random.choice(["!energy 4.0", "!barrier 5.5", "!width 0.35"])
                    text = p
                else:
                    greetings = [
                        "Ready for the next experiment!",
                        "Quark looks very confident today!",
                        "Let's see if classical or quantum wins this round!",
                        "Science is awesome!",
                    ]
                    text = random.choice(greetings)

                if self.on_chat:
                    self.on_chat(viewer, text, True)

                action = self.parser.parse_message(viewer, text, is_mod_or_streamer=False)
                if action and self.on_command:
                    self.on_command(action)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in simulation loop: {e}")
                await asyncio.sleep(2)
