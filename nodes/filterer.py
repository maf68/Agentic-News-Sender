from openai import OpenAI
from typing import Any, Dict
from datetime import datetime
from zoneinfo import ZoneInfo
from nodes.trace import header, divider, log, snippet
import json
import re

BEIRUT_TZ = ZoneInfo("Asia/Beirut")

SYSTEM_PROMPT = """
أنت محلل أخبار عسكري. مهمتك تحديد ما إذا كانت الرسالة تُفيد بوقوع ضربة أو هجوم عسكري في لبنان أو إسرائيل.

✅ قبول: ضربة أو هجوم عسكري حيث الهدف المُستهدَف يقع في لبنان أو إسرائيل.

❌ رفض في جميع الحالات التالية:
- الحدث يقع خارج لبنان وإسرائيل (سوريا، اليمن، غزة، العراق، إيران، إلخ)
- تصريح أو تحليل أو تعليق فقط دون حدث هجومي فعلي
- خبر سياسي أو دبلوماسي أو إنساني
- رسالة لا تذكر هجوماً أو ضربة بشكل صريح

إذا قبلت، استخرج:
- attacker: الجهة التي نفّذت الضربة (مثلاً: حزب الله، إسرائيل، المقاومة الإسلامية...)
- target: الهدف المُستهدَف (موقع، مركبة، منشأة، شخص)
- date: تاريخ الضربة إن ذُكر، وإلا تاريخ الرسالة
- time: وقت الضربة إن ذُكر، وإلا "غير محدد"
- place: الموقع الجغرافي للهدف
- summary: جملة واحدة بالعربية تبدأ باسم المُنفِّذ

أجب فقط بـ JSON:
{{"is_strike": true, "attacker": "...", "target": "...", "date": "...", "time": "...", "place": "...", "summary": "..."}}
أو:
{{"is_strike": false}}

لا تضف أي نص آخر.
""".strip()


ATTACKER_ALIASES = {
    "حزب الله": ["حزب الله", "المقاومة الإسلامية", "المقاومة الاسلامية", "حزب‌الله", "مقاومة اللبنانية", "المقاومة اللبنانية"],
    "إسرائيل": ["إسرائيل", "اسرائيل", "الجيش الإسرائيلي", "الجيش الاسرائيلي", "جيش الاحتلال", "قوات الاحتلال", "الاحتلال الإسرائيلي", "الاحتلال الاسرائيلي", "الاحتلال", "الكيان الصهيوني", "الكيان الصهيوني", "العدو الاسرائيلي", "جيش العدو"],
}

def normalize_attacker(name: str) -> str:
    for canonical, aliases in ATTACKER_ALIASES.items():
        if any(alias in name for alias in aliases):
            return canonical
    return name


def extract_json(text: str) -> dict:
    try:
        return json.loads(text.strip())
    except Exception:
        match = re.search(r'\{.*?\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return {"is_strike": False}


async def filter_node(state: Dict[str, Any]) -> Dict[str, Any]:
    config = state["config"]
    messages = state["messages"]
    strikes = []

    client = OpenAI(base_url=config.LM_STUDIO_BASE_URL, api_key="lm-studio")
    system = SYSTEM_PROMPT

    header(f"FILTER  ({len(messages)} messages)")

    for i, msg in enumerate(messages, 1):
        time_str = datetime.fromisoformat(msg["date"]).astimezone(BEIRUT_TZ).strftime("%H:%M")
        log(f"[{i:>3}/{len(messages)}] {msg['channel']}  {time_str}")
        log(f"        {snippet(msg['text'])}")

        user_content = f"قناة: {msg['channel']}\nالتاريخ: {msg['date']}\nالرسالة:\n{msg['text']}"

        try:
            response = client.chat.completions.create(
                model=config.LM_STUDIO_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.1,
                max_tokens=300,
            )
            raw = response.choices[0].message.content
            result = extract_json(raw)

            if result.get("is_strike"):
                extracted_time = result.get("time", "غير محدد")
                if not extracted_time or extracted_time == "غير محدد":
                    extracted_time = datetime.fromisoformat(msg["date"]).astimezone(BEIRUT_TZ).strftime("%H:%M")
                strikes.append({
                    "channel": msg["channel"],
                    "message_date": msg["date"],
                    "attacker": normalize_attacker(result.get("attacker", "غير محدد")),
                    "target": result.get("target", "غير محدد"),
                    "date": result.get("date", msg["date"][:10]),
                    "time": extracted_time,
                    "place": result.get("place", "غير محدد"),
                    "summary": result.get("summary", ""),
                    "original_text": msg["text"],
                })
                log(f"        ✅ STRIKE | {result.get('attacker')} ← {result.get('place')} | {extracted_time}")
                log(f"           {result.get('summary', '')}")
            else:
                log(f"        ✗ not a strike")

        except Exception as e:
            log(f"        ⚠️  LLM error: {e}")
            continue

    before = len(strikes)
    strikes = [s for s in strikes if s["attacker"] in ("حزب الله", "إسرائيل")]
    if len(strikes) != before:
        log(f"Filtered to Hezbollah/Israel only: {before} → {len(strikes)}")

    if config.TARGET_GROUP:
        before = len(strikes)
        strikes = [s for s in strikes if config.TARGET_GROUP in s["attacker"]]
        log(f"Filtered by TARGET_GROUP '{config.TARGET_GROUP}': {before} → {len(strikes)}")

    divider()
    log(f"Strikes found: {len(strikes)}")
    return {**state, "strikes": strikes}
