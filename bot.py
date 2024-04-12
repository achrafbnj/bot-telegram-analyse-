import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import telegram
from telegram.ext import Updater, CommandHandler

# Telegram bot token
TOKEN = "6723919110:AAF1GB2qAT4pfdJjLoXZV-HDrcdBsazE2NU"

def get_coin_data(coin_name, days=30):
    url = f'https://api.coingecko.com/api/v3/coins/{coin_name.lower()}/market_chart?vs_currency=usd&days={days}'
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df.set_index('timestamp')

def calculate_sma(prices, window=20):
    return prices['price'].rolling(window=window, min_periods=1).mean()

def calculate_rsi(prices, window=14):
    delta = prices['price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices, short_window=12, long_window=26):
    short_ema = prices['price'].ewm(span=short_window, min_periods=1, adjust=False).mean()
    long_ema = prices['price'].ewm(span=long_window, min_periods=1, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=9, min_periods=1, adjust=False).mean()
    return macd, signal

def calculate_signals(prices):
    prices['sma_short'] = calculate_sma(prices, window=20)
    prices['sma_long'] = calculate_sma(prices, window=50)
    prices['rsi'] = calculate_rsi(prices, window=14)
    macd, signal = calculate_macd(prices)
    prices['macd'] = macd
    prices['signal'] = signal
    prices['sma_signal'] = np.where(prices['sma_short'] > prices['sma_long'], 1.0, 0.0)
    prices['rsi_signal'] = np.where(prices['rsi'] < 30, 1.0, np.where(prices['rsi'] > 70, -1.0, 0.0))
    prices['macd_signal'] = np.where(macd > signal, 1.0, -1.0)
    return prices

def plot_chart(coin_name, prices):
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(12, 12), sharex=True)
    ax1.plot(prices.index, prices['price'], label=f'{coin_name.upper()} Price')
    ax1.plot(prices.index, prices['sma_short'], label='SMA (20)')
    ax1.plot(prices.index, prices['sma_long'], label='SMA (50)')
    ax1.set_ylabel('Price (USD)')
    ax1.legend()
    ax1.grid(True)

    ax2.plot(prices.index, prices['rsi'], label='RSI')
    ax2.axhline(y=30, color='r', linestyle='--', label='Oversold (30)')
    ax2.axhline(y=70, color='g', linestyle='--', label='Overbought (70)')
    ax2.set_ylabel('RSI')
    ax2.legend()
    ax2.grid(True)

    ax3.plot(prices.index, prices['macd'], label='MACD')
    ax3.plot(prices.index, prices['signal'], label='Signal')
    ax3.set_ylabel('MACD')
    ax3.legend()
    ax3.grid(True)

    ax4.plot(prices.index, prices['sma_signal'], label='SMA Crossover Signal')
    ax4.plot(prices.index, prices['rsi_signal'], label='RSI Signal')
    ax4.plot(prices.index, prices['macd_signal'], label='MACD Signal')
    ax4.set_ylabel('Signal')
    ax4.legend()
    ax4.grid(True)

    plt.xlabel('Time')
    plt.suptitle(f'{coin_name.upper()} Analysis')
    plt.show()

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the name of the cryptocurrency you want to analyze.")

def analyze_coin(update, context):
    coin_name = update.message.text.strip()
    prices = get_coin_data(coin_name)
    prices = calculate_signals(prices)
    
    # Generate the plot
    plot_chart(coin_name, prices)

def main():
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("analyze", analyze_coin))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
