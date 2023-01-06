import glob
import time
import re

import pandas as pd
from bs4 import BeautifulSoup
import urllib.request as req
import requests
from tqdm import tqdm
import pickle


def create_url_list(s_id:str):
    print('create url list...')
    headers = {"User-Agent": "Mozilla/5.0"}
    url = 'https://www.vleague.jp/round/list/{}'.format(s_id)
    request = req.Request(url, headers=headers)
    response = req.urlopen(request)
    parse_html = BeautifulSoup(response, 'html.parser')

    # ページ数取得
    hrefs = parse_html.find_all('a', href=re.compile("pg"))
    # print(hrefs)
    if len(hrefs) > 0:
        pages = int(hrefs[-2].text)  # 後ろから2番目が最終ページを表す為(1番目は次のページ)
        print(pages)
    else:
        pages = 1  # ページ数の無い場合は1ページ

    id_list = []
    # 各ページからidを取得
    for pg in tqdm(range(1, pages+1)):
        url = 'https://www.vleague.jp/round/list/{0}?pg={1}'.format(s_id, pg)
        request = req.Request(url, headers=headers)
        response = req.urlopen(request)
        parse_html = BeautifulSoup(response, 'html.parser')
        tables = parse_html.find_all('table')
        trs = tables[0].find_all('a', href=re.compile("/form/b"))
        for tr in trs:
            id = tr.attrs['href'][-5:]
            id_list.append(id)
        time.sleep(1)
    # print(id_list)
    return id_list
        
def b_to_bin(division,s_round,id_list: list,bin_id: list):
    print('create bin file...')
    for id in tqdm(id_list):
        # bin_idに無いものはスクレイピング
        if id not in bin_id:                
            # print(id)
            time.sleep(1)
            url = 'https://www.vleague.jp/form/b/' + id
            html = requests.get(url).text
            try:
                # ファイルの存在を確認
                pd.read_html(html)
                with open('html/{0}/{1}/{2}.bin'.format(division,s_round,id),'wb') as f:
                    pickle.dump(html,f)
            except:
                pass
    return 


s_round = '2022-23_regular'
s_id_dict = {'v1_m': '334', 'v2_m': '336',
             'v3_m': '337', 'v1_w': '333', 'v2_w': '335'}
# s_round = '2021-22_regular'
# s_id_dict = {'v1_m': '318', 'v2_m': '320',
#              'v3_m': '321', 'v1_w': '317', 'v2_w': '319'}
# s_round = '2020-21_regular'
# s_id_dict = {'v1_m': '301', 'v2_m': '299',
#              'v3_m': '300', 'v1_w': '303', 'v2_w': '302'}
# s_round = '2019-20_regular'
# s_id_dict = {'v1_m': '283', 'v2_m': '288',
#              'v3_m': '287', 'v1_w': '277', 'v2_w': '281'}
# s_round = '2018-19_regular'
# s_id_dict = {'v1_m': '258', 'v2_m': '266',
#              'v3_m': '267', 'v1_w': '269', 'v2_w': '264'}
# s_round = '2017-18_regular'
# s_id_dict = {'v1_m': '241', 'v2_m': '247',
#              'v3_m': '250', 'v1_w': '243', 'v2_w': '248'}


division = input('Select division: ')
s_id = s_id_dict[division]
bin_list = glob.glob('html/{0}/{1}/*.bin'.format(division,s_round))
bin_id = [b[-9:-4] for b in bin_list]

id_list = create_url_list(s_id)
b_to_bin(division,s_round,id_list,bin_id)