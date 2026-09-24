import os
import time
import requests
from telegram import Bot
from flask import Flask

# Configurazione del server web per soddisfare Render e tenere aperta la porta
app = Flask(__name__)

@app.route('/')
def home():
    return "Radio Verbania Bot is running!"

# Parametri del bot e della radio
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = "-1004486063729"
PINNED_MESSAGE_ID = None  # ID del messaggio pinnato nel canale
ZENO_API_URL = "https://api.zeno.fm/mounts/metadata/a1usb5hslvgvv"
PLAYER_URL = "https://zeno.fm/player/radio-verbania"

bot = Bot(token=TOKEN)

def get_current_song():
    try:
        response = requests.get(ZENO_API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("title", "Brano sconosciuto")
    except Exception as e:
        print(f"Errore nel recupero della metadata: {e}")
    return None

def update_radio_bot():
    global PINNED_MESSAGE_ID
    last_song = ""
    
    while True:
        current_song = get_current_song()
        if current_song and current_song != last_song:
            last_song = current_song
            # Messaggio che unisce il nome del brano in onda e il link della radio
            text = f"🎶 **In onda ora su Radio Verbania:**\n{current_song}\n\n🎧 Ascolta qui: {PLAYER_URL}"
            
            try:
                if PINNED_MESSAGE_ID is None:
                    # Invia il messaggio iniziale e lo pinna nel canale
                    sent_msg = bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")
                    PINNED_MESSAGE_ID = sent_msg.message_id
                    bot.pin_chat_message(chat_id=CHAT_ID, message_id=PINNED_MESSAGE_ID)
                else:
                    # Aggiorna il testo del messaggio pinnato esistente in tempo reale
                    bot.edit_message_text(
                        chat_id=CHAT_ID,
                        message_id=PINNED_MESSAGE_ID,
                        text=text,
                        parse_mode="Markdown"
                    )
            except Exception as e:
                print(f"Errore Telegram: {e}")
                
        time.sleep(30) # Controlla ogni 30 secondi se cambia la traccia

if __name__ == "__main__":
    import threading
    # Avvia la logica della radio in background
    t = threading.Thread(target=update_radio_bot)
    t.daemon = True
    t.start()
    
    # Avvia Flask sulla porta richiesta da Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
