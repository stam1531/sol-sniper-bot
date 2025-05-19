import streamlit as st
import requests
import time
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.signature import Signature
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
import base64

JUPITER_URL = "https://quote-api.jup.ag/v6/swap"

def get_keypair_from_mnemonic(mnemonic: str):
    seed = Bip39SeedGenerator(mnemonic).Generate()
    bip44_def_ctx = Bip44.FromSeed(seed, Bip44Coins.SOLANA)
    acct = bip44_def_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
    priv_key = acct.PrivateKey().Raw().ToBytes() + acct.PublicKey().RawCompressed().ToBytes()
    return Keypair.from_bytes(priv_key[:64])

def execute_swap(input_mint, output_mint, amount, slippage, keypair):
    headers = {"Content-Type": "application/json"}
    params = {
        "inputMint": input_mint,
        "outputMint": output_mint,
        "amount": str(amount),
        "slippageBps": int(slippage * 100),
        "userPublicKey": str(keypair.pubkey()),
        "wrapUnwrapSOL": True,
        "feeBps": 0
    }

    # Step 1: Fetch swap transaction
    response = requests.get(JUPITER_URL, params=params)
    if response.status_code != 200:
        st.error(f"Swap query failed: {response.text}")
        return
    data = response.json()
    swap_tx = data.get("swapTransaction")
    if not swap_tx:
        st.error("No transaction returned.")
        return

    # Step 2: Sign and send transaction
    swap_tx_bytes = base64.b64decode(swap_tx)
    from solders.transaction import VersionedTransaction
    tx = VersionedTransaction.from_bytes(swap_tx_bytes)
    tx.sign([keypair])

    send_resp = requests.post(
        "https://rpc-proxy.jup.ag/v1/send",
        json={"tx": base64.b64encode(bytes(tx)).decode()}
    )
    if send_resp.status_code == 200:
        txid = send_resp.json().get("txid")
        st.success(f"Transaction sent! Signature: {txid}")
        st.write(f"https://solscan.io/tx/{txid}")
    else:
        st.error(f"Transaction failed to send: {send_resp.text}")

# Streamlit interface
st.title("Solana Sniping Bot")

mnemonic = st.text_input("Enter your 12-word mnemonic:", type="password")
input_mint = st.text_input("Token to SELL (input mint address)", value="So11111111111111111111111111111111111111112")  # SOL
output_mint = st.text_input("Token to BUY (output mint address)")
amount = st.number_input("Amount to use (in lamports)", value=500_000_000)  # 0.5 SOL
slippage = st.slider("Slippage (%)", 0.1, 5.0, 1.0)

if st.button("Snipe Token"):
    try:
        st.info("Sniping in progress...")
        keypair = get_keypair_from_mnemonic(mnemonic)
        execute_swap(input_mint, output_mint, int(amount), slippage, keypair)
    except Exception as e:
        st.error(f"Σφάλμα Keypair: {e}")
