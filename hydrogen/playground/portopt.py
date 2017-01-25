import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize._minimize as minimize
import copy
import random


fileName = '~/repo/hydrogen/hydrogen/playground/data/three_assets.csv'
cor_to_weights = pd.read_csv("~/repo/hydrogen/hydrogen/playground/data/cor_to_weights.csv", index_col=('c1', 'c2', 'c3'))

daily_df = pd.read_csv(fileName, index_col=['date'], parse_dates=['date'])
daily_df = daily_df.fillna(0)

## Down-sample to weekly
weekly_df = daily_df.resample('1W').sum().diff()

# calculate correlation
daily_df.corr()
weekly_df.corr()

## Let's do some optimisation
## Feel free to play with these

def port_mean(weights, means):
    ''' returns the mean of a portfolio given component means and sigma '''
    return (weights*means).sum().item(0,0)

def port_var(weights, sigma_mat):
    ''' returns the cov_mat of a portfolio given component weights and sigma '''
    weights_row_matrix = weights.reshape([1, -1])
    return (weights_row_matrix * sigma_mat * weights_row_matrix.transpose()).item(0,0)

def port_SR(weights, means, cov_mat, risk_free_rates=0.0):
    ''' returns the SR of a portfolio given component weights and sigma '''
    return port_mean(weights, means-risk_free_rates)/(weights, cov_mat)**.5

def port_SR_negative(weights, means, cov_mat, risk_free_rates=0.0):
    ''' returns the negative SR of a portfolio given component weights and sigma '''
    return -port_SR(weights, means, cov_mat, risk_free_rates)


def round_to_nearest(xs, refs=np.array([0.25, 0.5, 0.9])):
    ## return x rounded to nearest value in ref
    return refs[np.argmin(np.abs(np.repeat(xs.reshape(-1, 1), 3, axis=1) - refs), 1)]

def cor_to_cov(std, cor):
    return std * cor * std

def weights_lookup(rounded_corr_values):
    cor_to_weights
    assert rounded_corr_values.shape == (3,3)
    return np.ones(3)/3

def handcrafting_weight_three(standardised_return_df):
    ''' Hand crafting portfolio weights '''
    n_asset = len(standardised_return_df.columns)
    sd = standardised_return_df.std()
    is_vol_standardised = (1 - (sd.max() - sd.min())) < 0.05
    if not(is_vol_standardised) & (n_asset > 3):
        raise Exception("handcrafting_weight only works with 3 or fewer assets with same vol")

    if (n_asset < 3):
        return np.ones(n_asset)/n_asset
    else: # n_asset==3
        corr_mat = standardised_return_df.corr().values
        off_diagonal_corr_values = corr_mat[np.triu_indices(3, 1)]
        rounded_corr_values = round_to_nearest(off_diagonal_corr_values)
        return weights_lookup(rounded_corr_values)
