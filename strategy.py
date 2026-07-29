import sys
# sys.path.append("../config/strategies")

from func import indicators as indi
import pandas as pd
import os.path
from window import Window as wn
import importlib.util
import shutil

             

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
        self.strat_dir = f"../config/strategies/{self.name}"
        strat_path = f"{self.strat_dir}/{self.name}.py"
        if os.path.exists(strat_path):
            abs_path = os.path.abspath(strat_path)
            spec = importlib.util.spec_from_file_location(self.name, abs_path)
            self.stg = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.stg)
            self.strategy_dict = self.stg.strat_dict

            # self.stg = __import__(self.name)
            # print(self.stg.__dict__)
            # self.strategy_dict = self.stg.strat_dict
            self.old_data = self.stg.strat_dict.copy()
            self.status = "existing"
        else:
            self.strategy_dict = {
                "name" : self.name,
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
        # self.save_strategy()
        self.stg.strat_dict.update(self.strategy_dict)
        
    
    def save_strategy(self, name=None):
        to_remove = False
        if not name:
            name = self.name
        else:          
            if os.path.exists(f"../config/strategies/{name}/{name}.py"):
                w = wn(main_label="Стратегия с таким именем уже существует. удалить её?", yes_no_buttons=["Да", "Нет"])
                if w.yes_no:
                    to_remove=True

        if os.path.exists(f"../config/strategies/{self.name}/{self.name}.py"):
            w = wn(main_label="Внести изменения в стратегию?", yes_no_buttons=["Да", "Нет"])
            if w.yes_no:
                if to_remove:
                    shutil.rmtree(f"../config/strategies/{name}")
                if name != self.name:
                    os.rename(f"../config/strategies/{self.name}", f"../config/strategies/{name}")
                    os.rename(f"../config/strategies/{name}/{self.name}.py", f"../config/strategies/{name}/{name}.py")
                self.name = name
                self.strategy_dict["name"] = self.name
                with open(f"../config/strategies/{self.name}/{self.name}.py","r+") as f:
                    old = f.read()
                    f.truncate(0)
                    f.seek(0)
                    new = old.replace(str(self.old_data), str(self.strategy_dict))
                    f.write(new)   

        else:
            if to_remove:
                os.remove(f"../config/strategies/{name}/{name}.py")
            self.name = name
            self.strategy_dict["name"] = self.name
            os.makedirs(f"../config/strategies/{self.name}", exist_ok=True)
            with open(f"../config/strategies/{self.name}/{self.name}.py","w+") as f:
                f.write(str(f"strat_dict = {self.strategy_dict}" +
                            "\ntrade_dict = {}\n\n\n" +
                            "\nimport datetime as dt\nimport sys\nimport os\nimport json\n\n" + 
                            "strategy_dir = os.path.dirname(os.path.abspath(__file__))\n" + 
                            "parent_dir = os.path.dirname(strategy_dir)\n" + 
                            "gparent_dir = os.path.dirname(parent_dir)\n" + 
                            "ggparent_dir = os.path.dirname(gparent_dir)\n" + 
                            "project_path = os.path.join(ggparent_dir, \"trading_bot\")\n\n"+ 
                            "if project_path not in sys.path:\n\tsys.path.insert(0, project_path)\n"
                            "from func.indicators import natr"))

                    



    def get_strat_list():
        strat_list = []
        try:
            for filename in os.listdir("../config/strategies"):
                if filename != "__pycache__":
                    strat_list.append(filename)#.rstrip(".py"))
                    # print(strat_list)
        except:
            pass
        return strat_list
    


    def calculate_strategy(self, client, add_symbol, fs=4, stl=14 ):
        if "key_fractals" in self.strategy_dict["indicators"] and not "fractals" in self.strategy_dict["indicators"]:
            self.strategy_dict["indicators"]["fractals"] = {}

        sl = set(self.strategy_dict["symbols"].copy() + list(client.deals) + [add_symbol])
        # if add_symbol not in sl:
        #     sl.append(add_symbol)
        indi_dict = {k:v |{"data":{k:{"intervals":{ k:{"data":""} for k in self.strategy_dict["timeframes"]}} for k in sl}} for k, v in self.strategy_dict["indicators"].items()}
        for symb in sl:
            for i in self.strategy_dict["timeframes"]:
                if "fractals" in self.strategy_dict["indicators"] or "key_fractals" in self.strategy_dict["indicators"]:
                    indi_dict["fractals"]["data"][symb]["intervals"][i]["data"] = indi.fractals(client.data_to_read(symb, i), size=fs)
                if "key_fractals" in self.strategy_dict["indicators"]:
                    indi_dict["key_fractals"]["data"][symb]["intervals"][i]["data"] = indi.key_fractals(self.indi_dict["fractals"]["data"][symb]["intervals"][i]["data"])
                if "imbalance" in self.strategy_dict["indicators"]:
                    indi_dict["imbalance"]["data"][symb]["intervals"][i]["data"] = indi.imbalance(client.data_to_read(symb, i))
                if "stoch" in self.strategy_dict["indicators"]:
                    indi_dict["stoch"]["data"][symb]["intervals"][i]["data"] = indi.stoch(client.data_to_read(symb, i), stl)
                if "volume" in self.strategy_dict["indicators"]:
                    indi_dict["volume"]["data"][symb]["intervals"][i]["data"] = pd.DataFrame(client.data_to_read(symb, i)["volume"])
                if "open_interest" in self.strategy_dict["indicators"]:
                    indi_dict["open_interest"]["data"][symb]["intervals"][i]["data"] = pd.DataFrame(client.data_to_read(symb, i)["open_interest"])
        self.stg.indi_dict = indi_dict
    

    def indi_dict_to_read(self, indicator, symbol, interval):
        return self.stg.indi_dict[indicator]["data"][symbol]["intervals"][interval]["data"].copy()
    
    def indicator_to_plot(self, indicator, symbol, interval):
        print(self.indicators[indicator] | self.indi_dict_to_read(indicator, symbol, interval))
        return self.indicators[indicator] | self.indi_dict_to_read(indicator, symbol, interval)
        

# st = Strategy("super_TPSL")
# st.save_strategy()