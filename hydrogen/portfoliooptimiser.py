import numpy as np
import pandas as pd
from scipy.optimize import minimize
from hydrogen.portfolio import Portfolio

class Optimiser():

    def __init__(self, port: Portfolio):
        self.port = port

    def port_mean(self, weights, means):
        ''' returns the mean of a portfolio given component means and sigma '''
        return weights.dot(means)

    def port_var(self, weights, sigma_mat):
        ''' returns the variance of a portfolio given component weights and sigma '''
        return weights.dot(sigma_mat).dot(weights.transpose())

    def port_SR(self, weights, means, sigma_mat, risk_free_rates=0.0):
        ''' returns the SR of a portfolio given component weights and sigma '''
        return self.port_mean(weights, means - risk_free_rates) / self.port_var(weights, sigma_mat) ** .5

    def port_SR_negative_riskfree(self, weights, means, sigma_mat):
        ''' returns the negative SR of a portfolio given component weights and sigma '''
        return -self.port_SR(weights, means, sigma_mat, risk_free_rates=0.0)

    def standardise_vol(self, return_df, annualised_target_vol):
        return return_df / return_df.std(axis=0) * (annualised_target_vol / 16)

    def handcrafted_port_opt(self, return_df, use_standardise_vol=False, annualised_target_vol=0.2):
        ''' Hand crafting portfolio weights '''
        n_assets = return_df.shape[1]

        if (not use_standardise_vol) or (n_assets > 3):
            raise Exception("handcrafting_weight only works with 3 or fewer assets with same vol")
        else:
            return_df = self.standardise_vol(return_df, annualised_target_vol)

        def round_to_nearest(xs, refs=np.array([0, 0.25, 0.5, 0.75, 0.9])):
            ## return x rounded to nearest value in ref
            return refs[np.argmin(np.abs(np.repeat(xs.reshape(-1, 1), len(refs), axis=1) - refs), 1)]

        def weights_lookup(corr_values):
            cor_to_weights = pd.read_csv("~/hydrogen/playground/data/cor_to_weights.csv",
                                         index_col=('c1', 'c2', 'c3'))
            indices = round_to_nearest(corr_values)
            return cor_to_weights.ix[indices[0]].ix[indices[1]].ix[indices[2]].values

        if n_assets < 3:
            return np.ones(n_assets) / n_assets
        elif n_assets == 3:
            corr_mat = return_df.corr().values
            off_diagonal_corr_values = corr_mat[np.triu_indices(3, 1)]
            return weights_lookup(off_diagonal_corr_values)
        else:
            raise NotImplementedError('This line should never be reached')

    def mean_var_port_opt(self, means, sigma_mat):
        n_assets = len(means)

        initial_weights = np.ones(n_assets).reshape([1, -1]) / n_assets

        bounds = [(0.0, 1.0)] * n_assets
        constraint_dict = [{'type': 'eq', 'fun': lambda weights: 1 - sum(weights)}]

        risk_free_rates = np.zeros(n_assets)
        mul_factors = np.ones(n_assets)

        solution = minimize(self.port_SR_negative_riskfree, initial_weights, (means, sigma_mat), method='SLSQP',
                            bounds=bounds,
                            constraints=constraint_dict, tol=0.00001)
        return solution['x']

    def markotwitz_port_opt(self, return_df, use_equal_means=False, use_standardise_vol=False, annualised_target_vol=0.2):
        n_assets = return_df.shape[1]

        if use_standardise_vol:
            return_df = self.standardise_vol(return_df, annualised_target_vol)
            return_df = self.standardise_vol(return_df, annualised_target_vol)

        sigma_mat = return_df.cov().values

        if use_equal_means:
            means = np.ones(n_assets) * return_df.mean(axis=0).mean()
        else:
            means = return_df.mean(axis=0)

        return self.mean_var_port_opt(means, sigma_mat)

    def bootstrap_port_opt(self, return_df, use_equal_means=False, use_standardise_vol=False, annualised_target_vol=0.2,
                           n_bootstrap_run=100, n_samples_per_run=256):
        ''' Monte_carlo number of bootstrap, not block bootstrap '''
        weights_mat = np.array(
            [self.markotwitz_port_opt(return_df.sample(n=n_samples_per_run, replace=True), use_equal_means,
                                 use_standardise_vol, annualised_target_vol) for _ in
             range(n_bootstrap_run)])

        return (weights_mat.T / weights_mat.sum(axis=1)).mean(axis=1)

    def port_opt(self,  return_df, fit_method, data_split_method, n_roll_days=256, step=22, **kwargs):
        '''
        
        :param return_df: 
        :param fit_method: 
        :param data_split_method: 
        :param n_roll_days: 
        :param step: 
        :param kwargs: 
        :return:

        Example:
        res = port_opt(daily_df, 'one_period', 'in_sample')
        res1 = port_opt(daily_df, 'one_period', 'in_sample', use_standardise_vol=True)
        res2 = port_opt(daily_df, 'one_period', 'in_sample', use_equal_means=True, use_standardise_vol=True)
        res3 = port_opt(daily_df, 'bootstrap', 'in_sample', use_standardise_vol=True , n_bootstrap_run=1024)
        res4 = port_opt(daily_df, 'one_period', 'rolling', use_standardise_vol=True)
        res5 = port_opt(daily_df, 'one_period', 'rolling', use_standardise_vol=True, n_roll_days=256*5)
        res6 = port_opt(daily_df, 'one_period', 'expanding', use_standardise_vol=True)
        res7 = port_opt(daily_df, 'bootstrap', 'expanding', use_standardise_vol=True, n_bootstrap_run=1024)

        '''

        df_list = self.generate_fitting_period(return_df, data_split_method, n_roll_days)

        weights_df_list = []

        port_opt_helper = {'handcrafted': self.handcrafted_port_opt,
                       'one_period': self.markotwitz_port_opt,
                       'bootstrap': self.bootstrap_port_opt}[fit_method]
        for df in df_list[::step]:
            print('Optimising portfolio using data between {start_date} and {end_date}'.format(start_date=df.index[0],
                                                                                           end_date=df.index[-1]))

            weights = port_opt_helper(df, **kwargs)

            weights_df = pd.DataFrame(weights.reshape(1, -1), [df.index[-1]], return_df.columns)

            weights_df_list.append(weights_df)

        return pd.concat(weights_df_list)

    def generate_fitting_period(self, return_df, data_split_method, n_roll_days=256):
        ''' Assume return_df has daily index '''
        supported_method = ['in_sample', 'rolling', 'expanding']

        if data_split_method == 'in_sample':
            df_list = [return_df]
        elif data_split_method == 'rolling':
            df_list = [return_df[start_date:end_date] for start_date, end_date in zip(return_df.index[:-n_roll_days + 1], return_df.index[n_roll_days - 1:] )]
        elif data_split_method == 'expanding':
            df_list = [return_df[:end_date] for end_date
                       in return_df.index[n_roll_days - 1:]]
        else:
            raise Exception(
                'Unregonised data split method: {method}. Supported methods are {supported_method}.'.format(
                    method=data_split_method,
                    supported_method=supported_method))
        return df_list