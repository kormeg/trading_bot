import pandas as pd
from pprint import pprint
from IPython.display import display
from func import tables as tb
from ta.momentum import StochasticOscillator


# ----------------------------------------------------------------------------------------------------------------

def fractals(data, size):
    df=data.copy()
    df = tb.time_to_index(df)
    l = []
    for i in range(size, len(df)-size):
        frag = df[i-size: i+size+1]
        if frag["high"][size] == frag["high"].max() and df["high"][i] not in df["high"][i-size:i].values:
            l.append([df.index[i], df["high"][i], "high"])
        if frag["low"][size] == frag["low"].min() and df["low"][i] not in df["low"][i-size: i].values:
            l.append([df.index[i], df["low"][i], "low"])
    df = pd.DataFrame(l, columns = ["time", "value", "type"])
    return tb.time_to_index(df)

# ----------------------------------------------------------------------------------------------------------------

def key_fractals(data, form="", direction="increase", time_to_ind=True, control=False):

    # df = fractals(data, pnp_size)
    df = data.copy()
    # pf = tb.get_postfix(df)
    df = tb.to_with_type(df)
    df = tb.set_direction(df, "increase")
    df.columns = ["time", "value", "type"]
    # df["type"] = df["type"].replace("up", "high").replace("down", "low")
    new_list = []
    try:
        first_down_row = df[df["type"] == "low"].head(1).reset_index(drop=True)
        last_down = [first_down_row["time"][0], first_down_row["value"][0], first_down_row["type"][0]]
        new_list.append(last_down)
    except:
        pass
    try:
        first_up_row = df[df["type"] == "high"].head(1).reset_index(drop=True)
        last_up = [first_up_row["time"][0], first_up_row["value"][0], first_up_row["type"][0]]
        new_list.append(last_up)
    except:
        pass
    if len(new_list) > 1:
        if new_list[0][0] > new_list[1][0]:
            new_list.reverse()
    if control:
        pprint(new_list)
        print("start of cicle \n")
    for i in range(len(df)):
        if control:
            print(i)
        if df["type"][i] == "high" and df["value"][i] >= last_up[1] and df["time"][i] != last_up[0]:
            new_element = [df["time"][i], df["value"][i], df["type"][i]]
            new_list.append(new_element)
            last_up = new_list[-1]
            if control:
                print(f"new_element \n {new_element} \n")
                pprint(new_list)
                print(f"last_up \n {last_up} \n")
            if new_list[-2][2] == "high":
                start = new_list[-2][0]
                end = new_list[-1][0]
                mid_lows = df[(df["time"] >= start) & (df["time"] <= end) & (df["type"] == "low")]
                mid_lower = mid_lows[mid_lows["value"] == mid_lows["value"].min()].reset_index(drop=True)
                if control:
                    print("second_term \n")
                    print(f"start {start} \n end {end} \n")
                    print(f"middle lower \n {mid_lower}\n")
                if len(mid_lower) > 0:
                    # if len(mid_lower) > 1:
                    #     print("attention!!!!!!! more then one middle lows")
                    for j in range(len(mid_lower)):
                        new_element = [mid_lower["time"][j], mid_lower["value"][j], mid_lower["type"][j]]
                        new_list.insert(-1, new_element )
                        last_down = new_list[-2]
                        if control:
                            print(f"new middle element {new_element}")
                            pprint(new_list)
                            print(f"last down \n {last_down}\n")

                else:
                    new_list.pop(-2)
                    if control:
                        print("some high element poped")
                        pprint(new_list)
                    
        if df["type"][i] == "low" and df["value"][i] <= last_down[1] and df["time"][i]!=last_down[0]:
            new_element = [df["time"][i], df["value"][i], df["type"][i]]
            new_list.append(new_element)
            last_down = new_list[-1]
            if control:
                print(f"new_element \n {new_element} \n")
                pprint(new_list)
                print(f"last_down \n {last_down} \n")
            if new_list[-2][2] == "low":
                start = new_list[-2][0]
                end = new_list[-1][0]
                mid_highs = df[(df["time"] >= start) & (df["time"] <= end) & (df["type"] == "high")]
                mid_higher = mid_highs[mid_highs["value"] == mid_highs["value"].max()].reset_index(drop=True)
                if control:
                    print("second_term \n")
                    print(f"start {start} \n end {end} \n")
                    print(f"middle higher \n {mid_higher} \n")
                if len(mid_higher) > 0:
                    # if len(mid_higher) > 1:
                        # print("attention!!!!!!! more then one middle highs")
                    for j in range(len(mid_higher)):
                        new_element = [mid_higher["time"][j], mid_higher["value"][j], mid_higher["type"][j]]
                        new_list.insert(-1, new_element)
                        last_up = new_list[-2]
                        if control:
                            print(f"new middle element {new_element}")
                            pprint(new_list)
                            print(f"last up \n {last_up}\n")

                else:
                    new_list.pop(-2)
                    if control:
                        print("some low element poped")
                        pprint(new_list)

    new_df = pd.DataFrame(new_list, columns = ["time", "value", "type"])
    # new_df["type"] = new_df["type"].replace("high", "up").replace("low", "down")
    # new_df = tb.set_postfix(new_df, pf=pf)
    new_df = tb.set_direction(new_df, direction)
    if form == "along":
        new_df = tb.to_along(new_df)
        if time_to_ind:
            new_df = tb.time_to_index(new_df)
            return new_df
    if form == "apart":
        first, second = tb.to_apart(new_df, direction)
        if time_to_ind:
            first = tb.time_to_index(first)
            second = tb.time_to_index(second)
        return first, second
    if time_to_ind:
        new_df = tb.time_to_index(new_df)
    return new_df

# ----------------------------------------------------------------------------------------------------------------

def choch(df, fractals, form=None, direction="increase", time_to_ind=False, control=False):
    pf = tb.get_postfix(fractals)
    new_df = df.copy()
    new_df = tb.set_direction(new_df, "increase")
    fr = fractals.copy()
    print("ok")
    high_fr, low_fr = tb.to_apart(fr, direction="increase")
    print("ok")
    if high_fr.columns[1][:3] == "low":
        high_fr, low_fr = low_fr, high_fr
    new_df.columns = ["time", "open", "high", "low", "close", "volume"]
    high_fr.columns = ["time", "high_fr"]
    low_fr.columns = ["time", "low_fr"]
    if control:
        display("ohlcv",new_df.head(), "high fractals", high_fr.head(), "low fractals", low_fr.head())
    
    choch = []
    if control:
        print("bullish choch cicle start\n")
    for i in range(1, len(high_fr)):
        if control:
            print(i)
        if high_fr["high_fr"][i] < high_fr["high_fr"][i-1]:
            start = high_fr["time"][i]
            end = new_df["time"][-1:].values[0]
            if start != high_fr["time"].tail(1).values[0]:
                if high_fr["high_fr"][i] < high_fr["high_fr"][i+1]:
                    gap = new_df[(new_df["time"] > start) & (new_df["time"] <= end)]
                    gap = gap.reset_index(drop=True)
                    if control:
                        print("start\n", start, high_fr["high_fr"][i])
                        print("end\n",end, high_fr["high_fr"][i+1])
                        display(gap)
                    flag = 0
                    for j in range(len(gap)):
                        if flag == 0:
                            last_peak = high_fr["high_fr"][i]
                            current_high = gap["high"][:j].max()
                            if gap["close"][j] > last_peak and gap["close"][j] > current_high :
                                if control:
                                    print("bullish choch")
                                if last_peak > current_high:
                                    choch.append([gap["time"][j], high_fr["time"][i], last_peak, "bull_chh"])
                                else:
                                    choch.append([gap["time"][j], high_fr["time"][i], current_high, "bull_chh"])
                                flag = 1
            else:
                gap = new_df[(new_df["time"] > start) & (new_df["time"] <= end)]
                gap = gap.reset_index(drop=True)
                if control:
                    print("start\n", start, high_fr["high_fr"][i])
                    print("end\n",end, high_fr["high_fr"][i+1], "last")
                    display(gap)
                flag = 0
                for j in range(len(gap)):
                    if flag == 0:
                        last_peak = high_fr["high_fr"][i]
                        current_high = gap["high"][:j].max()
                        if gap["close"][j] > last_peak and gap["close"][j] > current_high :
                            if control:
                                print("bullish choch")
                            if last_peak > current_high:
                                choch.append([gap["time"][j], high_fr["time"][i], last_peak, "bull_chh"])
                            else:
                                choch.append([gap["time"][j], high_fr["time"][i], current_high, "bull_chh"])
                            flag = 1

    if control:
        print("bearish choch cicle start\n")
    for i in range(1, len(low_fr)):
        if control:
            print(i)
        if low_fr["low_fr"][i] > low_fr["low_fr"][i-1]:
            start = low_fr["time"][i]
            end = new_df["time"][-1:].values[0]
            if start != low_fr["time"].tail(1).values[0]:
                if low_fr["low_fr"][i] > low_fr["low_fr"][i+1]:
                    gap = new_df[(new_df["time"] > start) & (new_df["time"] <= end)]
                    gap = gap.reset_index(drop=True)
                    if control:
                        print("start\n", start, low_fr["low_fr"][i])
                        print("end\n", end, low_fr["low_fr"][i+1])
                        display(gap)
                    flag = 0
                    for j in range(len(gap)):
                        if flag == 0:
                            last_pit = low_fr["low_fr"][i]
                            current_low = gap["low"][:j].min()
                            if gap["close"][j] < last_pit and gap["close"][j] < current_low:
                                if control:
                                    print("bearish choch")
                                if last_pit < current_low:
                                    choch.append([gap["time"][j], low_fr["time"][i], last_pit, "bear_chh"])
                                else:
                                    choch.append([gap["time"][j], low_fr["time"][i], current_low, "bear_chh"])
                                flag = 1
            else:
                gap = new_df[(new_df["time"] > start) & (new_df["time"] <= end)]
                gap = gap.reset_index(drop=True)
                if control:
                    print("start\n", start, low_fr["low_fr"][i])
                    print("end\n", end, low_fr["low_fr"][i+1], "last")
                    display(gap)
                flag = 0
                for j in range(len(gap)):
                    if flag == 0:
                        last_pit = low_fr["low_fr"][i]
                        current_low = gap["low"][:j].min()
                        if gap["close"][j] < last_pit and gap["close"][j] < current_low:
                            if control:
                                print("bearish choch")
                            if last_pit < current_low:
                                choch.append([gap["time"][j], low_fr["time"][i], last_pit, "bear_chh"])
                            else:
                                choch.append([gap["time"][j], low_fr["time"][i], current_low, "bear_chh"])
                            flag = 1

    if control:
        print("finish")
    
    choch = pd.DataFrame(choch, columns=["time", "last_peak_time", "value", "type"]).sort_values("time", ascending=True).reset_index(drop=True)
    choch = tb.set_postfix(choch, pf=pf)
    choch = tb.set_direction(choch, direction)
    if len(choch) == 0:
        print("no choches")
        return choch
    if len(choch) > 1:
        drop_ind = []
        for i in range(1,len(choch)):
            if choch[choch.columns[1]][i] < choch["time"][i-1]:
                drop_ind.append(choch.index[i])
        choch = choch.drop(index=drop_ind).reset_index(drop=True)

    if form == "for_visualization":
        return choch
    
    cols = list(choch.columns.values)
    choch = choch[[cols[0], cols[2], cols[3]]]

    if form == "with_type":
        return choch

    if form == "apart":
        first, second = tb.to_apart(choch)
        if time_to_ind:
            first = first.set_index("time")
            second = second.set_index("time")
        return first, second
    choch = tb.to_along(choch)
    return choch

# ----------------------------------------------------------------------------------------------------------------

# def equal_highs(high_fractals):
#     high_fractals
#     for i in range(high_fractals):


# ----------------------------------------------------------------------------------------------------------------

def imbalance(data, direction="increase"):
    df = data.copy()
    pf = tb.get_postfix(df)
    df = tb.set_direction(df, "increase")
    df = tb.time_to_columns(df)
    # df.columns = ["time","open", "high", "low", "close"]
    df.columns = tb.drop_postfix(df)
    imbalance = []
    imbalances = []
    for i in range(2, len(df)-1):
        if df["close"][i] > df["open"][i] and \
        df["high"][i-2] > df["high"][i-1] and \
        df["low"][i-2] < df["low"][i-1] and \
        df["high"][i-2] < df["low"][i+1]:
            imbalance.append(df["time"][i])
            imbalance.append(df["high"][i-2])
            imbalance.append(df["low"][i+1])
            imbalance.append("up")
            imbalances.append(imbalance)
            imbalance = []
        elif df["close"][i] > df["open"][i] and \
        (df["high"][i-2] < df["high"][i-1] or \
        df["low"][i-2] > df["low"][i-1]) and \
        df["high"][i-1] < df["low"][i+1]:
            imbalance.append(df["time"][i])
            imbalance.append(df["high"][i-1])
            imbalance.append(df["low"][i+1])
            imbalance.append("up")
            imbalances.append(imbalance)
            imbalance = []
        elif df["close"][i] < df["open"][i] and \
        df["high"][i-2] > df["high"][i-1] and \
        df["low"][i-2] < df["low"][i-1] and \
        df["low"][i-2] > df["high"][i+1]:
            imbalance.append(df["time"][i])
            imbalance.append(df["low"][i-2])
            imbalance.append(df["high"][i+1])
            imbalance.append("down")
            imbalances.append(imbalance)
            imbalance = []
        elif df["close"][i] < df["open"][i] and \
        (df["high"][i-2] < df["high"][i-1] or \
        df["low"][i-2] > df["low"][i-1]) and \
        df["low"][i-1] > df["high"][i+1]:
            imbalance.append(df["time"][i])
            imbalance.append(df["low"][i-1])
            imbalance.append(df["high"][i+1])
            imbalance.append("down")
            imbalances.append(imbalance)
            imbalance = []
    imbalances = pd.DataFrame(imbalances, columns=["time", "up_imb", "dn_imb", "imb_type"])
    # imbalances = tb.set_postfix(imbalances, pf=pf)
    imbalances = tb.set_direction(imbalances, direction)
    imbalances = tb.time_to_index(imbalances)

    return imbalances

# ----------------------------------------------------------------------------------------------------------------

def stoch(data, length, smooth=1, d=False):
    df = data.copy()
    stochastic = StochasticOscillator(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        window=length,
        smooth_window=smooth)
    # stoch = df.drop(columns=["open", "high", "low", "colse", "volume", "dk"], inplace=True)

    stoch = stochastic.stoch().to_frame(name="value")
    stoch = stoch.dropna()
    
    if d:
        stochastic.stoch_signal()
    return stoch
