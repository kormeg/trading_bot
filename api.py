import pandas as pd
import numpy as np
import datetime as dt
import time 
import re
from pybit.unified_trading import HTTP 
from pybit.unified_trading import WebSocket
from pybit import exceptions
from IPython.display import display
from func import tables as tb
from func.tables import frame_print
from pprint import pprint
import asyncio
import os
import sys
import threading
from queue import Queue, Empty
from collections import deque



class API():
    # intervals = ["1", "5", "15", "60"]
    intervals = ["1", "5"]
    oi_intervals = ["1m", "5min", "15min", "1h"]
    ignored_symbols = []
    position_items = ['symbol', 'side', 'size', 'entryPrice', 'leverage', 'positionValue', 'takeProfit', 'stopLoss', 'trailingStop', 'liqPrice', 'breakEvenPrice'] 
    closed_position_items = ['avgExitPrice', 'closedPnl', 'closeTime', 'openFee', 'closeFee']
    all_deal_items = ["symbol", "leverage", "breakEvenPrice", "liqPrice", "takeProfit", "positionValue", 
                 "trailingStop", "side", "size", "stopLoss", "entryPrice", "botName", "strategyName", 
                 "identificationTime", "openTime", "volumeDifference", "timeframe", "identificationPrice", 
                 "natr", "avgExitPrice", "closedPnl", "closeTime", "fee", "openId", "closeId"]

    # {"размер в монете" : ["size",  "qty", "closed_size"], 
    # "цена входа" : ["entryPrice", "avgPrice", "avgEntryPrice"], 
    # "размер в usdt" : ["positionValue", "cumEntryValue" ], 
    # "комииссии" : ["closeFee", "openFee"]}

    def __init__(self, api_key=None, secret_key=None, demo=True, websocket=True):

        self.api_key=api_key
        self.secret_key=secret_key
        self.demo=demo    

        self.session = None 
        self.public_ws = None
        self.private_ws = None

        self.data = {}
        self.deals = {}
        # self.closed = []
        self.deal_news = Queue()
        self.balance_news = False
        self.full_info = len(API.all_deal_items)

        self.private_mail_queue = Queue()
        self.public_mail_queue = deque(maxlen=10000)

        self.data_lock = threading.Lock()
        self.public_data_thread = threading.Thread(target=self.sort_public_mail, daemon=True)
        self.public_data_thread.start()
        self.deals_lock = threading.Lock()

        self.sync_system_time()
        if not self.api_connection():
            frame_print("Не удалось подключиться к Bybit. Попробуй позже.")   
            sys.exit()
        if websocket:
            self.public_ws_connection()
            if not self.public_ws:
                frame_print("Не пашет связь. Попробуй позже.")
                sys.exit()
            
            self.private_ws_connection()

        self.get_data_dict()
        self.all_symbols = list(self.data)


    def sync_system_time(self):
        try:
            res = os.system('w32tm /resync /force')
            if res != 0:
                frame_print("Нет прав для изменения системного времени (нужен запуск от имени администратора)")
                # sys.exit()
                return False
            else:
                time.sleep(2)
                return True
        except Exception as e:
            frame_print(e)
            frame_print("Системное время не синхронизировано")
            return False
    
    
    def api_connection(self, retries=3):
        if not self.session:
            for i in range(1, retries+1):
                timeout = 30*i
                params = {        
                    "api_key": self.api_key,
                    "api_secret" : self.secret_key,
                    "testnet": False,
                    "demo" : self.demo,
                    "timeout" : timeout,
                    "force_retry" : True,
                    "max_retries" : 1,
                    # "retry_delay" : 3,
                    "recv_window" : 10000
                }
                try:
                    self.session = HTTP(**params)
                    frame_print("http-соеднение готово")
                    return True
                except Exception as e:
                    frame_print(f"Попытка: {i}/{retries}. \nTimeout:{timeout}. \nНе удалось подключиться")
                    frame_print(e)
            return False
        else:
            return True
            

    def public_ws_connection(self):
        if self.public_ws:
            try:
                self.public_ws.exit()
            except Exception: 
                pass
            self.public_ws = None
        try:
            self.public_ws = WebSocket(
                    testnet=False,
                    channel_type="linear",
                    retries=10,
                    restart_on_error=True,
                    ping_interval=60,
                    ping_timeout=40, 
                    private_auth_expire=30
                )
            for symb in self.get_symbol_list():
                self.public_ws.ticker_stream(symbol=symb, callback=self.handle_public)
                for inter in API.intervals:
                    self.public_ws.kline_stream(interval=inter, symbol=symb, callback=self.handle_public)
            
            if self.is_ws_connect(self.public_ws):
                frame_print("Публичный вебсокет подключен") 
        except Exception as e:
            frame_print(e)


    def private_ws_connection(self):
        if self.private_ws:
            try:
                self.private_ws.exit()
            except Exception:
                pass
            self.private_ws = None
        try:
            self.private_ws = WebSocket(
                    testnet=False,
                    channel_type="private",
                    api_key=self.api_key,
                    api_secret=self.secret_key,
                    retries=10,
                    restart_on_error=True,
                    ping_interval=60,  
                    ping_timeout=40,
                    private_auth_expire=30
                )
            self.private_ws.position_stream(callback=self.handle_private)
            self.private_ws.wallet_stream(callback=self.handle_private)
            # self.private_ws.execution_stream(callback=self.handle_private)
            if self.is_ws_connect(self.private_ws):
                frame_print("Приватный вебсокет подключен")
        except Exception as e:
            frame_print(e)


    def is_ws_connect(self, ws):
        try:
            sock = getattr(getattr(ws, "ws", None), "sock", None)
            return bool(sock and sock.connected)
        except Exception:
            return False
        # try:
        #     return ws.ws.sock.connected
        # except (AttributeError, TypeError):
        #     return False
        

    def public_ws_reconnect(self):
        if not self.is_ws_connect(self.public_ws):
            frame_print(["Публичный вебсокет отвалился", "Восстанавливаю соединентие"], sep="\n")
            self.public_ws_connection()


    def private_ws_reconnect(self):
        if not self.is_ws_connect(self.private_ws):
            frame_print(["Приватный вебсокет отвалился", "Восстанавливаю соединентие"], sep="\n")
            self.private_ws_connection()


    def request_with_retry(self, func, *args, **kwargs):
        try:
            kwargs['timestamp'] = self.get_bybit_time()
            return func(*args, **kwargs)
        except Exception as e:
            err_str = str(e).lower()
            if 'reset by peer' in err_str or 'connection aborted' in err_str:
                print("HTTP соединение отвалилось Пересоздаю...")
                kwargs['timestamp'] = self.get_bybit_time()
                self.api_connection()
                return func(*args, **kwargs)
            raise


    def get_bybit_time(self):
        try:
            response = self.session.get_server_time()
            return int(response["result"]["timeSecond"]) * 1000
        except:
            return int(time.time() * 1000)


    def get_data_dict(self):
        while True:
            try:
                l = self.session.get_instruments_info(category="linear", limit=1000)["result"]["list"]
                d = {x["symbol"] : 
                     {
                         "price_scale": int(x["priceScale"]), 
                         "min_qty":float(x["lotSizeFilter"]["minOrderQty"]), 
                         "qty_step":float(x["lotSizeFilter"]["qtyStep"])
                     } for x in l if re.findall(r'\w+USDT$', x["symbol"]) and x["symbol"] not in self.ignored_symbols}
                l = self.session.get_tickers(category="linear")["result"]["list"]
                d2 = {x["symbol"] : 
                      {
                          "high24": float(x["highPrice24h"]), 
                          "low24":float(x["lowPrice24h"]), 
                          "qty_oi":float(x["openInterest"]), 
                          "value_oi":float(x["openInterestValue"]), 
                          "volume24": float(x["turnover24h"]),
                          "last_price": float(x["lastPrice"]), 
                          "intervals":{}
                      } for x in l if re.findall(r'\w+USDT$', x["symbol"]) and x["symbol"] not in self.ignored_symbols}
                
                self.data={k:d[k]|d2[k] for k in d}
            except:
                time.sleep(1)
            else:
                break
        

    def get_candles(self, symbol, interval, limit, start=None, end=None):

        candles = self.session.get_kline(category="linear", 
                            symbol=symbol.upper(), 
                            interval=interval,
                            start=start,
                            end=end,
                            limit=limit)["result"]["list"]
        
        try:
            self.params.get("test")
        except:
            self.params = {}
        
        # if self.params.get("open_interest", True) and interval != "1":
        #     oi = self.session.get_open_interest(
        #         category="linear",
        #         symbol=symbol.upper(),
        #         intervalTime=API.oi_intervals[API.intervals.index(interval)],
        #         limit=limit
        #         )["result"]["list"]
            
        #     oi = [list(x.values()) for x in oi]
        #     oi = pd.DataFrame(oi, columns=["open_interest", "time"])
        #     oi = oi.astype(float)
        #     oi["time"] = pd.to_datetime(oi["time"], unit="ms")
        #     oi["time"] = oi["time"]+ dt.timedelta(hours=3)
        #     oi = tb.time_to_index(oi)

        if self.params.get("last_closed", False):
            df = pd.DataFrame(candles[1:])    
        else:
            df = pd.DataFrame(candles)
        if self.params.get("volume", True):
            df = df.iloc[:,:7]
            df.columns=["time", "open", "high", "low", "close", "coin_volume", "volume"]
        else:
            df = df.iloc[:,:5]
            df.columns=["time", "open", "high", "low", "close"]
        df = df.astype(float)
        df["time"] = pd.to_datetime(df["time"], unit="ms")
        if self.params.get("moscow", True):
            df["time"] = df["time"]+ dt.timedelta(hours=3)
        if  self.params.get("time_to_ind", True):
            df = tb.time_to_index(df)
        # try:
        #     df = pd.concat([df, oi], axis=1)
        # except:
        #     pass
        if self.params.get("set_pf", False):
            df = tb.set_postfix(df, self.params.get("interval"), self.params.get("pf", None))
        df = tb.set_direction(df, self.params.get("direction", "decreace"))
        return df
    

    def get_data(self, symbols, intervals, limit=200, last_closed=False, 
                 volume=True, open_interest=True, moscow=True, 
                 time_to_ind=True, direction="decrease", 
                 pf=None, set_pf=False, start=None, end=None):
           
        if type(symbols) == str:
            self.symbols = [symbols.upper()]
        else:
            self.symbols = [x.upper() for x in symbols]
        if type(intervals) == int or type(intervals) == str:
            self.intervals = [str(intervals)]
        else:
            self.intervals = [str(x) for x in intervals]
        self.params = dict(last_closed=last_closed,
                           volume=volume,
                           open_interest=open_interest,
                           moscow=moscow,
                           time_to_ind=time_to_ind, 
                           direction=direction,
                           pf=pf, 
                           set_pf=set_pf)
        
        for symb in self.symbols:
            for inter in self.intervals:
                while True:
                    try:
                        data = self.get_candles(symb, inter, limit, start, end)
                        self.data[symb]["intervals"][inter] = dict(data=data)
                    except:
                        time.sleep(1)
                    else:
                        break


    async def a_get_candles(self, symbol, interval, limit, start=None, end=None):
         return self.get_candles(symbol, interval, limit, start=start, end=end)
    
    
    async def agd(self, symbols, intervals, limit=200, last_closed=False, volume=True, 
                  open_interest=False, moscow=True, time_to_ind=True, 
                  direction="decrease", pf=None, set_pf=False, start=None, end=None):
        if type(symbols) == str:
            self.symbols = [symbols.upper()]
        else:
            self.symbols = [x.upper() for x in symbols]
        if type(intervals) == int or type(intervals) == str:
            self.intervals = [str(intervals)]
        else:
            self.intervals = [str(x) for x in intervals]
        tasks = []
        # self.data = {}
        self.params = dict(last_closed=last_closed,
                           volume=volume,
                           open_interest=open_interest,
                           moscow=moscow,
                           time_to_ind=time_to_ind, 
                           direction=direction,
                           pf=pf, 
                           set_pf=set_pf)
        for symb in self.symbols:
            for inter in self.intervals:
                self.data[symb]["intervals"][inter] = {}

                while True:
                    try:
                        task = asyncio.create_task(self.a_get_candles(symb, inter, limit, start, end))
                        tasks.append([symb, inter , task])
                    except:
                        time.sleep(1)
                    else:
                        break
        for task in tasks:
            self.data[task[0]]["intervals"][task[1]]["data"] = await task[2]


    def a_get_data(self, symbols, intervals, limit=200, last_closed=False, volume=True, open_interest=True, moscow=True, time_to_ind=True, direction="decrease", 
                          pf=None, set_pf=False, start=None, end=None):
        asyncio.run(self.agd(symbols, intervals, limit, last_closed, volume, open_interest, moscow, time_to_ind, direction, pf, set_pf, start, end))
                
      
    def alternative_update_data(self, limit=2, collect=False, control=False):
        if self.data:
            for symb in self.symbols:
                for inter in self.intervals:
                    while True:
                        try:
                            last_data = self.get_candles(symb, inter, limit=limit)
                        except:
                            time.sleep(1)
                        else:
                            break
                    if control:
                        display(
                            f"\n=========================== DATA {symb} {inter} ===========================\n", self.data[symb]["intervals"][inter]["data"].head(), "\n", self.data[symb]["intervals"][inter]["data"].tail(), 
                            "\n======================================================================\n","\n#####################\n##### length of data:\n#####", 
                            len(self.data[symb]["intervals"][inter]["data"]), "\n#####################\n",f"\n========================= LAST DATA {symb} {inter} ========================\n", 
                            last_data, "\n======================================================================\n"
                            )

                    if last_data.head(1).index != self.data[symb]["intervals"][inter]["data"].head(1).index:
                        
                        self.data[symb]["intervals"][inter]["data"].loc[last_data.index[0]] = last_data.values[0]
                        self.data[symb]["intervals"][inter]["data"].sort_index(inplace=True, ascending=False)
                        if not collect:
                            self.data[symb]["intervals"][inter]["data"] = self.data[symb]["intervals"][inter]["data"].head(len(self.data[symb]["intervals"][inter]["data"])-1)

                        if control:
                            display(
                                "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n", 
                                f"\n======================= UPDATED DATA {symb} {inter} =======================\n", self.data[symb]["intervals"][inter]["data"].head(), "\n", self.data[symb]["intervals"][inter]["data"].tail(), 
                                "\n======================================================================\n","\n######################\n##### length of data:\n#####", 
                                len(self.data[symb]["intervals"][inter]["data"]), "\n######################\n","\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
                                )
                    else:
                        if not self.params.get("last_closed"):
                            self.data[symb]["intervals"][inter]["data"].iloc[:1] = last_data.head(1)
                            self.data[symb]["intervals"][inter]["data"].iloc[1:2] = last_data.tail(1)
                            if control:
                                print("######################\n###### replaced ######\n######################")


    def data_to_read(self, symbol=None, interval=None):
        with self.data_lock:
            if symbol:
                if interval:
                    return self.data[symbol]["intervals"][interval]["data"].copy()
                else:
                    return self.data[symbol].copy()
            else:
                return self.data.copy()
            
    
    def deals_to_read(self, symbol=None):
        with self.deals_lock:
            if symbol:
                return self.deals.get(symbol, {}).copy()
            else:
                return self.deals.copy()
            

    def handle_public(self, message):
        self.public_mail_queue.append(message)

        
    def sort_public_mail(self):
        while True:
            if not self.public_mail_queue:
                time.sleep(10)
            else:
                msg = self.public_mail_queue.popleft()   
                self.update_data(msg)   
    
    
    def update_data(self, message, collect=False):
        with self.data_lock:
            symb = re.findall(r'\w+USDT$', message["topic"])[0]
            if "tickers" in message["topic"]:
                try:
                    self.data[symb]["high24"] = float(message["data"]["highPrice24h"])
                    self.data[symb]["low24"] = float(message["data"]["lowPrice24h"])
                    self.data[symb]["qty_oi"] = float(message["data"]["openInterest"])
                    self.data[symb]["value_oi"] = float(message["data"]["openInterestValue"])
                    self.data[symb]["volume24"] = float(message["data"]["turnover24h"])
                except:
                    pass
            elif "kline" in message["topic"]:
                try:
                    inter = message["data"][0]["interval"]
                    if symb in self.symbols and inter in self.intervals:
                        data_list = [
                            message["data"][0]["start"],
                            message["data"][0]["open"],
                            message["data"][0]["high"],
                            message["data"][0]["low"],
                            message["data"][0]["close"]
                        ]
                        if self.params.get("volume", True):
                            data_list.append(message["data"][0]["volume"])
                            data_list.append(message["data"][0]["turnover"])
                            columns=["time", "open", "high", "low", "close", "coin_volume", "volume"]
                        else:
                            columns=["time", "open", "high", "low", "close"] 
                        if self.params.get("open_interest", True):
                            data_list.append(self.data[symb]["qty_oi"]) 
                            columns.append("open_interest") 
                        df = pd.DataFrame([data_list])
                        df.columns=columns
                        df = df.astype(float)
                        df["time"] = pd.to_datetime(df["time"], unit="ms")
                        df["time"] = df["time"]+ dt.timedelta(hours=3)
                        last_data = tb.time_to_index(df)

                        if last_data.index != self.data[symb]["intervals"][inter]["data"].head(1).index:
                            self.data[symb]["intervals"][inter]["data"] = pd.concat([last_data, self.data[symb]["intervals"][inter]["data"]])
                            if not collect:
                                self.data[symb]["intervals"][inter]["data"] = self.data[symb]["intervals"][inter]["data"].head(len(self.data[symb]["intervals"][inter]["data"])-1)
                        else:
                            if not self.params.get("last_closed"):
                                self.data[symb]["intervals"][inter]["data"].loc[last_data.index[0]] = last_data.values[0]
                                self.data[symb]["intervals"][inter]["data"].sort_index(inplace=True, ascending=False)
                except Exception as e:
                    pass
                    # frame_print("handle public exception")
                    # frame_print(e)
                else:
                    pass


    def handle_private(self, message):
        self.private_mail_queue.put(message)


    def sort_private_mail(self):

        while True:
            try:
                post = self.private_mail_queue.get_nowait()
            except Empty:
                break

            if post["topic"] == "position":
                for d in post["data"]:
                    symb = d["symbol"]
                    d = {k:v for k,v in d.items() if k in API.position_items}
                    print("check#######")
                    print(d)
                    print("###############")
                    if symb in self.deals: 
                        print("in deals")
                        print(list(self.deals))
                        if d["size"] != "0":
                            print("handle current")
                            d2 = {k:v for k,v in self.deals_to_read(symb).items() if k in API.position_items}
                            if d2 != d:
                                self.handle_current(d, symb)
                        else:
                            print("handle closed")
                            # print(post)
                            if self.handle_just_closed(symb):
                                print(list(self.deals))
                            else:
                                with self.deals_lock:
                                    deal_new = self.deals.pop(symb)
                                # self.closed.append(symb)
                                now = dt.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                                deal_new["closeTime"] = now
                                deal_new["closedPnl"] = "хз"
                                self.deal_news.put(deal_new)                            
                                frame_print(["Position is closed", now], sep="\n")
                                frame_print("Не удалось зафиксировать исход сделки")
                       

            elif post["topic"] == "wallet":
                post_time = dt.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                print("-----------------------------------")
                print("time : " + post_time )
                print("wallet")
                for i in post["data"][-1]["coin"]:
                    coin = i["coin"]
                    if self.balance[coin] != i["walletBalance"]:
                        self.balance[coin] = i["walletBalance"]
                        self.balance[coin+"_position"] = i["totalPositionIM"]
                        self.balance_news=True
                        print(self.balance["USDT"])
                        print(self.balance["USDT_position"])
                print("-----------------------------------")
            else:
                print(post)
    

    def create_order(self, symbol, side, qty, order_type="market", stop_loss=0, take_profit=0, leverage=1, trailing_stop=None, trail_act_price=None, price=None, addition_dict={}):
        
        if not self.api_connection():
            frame_print("Не удалось открыть позицию. Подключение отсутствует.")   
            return False
        try:
            # timestamp = self.get_bybit_time()
            self.sync_system_time()
            result = self.session.place_order( 
                category="linear", 
                symbol=symbol,
                side=side,
                qty=qty,
                orderType=order_type,
                price=price, 
                stopLoss=stop_loss,
                takeProfit=take_profit,
                # timestamp = timestamp
            )
            if result.get("retCode") == 0:
                # time.sleep(1) # чтобы не пришел ответ с нулевой позицией. можно обработать это в get_position, с количеством попыток и паузой, чтобы не застрять там навечно
                frame_print("Позиция открыта")
                self.sort_private_mail()
                self.set_leverage(symbol, leverage)
                if trailing_stop and trail_act_price:
                    self.set_tpsl(symbol=symbol, trailingStop=trailing_stop, activePrice=trail_act_price)
                self.handle_just_opened(symbol, addition_dict)
                return True   
                    
            else:
                frame_print("Не удалось открыть позицию")
                frame_print(result)
                return False
        except exceptions.InvalidRequestError as e:
            frame_print("не удалось открыть позицию")
            frame_print(["Bybit Request Error", e.status_code, e.message], sep=" | ")
            return False
        except exceptions.FailedRequestError as e:
            frame_print("не удалось открыть позицию")
            frame_print(["Request Failed", e.status_code, e.message], sep=" | ")
            return False
        except Exception as e:
            frame_print(["не удалось открыть позицию", e], sep="\n")
            return False
                     
        
    def close_position(self, symbol, side=None, qty=None):
        position = self.deals_to_read(symbol)
        if not position:
            frame_print(f"Не удалось закрыть позицию \nПо монете {symbol} не открыта позиция")
            return False
        else:
            if not side:
                side = "Sell" if position["side"] == "Buy" else "Buy"
            if not qty:
                qty = position["size"]
        
        if not self.api_connection():
            frame_print("Не удалось закрыть позицию")
            return False
            
        try:
            self.sync_system_time()
            # timestamp = self.get_bybit_time()
            result = self.session.place_order(
                    category="linear", 
                    symbol=symbol,
                    side=side,
                    qty=qty,
                    orderType="market",
                    reduce_only=True,
                    # timestamp=timestamp
                )
            if result.get("retCode") == 0:
                frame_print("Позиция закрыта")
                self.handle_just_closed(symbol)
                return True
            else:
                if not self.get_position(symbol):
                    self.handle_just_closed(symbol)
                    frame_print("Позиция закрылась сама")
                    return True
                else:
                    frame_print("Не удалось закрыть позицию")
                    return False
        except:
            frame_print("Не удалось закрыть позицию")
            return False


    def set_tpsl(self, symbol, tp=None, sl=None, trailing_stop=None, trail_act_price=None):

        self.api_connection()
        timestamp = self.get_bybit_time()
        params = {"category": "linear", 
                  "symbol": symbol, 
                  "position_idx":0,                               # 0 — односторонний режим; 1/2 — хедж-режим
                  "tpsl_mode":"Full",
                  "timestamp" : timestamp}                             # режим TP/SL: Full (вся позиция) или Partial (часть)   
        if tp:
            params["takeProfit"] = tp
        if sl:
            params["stopLoss"] = sl
        if trailing_stop and trail_act_price:
            params["trailingStop"] = trailing_stop
            params["activePrice"] = trail_act_price
        
        try:
            res = self.session.set_trading_stop(**params)
            if res.get("retCode") != 0:
                frame_print("Не удалось передвинуть TPSL")
            else:
                frame_print("Передвинули TPSL")
            self.sort_private_mail()
            return res
        except Exception as e:
            frame_print("Не удалось передвинуть TPSL")
            frame_print(e)


    def set_leverage(self, symbol, leverage):
        self.api_connection()
        timestamp = self.get_bybit_time()
        try:
            res = self.session.set_leverage(
                    category="linear",
                    symbol=symbol,
                    buyLeverage=str(leverage),
                    sellLeverage=str(leverage), 
                    timestamp=timestamp
                    )
            if res.get("retCode") != 0:
                frame_print("Не удалось поменять плечо")
            else:
                frame_print(f"Значение плеча изменено на {leverage}")
            self.sort_private_mail()
            return res
        except Exception as e:
            frame_print("Не удалось поменять плечо")
            frame_print(e)

        
    def get_deals(self, history): 
        history = history[-20:] 
        self.api_connection()      
        timestamp = self.get_bybit_time()
        res = self.session.get_positions(category="linear", settleCoin="USDT", timestamp=timestamp)
        for i in res["result"]["list"]:
            i["entryPrice"] = i.pop("avgPrice")
            open_id = "_".join([i["symbol"], i["entryPrice"], i["size"]])
            position = {k:v for k, v in i.items() if k in API.position_items}
            position["openId"] = open_id
            position["closedPnl"] = ""
            position["timeframe"] = ""
            for j in history:
                if j["openId"] == open_id:
                    position = position|j
                    break
            deal_new = position
            self.deal_news.put(deal_new)
            with self.deals_lock:
                self.deals[i["symbol"]] = position
            

    def get_position(self, symbol):
        try:
            self.api_connection()
            timestamp = self.get_bybit_time()
            res = self.session.get_positions(
                category="linear", 
                symbol=symbol, 
                timestamp=timestamp
                )
            position = res["result"]["list"][0]
            if not position["size"]:
                return {}
            position["entryPrice"] = position.pop("avgPrice")
            position = {k:v for k,v in position.items() if k in API.position_items + ["unrealisedPnl"]}
            # frame_print("check get_position_return")
            # frame_print(position)
            return position
        except:
            print("error in get_position")
    

    def handle_just_opened(self, symbol, addition_dict):
        position = self.get_position(symbol)
        position.pop("unrealisedPnl")
        position = position | addition_dict
        now = dt.datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")
        position["openTime"] = now
        open_id = "_".join([symbol, position["entryPrice"], position["size"]])
        position["openId"] = open_id
        deal_new = position.copy()
        self.deal_news.put(deal_new)
        with self.deals_lock:
            self.deals[symbol] = position
        frame_print(["Position is open", now], sep="\n")
        frame_print(position)
    

    def get_closed_deals(self, qty=5):
        self.api_connection()
        # timestamp = self.get_bybit_time()
        res = self.session.get_closed_pnl(
            category="linear", 
            limit=qty, 
            # timestamp=timestamp
            )
        positions = {}
        for i in res["result"]["list"]:
            i["closeTime"] = i.pop("updatedTime")
            i["closeId"] = "_".join([i["symbol"], i["closeTime"]])
            open_id = "_".join([i["symbol"], i["avgEntryPrice"], i["qty"]])
            # print(i)
            positions[open_id] = {k:v for k, v in i.items() if k in API.closed_position_items and k != "updatedTime"}
        return positions
    
    
    def handle_just_closed(self, symbol, retries=5):

        self.sync_system_time()
        for j in range(retries):
            closed = self.get_closed_deals(5)
            for i in closed:
                print(i)
                if i.split("_")[0] == symbol:
                    position = self.deals_to_read(symbol)
                    if i == position["openId"]:
                        print(position)
                        # positions[i]["closeTime"] = pd.to_datetime(positions[i]["closeTime"], unit='ms')#, errors='coerce')
                        closed[i]["closeTime"] = str(pd.to_datetime(pd.to_numeric(closed[i]["closeTime"]), unit='ms') + dt.timedelta(hours=3))  # to_numeric добавил, ибо вылезает предупреждение, что в будущих версиях не будут переводить в datetime str
                        print(closed[i])
                        ofee = float(closed[i].pop("openFee"))
                        cfee = float(closed[i].pop("closeFee"))
                        closed[i]["fee"] = str(ofee + cfee)
                        print(position)
                        position = position | closed[i]
                        print(position)
                        deal_new = position.copy()
                        self.deal_news.put(deal_new)
                        with self.deals_lock:
                            self.deals.pop(symbol)
                        # self.closed.append(symbol)
                        now = dt.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                        frame_print(["Position is closed", now], sep="\n")
                        frame_print(position)
                        return True
            time.sleep(1)
        return False
            

    def handle_current(self, update_dict, symbol=None):
        if not symbol:
            symbol = update_dict["symbol"]
        position = self.deals_to_read(symbol)
        print_dict = {k:v for k, v in update_dict.items() if position[k] != v or position[k] == "symbol"}
        position = position | update_dict
        deal_new = position.copy()
        self.deal_news.put(deal_new)
        with self.deals_lock:
            self.deals[symbol] = position
        now = dt.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        frame_print(["Position changed", now], sep="\n")
        frame_print(print_dict)


    def check_symb(self, symbol):
        try:
            self.session.get_kline(category="linear",
                              symbol=symbol,
                              interval=1,
                              limit=1)
            return True
        except:
            return False
        

    def get_symbol_list(self):
        timestamp = self.get_bybit_time()
        r = self.session.get_instruments_info(category="linear", limit=1000, timestamp=timestamp)["result"]["list"]
        l = [x["symbol"] for x in r if re.findall(r'\w+USDT$', x["symbol"])]
        return l


    def check_balance(self):
        timestamp = self.get_bybit_time()
        balance_mess = self.session.get_wallet_balance(accountType="UNIFIED", timestamp=timestamp)
        balance = balance_mess["result"]["list"][0]
        self.all_actives_in_usd = balance['totalEquity']
        self.all_usd_actives = balance['totalAvailableBalance']
        self.balance = {}
        for c in balance['coin']:
            self.balance[c["coin"]] = c["walletBalance"]

        self.balance["all actives in USD equivalent"] = self.all_actives_in_usd
        self.balance["all USD actives"] =  self.all_usd_actives
        frame_print(self.balance)



    
    


    






