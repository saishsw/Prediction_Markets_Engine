import logging

from src.core.orchestrator import run_pipeline


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

if __name__ == "__main__":
    logging.getLogger(__name__).info("Booting quant system integration test")
    run_pipeline()