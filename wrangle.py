import re
from os.path import isfile
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import seaborn as sns
from bs4 import BeautifulSoup
from bs4.element import ResultSet
from sklearn.model_selection import train_test_split

from contestants import clean_queens, get_all_contestants
from episodes import clean_episodes, get_all_episodes
from lipsyncs import get_all_lipsyncs
from queeneps import clean_queenep, get_all_contep

WIKI_URLS = [
    'RuPaul%27s_Drag_Race_(season_{:d})',
    'RuPaul%27s_Drag_Race_UK_(series_{:d})',
    'Canada%27s_Drag_Race_(season_{:d})',
    'RuPaul%27s_Drag_Race_Down_Under_(season_{:d})',
    'Drag_Race_Holland_(season_{:d})',
    'Drag_Race_España_(season_{:d})',
    'Drag_Race_Italia_(season_{:d})',
    'Drag_Race_France_(season_{:d})'
]
SERIES_NAMES = ['Rupaul\'s Drag Race',
                'Drag Race UK',
                'Canada\'s Drag Race',
                'Drag Race Down Under',
                'Drag Race Holland',
                'Drag Race España',
                'Drag Race Italia',
                'Drag Race France']
NO_SEASONS = [14, 4, 3, 2, 2, 2, 2, 1]
DATA_PATHS = ['data/queens', 'data/queeneps', 'data/episodes']


def rm_newline(s):
    return re.sub(r'(\n)|(\[.{1,2}\])', '', s)


def get_soup(f_url: str, no_seasons: int) -> List[BeautifulSoup]:
    series = []
    for season in range(1, no_seasons+1):
        response = requests.get(
            'https://en.wikipedia.org/wiki/' + f_url.format(season)).content
        series.append(BeautifulSoup(response, 'html.parser'))
    return series


def get_soups() -> Dict[str, List[BeautifulSoup]]:
    series_info = zip(SERIES_NAMES, WIKI_URLS, NO_SEASONS)
    return {name: get_soup(url, seasons) for name, url, seasons in series_info}


def get_show_data(repull=False) -> Tuple[pd.DataFrame,
                                         pd.DataFrame,
                                         pd.DataFrame]:
    # TODO Docstring
    if all([isfile(p + '.pkl') for p in DATA_PATHS]) and not repull:
        return (pd.read_pickle(path + '.pkl') for path in DATA_PATHS)
    soups = get_soups()
    queens = get_all_contestants(soups)
    queeneps = get_all_contep(soups)
    episodes = get_all_episodes(soups)
    return prepare_data(queens, queeneps, episodes)


def encode_episodes(queenep: pd.DataFrame,
                    episodes: pd.DataFrame) -> pd.DataFrame:
    # TODO Docstring
    queenep['episode_id'] = 0
    for index, episode in episodes.iterrows():
        ep_mask = (
            (episode.series == queenep.series)
            & (episode.season == queenep.season)
            & (episode.episode == queenep.episode)
        )
        queenep.loc[ep_mask, 'episode_id'] = index
    return queenep


def encode_mini_challenge_wins(queenep: pd.DataFrame,
                               episodes: pd.DataFrame) -> pd.DataFrame:
    # TODO Docstring
    queenep['minichalw'] = False
    join = pd.merge(queenep, episodes,
                    left_on=['series', 'season', 'episode'], right_on=[
                        'series', 'season', 'episode'])
    for index, j in join.iterrows():
        queenep.iloc[index, 6] = j.mini_challenge_winner.__contains__(
            j.queen_name)

    return queenep


def prepare_data(queens: pd.DataFrame,
                 queenep: pd.DataFrame,
                 episodes: pd.DataFrame) -> Tuple[pd.DataFrame,
                                                  pd.DataFrame, pd.DataFrame]:
    # TODO Docstring
    queens = clean_queens(queens)
    queenep = clean_queenep(queenep)
    episodes = clean_episodes(episodes)
    queenep = encode_episodes(queenep, episodes)
    queenep = encode_mini_challenge_wins(queenep, episodes)
    for path, data in zip(DATA_PATHS, (queens, queenep, episodes)):
        data.to_pickle(path + '.pkl')
    return queens, queenep, episodes


def tvt_split(df: pd.DataFrame,
              stratify: str = None,
              tv_split: float = .2,
              validate_split: int = .3):
    '''tvt_split takes a pandas DataFrame,
    a string specifying the variable to stratify over,
    as well as 2 floats where 0 < f < 1 and
    returns a train, validate, and test split of the DataFame,
    split by tv_split initially and validate_split thereafter. '''
    strat = df[stratify]
    train_validate, test = train_test_split(
        df, test_size=tv_split, random_state=911, stratify=strat)
    strat = train_validate[stratify]
    train, validate = train_test_split(
        train_validate, test_size=validate_split,
        random_state=911, stratify=strat)
    return train, validate, test


def split_queens(queens: pd.DataFrame,
                 contep: pd.DataFrame,
                 episodes: pd.DataFrame) -> Tuple[pd.DataFrame,
                                                  pd.DataFrame,
                                                  pd.DataFrame]:
    # TODO Docstring
    queen_split = train_test_split(
        queens, train_size=.8, random_state=420)
    ret_data = [pd.DataFrame(), pd.DataFrame()]
    for i in (range(len(queen_split))):
        ret_data[i] = pd.merge(queen_split[i], contep, how='inner', left_on=[
            'queen_name', 'series', 'season'],
            right_on=[
            'queen_name', 'series', 'season'])
        ret_data[i] = pd.merge(ret_data[i], episodes, how='inner', left_on=[
            'series', 'season', 'episode'], right_on=['series', 'season', 'episode'])
        ret_data[i] = ret_data[i].set_index(['queen_name','episode_id'])
    return ret_data[0], ret_data[1]
