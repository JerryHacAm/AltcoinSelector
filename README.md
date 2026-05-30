# Algorithmic Volatility Scanner & Breakout Terminal

An asynchronous, end-to-end quantitative trading terminal written in Python. It continuously monitors and filters cryptocurrency market structures across multiple timeframes, identifying high-probability breakout setups using mathematical volatility compression models.

## 📊 Core Algorithmic Logic
The system eliminates emotional bias by relying purely on statistical and mathematical indicators:
* **Volatility Compression (Squeeze):** Utilizes a **50-candle lookback window** to evaluate the bandwidth of Bollinger Bands against historical data, detecting periods of extreme asset consolidation.
* **Volume Confirmation:** Filters out false breakouts (Fakeouts) by requiring the breakout candle's volume to significantly exceed the moving average threshold.
* **Multi-Tier Grading Engine:** Automatically ranks market structures into 3 distinct Tiers, allowing traders to separate high-probability setups (Tier 1) from market noise (Tier 3/4).

## ⚡ Technical Highlights
* **Asynchronous Architecture:** Implemented Python's `asyncio` and `aiohttp` to manage concurrent API requests, minimizing latency when scanning hundreds of trading pairs simultaneously.
* **API Rate-Limit Defensive Design:** Engineered utilizing a semaphore queue system to handle exchange API limits gracefully and avoid IP bans.
* **Production Packaging:** Compiled the entire Python data pipeline into a standalone executable (`.exe`) configuration to eliminate local dependency issues for end-users.

## 🛠️ Tech Stack & Libraries
* **Language:** Python 3.10+
* **Data Science:** Pandas, NumPy
* **Financial Data Pipeline:** CCXT (CryptoCurrency eXchange Trading Library)
* **Concurrence:** Asyncio, Aiohttp

## 🚀 Getting Started

### Prerequisites
Make sure you have Python installed, then clone the repository:
```bash
git clone https://github.com/JerryHacAm/AltcoinSelector.git
cd AltcoinSelector
