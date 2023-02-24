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


def get_season_contep(bs: BeautifulSoup,
                      season: int, series: str) -> pd.DataFrame:
    table = bs.find('span', id='Contestant_progress').find_next(
        'table').find_all('tr')[2:]
    all_queens = []
    for queen in table:
        queen_name = rm_newline(queen.th.get_text())
        queen_performance = []
        for ep_no, outcome in enumerate(queen.find_all('td')):
            ep_no += 1
            episode = {}
            episode['series'] = series
            episode['season'] = season + 1
            episode['episode'] = ep_no
            episode['queen_name'] = queen_name
            out = rm_newline(outcome.get_text())
            if out != '':
                episode['outcome'] = out
            queen_performance.append(pd.Series(episode))
        all_queens.append(pd.DataFrame(queen_performance))
    return pd.concat(all_queens)


def get_series_contep(soup_list: BeautifulSoup, series: str) -> pd.DataFrame:
    return pd.concat([
        get_season_contep(soup,
                          season,
                          series) for season, soup in enumerate(soup_list)
    ])


def get_all_contep(soups: BeautifulSoup) -> pd.DataFrame:
    ret_frames = [get_series_contep(soup, series)
                  for series, soup in soups.items()]
    return pd.concat(ret_frames).dropna().reset_index(drop=True)


def clean_outcomes(queenep: pd.DataFrame) -> pd.DataFrame:
    queenep.loc[queenep.outcome == 'Eliminated', 'outcome'] = 'ELIM'
    queenep.loc[queenep.outcome.str.contains('LOST'), 'outcome'] = 'ELIM'
    queenep.loc[queenep.outcome == 'Runner-up', 'outcome'] = 'ELIM'
    queenep.loc[queenep.outcome == 'LOSS', 'outcome'] = 'BTM'
    queenep.loc[queenep.outcome == 'Winner', 'outcome'] = 'WIN'
    queenep.loc[queenep.outcome == 'OUT', 'outcome'] = 'GUEST'
    queenep.loc[queenep.outcome == 'Guest', 'outcome'] = 'GUEST'
    queenep.loc[queenep.outcome == 'RUNNING', 'outcome'] = 'GUEST'
    queenep.loc[queenep.outcome == 'TOP2', 'outcome'] = 'WIN'
    queenep.loc[queenep.outcome == 'IN', 'outcome'] = 'WIN'
    queenep.loc[queenep.outcome == 'R-up', 'outcome'] = 'ELIM'
    queenep.loc[queenep.outcome == 'TOP 4', 'outcome'] = 'SAFE'
    queenep.loc[queenep.outcome == 'STAY', 'outcome'] = 'SAFE'
    queenep.loc[queenep.outcome == 'SAVE', 'outcome'] = 'BTM'
    queenep.loc[queenep.outcome == 'RTRN', 'outcome'] = 'GUEST'
    queenep.loc[queenep.outcome == 'Miss C', 'outcome'] = 'GUEST'
    queenep.loc[queenep.outcome == 'QUIT', 'outcome'] = 'ELIM'
    queenep = queenep.drop(
        queenep[~queenep.outcome.isin(['WIN', 'SAFE', 'BTM', 'ELIM'])].index)
    queenep.outcome = queenep.outcome.astype('category')
    return queenep


def clean_queenep(queenep: pd.DataFrame) -> pd.DataFrame:
    queenep = clean_outcomes(queenep)
    queenep.season = queenep.season.astype(np.uint8)
    queenep.episode = queenep.episode.astype(np.uint8)
    return queenep
