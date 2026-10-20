"""Send one Telegram message to the owner. Usage: python3 tools/notify.py "text"

Reads TELEGRAM_BOT_TOKEN and TELEGRAM_OWNER_CHAT_ID from the environment (GitHub secrets).
If they are not configured yet, prints the message and exits 0 so the workflow log still shows it.
Never prints the token.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request


def main() -> int:
    text = " ".join(sys.argv[1:]) or "(empty)"
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat = os.environ.get("TELEGRAM_OWNER_CHAT_ID", "")
    if not token or not chat:
        print(f"[notify] Telegram not configured; message was: {text}")
        return 0
    body = json.dumps({"chat_id": chat, "text": text, "disable_web_page_preview": True}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print(f"[notify] sent ({r.status})")
    except Exception as e:  # noqa: BLE001 - alerting must never fail the job loudly with the URL
        print(f"[notify] failed: {type(e).__name__}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
