import os
from flask import Flask, request
from bot import QuoteBot, ImageProcessingBot

app = Flask(__name__)

TELEGRAM_APP_URL = 'https://t.me/@Smileythebot'
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

if not TELEGRAM_TOKEN:
    raise ValueError("No TELEGRAM_TOKEN provided")

@app.route('/', methods=['GET'])
def index():
    """
    This is a function docstring.
    """
    return 'Ok'


@app.route(f'/{TELEGRAM_TOKEN}/', methods=['POST'])
def webhook():
    """
    This is a function docstring.
    """
    req = request.get_json()
    print(req)
    if 'message' in req:
        QuoteBot.handle_message(req['message'])
    return 'Ok'


if __name__ == "__main__":
    QuoteBot = ImageProcessingBot(TELEGRAM_TOKEN, TELEGRAM_APP_URL)

    app.run(host='0.0.0.0', port=8443)
