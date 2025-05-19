import streamlit as st
import requests
import json
import time
import threading
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins
from solana.keypair import Keypair
from solana.rpc.api import Client
from jupiter_python import Jupiter

stop_bot = False

st.set_page_config(page_title="Sol Sniper", layout="centered")
st.title("Solana Meme Token Sniper")
st.markdown("**Auto-buy 0.5 SOL | Auto-sell x multiplier | Stop Loss -30%**")

api_key = st.text_input("Birdeye API Key", type="password")
mnemonic = st.text_area("12-word Mnemonic (Seed Phrase)", height=100)
slippage = st.slider("Slippage (%)", 0.1, 10.0, 3.0)
auto_sell_multiplier = st.selectbox("Auto-Sell Multiplier", [2, 3, 5, 10], index=2)
status = st.empty()

if st.button("Stop Bot"):
    stop_bot = True

def start_bot(status):
    global stop_bot
    stop_bot = False

    try:
        # Μετατροπή mnemonic σε Keypair
        seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
        bip44 = Bip44.FromSeed(seed_bytes, Bip44Coins.SOLANA)
        private_key = bip44.PrivateKey().Raw().ToBytes()
        keypair = Keypair.from_secret_key(private_key)
    except Exception as e:
        status.error(f"Σφάλμα στο keypair: {e}")
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
    if not api_key or not mnemonic:
        st.error("Συμπλήρωσε API key και mnemonic")
    else:
        threading.Thread(target=start_bot, args=(status,)).start()
