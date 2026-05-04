from openai import OpenAI
from typing import Any, Dict
from datetime import datetime, timezone
from nodes.trace import header, divider, log, snippet
import json
import re


REFLECTION_PROMPT = """
أنت مدقق أخبار صارم. مهمتك التحقق مما إذا كانت الرسالة تُثبت فعلاً ضربة أو هجوماً عسكرياً في لبنان أو إسرائيل.

أكّد فقط إذا:
- الرسالة تذكر ضربة أو هجوماً عسكرياً فعلياً
- الموقع المستهدف في لبنان أو إسرائيل
- المنفِّذ محدد أو يمكن استنتاجه بوضوح

لا تؤكد إذا:
- الحدث خارج لبنان وإسرائيل
- المعلومات غير مؤكدة أو تحليل فقط

أجب فقط بـ JSON:
{{"confirmed": true}}
أو
{{"confirmed": false, "reason": "..."}}

لا تضف أي نص آخر.
""".strip()


def _extract_json(text: str) -> dict:
    try:
        return json.loads(text.strip())
    except Exception:
        match = re.search(r'\{.*?\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return {"confirmed": False, "reason": "failed to parse LLM response"}


async def reflector_node(state: Dict[str, Any]) -> Dict[str, Any]:
    config = state["config"]
    strikes = state["strikes"]

    client = OpenAI(base_url=config.LM_STUDIO_BASE_URL, api_key="lm-studio")
    system = REFLECTION_PROMPT

    header(f"REFLECTOR  ({len(strikes)} candidates)")

    confirmed = []
    for i, strike in enumerate(strikes, 1):
        log(f"[{i}/{len(strikes)}] {strike['place']}  |  {strike['channel']}")
        log(f"        {snippet(strike['original_text'])}")

        user_content = f"قناة: {strike['channel']}\nالتاريخ: {strike['message_date']}\nالرسالة:\n{strike['original_text']}"

        try:
            response = client.chat.completions.create(
                model=config.LM_STUDIO_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.0,
                max_tokens=150,
            )
            raw = response.choices[0].message.content
            result = _extract_json(raw)

            if result.get("confirmed"):
                confirmed.append(strike)
                log(f"        ✅ CONFIRMED")
            else:
                log(f"        ❌ REJECTED: {result.get('reason', '')}")

        except Exception as e:
            log(f"        ⚠️  error: {e}")
            confirmed.append(strike)

    divider()
    log(f"Confirmed: {len(confirmed)}/{len(strikes)}")

    DEDUP_WINDOW_MINUTES = 30
    unique = []
    for strike in confirmed:
        t = datetime.fromisoformat(strike["message_date"]).astimezone(timezone.utc)
        is_dup = any(
            abs((t - datetime.fromisoformat(s["message_date"]).astimezone(timezone.utc)).total_seconds()) < DEDUP_WINDOW_MINUTES * 60
            for s in unique
        )
        if not is_dup:
            unique.append(strike)
        else:
            log(f"🔁 Duplicate removed: {strike['place']}  via {strike['channel']}")

    if len(unique) < len(confirmed):
        log(f"Deduplicated to {len(unique)} unique strike(s).")

    return {**state, "strikes": unique}
