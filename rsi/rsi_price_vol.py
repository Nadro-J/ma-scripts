import ccxt
import pandas as pd
import numpy as np
import time
from rich.align import Align
from rich.console import Console
from rich.table import Table
from rich.columns import Columns
from rich.panel import Panel
from asciichartpy import plot


def calculate_RSI(data, period):
    delta = data.diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    gain = up.rolling(period).mean()
    loss = abs(down.rolling(period).mean())
    RS = gain / loss
    rsi = 100.0 - (100.0 / (1.0 + RS))
    return rsi


# Define the exchanges to check
exchanges = ['binance', 'okx', 'huobi']

# Define the symbols
spot_symbol = 'BTC/USDT:USDT'

# Define the timeframe and the number of periods for RSI calculation
timeframe = '1m'
periods = 20
history = {
    exchange: {
        'rsi': [],
        'open': [],
        'volume': [],
        'positive_volume': [0],
        'negative_volume': [0]
    } for exchange in exchanges
}
console = Console()
while True:
    panels = []
    for exchange_id in exchanges:
        try:
            exchange = getattr(ccxt, exchange_id)()
            candles = exchange.fetch_ohlcv(spot_symbol, timeframe, limit=periods * 2)
            df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df['rsi'] = calculate_RSI(df['close'], periods)
            last_rsi = df['rsi'].iloc[-1]

            if np.isnan(last_rsi):
                sentiment = 'insufficient data'
                sentiment_color = "yellow"
            elif last_rsi > 70:
                sentiment = 'overbought'
                sentiment_color = "red"
            elif last_rsi < 30:
                sentiment = 'oversold'
                sentiment_color = "green"
            else:
                sentiment = 'neutral'
                sentiment_color = "white"

            history[exchange_id]['rsi'].append(last_rsi)
            history[exchange_id]['rsi'] = history[exchange_id]['rsi'][-30:]

            # Storing the open price history
            history[exchange_id]['open'].append(df['open'].iloc[-1])
            history[exchange_id]['open'] = history[exchange_id]['open'][-30:]

            # Storing the volume history
            history[exchange_id]['volume'].append(df['volume'].iloc[-1])
            history[exchange_id]['volume'] = history[exchange_id]['volume'][-30:]

            # Storing positive and negative volumes
            if len(history[exchange_id]['open']) > 1:
                if df['close'].iloc[-1] > history[exchange_id]['open'][-2]:
                    history[exchange_id]['positive_volume'].append(df['volume'].iloc[-1])
                    history[exchange_id]['negative_volume'].append(0)
                else:
                    history[exchange_id]['positive_volume'].append(0)
                    history[exchange_id]['negative_volume'].append(df['volume'].iloc[-1])
            history[exchange_id]['positive_volume'] = history[exchange_id]['positive_volume'][-30:]
            history[exchange_id]['negative_volume'] = history[exchange_id]['negative_volume'][-30:]

            # Create positive and negative volume charts
            positive_volume_chart = plot(history[exchange_id]['positive_volume'], {'height': 6, 'min': min(history[exchange_id]['positive_volume']), 'max': max(history[exchange_id]['positive_volume'])})
            negative_volume_chart = plot(history[exchange_id]['negative_volume'], {'height': 6, 'min': min(history[exchange_id]['negative_volume']), 'max': max(history[exchange_id]['negative_volume'])})

            table = Table()
            table.add_column("Timestamp", style="white")
            table.add_column("Open", style="cyan")
            table.add_column("High", style="cyan")
            table.add_column("Low", style="cyan")
            table.add_column("Close", style="cyan")
            table.add_column("Volume", style="cyan")
            table.add_column("RSI", style="magenta")
            table.add_column("Sentiment", style=sentiment_color)
            last_candle = df.iloc[-1]
            table.add_row(str(df.index[-1]), f"{last_candle['open']:.2f}", f"{last_candle['high']:.2f}",
                          f"{last_candle['low']:.2f}", f"{last_candle['close']:.2f}",
                          f"{last_candle['volume']:.2f}", f"{last_rsi:.2f}", sentiment)

            rsi_chart = plot(history[exchange_id]['rsi'], {'height': 6, 'min': min(history[exchange_id]['rsi']), 'max': max(history[exchange_id]['rsi'])})
            open_chart = plot(history[exchange_id]['open'], {'height': 6, 'min': min(history[exchange_id]['open']), 'max': max(history[exchange_id]['open'])})
            volume_chart = plot(history[exchange_id]['volume'], {'height': 6, 'min': min(history[exchange_id]['volume']), 'max': max(history[exchange_id]['volume'])})

            panel_content = f"Open: {last_candle['open']:,.2f}\n" + \
                            f"Sentiment: [{sentiment_color}]{sentiment}[/{sentiment_color}]\n" + \
                            "\nOpen Price\n" + "[bright_yellow]" + open_chart + "[/bright_yellow]" + \
                            "\n\nRelative Strength Indicator\n" + "[bright_magenta]" + rsi_chart + "[/bright_magenta]" + \
                            "\nVolume\n" + "[gray]" + volume_chart + "[/gray]" + \
                            "\nBought\n" + "[bright_green]" + positive_volume_chart + "[/bright_green]" + \
                            "\nSold\n" + "[bright_red]" + negative_volume_chart + "[/bright_red]"
            panels.append(Panel(panel_content, title=f"[bright_blue]{exchange_id.upper()}[/bright_blue] - [white]{str(df.index[-1])}[/white]", height=50, style="cyan"))

        except Exception as e:
            console.print(f"An error occurred while fetching data from {exchange_id}: {e}", style="purple")

    console.clear()
    console.print(Align.center("""
              _,,ddF```Ybb,,_
            ,dCHAOSDAO,   `"Yb,
          ,d#@#V``V@#@#b      "b,
         d@#@#I    I@#@8        "b
        d@#@#@#A..A@#@#P         `b
        8#@#@#@#@#@#@8"           8
        8@#@#@#@#@#@J             8
        8#@#@#@#@#P               8
        Y@#@#@#@#P    ,db,       ,P
         Y@#@#@#@)    @420      aP
          "Y#@#@#b    `69'    aP"
            "Y@#@#g,,     _,dP"
              `""YBBgggddP""'
              
AAAaaaauughh, Immmmmm X100 leverrrrraaaggiiiingggh"""))
    console.print(Align.center(f"Watching {spot_symbol} on {timeframe} timeframe using {periods} periods"), style="magenta")
    console.print(Align.center(Columns(panels)))
    time.sleep(10)
