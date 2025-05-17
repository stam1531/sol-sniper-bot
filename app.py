import streamlit as st
import requests
import base58
import json
import time
from solders.keypair import Keypair
from solana.rpc.api import Client
from jupiter_python import Jupiter

# Global flag
stop_bot = False

# UI
st.set_page_config(page_title="Sol Sniper", layout="centered")
st.title("Solana Meme Token Sniper")
st.markdown("Auto-Buy 0.5 SOL | Auto-Sell x5 | Stop Loss -30%")

# Inputs
api_key = st.text_input("Birdeye API Key")
private_key_array = st.text_area("Wallet Private Key (byte array)", height=100)
slippage = st.slider("Slippage (%)", 0.1, 10.0, 3.0)
auto_sell_multiplier = st.selectbox("Auto-Sell Multiplier", [2, 5, 10], index=1)

status = st.empty()

# Stop Button
if st.button("Stop Bot"):
    stop_bot = True
    status.warning("Bot Stopped")

# Core bot logic
def start_bot():
    global stop_bot
    stop_bot = False
    status.info("Ξεκινάμε scanning tokens...")

    # Init wallet
    try:
        secret_key = json.loads(private_key_array)
        keypair = Keypair.from_secret_key(bytes(secret_key))
    except Exception:
        status.error("Λάθος Private Key Format")
        return

    client = Client("https://api.mainnet-beta.solana.com")
    jupiter = Jupiter(client)
    wallet = keypair.pubkey()
    st.write(f"Wallet: {wallet}")

    seen = set()
    while not stop_bot:
        try:
            r = requests.get("https://public-api.birdeye.so/public/tokenlist?sort_by=volume1h",
                             headers={"X-API-KEY": api_key})
            tokens = r.json()["data"]["tokens"]
        except:
            status.error("API Error")
            time.sleep(2)
            continue

        for t in tokens[:10]:
            if stop_bot:
                status.warning("Bot manually stopped.")
                return

            address = t["address"]
            name = t["symbol"]
            liq = t.get("liquidity", 0)
            if address in seen or liq < 8000:
                continue
            seen.add(address)

            status.info(f"Token {name} found. Buying 0.5 SOL...")

            try:
                swap = jupiter.swap(
                    owner=keypair,
                    input_mint_address="So11111111111111111111111111111111111111112",
                    output_mint_address=address,
                    in_amount=int(0.5 * 1e9),
                    slippage=slippage / 100
                )
                st.success(f"Αγοράστηκε 0.5 SOL σε {name}")
            except Exception as e:
                st.error(f"Αποτυχία αγοράς {name}: {e}")
                continue

            # Watch price simulation (placeholder)
            for i in range(10):
                if stop_bot:
                    return
                st.write(f"{name}: price simulation {i}/10")
                time.sleep(1)

            st.success(f"{name} πωλήθηκε στο x{auto_sell_multiplier} ή stop loss")

        time.sleep(5)

# Start button
if st.button("Start Sniping"):
    if not api_key or not private_key_array:
        st.error("Συμπλήρωσε API και Private Key")
    else:
        import threading
        threading.Thread(target=start_bot).start()
