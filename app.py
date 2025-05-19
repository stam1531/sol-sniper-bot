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

st.set_page_config(page_title="Sol Sniping Bot", layout="centered")
st.title("Token Sniper")
st.markdown("**Auto-buy 0.5 SOL | Auto-sell x5 | Stop Loss -30%**")

api_key = st.text_input("Birdeye API Key")
slippage = st.slider("Slippage (%)", 0.1, 10.0, 3.0)
auto_sell_multiplier = st.selectbox("Auto-Sell Multiplier", [2, 5, 10])
status = st.empty()

# Χρήση του keypair σου
private_key_array = [
    91, 62, 76, 49, 14, 87, 155, 200, 72, 135, 198, 132, 24, 54, 124, 127,
    46, 158, 29, 8, 145, 148, 3, 78, 211, 58, 124, 77, 202, 144, 16, 30,
    173, 186, 160, 244, 5, 152, 100, 58, 164, 60, 52, 117, 126, 53, 60, 75,
    199, 136, 23, 2, 204, 133, 157, 1, 219, 149, 5, 213, 138, 161, 60, 181
]

if st.button("Stop Bot"):
    stop_bot = True

def start_bot(status):
    global stop_bot
    try:
        secret_key = json.loads(json.dumps(private_key_array))
        keypair = Keypair.from_bytes(bytes(secret_key))
    except Exception as e:
        status.error(f"Λάθος Private Key: {e}")
        return

    client = Client("https://api.mainnet-beta.solana.com")
    jupiter = Jupiter(keypair, client)
    seen = set()

    while not stop_bot:
        try:
            url = f"https://public-api.birdeye.so/public/tokenlist?sort_by=volume_24h&sort_type=desc"
            headers = {"X-API-KEY": api_key}
            response = requests.get(url, headers=headers)
            tokens = response.json()["data"]["tokens"]

            for token in tokens:
                address = token["address"]
                liq = token.get("liquidity", 0)
                name = token.get("name", "")

                if address in seen or liq < 8000:
                    continue

                seen.add(address)
                print(f"Token εντοπίστηκε: {name} ({address})")

                buy_res = jupiter.swap("So11111111111111111111111111111111111111112", address, 0.5, slippage)
                print(f"Αγορά: {buy_res}")

                if buy_res and "outputAmount" in buy_res:
                    amount_out = float(buy_res["outputAmount"]) / (10 ** token["decimals"])
                    target_price = amount_out * auto_sell_multiplier
                    stop_loss_price = amount_out * 0.7

                    while True:
                        time.sleep(5)
                        price_url = f"https://public-api.birdeye.so/public/price?address={address}"
                        price_res = requests.get(price_url, headers=headers)
                        price_data = price_res.json().get("data", {})
                        price = price_data.get("value", 0)

                        if price >= target_price or price <= stop_loss_price:
                            sell_res = jupiter.swap(address, "So11111111111111111111111111111111111111112", amount_out, slippage)
                            print(f"Πώληση: {sell_res}")
                            break

                if stop_bot:
                    break

            time.sleep(10)

        except Exception as e:
            print(f"Σφάλμα: {e}")
            time.sleep(5)

if st.button("Start Sniping"):
    threading.Thread(target=start_bot, args=(status,)).start()
