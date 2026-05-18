import requests
import json

POLYMARKET_DATA_URL = "https://data-api.polymarket.com"
POLYMARKET_CLOB_URL = "https://clob.polymarket.com"
POLYMARKET_GAMMA_URL = "https://gamma-api.polymarket.com"

def get_live_orderbook(token_id):
    endpoint = f"{POLYMARKET_CLOB_URL}/book"
    response = requests.get(endpoint, params = {"token_id" : id})

    if response.status_code == 200:
        orderbook_dict = response.json()
        best_bid = float(orderbook_dict["bids"][0]["price"]) if orderbook_dict.get("bids") else 0.0
        best_ask = float(orderbook_dict["asks"][0]["price"]) if orderbook_dict.get("asks") else 1.0
        return {"bid": best_bid, "ask": best_ask}
    
    else:
        return {"bid": 0.0, "ask": 1.0}

def get_market_token_ids(slug):
    endpoint = f"{POLYMARKET_GAMMA_URL}/events"
    response = requests.get(endpoint, params = {"slug" : slug})

    if response.status_code == 200:
        event_dict = response.json()

        if len(event_dict) > 0:
            market_data = event_dict[0]["markets"][0]
            outcomes_raw = market_data.get("outcomes", [])
            token_ids_raw = market_data.get("clobTokenIds", [])

            outcomes = json.loads(outcomes_raw)
            token_ids = json.loads(token_ids_raw)

            return dict(zip(outcomes, token_ids))
        
    else:
        return {}
    
def get_market_condition_ids(slug):
    endpoint = f"{POLYMARKET_GAMMA_URL}/events"
    response = requests.get(endpoint, params = {"slug" : slug})

    if response.status_code == 200:
        event_dict = response.json()

        if len(event_dict) > 0:
            condition_id = event_dict[0]["markets"][0]["conditionId"]
            return condition_id
        else:
            return {}
        
    else:
        return ""

def get_recent_public_trades(limit = 100):
    endpoint = f"{POLYMARKET_DATA_URL}/trades"
    response = requests.get(endpoint, params={"limit": limit})

    if response.status_code == 200:
        payload = response.json()
        return payload.get("data", [])
    else:
        return {}
        
def get_market_trades(condition_id, limit = 100):
    endpoint = f"{POLYMARKET_DATA_URL}/trades"
    response = requests.get(endpoint, params = {"market" : condition_id, "limit" : limit} )

    if response.status_code == 200:
        payload = response.json()
        return payload.get("data", [])
    else:
        return []

def get_user_positons(user):
    endpoint = f"{POLYMARKET_DATA_URL}/positions"
    response = requests.get(endpoint, params = {"user" : user})

    if response.status_code == 200:
        user_positions = response.json()
        return user_positions
    else:
        return []




