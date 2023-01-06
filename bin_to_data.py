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

def divide_set(point:str,df:pd.DataFrame):
    # 1セットあたりの得点等に換算する
    # ランキングではAP/SとBP/Sのみ
    new_df = df.copy()
    point_by_set = point + '/S'
    new_df[point_by_set] = (df[point]/df['Set']).round(2)
    return new_df


def calc_percent(df:pd.DataFrame):
    # %系(アタック決定率、バックアタック決定率、サーブ効果率、サーブレシーブ成功率)を計算する
    new_df = df.copy()
    new_df['ASucc%'] = (df['AP']*100/df['AA']).round(1)
    new_df['BASucc%'] = (df['BAP']*100/df['BAA']).round(1)
    new_df['SVEff%'] = ((df['SVP']*100+df['SVx']*25-df['SVE']*25)/df['SVA']).round(1)
    new_df['RSucc%'] = ((df['Rx']*100+df['Rg']*50)/df['RA']).round(1)
    return new_df


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


# def data_cleansing_value(df:pd.DataFrame):
#     # 量的変数をクレンジング
#     new_df = df.copy()
#     new_df['ASucc%'] = ((df['AP'] / df['AA']) * 100).round(1)
#     new_df['AEff%'] = (((df['AP']-df['AE']) / df['AA']) * 100).round(1)
#     new_df['BASucc%'] = ((df['BAP'] / df['BAA']) * 100).round(1)
#     new_df['BAEff%'] = (((df['BAP']-df['BAE']) / df['BAA']) * 100).round(1)
#     # AP/S,BP/S: チームでは変更必要
#     new_df['AP/S'] = (df['AP'] / df['Set']).round(2)
#     new_df['BP/S'] = (df['BP/S'] / df['Set']).round(2)
#     new_df['SVEff%'] = ((df['SVP'] * 100 + df['SVx'] * 25 - df['SVE'] * 25) / df['SVA']).round(1)
#     new_df['RSucc%'] = ((df['Rx'] * 100 + df['Rg'] * 50) / df['RA']).round(1)
#     return new_df


# def table_to_stats(num:int, table:list):
#     stats_df = table[num]
#     return stats_df


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


def table_to_individual_stats(num:int,columns:list,tables:list,soup,soup_info:bool,table_info:bool):
    # htmlテーブルから個人スタッツを
    # 4: home, 5: Away
    individual_stats_df = tables[num].iloc[1:-1,:]
    # individual_stats_df.columns = individual_stats_df.columns.get_level_values(1)
    individual_stats_df.columns = columns
    if soup_info == True:
        individual_stats_df = get_info_by_soup(num,individual_stats_df,soup)
    if table_info == True:
        individual_stats_df = get_info_by_table(num,individual_stats_df,tables)
    # individual_stats_df = data_cleansing_value(individual_stats_df)
    return individual_stats_df

# s_id_dict = {'v1_m': '334', 'v2_m': '336',
#              'v3_m': '337', 'v1_w': '333', 'v2_w': '335'}

# カラム名
columns = ['背番号', 'リベロ', '選手', '出場セット',
            '1set', '2set', '3set', '4set', '5set',
            'アタック打数', 'アタック得点', 'アタック失点',
            'アタック決定率', 'アタック平均セット',
            'バックアタック打数', 'バックアタック得点', 'バックアタック失点', 'バックアタック決定率',
            'ブロック得点', 'ブロック平均セット', 'サーブ打数', 'サーブ得点',
            'サーブ失点', 'サーブ効果', 'サーブ効果率', 'サーブレシーブ受数',
            'サーブレシーブ成功・優', 'サーブレシーブ成功・良',
            'サーブレシーブ成功率']

columns_e = ['No.', 'L', 'Player', 'Set', '1set', '2set', '3set', '4set', '5set',
            'AA', 'AP', 'AE', 'ASucc%', 'AP/S', 'BAA', 'BAP', 'BAE', 'BASucc%',
            'BP', 'BP/S', 'SVA', 'SVP', 'SVE', 'SVx', 'SVEff%',
            'RA', 'Rx', 'Rg', 'RSucc%']

division = input('Select division: ')
s_round = '2022-23_regular'
# s_id = s_id_dict[division]
bin_list = glob.glob('html/{0}/{1}/*.bin'.format(division,s_round))

individual_df_list = []
for bin in tqdm(bin_list):
    tables,soup = bin_to_table_soup(bin)
    individual_df_home = table_to_individual_stats(4,columns_e,tables,soup,soup_info=True,table_info=False)
    individual_df_away = table_to_individual_stats(5,columns_e,tables,soup,soup_info=True,table_info=False)
    individual_df_list.append(individual_df_home)
    individual_df_list.append(individual_df_away)

individual_df_all = pd.concat(individual_df_list)
individual_df_all = astype_df(individual_df_all)
individual_df_all.to_csv('data/{0}/individual_daily_{1}.csv'.format(division,s_round),index=False)

print(individual_df_all.head())
print(individual_df_all.shape)