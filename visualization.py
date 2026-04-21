import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from func import tables as tb
from window import Window as wn
from matplotlib.widgets import Cursor


class Visualization:

    def __init__(self, params={}):

        self.plotting_list = []
        self.figsize = params.get("fig_size",(14, 7))
        self.win_color = params.get("win_color","#86a3c4")
        self.bg_color = params.get("bg_color", "#c5d8ed")
        self.grid_color = params.get("grid_color", "gray")
        self.xax_position = params.get("xax_position", 'bottom')
        self.yax_position = params.get("yax_position", "right")
        self.add_win = params.get("add_windows", 0)
        self.axis_index = 1

        if self.add_win >= 3:
            if self.add_win > 3:
                wn(label="you can add no more than three additional charts", exit="ok")
            self.fig, (self.main_ax, self.ax_one, self.ax_two, self.ax_three) = plt.subplots(4, 1, gridspec_kw={'height_ratios': [4, 1, 1, 1]}, figsize=self.figsize, sharex=True)
            self.axis_list = [self.main_ax, self.ax_one, self.ax_two, self.ax_three ]

        elif self.add_win == 2:
            self.fig, (self.main_ax, self.ax_one, self.ax_two) = plt.subplots(3, 1, gridspec_kw={'height_ratios': [5, 1, 1]}, figsize=self.figsize, sharex=True)
            self.axis_list = [self.main_ax, self.ax_one, self.ax_two]

        elif self.add_win == 1:
            self.fig, (self.main_ax, self.ax_one) = plt.subplots(2, 1, gridspec_kw={'height_ratios': [6, 1]}, figsize=self.figsize, sharex=True)
            self.axis_list = [self.main_ax, self.ax_one]
        else:
            self.fig, (self.main_ax) = plt.subplots(1, 1, gridspec_kw={'height_ratios': [7]}, figsize=self.figsize, sharex=True)
            self.axis_list = [self.main_ax]
        
        # self.xlim = self.main_ax.get_xlim() # пределы оси X для относительных рассчетов, ибо datetime не подходит

        # self.fig.set_dpi(120)
        self.fig.set_facecolor(self.win_color)
        plt.subplots_adjust(left=0.04, right=0.92, bottom=0.06, top=0.94)
        plt.xticks(rotation=0, ha='center')


        for ax in self.axis_list:
            ax.set_facecolor(self.bg_color)
            ax.set_axisbelow(True)
            ax.grid(linewidth=0.5, color=self.grid_color, alpha=.5)
            ax.xaxis.set_ticks_position(self.xax_position)
            ax.yaxis.set_ticks_position(self.yax_position)
            ax.tick_params(axis='both', which='major', labelsize=6)
            

        
    def grid_scale(a, b):
        coef = 1
        round_coef = 0
        gap_tops = [180, 250, 335, 420, 505, 590, 675, 760, 845, 930, 1015, 1100, 1185, 1270, 1400]
        grid_step = 10
        c = b - a
        while True:
            if c < 140:
                    a *= 10
                    b *= 10
                    coef /= 10
                    round_coef += 1
                    c = round(b - a)
            elif c >= 1400:
                    a /= 10
                    b /= 10
                    coef *= 10
                    round_coef += 1
                    c = round(b - a)
            else:
                break
        start = round(a + 0.51)
        while start % 10 != 0:
            start += 1
        for i in gap_tops:
            if c > i:
                grid_step += 5
            else: 
                break
        l = []
        x = start
        while x < b:
            l.append(round((x * coef), round_coef ))
            x += grid_step
        return l
    

    def set_axis(self):
        ax = self.axis_list[self.axis_index]
        if self.axis_index < self.add_win:
            self.axis_index += 1
        else:
            self.axis_index = 1
        return ax
    

    def add_dict(self, **kwargs):

        d = {k:v for k, v in kwargs.items()}
        self.plotting_list.append(d)
        


    def add_candles(self, data, symbol, timeframe, colors=["green", "red", "black"]):

        self.symbol = symbol
        self.timeframe = timeframe
        df = data[self.symbol]["intervals"][self.timeframe]["data"].copy()
        df.columns = tb.drop_postfix(df)
        self.index=df.index
        self.up = df[df["close"] >= df["open"]] 
        self.dn = df[df["close"] < df["open"]]
        self.mean_candle = (df["high"] - df["low"]).mean()
        self.max_y = df["high"].max() + self.mean_candle
        self.min_y = df["low"].min() - self.mean_candle
        self.df = df
        if len(colors) != 3:
            colors=["green", "red", "black"]
        self.add_dict(chart_type="candles", chart="main", colors=colors)

    

    def add_dots(self, data, chart="main", symbol=None, timeframe=None, colors=["black"], marks=["o"], mark_size=5, transparency=.5):
        if symbol:
            self.symbol= symbol
        if timeframe:
            self.timeframe = timeframe
        df = data[self.symbol]["intervals"][self.timeframe]["data"].copy()
        df.columns = tb.drop_postfix(df)

        l = []
        if "type" in df.columns:
            for i in df["type"].unique():
                l.append(df[df["type"] == i])
        else:
            l.append(df)
        if len(colors) < len(l):
            colors = colors[:1] * len(l)
        if len(marks) < len(l):
            marks = marks[:1] * len(l)
        self.add_dict(chart_type="dots", chart=chart, data=l, colors=colors, marks=marks, mark_size=mark_size, transparency=transparency)


    
    def add_bars(self, data, c_name=None, chart="add", cut_to_min=False, symbol=None, timeframe=None, colors=["black"], transparency=.4):
        bottom = 0
        if symbol:
            self.symbol = symbol
        if timeframe:
            self.timeframe = timeframe
        df = data[self.symbol]["intervals"][self.timeframe]["data"].copy()
        if c_name:
            df = pd.DataFrame(df[c_name])
            df.columns=["value"]
            
        if chart == "main":
            df = df/ (df.max()/self.mean_candle)*4
            bottom = self.min_y
        if cut_to_min:
            df = df-(df.min()*0.9)
            bottom = df["value"].min()
        if colors:
            if len(colors) > 1:
                colors = colors[:2]
                l = [df[df.index.isin(self.up.index)], df[df.index.isin(self.dn.index)]]
            else:
                l = [df]
        else:
            colors=["black"]
        self.add_dict(chart_type="bars", chart=chart, data=l, colors=colors, transparency=transparency, bottom=bottom)


    
    def add_area(self, data, chart="main", symbol=None, timeframe=None, colors=["black"], width=2, linewidth=1, transparency=.2):

        if symbol:
            self.symbol= symbol
        if timeframe:
            self.timeframe = timeframe
        df = data[self.symbol]["intervals"][self.timeframe]["data"].copy()
        df.columns = ["top", "bottom", "type"]
        l = []
        l.append(df[df["type"] == "up"])
        l.append(df[df["type"] == "down"])
        if len(colors) < len(l):
            colors = colors[:1] * len(l)
        self.add_dict(chart_type="area", chart=chart, data=l, colors=colors, width=width, linewidth=linewidth, align="edge", transparency=transparency)

    
    def add_curve(self, data, chart="add", c_name=None, symbol=None, timeframe=None, colors=["black"], linewidth=1, transparency=.8, h_lines=[]):

        if symbol:
            self.symbol = symbol
        if timeframe:
            self.timeframe = timeframe
        df = data[self.symbol]["intervals"][self.timeframe]["data"].copy()
        if c_name:
            df = pd.DataFrame(df[c_name]) 
            df.columns=["value"]
        if colors:
            if len(colors) > 1:
                colors = colors[:2]
        else:
            colors=["black"]
        self.add_dict(chart_type="curve", chart=chart, data=df, colors=colors, linewidth=linewidth, transparency=transparency, h_lines=h_lines)



    def add_hlines(self, data, chart="main", symbol=None, timeframe=None, colors=["black"], linestyle='-', linewidth=0.4, transparency=.8, titles=[], xmins=[], xmaxs=[]):
        if symbol:
            self.symbol = symbol
        if timeframe:
            self.timeframe = timeframe
        if type(data) in [str, int, float]:
            data = [float(data)]
        if len(colors) < len(data):
            colors = colors + colors[-1:]*(len(data)-len(colors))
        else:
            colors = colors[:len(data)]
        if len(titles) != len(data):
            titles = []
        if len(xmins) != len(data):
            xmins = []
        if len(xmaxs) != len(data):
            xmaxs = []
        self.add_dict(chart_type="hlines", chart=chart, data=data, colors=colors, linestyle=linestyle, linewidth=linewidth, transparency=transparency, titles=titles, xmins=xmins, xmaxs=xmaxs)




    def add_plot(self, 
                 data, 
                 chart_type, 
                 chart=None, 
                 colors=None, 
                 symbol=None, 
                 timeframe=None, 
                 c_name=None, 
                 cut_to_min=False, 
                 h_lines=[], 
                 marks=None, 
                 mark_size=None,  
                 width=None, 
                 linewidth=None, 
                 transparency=None, 
                 linestyle=None, 
                 titles=None, 
                 xmins=None, 
                 xmaxs=None ):

        if timeframe:
            self.timeframe = timeframe
        if symbol:
            self.symbol = symbol
        if not colors:
            colors = ["black"]
        try:
            if chart_type == "dots":
                if not chart:
                    chart = "add"
                if not marks:
                    marks = ["o"]
                if not mark_size:
                    mark_size =  5
                if not transparency:
                    transparency = .5
                self.add_dots(data=data, chart=chart, colors=colors, marks=marks, mark_size=mark_size, transparency=transparency)
            if chart_type == "bars":
                if not chart:
                    chart = "add"
                    if not transparency:
                        transparency = .4
                self.add_bars(data=data, c_name=c_name, chart=chart, cut_to_min=cut_to_min, colors=colors, transparency=transparency)
            if chart_type == "area":
                if not chart:
                    chart = "main"
                if not width:
                    width = 2
                if not linewidth:
                    linewidth = 1
                if not transparency:
                    transparency = .2
                self.add_area( data=data, chart=chart, colors=colors, width=width, linewidth=linewidth, transparency=transparency)
            if chart_type == "curve":
                if not chart:
                    chart = "add"
                if not linewidth:
                    linewidth=1
                if not transparency:
                    transparency=.8
                self.add_curve(data=data, chart=chart, c_name=c_name, colors=colors, linewidth=linewidth, transparency=transparency, h_lines=h_lines)
            if chart_type == "hlines":
                if not chart:
                    chart = "main"
                if not linestyle:
                    linestyle = '-'
                if not linewidth:
                    linewidth = .4
                if not transparency:
                    transparency = .8
                if not titles:
                    titles = []
                if not xmins:
                    xmins = []
                if not xmaxs:
                    xmaxs = []
                self.add_hlines(data=data, chart=chart, colors=colors, linewidth=linewidth, linestyle=linestyle, transparency=transparency, titles=titles, xmins=xmins, xmaxs=xmaxs)                  
        except:
            print("add_plot is not working")



    def candles_plot(self, params:dict):

        self.main_ax.set_ylim(self.min_y, self.max_y)
        l =  Visualization.grid_scale(self.min_y, self.max_y)  
        self.main_ax.set_yticks(l)
        self.main_ax.set_title(label="#" + self.symbol + "#" + str(self.timeframe) + "#")
        for ax in self.axis_list:
            ax.grid(linewidth=0.5, color="gray", alpha=.5)
            inter = int(float(self.timeframe)/5)
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=inter))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m %H:%M"))

        self.candle_width = dt.timedelta(minutes=int(self.timeframe)*.85)
        self.shadow_width = self.candle_width/5
 
        self.main_ax.bar(self.up.index, self.up["close"]-self.up["open"], self.candle_width, bottom=self.up["open"], color=params["colors"][0], alpha=.6) 
        self.main_ax.bar(self.up.index, self.up["high"]-self.up["close"], self.shadow_width, bottom=self.up["close"], color=params["colors"][2], alpha=.6) 
        self.main_ax.bar(self.up.index, self.up["low"]-self.up["open"], self.shadow_width, bottom=self.up["open"], color=params["colors"][2], alpha=.6) 

        self.main_ax.bar(self.dn.index, self.dn["close"]-self.dn["open"], self.candle_width, bottom=self.dn["open"], color=params["colors"][1], alpha=.6) 
        self.main_ax.bar(self.dn.index, self.dn["high"]-self.dn["open"], self.shadow_width, bottom=self.dn["open"], color=params["colors"][2], alpha=.6) 
        self.main_ax.bar(self.dn.index, self.dn["low"]-self.dn["close"], self.shadow_width, bottom=self.dn["close"], color=params["colors"][2], alpha=.6)

        line_color = "red" if self.df["close"][0] < self.df["close"][1] else "green"
        self.main_ax.axhline(y=self.df["close"][0], color=line_color, linestyle='--', linewidth=0.2) #текущая цена
        self.main_ax.text(x=self.df.index[0]+ dt.timedelta(minutes=int(self.timeframe)*1), y=self.df["close"][0], s=str(self.df["close"][0]), ha='left', color=line_color, fontsize=6)
        self.cursor = Cursor(self.main_ax, useblit=True, color='black', linewidth=.5,  linestyle='--')
        

        

    def dot_plot(self, params:dict):
        if params["chart"] == "main":  
            ax = self.main_ax 
        else:
            ax = self.set_axis()
        for i in range(len(params["data"])):
            ax.plot(
                params["data"][i].index,
                params["data"][i]["value"],
                params["marks"][i], 
                c = params["colors"][i],
                ms = params["mark_size"], 
                alpha = params["transparency"]
            )


    def bar_plot(self, params:dict):
        if params["chart"] == "main":
            ax = self.main_ax
        else:
            ax = self.set_axis()
        # print(params["data"])
        for i in range(len(params["data"])):
            
            ax.bar(params["data"][i].index,
                   params["data"][i]["value"],
                   self.candle_width,
                   color=params["colors"][i],
                   bottom=params["bottom"],
                   alpha=params["transparency"]
                   )
            
        
    def area_plot(self, params:dict):
        for i in range(len(params["data"])):
            self.main_ax.bar(
                params["data"][i].index, 
                params["data"][i]["top"] - params["data"][i]["bottom"], 
                width = int(self.timeframe)/1000 * params["width"], 
                bottom=params["data"][i]["bottom"], 
                color=params["colors"][i], 
                align=params["align"], 
                alpha= params["transparency"], 
                edgecolor=params["colors"][i], 
                linewidth=params["linewidth"]
            )
    
    
    def curve_plot(self, params:dict):
        # print(params)
        if params["chart"] == "main":
            ax = self.main_ax
        else:
            ax = self.set_axis()
            if params["h_lines"]:
                for hl in params["h_lines"]:
                    ax.axhline(y=hl, color=params["colors"][-1], linestyle='-', linewidth=0.4)
        ax.plot(params["data"].index,
                params["data"]["value"],
                linewidth=params["linewidth"],
                color=params["colors"][0],
                alpha=params["transparency"]
                )


    def hlines_plot(self, params:dict):
        if params["chart"] == "main":
            ax = self.main_ax
        else:
            ax = self.set_axis()

        if type(self.df.index[0]) == pd._libs.tslibs.timestamps.Timestamp:
            xlim = (self.df.index[-1], self.df.index[0] + dt.timedelta(minutes=int(self.timeframe)*5))
            num_xlim = [mdates.date2num(x) for x in xlim]
        else:
            xlim = (self.df.index[-1], self.df.index[0])
            num_xlim = xlim

        if not params["xmins"]:
            params["xmins"] = [xlim[0]]*len(params["data"])
            num_xmins = [num_xlim[0]]*len(params["data"])
            params["rel_xmins"] = [(x - num_xlim[0]) / (num_xlim[1] - num_xlim[0]) for x in num_xmins]
        elif type(params["xmins"][0]) == pd._libs.tslibs.timestamps.Timestamp:
            params["rel_xmins"] = [(mdates.date2num(x) - num_xlim[0]) / (num_xlim[1] - num_xlim[0]) for x in params["xmins"]]
        else:
            params["rel_xmins"] = [(x - num_xlim[0]) / (num_xlim[1] - num_xlim[0]) for x in params["xmins"]]
        if not params["xmaxs"]:
            params["xmaxs"] = [xlim[1]]*len(params["data"])
            num_xmaxs = [num_xlim[1]]*len(params["data"])
            params["rel_xmaxs"] = [(x - num_xlim[0]) / (num_xlim[1] - num_xlim[0]) for x in num_xmaxs]
        elif type(params["xmaxs"][0]) == pd._libs.tslibs.timestamps.Timestamp:
            params["rel_xmaxs"] = [(mdates.date2num(x) - num_xlim[0]) / (num_xlim[1] - num_xlim[0]) for x in params["xmaxs"]]
        else:
            params["rel_xmaxs"] = [(x - num_xlim[0]) / (num_xlim[1] - num_xlim[0]) for x in params["xmaxs"]]


        for i in range(len(params["data"])):
            if params["xmins"][i] >= xlim[0]:
                ax.axhline(y=params["data"][i], 
                        xmin=params["rel_xmins"][i], 
                        xmax=params["rel_xmaxs"][i], 
                        color=params["colors"][i], 
                        linestyle=params["linestyle"], 
                        linewidth=params["linewidth"])
                if params["titles"]:
                    ax.text(x=params["xmins"][i], 
                            y=params["data"][i], 
                            s=params["titles"][i], 
                            ha='left', 
                            color=params["colors"][i], 
                            fontsize=12)
                


    def visualize(self):
        for i in self.plotting_list:
            if i["chart_type"] == "candles":
                self.candles_plot(i)
            elif i["chart_type"] == "dots":
                self.dot_plot(i)
            elif i["chart_type"] == "area":
                self.area_plot(i)
            elif i["chart_type"] == "bars":
                self.bar_plot(i)
            elif i["chart_type"] == "curve":
                self.curve_plot(i)
            elif i["chart_type"] == "hlines":
                self.hlines_plot(i)
        self.plotting_list = []
