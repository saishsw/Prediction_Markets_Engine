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
