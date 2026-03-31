#!/usr/bin/env python3
"""
UptimeRobot → Telegram alerting bridge.

Polls UptimeRobot API every 60s, sends Telegram messages on status changes.
Runs as a lightweight Docker container or standalone script.

Environment variables:
  UPTIMEROBOT_API_KEY  — UptimeRobot API key (read-only is enough)
  TELEGRAM_BOT_TOKEN   — Telegram bot token from @BotFather
  TELEGRAM_CHAT_ID     — Chat/group ID to send alerts to
  POLL_INTERVAL        — Seconds between checks (default: 60)
"""

import os
import sys
import time
import json
import logging
import urllib.request
import urllib.parse
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("uptimerobot-telegram")

# Config from environment
API_KEY = os.environ.get("UPTIMEROBOT_API_KEY", "")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "60"))

# State file to persist status between restarts
STATE_FILE = Path("/tmp/uptimerobot_state.json")

# UptimeRobot status codes
STATUS_MAP = {
    0: ("paused", "⏸"),
    1: ("not checked yet", "⏳"),
    2: ("up", "✅"),
    8: ("seems down", "⚠️"),
    9: ("down", "🔴"),
}


def uptimerobot_get_monitors() -> list[dict]:
    """Fetch all monitors from UptimeRobot API."""
    data = urllib.parse.urlencode({
        "api_key": API_KEY,
        "format": "json",
    }).encode()

    req = urllib.request.Request(
        "https://api.uptimerobot.com/v2/getMonitors",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())

    if result.get("stat") != "ok":
        logger.error("UptimeRobot API error: %s", result)
        return []

    return result.get("monitors", [])


def telegram_send(text: str) -> bool:
    """Send a message via Telegram Bot API."""
    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            return result.get("ok", False)
    except Exception as e:
        logger.error("Telegram send failed: %s", e)
        return False


def load_state() -> dict[str, int]:
    """Load previous monitor statuses from state file."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {}


def save_state(state: dict[str, int]):
    """Save current monitor statuses to state file."""
    STATE_FILE.write_text(json.dumps(state))


def check_and_alert():
    """Main check loop iteration."""
    monitors = uptimerobot_get_monitors()
    if not monitors:
        return

    prev_state = load_state()
    new_state = {}

    for m in monitors:
        mid = str(m["id"])
        name = m["friendly_name"]
        status = m["status"]
        url = m.get("url", "")

        new_state[mid] = status

        prev_status = prev_state.get(mid)

        # Skip if no change or first run
        if prev_status is None or prev_status == status:
            continue

        # Status changed — send alert
        _, prev_emoji = STATUS_MAP.get(prev_status, ("unknown", "❓"))
        status_name, emoji = STATUS_MAP.get(status, ("unknown", "❓"))

        if status == 2:  # Back up
            msg = (
                f"{emoji} <b>RECOVERED</b>\n"
                f"<b>{name}</b> is back UP\n"
                f"<code>{url}</code>"
            )
        elif status in (8, 9):  # Down
            msg = (
                f"{emoji} <b>DOWN</b>\n"
                f"<b>{name}</b> is {status_name}!\n"
                f"<code>{url}</code>"
            )
        else:
            msg = (
                f"{emoji} <b>Status changed</b>\n"
                f"<b>{name}</b>: {status_name}\n"
                f"<code>{url}</code>"
            )

        logger.info("Alert: %s → %s (%s)", name, status_name, status)
        telegram_send(msg)

    save_state(new_state)


def send_startup_report():
    """Send current status of all monitors on startup."""
    logger.info("Fetching monitors from UptimeRobot...")
    monitors = uptimerobot_get_monitors()
    if not monitors:
        logger.warning("No monitors found in UptimeRobot")
        telegram_send("⚠️ <b>AI Mentor Monitor</b>\nStarted, but no monitors found in UptimeRobot.")
        return

    logger.info("Found %d monitors, sending startup report to Telegram", len(monitors))
    lines = ["🤖 <b>AI Mentor Monitor started</b>\n"]
    for m in monitors:
        status = m["status"]
        name = m["friendly_name"]
        _, emoji = STATUS_MAP.get(status, ("unknown", "❓"))
        lines.append(f"{emoji} {name}")

    if telegram_send("\n".join(lines)):
        logger.info("Startup report sent to Telegram")
    else:
        logger.error("Failed to send startup report")


def main():
    if not all([API_KEY, BOT_TOKEN, CHAT_ID]):
        logger.error(
            "Missing env vars. Required: UPTIMEROBOT_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID"
        )
        sys.exit(1)

    logger.info("Starting UptimeRobot → Telegram bridge (poll every %ds)", POLL_INTERVAL)

    # Send startup report
    send_startup_report()

    # Initialize state on first run
    monitors = uptimerobot_get_monitors()
    if monitors:
        state = {str(m["id"]): m["status"] for m in monitors}
        save_state(state)

    # Main loop
    logger.info("Entering main loop (checking every %ds)", POLL_INTERVAL)
    while True:
        time.sleep(POLL_INTERVAL)
        try:
            check_and_alert()
        except Exception as e:
            logger.error("Check failed: %s", e)


if __name__ == "__main__":
    main()
