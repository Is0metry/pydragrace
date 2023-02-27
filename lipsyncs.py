from typing import Dict, List
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from wrangle import get_soups, rm_newline
import re

WINNER_COLOR = {'bgcolor': '#D4AF37'}


def get_song(song):
    match_grp = re.match(r'"(?P<song_name>.*)"\s*\((?P<artist>.*)\)', song)
    if match_grp is None:
        raise SyntaxError('ya fucked something up')
    return match_grp.group('song_name'), match_grp.group('artist')


def get_season_lipsyncs(soup: BeautifulSoup, series: str, season: int) -> pd.DataFrame:
    table = soup.table.find_next('table').find_next('table').find_next('table')
    trs = table.find_all('tr')[1:]
    all_lipsyncs = []
    for i, tr in enumerate(trs):
        if len(tr.find_all('th')) > 1:
            continue
        lipsync = {'series': series, 'season': season}
        if tr.th is not None:
            lipsync['episode'] = rm_newline(tr.th.get_text())
        td = [rm_newline(t.get_text()) for t in tr.find_all('td')]
        if len(td) < 3:
            continue
        elif len(td) < 4:
            for index, value in enumerate(td[0].split(' vs. ')):
                lipsync[f'queen_{index + 1}'] = value
            song_index = 1
        elif len(td) < 6:
            lipsync['queen_1'] = td[0]
            lipsync['queen_2'] = td[2]
        else:
            lipsync['episode'] = td[0]
            lipsync['queen_1'] = td[1]
            lipsync['queen_2'] = td[3]
        lipsync['song_name'], lipsync['artist'] = get_song(td[len(td)-2])
        eliminated = td[len(td)-1]
        if not re.search(r'None', eliminated):
            lipsync['eliminated'] = eliminated

        all_lipsyncs.append(lipsync)
    ret_frame = pd.DataFrame(all_lipsyncs)
    ret_frame.episode = ret_frame.episode.fillna(method='ffill')
    return ret_frame


def get_series_lipsyncs(soup_list: List[BeautifulSoup], series: str) -> pd.DataFrame:
    series_lipsyncs = [get_season_lipsyncs(
        soup, series, season + 1) for season, soup in enumerate(soup_list)]
    return pd.concat(series_lipsyncs)


def get_all_lipsyncs(soups: Dict[str, List[BeautifulSoup]]) -> pd.DataFrame:
    all_lipsyncs = [get_series_lipsyncs(soup, series)
                    for series, soup in soups.items()]
    return pd.concat(all_lipsyncs)
