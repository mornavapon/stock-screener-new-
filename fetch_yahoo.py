import json
import time
import yfinance as yf
import pandas as pd
from datetime import datetime

tickers = [
    # หุ้นไทยยอดนิยม / SET100 ตัวหลัก
    "PTT.BK", "AOT.BK", "DELTA.BK", "GULF.BK", "ADVANC.BK", "PTTEP.BK", "BDMS.BK", "CPALL.BK", "SCB.BK", "BBL.BK",
    "KBANK.BK", "KTB.BK", "TTB.BK", "CPN.BK", "CRC.BK", "COM7.BK", "MINT.BK", "BEM.BK", "BTS.BK", "LH.BK",
    "QH.BK", "SPALI.BK", "AP.BK", "AMATA.BK", "WHA.BK", "IVL.BK", "SCC.BK", "SCGP.BK", "TOP.BK", "BCP.BK",
    "PTTGC.BK", "EA.BK", "GPSC.BK", "BGRIM.BK", "TRUE.BK", "INTUCH.BK", "HMPRO.BK", "GLOBAL.BK", "BJC.BK",

    # หุ้นสหรัฐฯ (US Tech & Blue Chips) - รายการเดิม
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX", "AMD", "INTC",
    "QCOM", "AVGO", "TXN", "MU", "AMAT", "LRCX", "PYPL", "SHOP", "ASML", "TSM",
    "JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "AXP", "DIS",

    # หุ้นสหรัฐฯ - เพิ่มใหม่ (ตัดตัวที่ซ้ำกับด้านบนออกแล้ว)
    "KO", "ARM", "GOOG", "SPCX", "LITE", "COHR",
    "HPE", "T", "MRNA", "OXY", "VZ", "TMUS",
    "CSCO", "TGT", "WMT", "PLTR", "PG",
    "PEP", "COIN", "JNJ", "MMM",
    "UNH", "MCD", "AMGN", "FDX", "HD", "BRK-B", "CAT", "COST", "BLK", "BRK-A",
    "UBI.PA", "U", "RBLX", "SE", "TTWO",
    # กลุ่มอาวุธ / ป้องกันประเทศ
    "XAR", "PPA", "ITA", "RTX", "GD", "LHX", "LMT", "NOC",
    # กลุ่มอวกาศ
    "RKLB", "VSAT", "PL", "SPCE", "LUNR", "ASTS",
    "F", "MANU", "NKE", "UBER", "MRVL", "ORCL", "SNOW", "CRM", "GM",
    "SBUX", "XOM", "CVX", "PM", "HIMS", "IBM", "VRSN", "ADBE", "WDC", "CRWD",
    "STX", "SNDK", "YUM", "NDAQ", "HOOD", "BULL", "CME", "RDDT", "BNO",
    "VCX", "TEM", "MSTR", "VFS",

    # หุ้นจีน / ฮ่องกงที่คุณสนใจ
    "0700.HK", "9988.HK", "1810.HK", "300750.SZ", "2318.HK", "9888.HK", "0981.HK",
    "3690.HK", "002027.SZ", "002594.SZ", "600519.SS", "0388.HK", "1024.HK", "2015.HK", "9618.HK"
]

# กันรหัสซ้ำอัตโนมัติ (ไม่สนตัวพิมพ์เล็ก/ใหญ่) โดยคงลำดับเดิมไว้
_seen = set()
_unique = []
for _t in tickers:
    _key = _t.strip().upper()
    if _key in _seen:
        print(f"ข้ามรหัสที่ซ้ำ: {_t}")
        continue
    _seen.add(_key)
    _unique.append(_t.strip())
tickers = _unique

print(f"กำลังดึงข้อมูลหุ้นทั้งหมด {len(tickers)} ตัว...")

data_list = []

for ticker in tickers:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        name = info.get('longName', info.get('shortName', ticker))
        price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        market_cap = info.get('marketCap', 0)
        pe = info.get('trailingPE', 0)
        pb = info.get('priceToBook', 0)
        roe = info.get('returnOnEquity', 0)
        # yfinance รุ่นใหม่ส่ง dividendYield มาเป็น "เปอร์เซ็นต์" อยู่แล้ว (เช่น 0.31 = 0.31%)
        # จึงไม่คูณ 100 อีก; ถ้ามี dividendRate กับราคา ให้คำนวณเองเพื่อความแม่นยำ
        dividend_rate = info.get('dividendRate') or info.get('trailingAnnualDividendRate')
        if dividend_rate and price:
            dividend_yield = dividend_rate / price * 100
        else:
            dividend_yield = info.get('dividendYield', 0) or 0

        de = info.get('debtToEquity', 0)
        gpm = info.get('grossMargins', 0)
        npm = info.get('profitMargins', 0)

        data_list.append({
            "ticker": ticker,
            "name": name,
            "price": price if price else 0,
            "marketCap": market_cap if market_cap else 0,
            "pe": pe if pe else 0,
            "pb": pb if pb else 0,
            "roe": roe * 100 if roe else 0,
            "dividendYield": dividend_yield,
            "de": de / 100 if de else 0, # Yahoo ส่งมาเป็น % บางทีต้องหาร 100 หรือใช้ตามค่าจริง
            "gpm": gpm * 100 if gpm else 0,
            "npm": npm * 100 if npm else 0,
            "currency": info.get('currency', 'USD')
        })
        print(f"สำเร็จ: {ticker}")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการดึงข้อมูล {ticker}: {e}")
    time.sleep(0.3)  # เว้นจังหวะเล็กน้อย ลดโอกาสโดน Yahoo จำกัดการเรียก

output = {
    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "stocks": data_list
}

with open("stocks_data.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("สร้างไฟล์ stocks_data.json เรียบร้อยแล้ว!")
