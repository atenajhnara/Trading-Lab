#یه وب‌اپ که کاربر می‌تونه استراتژی خودش رو بسازه و بعد بک‌تست بگیره روی داده‌های واقعی (مثلاً قیمت بیت‌کوین توی ۳۰ روز گذشته).
#نتیجه هم به‌صورت نمودار و درصد سود و ضرر نشون داده میشه

from flask import  Flask  #یه کتابخانه معروف برای ساخت سایت با پایتونه

# -----------------------------
# 📦 وارد کردن کتابخونه‌ها
# -----------------------------
from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd
import ta
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import json
from plotly.utils import PlotlyJSONEncoder

app = Flask(__name__)  # <- اصلاح شد

@app.route('/')
def home():
    # مقدارهای اولیه None تا template خطا نده
    return render_template('index.html',
                           last_close=None,
                           last_rsi=None,
                           candle_count=None,
                           strategy=None,
                           symbol=None,
                           timeframe=None,
                           graphJSON=None)

@app.route('/backtest', methods=['POST'])
def backtest():
    # گرفتن ورودی فرم
    strategy = request.form.get('strategy', '')
    timeframe = request.form.get('timeframe', '1h')
    symbol = request.form.get('symbol', '').strip()

    if not symbol:
        return render_template('index.html',
                               last_close=None,
                               last_rsi=None,
                               candle_count=None,
                               strategy=None,
                               symbol=None,
                               timeframe=None,
                               graphJSON=None,
                               error="نماد وارد نشده است")

    # نگاشت تایم فریم (برای yfinance)
    tf_map = {"1h": "1h", "30m": "30m", "1d": "1d"}

    # تنظیم ticker
    ticker = symbol.upper()
    if "-" not in ticker:
        ticker = f"{ticker}-USD"

    # دانلود داده — اگر 4h خواسته شده، ابتدا 1h می‌گیری و بعد resample می‌کنی
    try:
        if timeframe == "4h":
            raw = yf.download(ticker, interval="60m", period="90d", progress=False)
        else:
            interval = tf_map.get(timeframe, "1h")
            raw = yf.download(ticker, interval=interval, period="90d", progress=False)
    except Exception as e:
        return render_template('index.html',
                               last_close=None,
                               last_rsi=None,
                               candle_count=None,
                               strategy=None,
                               symbol=None,
                               timeframe=None,
                               graphJSON=None,
                               error=f"خطا در دانلود داده: {e}")

    if raw.empty:
        return render_template('index.html',
                               last_close=None,
                               last_rsi=None,
                               candle_count=None,
                               strategy=None,
                               symbol=None,
                               timeframe=None,
                               graphJSON=None,
                               error="داده‌ای از Yahoo پیدا نشد. نماد یا تایم‌فریم را بررسی کن.")

    # اگر MultiIndex بود سعی در extract کنیم
    if isinstance(raw.columns, pd.MultiIndex):
        try:
            data = raw.xs(ticker, axis=1, level=0)
        except Exception:
            short = ticker.split("-")[0]
            try:
                data = raw.xs(short, axis=1, level=0)
            except Exception:
                raw.columns = ['_'.join(map(str, c)).strip() for c in raw.columns.values]
                data = raw.copy()
    else:
        data = raw.copy()

    # پیدا کردن ستون‌های Open/High/Low/Close/Volume به صورت case-insensitive
    def find_col(df, keywords):
        for k in keywords:
            for c in df.columns:
                if k in str(c).lower():
                    return c
        return None

    open_col  = find_col(data, ['open'])
    high_col  = find_col(data, ['high'])
    low_col   = find_col(data, ['low'])
    close_col = find_col(data, ['close'])
    vol_col   = find_col(data, ['volume', 'vol'])

    if None in (open_col, high_col, low_col, close_col, vol_col):
        return render_template('index.html',
                               last_close=None,
                               last_rsi=None,candle_count=None,
                               strategy=None,
                               symbol=None,
                               timeframe=None,
                               graphJSON=None,
                               error=f"ستون‌های لازم وجود ندارند. ستون‌های موجود: {list(data.columns)}")

    # استانداردسازی ستون‌ها
    data = data[[open_col, high_col, low_col, close_col, vol_col]].copy()
    data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

    # ایندکس تاریخ و پاکسازی
    data.index = pd.to_datetime(data.index)
    print("tedad candle",len(data))
    data = data.sort_index()
    data = data[~data.index.duplicated()]
    data = data.dropna()

    # اگر 4h خواسته شده resample کن
    if timeframe == "4h":
        data = data.resample('4H').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()

    # باز هم پاکسازی بعد از resample
    data = data.sort_index()
    data = data[~data.index.duplicated()]
    data = data.dropna()

    if data.empty:
        return render_template('index.html',
                               last_close=None,
                               last_rsi=None,
                               candle_count=None,
                               strategy=None,
                               symbol=None,
                               timeframe=None,
                               graphJSON=None,
                               error="بعد از پردازش داده، دیتافریم خالی شد.")

    # محاسبه اندیکاتورها
    close_prices = data['Close'].astype(float)
    if "rsi" in strategy.lower():
        data['RSI'] = ta.momentum.RSIIndicator(close_prices).rsi()
    if "macd" in strategy.lower():
        macd = ta.trend.MACD(close_prices)
        data['MACD'] = macd.macd()
        data['Signal'] = macd.macd_signal()

    # پاکسازی نهایی (حذف ردیف‌هایی که اندیکاتور NaN دارند)
    data = data.dropna(subset=['Close'])  # حداقل Close باید وجود داشته باشه
    if "RSI" in data.columns:
        data = data.dropna(subset=['RSI'])
    if "MACD" in data.columns:
        data = data.dropna(subset=['MACD','Signal'])

    if data.empty:
        return render_template('index.html',
                               last_close=None,
                               last_rsi=None,
                               candle_count=None,
                               strategy=None,
                               symbol=None,
                               timeframe=None,
                               graphJSON=None,
                               error="بعد از محاسبه اندیکاتورها، دیتافریم خالی شد (دیتای کافی نیست).")

    # استخراج اعداد برای نمایش
    last_close = float(data['Close'].values[-1])
    last_close = round(last_close, 2)
    last_rsi = round(float(data['RSI'].values[-1]), 2) if 'RSI' in data.columns else "N/A"

    # آماده‌سازی برای Plotly: تبدیل به float و 1D
    if 'RSI' in data.columns:
        data['RSI'] = data['RSI'].astype(float).squeeze()
    if 'MACD' in data.columns:
        data['MACD'] = data['MACD'].astype(float).squeeze()
        data['Signal'] = data['Signal'].astype(float).squeeze()

    # ساخت نمودار
    # ------------------- رسم نمودار -------------------
    # تعیین چند ردیف بر اساس اندیکاتورهای فعال
    rows = 1
    if 'RSI' in data.columns:
        rows += 1
    if 'MACD' in data.columns:
        rows += 1

    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True,
                        vertical_spacing=0.03,
                        row_heights=[0.6] + [0.2]*(rows-1))

    current_row = 1

    # کندل‌ها
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Price'
    ), row=current_row, col=1)

    current_row += 1

    # RSI
    if 'RSI' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['RSI'],
            line=dict(color='orange', width=2),
            name='RSI'
        ), row=current_row, col=1)
        current_row += 1

    # MACD
    if 'MACD' in data.columns and 'Signal' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['MACD'],
            line=dict(color='green', width=2),
            name='MACD'
        ), row=current_row, col=1)
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['Signal'],
            line=dict(color='red', width=2),
            name='Signal'
        ), row=current_row, col=1)

    fig.update_layout(
        height=900,
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        title=f"{symbol.upper()} — {strategy}"
    )

    graphJSON = json.dumps(fig, cls=PlotlyJSONEncoder)

    return render_template('index.html',
                           last_close=last_close,
                           last_rsi=last_rsi,
                           candle_count=len(data),
                           strategy=strategy,
                           symbol=symbol,
                           timeframe=timeframe,
                           graphJSON=graphJSON)

if __name__ == '__main__':  # <- اصلاح شد
    app.run(debug=True)

