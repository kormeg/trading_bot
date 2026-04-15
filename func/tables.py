import pandas as pd 
import re







def set_postfix(df, interval=None, pf=None):
    if pf == None:
        if type(interval) != str:
            pf = str(interval)+"m"
        else:
            pf = interval
    df.columns = [x+"_"+str(pf) if x!="time" else x for x in df.columns ]
    return df
# ----------------------------------------------------------------------------------------------------------------

def get_postfix(df):
    match = re.findall(r"(.*)(_.*)", df.columns[-1])
    if len(match) == 1:
        pf = match[0][1].strip("_")
        return pf
    return ""

# ----------------------------------------------------------------------------------------------------------------

def drop_postfix(cols=(list, pd.DataFrame)):
    if type(cols) == pd.DataFrame:
        cols = list(cols.columns)
    else:
        cols = list(cols)
    # print(cols)
    l_split = [x.split("_") for x in cols]
    # print(l_split)
    new_cols = ["_".join(x[:-1]) for x in l_split if len(x) > 1 ]
    # print(new_cols, cols)
    if len(cols) == len(new_cols):
        return new_cols
    elif len(cols) == len(new_cols)+1:
        # print(cols[:1] + new_cols)
        return cols[:1] + new_cols
    else:
        return cols
    # new_cols = []
    # for i in cols:
    #     match = re.findall(r"(.*)(_.*)", i)
    #     if len(match) == 1:
    #         new_cols.append(match[0][0])s
    #     else:
    #         return cols
    #         # new_cols.append(i)
    # return new_cols

    # сделать параметр return_df=False сделать проверку если тру и тип не датафрейм raise error

# ----------------------------------------------------------------------------------------------------------------

def time_to_columns(df):
    if len(df) == 0:
        print("empty DataFrame")
        return df
    if type(df.index[0]) == pd._libs.tslibs.timestamps.Timestamp:
        df["time"] = df.index
        # df = df.reset_index(drop=True)
        cols = list(df.columns.values)
        cols = cols[-1:] + cols[:-1]
        df = df[cols]
        df = df.reset_index(drop=True)
        return df
    # df = df.reset_index(drop=True)
    return df

# ----------------------------------------------------------------------------------------------------------------

def time_to_index(df):
    if len(df) == 0:
        print("empty DataFrame")
        return df
    if type(df.index[0]) != pd._libs.tslibs.timestamps.Timestamp:
        df = df.set_index("time")
        return df
    return df

# ----------------------------------------------------------------------------------------------------------------

def set_direction(df, direction=("increase", "decrease")):
    if len(df) == 0:
        print("empty DataFrame")
        return df
    time_ind = False
    if type(df.index[0]) == pd._libs.tslibs.timestamps.Timestamp:
        time_ind = True
    if len(df) == 1:
        return df
    df = time_to_columns(df)
    if df["time"][0] > df["time"][1]:
        if direction =="increase":
            df = df.loc[::-1]
            df = df.reset_index(drop=True)
        if time_ind:
            df = time_to_index(df)
        return df
    if direction == "decrease":
        df = df.loc[::-1]
        df = df.reset_index(drop=True)
    if time_ind:
        df = time_to_index(df)
    

    return df
    
# ----------------------------------------------------------------------------------------------------------------

def to_with_type(orig_df, direction=None, pf=None):
    df = orig_df.copy()
    df = time_to_columns(df)
    if len(df) == 0:
        print("empty DataFrame")
        return df
    cols = list(df.columns.values)
    if type(df[cols[-1]][0]) == str: 
        return df
    if pf:
        pf = pf
    else:
        pf = get_postfix(df)
    cols = drop_postfix(cols)
    df.columns = cols
    first_df = df[df[cols[-2]].notna()]
    second_df = df[df[cols[-1]].notna()]
    first_time = list(first_df["time"].values)
    second_time = list(second_df["time"].values)
    first_list = [[x, cols[-2]] for x in first_df[cols[-2]]]
    second_list = [[x, cols[-1]] for x in second_df[cols[-1]]]
    along_time = first_time + second_time
    along_data = first_list + second_list
    df = pd.DataFrame(along_data, columns=["value", "type"])
    df["time"] = along_time
    df = df.sort_values("time").reset_index(drop=True)
    df = df[["time", "value", "type"]]
    df = set_postfix(df, pf=pf)
    if direction:
        df = set_direction(df, direction)
        df = time_to_index(df)
    return df

# ----------------------------------------------------------------------------------------------------------------

def to_apart(orig_df, direction=None, pf=None):
    df = orig_df.copy()
    df = time_to_columns(df)
    if pf:
        pf = pf
    else:
        pf = get_postfix(df)
    if len(df) == 0:
        print("empty DataFrame")
        return df, df
    cols = list(df.columns.values)
    last_col = cols[-1]
    first_cols = cols[:-1]
    if type(df[last_col][0]) == str:
        types = list(df[last_col].unique())
        final_list = []
        for i in types:
            table = df[df[last_col] == i][first_cols]
            table = table.reset_index(drop=True)
            table.columns = cols[:-2] + [i]
            final_list.append(table)
        final_list = [set_postfix(x, pf=pf) for x in final_list]
        if direction:
            final_list = [set_direction(x, direction) for x in final_list]
        if len(final_list) == 1:
            return final_list[0], pd.DataFrame(columns=final_list[0].columns)
        if len(final_list) == 2:
            if final_list[0][final_list[0].columns[-1]].median() < final_list[1][final_list[1].columns[-1]].median():
                final_list.reverse()
                return final_list
        return final_list
    first_df = df[df[cols[-2]].notna()][first_cols].reset_index(drop=True)
    second_df = df[df[cols[-1]].notna()][cols[:-2] + [cols[-1]]].reset_index(drop=True)
    if direction:
        first_df = set_direction(first_df, direction)
        second_df = set_direction(second_df, direction)
    return first_df, second_df

# ----------------------------------------------------------------------------------------------------------------

def to_along(orig_df, direction=None, pf=None, time_to_ind=False):
    df = orig_df.copy()
    df = time_to_columns(df)
    if pf == None:
        pf = get_postfix(df)
    if len(df) == 0:
        print("empty DataFrame")
        return df
    df.columns = drop_postfix(df.columns)
    cols = list(df.columns.values)
    last_col = cols[-1]
    first_cols = cols[:-1]
    if type(df[last_col][0]) == str:
        types = list(df[last_col].unique())
        final_list = []
        for i in types:
            table = df[df[last_col] == i][first_cols]
            table.columns = cols[:-2] + [i]
            final_list.append(table)
        first_df = final_list[0]
        other_dfs = final_list[1:]
        # display(other_dfs)
        for x in other_dfs:
            df = first_df.merge(x,"outer", on=list(first_df.columns[:-1]))
        df = df.sort_values("time")
    df = set_postfix(df, pf=pf)
    if direction:
        df = set_direction(df, direction)
    if time_to_ind:
        df = time_to_index(df)
    return df

# ----------------------------------------------------------------------------------------------------------------

def get_overall_table(df, dfs=(list, pd.DataFrame), direction="decrease", time_to_ind=True):
    overall_df = df.copy()
    overall_df = set_direction(overall_df, direction)
    if type(dfs) == pd.DataFrame:
        dfs = [dfs]
    dfs = [to_along(x) for x in dfs]
    dfs = [time_to_columns(x) for x in dfs]
    for i in dfs:
        overall_df = overall_df.merge(i, how="outer", on="time")
    overall_df = set_direction(overall_df)
    if time_to_ind:
        overall_df = overall_df.set_index("time")
    
    return overall_df

# ----------------------------------------------------------------------------------------------------------------

# def get_history(client, symbol, interval, for_what, start, end=now_dt, pf=None, time_to_ind=True, 
#                 direction="decrease", moscow=True, category ="linear"):
#     if interval == "D":
#         inter = 60 * 24
#     elif interval == "W":
#         inter = 60*24*7
#     elif interval == "M":
#         print("XZ")
#         return
#     else:
#         inter = interval

#     start = pd.to_datetime(start)
#     end = pd.to_datetime(end)
#     start_tmp = end - dt.timedelta(minutes=200 * inter)
#     candles_tmp = []
#     while start_tmp > start:
#         candles = get_info_bybit(client, symbol, interval, category=category, 
#                                  start=int(time.mktime(start_tmp.timetuple())) * 1000, 
#                                 #  now_timestamp = int(time.mktime(now_dt.timetuple())) * 1000,
#                                  end=int(time.mktime(end.timetuple())) * 1000)
#         end = start_tmp
#         start_tmp = end - dt.timedelta(minutes = 200 * inter)
#         candles_tmp += candles
#     candles = get_info_bybit(client, symbol, interval, category=category, 
#                          start=int(time.mktime(start.timetuple())) * 1000, 
#                          end=int(time.mktime(end.timetuple())) * 1000)
#     candles_tmp += candles

#     df = candles_to_df(candles_tmp, for_what=for_what, moscow=moscow, bybit=True)
#     df = set_postfix(df, interval, pf)
#     df = set_direction(df, direction)
#     if time_to_ind:
#         df = df.set_index("time")
#     return df

