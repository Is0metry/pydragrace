import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from typing import Tuple
from sklearn.model_selection import train_test_split


def acquire_rpdr_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    '''
    Gets the RuPaul's Drag Race data from pickle files 
    converted from `.rda` files in `extract.ipynb`
    ## Parameters
    None
    ## Returns
    contestants: `DataFrame` of all contestants in US regular seasons
    of RuPaul's Drag Race.
    contep: Contestant performance per episode.
    episodes: summary of all episodes
    '''
    contestants = pd.read_pickle('data/contestants.pkl')
    contep = pd.read_pickle('data/contep.pkl')
    episodes = pd.read_pickle('data/episodes.pkl')
    return contestants, contep, episodes


def split_queens(data: Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]) -> Tuple[pd.DataFrame,
                                                                                 pd.DataFrame,
                                                                                 pd.DataFrame]:
    # TODO Docstring
    queen_split = tvt_split(data[0], stratify='winner')
    ret_data = [pd.DataFrame(), pd.DataFrame, pd.DataFrame]
    for i in range(len(queen_split)):
        ret_data[i] = pd.merge(queen_split[i], data[1], how='inner', left_on=[
            queen_split[i].index, 'season'],
            right_on=[
            'queen_id', 'season']).drop(columns=['queen_id'])
        ret_data[i] = pd.merge(ret_data[i], data[2], how='inner', left_on=[
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
    df.loc[df.main_challenge == 'Reunion', 'etype'] = 'Reunion'
    df.loc[df.main_challenge == 'Reunion', 'main_challenge'] = 'N/A'
    df.loc[df.main_challenge == 'Finale','main_challenge'] = 'N/A'
    df.loc[df.main_challenge == 'Performing','main_challenge'] = 'Performance'
    df.loc[df.nickname == '10s Across The Board','main_challenge'] = 'Fabrication'
    df.loc[df.outcome == 'Eliminated','outcome'] = 'ELIM'
    df.loc[df.outcome == 'LOSS','outcome'] = 'BTM'
    df.loc[df.outcome.str.contains('LOST'),'outcome'] = 'ELIM'
    df.loc[df.outcome == 'Winner','outcome'] = 'WIN'
    df = df.rename(columns={'main_challenge':'challenge_type'})
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
