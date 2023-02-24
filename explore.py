import seaborn as sns
import matplotlib.pyplot as plt
from IPython.display import Markdown as md
import pandas as pd

def series_markdown(episodes: pd.DataFrame) -> md:
    ret_str = ''
    e = episodes.groupby('series').season.max().sort_values(ascending=False)
    for series, seasons in e.items():
        ret_str += (f'- {series}'
                    f' (season{"s 1-"+str(seasons) if seasons > 1 else " 1"})\n\n')
    return md(ret_str)