import glob

import numpy as np
import pandas as pd
from tqdm import tqdm
import pickle
from bs4 import BeautifulSoup

def bin_to_table_soup(bin):
    # binからhtmlを読み込み
    with open(bin,'rb') as f:
        html = pickle.load(f)
        tables = pd.read_html(html)
        soup = BeautifulSoup(html,'lxml')
    return tables,soup

# チームで分ける必要ないため、bin_to_data.pyにあるnumは不要
def get_info_by_soup(df:pd.DataFrame,soup):
    # カテゴリ変数をクレンジング(soupを用いて)
    new_df = df.copy()
    # new_df['Player'] = df['Player'].str.replace(' ','').str.replace('\u3000','')
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

    # 次のbin_to_teamstatsからチーム名取るため不要
    # # チーム名
    # home_team = soup.find('div',attrs='team1').find('span',attrs='vs_team_name').text
    # away_team = soup.find('div',attrs='team2').find('span',attrs='vs_team_name').text
    # if num == 4: # Home
    #     new_df['Team'] = home_team
    #     new_df['Op.Team'] = away_team
    # elif num == 5: # Away
    #     new_df['Team'] = away_team
    #     new_df['Op.Team'] = home_team

    return new_df 


def bin_to_teamstats(tables:list):
    team_df = tables[0].copy().iloc[:-1,:]
    team_df = team_df.rename(columns={
        'チーム':'Team','セット':'GetSet','ポイント':'GetPoint',
        '1':'1SetPoint','2':'2SetPoint','3':'3SetPoint','4':'4SetPoint','5':'5SetPoint','合計':'TotalPoint',
        })
        
    # 個人スタッツの最下部から抽出
    team1_df = tables[4]
    team2_df = tables[5]
    team1_stats = team1_df.iloc[-1,-20:].values
    team2_stats = team2_df.iloc[-1,-20:].values
    # RA,Rx,Rg,RSucc = team1_df.iloc[-1,-4:].values
    # print(RA,Rx,Rg,RSucc)
    stats_cols = [
        'AA','AP','AE','ASucc%','AP/S','BAA','BAP','BAE','BASucc%',
        'BP','BP/S','SVA','SVP','SVE','SVx','SVEff%','RA','Rx','Rg','RSucc%'
    ]

    # チーム得点データと連結
    team_stats_df = pd.DataFrame([team1_stats,team2_stats],columns=stats_cols)
    # team_stats_df
    team_df2 = pd.concat([team_df,team_stats_df],axis=1)

    # チームフォルトと相手のミスを追加
    team_stats = tables[3]
    TF1 = team_stats.iloc[-2,1]
    OpE1 = team_stats.iloc[-2,3]
    TF2 = team_stats.iloc[-2,-2]
    OpE2 = team_stats.iloc[-2,-4]
    team_df2.loc[:,'TF'] = [TF1,TF2]  # チームフォルト
    team_df2.loc[:,'OpE'] = [OpE1,OpE2]  # 相手のミス
    cols = team_df2.columns

    for col in cols:
        if 'Get' in col:
            opcol = 'Lost'+ col.replace('Get','')
        else:
            opcol = 'Op'+ col
        # 順番逆にする
        team_df2[opcol] = team_df2[col][::-1].values
    
    return team_df2


division = input('Select division: ')
s_round = '2022-23_regular'
print(s_round)
bin_list = glob.glob('html/{0}/{1}/*.bin'.format(division,s_round))

team_df_list = []
for bin in tqdm(bin_list):
    tables,soup = bin_to_table_soup(bin)
    team_df = bin_to_teamstats(tables)
    team_df = get_info_by_soup(team_df,soup)
    team_df_list.append(team_df)

team_df_all = pd.concat(team_df_list)
team_df_all.to_csv('data/{0}/team_daily_{1}.csv'.format(division,s_round),index=False)