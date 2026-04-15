from pybit.unified_trading import HTTP 
from pybit.unified_trading import WebSocket
from pybit import exceptions
import pandas as pd
import numpy as np
import datetime as dt
import time 
import re
from IPython.display import display
from func import tables as tb
from pprint import pprint
import asyncio


class API():
    # intervals = ["1", "5", "15", "60","120", "240", "D", "W", "M"]
    intervals = ["5", "15", "60"]
    oi_intervals = ["5min", "15min", "1h"]
    ignored_symbols = []
    position_list = ['symbol', 'side', 'size', 'entryPrice', "leverage", 'positionValue', 'takeProfit', 'stopLoss', 'trailingStop', 'createdTime', 'updatedTime', 'tpslMode', 'liqPrice', 'breakEvenPrice', 'isReduceOnly', 'positionStatus', 'curRealisedPnl', 'cumRealisedPnl']

    def __init__(self, api_key=None, secret_key=None, demo=True, websocket=True):

        self.private_mail = []
        self.deals = {}
        self.deal_news = False
        self.balance_news = False

        
        self.client = HTTP(
            api_key=api_key,
            api_secret=secret_key,
            testnet=False,
            max_retries=200,
            retry_delay=3,
            demo=demo,
            # recv_window=60000
        )

        self.get_data_dict()
        self.all_symbols = list(self.data)
        
        if websocket:
            self.ws = WebSocket(
                testnet=False,
                channel_type="linear",
                retries=200,
                restart_on_error=True,
            )
            
            for symb in self.get_symbol_list():
                self.ws.ticker_stream(
                        symbol=symb,
                        callback=self.handle_message
                    )
                for inter in API.intervals:
                    self.ws.kline_stream(
                        interval=inter,
                        symbol=symb,
                        callback=self.handle_message
                        ) 
            self.private_ws = WebSocket(
                testnet=False,
                channel_type="private",
                api_key=api_key,
                api_secret=secret_key,
                retries=200,
                restart_on_error=True
            )
            self.private_ws.position_stream(callback=self.private_handle)
            self.private_ws.order_stream(callback=self.private_handle)
            self.private_ws.wallet_stream(callback=self.private_handle)
            self.private_ws.execution_stream(callback=self.private_handle)



    def private_handle(self, message):
        self.private_mail.append(message)
        


    
    def sort_private_mail(self):
        if self.private_mail:
            for i in range(len(self.private_mail)):
                post_time = pd.to_datetime(self.private_mail[0]["creationTime"], unit="ms").strftime("%d.%m.%Y %H:%M:%S")
                if self.private_mail[0]["topic"] == "position":
                    for j in self.private_mail[0]["data"]:
                        symb = j["symbol"] 
                        # creation_time = j["createdTime"] # лишняя переменная
                        d = {k:v for k,v in j.items() if k in API.position_list}
                        # d["createdTime"] = pd.to_datetime(d["createdTime"], unit="ms").strftime("%d.%m.%Y %H:%M:%S")
                        if symb in list(self.deals):
                            if d["size"] != "0":
                                if self.deals[symb] != d:
                                    print_dict = {k:v for k, v in d.items() if self.deals[symb][k] != v}
                                    self.deals[symb] = self.deals[symb]| d
                                    self.deal_news = True
                                    print("-----------------------------------")
                                    print("time : " + post_time )
                                    print("position")
                                    print(symb)
                                    for k, v in print_dict.items():
                                        print(f"{k} : {v}")
                                    print("----------------------------------")
                            else:
                                self.deals.pop(symb)
                                self.deal_news = True
                                print("-----------------------------------")
                                print("time : " + post_time )
                                print("position")
                                print(symb)
                                print("the deal is closed")
                                print("----------------------------------")
                        else:
                            print("-----------------------------------")
                            print("time : " + post_time )
                            print("position")
                            print(symb)
                            if d["size"] != "0":
                                self.deals[symb] = d
                                self.deal_news=True
                                for k, v in self.deals[symb].items():
                                    print(f"{k} : {v}")
                            else:
                                # self.closed_deals[symb + "_" +d["createdTime"]] = d            
                                print("the deal is closed")
                            print("----------------------------------")
                            self.deal_news = True

                elif self.private_mail[0]["topic"] == "wallet":
                    print("-----------------------------------")
                    print("time : " + post_time )
                    print("wallet")
                    for j in self.private_mail[0]["data"][-1]["coin"]:
                        coin = j["coin"]
                        if self.balance[coin] != j["walletBalance"]:
                            self.balance[coin] = j["walletBalance"]
                            self.balance[coin+"_position"] = j["totalPositionIM"]
                            self.balance_news=True
                            print(self.balance["USDT"])
                            print(self.balance["USDT_position"])
                    print("----------------------------------")
                else:
                    print(self.private_mail[0])
               
                self.private_mail.pop(0)

            

    def get_data_dict(self):
        while True:
            try:
                l = self.client.get_instruments_info(category="linear", limit=1000)["result"]["list"]
                d = {x["symbol"] : 
                     {
                         "price_scale": int(x["priceScale"]), 
                         "min_qty":float(x["lotSizeFilter"]["minOrderQty"]), 
                         "qty_step":float(x["lotSizeFilter"]["qtyStep"])
                     } for x in l if re.findall(r'\w+USDT$', x["symbol"]) and x["symbol"] not in self.ignored_symbols}
                l = self.client.get_tickers(category="linear")["result"]["list"]
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
                
                self.data={k:d[k]|d2[k] for k in list(d)}
            except:
                time.sleep(1)
            else:
                break
        


    def get_candles(self, symbol, interval, limit, start=None, end=None):

        candles = self.client.get_kline(category="linear", 
                            symbol=symbol.upper(), 
                            interval=interval,
                            start=start,
                            end=end,
                            limit=limit)["result"]["list"]
        

        try:
            self.params.get("test")
        except:
            self.params = {}
        
        if self.params.get("open_interest", True):
            oi = self.client.get_open_interest(
                category="linear",
                symbol=symbol.upper(),
                intervalTime=API.oi_intervals[API.intervals.index(interval)],
                limit=limit
                )["result"]["list"]
            
            oi = [list(x.values()) for x in oi]
            oi = pd.DataFrame(oi, columns=["open_interest", "time"])
            oi = oi.astype(float)
            oi["time"] = pd.to_datetime(oi["time"], unit="ms")
            oi["time"] = oi["time"]+ dt.timedelta(hours=3)
            oi = tb.time_to_index(oi)

        if self.params.get("last_closed", False):
            df = pd.DataFrame(candles[1:])    
        else:
            df = pd.DataFrame(candles)
        if self.params.get("volume", True):
            df = df.iloc[:,:7]
            # df = df.drop(5, axis=1)
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
        try:
            df = pd.concat([df, oi], axis=1)
        except:
            pass
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
            # symb_dict = {}
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
                  open_interest=True, moscow=True, time_to_ind=True, 
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
                
      
    def update_data(self, limit=2, collect=False, control=False):

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


    def handle_message(self, message, collect=False):
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
                    data_list = [message["data"][0]["start"],
                                message["data"][0]["open"],
                                message["data"][0]["high"],
                                message["data"][0]["low"],
                                message["data"][0]["close"]]
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
            except:
                pass
        else:
            print(message)

    
    
    def create_order(self, symbol, side, qty, order_type, stop_loss, take_profit=0, price=None, trailing_stop=False, trail_act_price=False):
        try: 
            result = self.client.place_order(
                category="linear", 
                symbol=symbol,
                side=side,
                qty=qty,
                orderType=order_type,
                price=price, 
                stopLoss=stop_loss,
                takeProfit=take_profit,
                leverage =  2,
            )
            if trailing_stop and trail_act_price:
                response = self.client.set_trading_stop(
                    category="linear",
                    symbol=symbol,
                    trailingStop=trailing_stop,
                    activePrice=trail_act_price,
                    position_idx=0,                          # 0 — односторонний режим; 1/2 — хедж-режим
                    tpsl_mode="Full"                         # режим TP/SL: Full (вся позиция) или Partial (часть)
                    )


        except exceptions.InvalidRequestError as e:
            print("Bybit Request Error", e.status_code, e.message, sep=" | ")
        except exceptions.FailedRequestError as e:
            print("Request Failed", e.status_code, e.message, sep=" | ")
        except Exception as e:
            print(e)
        else:
            return result
        


    def check_symb(self, symbol):
        try:
            self.client.get_kline(category="linear",
                              symbol=symbol,
                              interval=1,
                              limit=1)
            return True
        except:
            return False
        
    def get_symbol_list(self):
        while True:
            try:
                r = self.client.get_instruments_info(category="linear", limit=1000)["result"]["list"]
                # l = [x["symbol"] for x in r]
                l = [x["symbol"] for x in r if re.findall(r'\w+USDT$', x["symbol"])]
                # l = l = [x["symbol"] for x in r if x["symbol"][0] == "A"]
                return l
            except:
                time.sleep(1)

    def check_balance(self):
        balance_mess = self.client.get_wallet_balance(accountType="UNIFIED")
        balance = balance_mess["result"]["list"][0]
        self.all_actives_in_usd = balance['totalEquity']
        self.all_usd_actives = balance['totalAvailableBalance']
        self.balance = {}
        for c in balance['coin']:
            self.balance[c["coin"]] = c["walletBalance"]

        self.balance["all actives in USD equivalent"] = self.all_actives_in_usd
        self.balance["all USD actives"] =  self.all_usd_actives
        
        print(self.balance)

    def get_one(self, symbol, interval):
        return self.data[symbol][interval]["data"]




# for i in cl.data:
#     df = cl.data[i][1]["data"]
#     print(df.head())
#     df["5m_time"] = df[df["time"].dt.minute%5==0]["time"]
#     df["5m_time"] = df["5m_time"].fillna(method="bfill")
#     df["15m_time"] = df[df["time"].dt.minute%15==0]["time"]
#     df["15m_time"] = df["15m_time"].fillna(method="bfill")
#     vol5 = df.groupby("5m_time").agg(
#         {
#             "open" : "last",
#             "high" : "max",    
#             "low" : "min",
#             "close" : "first",
#             "volume" : "sum"
            
#         }
#     ).iloc[::-1]

#     vol15 = df.groupby("15m_time").agg(
#         {
#             "open" : "last",
#             "high" : "max",
#             "low" : "min",
#             "close" : "first",
#             "volume" : "sum"
            
#         }
#     ).iloc[::-1]
#     print(vol5.head())
#     print(vol15.head())




