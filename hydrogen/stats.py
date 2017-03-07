import pandas as pd
import numpy as np

N_BUSINESS_DAY = 256

import pandas as pd


def summary(returns: pd.DataFrame):
    """
    :param returns: a return time series
    :return returns a summary description of the time series return provided
    """
    summary = returns.describe().T
    sharpe_ratio = (returns.mean() / returns.std()).rename('sharpe_ratio')
    skew = returns.skew().rename('skew')
    kurtosis = returns.kurtosis().rename('kurtosis')
    avg_gain_avg_loss_ratio = ((returns[returns > 0]).mean() / (returns[returns < 0]).mean()).rename(
        'avg_gain_avg_loss_ratio')
    hit_ratio = ((returns[returns > 0]).count() / (returns[returns < 0]).count()).rename('hit_ratio')
    return pd.concat([summary, sharpe_ratio, skew, kurtosis, avg_gain_avg_loss_ratio, hit_ratio], axis=1).T



def stats(ts: pd.DataFrame):
    """ Assume ts is business day, and n business day is 256 """

    res = ts.describe()

    sharpe_ratio = (ts.mean() / ts.std() * np.sqrt(256)).rename('Sharpe ratio')
    skew = ts.skew().rename('skew')
    kurtosis = ts.kurtosis().rename('kurtosis')
    hit_rate = ((ts > 0).sum() / len(ts)).rename('hit rate')
    res_extra = pd.concat([skew, kurtosis, hit_rate, sharpe_ratio], axis=1).T

    res = res.append(res_extra)

    return (res)


def create_test_time_series(mu=0, sd=0.2, n=1000, sharpe_ratio=None, random_seed=None):
    ''' Create a random daily time series with mean and standard deviation as specified. '''
    if sharpe_ratio is not None:
        mu = sharpe_ratio * sd

    mu = mu / 256
    sd = sd / np.sqrt(256)
    if random_seed:
        np.random.seed(random_seed)

    start_date = pd.datetime(2000, 1, 1)
    end_date = start_date + pd.datetools.BDay(n)
    dates = pd.bdate_range(start=start_date, end=end_date)
    ts = pd.DataFrame({'Return': mu + np.random.randn(n) * sd}, index=dates)
    return (ts)


def sharpe_ratio(ts):
    '''assume time series is daily return '''
    return (ts.mean() / ts.std() * np.sqrt(256))[0]


def check_sharpe_ratio_gt_threshold(sharpe_ratio_list, threshold=1.0):
    sharpe_ratio_array = np.array(sharpe_ratio_list)
    c1 = (sharpe_ratio_array > threshold).sum()
    return (c1)


def construct_table_1():
    for n_rule in [1, 5, 10, 50, 100]:
        for sharpe_threshold in [0.5, 1.0, 2.0]:
            avg_count = 0
            n_exp = 200
            for exp_id in range(n_exp):
                sharpe_ratio_list = [sharpe_ratio(create_test_time_series(n=256, sharpe_ratio=0, sd=0.1)) for i in
                                     range(n_rule)]
                avg_count += check_sharpe_ratio_gt_threshold(sharpe_ratio_list, threshold=sharpe_threshold) / n_exp
            print('Average of number rules accepted for number of rules = {}, min SR = {}  = {}'.format(n_rule,
                                                                                                        sharpe_threshold,
                                                                                                        avg_count))


def all_good_rules(n_rule, n_year, SR=0):
    sharpe_ratio_list = [sharpe_ratio(create_test_time_series(sharpe_ratio=SR, n=n_year * 256)) for i in
                             range(n_rule)]
    sharpe_ratio_array = np.array(sharpe_ratio_list)
    # any bad rule exist
    return (sharpe_ratio_array > 0).all()


def find_sharpe_ratio(n_rule, n_year):
    SR = 0
    while True:
        SR += 0.1
        c = np.array([ all_good_rules(n_rule, n_year, SR) for i in range(100) ]).mean()
        print(c)
        if c >= 0.95:
            break
    return(SR)

for n_rule in [1, 5, 10, 50, 100]:
    for n_year in np.array([1, 5, 10, 30]):
        avg_sharpe = find_sharpe_ratio(n_rule, n_year)
        print(
            "The average to be able to distinguish true SR from random is SR={sr} using {n_years} years historical data with {n_rules}".format(
                sr=avg_sharpe, n_years=n_year, n_rules=n_rule))
