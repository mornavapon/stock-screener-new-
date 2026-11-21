"""
check_alerts.py — แจ้งเตือนหุ้นผ่าน ntfy (รันต่อจาก "Update Stock Data" อัตโนมัติ)

อ่านข้อมูลจาก stocks_data.json (หุ้นทั้งหมดใน fetch_yahoo.py) แล้วเตือน 5 เงื่อนไข:
  1) P/E <= PE_MAX
  2) ราคาแตะ/ใกล้จุดสูงสุด 52 สัปดาห์
  3) ราคาแตะ/ใกล้จุดต่ำสุด 52 สัปดาห์
  4) Golden Cross : ราคาเคยอยู่ใต้ EMA200 แล้วข้ามขึ้นไปอยู่เหนือ
  5) Dead Cross   : ราคาเคยอยู่เหนือ EMA200 แล้วหลุดลงมาอยู่ใต้ (หรือเท่ากับ)

หลักการ: เตือน "ตอนที่เงื่อนไขเพิ่งเกิดขึ้น" (เปลี่ยนจากไม่ใช่ -> ใช่) โดยจำสถานะเมื่อวานไว้ใน alerts_state.json
ยกเว้น 52W สูงสุด/ต่ำสุด ที่เตือนซ้ำทุกวันตราบใดที่ยังแตะอยู่ (ปรับที่ REPEAT_52W)

ตัวแปรสภาพแวดล้อม:
  NTFY_TOPIC   (บังคับ)  ชื่อช่อง ntfy  — ตั้งใน GitHub Secret ชื่อ NTFY_TOPIC_SCREENER
  ALERT_TEST   = "true"  ส่งข้อความทดสอบ 1 ฉบับ (ไม่บันทึกสถานะ)
  DRY_RUN      = "1"     ไม่ส่งจริง แค่พิมพ์ข้อความออกหน้าจอ (ใช้ทดสอบในเครื่อง)
"""
import json
import os
import sys
from datetime import datetime

import requests

# ====== ตั้งค่า (แก้ตัวเลขตรงนี้ได้) ======
PE_MAX = 10.0          # เตือนเมื่อ P/E ต่ำกว่าหรือเท่ากับค่านี้ (และมากกว่า 0)
NEAR_PCT = 0.5         # "แตะ" จุดสูงสุด/ต่ำสุด 52W = ห่างไม่เกินกี่ % (ราคาปิดแทบไม่เท่ากับจุดสูงสุดระหว่างวันพอดี)
REPEAT_52W = True      # True = แตะสูงสุด/ต่ำสุด 52W แล้วเตือนซ้ำทุกวันที่ยังแตะอยู่ (กรณีขึ้น/ลงแรงต่อเนื่อง) / False = เตือนเฉพาะวันแรก
MAX_NOTIFS = 12        # ส่งแยกต่อหุ้นไม่เกินกี่ฉบับต่อรอบ ที่เหลือรวมเป็นฉบับสรุป
APP_URL = "https://mornavapon.github.io/stock-screener-new-/"
NTFY_URL = "https://ntfy.sh/"
DATA_FILE = "stocks_data.json"
STATE_FILE = "alerts_state.json"
# ==========================================


def tv_symbol(t):
    """รหัสสำหรับ TradingView (เหมือนที่ใช้ในเว็บแอป)"""
    u = t.upper()
    if u.endswith(".BK"): return "SET:" + u[:-3]
    if u.endswith(".HK"): return "HKEX:" + str(int(u[:-3]))
    if u.endswith(".SZ"): return "SZSE:" + u[:-3]
    if u.endswith(".SS"): return "SSE:" + u[:-3]
    if u.endswith(".PA"): return "EURONEXT:" + u[:-3]
    return u.replace("-", ".")


def tv_url(t):
    from urllib.parse import quote
    return "https://www.tradingview.com/chart/?symbol=" + quote(tv_symbol(t), safe="")


def num(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return 0.0
    return x if x == x and x not in (float("inf"), float("-inf")) else 0.0


def evaluate(s):
    """คืนสถานะของแต่ละเงื่อนไข: True / False / None (None = ไม่มีข้อมูล ให้คงสถานะเดิม)"""
    price, pe = num(s.get("price")), num(s.get("pe"))
    hi, lo, ema = num(s.get("fiftyTwoWeekHigh")), num(s.get("fiftyTwoWeekLow")), num(s.get("ema200"))
    return {
        "pe_low": (0 < pe <= PE_MAX) if pe > 0 else None,
        "near_high": (price >= hi * (1 - NEAR_PCT / 100)) if (price > 0 and hi > 0) else None,
        "near_low": (price <= lo * (1 + NEAR_PCT / 100)) if (price > 0 and lo > 0) else None,
        "above_ema": (price > ema) if (price > 0 and ema > 0) else None,
    }


def f2(v):
    return f"{v:,.2f}"


def build_lines(s, events):
    price, hi, lo, ema = num(s.get("price")), num(s.get("fiftyTwoWeekHigh")), num(s.get("fiftyTwoWeekLow")), num(s.get("ema200"))
    lines = []
    for e in events:
        if e == "pe_low":
            lines.append(f"💰 P/E ต่ำ: {f2(num(s.get('pe')))} (≤ {PE_MAX:g})")
        elif e == "near_high":
            lines.append(f"🚀 ราคาแตะจุดสูงสุด 52 สัปดาห์: {f2(hi)} (ราคาห่าง {(price - hi) / hi * 100:+.1f}%)")
        elif e == "near_low":
            lines.append(f"🔻 ราคาแตะจุดต่ำสุด 52 สัปดาห์: {f2(lo)} (ราคาสูงกว่า {(price - lo) / lo * 100:+.1f}%)")
        elif e == "golden":
            lines.append(f"🟢 Golden Cross: ราคาข้ามขึ้นเหนือ EMA200 ({f2(ema)})")
        elif e == "dead":
            lines.append(f"🔴 Dead Cross: ราคาหลุดลงใต้ EMA200 ({f2(ema)})")
    return lines


def title_for(ticker, events):
    names = {"pe_low": "P/E ต่ำ", "near_high": "แตะสูงสุด 52W", "near_low": "แตะต่ำสุด 52W",
             "golden": "Golden Cross", "dead": "Dead Cross"}
    emoji = {"pe_low": "💰", "near_high": "🚀", "near_low": "🔻", "golden": "🟢", "dead": "🔴"}
    if len(events) == 1:
        return f"{emoji[events[0]]} {ticker} — {names[events[0]]}"
    return f"🔔 {ticker} — {len(events)} สัญญาณ"


def send(topic, title, message, with_links_for=None, priority=3):
    body = {"topic": topic, "title": title, "message": message, "priority": priority, "click": APP_URL}
    actions = []
    if with_links_for:
        actions.append({"action": "view", "label": "📊 ดูกราฟ TradingView", "url": tv_url(with_links_for), "clear": False})
    actions.append({"action": "view", "label": "📱 เปิดเว็บแอป", "url": APP_URL, "clear": False})
    body["actions"] = actions
    if os.environ.get("DRY_RUN") == "1":
        print("---- [DRY RUN] ----")
        print(json.dumps(body, ensure_ascii=False, indent=2))
        return True
    try:
        r = requests.post(NTFY_URL, json=body, timeout=30)
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"ส่ง ntfy ไม่สำเร็จ ({title}): {e}")
        return False


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def main():
    topic = os.environ.get("NTFY_TOPIC", "").strip()
    if not topic and os.environ.get("DRY_RUN") != "1":
        print("ไม่พบ NTFY_TOPIC — ต้องตั้ง Secret ชื่อ NTFY_TOPIC_SCREENER ในหน้า Settings ของ repo")
        sys.exit(1)

    data = load_json(DATA_FILE, None)
    stocks = (data or {}).get("stocks") or []
    if not stocks:
        print("ไม่พบข้อมูลใน stocks_data.json — ข้ามการตรวจ")
        sys.exit(0)

    now = {s["ticker"]: evaluate(s) for s in stocks if s.get("ticker")}
    by_ticker = {s["ticker"]: s for s in stocks if s.get("ticker")}

    # ---------- โหมดทดสอบ ----------
    if os.environ.get("ALERT_TEST", "").lower() == "true":
        cnt = lambda k: sum(1 for v in now.values() if v[k])
        sample = next((s for s in stocks if num(s.get("price")) > 0), stocks[0])
        ev = []
        if num(sample.get("pe")) > 0: ev.append("pe_low")
        if num(sample.get("fiftyTwoWeekHigh")) > 0: ev.append("near_high")
        if num(sample.get("fiftyTwoWeekLow")) > 0: ev.append("near_low")
        if num(sample.get("ema200")) > 0: ev.append("golden")
        msg = (f"{sample.get('name', sample['ticker'])}\nราคา {f2(num(sample.get('price')))} {sample.get('currency', '')}\n\n"
               + "\n".join(build_lines(sample, ev)) + "\n\n"
               f"📋 ภาพรวมตอนนี้ ({len(stocks)} ตัว)\n"
               f"• P/E ≤ {PE_MAX:g}: {cnt('pe_low')} ตัว\n"
               f"• ใกล้จุดสูงสุด 52W: {cnt('near_high')} ตัว\n"
               f"• ใกล้จุดต่ำสุด 52W: {cnt('near_low')} ตัว\n"
               f"• ราคาอยู่เหนือ EMA200: {cnt('above_ema')} ตัว")
        ok = send(topic, "🧪 ทดสอบระบบแจ้งเตือน (ข้อความตัวอย่าง)", msg, with_links_for=sample["ticker"])
        print("ส่งข้อความทดสอบแล้ว" if ok else "ส่งทดสอบไม่สำเร็จ")
        sys.exit(0 if ok else 1)

    # ---------- โหมดปกติ ----------
    old_state = load_json(STATE_FILE, None)
    first_run = old_state is None
    old = (old_state or {}).get("stocks", {})

    new_state = {}
    alerts = []   # (ticker, [events])
    for t, cur in now.items():
        prev = old.get(t, {})
        merged = {}
        for k, v in cur.items():
            merged[k] = v if v is not None else prev.get(k)   # ไม่มีข้อมูล = คงสถานะเดิม
        new_state[t] = merged

        if first_run:
            continue
        ev = []
        for k in ("pe_low", "near_high", "near_low"):
            if cur[k] is True and prev.get(k) is False:        # เพิ่งเปลี่ยนจาก "ไม่ใช่" เป็น "ใช่"
                ev.append(k)
            elif REPEAT_52W and k in ("near_high", "near_low") and cur[k] is True and prev.get(k) is True:
                ev.append(k)                                    # ยังแตะอยู่ต่อเนื่อง -> เตือนซ้ำ
        if cur["above_ema"] is True and prev.get("above_ema") is False:
            ev.append("golden")
        if cur["above_ema"] is False and prev.get("above_ema") is True:
            ev.append("dead")
        if ev:
            alerts.append((t, ev))

    if first_run:
        send(topic, "✅ ระบบแจ้งเตือนหุ้นเริ่มทำงานแล้ว",
             f"บันทึกสถานะเริ่มต้นของหุ้น {len(now)} ตัวเรียบร้อย\n\n"
             f"ตั้งแต่พรุ่งนี้จะแจ้งเมื่อมีหุ้นที่ 'เพิ่งเข้าเงื่อนไข':\n"
             f"💰 P/E ≤ {PE_MAX:g}\n🚀 แตะสูงสุด 52W\n🔻 แตะต่ำสุด 52W\n🟢 Golden Cross EMA200\n🔴 Dead Cross EMA200")
    else:
        for t, ev in alerts[:MAX_NOTIFS]:
            s = by_ticker[t]
            msg = f"{s.get('name', t)}\nราคา {f2(num(s.get('price')))} {s.get('currency', '')}\n\n" + "\n".join(build_lines(s, ev))
            send(topic, title_for(t, ev), msg, with_links_for=t)
        rest = alerts[MAX_NOTIFS:]
        if rest:
            txt = "\n".join(f"• {t}: " + ", ".join(e for e in ev) for t, ev in rest)
            send(topic, f"🔔 อีก {len(rest)} ตัวที่เข้าเงื่อนไข", "ไม่ได้แยกส่งเพราะมีจำนวนมาก:\n\n" + txt)
        print(f"ตรวจ {len(now)} ตัว พบสัญญาณใหม่ {len(alerts)} ตัว")

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "stocks": new_state}, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
