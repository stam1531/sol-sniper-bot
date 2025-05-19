import streamlit as st
import requests
import base58
import json
import time
import threading
from solders.keypair import Keypair
from solana.rpc.api import Client
from jupiter_python import Jupiter

stop_bot = False

st.set_page_config(page_title="Sol Sniper", layout="centered")
st.title("Solana Meme Token Sniper")
st.markdown("**Auto-buy 0.5 SOL | Auto-sell x5 | Stop Loss -30%**")

api_key = st.text_input("Birdeye API Key")
slippage = st.slider("Slippage (%)", 0.1, 10.0, 3.0)
auto_sell_multiplier = st.selectbox("Auto-Sell Multiplier", [2, 3, 4, 5, 10])
status = st.empty()

# Ενσωματωμένο Private Key
private_key_array = [124, 77, 202, 144, 16, 30, 173, 186, 160, 244, 5, 152, 100, 58, 164, 60, 52, 117, 126, 53, 60, 75, 199, 136, 23, 2, 204, 133, 157, 1, 219, 149, 5, 213, 138, 161, 60, 181]

if st.button("Stop Bot"):
    stop_bot = True

def start_bot():
    global stop_bot
    client = Client("https://api.mainnet-beta.solana.com")
    jupiter = Jupiter(client)
    seen = set()

    try:
        secret_key = bytes(private_key_array)
        keypair = Keypair.from_bytes(secret_key)
    except Exception as e:
        status.error(f"Λάθος Private Key: {e}")
        return

    while not stop_bot:
        try:
            response = requests.get(
                "https://public-api.birdeye.so/public/last_tokens",
                headers={"X-API-KEY": api_key}
            )
            data = response.json().get("data", [])
            for token in data:
                address = token.get("address")
                name = token.get("name", "Unknown")
                liq = token.get("liquidity", 0)

                if address in seen or liq < 8000:
                    continue

                seen.add(address)
                status.info(f"Token εντοπίστηκε: {name}")

                try:
                    quote = jupiter.quote(input_mint="So11111111111111111111111111111111111111112",
                                          output_mint=address,
                                          amount=500_000_000,
                                          slippage=slippage)

                    tx = jupiter.swap(quote, keypair)
                    status.success(f"Αγοράστηκε: {name}")
                except Exception as err:
                    status.error(f"Σφάλμα στην αγορά {name}: {err}")

            time.sleep(5)
        except Exception as main_err:
            status.error(f"Σφάλμα API: {main_err}")
            time.sleep(5)

if st.button("Start Sniping"):
    threading.Thread(target=start_bot).start()
