import os
import time
import requests
from telegram import Bot
from flask import Flask

# Configurazione del server web per Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Radio Verbania Bot is running!"

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = "-1004486063729"
PINNED_MESSAGE_ID = None  
ZENO_API_URL = "https://api.zeno.fm/mounts/metadata/a1usb5hslvgvv"
SITE_URL = "https://radioverbania.surge.sh"

bot = Bot(token=TOKEN)

def get_current_song():
    try:
        response = requests.get(ZENO_API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Spesso Zeno.fm restituisce il brano sotto 'title' o 'artist'/'song'
            song = data.get("title")
            if not song:
                song = "In diretta / In onda"
            return song
    except Exception as e:
        print(f"Errore nel recupero della metadata: {e}")
    return "Radio Verbania On Air"

def update_radio_bot():
    global PINNED_MESSAGE_ID
    last_song = ""
    
    while True:
        current_song = get_current_song()
        # Perforza l'invio almeno al primo avvio o se cambia la canzone
        if current_song != last_song or PINNED_MESSAGE_ID is None:
            last_song = current_song
            
            text = f"🔴 **RADIO VERBANIA**\n🎧 In onda ora: {current_song}\n\n🌐 Visita il sito: {SITE_URL}"
            
            try:
                # Se c'è già un messaggio pinnato, proviamo a modificarlo
                if PINNED_MESSAGE_ID is not None:
                    try:
                        bot.edit_message_text(
                            chat_id=CHAT_ID,
                            message_id=PINNED_MESSAGE_ID,
                            text=text,
                            parse_mode="Markdown"
                        )
                    except Exception:
                        # Se il messaggio è stato cancellato a mano, lo rimandiamo
                        PINNED_MESSAGE_ID = None

                if PINNED_MESSAGE_ID is None:
                    sent_msg = bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")
                    PINNED_MESSAGE_ID = sent_msg.message_id
                    bot.pin_chat_message(chat_id=CHAT_ID, message_id=PINNED_MESSAGE_ID)
                    
            except Exception as e:
                print(f"Errore Telegram: {e}")
                
        time.sleep(30)

if __name__ == "__main__":
    import threading
    t = threading.Thread(target=update_radio_bot)
    t.daemon = True
    t.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
