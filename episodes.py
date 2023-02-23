import re
from typing import List, Dict
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import requests
from common import rm_newline
items_to_get = {
    re.compile(r'Mini-Challenge Winner(s)?(:)?'): 'mini_challenge_winner',
    re.compile(r'Mini-Challenge(:)?'): 'mini_challenge',
    re.compile(r'(Main)|(Maxi) Challenge(:)?'): 'main_challenge',
    re.compile(r'Runway Theme(s)?(:)?'): 'runway_theme'
}


def get_season_episodes(bs: BeautifulSoup,
                        season: int,
                        series: str) -> List[pd.Series]:
    table = bs.find('table', class_='wikiepisodetable').find_all('td')
    episodes = []

    for i in range(0, len(table), 4):
        episode = {'series': series, 'season': season + 1}
        episode['episode'] = i // 4 + 1
        episode['episode_name'] = table[i+1].get_text()
        episode['air_date'] = table[i+2].find('span', class_='bday').get_text()
        episode['summary'] = table[i+3].get_text()
        description_lists = table[i+3].find_all('ul')
        if len(description_lists) > 0:
            ep_info = description_lists[len(
                description_lists)-1]
            for info in ep_info.find_all('li'):
                if info.b is not None:
                    info_type = info.b.extract()
                    for key in items_to_get.keys():
                        if re.search(key, info_type.get_text()) is not None:
                            episode[items_to_get[key]] = info.get_text()
                            break
                    info.insert(0, info_type)
        episodes.append(episode)
    return episodes


def get_series_episodes(soup_list: List[BeautifulSoup],
                        series_name: str) -> pd.DataFrame:
    episodes = []
    for season, soup in enumerate(soup_list):
        episodes += get_season_episodes(soup, season, series_name)
    return episodes


def get_all_episodes(soups: Dict[str, List[BeautifulSoup]]) -> pd.DataFrame:
    ret_lst = []
    for series_name, soup_list in soups.items():
        ret_lst += get_series_episodes(soup_list, series_name)
    return pd.DataFrame(ret_lst).fillna('None')


def clean_episodes(episodes: pd.DataFrame) -> pd.DataFrame:
    episodes.season = episodes.season.astype(np.uint8)
    episodes.episode = episodes.episode.astype(np.uint8)
    episodes.air_date = pd.to_datetime(episodes.air_date)
    return episodes
