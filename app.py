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

st.set_page_config(page_title="Sol Sniper Bot", layout="centered")
st.title("Token Sniper")
st.markdown("**Auto-buy 0.5 SOL | Auto-sell x5 | Stop Loss -30%**")

api_key = st.text_input("Birdeye API Key", value="", type="password")
slippage = st.slider("Slippage (%)", 0.1, 10.0, 3.0)
auto_sell_multiplier = st.selectbox("Auto-Sell Multiplier", [2, 3, 5, 10], index=2)
status = st.empty()

# Ενσωματωμένο Private Key
private_key_array = [
    124, 77, 202, 144, 16, 30, 173, 186, 160, 244, 5, 152,
    100, 58, 164, 60, 52, 117, 126, 53, 60, 75, 199, 136,
    23, 2, 204, 133, 157, 1, 219, 149, 5, 213, 138, 161,
    60, 181, 91, 62, 76, 49, 14, 87, 155, 200, 72, 135,
    198, 132, 24, 54, 124, 127, 46, 158, 29, 8, 145, 148,
    3, 78, 211, 58
]

def start_bot():
    global stop_bot
    try:
        secret_key = bytes(private_key_array)
        keypair = Keypair.from_bytes(secret_key)
    except Exception as e:
        print(f"Λάθος Private Key: {e}")
        return

    client = Client("https://api.mainnet-beta.solana.com")
    jupiter = Jupiter(keypair, slippage)

    seen = set()

    while not stop_bot:
        try:
            headers = {"X-API-KEY": api_key}
            response = requests.get("https://public-api.birdeye.so/public/last_tokens", headers=headers)
            tokens = response.json().get("data", [])

            for token in tokens:
                if stop_bot:
                    break

                address = token["address"]
                liq = token.get("liquidity", 0)
                name = token.get("name", "")

                if address in seen or liq < 8000:
                    continue

                seen.add(address)
                print(f"Token εντοπίστηκε: {name} ({address})")

                buy_response = jupiter.buy(address, 0.5)
                print(f"Αγορά: {buy_response}")

                entry_price = jupiter.get_price(address)
                target_price = entry_price * auto_sell_multiplier
                stop_loss = entry_price * 0.7

                while True:
                    current_price = jupiter.get_price(address)
                    if current_price >= target_price:
                        sell_response = jupiter.sell(address)
                        print(f"Auto-Sell επιτυχές: {sell_response}")
                        break
                    elif current_price <= stop_loss:
                        sell_response = jupiter.sell(address)
                        print(f"Stop Loss ενεργοποιήθηκε: {sell_response}")
                        break

                    time.sleep(5)

        except Exception as e:
            print(f"Σφάλμα: {e}")
            time.sleep(5)

if st.button("Start Sniping"):
    stop_bot = False
    threading.Thread(target=start_bot).start()

if st.button("Stop Bot"):
    stop_bot = True
    print("Bot σταμάτησε.")
