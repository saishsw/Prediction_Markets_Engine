# System Context & Coding Standards: Prediction Markets Quant Agent

## Project Overview
This project is an autonomous, multi-agent quantitative trading pipeline designed to interact with the Polymarket prediction market ecosystem. The architecture evaluates blockchain-based prediction markets, tracks high-conviction "whale" wallets, assesses dynamic order book liquidity, and will eventually execute trades programmatically.

## Architectural Philosophy
The system relies on **Modular, Blind Agents** connected by a central **Orchestrator**.
* **Isolation:** Agents (Scanner, Alpha Engine, Risk Manager) must not import or know about each other. They strictly take in raw data/dataframes and return structured Python dictionaries.
* **The Orchestrator:** Acts as a pure "conveyor belt." It does no analytical math. It handles the API requests, passes data between agents, injects contextual metadata into signals, and maintains a strict `try/except/continue` shield to prevent a single market failure from crashing the entire pipeline loop.

## Directory Structure & Agent Roles
When suggesting code or file imports, respect the absolute pathing structure (`src/` appended to `sys.path`):
* `config/`: Contains `.env` (private keys) and JSON configuration files (risk thresholds).
* `data/`: Stores append-only `.log` files and historical JSON trade snapshots.
* `src/api/`: Pluggable REST/Web3 clients (Gamma API for market discovery, CLOB API for order books/trades).
* `src/agents/`:
    * **Market Scanner (The Eye):** Hits the Gamma API. Uses dynamic quantile-based thresholding (not hardcoded numbers) to filter active, highly liquid markets.
    * **Top Traders Alpha (The Brain):** The data preprocessor and whale engine. Uses Pandas to calculate volume skew and wallet conviction. Returns a standardized JSON/dict payload.
    * **Risk Manager (The Shield - WIP):** Enforces Kelly Criterion, portfolio AUM caps, and checks live order book depth to prevent slippage.
* `src/core/orchestrator.py`: The master execution loop.

## Code Design & Anti-Patterns
When writing or refactoring code for this project, adhere to the following rules:

### 1. Data Processing (The Hybrid Sieve Pattern)
* **Vectorization First:** Use Pandas boolean masking for high-level numeric filtering (e.g., dropping low liquidity/volume markets). 
* **Standard Python for Parsing:** Only convert the surviving subset of rows into native dictionaries (`.to_dict('records')`) before running loops to unpack complex or stringified JSON fields.
* **Polymarket API Quirk:** The Gamma API often returns lists (like contract `outcomes`) as **stringified JSON arrays** (e.g., `"["Yes", "No"]"`). Do not attempt to vectorize text/list unpacking; use `json.loads()` inside a standard loop on the filtered dictionary records.

### 2. Error Handling & Execution Control
* **No Unbounded Requests:** All `requests.get()` or `requests.post()` calls must include a strict `timeout` parameter (e.g., `timeout=10`).
* **Graceful Degradation:** Agents should return empty lists `[]` or base-case dictionaries on failure, rather than raising fatal tracebacks, allowing the Orchestrator's loop to `continue`.
* **Rate Limiting:** Always respect API rate limits by injecting `time.sleep()` within massive iteration loops.

### 3. Logging over Printing
* Do not use `print()` in production execution paths.
* Use the standard Python `logging` module. 
* Different severity levels (`info` for lifecycle, `warning` for skipped/empty markets, `critical` for network/wallet drops) must be respected so they properly route to `data/logs/`.

### 4. Path Resolution
* Always resolve paths dynamically using `os.path.dirname(os.path.abspath(__file__))` and walk up the tree to locate `project_root`. Do not rely on relative execution paths.

## Profitability, Risk & Operational Guidelines
These additions capture practical rules and checks the agents and Orchestrator should follow to increase the chance of being profitable while remaining safe in production.

- **Profitability Objective:** Focus on high conviction, low-slippage opportunities. Prioritize markets with both high liquidity and concentrated directional activity from elite wallets. Avoid chasing noisy low-volume trades.

- **Sizing & Execution:** implement a configurable sizing policy (see `config/`): **max_position_per_market_pct**, **max_exposure_total_pct**, and **kelly_fraction**. Default to conservative fractions (e.g., 0.5 of Kelly) until live performance is validated in a paper trading mode.

- **Slippage & Fees:** Always subtract estimated slippage and trading fees when evaluating expected value of a trade. Use live orderbook depth (`api.polymarket.get_live_orderbook`) to compute implied price impact for `target_size` before suggesting an execution.

- **Minimum Quality Gates:** before converting a `signal` to an executable order, check:
    - market liquidity above `liquidity_threshold` (quantile-based),
    - orderbook depth supports `target_size` within acceptable price range,
    - time-since-last-whale-trade < `max_signal_age_seconds` (stale signals are less predictive).

- **Paper Trading & Backtests:** never enable live execution without a robust backtest and a live paper-trading period. Implement a reproducible backtest harness using snapshot JSONs in `data/historical_trades/` and log outcomes to `data/logs/`.

- **Risk Controls (must be enforced in `Risk Manager`):**
    - hard `max_drawdown_pct` and daily loss limits,
    - per-wallet trade limits to avoid copying market manipulators blindly,
    - circuit breaker for API failures or anomalous volatility.

- **Performance Metrics to Monitor:** track and log `win_rate`, `profit_factor`, `average_return_per_trade`, `max_drawdown`, `Sharpe_ratio` (use daily returns). Emit metrics every run to `data/logs/metrics.log`.

- **Data Hygiene & Replayability:** persist raw API responses (append-only) with timestamps and offsets so backtests can exactly replay the environment that produced a signal. Avoid dropping fields even if unused.

- **Deployment & Rate Limits:** use exponential backoff on rate-limited endpoints. Keep configurable `requests.timeout` and `rate_limit_sleep` values in `config/`.

- **Security & Secrets:** keep API keys and wallet private keys out of repo. Use environment variables or a secrets manager; ensure the Orchestrator will refuse to run live executions without an explicit `--live` flag and presence of a signed configuration permit.

## Practical Implementation Notes (quick checklist)
- **Start with paper mode:** set `LIVE=false` in env and route executions to a dry-run executor in `src/api/execution.py`.
- **Unit tests & Backtests:** add tests for `Data_Preprocessor`, `Whale_Alpha_Engine`, and `Market_Scanner` focusing on edge cases (empty payloads, stringified JSON fields, malformed trades).
- **Instrumentation:** integrate basic metric emission (stdout JSON or file logs) for each pipeline run: inputs, signals, execution attempt, and final P&L impact estimate.

## Next Steps (recommended)
- Add a `paper_executor` implementation to `src/api/execution.py` and wire the Orchestrator to toggle between paper/live.
- Implement the `Risk Manager` (currently WIP) to enforce the checks above before any execution is passed to the executor.
- Create a reproducible `backtest.py` that consumes files from `data/historical_trades/` and validates the alpha engine's historical predictive power.

---
End of additions.
