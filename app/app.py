from petrosa.ta import strategies as screenings
from petrosa.database import mongo
from petrosa.binance import binance
import threading

periods = ["m15", "m30", "h1"]

COL_PREFIX = "candles_"

asset_list = binance.get_future_assets()

LOOKBACK = 200

data_base = {}
for period in periods:
    if period not in data_base:
        data_base[period] = {}


def get_symbol_data(period, ticker) -> None:
    data_base[period][ticker] = mongo.get_data("petrosa_crypto",
                                               COL_PREFIX + period, ticker, LOOKBACK)


def get_all_data():
    for period in periods:
        for ticker in asset_list:
            threading.Thread(target=get_symbol_data, args=(
                period, ticker["symbol"],)).start()


get_all_data()

print("le fin")
