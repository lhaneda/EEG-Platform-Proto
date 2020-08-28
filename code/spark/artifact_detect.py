import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler


def center_signal(x):
    return x - np.median(x)


def remove_outliers_idx(x, window_size=150, q=0.99, check_ylim=False):
    x = pd.Series(x)
    x_std = x.rolling(window=window_size, center=True).std().bfill().ffill()
    x_std = MinMaxScaler().fit_transform(x_std.values.reshape(-1, 1)
                                         ).reshape(-1)
    threshold = np.quantile(x_std, q, axis=0)
    if not check_ylim:
        return x_std > threshold
    else:
        return (x_std > threshold) | (abs(x) > 3e5)


def step_detection(x):
    df = pd.DataFrame(x.astype(np.int), columns=['x'])
    param = 'x'

    def return_direction(x):
        return 1 if x > 0 else -1

    steps = pd.DataFrame(columns=['Index', 'Change', 'Direction'])
    cond = df[param].diff() != 0
    if x[0] is True:
        steps['Index'] = df[cond].index
        steps['Change'] = (100 * df[param].diff() / df[param].shift()
                           )[cond].values
    else:
        steps['Index'] = df[cond].index[1:]
        steps['Change'] = (100 * df[param].diff() / df[param].shift()
                           )[cond].values[1:]
    steps['Direction'] = steps['Change'].apply(return_direction)
    steps['Change'] = steps['Change'].apply(np.abs)
    steps.index = steps['Index']
    steps.drop(['Index'], inplace=True, axis=1)

    return steps


def get_good_intervals(x, center=False):
    if center:
        x = center_signal(x)
    artifacts = step_detection(remove_outliers_idx(x)).index.values
    df = pd.DataFrame({'start': np.concatenate([[0], artifacts,
                                               [x.shape[0]]])})
    df['length'] = df['start'].diff(-1).abs().fillna(0).astype(np.int)
    df['end'] = df['start'] + df['length']
    df = df[df.index % 2 == 0]
    idx = df.sort_values(by=['length'],
                         ascending=False)[:3][['start', 'end']].values
    # currently the whole length of artifact free signal
    # we might need to cut it's length to 30 secs.
    res = {'f_raw': x[idx[0][0]:idx[0][1]],
           'top_3': idx}
    return res


def get_bad_intervals(x, center=False):
    if center:
        x = center_signal(x)
    artifacts = step_detection(remove_outliers_idx(x)).index.values
    return artifacts.reshape(-1, 2)
