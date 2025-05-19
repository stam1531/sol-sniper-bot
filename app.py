import streamlit as st
import requests
import json
import time
import threading
from solders.keypair import Keypair
from solana.rpc.api import Client
from jupiter_python import Jupiter

stop_bot = False

st.set_page_config(page_title="Sol Sniper", layout="centered")
st.title("Solana Meme Token Sniper")
st.markdown("**Auto-buy 0.5 SOL | Auto-sell x multiplier | Stop Loss -30%**")

api_key = st.text_input("Birdeye API Key", type="password")
slippage = st.slider("Slippage (%)", 0.1, 10.0, 3.0)
auto_sell_multiplier = st.selectbox("Auto-Sell Multiplier", [2, 3, 5, 10], index=2)
status = st.empty()

# Το keypair σου (64 bytes)
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
    stop_bot = False

    try:
        keypair = Keypair.from_bytes(bytes(private_key_array))
    except Exception as e:
        status.error(f"Λάθος Keypair: {e}")
        return

    client = Client("https://api.mainnet-beta.solana.com")
    jupiter = Jupiter(client)
    seen = set()

    while not stop_bot:
        try:
            response = requests.get(
                "https://public-api.birdeye.so/public/tokenlist?sort_by=volume1h",
                headers={"X-API-KEY": api_key}
            )
            tokens = response.json()["data"]["tokens"]
        except Exception as e:
            print(f"API Error: {e}")
            time.sleep(5)
            continue

        for t in tokens[:10]:
            if stop_bot:
                print("Bot manually stopped.")
                return

            address = t["address"]
            name = t["symbol"]
            liq = t.get("liquidity", 0)

            if address in seen or liq < 8000:
                continue

            seen.add(address)
            print(f"Token εντοπίστηκε: {name} (liq {liq}). Εκτελείται αγορά...")

            try:
                swap = jupiter.swap(
                    owner=keypair,
                    input_mint_address="So11111111111111111111111111111111111111112",
                    output_mint_address=address,
                    in_amount=int(0.5 * 1e9),
                    slippage=slippage / 100
                )
                print(f"Αγοράστηκε 0.5 SOL από {name}")
            except Exception as e:
                print(f"Αποτυχία αγοράς {name}: {e}")
                continue

            for i in range(10):
                if stop_bot:
                    return
                time.sleep(1)
                print(f"{name} tracking... [{i+1}/10]")

            print(f"{name} πωλήθηκε στο x{auto_sell_multiplier} ή stop loss")

        time.sleep(5)

if st.button("Start Sniping"):
    if not api_key:
        st.error("Συμπλήρωσε API key")
    else:
        threading.Thread(target=start_bot, args=(status,)).start()
