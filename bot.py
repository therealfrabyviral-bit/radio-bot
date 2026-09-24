import os
import time
import json
import requests
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Radio Verbania Bot is running!"

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = "-1004486063729"
ZENO_API_URL = "https://api.zeno.fm/mounts/metadata/subscribe/a1usb5hslvgvv"
SITE_URL = "https://radioverbania.surge.sh"

PIN_FILE = "pinned.json"

def load_pinned_id():
    if os.path.exists(PIN_FILE):
        try:
            with open(PIN_FILE, "r") as f:
                data = json.load(f)
                return data.get("message_id")
        except Exception:
            pass
    return None

def save_pinned_id(message_id):
    try:
        with open(PIN_FILE, "w") as f:
            json.dump({"message_id": message_id}, f)
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Errore salvataggio pin file: {e}", flush=True)

PINNED_MESSAGE_ID = load_pinned_id()

def get_current_song():
    response = None
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'text/event-stream'
        }
        response = requests.get(ZENO_API_URL, headers=headers, stream=True, timeout=(5, 15))

        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    decoded = line.decode('utf-8', errors='ignore').strip()
                    if decoded.startswith("data:"):
                        json_str = decoded[5:].strip()
                        try:
                            data = json.loads(json_str)
                            if isinstance(data, dict):
                                title = data.get("streamTitle") or data.get("title") or data.get("song")
                                if title:
                                    print(f"[{time.strftime('%H:%M:%S')}] Titolo ricevuto: {title}", flush=True)
                                    return str(title).strip()
                        except json.JSONDecodeError:
                            pass
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Errore Zeno: {e}", flush=True)
    finally:
        if response is not None:
            response.close()

    return "In diretta"

def send_telegram(method, payload):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    try:
        response = requests.post(url, json=payload, timeout=10)
        res_json = response.json()
        print(f"[{time.strftime('%H:%M:%S')}] Telegram {method} response: {res_json}", flush=True)
        return res_json
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Errore richiesta Telegram {method}: {e}", flush=True)
        return None

def update_radio_bot():
    global PINNED_MESSAGE_ID
    last_song = ""
    
    time.sleep(5)
    
    while True:
        current_song = get_current_song()
        if current_song != last_song or PINNED_MESSAGE_ID is None:
            last_song = current_song
            
            text = f"🔴 RADIO VERBANIA\n🎧 In onda ora: {current_song}\n\n🌐 Ascolta sul sito: {SITE_URL}"
            
            try:
                if PINNED_MESSAGE_ID is not None:
                    edit_payload = {
                        "chat_id": CHAT_ID,
                        "message_id": PINNED_MESSAGE_ID,
                        "text": text
                    }
                    res = send_telegram("editMessageText", edit_payload)
                    # Se il messaggio non esiste più o dà errore strutturale, azzeriamo per crearne uno nuovo
                    if not res or (not res.get("ok") and "message to edit not found" in str(res.get("description", "")).lower()):
                        PINNED_MESSAGE_ID = None
                        save_pinned_id(None)

                if PINNED_MESSAGE_ID is None:
                    send_payload = {
                        "chat_id": CHAT_ID,
                        "text": text,
                        "disable_notification": True
                    }
                    res = send_telegram("sendMessage", send_payload)
                    if res and res.get("ok"):
                        PINNED_MESSAGE_ID = res["result"]["message_id"]
                        save_pinned_id(PINNED_MESSAGE_ID)
                        
                        pin_payload = {
                            "chat_id": CHAT_ID,
                            "message_id": PINNED_MESSAGE_ID,
                            "disable_notification": True
                        }
                        send_telegram("pinChatMessage", pin_payload)
                        
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] Errore ciclo bot: {e}", flush=True)
                
        time.sleep(30)

if __name__ == "__main__":
    import threading
    t = threading.Thread(target=update_radio_bot)
    t.daemon = True
    t.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, threaded=True)
