# 📊 TradingLab | وب‌اپ بک‌تست استراتژی‌های معاملاتی

A Flask-based web application for testing trading strategies on real cryptocurrency data (e.g., Bitcoin, Ethereum).  
It allows users to select indicators like RSI and MACD, choose a timeframe, and visualize results interactively with Plotly.

یک وب‌اپ ساده و کاربردی برای بک‌تست استراتژی‌های معاملاتی با داده‌های واقعی از بازار ارز دیجیتال.  
کاربر می‌تواند نماد، تایم‌فریم و استراتژی موردنظر خود را انتخاب کند و نتایج را روی نمودار ببیند.

---

## 🧠 Technologies Used | تکنولوژی‌های استفاده‌شده

- Flask – برای ساخت وب‌اپلیکیشن  
- Plotly – برای رسم نمودارهای تعاملی  
- pandas / NumPy – برای پردازش داده‌ها  
- ta (Technical Analysis Library) – محاسبه اندیکاتورها (RSI، MACD و...)  
- yfinance – دریافت داده‌های واقعی قیمت رمزارزها  

---

## ⚙️ How It Works | نحوه کار

1. کاربر نماد (مثل BTC یا ETH)، تایم‌فریم (1h، 4h، 1d) و استراتژی (RSI یا RSI+MACD) را وارد می‌کند.  
2. برنامه داده‌های قیمت را از Yahoo Finance می‌گیرد.  
3. اندیکاتورهای انتخابی محاسبه می‌شوند (RSI، MACD و Signal).  
4. نمودار کندل‌ها و اندیکاتورها با Plotly رسم می‌شود.  
5. نتایج شامل قیمت آخر، RSI، تعداد کندل‌ها و نمودار نهایی به کاربر نمایش داده می‌شود.  

---

## 🧩 Key Code Structure | ساختار اصلی کد

```python
# Flask app initialization
app = Flask(__name__)

# Home route (form input)
@app.route('/')
def home():
    return render_template('index.html', ...)

# Backtest route
@app.route('/backtest', methods=['POST'])
def backtest():
    # Get symbol, strategy, timeframe
    # Download data using yfinance
    # Calculate indicators (RSI, MACD)
    # Build Plotly chart
    ...
