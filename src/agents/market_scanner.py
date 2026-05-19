import requests
import json
import pandas as pd
import numpy as np
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'src'))

from api import polymarket

class Market_Scanner():
    def __init__(self):
        self.endpoint = f"https://gamma-api.polymarket.com/events"
        self.params = {
            "limit" : 100, 
            "order" : "volume_num",
            "closed" : False, 
        }
        self.liquidity_quantile(0.75)
        self.volume_quantile(0.75)

    def fetch_raw_markets(self):
        try:
            response = requests.get(self.endpoint, params=self.params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[-] Scanner API Error: Received HTTP status {response.status_code}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"[-] Scanner Network failure: {e}")
            return []
    
    def get_top_markets(self):
        raw_data = self.fetch_raw_markets()
        if not raw_data:
            return []
        
        df = pd.dataFrame(raw_data)
        df['liquidity'] = df['liquidity'].astype(float)
        df['volume'] = df['volume'].astype(float)

        min_liquidity = df['liquidity'].quantile(self.liquidity_quantile)
        min_volume = df['volume'].quantile(self.volume_quantile)

        mask = (df['liquidity'] >= min_liquidity) & (df['volume'] >= min_volume)
        filtered_df = df[mask]
        qualified_records = filtered_df.to_dict('records')
    
        qualified_markets = []

        for market in qualified_records:
            try:
                outcomes_list = json.loads(market.get('outcomes', '[]'))
            except json.JSONDecodeError:
                outcomes_list = []
            
            qualified_markets.append({
                "market_slug": market.get('slug'),
                "condition_id": market.get('conditionId'),
                "liquidity": market.get('liquidity'),
                "volume": market.get('volume'),
                "outcomes": outcomes_list,
                "title": market.get('question')
            })
            
        return qualified_markets
        