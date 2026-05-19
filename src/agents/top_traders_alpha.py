import pandas as pd
import numpy as np
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'src'))

from api import polymarket

class Data_Preprocessor():
    def __init__(self, raw_top_market_trades):
        self.raw_top_market_trades = raw_top_market_trades
        if isinstance(self.raw_top_market_trades, list):
            self.raw_df = pd.DataFrame(self.raw_top_market_trades)
        else:
            self.raw_df = pd.DataFrame()
        self.clean_df = self.raw_df.copy()

    def clean_and_parse(self, target_outcome=None):
        if self.raw_df.empty:
            return pd.DataFrame()
                
        rename_map = {
            "proxyWallet": "maker_address",
            "transactionHash": "id",
            "makerAddress": "maker_address" 
        }
        
        active_renames = {k: v for k, v in rename_map.items() if k in self.clean_df.columns}
        self.clean_df = self.clean_df.rename(columns=active_renames)

        if "id" not in self.clean_df.columns:
            self.clean_df["id"] = self.clean_df.index.astype(str)

        self.clean_df[["price", "size"]] = self.clean_df[["price", "size"]].astype(float)

        valid_size_mask = self.clean_df["size"] > 0
        self.clean_df = self.clean_df[valid_size_mask]

        if "outcome" in self.clean_df.columns and not self.clean_df.empty:
            if target_outcome is None:
                selected_target = self.clean_df["outcome"].value_counts().idxmax()
            else:
                unique_outcomes = self.clean_df["outcome"].unique()
                match_generator = [o for o in unique_outcomes if str(o).upper() == str(target_outcome).upper()]
        
            if match_generator:
                selected_target = match_generator[0]
            else:
                return pd.DataFrame()
            
        valid_outcome_mask = self.clean_df["outcome"] == selected_target
        self.clean_df = self.clean_df[valid_outcome_mask]


        try:
            self.clean_df = self.clean_df[["id", "maker_address", "side", "outcome", "price", "size"]]
        except KeyError as e:
            return pd.DataFrame()
        
        return self.clean_df
    
class Whale_Alpha_Engine():
    def __init__(self, clean_df):
        self.clean_df = clean_df
        self.aggregated_df = pd.DataFrame()
    
    def calculate_metrics(self):
        if self.clean_df.empty: return 

        self.clean_df["dollar_volume"] = self.clean_df["price"] * self.clean_df["size"]
        self.clean_df["directional_volume"] = np.where(self.clean_df["side"] == "BUY", self.clean_df["dollar_volume"], -self.clean_df["dollar_volume"])

        self.aggregated_df = self.clean_df.groupby("maker_address").agg(
            trade_count = ("id", "count"),
            total_volume = ("dollar_volume", "sum"),
            net_volume = ("directional_volume", "sum")
        ).reset_index()

        self.aggregated_df["avg_trade_size"] = self.aggregated_df["total_volume"] / self.aggregated_df["trade_count"]
        self.aggregated_df["volume_skew"] = self.aggregated_df["net_volume"] / self.aggregated_df["total_volume"]

    def get_elite_whales(self):
        if self.aggregated_df.empty:
            return pd.DataFrame()

        min_volume = self.aggregated_df['total_volume'].quantile(0.97)
        min_avg_size = self.aggregated_df['avg_trade_size'].quantile(0.95)

        vol_pass = (self.aggregated_df["total_volume"] > min_volume).sum()
        size_pass = (self.aggregated_df["avg_trade_size"] > min_avg_size).sum()
        skew_pass = (self.aggregated_df["volume_skew"].abs() > 0.85).sum()

        whale_mask = (
            (self.aggregated_df["total_volume"] > min_volume) &
            (self.aggregated_df["avg_trade_size"] > min_avg_size) &
            (self.aggregated_df["volume_skew"].abs() > 0.85) 
        )

        final_df = self.aggregated_df[whale_mask]
        return final_df.sort_values(by="total_volume", ascending=False)
    
    def generate_signals(self, elite_whales_df):
        if self.aggregated_df.empty or elite_whales_df.empty:
            return {
                "status": "scan_complete",
                "whale_count": 0,
                "signals": []
            }
        
        signals_list = []
        
        for _, whale in elite_whales_df.iterrows():
            address = whale['maker_address']
            whale_ledger = self.clean_df[self.clean_df['maker_address'] == address]
            latest_trade = whale_ledger.iloc[-1]
            action_verb = "BUY" if latest_trade['side'] == "BUY" else "SELL"

            whale_signal = {
                "wallet_address": address,
                "trade_count": int(whale['trade_count']),
                "total_volume": float(whale['total_volume']),
                "volume_skew": float(whale['volume_skew']),
                "avg_bet_size": float(whale['avg_trade_size']),
                "suggested_action": action_verb,
                "target_price": float(latest_trade['price']),
                "target_size": float(latest_trade['size'])
            }
            signals_list.append(whale_signal)
        
        return {
            "status": "whales_detected",
            "whale_count": len(signals_list),
            "signals": signals_list
        }

if __name__ == "__main__":
    market_slug = "nba-cle-nyk-2026-05-19"
    target_team = "Cavaliers"
    target_condition_id = polymarket.get_market_condition_id(market_slug)
    
    if not target_condition_id:
        sys.exit()
    
    raw_trades = polymarket.get_market_trades(target_condition_id, 1000)
    
    if not raw_trades:
        sys.exit()
    
    preprocessor = Data_Preprocessor(raw_trades)
    clean_df = preprocessor.clean_and_parse(target_outcome = target_team)
    
    engine = Whale_Alpha_Engine(clean_df)
    engine.calculate_metrics()
    
    elite_whales = engine.get_elite_whales()
    engine.generate_signals(elite_whales)