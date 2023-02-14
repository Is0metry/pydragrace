import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def get_rpdr_data()->pd.DataFrame:
    contestants = pd.read_pickle('data/contestants.pkl')
    contep = pd.read_pickle('data/contep.pkl')
    episodes = pd.read_pickle('data/episodes.pkl')
    contest_contep = pd.merge(contestants,contep,left_on='contestant',right_on='contestant')
    return contest_contep