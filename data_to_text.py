import glob

import numpy as np
import pandas as pd
from tqdm import tqdm
import pickle
from bs4 import BeautifulSoup

def astype_df(df:pd.DataFrame):
    # 型変換
    to_int_list = [
        'AA','AP','AE','BAA','BAP','BAE','BP','SVA','SVP','SVE','SVx','RA','Rx','Rg',
        'WinPoint','OpWinPoint','1setPoint','2setPoint','3setPoint','4setPoint','5setPoint','TotalPoint',
        'Op1setPoint','Op2setPoint','Op3setPoint','Op4setPoint','Op5setPoint','OpTotalPoint',
        'Spectators'
        ]
    to_float_list = ['ASucc%','AP/S','BASucc%','BP/S','SVEff%','RSucc%']
    to_datetime_list = ['Date','1setTime','2setTime','3setTime','4setTime','5setTime']
    for col in df.columns:
        # print(individual_df_all[col].dtype)
        if col in to_int_list:
            df[col] = df[col].astype('i8')
        elif col in to_float_list:
            df[col] = df[col].replace('-',np.nan).astype('f8')
        elif col in to_datetime_list:
            df[col] =  pd.to_datetime(df[col])
    return df    

def bin_to_table_soup(bin):
    # binからhtmlを読み込み
    with open(bin,'rb') as f:
        html = pickle.load(f)
        tables = pd.read_html(html)
        soup = BeautifulSoup(html,'lxml')
    return tables,soup

def get_info_by_soup(num:int,df:pd.DataFrame,soup):
    # カテゴリ変数をクレンジング(soupを用いて)
    new_df = df.copy()
    new_df['Player'] = df['Player'].str.replace(' ','').str.replace('\u3000','')
    # BeautifulSoupから取得したデータを追記
    new_df['GameId'] = soup.find('p',attrs='match_no left').find('span').text # 試合番号
    new_df['Date'] = soup.find('p',attrs='match_date left').find('span').text # 開催日
    new_df['Place'] = soup.find('p',attrs='match_place left').find('span').text # 開催地
    new_df['Venue'] = soup.find('p',attrs='venue').find('span').text # 会場
    
    # 人・時間 & 審判 header2 cf & li
    info_columns = ['Spectators','StartTime','EndTime','GameTime',
                    'JURY','ChiefUmpire','SubUmpire','Judge']
    lis =  soup.find('div',attrs='header2 cf').find_all('li') 
    for info_column,li in zip(info_columns,lis):
        span = li.find_all('span')[-1].text.replace('　','')
        new_df[info_column] = span

    # チーム名
    home_team = soup.find('div',attrs='team1').find('span',attrs='vs_team_name').text
    away_team = soup.find('div',attrs='team2').find('span',attrs='vs_team_name').text
    if num == 4: # Home
        new_df['Team'] = home_team
        new_df['Op.Team'] = away_team
    elif num == 5: # Away
        new_df['Team'] = away_team
        new_df['Op.Team'] = home_team

    return new_df 

def get_info_by_table(num:int,df:pd.DataFrame,tables:list):
    # カテゴリ変数をクレンジング(tableを用いて)
    new_df = df.copy()
    point_table = tables[0]
    info_columns1 = ['WinPoint','1setPoint','2setPoint','3setPoint','4setPoint','5setPoint','TotalPoint']
    info_columns1op = ['Op'+col for col in info_columns1]
    info_columns2 = ['1setTime','2setTime','3setTime','4setTime','5setTime','TotalTime']
    home_info = point_table.iloc[0,:].values # Homeの勝ち点・得点
    away_info = point_table.iloc[1,:].values # Awayの勝ち点・得点
    time_info = point_table.iloc[2,:].values # 時間
    for i in range(len(info_columns1)):
        if home_info[i+2]==np.nan: # セットが無い時
            new_df[info_columns1[i]],new_df[info_columns1op[i]] = 0,0
        if num == 4: # Home
            new_df[info_columns1[i]] = home_info[i+2]
            new_df[info_columns1op[i]] = away_info[i+2]
        elif num == 5: # Away
            new_df[info_columns1[i]] = away_info[i+2]
            new_df[info_columns1op[i]] = home_info[i+2]
    for i in range(len(info_columns2)): # 共通
        new_df[info_columns2[i]] = time_info[i+3]
    

    return new_df
