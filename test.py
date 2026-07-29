

# import tkinter as tk
# from tkinter import ttk

# def on_tree_click(event):
#     tree = event.widget
#     # Определяем строку и колонку
#     row_id = tree.identify_row(event.y)
#     col_id = tree.identify_column(event.x)   # '#1', '#2', ...
#     if not row_id:   # клик мимо строк
#         return
    
#     # Проверяем, что кликнули по нужной колонке, например, по второй
#     if col_id == '#2':
#         # Получаем значение ячейки (опционально)
#         value = tree.set(row_id, column=col_id)
#         print(f"Клик по колонке {col_id}, значение: {value}")
#         # Здесь вызываете свою функцию
#         my_custom_function(row_id, value)

# def my_custom_function(row_id, value):
#     print(f"Вызвана функция для строки {row_id}, значение {value}")

# root = tk.Tk()
# tree = ttk.Treeview(root, columns=('col1', 'col2', 'col3'), show='headings')
# tree.heading('col1', text='Имя')
# tree.heading('col2', text='Возраст')
# tree.heading('col3', text='Город')
# tree.pack()

# # Добавляем данные
# for i in range(5):
#     tree.insert('', 'end', values=(f'User{i}', 20+i, f'City{i}'))

# # Привязываем обработчик клика
# tree.bind('<Button-1>', on_tree_click)

# root.mainloop()



# # Bybit Request Error | 30228 | No new positions during delisting.



# import datetime as dt


# dates = ["2026-05-31 14:30:00:234567", "2026-05-31 15:00:00:234567", "2026-05-31 15:30:00:234567"]

# def handle_deal(l):
# 	for i in range(len(l)):
# 		if ((dt.datetime.now()-dt.datetime.fromisoformat(l[i][:19])).total_seconds())/60/60 >= 1:
# 			print(i)
# 			print("delete")
			
# handle_deal(dates)



# import datetime as dt
# import pytz
# import time
# tz = pytz.timezone("Europe/Moscow")


# date_str = "2026-05-31 14:30:00:234567"
# date = date_str[:19]
# date = dt.datetime.fromisoformat(date)  
# print(date)

# now = now_utc = dt.datetime.now()
# print(now)

# diff = (now- date).total_seconds()
# print(diff/60/60)


# unix_date = int(tz.localize(date).timestamp())
# print(unix_date)
# dt_moscow = dt.datetime.fromtimestamp(unix_date, tz=tz)
# result_date = dt_moscow.strftime("%Y-%m-%d %H:%M:%S")
# print(result_date)  # 2025-05-31 14:30:00




# import matplotlib.pyplot as plt
# import api
# import visualization as vn
# from func import indicators as indi

# symbol = "APRUSDT"
# timeframe = "5"
# indi_dict = {}

# cl = api.API("","", websocket=False)
# cl.a_get_data(symbol, timeframe, 100)
# print(cl.data)
# df = cl.data[symbol]["intervals"][timeframe]["data"]
# bb = indi.bollinger(df, 20, 4) 
# indi_dict["bollinger"] = {"data" : {symbol : {"intervals" : {timeframe :{"data": bb}}}}}
# print(indi_dict)
# chart = vn.Visualization(params={"add_windows" : 0})
# chart.add_candles(cl.data, symbol=symbol, timeframe=timeframe)
# for c_name in indi_dict["bollinger"]["data"][symbol]["intervals"][timeframe]["data"].columns:
#     chart.add_plot(chart="main", c_name = c_name, symbol=symbol, timeframe=timeframe, chart_type="curve", colors = ["blue"], data = indi_dict["bollinger"]["data"])
# print(chart.plotting_list)
# chart.visualize()
# plt.show()



# import tkinter as tk

# def open_child_window():
#     child_window = tk.Toplevel(root)
#     child_window.title("Дочернее окно")

#     # Создаем поле для ввода
#     entry_field = tk.Entry(child_window, width=30)
#     entry_field.pack(pady=20)

#     # --- Устанавливаем курсор в это поле ---
#     entry_field.focus()  # Или entry_field.focus_set()

# # Основное окно
# root = tk.Tk()
# root.title("Главное окно")

# open_button = tk.Button(root, text="Открыть дочернее окно", command=open_child_window)
# open_button.pack(pady=20)

# root.mainloop()







# # В __init__:
# self.latest_bars = {}  # { (symb, inter): { timestamp: [open, high, low, close, volume] } }

# # В update_data для kline:
# key = (symb, inter)
# timestamp = message["data"][0]["start"]
# ohlcv = [
#     float(message["data"][0]["open"]),
#     float(message["data"][0]["high"]),
#     float(message["data"][0]["low"]),
#     float(message["data"][0]["close"]),
#     float(message["data"][0]["volume"])
# ]
# # Просто обновляем словарь:
# self.latest_bars.setdefault(key, {})[timestamp] = ohlcv
# # Никакого доступа к DataFrame здесь нет.

# # Отдельный метод синхронизации (вызывать, например, каждые 0.5 секунды):
# def sync_to_dataframe(self):
#     for (symb, inter), bars in self.latest_bars.items():
#         if not bars:
#             continue
#         # Преобразуем в DataFrame
#         new_df = pd.DataFrame.from_dict(bars, orient='index', 
#                                         columns=['open','high','low','close','volume'])
#         new_df.index = pd.to_datetime(new_df.index, unit='ms') + dt.timedelta(hours=3)
#         new_df.sort_index(ascending=False, inplace=True)
        
#         old_df = self.data[symb]["intervals"][inter]["data"]
#         # Объединяем, удаляем дубликаты по индексу (keep='first' оставит последнее обновление)
#         combined = pd.concat([new_df, old_df])
#         combined = combined[~combined.index.duplicated(keep='first')]
#         # Ограничиваем длину
#         if len(combined) > self.max_bars:
#             combined = combined.head(self.max_bars)
#         self.data[symb]["intervals"][inter]["data"] = combined
#         # Очищаем синхронизированные бары, чтобы не перезаписывать снова
#         bars.clear()
# Преимущества:
# Вебсокет-обработчик делает только запись в dict – дешёвая операция.

# Тяжёлая работа с pandas происходит редко (раз в 0.5-1 секунду) и в одном потоке.

# Дубликаты автоматически устраняются через duplicated(keep='first').

# import datetime as dt
# print(dt.datetime.now())



# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# важно. нужна проверка на нулевой размер позиции и ожидание. иногда открывается с нулем. в историю записалось
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# Возможно достаточно поставить задержку




# 23.06.2026 18:50:24.923592   start of iteration
# ESPORTSUSDT 1
# 5.5   natr
# 3043.2136335970786   coin_qty
# 1.0   min_qty
# 3043.0   right_qty
# 0.03286   current price
# Buy
# 0.01643   stop loss
# 950   difference
# 23.06.2026 18:50:25   start of iteration
# 23.06.2026 18:50:25   end of iteration

# ------------------------------------------------
# Позиция открыта
# ------------------------------------------------
# check#######
# {'symbol': 'ESPORTSUSDT', 'side': 'Buy', 'size': '3043', 'entryPrice': '0.03439', 'leverage': '1', 'positionValue': '104.64877', 'takeProfit': '0.0345', 'stopLoss': '0.01643', 'trailingStop': '0', 'liqPrice': '', 'breakEvenPrice': '0.03444677'}
# ###############
# -----------------------------------
# time : 23.06.2026 18:50:48
# wallet
# 48830.25788644
# 802.47610481
# -----------------------------------

# ------------------------------------------------
# Не удалось поменять плечо
# ------------------------------------------------

# ------------------------------------------------
# leverage not modified (ErrCode: 110043) (ErrTime: 15:50:49).
# Request → POST https://api-demo.bybit.com/v5/position/set-leverage: {"category": "linear", "symbol": "ESPORTSUSDT", "buyLeverage": "1", "sellLeverage": "1", "timestamp": 1782229848000}.
# ------------------------------------------------

# ------------------------------------------------
# Position is open
# 23.06.2026 18:50:49.759611
# ------------------------------------------------

# ------------------------------------------------
# symbol : ESPORTSUSDT
# leverage : 1
# breakEvenPrice : 
# liqPrice : 
# takeProfit : 
# positionValue : 
# trailingStop : 0
# side : 
# size : 0
# stopLoss : 
# entryPrice : 0
# botName : demo_bot
# strategyName : volume_strategy
# identificationTime : 23.06.2026 18:50:24.923592
# openTime : 23.06.2026 18:50:49.759611
# volumeDifference : 950
# timeframe : 1
# identificationPrice : 0.03286
# natr : 5.5
# avgExitPrice : 
# closedPnl : 
# closeTime : 
# fee : 
# openId : ESPORTSUSDT_0_0
# closeId : 
# ------------------------------------------------

# ------------------------------------------------
# Не удалось передвинуть TPSL
# ------------------------------------------------

# ------------------------------------------------
# can not set tp/sl/ts for zero position (ErrCode: 10001) (ErrTime: 15:50:50).
# Request → POST https://api-demo.bybit.com/v5/position/trading-stop: {"category": "linear", "symbol": "ESPORTSUSDT", "position_idx": 0, "tpsl_mode": "Full", "timestamp": 1782229849000, "takeProfit": "0.0016429999999999986", "stopLoss": "-0.01643"}.
# ------------------------------------------------
# check#######
# {'symbol': 'ESPORTSUSDT', 'side': 'Buy', 'size': '3043', 'entryPrice': '0.03439', 'leverage': '1', 'positionValue': '104.64877', 'takeProfit': '0.0345', 'stopLoss': '0.01643', 'trailingStop': '0', 'liqPrice': '', 'breakEvenPrice': '0.03444677'}
# ###############
# in deals
# ['SOLAYERUSDT', 'REUSDT', 'AVAAIUSDT', 'BICOUSDT', 'MBOXUSDT', 'BEUSDT', 'RKLBUSDT', 'ESPORTSUSDT']
# handle current

# ------------------------------------------------
# Position changed
# 23.06.2026 18:50:50
# ------------------------------------------------

# ------------------------------------------------
# side : Buy
# size : 3043
# entryPrice : 0.03439
# positionValue : 104.64877
# takeProfit : 0.0345
# stopLoss : 0.01643
# breakEvenPrice : 0.03444677





