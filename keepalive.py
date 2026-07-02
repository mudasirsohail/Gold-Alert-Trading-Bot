from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
    <head><title>Gold FVG Alert Bot</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px; background: #1a1a1a; color: white;">
        <h1>🟡 Gold FVG Alert Bot</h1>
        <p style="color: #00ff00; font-size: 20px;">✅ Bot is Running 24/7</p>
        <p>Monitoring XAUUSD for Fair Value Gaps</p>
        <p>Notifications sent via Telegram</p>
    </body>
    </html>
    """

@app.route('/health')
def health():
    return {"status": "running", "bot": "Gold FVG Alert"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
