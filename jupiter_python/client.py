import requests

class Jupiter:
    def __init__(self):
        self.base_url = "https://quote-api.jup.ag/v6"

    def get_price(self, input_mint, output_mint, amount):
        url = f"{self.base_url}/quote"
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": amount,
            "slippageBps": 100,
            "onlyDirectRoutes": False
        }
        response = requests.get(url, params=params)
        return response.json()
