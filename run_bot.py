import logging
import json

from src.core.orchestrator import run_pipeline


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

if __name__ == "__main__":
    logging.getLogger(__name__).info("Booting quant system integration test")
    master_signals = run_pipeline()

    if master_signals:
        logging.getLogger(__name__).info(json.dumps(master_signals, indent=2))
    else:
        logging.getLogger(__name__).warning("No master_signals were generated")