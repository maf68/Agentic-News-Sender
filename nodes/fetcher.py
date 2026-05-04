from telethon import TelegramClient
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Any, Dict
from nodes.trace import header, divider, log

BEIRUT_TZ = ZoneInfo("Asia/Beirut")


async def fetcher_node(state: Dict[str, Any]) -> Dict[str, Any]:
    config = state["config"]
    cutoff = datetime.now(timezone.utc) - timedelta(hours=config.LOOKBACK_HOURS)
    all_messages = []

    header(f"FETCHER  (last {config.LOOKBACK_HOURS}h)")
    log(f"Cutoff: {cutoff.astimezone(BEIRUT_TZ).strftime('%Y-%m-%d %H:%M')} Beirut")

    async with TelegramClient("session.session", config.TELEGRAM_API_ID, config.TELEGRAM_API_HASH) as client:
        for channel in config.CHANNELS:
            try:
                before = len(all_messages)
                async for message in client.iter_messages(channel, offset_date=None, reverse=False, limit=200):
                    if message.date < cutoff:
                        break
                    if message.text:
                        all_messages.append({
                            "channel": channel,
                            "date": message.date.isoformat(),
                            "text": message.text,
                            "message_id": message.id,
                        })
                count = len(all_messages) - before
                log(f"📡 {channel:30s} → {count} messages")
            except Exception as e:
                log(f"⚠️  {channel}: {e}")

    divider()
    log(f"Total fetched: {len(all_messages)} messages")
    return {**state, "messages": all_messages}
