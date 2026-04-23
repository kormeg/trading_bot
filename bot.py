import api
import gui
from window import Window as wn
import datetime as dt
import sys
import json
import os


class Bot():
    
    def __init__(self):

        config_path = "../config"
        if not os.path.exists(config_path):
            os.mkdir(config_path)
            
        bots_folder_path = config_path + "/bots"
        if not os.path.exists(bots_folder_path):
            os.mkdir(bots_folder_path)

        
        bots_list = ["Новый бот"]
        for filename in os.listdir(bots_folder_path):
            bots_list.append(filename)

        while True:
            w = wn("SUPER-DUPER BOT ULTIMATE-3000", default_ddl="Выбери бота", drop_down_list=bots_list)
            if not w.selected_value == "Новый бот":
                self.name = w.selected_value
                break   
            else:
                w = wn("bot_registration", main_label="Enter name of a bot", entry=True, exit="ok")
                if not w.entered_value in bots_list:
                    self.name = w.entered_value
                    break
                else:
                    w = wn("", main_label="бот с таким именем уже существует", exit="ok")
                    
        bot_path = bots_folder_path + f"/{self.name}"
        if not os.path.exists(bot_path):
            os.mkdir(bot_path)

        self.settings_path = bot_path + "/settings.json"
        try:
            with open(self.settings_path, "r", encoding="utf-8") as f:
                self.settings = json.load(f)
                
        except:
            self.settings = {}
            w = wn("bot_registration", main_label="type your api-key", entry=True, exit="ok")
            self.settings["api_key"] = w.entered_value
            w = wn("bot_registration", main_label="type your secret-key", entry=True, exit="ok")
            self.settings["secret_key"] = w.entered_value
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        
        self.api_key = self.settings.get("api_key", None)
        self.secret_key = self.settings.get("secret_key", None)

        print("bot started")
        print()
        self.bb_client = api.API(self.api_key, self.secret_key, websocket=True)
        try:
            self.bb_client.check_balance()
        except:
            w = wn("", main_label="API не работает, а значит вы не сможете торговать как реальными, так и демо средствами, " + 
                   "но прочие функции должны работать. Можете с ними ознакомиться", exit="ok", interrupt=True)

        symbols = self.bb_client.get_symbol_list()[:5]
        intervals = api.API.intervals[:3]
        print(dt.datetime.now())
        w = wn(main_label="loading....", interrupt=True, progress_bar=True, func=self.bb_client.a_get_data, symbols=symbols, intervals=intervals, open_interest=True)
        print(dt.datetime.now())

        self.gui = gui.GUI(self.bb_client, self.settings_path)
        self.gui.window.protocol("WM_DELETE_WINDOW",lambda:self.on_closing())
        self.gui.window.mainloop()

    def on_closing(self):
        sys.exit()



