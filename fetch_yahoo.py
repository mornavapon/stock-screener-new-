import json
import yfinance as yf
import pandas as pd
from datetime import datetime

# กำหนดรายชื่อหุ้น Universe ทั้งหมด (รวมไทย SET100 บางส่วน/หลัก, US, จีน, ฮ่องกง)
tickers = [
    # หุ้นไทยยอดนิยม / SET100 ตัวหลัก
    "PTT.BK", "AOT.BK", "DELTA.BK", "GULF.BK", "ADVANC.BK", "PTTEP.BK", "BDMS.BK", "CPALL.BK", "SCB.BK", "BBL.BK",
    "KBANK.BK", "KTB.BK", "TTB.BK", "CPN.BK", "CRC.BK", "COM7.BK", "MINT.BK", "BEM.BK", "BTS.BK", "LH.BK",
    "QH.BK", "SPALI.BK", "AP.BK", "AMATA.BK", "WHA.BK", "IVL.BK", "SCC.BK", "SCGP.BK", "TOP.BK", "BCP.BK",
    "PTTGC.BK", "EA.BK", "GPSC.BK", "BGRIM.BK", "TRUE.BK", "INTUCH.BK", "COM7.BK", "HMPRO.BK", "GLOBAL.BK", "BJC.BK",
    
    # หุ้นสหรัฐฯ (US Tech & Blue Chips)
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX", "AMD", "INTC",
    "QCOM", "AVGO", "TXN", "MU", "AMAT", "LRCX", "PYPL", "SHOP", "ASML", "TSM",
    "JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "AXP", "DIS",
    
    # หุ้นจีน / ฮ่องกงที่คุณสนใจ และ Tech 50 ฮ่องกง
    "0700.HK", "9988.HK", "1810.HK", "300750.SZ", "2318.HK", "9888.HK", "0981.HK", 
    "3690.HK", "002027.SZ", "002594.SZ", "600519.SS", "0388.HK", "1024.HK", "2015.HK", "9618.HK"
]

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
        dividend_yield = info.get('dividendYield', 0)
        if dividend_yield:
            dividend_yield = dividend_yield * 100 # แปลงเป็นเปอร์เซ็นต์
        else:
            dividend_yield = 0
            
        sector = info.get('sector', 'Other')
        currency = info.get('currency', 'USD')

        data_list.append({
            "ticker": ticker,
            "name": name,
            "price": price if price else 0,
            "marketCap": market_cap if market_cap else 0,
            "pe": pe if pe else 0,
            "pb": pb if pb else 0,
            "roe": roe * 100 if roe else 0, # แปลงเป็น %
            "dividendYield": dividend_yield,
            "sector": sector,
            "currency": currency
        })
        print(f"สำเร็จ: {ticker}")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการดึงข้อมูล {ticker}: {e}")

# บันทึกเป็นไฟล์ JSON กลาง
output = {
    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "stocks": data_list
}

with open("stocks_data.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("สร้างไฟล์ stocks_data.json เรียบร้อยแล้ว!")
