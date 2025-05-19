import streamlit as st
import threading
from solders.keypair import Keypair
from solders.pubkey import Pubkey
import base64

# Σταθερές
PRIVATE_KEY_BYTES = [
    91, 62, 76, 49, 14, 87, 155, 200, 72, 135, 198, 132, 24, 54, 124, 127,
    46, 158, 29, 8, 145, 148, 3, 78, 211, 58, 124, 77, 202, 144, 16, 30,
    173, 186, 160, 244, 5, 152, 100, 58, 164, 60, 52, 117, 126, 53, 60, 75,
    199, 136, 23, 2, 204, 133, 157, 1, 219, 149, 5, 213, 138, 161, 60, 181
]

# Δημιουργία keypair από byte array
try:
    keypair = Keypair.from_bytes(bytes(PRIVATE_KEY_BYTES))
except Exception as e:
    st.error(f"Λάθος στο Keypair: {e}")
    st.stop()

# UI
st.title("Solana Sniping Bot")
st.markdown("Ready to snipe on Solana")

# Κατάσταση bot
bot_running = st.empty()

def start_bot():
    try:
        print("Ξεκινάει το bot...")
        print(f"Wallet Address: {keypair.pubkey()}")
        print("Εδώ θα μπουν οι συναλλαγές μέσω Jupiter API...")
        # TODO: ενσωμάτωση πραγματικών συναλλαγών
    except Exception as e:
        print(f"Λάθος κατά την εκκίνηση bot: {e}")

if st.button("Start Bot"):
    bot_running.text("Bot is running...")
    threading.Thread(target=start_bot).start()
