import os
import time
import requests
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Radio Verbania Bot is running!"

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = "-1004486063729"
PINNED_MESSAGE_ID = None  
ZENO_API_URL = "https://api.zeno.fm/mounts/metadata/a1usb5hslvgvv"
SITE_URL = "https://radioverbania.surge.sh"

def get_current_song():
    try:
        response = requests.get(ZENO_API_URL, timeout=10)
        print(f"Status: {response.status_code}, Contenuto: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict):
                    song = (
                        data.get("title") or 
                        data.get("song") or 
                        data.get("streamTitle") or 
                        data.get("now_playing") or
                        data.get("ticker")
                    )
                    if song:
                        return str(song).strip()
                elif isinstance(data, list) and len(data) > 0:
                    first = data[0]
                    if isinstance(first, dict):
                        song = first.get("title") or first.get("song")
                        if song:
                            return str(song).strip()
            except Exception:
                text_clean = response.text.strip()
                if text_clean and "{" not in text_clean:
                    return text_clean
                    
    except Exception as e:
        print(f"Errore nel recupero della metadata: {e}")
    
    return "In diretta"

def send_telegram(method, payload):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Errore richiesta Telegram {method}: {e}")
        return None

def update_radio_bot():
    global PINNED_MESSAGE_ID
    last_song = ""
    
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
                    if not res or not res.get("ok"):
                        PINNED_MESSAGE_ID = None  

                if PINNED_MESSAGE_ID is None:
                    send_payload = {
                        "chat_id": CHAT_ID,
                        "text": text
                    }
                    res = send_telegram("sendMessage", send_payload)
                    if res and res.get("ok"):
                        PINNED_MESSAGE_ID = res["result"]["message_id"]
                        
                        pin_payload = {
                            "chat_id": CHAT_ID,
                            "message_id": PINNED_MESSAGE_ID
                        }
                        send_telegram("pinChatMessage", pin_payload)
                        
            except Exception as e:
                print(f"Errore ciclo bot: {e}")
                
        time.sleep(30)

if __name__ == "__main__":
    import threading
    t = threading.Thread(target=update_radio_bot)
    t.daemon = True
    t.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
