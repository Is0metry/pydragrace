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


def scrape_episode_info(url:str,season:int) -> List[pd.Series]:
    url = url.format(season)
    response = requests.get(url).text
    bs = BeautifulSoup(response, 'html.parser')
    table = bs.find('table', class_='wikiepisodetable').find_all('td')
    episodes = []
    items_to_get = {
        'Mini-Challenge':'mini_challenge',
        'Mini-Challenge Winner':'mini_challenge_winner',
        'Mini-Challenge Winners':'mini_challenge_winner',
        'Main Challenge':'main_challenge',
        'Runway Theme':'runway_theme'
    }
    for i in range(0, len(table), 4):
        episode = {'season': season}
        episode['episode'] = int(table[i].get_text())
        episode['episode_name'] = table[i+1].get_text()
        episode['air_date'] = table[i+2].find('span', class_='bday').get_text()
        description_lists = table[i+3].find_all('ul')
        if len(description_lists) > 0:
            ep_info = description_lists[len(
                description_lists)-1]
            for info in ep_info.find_all('li'):
                if info.b is not None:
                    info_type = info.b.get_text()
                    if info_type in items_to_get.keys():
                        info.b.decompose()
                        episode[items_to_get[info_type]] = info.get_text()[2:]
        episodes.append(episode)
    return episodes

def get_all_episodes()->pd.DataFrame:
    url = 'https://en.wikipedia.org/wiki/RuPaul%27s_Drag_Race_(season_{:d})'
    episodes = []
    for i in range(1,15):
        episodes += scrape_episode_info(url,i)
    
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
