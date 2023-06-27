import json
import logging
import os
import threading
import time

from petrosa.binance import binance
from petrosa.database import mongo
from petrosa.messaging import kafkareceiver
from petrosa.ta import strategies as screenings

logging.basicConfig(level=logging.INFO)

struct = {"15m": "m15",
          "30m": "m30",
          "1h": "h1",
          }

LOOKBACK = 200

N_TRADES_LIMIT = int(os.getenv("N_TRADES_LIMIT", 10))
SQN_LIMIT = int(os.getenv("SQN_LIMIT", 1))


def get_bt_result(symbol, strategy, period):
    bt_result = mongo.get_client()["petrosa_crypto"]["backtest_results"].find_one({"period": period,
                                                                                   "symbol": symbol,
                                                                                   "strategy": strategy})
    return bt_result

def run_strategies(raw_period, ticker) -> None:
    if(raw_period not in struct):
        # print("period", raw_period, "not allowed. exiting...")
        return 
        
    time.sleep(1)
    data = mongo.get_data("petrosa_crypto",
                          "candles_" + struct[raw_period], ticker, LOOKBACK)
    msg = "getting data for ", ticker, struct[raw_period]
    # logging.info(msg)
    for ta in screenings.strategy_list:
        # msg2 = "Running strategy ", ta, " for ", ticker, " in ", struct[raw_period]
        # logging.info(msg2)
        func = getattr(screenings, ta)
        result = func(data, struct[raw_period])
        if result != {}:
            bt_result = get_bt_result(symbol=ticker, strategy=ta, period=struct[raw_period])
            try:
                if(bt_result and 
                bt_result["n_trades"] > N_TRADES_LIMIT and 
                bt_result["sqn"] > SQN_LIMIT):
                    full_result = {**result, **bt_result}
                    # msg3 = "persisting", result
                    # logging.info(msg3)
                    mongo.get_client()["petrosa_crypto"]["time_limit_orders"].insert_one(full_result)
                    order_res = binance.send_order(ticker=ticker, 
                                       type=full_result["type"], 
                                       price=full_result["entry_value"],
                                       stop_loss=full_result["stop_loss"],
                                       take_profit=full_result["take_profit"],
                                       valid_until=full_result["valid_until"]
                                       )
                    logging.info(order_res)
                    
            except Exception as e:
                msg = str(e) + " - " + str(result) + " - " + str(bt_result)
                logging.error(msg)

receiver = kafkareceiver.get_consumer("binance_klines_current")


_thread_list = []
for msg in receiver:
    # print(json.loads(msg.value.decode()))
    msg = json.loads(msg.value.decode())
    curr_kline = msg
    _t = threading.Thread(target=run_strategies, 
                          args=(curr_kline["k"]["i"], curr_kline["k"]["s"],))
    _t.start()
    _thread_list.append(_t)
    

for _thread in _thread_list:
    _thread.join()