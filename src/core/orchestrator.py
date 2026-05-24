import os
import sys
import time
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'src'))

from api import polymarket 
from agents.market_scanner import Market_Scanner
from agents.top_traders_alpha import Data_Preprocessor, Whale_Alpha_Engine 


logger = logging.getLogger(__name__)


def run_pipeline():
    scanner = Market_Scanner()
    top_markets = scanner.get_top_markets()

    if not top_markets:
        logger.warning("No qualified markets were returned by the scanner")
        return []
    
    master_signals = []

    for market in top_markets:
        try:
            target_token = market.get("outcome") or (market.get("outcomes") or [None])[0]
            condition_id = market.get("condition_id")

            if not condition_id or not target_token:
                logger.debug(
                    "Skipping market with missing condition id or target outcome: %s",
                    market.get("market_slug"),
                )
                continue

            raw_trades = polymarket.get_market_trades(condition_id, target_depth=500)

            if not raw_trades:
                logger.debug("No trades returned for market %s", market.get("market_slug"))
                continue

            preprocessor = Data_Preprocessor(raw_trades)
            clean_df = preprocessor.clean_and_parse(target_outcome=target_token)

            if clean_df.empty:
                logger.debug("No usable trades after preprocessing for market %s", market.get("market_slug"))
                continue

            alpha_engine = Whale_Alpha_Engine(clean_df)
            alpha_engine.calculate_metrics()
            elite_whales = alpha_engine.get_elite_whales()
            signal_payload = alpha_engine.generate_signals(elite_whales)

            if signal_payload.get("whale_count", 0) > 0:
                signal_payload["market_title"] = market.get("title")
                signal_payload["market_slug"] = market.get("market_slug")
                signal_payload["tracked_target"] = target_token

                master_signals.append(signal_payload)
                logger.info(
                    "Detected %s whale signals for %s",
                    signal_payload.get("whale_count", 0),
                    market.get("market_slug"),
                )
            
        except Exception as e:
            logger.exception("Pipeline failed for market %s: %s", market.get("market_slug"), e)
            continue
        time.sleep(0.5)

    if master_signals:
        logger.info("Generated %s market signal payloads", len(master_signals))

    return master_signals


if __name__ == "__main__":
    run_pipeline()









