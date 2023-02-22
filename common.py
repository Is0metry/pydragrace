import re
from typing import Dict, List

from bs4 import BeautifulSoup
import requests


WIKI_URLS = ['https://en.wikipedia.org/wiki/RuPaul%27s_Drag_Race_(season_{:d})',
             'https://en.wikipedia.org/wiki/RuPaul%27s_Drag_Race_UK_(series_{:d})',
             'https://en.wikipedia.org/wiki/Canada%27s_Drag_Race_(season_{:d})',
             'https://en.wikipedia.org/wiki/RuPaul%27s_Drag_Race_Down_Under_(season_{:d})',
             'https://en.wikipedia.org/wiki/Drag_Race_Holland_(season_{:d})',
             'https://en.wikipedia.org/wiki/Drag_Race_España_(season_{:d})',
             'https://en.wikipedia.org/wiki/Drag_Race_Italia_(season_{:d})',
             'https://en.wikipedia.org/wiki/Drag_Race_France_(season_{:d})']
SERIES_NAMES = ['Rupaul\'s Drag Race',
                'Drag Race UK',
                'Canada\'s Drag Race',
                'Drag Race Down Under',
                'Drag Race Holland',
                'Drag Race España',
                'Drag Race Italia',
                'Drag Race France']
NO_SEASONS = [14, 4, 3, 2, 2, 2, 2, 1]


def rm_newline(s):
    return re.sub(r'(\n)|(\[.{1,2}\])', '', s)


def get_soup(f_url: str, no_seasons: int) -> List[BeautifulSoup]:
    series = []
    for season in range(1, no_seasons+1):
        response = requests.get(f_url.format(season)).content
        series.append(BeautifulSoup(response, 'html.parser'))
    return series


def get_soups() -> Dict[str,List[BeautifulSoup]]:
    series_info = zip(SERIES_NAMES, WIKI_URLS, NO_SEASONS)
    return {name: get_soup(url, seasons) for name, url, seasons in series_info}
