import re
import time
from typing import Union

import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from common import rm_newline
from typing import Dict, List


def get_season_contestants(soup: BeautifulSoup, season, series):
    table = soup.find('table', class_='sortable')
    queens = []
    queen_data = table.find_all('tr')
    columns = [rm_newline(col.get_text()).lower(
    ) for col in queen_data[0].find_all('th')]
    for q in queen_data[1:]:
        row = q.find_all(['th', 'td'])
        queen = {col[0]: re.sub(r'(\n)|(\[[a-z]\])', '', col[1].get_text())
                 for col in zip(columns, row)}
        queen['season'] = season + 1
        queen['series'] = series
        if 'current city' in queen.keys():
            queen['city'] = queen['current city']
            queen.pop('current city')
        if 'hometown' in queen.keys():
            if 'city' not in queen.keys():
                queen['city'] = queen['hometown']
            queen.pop('hometown')
        queens.append(pd.Series(queen))
    return pd.DataFrame(queens).fillna(method='ffill')


def get_series_contestants(series_name: str, soup_list: List[BeautifulSoup]) -> pd.DataFrame:
    ret_frames = []
    for season, soup in enumerate(soup_list):
        ret_frames.append(get_season_contestants(soup, season, series_name))
    return pd.concat(ret_frames)


def get_all_contestants(soups: Dict[str, List[BeautifulSoup]]) -> pd.DataFrame:
    all_queens = []
    for name, soup_list in soups.items():
        all_queens.append(get_series_contestants(name, soup_list))
    return pd.concat(all_queens).reset_index(drop=True)


def clean_queens(df: pd.DataFrame) -> pd.DataFrame:
    queens = df.copy()
    queens.age = queens.age.astype(np.uint16)
    queens.season = queens.season.astype(np.uint8)
    queens.series = queens.series.astype('category')
    queens.loc[queens.outcome == 'Winner', 'outcome'] = '1'
    queens.loc[queens.outcome.str.contains('Runner'), 'outcome'] = '2'
    queens.loc[queens.outcome == 'Disqualified', 'outcome'] = '-1'
    queens.outcome = queens.outcome.apply(
        lambda s: re.sub(r'^(\d{1,2}).*', r'\1', s)).astype(np.int8)
    split = queens.city.str.split(', ', expand=True)
    split.iloc[112, 1] = 'Massechussetts'
    split.iloc[291, 1] = 'Belgium'
    split = split.drop(columns=[2])
    queens = pd.concat([queens, split], axis=1).drop(columns=['city'])
    return queens.rename(columns={0: 'city',
                                  1: 'region',
                                  'contestant': 'queen_name'})
