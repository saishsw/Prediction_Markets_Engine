import pandas as pd
import numpy as np
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'src', 'prediction_markets_agent'))


from api import polymarket

class Data_Preprocessor():
    def __init__(self, raw_top_market_trades):
        self.raw_top_market_trades = raw_top_market_trades
        self.raw_df = pd.DataFrame(self.raw_top_market_trades)
        self.clean_df = self.raw_df.copy()

    def clean_and_parse(self):
        if not self.raw_df:
            return pd.DataFrame()
        
        self.clean_df[["price", "size"]] = self.clean_df[["price", "size"]].astype(float)

        valid_size_mask = self.clean_df["size"] > 0
        self.clean_df = self.clean_df[valid_size_mask]

        valid_outcome_mask = self.clean_df["outcome"] == "YES"
        self.clean_df = self.clean_df[valid_outcome_mask]

        try:
            self.clean_df = self.clean_df[["id", "maker_address", "side", "outcome", "price", "size"]]
        except KeyError as e:
            print(f"[-] API Schema mismatch. Missing expected column: {e}")
            return self.clean_df
        
        return self.clean_df
    
class Whale_Alpha_Engine():
    def __init__(self, clean_df):
        self.clean_df = clean_df
        self.aggregated_df = pd.DataFrame()
    
    def calculate_metrics(self):
        self.clean_df["dollar_volume"] = self.clean_df["price"] * self.clean_df["size"]
        self.clean_df["directional_volume"] = np.where(self.clean_df["side"] == "BUY", self.clean_df["dollar_volume"], -self.clean_df["dollar_volume"])

        self.aggregated_df = self.clean_df.groupby("maker_address").agg(
            trade_count = ("id", "count"),
            total_volume = ("dollar_volume", "sum"),
            net_volume = ("directional_volume", "sum")
        ).reset_index()

        self.aggregated_df["avg_trade_size"] = self.aggregated_df["total_volume"] / self.aggregated_df["trade_count"]
        self.aggregated_df["volume_skew"] = self.aggregated_df["net_volume"] / self.aggregated_df["total_volume"]

    def get_elite_whales(self, min_volume, min_avg_size, min_skew):
        whale_mask = (
            (self.aggregated_df["total_volume"] > min_volume) &
            (self.aggregated_df["avg_trade_size"] > min_avg_size) &
            (self.aggregated_df["volume_skew"].abs() > min_skew) 
        )

        final_df = self.aggregated_df[whale_mask]

        return final_df.sort_values(by="total_volume", ascending = False)

