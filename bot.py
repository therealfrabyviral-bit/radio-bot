import requests
import time

CHAT_ID = -1004486063729
TOKEN = "8617649221:AAGLKbATz5azQYtnwdR-SXwjY5wDS61CL7Y"

def send_telegram(method, data):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Errore Telegram: {e}")
        return None

def get_now_playing():
    try:
        r = requests.get("https://api.zeno.fm/mounts/metadata/a1usb5hslvgvv", timeout=5)
        data = r.json()
        return data.get("title", "Radio in onda")
    except Exception:
        return "In onda su Zeno.fm"

print("Avvio del monitoraggio radio cloud 24/7...")

last_title = None
live_message_id = None

title = get_now_playing()
last_title = title
testo = f"🔴 IN ONDA ORA\n🎶 {title}"

res = send_telegram("sendMessage", {"chat_id": CHAT_ID, "text": testo})
if res and res.get("ok"):
    live_message_id = res["result"]["message_id"]
    send_telegram("pinChatMessage", {"chat_id": CHAT_ID, "message_id": live_message_id, "disable_notification": True})
    print("Messaggio iniziale inviato e pinnato sul cloud!")

while True:
    time.sleep(15)
    title = get_now_playing()

    if title != last_title:
        last_title = title
        testo = f"🔴 IN ONDA ORA\n🎶 {title}"

        if live_message_id:
            edit_res = send_telegram("editMessageText", {
                "chat_id": CHAT_ID,
                "message_id": live_message_id,
                "text": testo
            })
            if edit_res and edit_res.get("ok"):
                print(f"Brano aggiornato sul cloud: {title}")