import re
import numpy as np
import pandas as pd
import requests
import seaborn as sns
import matplotlib.pyplot as plt
from typing import Tuple
from sklearn.model_selection import train_test_split
from bs4 import BeautifulSoup
from bs4.element import ResultSet
from typing import List
from contestants import get_all_contestants
from contep import get_all_contep
from common import get_soups
from episodes import get_all_episodes
from os.path import isfile

DATA_PATHS = ['data/queens', 'data/queenep', 'data/episodes']


def get_show_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if all([isfile(p + '.pkl') for p in DATA_PATHS]):
        return (pd.read_pickle(path + '.pkl') for path in DATA_PATHS)
    if any([not isfile(p + '.csv') for p in DATA_PATHS]):
        soups = get_soups()
        data = (get_all_contestants(soups),
                get_all_contep(soups),
                get_all_episodes(soups))
        for path, df in zip(DATA_PATHS, data):
            df.to_csv(path + '.csv', index=False)
        return data
    return (pd.read_csv(path + '.csv') for path in DATA_PATHS)





def split_queens(queens: pd.DataFrame,
                 contep: pd.DataFrame,
                 episodes: pd.DataFrame) -> Tuple[pd.DataFrame,
                                                  pd.DataFrame,
                                                  pd.DataFrame]:
    # TODO Docstring
    queen_split = tvt_split(queens, stratify='winner')
    ret_data = [pd.DataFrame(), pd.DataFrame, pd.DataFrame]
    for i in (range(len(queen_split))):
        ret_data[i] = pd.merge(queen_split[i], contep, how='inner', left_on=[
            queen_split[i].index, 'season'],
            right_on=[
            'queen_id', 'season']).drop(columns=['queen_id'])
        ret_data[i] = pd.merge(ret_data[i], episodes, how='inner', left_on=[
            'season', 'episode'], right_on=['season', 'episode'])
        ret_data[i] = fix_data(ret_data[i])
    return ret_data[0], ret_data[1], ret_data[2]


def fix_data(df: pd.DataFrame) -> pd.DataFrame:
    df.main_challenge = df.main_challenge.astype('string')
    df.loc[df.main_challenge == 'Improv', 'main_challenge'] = 'Comedy'
    df.loc[df.main_challenge == 'Acting', 'main_challenge'] = 'Comedy'
    df.etype = df.etype.astype('string')
    df.loc[df.main_challenge == 'Misc', 'main_challenge'] = 'Performing'
    df.loc[df.main_challenge == 'Product', 'main_challenge'] = 'Comedy'
    df.loc[df.main_challenge == 'Design',
           'main_challenge'] = 'Fabrication'
    df.loc[df.main_challenge == 'Rusical', 'etype'] = 'Rusical'
    df.loc[df.main_challenge == 'Rusical', 'main_challenge'] = 'Performing'
    df.loc[df.main_challenge == 'Reunion', 'etype'] = 'Reunion'
    df.loc[df.main_challenge == 'Reunion', 'main_challenge'] = 'N/A'
    df.loc[df.main_challenge == 'Finale', 'main_challenge'] = 'N/A'
    df.loc[df.main_challenge == 'Performing', 'main_challenge'] = 'Performance'
    df.loc[df.nickname == '10s Across The Board',
           'main_challenge'] = 'Fabrication'
    df.loc[df.outcome == 'Eliminated', 'outcome'] = 'ELIM'
    df.loc[df.outcome.str.contains('LOST'), 'outcome'] = 'ELIM'
    df.loc[df.outcome == 'Runner-up', 'outcome'] = 'ELIM'
    df.loc[df.outcome == 'LOSS', 'outcome'] = 'BTM'
    df.loc[df.outcome == 'Winner', 'outcome'] = 'WIN'
    df.loc[df.outcome == 'OUT', 'outcome'] = 'GUEST'
    df.loc[df.outcome == 'Guest', 'outcome'] = 'GUEST'
    df.loc[df.outcome == 'RUNNING', 'outcome'] = 'GUEST'
    df.loc[df.outcome == 'TOP2', 'outcome'] = 'HIGH'
    df.loc[df.outcome == 'TOP 4', 'outcome'] = 'HIGH'
    df.loc[df.outcome == 'SAFE+DEPT', 'outcome'] = 'WDR'
    df.loc[df.outcome == 'WIN+RTRN', 'outcome'] = 'WIN'
    df.loc[df.outcome == 'STAY', 'outcome'] = 'SAFE'
    df.loc[df.outcome == 'SAVE', 'outcome'] = 'BTM'
    df.loc[df.outcome == 'RTRN', 'outcome'] = 'GUEST'
    df.loc[df.outcome == 'MISSCON', 'outcome'] = 'GUEST'
    df = df[df.outcome != 'Miss C']
    df = df[df.queen_name != 'Sherry Pie']
    df = df.rename(columns={'main_challenge': 'challenge_type'})
    df = df.reset_index(drop=True)
    return df


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
