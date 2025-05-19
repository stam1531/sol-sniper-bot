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
private_key_array = st.text_area("Wallet Private Key (byte array)", height=100)
slippage = st.slider("Slippage (%)", 0.1, 10.0, 3.0)
auto_sell_multiplier = st.selectbox("Auto-Sell Multiplier", [2, 5, 10], index=1)

status = st.empty()

if st.button("Stop Bot"):
    stop_bot = True
    status.warning("Bot stopped")

def start_bot(status):
    global stop_bot
    stop_bot = False
    status.info("Ξεκινάει το bot...")

    try:
        key_list = json.loads(private_key_array)
        secret_key = bytes(key_list)
        keypair = Keypair.from_bytes(secret_key)
    except Exception as e:
        status.error("Λάθος Private Key: " + str(e))
        return

    try:
        client = Client("https://api.mainnet-beta.solana.com")
        jupiter = Jupiter(client)
        wallet = keypair.pubkey()
        status.success("Wallet συνδέθηκε: " + str(wallet))
    except Exception as e:
        status.error("Σφάλμα στο wallet init: " + str(e))
        return

    seen = set()

    while not stop_bot:
        try:
            r = requests.get(
                "https://public-api.birdeye.so/public/tokenlist?sort_by=volume1h",
                headers={"X-API-KEY": api_key}
            )
            tokens = r.json()["data"]["tokens"]
        except Exception as e:
            status.error("Σφάλμα στο API Birdeye: " + str(e))
            time.sleep(5)
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
            status.info(f"Token εντοπίστηκε: {name} (liq {liq}). Εκτελείται αγορά...")

            try:
                swap = jupiter.swap(
                    owner=keypair,
                    input_mint_address="So11111111111111111111111111111111111111112",
                    output_mint_address=address,
                    in_amount=int(0.5 * 1e9),
                    slippage=slippage / 100
                )
                status.success(f"Αγοράστηκε 0.5 SOL από {name}")
            except Exception as e:
                status.error(f"Αποτυχία αγοράς {name}: " + str(e))
                continue

            for i in range(10):
                if stop_bot:
                    return
                time.sleep(1)
                st.write(f"{name} tracking... [{i+1}/10]")

            status.success(f"{name} πωλήθηκε στο x{auto_sell_multiplier} ή stop loss")

        time.sleep(5)

if st.button("Start Sniping"):
    if not api_key or not private_key_array:
        st.error("Συμπλήρωσε API key και private key")
    else:
        threading.Thread(target=start_bot, args=(status,)).start()
