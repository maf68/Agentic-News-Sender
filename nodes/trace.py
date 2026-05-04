import sys

sys.stdout.reconfigure(encoding="utf-8")

W = 52

def header(title: str):
    print(f"\n╔{'═' * W}╗")
    print(f"║  {title:<{W-2}}║")
    print(f"╚{'═' * W}╝")

def divider():
    print(f"  {'─' * (W - 2)}")

def log(msg: str):
    print(f"  {msg}")

def snippet(text: str, max_len: int = 80) -> str:
    text = text.replace("\n", " ").strip()
    return text[:max_len] + "…" if len(text) > max_len else text
