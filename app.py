import streamlit as st
import time
import threading

# GLOBAL FLAG
stop_bot = False

# UI
st.set_page_config(page_title="Solana Sniping Bot", layout="centered")
st.title("Solana Meme Token Sniping Bot")
st.markdown("**Auto-buy 0.5 SOL | Auto-sell x10 | Stop loss -30%**")

# Inputs
api_key = st.text_input("Birdeye API Key")
private_key = st.text_area("Wallet Private Key (byte array)", height=100)
buy_amount = st.number_input("Buy Amount (SOL)", value=0.5)
slippage = st.slider("Slippage (%)", 0.1, 10.0, 3.0)
auto_sell_multiplier = st.selectbox("Auto-Sell Multiplier", [2, 5, 10, 20], index=2)

# Placeholder για status
status = st.empty()

# Stop button
if st.button("Stop Bot"):
    stop_bot = True
    status.warning("Bot stopped by user.")

# Πυρήνας λειτουργίας bot (DEMO VERSION για UI)
def start_bot():
    global stop_bot
    stop_bot = False
    status.info("Sniping ξεκίνησε. Περιμένουμε tokens...")

    for i in range(10):
        if stop_bot:
            status.warning("Bot σταμάτησε.")
            break
        st.write(f"[Token Found] DEMO{i} | Buy 0.5 SOL")
        time.sleep(1)
        st.write(f"[Auto-Sell set] x{auto_sell_multiplier} | Stop loss -30%")
        time.sleep(1)
        st.success(f"[TRADE DONE] Token{i} bought & sold (demo)")
        time.sleep(1)

# Start button
if st.button("Start Sniping"):
    if not api_key or not private_key:
        st.error("Συμπλήρωσε API Key και Private Key!")
    else:
        threading.Thread(target=start_bot).start()
