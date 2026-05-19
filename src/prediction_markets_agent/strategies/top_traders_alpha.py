import pandas as pd
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







if __name__ == "__main__":
    condition_id = polymarket.get_market_condition_id("ky-04-republican-primary-winner")

    print(condition_id)

    top_trades = polymarket.get_market_trades(condition_id)

    print(top_trades)


## Three directional markets 1. intensity 2. consistency 3. directional conviction


