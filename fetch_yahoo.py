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

    # SET100 ครึ่งปีหลัง 2569 (มีผล 1 ก.ค. - 31 ธ.ค. 2569) - ตัวที่เพิ่มเข้ามาให้ครบ 100 ตัว
    "AAV.BK", "AEONTS.BK", "AURA.BK", "AWC.BK", "BA.BK", "BAM.BK", "BANPU.BK", "BCH.BK", "BCPG.BK", "BH.BK",
    "BLA.BK", "BTG.BK", "CBG.BK", "CCET.BK", "CENTEL.BK", "CHG.BK", "CK.BK", "CPF.BK", "DOHOME.BK", "EGCO.BK",
    "ERW.BK", "GFPT.BK", "GUNKUL.BK", "HANA.BK", "ICHI.BK", "IRPC.BK", "JMT.BK", "JTS.BK", "KCE.BK", "KKP.BK",
    "KTC.BK", "M.BK", "MEGA.BK", "MOSHI.BK", "MRDIYT.BK", "MTC.BK", "OR.BK", "OSP.BK", "PLANB.BK", "PR9.BK",
    "PRM.BK", "PTG.BK", "RATCH.BK", "RCL.BK", "SAWAD.BK", "SIRI.BK", "SPRC.BK", "STA.BK", "STECON.BK", "STGT.BK",
    "TASCO.BK", "TCAP.BK", "TFG.BK", "THAI.BK", "THCOM.BK", "TIDLOR.BK", "TISCO.BK", "TLI.BK", "TOA.BK", "TU.BK",
    "VGI.BK", "WHAUP.BK",

    # หุ้นไทยที่ใช้ใน My Watchlist (เพิ่มจากรายการที่เลือก)
    "AXTRART.BK", "CPAXT.BK", "DRT.BK", "DCC.BK", "IMPACT.BK", "KYE.BK", "STPI.BK", "TVO.BK", "LTMH.BK", "ADVICE.BK",
    "SYNEX.BK", "SIS.BK", "ASP.BK", "TFMAMA.BK", "JMART.BK", "VIH.BK", "BAFS.BK", "PSH.BK", "JUBILE.BK", "AIT.BK",
    "PDG.BK", "spvi.bk", "it.bk", "cpw.bk",

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
    # (เพิ่มใหม่) หุ้นจีน/ฮ่องกง และหุ้นจีนที่จดทะเบียนในสหรัฐ
    "688981.SS", "2809.HK", "PDD", "1211.HK", "688825.SS", "600941.SS", "9999.HK", "002352.SZ", "0694.HK", "BILI",
    "0941.HK", "1177.HK", "600276.SS", "3988.HK", "601318.SS",
    "0700.HK", "9988.HK", "1810.HK", "300750.SZ", "2318.HK", "9888.HK", "0981.HK", "3750.HK",
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

def safe_num(v):
    """แปลงค่าจาก Yahoo ให้เป็นตัวเลขที่ปลอดภัย (ถ้าเป็น None / 'Infinity' / NaN จะได้ 0)
    กันไม่ให้ไฟล์ JSON มีค่าที่เว็บแอปอ่านไม่ได้"""
    try:
        x = float(v)
    except (TypeError, ValueError):
        return 0
    if x != x or x in (float('inf'), float('-inf')):
        return 0
    return x


data_list = []

for ticker in tickers:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        name = info.get('longName') or info.get('shortName') or ticker
        price = safe_num(info.get('currentPrice') or info.get('regularMarketPrice'))
        market_cap = safe_num(info.get('marketCap'))
        pe = safe_num(info.get('trailingPE'))
        forward_pe = safe_num(info.get('forwardPE'))
        # PEG: Yahoo บางตัวใช้ชื่อ pegRatio บางตัวใช้ trailingPegRatio (บางตัวไม่มีข้อมูลเลย จะได้ 0)
        peg = safe_num(info.get('pegRatio')) or safe_num(info.get('trailingPegRatio'))
        pb = safe_num(info.get('priceToBook'))
        roe = safe_num(info.get('returnOnEquity'))
        high_52w = safe_num(info.get('fiftyTwoWeekHigh'))
        low_52w = safe_num(info.get('fiftyTwoWeekLow'))
        # yfinance รุ่นใหม่ส่ง dividendYield มาเป็น "เปอร์เซ็นต์" อยู่แล้ว (เช่น 0.31 = 0.31%)
        # จึงไม่คูณ 100 อีก; ถ้ามี dividendRate กับราคา ให้คำนวณเองเพื่อความแม่นยำ
        dividend_rate = safe_num(info.get('dividendRate')) or safe_num(info.get('trailingAnnualDividendRate'))
        if dividend_rate and price:
            dividend_yield = dividend_rate / price * 100
        else:
            dividend_yield = safe_num(info.get('dividendYield'))

        de = safe_num(info.get('debtToEquity'))
        gpm = safe_num(info.get('grossMargins'))
        npm = safe_num(info.get('profitMargins'))

        data_list.append({
            "ticker": ticker,
            "name": name,
            "price": price,
            "marketCap": market_cap,
            "pe": pe,
            "forwardPE": forward_pe,
            "pegRatio": peg,
            "pb": pb,
            "roe": roe * 100 if roe else 0,
            "dividendYield": dividend_yield,
            "de": de / 100 if de else 0, # Yahoo ส่งมาเป็น % บางทีต้องหาร 100 หรือใช้ตามค่าจริง
            "gpm": gpm * 100 if gpm else 0,
            "npm": npm * 100 if npm else 0,
            "fiftyTwoWeekHigh": high_52w,
            "fiftyTwoWeekLow": low_52w,
            "currency": info.get('currency') or 'USD'
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
