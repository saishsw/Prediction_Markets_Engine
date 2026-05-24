import os
import sys
import json
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'src'))

from api import polymarket 
from agents.market_scanner import Market_Scanner
from agents.top_traders_alpha import Data_Preprocessor, Whale_Alpha_Engine 

def pipeline():
    scanner = Market_Scanner()
    top_markets = Market_Scanner.get_top_markets()

    if not top_markets:
        return
    
    master_signals = []

    for index, market in enumerate(top_markets):
        try:
            target_token = market['outcomes']
            condition_id = market['condition_id']
            raw_trades = polymarket.get_market_trades(condition_id)

            preprocessor = Data_Preprocessor(raw_trades)
            clean_df = preprocessor.clean_and_parse(target_outcome=target_token)

            alpha_engine = Whale_Alpha_Engine()
            alpha_engine.calculate_metrics()
            elite_whales = alpha_engine.get_elite_whales()
            signal_payload = alpha_engine.generate_signals(elite_whales)

            if signal_payload.get("whale_count", 0) > 0:
                signal_payload["market_title"] = market['title']
                signal_payload["market_slug"] = market['market_slug']
                signal_payload["tracked_target"] = target_token

                master_signals.append(signal_payload)
            
        except Exception as e:
            continue
        time.sleep(0.5)

        if master_signals:
            print(json.dumps(master_signals, indent=4))

if __name__ == "__main__":
    pipeline()






    

