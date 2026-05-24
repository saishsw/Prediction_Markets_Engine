import requests
import json
import logging
import time

POLYMARKET_DATA_URL = "https://data-api.polymarket.com"
POLYMARKET_CLOB_URL = "https://clob.polymarket.com"
POLYMARKET_GAMMA_URL = "https://gamma-api.polymarket.com"


logger = logging.getLogger(__name__)


def _loads_if_needed(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return []
    if isinstance(value, list):
        return value
    return []


def get_live_orderbook(token_id):
    endpoint = f"{POLYMARKET_CLOB_URL}/book"
    try:
        response = requests.get(endpoint, params={"token_id": token_id}, timeout=10)

        if response.status_code == 200:
            orderbook_dict = response.json()
            best_bid = float(orderbook_dict["bids"][0]["price"]) if orderbook_dict.get("bids") else 0.0
            best_ask = float(orderbook_dict["asks"][0]["price"]) if orderbook_dict.get("asks") else 1.0
            return {"bid": best_bid, "ask": best_ask}

        logger.warning("Orderbook API returned HTTP %s for token %s", response.status_code, token_id)
    except requests.exceptions.RequestException as exc:
        logger.warning("Orderbook request failed for token %s: %s", token_id, exc)

    return {"bid": 0.0, "ask": 1.0}


def get_market_token_ids(slug):
    endpoint = f"{POLYMARKET_GAMMA_URL}/events"
    try:
        response = requests.get(endpoint, params={"slug": slug}, timeout=10)

        if response.status_code == 200:
            event_dict = response.json()

            if len(event_dict) > 0:
                market_data = event_dict[0]["markets"][0]
                outcomes = _loads_if_needed(market_data.get("outcomes", []))
                token_ids = _loads_if_needed(market_data.get("clobTokenIds", []))

                return dict(zip(outcomes, token_ids))
    except requests.exceptions.RequestException as exc:
        logger.warning("Token id lookup failed for slug %s: %s", slug, exc)

    return {}


def get_market_condition_id(slug):
    endpoint = f"{POLYMARKET_GAMMA_URL}/events"
    try:
        response = requests.get(endpoint, params={"slug": slug}, timeout=10)

        if response.status_code == 200:
            event_dict = response.json()

            if len(event_dict) > 0:
                condition_id = event_dict[0]["markets"][0]["conditionId"]
                return condition_id
    except requests.exceptions.RequestException as exc:
        logger.warning("Condition id lookup failed for slug %s: %s", slug, exc)

    return ""


def get_recent_public_trades(limit=100):
    endpoint = f"{POLYMARKET_DATA_URL}/trades"
    try:
        response = requests.get(endpoint, params={"limit": limit}, timeout=10)

        if response.status_code == 200:
            payload = response.json()
            if isinstance(payload, list):
                return payload
            if isinstance(payload, dict):
                return payload.get("data", [])
    except requests.exceptions.RequestException as exc:
        logger.warning("Recent trades request failed: %s", exc)

    return []


def get_market_trades(condition_id, target_depth=1000, page_size=1000, lookback_hours=None):
    endpoint = f"{POLYMARKET_DATA_URL}/trades"
    total_trades = []
    current_offset = 0
    page_size = max(1, min(int(page_size), 1000))
    cutoff_timestamp = None

    if lookback_hours is not None:
        try:
            cutoff_timestamp = int(time.time()) - int(lookback_hours * 3600)
        except (TypeError, ValueError):
            cutoff_timestamp = None

    while len(total_trades) < target_depth:
        params = {
            "market": condition_id,
            "limit": page_size,
            "offset": current_offset,
        }
        try:
            response = requests.get(endpoint, params=params, timeout=10)

            if response.status_code != 200:
                logger.warning("Trade request returned HTTP %s at offset %s", response.status_code, current_offset)
                break

            payload = response.json()
            batch = payload if isinstance(payload, list) else payload.get("data", [])
            if not batch:
                break

            total_trades.extend(batch)
            current_offset += len(batch)
            time.sleep(0.2)
        except requests.exceptions.RequestException as exc:
            logger.warning("Trade request failed at offset %s: %s", current_offset, exc)
            break

    if cutoff_timestamp is not None:
        filtered_trades = []
        for trade in total_trades:
            trade_timestamp = trade.get("timestamp")
            try:
                if trade_timestamp is not None and int(trade_timestamp) >= cutoff_timestamp:
                    filtered_trades.append(trade)
            except (TypeError, ValueError):
                continue
        total_trades = filtered_trades

    return total_trades[:target_depth]


def get_user_positons(user):
    endpoint = f"{POLYMARKET_DATA_URL}/positions"
    try:
        response = requests.get(endpoint, params={"user": user}, timeout=10)

        if response.status_code == 200:
            user_positions = response.json()
            return user_positions
    except requests.exceptions.RequestException as exc:
        logger.warning("Position request failed for user %s: %s", user, exc)

    return []


def get_user_trades(wallet_address):
    endpoint = f"{POLYMARKET_DATA_URL}/allTradesForUser"
    try:
        response = requests.get(endpoint, params={"hash": wallet_address}, timeout=10)

        if response.status_code == 200:
            payload = response.json()
            if isinstance(payload, list):
                return payload
            if isinstance(payload, dict):
                return payload.get("data", [])
    except requests.exceptions.RequestException as exc:
        logger.warning("User trade request failed for %s: %s", wallet_address, exc)

    return []




