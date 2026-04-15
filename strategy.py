import sys
sys.path.append("../config/strategies")

from func import tables as tb
from func import indicators as indi

import matplotlib.markers as mark
# import mplfinance as mpf
# import pandas_ta as ta
import pandas as pd
import json
import os.path
from pprint import pprint
from window import Window as wn

             

class Strategy:
    indicators = {
        "fractals":{
            "chart":"main", "chart_type":"dots", "colors":["green", "red"],"marks":["^", "v"], "transparency":.5
        },
        "key_fractals":{
            "chart":"main", "chart_type":"dots", "colors":["black"], "marks" : ["o"], "transparency":.5
        }, 
        "imbalance":{
            "chart":"main", "chart_type":"area", "colors": ["green", "red"], "width":2, "linewidth": 1, "transparency":.2
        }, 
        "volume":{
            "chart":"main", "chart_type":"bars", "colors": ["green", "red"], "c_name":"volume", "cut_to_min":False, "transparency":.3
        }, 
        "open_interest":{
            "chart":"add", "chart_type":"bars", "colors" : ["green", "red"], "c_name": "open_interest", "cut_to_min": True, "transparency":.5
        }, 
        "stoch":{
            "chart":"add", "chart_type":"curve", "colors" : ["blue", "black"], "h_lines" : [20, 80]
        }
    }

    def __init__(self, name):
        if not os.path.exists("../config/strategies"):
            os.mkdir("../config/strategies")
        self.name = name
        if os.path.exists(f"../config/strategies/{self.name}.py"):
            self.stg = __import__(self.name)
            # self.stg.strat_dict["strat_name"] = self.name
            self.strategy_dict = self.stg.strat_dict
            self.old_data = self.stg.strat_dict.copy()
            self.status = "existing"
        else:
            self.strategy_dict = {
                "symbols" : [],
                "timeframes" : ["5", "15"],
                "order_type" : "limit",
                "indicators" : {},
                "max_risk" : 1,
                "min_profit" : 1 
            }
            self.status = "new"
        
    def change_strategy(self, 
                        symbols = False,
                        timeframes = False,
                        orderType = False,
                        indicators = False,          
                        max_risk = False,
                        min_profit = False
                        ):
        new_dict = {k:v for k, v in locals().items() if type(v) != bool and k != "self"}  
        self.strategy_dict = self.strategy_dict | new_dict
        # self.stg.strat_dict = self.strategy_dict
        self.stg.strat_dict.update(self.strategy_dict)
        # self.save_strategy()
        
    
    def save_strategy(self, name=None):
        if name:
            to_remove = False
            if os.path.exists(f"../config/strategies/{name}.py"):
                w = wn(label="Стратегия с таким именем уже существует. удалить её?", yes_no_buttons=["Да", "Нет"])
                if w.yes_no:
                    to_remove=True
                    # os.remove(f"../config/strategies/{name}.py")

            if os.path.exists(f"../config/strategies/{self.name}.py"):
                w = wn(label="Внести изменения в стратегию?", yes_no_buttons=["Да", "Нет"])
                if w.yes_no:
                    if to_remove:
                        os.remove(f"../config/strategies/{name}.py")
                    os.rename(f"../config/strategies/{self.name}.py", f"../config/strategies/{name}.py")
                    with open(f"../config/strategies/{name}.py","r+") as f:
                        old = f.read()
                        f.truncate(0)
                        f.seek(0)
                        new = old.replace(str(self.old_data), str(self.strategy_dict))
                        f.write(new)   

            else:
                if to_remove:
                    os.remove(f"../config/strategies/{name}.py")
                with open(f"../config/strategies/{name}.py","w+") as f:
                    f.write(str(f"strat_dict = {self.strategy_dict}"))
                
        else:
            if os.path.exists(f"../config/strategies/{self.name}.py"):
                w = wn(label="Внести изменения в стратегию?", yes_no_buttons=["Да", "Нет"])
                if w.yes_no:
                    with open(f"../config/strategies/{self.name}.py","r+") as f:
                        old = f.read()
                        f.truncate(0)
                        f.seek(0)
                        new = old.replace(str(self.old_data), str(self.strategy_dict))
                        f.write(new)
            else:
                with open(f"../config/strategies/{self.name}.py","w+") as f:
                    f.write(str(f"strat_dict = {self.strategy_dict}")) 



    def get_strat_list():
        strat_list = []
        try:
            for filename in os.listdir("../config/strategies"):
                strat_list.append(filename.rstrip(".py"))
        except:
            pass
        return strat_list
    


    def calculate_strategy(self, data, add_symbol, fs=4, stl=14 ):
        if "key_fractals" in list(self.strategy_dict["indicators"]) and not "fractals" in list(self.strategy_dict["indicators"]):
            self.strategy_dict["indicators"]["fractals"] = {}

        sl = self.strategy_dict["symbols"].copy()
        if add_symbol not in sl:
            sl.append(add_symbol)
        self.indi_dict = {k:v |{"data":{k:{"intervals":{ k:{"data":""} for k in self.strategy_dict["timeframes"]}} for k in sl}} for k, v in self.strategy_dict["indicators"].items()}
        for symb in sl:
            for i in self.strategy_dict["timeframes"]:
                if "fractals" in list(self.strategy_dict["indicators"]) or "key_fractals" in list(self.strategy_dict["indicators"]):
                    self.indi_dict["fractals"]["data"][symb]["intervals"][i]["data"] = indi.fractals(data[symb]["intervals"][i]["data"], size=fs)
                if "key_fractals" in list(self.strategy_dict["indicators"]):
                    self.indi_dict["key_fractals"]["data"][symb]["intervals"][i]["data"] = indi.key_fractals(self.indi_dict["fractals"]["data"][symb]["intervals"][i]["data"])
                if "imbalance" in list(self.strategy_dict["indicators"]):
                    self.indi_dict["imbalance"]["data"][symb]["intervals"][i]["data"] = indi.imbalance(data[symb]["intervals"][i]["data"])
                if "stoch" in list(self.strategy_dict["indicators"]):
                    self.indi_dict["stoch"]["data"][symb]["intervals"][i]["data"] = indi.stoch(data[symb]["intervals"][i]["data"].iloc[::-1], stl)
                if "volume" in list(self.strategy_dict["indicators"]):
                    self.indi_dict["volume"]["data"][symb]["intervals"][i]["data"] = pd.DataFrame(data[symb]["intervals"][i]["data"]["volume"])
                if "open_interest" in list(self.strategy_dict["indicators"]):
                    self.indi_dict["open_interest"]["data"][symb]["intervals"][i]["data"] = pd.DataFrame(data[symb]["intervals"][i]["data"]["open_interest"])



