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
