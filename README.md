# news-filterer

A LangGraph agent that monitors Telegram channels, uses a local LLM to detect news (such as strike reports), and sends structured digests straight to your Telegram.

---

## Agent Graph

```
          START
            │
            ▼
    ┌───────────────┐
    │   fetcher     │  pulls messages from configured channels
    └───────┬───────┘
            │
            ▼
    ┌───────────────┐
    │   filterer    │  local LLM detects & extracts strike events
    └───────┬───────┘
            │
       ┌────┴─────┐
       │          │
  strikes?      none
       │          │
       ▼          ▼
  ┌─────────┐   END
  │ sender  │  formats Arabic digest → Telegram
  └────┬────┘
       │
      END
```

---

## Setup

**1. Install**
```bash
pip install -r requirements.txt
```

**2. Configure** — fill in `config.py`:
- Telegram API credentials & bot token
- Channel list, lookback window, run interval
- LM Studio model name & endpoint

**3. Auth** *(once)*
```bash
python graph.py auth
```

**4. Get your chat ID** — send `/start` to your bot, then:
```bash
python graph.py chat-id
```

**5. Start LM Studio** with your model on port `1234`.

---

## Run

```bash
python graph.py
```

Runs on a configurable loop. Silent when nothing is found; sends a grouped Arabic digest when events are detected.

---

## Stack

`LangGraph` · `Telethon` · `LM Studio (local LLM)` · `Telegram Bot API`
