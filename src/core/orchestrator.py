import os
import sys
import time
import logging
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'src'))

from api import polymarket 
from agents.top_traders_alpha import Data_Preprocessor, Whale_Alpha_Engine 


logger = logging.getLogger(__name__)


def run_pipeline():
    recent_trades = polymarket.get_recent_public_trades(limit=500)

    if not recent_trades:
        logger.warning("No recent trades were returned by the data API")
        return []

    trades_df = pd.DataFrame(recent_trades)
    if trades_df.empty or "conditionId" not in trades_df.columns:
        logger.warning("Recent trades payload is missing a usable conditionId column")
        return []
    
    master_signals = []

    grouped_trades = sorted(trades_df.groupby("conditionId"), key=lambda item: len(item[1]), reverse=True)

    for condition_id, group in grouped_trades:
        try:
            target_token = group["outcome"].mode().iat[0] if "outcome" in group.columns and not group["outcome"].dropna().empty else None
            market_title = group["title"].mode().iat[0] if "title" in group.columns and not group["title"].dropna().empty else None
            market_slug = group["slug"].mode().iat[0] if "slug" in group.columns and not group["slug"].dropna().empty else None

            if not target_token:
                logger.debug("Skipping condition %s because no target outcome was found", condition_id)
                continue

            expanded_trades = polymarket.get_market_trades(condition_id, target_depth=1000, page_size=1000, lookback_hours=72)
            if not expanded_trades:
                logger.debug("No expanded trades returned for condition %s", condition_id)
                continue

            preprocessor = Data_Preprocessor(expanded_trades)
            clean_df = preprocessor.clean_and_parse(target_outcome=target_token)

            if clean_df.empty:
                logger.debug("No usable trades after preprocessing for condition %s", condition_id)
                continue

            alpha_engine = Whale_Alpha_Engine(clean_df)
            alpha_engine.calculate_metrics()
            elite_whales = alpha_engine.get_elite_whales()
            signal_payload = alpha_engine.generate_signals(elite_whales)

            if signal_payload.get("whale_count", 0) > 0:
                signal_payload["market_title"] = market_title
                signal_payload["market_slug"] = market_slug
                signal_payload["condition_id"] = condition_id
                signal_payload["tracked_target"] = target_token

                master_signals.append(signal_payload)
                logger.info(
                    "Detected %s whale signals for %s",
                    signal_payload.get("whale_count", 0),
                    market_slug,
                )
            
        except Exception as e:
            logger.exception("Pipeline failed for condition %s: %s", condition_id, e)
            continue
        time.sleep(0.5)

    if master_signals:
        logger.info("Generated %s market signal payloads", len(master_signals))

    return master_signals


if __name__ == "__main__":
    run_pipeline()









