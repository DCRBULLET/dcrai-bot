# core/telegram_alert.py

import requests
import logging

# Your bot credentials
BOT_TOKEN = "7003953382:AAEY1Yg8QMk_T02PD5cj1lfHAxMojDTm6ZU"
CHANNEL_ID = "-1002823773665"  # DCR AI

def send_trade_alert(data: dict):
    """
    Sends a trade alert to the DCR AI Telegram channel.
    Only used for live entries.
    """
    message = (
        f"🚨 *New Trade Placed*\n"
        f"━━━━━━━━━━━━━━\n"
        f"📈 *{data['symbol']}* | *{data['direction']}*\n"
        f"🎯 Entry: `{data['price']}`\n"
        f"🛑 SL: `{data['sl']}`\n"
        f"🎯 TP: `{data['tp']}`\n"
        f"💼 Lot: `{data['lot']}`\n"
        f"🧠 Strategy: `{data['strategy']}`\n"
        f"🆔 Order ID: `{data['order_id']}`"
    )

    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            logging.warning(f"⚠️ Telegram alert failed: {response.status_code} {response.text}")
    except Exception as e:
        logging.error(f"❌ Telegram alert error: {e}")
