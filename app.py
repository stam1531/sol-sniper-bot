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

st.set_page_config(page_title="Sol Sniper", page_icon="⚡")
st.title("Token Sniper")
st.markdown("**Auto-buy 0.5 SOL | Auto-sell x5 | Stop Loss -30%**")

api_key = st.text_input("Birdeye API Key")
private_key_array = st.text_area("Wallet Private Key (byte array)", placeholder="[1,2,3,...]")
slippage = st.slider("Slippage (%)", 0.1, 10.0, 3.0)
auto_sell_multiplier = st.selectbox("Auto-Sell Multiplier", [2, 3, 4, 5, 10])
status = st.empty()

if st.button("Stop Bot"):
    stop_bot = True

def start_bot(status):
    global stop_bot
    seen = set()
    client = Client("https://api.mainnet-beta.solana.com")

    try:
        secret_key = json.loads(private_key_array)
        keypair = Keypair.from_bytes(bytes(secret_key))
    except Exception as e:
        status.error(f"Λάθος Private Key: {e}")
        return

    jup = Jupiter(keypair)

    while not stop_bot:
        try:
            headers = {"X-API-KEY": api_key}
            response = requests.get("https://public-api.birdeye.so/public/tokenlist?sort_by=volume_24h", headers=headers)
            tokens = response.json().get("data", [])

            for token in tokens:
                address = token.get("address")
                liq = token.get("liquidity", 0)
                name = token.get("name", "N/A")

                if address in seen or liq < 8000:
                    continue

                seen.add(address)
                status.info(f"Token εντοπίστηκε: {name}")

                try:
                    jup_route = jup.route("So11111111111111111111111111111111111111112", address, 0.5, slippage=slippage)
                    if jup_route:
                        swap_tx = jup.swap(jup_route)
                        status.success(f"Αγοράστηκε: {name}")
                        print(f"Αγοράστηκε: {name} στη διεύθυνση {address}")

                        target_price = jup_route.out_amount * auto_sell_multiplier
                        stop_loss = jup_route.out_amount * 0.7

                        while True:
                            price_check = requests.get(f"https://public-api.birdeye.so/public/price?address={address}", headers=headers)
                            price = price_check.json().get("data", {}).get("value", 0)

                            if price >= target_price:
                                jup_route_sell = jup.route(address, "So11111111111111111111111111111111111111112", jup_route.out_amount, slippage=slippage)
                                if jup_route_sell:
                                    jup.swap(jup_route_sell)
                                    status.success(f"Πωλήθηκε με κέρδος x{auto_sell_multiplier}: {name}")
                                    break

                            if price <= stop_loss:
                                jup_route_sell = jup.route(address, "So11111111111111111111111111111111111111112", jup_route.out_amount, slippage=slippage)
                                if jup_route_sell:
                                    jup.swap(jup_route_sell)
                                    status.error(f"Πωλήθηκε στο Stop Loss: {name}")
                                    break

                            time.sleep(5)

                except Exception as e:
                    status.error(f"Σφάλμα με το token {name}: {e}")
        except Exception as e:
            status.error(f"Σφάλμα στο API ή στο loop: {e}")

        time.sleep(10)

if st.button("Start Sniping"):
    threading.Thread(target=start_bot, args=(status,)).start()
