from flask import Flask, render_template, jsonify
import yfinance as yf
import pandas as pd
import requests

app = Flask(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Hàm Scraping bóc tách danh sách mã cổ phiếu từ Yahoo Finance
def scrape_stock_list(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        tables = pd.read_html(response.text)
        if tables:
            df = tables[0]
            # Lấy cột Symbol (thường là cột đầu tiên), bỏ qua các mã có dấu phụ khó hiểu
            return df.iloc[:, 0].head(8).tolist()
    except Exception as e:
        print(f"Scraping error: {e}")
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/list/<category>')
def get_list(category):
    urls = {
        "most_active": "https://finance.yahoo.com/markets/stocks/most-active/",
        "gainers": "https://finance.yahoo.com/markets/stocks/gainers/",
        "crypto": "https://finance.yahoo.com/markets/crypto/all/"
    }
    
    if category == "vn":
        stocks = ["FPT.VN", "HPG.VN", "VCB.VN", "VNM.VN", "VIC.VN", "MWG.VN", "TCB.VN", "^VNINDEX"]
    else:
        stocks = scrape_stock_list(urls.get(category))
    
    return jsonify({"stocks": stocks})

@app.route('/api/stock/<ticker>')
def get_stock_details(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo")
        if df.empty: return jsonify({"error": "N/A"}), 404

        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        change_pct = ((current_price - prev_price) / prev_price) * 100
        
        # Tính RSI (Chỉ số sức mạnh) đơn giản
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs.iloc[-1]))

        return jsonify({
            "symbol": ticker.upper(),
            "price": round(current_price, 2),
            "change": round(change_pct, 2),
            "rsi": round(rsi, 2),
            "history": df['Close'].tail(30).tolist(),
            "labels": df.index.strftime('%d/%m').tail(30).tolist()
        })
    except:
        return jsonify({"error": "Error"}), 500

if __name__ == '__main__':
    app.run(debug=True)