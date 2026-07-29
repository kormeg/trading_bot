import tkinter as tk
from tkinter import ttk
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
from func.indicators import natr as get_natr
from queue import Queue, Empty
import csv



class GUI():
    app_name = "SUPER-DUPER BOT ULTIMATE-3000"
    chart_length = 200
    grid_rows = 24
    grid_cols = 20
    modes = ["view", "trade", "edit"]   # режимы окна
    history_items = {
        "symbol":              ["Монета", 100], 
        "side":                ["Сторона", 60], 
        "positionValue":       ["Размер позиции", 100], 
        "identificationPrice": ["Цена обнаружения", 100],
        "entryPrice":          ["Цена Входа", 80], 
        "stopLoss":            ["Stop loss", 70], 
        "takeProfit":          ["Take profit", 70],
        "openTime":            ["Время открытия", 100],
        "identificationTime":  ["Время обнаружения", 100],
        "timeframe":           ["ТФ", 30], 
        "closedPnl" :          ["Прибыль", 60], 
        "volumeDifference":    ["% Объема", 40], 
        "natr":                ["NATR", 30],
        "leverage":            ["Плечо", 30],
        "closeTime" :          ["Время закрытия", 100] ,
        "fee":                 ["Комиссия", 60],
    }



    def __init__(self, client, settings_path, bot_name):

        self.client = client
        self.settings_path = settings_path
        self.bot_name = bot_name
        self.mode = "view"              # режим окна с разным функционалом для анализа/торговли/просмотра и т д
        self.trading = False            # торгует или не торгует в данный момент
        self.vol_sorted = False         # флажок сортировки монет в меню по волатильности
        self.vol_cut = False            # флажок режима отсечения по волатильности
        self.vol_qty_cut = None         # режим при котором для стратегии на каждой итерации отбирается определенное число наиболее волатильных монет
        self.vol_val_cut = None         # режим при котором для стратегии на каждой итерации отбираются монеты по минимальному значению волатильности 
        self.history = []
        self.deal_id_iid = {}
        self.history_columns = list(GUI.history_items)
        self.history_col_index = {col: idx for idx, col in enumerate(self.history_columns)}

        # загружаем настройки. апи ключи, последние монета, таймфрейм, стратегия, индикаторы
        with open(self.settings_path, "r", encoding="utf-8") as f:
            self.settings = json.load(f) 

        # проверяем была ли установлена стратегия при прошлом запуске
        strategy_name = self.settings.get("last_strategy", None)
        if strategy_name:
            if strategy_name in st.Strategy.get_strat_list():
                self.set_strategy(strategy_name, True)

        else:
            self.indicators = self.settings.get("last_indicators", {})
        if not all(item in st.Strategy.indicators for item in self.indicators):
            self.indicators = {k:v for k, v in self.indicators.items() if k in st.Strategy.indicators}

        self.window = tk.Tk()

        # try:
        #     windll.shcore.SetProcessDpiAwareness(1) # 1 = DPI_AWARENESS_CONTEXT_SYSTEM_AWARE
        # except AttributeError:
        #     pass # Не Windows или версия Python старая

        # # Получаем DPI экрана (для Windows)
        # try:
        #     dpi = windll.user32.GetDpiForWindow(self.window.winfo_id())
        # except AttributeError:
        #     dpi = 96 # Значение по умолчанию, если функция недоступна

        # scaling_factor = dpi / 96
        # self.window.tk.call('tk', 'scaling', scaling_factor)

        self.window.title(GUI.app_name)
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        # self.app_width = int(screen_width*0.75* scaling_factor)
        # self.app_height = int(screen_height*0.7* scaling_factor)
        # x = int((screen_width/2 * scaling_factor) - self.app_width/2)
        # y = int((screen_height/2 * scaling_factor) - self.app_height/2)
        self.app_width = int(screen_width*0.75)
        self.app_height = int(screen_height*0.7)
        x = int((screen_width/2) - self.app_width/2)
        y = int((screen_height/2) - self.app_height/2)
        self.window.geometry(f"{self.app_width}x{self.app_height}+{x}+{y}")

        self.xsf = ("TkMenuFont", int(round(screen_height/130)))
        self.sf =("TkMenuFont", int(round(screen_height/110)))
        self.mf = ("TkMenuFont", int(round(screen_height/90)))
        self.lf = ("TkMenuFont", int(round(screen_height/85)))
        self.xlf = ("TkMenuFont", int(round(screen_height/70)))
        print(self.xsf, self.sf, self.mf, self.lf, self.xlf)
        
        
        for i in range(GUI.grid_rows):
            self.window.rowconfigure(i+1, weight=1, minsize=int(self.app_height/GUI.grid_rows))
        for i in range(GUI.grid_cols):
            self.window.columnconfigure(i+1, weight=1, minsize=int(self.app_width/GUI.grid_cols))

        if self.indicators:
            self.add_winds = len([x for x in [self.indicators[x]["chart"] for x in self.indicators] if x == "add"])
        else:
            self.add_winds = 0

        self.set_styles()
        self.make_menu()
        self.fill_menu()
        self.make_widgets()
        self.live_chart(vn.Visualization(params={"add_windows" : self.add_winds}))


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
                self.timeframe_menu.add_command(label=i, font=self.sf, command=partial(self.set_timeframe, i))

        if strategy:
            for i in st.Strategy.get_strat_list():
                self.strategy_menu.add_command(label=i, font=self.sf, command=partial(self.set_strategy, i))

        if indicator:
            for i in st.Strategy.indicators:
                self.indicator_menu.add_command(label=i, font=self.sf, command=partial(self.set_indicator, i))
        
        if mode:
            for i in GUI.modes:
                self.mode_menu.add_command(label=i, font=self.sf, command=partial(self.set_mode, i))

    
    def fill_symbol_menu(self):
        self.symbol_menu.delete(0, "end")    
        if self.vol_sorted:
            self.get_volatility()
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


    def make_history_widget(self):
        try:
            self.history_widget.destroy()
        except:
            pass
        columns = self.history_columns
        self.history_widget = ttk.Treeview(self.window, columns=columns, show='headings', style="Treeview")
        self.deal_id_iid.clear()
        for col in columns:
            self.history_widget.heading(col, text=self.history_items[col][0])
            
        
        scrollbar = ttk.Scrollbar(self.window, orient=tk.VERTICAL, command=self.history_widget.yview)
        self.history_widget.configure(yscrollcommand=scrollbar.set)

        self.history_widget.grid(row=20, column=1, columnspan=24, rowspan=5, sticky="nsew")
        scrollbar.grid(row=20, column=24, rowspan=5, sticky="nse")
        for col in columns:
            self.history_widget.column(col, width=self.history_items[col][1], anchor="w")

        self.history_widget.tag_configure('profit', background='lightgreen', foreground='black')
        self.history_widget.tag_configure('loss', background='lightcoral', foreground='black')
        self.history_widget.tag_configure('open', background='lightyellow', foreground='black')
        self.history_widget.tag_configure('not_closed', background='lightblue', foreground='black')
        self.load_history(100)
        self.init_history_tree()
        self.client.get_deals(self.history)


    def make_trading_status_widget(self):
        try:
            self.trading_status_label.destroy()
        except:
            pass
        if self.trading:
            self.trading_status_label = tk.Label(self.window, text="Бот Торгует", foreground = "red", background="black", font=self.lf)
        else:
            self.trading_status_label = tk.Label(self.window, text="Бот Не Торгует", foreground = "black", background="#7aabdb", font=self.lf)
        self.trading_status_label.grid(row=1, column=15, columnspan=2, rowspan=2, sticky="nsew", padx=5)


    def make_bot_status_widget(self):
        try:
            self.status_label .destroy()
        except:
            pass
        self.status_label = tk.Label(self.window, text=f"Текущая стратегия:   ● {self.strategy.name} ●   Бот в режиме:   ● {self.mode} ●", font=self.mf)
        self.status_label.grid(row=2, column=1, columnspan=8, rowspan=1, sticky="nsw")


    def make_vol_cut_widget(self):
        try:
            self.volty_button.destroy()
        except:
            pass
        if not self.vol_cut:
            self.volty_button = tk.Button(self.window, text = "отобрать волатильные монеты", wraplength=self.app_width/12.5, font=self.sf, command= self.vol_cut_on_off)
        else:
            self.volty_button = tk.Button(self.window, text = "оставить текущие монеты", wraplength=self.app_width/12.5, font=self.sf, command= self.vol_cut_on_off)
        self.volty_button.grid(row=1, column=11, columnspan=2, rowspan=2, sticky="nsew")


    def make_balance_widget(self):
        try:
            self.balance_widget.destroy()
        except:
            pass
        self.balance = self.client.balance["USDT"]
        self.balance_widget = tk.Label(self.window, text=f"Баланс:  {self.balance}", wraplength=self.app_width/6.5, 
                                    background="#7aabdb", anchor="c", font=self.lf)
        self.balance_widget.grid(row = 1, rowspan=2, column=17, columnspan=4, sticky="nsew")
        self.client.balance_news=False


    def make_start_trading_button(self):
        try:
            self.start_stop_button.destroy()
        except:
            pass
        if self.trading:
            text = "Стоп"
        else:
            text="Торговать"
        self.start_stop_button = tk.Button(self.window, text=text, font=self.lf, command=self.trade_on_off)
        self.start_stop_button.grid(row=1, column=13, columnspan=2, rowspan=2, sticky="nsew")


    def make_widgets(self):
        try:
            self.history_widget.destroy()
            self.history_widget=None
        except:
            pass
        try:
            self.trading_status_label.destroy()
        except:
            pass
        try:
            self.status_label .destroy()
        except:
            pass
        try:
            self.volty_button.destroy()
        except:
            pass
        try:
            self.balance_widget.destroy()
        except:
            pass
        try:
            self.start_stop_button.destroy()
        except:
            pass

        if self.mode == "trade":
            self.make_history_widget()
            self.make_balance_widget()
            self.make_vol_cut_widget()
            self.make_start_trading_button()
        # elif self.mode == "edit":
        #     pass
        self.make_bot_status_widget()
        self.make_trading_status_widget()
        

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
            # self.chart.add_candles(self.client.data_to_read(), symbol=self.chart.symbol, timeframe=self.chart.timeframe)
            # if self.mode == "trade" and self.history:
                # for i in range(len(self.history[-100:])):
                #     if self.history[i].get("symbol", "") == self.chart.symbol:
                #         try:
                #             self.chart.add_plot(data=[float(self.history[i]["entryPrice"]), float(self.history[i]["stopLoss"]), float(self.history[i]["takeProfit"])], 
                #                                 chart="main", 
                #                                 chart_type="hlines",
                #                                 colors=["black", "red", "green" ], 
                #                                 linewidth=0.5, 
                #                                 transparency=0.6, 
                #                                 titles=[self.history[i]["side"], "stop loss", "take profit"], 
                #                                 xmins=[pd.to_datetime(self.history[i]["identification_time"], dayfirst=True)]*3
                #                                 )
                #         except:
                #             pass
            if self.strategy:
                self.strategy.calculate_strategy(self.client, self.chart.symbol)     
                # for i in self.strategy.stg.indi_dict:
                #     self.chart.add_plot(**(self.strategy.indicators[i]|self.strategy.stg.indi_dict[i]))

            # self.chart.visualize()
            self.canvas = bt.FigureCanvasTkAgg(self.chart.fig, self.window)
            if self.mode == "trade":
                self.canvas.get_tk_widget().grid(row=3, column=1, columnspan=20, rowspan=17, sticky="nsew")
            else:
                self.canvas.get_tk_widget().grid(row=3, column=1, columnspan=20, rowspan=22, sticky="nsew")
            self.update_chart()


    def update_chart(self):

        self.client.public_ws_reconnect()
        self.client.private_ws_reconnect()

        for ax in self.chart.axis_list:
            ax.clear()
        # self.chart.add_candles(self.client.data_to_read(), symbol=self.chart.symbol, timeframe=self.chart.timeframe)
        # if self.mode == "trade" and self.history:
        #     for i in range(len(self.history[-100:])):
        #         if self.history[i].get("symbol", "") == self.chart.symbol:
        #             try:
        #                 self.chart.add_plot(data=[float(self.history[i]["entryPrice"]), float(self.history[i]["stopLoss"]), float(self.history[i]["takeProfit"])], 
        #                                     chart="main", 
        #                                     chart_type="hlines",
        #                                     colors=["black", "red", "green" ], 
        #                                     linewidth=0.5, 
        #                                     transparency=0.6, 
        #                                     titles=[self.history[i]["side"], "stop loss", "take profit"], 
        #                                     xmins=[pd.to_datetime(self.history[i]["identification_time"], dayfirst=True)]*3
        #                                         )
        #             except:
        #                 pass

        if self.strategy:
            self.cut_by_volatility()
            self.strategy.calculate_strategy(self.client, self.chart.symbol)
            if self.trading:
                if not self.strategy.stg.trade_dict["trade"]:
                    self.strategy.stg.trade(self.client, self.bot_name)
            self.client.sort_private_mail()
            self.update_history() 
                
            if self.client.balance_news:
                self.make_balance_widget()
            
            # for i in self.strategy.stg.indi_dict:
            #     self.chart.add_plot(**(self.strategy.indicators[i]|self.strategy.stg.indi_dict[i]))
            
        # self.chart.visualize()
        # plt.draw()
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
        

    def set_strategy(self, name, init=False):

        if self.trading:
            self.trade_on_off()
        self.strategy = st.Strategy(name)
        # загружаем индикаторы из самой стратегии на случай, если она была изменена вручную.
        self.indicators = self.strategy.strategy_dict["indicators"]
        self.history_path = self.strategy.strat_dir+"/history.csv"
        if not init:
            self.load_history(100)
            self.make_menu()
            self.fill_menu()
            self.make_widgets()
            if self.add_winds != len([x for x in [self.indicators[x]["chart"] for x in self.indicators] if x == "add"]):
                self.add_winds = len([x for x in [self.indicators[x]["chart"] for x in self.indicators] if x == "add"])
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
        self.canvas.get_tk_widget().destroy()
        self.live_chart(vn.Visualization(params={"add_windows":self.add_winds}))
        plt.draw()
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
                w = wn ("Отсечь по волатильности", main_label="Выбери режим", yes_no_buttons=["топ", "порог"], root=self.window)
                if w.yes_no:
                    w = wn("Отсечь топ наиболее волатильных", main_label="Введи количество", entry=True, exit="ok", root=self.window)
                    self.vol_qty_cut=int(w.entered_value)
                else:
                    w = wn("Отсечь монетвы по пороговому значению волатильности", main_label="Введи минимальное значение", entry=True, exit="ok", root=self.window)  
                    self.vol_val_cut=float(w.entered_value)
                self.vol_cut = True
                self.cut_by_volatility()

            except: 
                print("отмена")
                return
            
        else:
            self.vol_cut = False
            self.vol_qty_cut = None
            self.vol_val_cut = None
        self.make_menu()
        self.fill_menu()
        self.make_vol_cut_widget()


    def get_volatility(self):
        if "5" in self.client.intervals:
            df = []
            for symb in self.client.symbols:
                try:
                    natr = get_natr(self.client.data_to_read(symb,"5"))
                except:
                    natr = 0
                # self.client.data_to_read(symb)["natr"] = natr
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
            self.get_volatility()
            if len(self.volatility) > 0:
                if self.vol_qty_cut:
                    self.strategy.change_strategy(symbols=self.volatility["symbol"][:self.vol_qty_cut].to_list())
                    if self.vol_val_cut:
                        print("shl'apa")
                else:
                    if not self.vol_val_cut:
                        print("shl'apa again")
                    else:
                        self.strategy.change_strategy(symbols=self.volatility[self.volatility["natr"] >=self.vol_val_cut]["symbol"].tolist())


    def trade_on_off(self):
        if self.trading:
            self.trading=False
            self.strategy.stg.trade_dict={"trade":False}
            message = "---------stop trading--------"
        else:
            self.trading = True
            message = "--------start trading--------"
            # self.client.get_deals()
            # self.cut_by_volatility()
            # self.strategy.calculate_strategy(self.client, self.chart.symbol)
            # self.strategy.stg.trade(self.client, self.bot_name)
        # now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # self.history_widget.insert('', tk.END, values=(message,))
        # self.history[time.time()] = {"time": now, "action": message}
        # try:
        #     if not os.path.exists(self.settings_path.rstrip("settings.json")+self.strategy.name):
        #         os.mkdir(self.settings_path.rstrip("settings.json")+self.strategy.name)
        #     with open(self.history_path, "w", encoding="utf-8") as f:
        #         json.dump(self.history, f, indent=4, ensure_ascii=False)
        # except:
        #     print("отсутствует стратегия")
        self.make_start_trading_button()
        self.make_trading_status_widget()


    def load_history(self, size):
        """возвращает список словарей"""
        if os.path.exists(self.history_path):
            #  if os.path.getsize(self.history_path) != 0:
            try:
                df = pd.read_csv(self.history_path, dtype=str, keep_default_na=False, delimiter=";")
                if df.empty:
                    self.history = []
                    return
                df["time"] = pd.to_datetime(df["openTime"], format="%d.%m.%Y %H:%M:%S.%f", errors="coerce")
                df = df.groupby("openTime", as_index=False).last()
                df = df.sort_values(["time"])
                df = df.drop(columns=["time"])
                self.history = df.tail(size).to_dict(orient="records")
                return
            except pd.errors.EmptyDataError:
                pass
        with open(self.history_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=self.client.all_deal_items, delimiter=';')
            writer.writeheader()
            self.history = []
  
    
    def init_history_tree(self):

        if self.history:
            # print("ok")
            for i in range(len(self.history)):
                # print("ok")
                # print(self.history[i])
                self.update_history_row(self.history[i], True)
            
 
    def is_history_bottom_visible(self):
        
        lower = self.history_widget.yview()[1]    # yview() возвращает (верхняя_видимая_доля, нижняя_видимая_доля)
        return lower >= 0.99            # Если нижний край видимой области >= 0.99, считаем, что пользователь смотрит вниз
    

    def get_row_tag(self, data, from_history):
        """Определяет цвет строки на основе данных сделки."""
        # Пример: если есть pnl и он >0 -> прибыль, <0 -> убыток, иначе открытая
        pnl = data.get('closedPnl')
        if pnl is not None:
            try:
                pnl = float(pnl)
                if pnl > 0:
                    return 'profit'
                elif pnl < 0:
                    return 'loss'
                else:
                    if from_history:
                        return "not_closed"
                    else:
                        return 'open'
            except:
                pass
        # Если нет pnl или он не число, возможно сделка ещё открыта
        if from_history:
            return "not_closed"
        else:
            return 'open'

   
    def update_history_row(self, data, from_history=False):
        tag = self.get_row_tag(data, from_history)
        open_id = data.get('openId')
        
        row_values = []
        if len(data) == self.client.full_info:
            row_values = [str(data.get(col, "")) for col in self.history_columns]

        if open_id in self.deal_id_iid:
            iid = self.deal_id_iid[open_id]
            if not row_values:
                row_values = list(self.history_widget.item(iid, 'values'))
                for col, val in data.items():
                    if col in self.history_col_index:
                        row_values[self.history_col_index[col]] = str(val) if val is not None else ""
            self.history_widget.item(iid, values=row_values, tags=(tag,))
            
        else:
            if row_values:
                iid = self.history_widget.insert('', tk.END, values=row_values, tags=(tag,))
                self.deal_id_iid[open_id] = iid
                if self.is_history_bottom_visible():
                    # self.history_widget.after_idle(lambda: self.history_widget.see(iid))
                    self.history_widget.see(iid)


    def update_history(self):
        while True:
            try:
                message = self.client.deal_news.get_nowait()
            except Empty:
                break
            if self.history_widget:
                self.update_history_row(message)
            self.deal_update_to_csv(message)


    def deal_update_to_csv(self, deal):
        """
        Добавляет одну сделку в конец CSV.
        Предполагается, что файл существует и имеет заголовки.
        """
        with open(self.history_path, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=self.client.all_deal_items, delimiter=";")
            writer.writerow(deal)


    def set_styles(self):
        style = ttk.Style(self.window)  # Используем стиль окна, а не создаём новый

        try:
            style.theme_use("default")  # или "clam", "alt"
        except tk.TclError:
            pass

        style.configure("Treeview.Heading",
                        font = self.xsf,
                        # font=("Arial", 20, "bold"),
                        # foreground="white",
                        background="#7aabdb",
                        # padding=(10, 5)
                        )
        style.configure("Treeview",
                # rowheight=60,
                font = self.xsf,
                # font=("Arial", 13),
                # background="white",
                # fieldbackground="white"
                )


    def append_deal_csv(filename, deal_dict, fieldnames):
        """
        Добавляет одну сделку в конец CSV.
        Предполагается, что файл существует и имеет заголовки.
        """
        with open(filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writerow(deal_dict)


    def screen_diagnostics(self):
        print(f"Ширина экрана: {self.window.winfo_screenwidth()}")
        print(f"Высота экрана: {self.window.winfo_screenheight()}")
        print(f"Масштаб Tk: {self.window.tk.call('tk', 'scaling')}")
        try:
            
            dpi = windll.user32.GetDpiForWindow(self.window.winfo_id())
            print(f"DPI окна: {dpi}")
        except:
            print("DPI: недоступно (не Windows или старая версия)")
        print(f"Геометрия окна: {self.window.geometry()}")