import pandas as pd
import asyncio
import aiohttp
import certifi
import ssl
import socket
import threading
from data_fetcher import fetch_top_symbols, fetch_ohlcv
from analyzer import analyze_squeeze_and_rsi

async def process_symbol(session, sem, sym_data, timeframe, results, progress_info):
    symbol = sym_data['symbol']
    
    async with sem:
        df, _ = await fetch_ohlcv(session, symbol, timeframe, limit=150)
        
        if df is not None:
            analyzed = analyze_squeeze_and_rsi(df)
            
            if analyzed is not None and not analyzed.empty:
                latest = analyzed.iloc[-1]
                
                if timeframe == "15m":
                    sqz_limit, high_limit = 3.0, 8.0
                elif timeframe == "1H":
                    sqz_limit, high_limit = 5.0, 12.0
                elif timeframe == "4H":
                    sqz_limit, high_limit = 8.0, 18.0
                else:
                    sqz_limit, high_limit = 12.0, 30.0

                signal = "Neutral"
                if latest['bandwidth'] < sqz_limit:
                    if latest['rsi'] > 60:
                        signal = "Bullish Breakout"
                    elif latest['rsi'] < 40:
                        signal = "Bearish Breakout"
                    else:
                        signal = "Squeezing"
                elif latest['bandwidth'] > high_limit:
                    signal = "High Volatility"
                
                current_price = float(latest['close'])
                current_vol = float(latest['volume'])
                rsi = float(latest.get('RSI', latest.get('rsi', 50)))
                bandwidth = float(latest.get('bandwidth', latest.get('Bandwidth', 0)))

                score = (100 - bandwidth) * 2 + (rsi if rsi > 50 else (100 - rsi))
                tier = 4  # Mặc định tất cả đều là Phương án A (Cơ sở để chèn cho đủ 10 con)

                # Mô phỏng MA để check xu hướng lớn và Volume
                if len(df) >= 100:
                    vol_ma20 = df['volume'].rolling(20).mean().iloc[-2] # Trung bình Vol 20 nến trước
                    sma100 = df['close'].rolling(100).mean().iloc[-1]   # Đại diện cho xu hướng 4H
                    sma4 = df['close'].rolling(4).mean().iloc[-1]       # Đại diện cho xu hướng 15m
            
                    # Phân loại xu hướng rõ ràng
                    is_bullish_trend = current_price > sma100
                    is_bearish_trend = current_price < sma100
                    
                    # PHƯƠNG ÁN C (Tier 3): Thuận xu hướng 4H (Long trên SMA, Short dưới SMA)
                    if (signal == "Bullish Breakout" and is_bullish_trend) or (signal == "Bearish Breakout" and is_bearish_trend):
                        tier = 3
                
                    # PHƯƠNG ÁN B (Tier 2): Breakout + Volume Cá Mập (Đột biến > 2.5 lần)
                    if "Breakout" in signal and current_vol > (vol_ma20 * 2.5):
                        tier = 2
                
                    # ĐỈNH CAO (Tier 1): Đồng thuận 3 khung + Vol đột biến (Thuận trend cả 2 đường SMA)
                    if tier == 2:
                        if (signal == "Bullish Breakout" and is_bullish_trend and current_price > sma4) or \
                           (signal == "Bearish Breakout" and is_bearish_trend and current_price < sma4):
                            tier = 1

                results.append({
                    'Symbol': symbol,
                    'Price': round(latest['close'], 4),
                    'Change': sym_data['change'],
                    'Volume': sym_data['vol'],
                    'Bandwidth': round(latest['bandwidth'], 2),
                    'RSI': round(latest['rsi'], 2),
                    'Signal': signal,
                    'Tier': tier,
                    'Score': score
                })
        
        progress_info['current'] += 1
        if progress_info['callback']:
            progress_info['callback'](progress_info['current'], progress_info['total'], symbol)

async def run_screener_async(top_n=50, timeframe="1H", progress_callback=None):
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    resolver = aiohttp.ThreadedResolver()
    connector = aiohttp.TCPConnector(ssl=ssl_context, resolver=resolver, family=socket.AF_INET)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        symbols_info = await fetch_top_symbols(session, limit=top_n)
        
        if not symbols_info:
            return pd.DataFrame()

        results = []
        progress_info = {'current': 0, 'total': len(symbols_info), 'callback': progress_callback}
        sem = asyncio.Semaphore(15)
        
        tasks = [process_symbol(session, sem, sym_data, timeframe, results, progress_info) for sym_data in symbols_info]
        await asyncio.gather(*tasks)

        result_df = pd.DataFrame(results)
        
        if not result_df.empty:
            result_df = result_df.sort_values(by='Bandwidth').reset_index(drop=True)

            # Lọc VIP: Chỉ lấy những con đạt Tier 1, 2, hoặc 3 (Bỏ qua Tier 4)
            if not result_df.empty:
                result_df = result_df.sort_values(by='Bandwidth').reset_index(drop=True)
        return result_df
    
def send_telegram_alert(message):
    import requests
    import json
    
    try:
        with open("config.json", "r") as f:
            cfg = json.load(f)
            BOT_TOKEN = cfg.get("tg_token", "")
            CHAT_ID = cfg.get("tg_chat_id", "")
    except:
        return # Nếu không có file config thì thôi khỏi bắn
        
    if not BOT_TOKEN or not CHAT_ID:
        return # Nếu khách nhập chuỗi rỗng thì cũng bỏ qua
        
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass