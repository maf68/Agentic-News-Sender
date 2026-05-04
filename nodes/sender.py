import httpx
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Any, Dict
from nodes.trace import header, divider, log

BEIRUT_TZ = ZoneInfo("Asia/Beirut")


def format_digest(strikes: list, lookback_hours: int) -> str:
    from collections import defaultdict
    from datetime import timedelta
    now = datetime.now(BEIRUT_TZ)
    since = now - timedelta(hours=lookback_hours)
    time_range = f"{since.strftime('%H:%M')} — {now.strftime('%H:%M')}"

    lines = [
        f"🎯 <b>تقرير الضربات</b>",
        f"📅 {now.strftime('%Y-%m-%d')}  🕐 {time_range}",
    ]

    by_attacker = defaultdict(list)
    for strike in strikes:
        by_attacker[strike["attacker"]].append(strike)

    for attacker, group in by_attacker.items():
        lines.append(f"\n━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"⚔️ <b>{attacker}</b>  ({len(group)} ضربة)")
        lines.append(f"━━━━━━━━━━━━━━━━━━━━━━")
        for i, strike in enumerate(group, 1):
            lines.append(f"\n<b>{i}.</b> {strike['summary']}\n")
            lines.append(f"   🎯 {strike['target']}")
            lines.append(f"   📍 {strike['place']}")
            lines.append(f"   📅 {strike['date']}  🕐 {strike['time']}")
            lines.append(f"   📢 {strike['channel']}\n")

    lines.append(f"\n━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"🔢 الإجمالي: {len(strikes)} ضربة")

    return "\n".join(lines)


async def sender_node(state: Dict[str, Any]) -> Dict[str, Any]:
    config = state["config"]
    strikes = state["strikes"]
    message = format_digest(strikes, config.LOOKBACK_HOURS)

    header(f"SENDER  ({len(strikes)} strikes)")
    log("Message preview:")
    divider()
    for line in message.splitlines():
        log(line)
    divider()

    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.YOUR_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        if response.status_code == 200:
            log("✅ Digest sent successfully.")
        else:
            log(f"⚠️  Failed: {response.text}")

    return state
