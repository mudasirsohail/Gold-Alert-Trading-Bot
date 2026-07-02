import requests
import time
import schedule
from datetime import datetime

# ─── CONFIG ────────────────────────────────────────────
TWELVE_DATA_API_KEY = ""
NTFY_TOPIC          = ""

SYMBOL    = "XAU/USD"
INTERVAL  = "1h"
LOOKBACK  = 50
SWING_LB  = 20
# ───────────────────────────────────────────────────────


def send_notification(title, message, priority="default"):
    """Send notification via ntfy.sh"""
    try:
        response = requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers={
                "Title": title,
                "Priority": priority,
                "Content-Type": "text/plain; charset=utf-8"
            },
            timeout=30
        )
        if response.status_code == 200:
            print(f"✅ Notification sent: {title}")
        else:
            print(f"❌ ntfy error: {response.text}")
    except Exception as e:
        print(f"❌ ntfy exception: {e}")


def get_candles(count=LOOKBACK + 5):
    url = "https://api.twelvedata.com/time_series"
    params = {"symbol": SYMBOL, "interval": INTERVAL, "outputsize": count, "apikey": TWELVE_DATA_API_KEY}
    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        if "values" not in data:
            print(f"❌ API error: {data}")
            return None
        candles = []
        for c in reversed(data["values"]):
            candles.append({
                "time":  c["datetime"],
                "open":  float(c["open"]),
                "high":  float(c["high"]),
                "low":   float(c["low"]),
                "close": float(c["close"])
            })
        return candles
    except Exception as e:
        print(f"❌ Fetch error: {e}")
        return None


def check_fvg(candles):
    c1, c2, c3 = candles[-4], candles[-3], candles[-2]
    print(f"  [FVG] C1 High:{c1['high']:.2f} Low:{c1['low']:.2f}")
    print(f"  [FVG] C2 High:{c2['high']:.2f} Low:{c2['low']:.2f}")
    print(f"  [FVG] C3 High:{c3['high']:.2f} Low:{c3['low']:.2f}")

    if c3['low'] > c1['high']:
        gap = round(c3['low'] - c1['high'], 2)
        send_notification(
            "Bullish FVG Detected",
            f"GREEN FVG - Gold moving UP\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M')}\nGap: {c1['high']:.2f} to {c3['low']:.2f}\nSize: {gap} pips",
            "high"
        )
        print("  🟢 Bullish FVG found!")
        return

    if c3['high'] < c1['low']:
        gap = round(c1['low'] - c3['high'], 2)
        send_notification(
            "Bearish FVG Detected",
            f"RED FVG - Gold moving DOWN\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M')}\nGap: {c3['high']:.2f} to {c1['low']:.2f}\nSize: {gap} pips",
            "high"
        )
        print("  🔴 Bearish FVG found!")
        return

    print("  ⚪ No FVG detected")


def check_trendline(candles):
    recent = candles[-LOOKBACK:]
    current_price = candles[-1]['close']
    highs = [c['high'] for c in recent]
    lows  = [c['low']  for c in recent]

    h_indices = sorted(range(len(highs)), key=lambda i: highs[i], reverse=True)[:2]
    h_indices.sort()
    i1, i2 = h_indices[0], h_indices[1]
    h1, h2 = highs[i1], highs[i2]
    time_h1, time_h2 = recent[i1]['time'], recent[i2]['time']
    resistance_now = h1 + ((h2 - h1) / (i2 - i1)) * (len(recent) - 1 - i1) if i2 != i1 else h1

    l_indices = sorted(range(len(lows)), key=lambda i: lows[i])[:2]
    l_indices.sort()
    j1, j2 = l_indices[0], l_indices[1]
    l1, l2 = lows[j1], lows[j2]
    time_l1, time_l2 = recent[j1]['time'], recent[j2]['time']
    support_now = l1 + ((l2 - l1) / (j2 - j1)) * (len(recent) - 1 - j1) if j2 != j1 else l1

    threshold = 0.002
    print(f"  [TL] Price:{current_price:.2f} Resistance:{resistance_now:.2f} Support:{support_now:.2f}")

    if abs(current_price - resistance_now) / resistance_now < threshold:
        send_notification(
            "Resistance Trendline Touched",
            f"Price hitting RESISTANCE - possible reversal DOWN\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M')}\nCurrent Price: {current_price:.2f}\nResistance: {resistance_now:.2f}\nPoint 1: {time_h1} High: {h1:.2f}\nPoint 2: {time_h2} High: {h2:.2f}",
            "high"
        )
        print("  📉 Resistance trendline touched!")
        return

    if abs(current_price - support_now) / support_now < threshold:
        send_notification(
            "Support Trendline Touched",
            f"Price hitting SUPPORT - possible reversal UP\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M')}\nCurrent Price: {current_price:.2f}\nSupport: {support_now:.2f}\nPoint 1: {time_l1} Low: {l1:.2f}\nPoint 2: {time_l2} Low: {l2:.2f}",
            "high"
        )
        print("  📈 Support trendline touched!")
        return

    print("  ⚪ No trendline touch")


def check_fibonacci(candles):
    recent = candles[-SWING_LB:]
    current_price = candles[-1]['close']
    swing_high = max(c['high'] for c in recent)
    swing_low  = min(c['low']  for c in recent)
    diff = swing_high - swing_low
    fib_50  = swing_high - 0.500 * diff
    fib_618 = swing_high - 0.618 * diff
    print(f"  [FIB] Price:{current_price:.2f} Zone:{fib_618:.2f}-{fib_50:.2f} (H:{swing_high:.2f} L:{swing_low:.2f})")

    if fib_618 <= current_price <= fib_50:
        send_notification(
            "Fibonacci Golden Zone",
            f"Price in 0.5-0.618 retracement zone\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M')}\nCurrent Price: {current_price:.2f}\nZone: {fib_618:.2f} to {fib_50:.2f}\nSwing High: {swing_high:.2f}\nSwing Low: {swing_low:.2f}",
            "high"
        )
        print("  🟡 Fibonacci golden zone hit!")
    else:
        print("  ⚪ Price not in fib zone")


def run_checks():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n{'='*50}\n🔍 Running checks at {now}\n{'='*50}")
    candles = get_candles()
    if candles is None or len(candles) < LOOKBACK:
        print("❌ Not enough candles")
        send_notification("Error", "Could not fetch candle data.")
        return
    print(f"✅ Fetched {len(candles)} candles\n")
    print("1️⃣  Checking FVG...")
    check_fvg(candles)
    print("\n2️⃣  Checking Trendlines...")
    check_trendline(candles)
    print("\n3️⃣  Checking Fibonacci...")
    check_fibonacci(candles)
    print(f"\n✅ All checks done at {now}")


def main():
    print("🚀 Gold Alert Bot Starting...")
    print(f"   Detecting: FVG + Trendline + Fibonacci")
    print(f"   Symbol: {SYMBOL} | Interval: {INTERVAL}\n")

    send_notification(
        "Gold Alert Bot Started",
        "Monitoring every hour for:\n- FVG (Bullish & Bearish)\n- Trendline Touch\n- Fibonacci 0.5-0.618 Zone",
        "default"
    )

    run_checks()
    schedule.every().hour.at(":02").do(run_checks)
    print("\n⏰ Scheduler running...\n")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
