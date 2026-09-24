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
PINNED_MESSAGE_ID = None  
# URL corretto con /subscribe/ per le API pubbliche di Zeno.fm
ZENO_API_URL = "https://api.zeno.fm/mounts/metadata/subscribe/a1usb5hslvgvv"
SITE_URL = "https://radioverbania.surge.sh"

def get_current_song():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'text/event-stream'
        }
        print("Invio richiesta a Zeno.fm (subscribe)...", flush=True)
        
        # Usiamo stream=True per leggere lo stream di eventi SSE di Zeno
        response = requests.get(ZENO_API_URL, headers=headers, stream=True, timeout=8)
        print(f"ZENO RESPONSE CODE: {response.status_code}", flush=True)
        
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    decoded = line.decode('utf-8', errors='ignore')
                    print(f"ZENO LINE: {decoded}", flush=True)
                    
                    # Rimuoviamo il prefisso "data:" tipico degli SSE se presente
                    if decoded.startswith("data:"):
                        decoded = decoded[5:].strip()
                        
                    try:
                        data = json.loads(decoded)
                        if isinstance(data, dict):
                            title = data.get("title") or data.get("song") or data.get("streamTitle") or data.get("now_playing") or data.get("songTitle")
                            artist = data.get("artist") or data.get("author")
                            
                            if artist and title:
                                return f"{artist} - {title}".strip()
                            elif title:
                                return str(title).strip()
                                
                            # Cerca tra tutte le chiavi se non trova i campi standard
                            for k, v in data.items():
                                if any(kw in k.lower() for kw in ["title", "song", "playing", "artist", "name", "text"]) and v:
                                    return str(v).strip()
                    except json.JSONDecodeError:
                        # Se non è un JSON puro ma del testo valido
                        if decoded and not decoded.startswith("{") and len(decoded) > 1:
                            return decoded
                            
                    # Usciamo dal ciclo dopo aver letto il primo pacchetto utile per evitare blocchi
                    break
                    
    except Exception as e:
        print(f"ECCEZIONE CRITICA in get_current_song: {e}", flush=True)
    
    return "In diretta"

def send_telegram(method, payload):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Errore richiesta Telegram {method}: {e}", flush=True)
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
                print(f"Errore ciclo bot: {e}", flush=True)
                
        time.sleep(30)

if __name__ == "__main__":
    import threading
    t = threading.Thread(target=update_radio_bot)
    t.daemon = True
    t.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
