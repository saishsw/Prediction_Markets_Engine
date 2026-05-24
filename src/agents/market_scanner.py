import requests
import json
import pandas as pd
import numpy as np
import sys
import os
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'src'))

from api import polymarket


logger = logging.getLogger(__name__)


def _parse_json_like(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    return []

class Market_Scanner():
    def __init__(self):
        self.endpoint = f"https://gamma-api.polymarket.com/markets"
        self.params = {
            "limit" : 100, 
            "order" : "volumeNum",
            "closed" : "false", 
        }
        self.liquidity_quantile = 0.75
        self.volume_quantile = 0.75

    def fetch_raw_markets(self):
        try:
            response = requests.get(self.endpoint, params=self.params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning("Scanner API returned HTTP %s", response.status_code)
                return []
                
        except requests.exceptions.RequestException as e:
            logger.warning("Scanner network failure: %s", e)
            return []
    
    def get_top_markets(self):
        raw_data = self.fetch_raw_markets()
        if not raw_data:
            return []
        
        df = pd.DataFrame(raw_data)
        if df.empty:
            return []

        if 'liquidity' not in df.columns or 'volume' not in df.columns:
            logger.warning("Scanner payload is missing liquidity or volume columns")
            return []

        df['liquidity'] = pd.to_numeric(df['liquidity'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        df = df.dropna(subset=['liquidity', 'volume'])

        if df.empty:
            return []

        min_liquidity = df['liquidity'].quantile(self.liquidity_quantile)
        min_volume = df['volume'].quantile(self.volume_quantile)

        mask = (df['liquidity'] >= min_liquidity) & (df['volume'] >= min_volume)
        filtered_df = df[mask]
        qualified_records = filtered_df.to_dict('records')
    
        qualified_markets = []

        for market in qualified_records:
            outcomes_list = _parse_json_like(market.get('outcomes', []))
            
            qualified_markets.append({
                "market_slug": market.get('slug'),
                "condition_id": market.get('conditionId') or market.get('condition_id'),
                "liquidity": market.get('liquidity'),
                "volume": market.get('volume'),
                "outcomes": outcomes_list,
                "outcome": outcomes_list[0] if outcomes_list else None,
                "title": market.get('question') or market.get('title')
            })
            
        return qualified_markets
        