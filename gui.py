import tkinter as tk
import strategy as st
import visualization as vn
import matplotlib.pyplot as plt
import matplotlib.backends.backend_tkagg as bt
from window import Window as wn
import numpy as np
import pandas as pd
from func import tables as tb
import re
import datetime as dt
from functools import partial
import time
import json
import os
from ctypes import windll



class GUI():
    app_name = "SUPER-DUPER BOT ULTIMATE-3000"
    # app_width = 1600
    # app_height = 800
    chart_length = 200
    grid_rows = 12
    grid_cols = 12
    modes = ["view", "trade", "edit"]
    history_items = {"identification_time": "Время", 
                    "symbol": "Монета", 
                    "timeframe": "Таймфрейм", 
                    "side": "Направление", 
                    "entryPrice": "Цена Входа", 
                    "identification_price": "Обнаружено при цене", 
                    "difference": "Скачок объема", 
                    "natr": "NATR", 
                    "stopLoss": "Stop loss", 
                    "takeProfit": "Take profit", 
                    "size": "Размер ордера", 
                    "positionValue": "Размер ордера в $", 
                    "breakEvenPrice": "Безубыток",
                    "leverage": "Плечо", 
                    "trailingStop": "Traling stop"}



    def __init__(self, client, settings_path):

        self.client = client
        self.settings_path = settings_path
        self.mode = "view"
        self.trading = False
        self.vol_sorted = False
        self.vol_cut = False
        self.new_deals = {}
        self.history = {}

        with open(self.settings_path, "r", encoding="utf-8") as f:
            self.settings = json.load(f) 
# стратегия------
        self.strategy = st.Strategy(self.settings.get("last_strategy", None))
        if self.strategy.name not in st.Strategy.get_strat_list():
            self.strategy.name = None 
# ---------------
        if self.strategy.name:
            self.indicators = self.strategy.strategy_dict["indicators"]
            self.history_path = self.settings_path.rstrip("settings.json")+self.strategy.name+"/history.json"
            try:
                with open(self.history_path, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except:
                print("нет истории")
        else:
            self.indicators = self.settings.get("last_indicators", {})
        if not all(item in list(st.Strategy.indicators) for item in list(self.indicators)):
            self.indicators = {k:v for k, v in self.indicators.items() if k in list(st.Strategy.indicators)}

        self.window = tk.Tk()

        self.window.title(GUI.app_name)
        
        dpi = windll.user32.GetDpiForWindow(self.window.winfo_id())
        self.dpi_coef = int(dpi/96)
        self.sf =("TkMenuFont", 8 * self.dpi_coef)
        self.mf = 12 * self.dpi_coef
        self.lf = 20 * self.dpi_coef
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        self.app_width = int(screen_width*self.dpi_coef/4*3)
        self.app_height = int(screen_height*self.dpi_coef/3*2)

        x = int((screen_width*self.dpi_coef/2) - self.app_width/2)
        y = int((screen_height*self.dpi_coef/2) - self.app_height/2)
        self.window.geometry(f"{self.app_width}x{self.app_height}+{x}+{y}")

        for i in range(GUI.grid_rows):
            self.window.rowconfigure(i, weight=1)
        for i in range(GUI.grid_cols):
            self.window.columnconfigure(i, weight=1)

        if self.indicators:
            self.add_winds = len([x for x in [self.indicators[x]["chart"] for x in list(self.indicators)] if x == "add"])
        else:
            self.add_winds = 0

        self.widgets = []
        self.volatility_rate()
        self.make_menu()
        self.fill_menu()
        self.make_widgets()
        self.live_chart(vn.Visualization(params={"add_windows" : self.add_winds}))

        # диагностика
        print(f"Ширина экрана: {self.window.winfo_screenwidth()}")
        print(f"Высота экрана: {self.window.winfo_screenheight()}")
        print(f"Масштаб Tk: {self.window.tk.call('tk', 'scaling')}")
        try:
            
            dpi = windll.user32.GetDpiForWindow(self.window.winfo_id())
            print(f"DPI окна: {dpi}")
        except:
            print("DPI: недоступно (не Windows или старая версия)")
        print(f"Геометрия окна: {self.window.geometry()}")



    def make_menu(self):
        try:
            self.main_menu.delete(0,"end")
        except:
            pass

        self.main_menu = tk.Menu(self.window)
        self.window.config(menu=self.main_menu)

        self.symbol_menu = tk.Menu(self.main_menu, tearoff=0, postcommand=self.fill_symbol_menu)
        self.main_menu.add_cascade(label="Symbol", menu=self.symbol_menu)

        self.timeframe_menu = tk.Menu(self.main_menu, tearoff=0)
        self.main_menu.add_cascade(label="Timeframe", menu=self.timeframe_menu)

        self.strategy_menu = tk.Menu(self.main_menu, tearoff=0)
        self.main_menu.add_cascade(label="Strategy", menu=self.strategy_menu)

        self.indicator_menu = tk.Menu(self.main_menu, tearoff=0)
        self.main_menu.add_cascade(label="Indicator", menu=self.indicator_menu)

        self.mode_menu = tk.Menu(self.main_menu, tearoff=0)
        self.main_menu.add_cascade(label="Mode", menu=self.mode_menu)
        if not self.vol_sorted:
            self.main_menu.add_command(label="сортировать по волатитьности", command= self.volatility_sort_on_off)
        else:
            self.main_menu.add_command(label="отменить сортировку", command= self.volatility_sort_on_off)



    def fill_menu(self, timeframe=True, indicator=True, strategy=True, mode=True):

        if timeframe:
            for i in self.client.intervals:
                self.timeframe_menu.add_command(label=i, command=partial(self.set_timeframe, i))

        if strategy:
            for i in st.Strategy.get_strat_list():
                self.strategy_menu.add_command(label=i, command=partial(self.set_strategy, i))

        if indicator:
            for i in list(st.Strategy.indicators):
                self.indicator_menu.add_command(label=i, command=partial(self.set_indicator, i))
        
        if mode:
            for i in GUI.modes:
                self.mode_menu.add_command(label=i,command=partial(self.set_mode, i))

    
    
    def fill_symbol_menu(self):
        self.symbol_menu.delete(0, "end")    
        if self.vol_sorted:
            self.volatility_rate()
            if len(self.volatility) > 0:
                for i in range(len(self.volatility)):
                    j = self.volatility["symbol_natr"][i]
                    if self.volatility["symbol"][i] in self.strategy.strategy_dict["symbols"]:
                        self.symbol_menu.add_command(label=j, foreground="white", background="black", font=self.sf, command=partial(self.set_symbol, j))
                    else:
                        if not self.mode=="trade":
                            self.symbol_menu.add_command(label=j, font=self.sf, command=partial(self.set_symbol, j))
        else:
            for i in [x for x in self.strategy.strategy_dict["symbols"] if x in self.client.symbols]:
                self.symbol_menu.add_command(label=i, foreground="white", background="black", font=self.sf, command=partial(self.set_symbol, i))
            if not self.mode == "trade":
                for i in [x for x in self.client.symbols if x not in self.strategy.strategy_dict["symbols"]]: 
                    self.symbol_menu.add_command(label=i, font=self.sf, command=partial(self.set_symbol, i))



    def make_widgets(self):

        if self.widgets:
            for widget in self.widgets:
                widget.destroy()
        if self.mode == "trade":
            self.output_window = tk.Text(self.window, bd=3, width=30)
            self.output_window.grid(row=2, column=10, columnspan=2, rowspan=10, sticky="nsew")
            self.widgets.append(self.output_window)
            if self.history:
                text = ""
                for i in list(self.history):
                    if "symbol" in list(self.history[i]):
                        print_dict = {v:self.history[i][k] if k in list(self.history[i]) else "не зафиксировано" for k, v in self.history_items.items()}
                    else:
                        print_dict = self.history[i]
                    text+="\n\n------------------------------\n"+"\n".join([k+" : "+ v for k, v in print_dict.items()])
                self.output_window.insert(index=tk.END, chars=text)
                self.output_window.see("end")

            self.balance = self.client.balance["USDT"]
            self.money_info = tk.Label(self.window, text=f"Баланс:  {self.balance}", wraplength=self.app_width/6.5, 
                                       background="blue", anchor="w", font=40)
            self.money_info.grid(row = 9, column=0, sticky="nsew")
            self.widgets.append(self.money_info)
            if self.trading:
                text = "Стоп"
            else:
                text="Торговать"
            self.start_stop_button = tk.Button(self.window, text=text, font=28, command=self.trade_on_off)
            self.start_stop_button.grid(row=0, column=8, sticky="nsew")
            self.widgets.append(self.start_stop_button)

            self.history_label = tk.Label(self.window, text = "История сделок", font=20)
            self.history_label.grid(row=1, column=10, columnspan=2, sticky="nsew")
            self.widgets.append(self.history_label)

        # elif self.mode == "edit":
            if not self.vol_cut:
                self.volty_button = tk.Button(self.window, text = "отобрать волатильные монеты", wraplength=self.app_width/12.5, command= self.vol_cut_on_off)
            else:
                self.volty_button = tk.Button(self.window, text = "оставить текущие монеты", wraplength=self.app_width/12.5, command= self.vol_cut_on_off)
            self.volty_button.grid(row=0, column=7, sticky="nsew")
            self.widgets.append(self.volty_button)

        self.status_label = tk.Label(self.window, text=f"Текущая стратегия:    ={self.strategy.name}=,     Бот в режиме:    ={self.mode}=", font=20)
        self.status_label.grid(row=0, column=0, columnspan=4, rowspan=1, sticky="nsw")#.pack(side="left", anchor="nw")
        if self.trading:
            self.trading_status_label = tk.Label(self.window, text="Бот Торгует", foreground = "red", background="black", font=28)
        else:
            self.trading_status_label = tk.Label(self.window, text="Бот Не Торгует", foreground = "black", background="blue", font=28)
        self.trading_status_label.grid(row=0, column=9, columnspan=1, rowspan=1, sticky="nsew", padx=5)#.pack(side="right", anchor="ne")
        self.widgets.append(self.status_label)
        self.widgets.append(self.trading_status_label)
        

    def live_chart(self, chart):

        self.chart = chart  
        self.chart.symbol = self.settings.get("last_symbol", self.client.symbols[0])
        if self.chart.symbol not in self.client.symbols:
            self.chart.symbol = self.client.symbols[0]
        self.chart.timeframe = self.settings.get("last_timeframe", self.client.intervals[0])
        if self.chart.timeframe not in self.client.intervals:
            self.chart.timeframe = self.client.intervals[0]

        self.settings["last_strategy"] = self.strategy.name
        self.settings["last_symbol"] = self.chart.symbol
        self.settings["last_timeframe"] = self.chart.timeframe
        self.settings["last_indicators"] = self.indicators

        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=4, ensure_ascii=False)

        if self.chart.symbol and self.chart.timeframe:
            self.chart.add_candles(self.client.data, symbol=self.chart.symbol, timeframe=self.chart.timeframe)
            for i in list(self.history)[100:]:
                if self.history[i].get("symbol", "") == self.chart.symbol:
                    try:
                        self.chart.add_plot(data=[float(self.history[i]["entryPrice"]), float(self.history[i]["stopLoss"]), float(self.history[i]["takeProfit"])], 
                                            chart="main", 
                                            chart_type="hlines",
                                            colors=["black", "red", "green" ], 
                                            linewidth=0.5, 
                                            transparency=0.6, 
                                            titles=[self.history[i]["side"], "stop loss", "take profit"], 
                                            xmins=[pd.to_datetime(self.history[i]["identification_time"], dayfirst=True)]*3
                                            )
                    except:
                        pass
            if self.strategy.name:
                self.strategy.calculate_strategy(self.client.data, self.chart.symbol)     
                for i in list(self.strategy.indi_dict):
                    self.chart.add_plot(**(self.strategy.indicators[i]|self.strategy.indi_dict[i]))

            self.chart.visualize()

            self.canvas = bt.FigureCanvasTkAgg(self.chart.fig, self.window)
            self.canvas.get_tk_widget().grid(row=2, column=0, columnspan=10, rowspan=6, sticky="nsew")
            self.update_chart()


    def update_chart(self):
        if not self.client.client:
            self.client.api_connection(self.settings["api_key"], self.settings["secret_key"], self.client.demo)
        if not self.client.is_ws_connect(self.client.public_ws):
            self.client.public_ws_connection()
        if not self.client.is_ws_connect(self.client.private_ws):
            self.client.private_ws_connection(self.settings["api_key"], self.settings["secret_key"])
        for ax in self.chart.axis_list:
            ax.clear()
        self.chart.add_candles(self.client.data, symbol=self.chart.symbol, timeframe=self.chart.timeframe)
        for i in list(self.history)[-100:]:
            if self.history[i].get("symbol", "") == self.chart.symbol:
                try:
                    self.chart.add_plot(data=[float(self.history[i]["entryPrice"]), float(self.history[i]["stopLoss"]), float(self.history[i]["takeProfit"])], 
                                        chart="main", 
                                        chart_type="hlines",
                                        colors=["black", "red", "green" ], 
                                        linewidth=0.5, 
                                        transparency=0.6, 
                                        titles=[self.history[i]["side"], "stop loss", "take profit"], 
                                        xmins=[pd.to_datetime(self.history[i]["identification_time"], dayfirst=True)]*3
                                            )
                except:
                    pass
        if self.strategy.name:
            if self.trading:
                self.cut_by_volatility()
            self.strategy.calculate_strategy(self.client.data, self.chart.symbol)
            self.trade()
            
            for i in list(self.strategy.indi_dict):
                self.chart.add_plot(**(self.strategy.indicators[i]|self.strategy.indi_dict[i]))
            
        self.chart.visualize()
        plt.draw()
        self.window.after(ms=5000, func=self.update_chart)



    def set_symbol(self, symbol):
        self.chart.symbol = re.split(r"\s+", symbol)[0]
        plt.draw()
        self.settings["last_symbol"] = self.chart.symbol
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=4, ensure_ascii=False)
        


    def set_timeframe(self, timeframe):
        self.chart.timeframe = timeframe
        plt.draw()
        self.settings["last_timeframe"] = self.chart.timeframe
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=4, ensure_ascii=False)
        


    def set_strategy(self, name):
        self.strategy = st.Strategy(name)
        self.indicators = self.strategy.strategy_dict["indicators"]
        self.history_path = self.settings_path.rstrip("settings.json")+self.strategy.name+"/history.json"
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                self.history = json.load(f)
        except:
            print("нет истории")
        self.make_menu()
        self.fill_menu()
        self.make_widgets()
        if self.add_winds != len([x for x in [self.indicators[x]["chart"] for x in list(self.indicators)] if x == "add"]):
            self.add_winds = len([x for x in [self.indicators[x]["chart"] for x in list(self.indicators)] if x == "add"])
            self.canvas.get_tk_widget().destroy()
            self.live_chart(vn.Visualization(params={"add_windows":self.add_winds}))
        plt.draw()
        self.settings["last_strategy"] = self.strategy.name
        self.settings["last_indicators"] = self.indicators

        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=4, ensure_ascii=False)



    def set_indicator(self, indicator):
        pass

    

    def set_mode(self, mode):
        self.mode = mode
        self.make_widgets()



    def volatility_sort_on_off(self):
        if self.vol_sorted:
            self.vol_sorted = False
        else:
            self.vol_sorted = True
        self.make_menu()
        self.fill_menu()
        # self.fill_symbol_menu()
    


    def vol_cut_on_off(self):
        if not self.vol_cut:
            try:
                w = wn("Отсечь по волатильности", main_label="Введи количество", entry=True, exit="ok", root=self.window)
                self.vol_cut=int(w.entered_value)
                self.cut_by_volatility()
            except: 
                print("отмена")
                return
            
        else:
            self.vol_cut = False
        self.make_menu()
        self.fill_menu()
        # self.fill_symbol_menu()
        self.make_widgets()



    def volatility_rate(self):
        if "5" in self.client.intervals:
            df = []
            for symb in self.client.symbols:
                natr = GUI.natr(self.client.data[symb]["intervals"]["5"]["data"])
                self.client.data[symb]["natr"] = natr
                l = [symb, natr]
                df.append(l)
            df = pd.DataFrame(df, columns=["symbol", "natr"])
            df["symbol_natr"] = df["symbol"] + " " + df["natr"].astype(str)
            df = df.sort_values(by="natr", ascending=False).reset_index(drop=True)
            self.volatility = df
        else:
            self.volatility = pd.DataFrame(columns=["symbol", "natr", "symbol_natr"])



    def cut_by_volatility(self):
        if self.vol_cut:
            self.volatility_rate()
            if len(self.volatility) > 0:
                self.strategy.change_strategy(symbols=[x for x in self.volatility["symbol"][:self.vol_cut]])



    def natr(data, period=14):
        df=data.copy()
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        atr = df['tr'][:period].mean()
        current_close = df['close'][0]
        natr = (atr / current_close) * 100
        return round(natr, 2)
    
    

    def trade_on_off(self):
        if self.trading:
            self.trading=False
            self.strategy.stg.trade_dict={}
            message = "\n-------------------\n------stop trading-----\n"
        else:
            self.trading = True
            message = "\n-------------------\n-----start trading-----\n"
        now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.history[time.time()] = {"time": now, "trading": message}
        try:
            if not os.path.exists(self.settings_path.rstrip("settings.json")+self.strategy.name):
                os.mkdir(self.settings_path.rstrip("settings.json")+self.strategy.name)
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=4, ensure_ascii=False)
        except:
            print("отсутствует стратегия")
        self.make_widgets()



    def trade(self):
        if self.trading:
            if self.client.balance_news:
                self.make_widgets()
                self.client.balance_news=False
            # if self.client.deal_news:
                

            for symb in self.strategy.strategy_dict["symbols"]:
                for inter in self.strategy.strategy_dict["timeframes"]:
                    if inter == "15":
                        natr = GUI.natr(self.client.data[symb]["intervals"]["15"]["data"]) 
                    else:
                        natr = self.client.data[symb]["natr"]
                    deal = self.strategy.stg.trade(self.client, self.strategy, symb, inter, natr, 14, 0, 1, 1)
                    if deal:
                        if symb in list(self.client.deals):
                            position = self.client.get_deals(symb)
                            if position["side"] != deal["side"]:
                                k = symb + "_" + position["entryPrice"]+position["size"]
                                h_position = self.history[k]
                                if (inter == "15" or (inter == "5" and h_position["timeframe"] == "5")) and float(position["unrealisedPnl"]) > 0:
                                    side = "Buy" if position["side"] == "Sell" else "Sell"
                                    try:
                                        self.client.create_order(symbol=position["symbol"], side=side, qty=position["size"], leverage=1)
                                        while not self.client.private_mail:
                                            time.sleep(0.1)
                                        self.client.sort_private_mail()
                                        if symb not in list(self.client.deals):
                                            print("----------------------------------------------")
                                            print("Перезаход")
                                            try:
                                                self.order = self.client.create_order(
                                                    symbol=symb, side=deal["side"], 
                                                    qty=deal["deal_price"], 
                                                    order_type=self.strategy.strategy_dict["order_type"], 
                                                    stop_loss=deal["stop_loss"], 
                                                    # trailing_stop= deal["trailing_stop"], 
                                                    # trail_act_price=deal["trail_act_price"], 
                                                    take_profit=deal["take_profit"])
                                                while not self.client.private_mail:
                                                    time.sleep(0.1)
                                                self.client.sort_private_mail()
                                                if symb in list(self.client.deals):
                                                    self.new_deals[symb]=deal
                                                    print("перезашли")
                                                difference = float(self.client.deals[symb]["entryPrice"]) - float(deal["identification_price"])
                                                if difference != 0:
                                                    stop_loss = str(float(deal["stop_loss"])+difference)
                                                    take_profit = str(float(deal["take_profit"])+difference)
                                                    try:
                                                        self.client.set_tpsl(symbol=symb, tp=take_profit, sl=stop_loss)#, trail_act_price=trail_act_price, trailing_stop=trailing_stop)
                                                        print("передвинули tpsl")
                                                    except:
                                                        print("не получилось передвинуть tpsl")
                                            except:
                                                print("не получилось перезайти. сделка отменена")
                                    except:
                                        self.client.sort_private_mail()
                                        if symb in list(self.client.deals):
                                            print("не удалось отменить сделку")
                                        else:
                                            print("сделка завершилась сама")
                                        
                        elif symb not in list(self.client.deals) and len(list(self.client.deals)) < 5:
                            print("----------------------------------------------")
                            print("deal")
                            self.new_deals[symb]=deal
                            try:
                                self.order = self.client.create_order(
                                    symbol=symb, side=deal["side"], 
                                    qty=deal["deal_price"], 
                                    order_type=self.strategy.strategy_dict["order_type"], 
                                    stop_loss=deal["stop_loss"], 
                                    # trailing_stop= deal["trailing_stop"], 
                                    # trail_act_price=deal["trail_act_price"], 
                                    take_profit=deal["take_profit"])
                    
                                while not self.client.private_mail:
                                        time.sleep(0.1)
                                self.client.sort_private_mail()
                                if symb in list(self.client.deals):
                                    self.new_deals[symb]=deal
                                    print("позиция открыта")
                            
                                difference = float(self.client.deals[symb]["entryPrice"]) - float(deal["identification_price"])
                                if difference != 0:
                                    stop_loss = str(float(deal["stop_loss"])+difference)
                                    take_profit = str(float(deal["take_profit"])+difference)
                                    try:
                                        self.client.set_tpsl(symbol=symb, tp=take_profit, sl=stop_loss)#, trail_act_price=trail_act_price, trailing_stop=trailing_stop)
                                        print("Передвинули tpsl")
                                    except:
                                        print("не удалось передвинуть tpls")
                            except:
                                print("не удалось открыть позицию")
                    
                    self.client.sort_private_mail()
                    if self.client.deal_news:
                        self.update_history()



    def update_history(self):
        d = {k+"_"+self.client.deals[k]["entryPrice"]+self.client.deals[k]["size"]:v|self.new_deals[k] if k in list(self.new_deals) else v for k,v in self.client.deals.items()}
        self.new_deals={}
        
        for i in range(len(list(d))):
            if len(d[list(d)[i]])>21:
                self.history[list(d)[i]]=d[list(d)[i]]
            else:
                try:
                    self.history[list(d)[i]] = self.history[list(d)[i]]|d[list(d)[i]]
                except:
                    self.history[list(d)[i]]=d[list(d)[i]]
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=4, ensure_ascii=False)
        self.make_widgets()
        self.client.deal_news=False
        self.client.balance_news=False