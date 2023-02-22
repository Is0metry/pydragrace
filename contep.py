import re
from typing import Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import seaborn as sns
from bs4 import BeautifulSoup
from bs4.element import ResultSet
from common import rm_newline


def get_season_contep(bs: BeautifulSoup, season: int) -> pd.DataFrame:
    table = bs.find('span', id='Contestant_progress').find_next(
        'table').find_all('tr')[2:]
    all_queens = []
    for queen in table:
        queen_name = rm_newline(queen.th.get_text())
        queen_performance = []
        for ep_no, outcome in enumerate(queen.find_all('td')):
            ep_no += 1
            episode = {}
            episode['season'] = season + 1
            episode['episode'] = ep_no
            episode['queen_name'] = queen_name
            out = rm_newline(outcome.get_text())
            if out != '':
                episode['outcome'] = out
            queen_performance.append(pd.Series(episode))
        all_queens.append(pd.DataFrame(queen_performance))
    return pd.concat(all_queens)


def get_series_contep(soup_list: BeautifulSoup) -> pd.DataFrame:
    return pd.concat([
        get_season_contep(soup,
                          season) for season, soup in enumerate(soup_list)
    ])


def get_all_contep(soups: BeautifulSoup) -> pd.DataFrame:
    ret_frames = [get_series_contep(soup) for soup in soups.values()]
    return pd.concat(ret_frames).dropna().reset_index(drop=True)