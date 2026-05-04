import asyncio
import sys
import httpx
from telethon import TelegramClient
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any
from nodes.fetcher import fetcher_node
from nodes.filterer import filter_node
from nodes.reflector import reflector_node
from nodes.sender import sender_node
from config import Config


# ── Graph ────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: List[Dict[str, Any]]
    strikes: List[Dict[str, Any]]
    config: Config


def build_graph(config: Config) -> StateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("fetcher", fetcher_node)
    graph.add_node("filter", filter_node)
    # graph.add_node("reflector", reflector_node)
    graph.add_node("sender", sender_node)
    graph.set_entry_point("fetcher")
    graph.add_edge("fetcher", "filter")
    graph.add_conditional_edges(
        "filter",
        lambda state: "sender" if state["strikes"] else END,
    )
    # graph.add_conditional_edges(
    #     "reflector",
    #     lambda state: "sender" if state["strikes"] else END,
    # )
    graph.add_edge("sender", END)
    return graph.compile()


# ── Runner ───────────────────────────────────────────────────────────

async def run():
    config = Config()
    graph = build_graph(config)

    while True:
        print(f"\n{'='*50}")
        print(f"Running Strike Tracker...")
        print(f"{'='*50}")
        try:
            await graph.ainvoke({
                "messages": [],
                "strikes": [],
                "config": config,
            })
        except Exception as e:
            print(f"Error during run: {e}")

        print(f"\nNext run in {config.RUN_EVERY_HOURS} hours...")
        await asyncio.sleep(config.RUN_EVERY_HOURS * 3600)


# ── Setup ────────────────────────────────────────────────────────────

async def authenticate():
    """Run once to create session.session for Telegram auth."""
    config = Config()
    async with TelegramClient("session", config.TELEGRAM_API_ID, config.TELEGRAM_API_HASH) as client:
        me = await client.get_me()
        print(f"Authenticated as: {me.first_name} (@{me.username})")
        print("session.session file created.")


def get_chat_id():
    """Run once after sending /start to your bot to find your chat ID."""
    config = Config()
    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/getUpdates"
    data = httpx.get(url).json()
    if data["result"]:
        for update in data["result"]:
            chat = update.get("message", {}).get("chat", {})
            print(f"chat_id: {chat.get('id')}  (username: {chat.get('username')})")
    else:
        print("No updates found. Make sure you sent /start to your bot first.")


# ── Entry Point ──────────────────────────────────────────────────────

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "auth":
        asyncio.run(authenticate())
    elif cmd == "chat-id":
        get_chat_id()
    else:
        asyncio.run(run())
