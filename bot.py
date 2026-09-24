import os
import time
import requests
from telegram import Bot
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

bot = Bot(token=TOKEN)

def get_current_song():
    try:
        response = requests.get(ZENO_API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            song = data.get("title")
            if not song:
                song = "In diretta"
            return song
    except Exception as e:
        print(f"Errore nel recupero della metadata: {e}")
    return "Radio Verbania On Air"

def update_radio_bot():
    global PINNED_MESSAGE_ID
    last_song = ""
    
    while True:
        current_song = get_current_song()
        if current_song != last_song or PINNED_MESSAGE_ID is None:
            last_song = current_song
            
            # Testo pulito senza simboli Markdown che possano spezzare il messaggio
            text = f"RADIO VERBANIA\nIn onda ora: {current_song}\n\nAscolta sul sito: {SITE_URL}"
            
            try:
                if PINNED_MESSAGE_ID is not None:
                    try:
                        bot.edit_message_text(
                            chat_id=CHAT_ID,
                            message_id=PINNED_MESSAGE_ID,
                            text=text
                        )
                    except Exception:
                        PINNED_MESSAGE_ID = None

                if PINNED_MESSAGE_ID is None:
                    sent_msg = bot.send_message(chat_id=CHAT_ID, text=text)
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
