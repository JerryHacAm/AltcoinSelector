import aiohttp
import asyncio
import pandas as pd

STABLECOINS = {"USDC", "FDUSD", "DAI", "TUSD", "USDE", "PYUSD", "EURT", "BUSD", "USD", "USDG", "RLUSD"}

async def fetch_top_symbols(session, limit=100):
    url = "https://www.okx.com/api/v5/market/tickers"
    params = {"instType": "SPOT"}
    
    try:
        async with session.get(url, params=params, timeout=10) as response:
            response.raise_for_status()
            data = await response.json()
            
            if data.get('code') != '0':
                return []
                
            tickers = data['data']
            usdt_tickers = []
            
            for t in tickers:
                inst_id = t['instId']
                if inst_id.endswith('-USDT'):
                    base_coin = inst_id.split('-')[0]
                    if base_coin not in STABLECOINS:
                        usdt_tickers.append(t)
                        
            usdt_tickers.sort(key=lambda x: float(x['volCcy24h']), reverse=True)
            
            symbols_info = []
            for t in usdt_tickers[:limit]:
                open_price = float(t['sodUtc0'])
                last_price = float(t['last'])
                change = ((last_price - open_price) / open_price * 100) if open_price > 0 else 0
                
                symbols_info.append({
                    'symbol': t['instId'],
                    'vol': float(t['volCcy24h']),
                    'change': change
                })
            return symbols_info
            
    except Exception as e:
        print(f"[ERROR - TOP SYMBOLS]: {e}")
        return []

async def fetch_ohlcv(session, symbol="BTC-USDT", timeframe="1H", limit=100):
    url = "https://www.okx.com/api/v5/market/candles"
    params = {
        "instId": symbol,
        "bar": timeframe,
        "limit": limit
    }
    
    max_retries = 5
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            async with session.get(url, params=params, timeout=10) as response:
                if response.status == 429:
                    await asyncio.sleep(base_delay * (2 ** attempt))
                    continue
                    
                response.raise_for_status() 
                data = await response.json()
                
                if data.get('code') != '0':
                    return None, symbol
                    
                columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm']
                df = pd.DataFrame(data['data'], columns=columns)
                
                df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                df = df.astype(float)
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df = df.sort_values('timestamp').reset_index(drop=True)
                
                return df, symbol

        except Exception as e:
            if "429" in str(e) or "Too Many Requests" in str(e):
                await asyncio.sleep(base_delay * (2 ** attempt))
                continue
            else:
                print(f"[ERROR - OHLCV] {symbol}: {e}")
                return None, symbol
                
    print(f"[WARNING] Skipping {symbol} after {max_retries} attempts.")
    return None, symbol