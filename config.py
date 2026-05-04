from dataclasses import dataclass, field
from typing import List

@dataclass
class Config:
    # ── Telegram Reader (your account) ──────────────────────────────
    TELEGRAM_API_ID: int = 34258591
    TELEGRAM_API_HASH: str = "bafdad68855aca4bb4daeb45fbf8b5cd"

    # ── Telegram Bot (sends you the digest) ─────────────────────────
    BOT_TOKEN: str = "8728024362:AAHWSR6yL5iB6512ZPRqbx7mYmhTwxqc96g"
    YOUR_CHAT_ID: int = 7665622977  # ← Fill this in (instructions in README)

    # ── Channels to monitor ─────────────────────────────────────────
    CHANNELS: List[str] = field(default_factory=lambda: [
        "@AjaNews",   # ← Replace with real channel usernames
        "@mayadeenchannel",
        "@alakhbar_news",
        "@Middle_East_Spectator"
    ])

    # ── Optional: filter strikes by a specific group (leave empty to get all) ──
    TARGET_GROUP: str = ""

    # ── LM Studio ───────────────────────────────────────────────────
    LM_STUDIO_BASE_URL: str = "http://localhost:1234/v1"
    LM_STUDIO_MODEL: str = "mistralai/devstral-small-2-2512"  # ← As shown in LM Studio

    # ── How many hours back to look on each run ──────────────────────
    LOOKBACK_HOURS: int = 5

    # ── How often to run (in hours) ─────────────────────────────────
    RUN_EVERY_HOURS: int = 1
