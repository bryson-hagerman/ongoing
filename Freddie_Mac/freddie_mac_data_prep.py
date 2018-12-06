'''
Script to process and merge available quarter loan information from
Freddie Mac.
'''
import click
import pandas as pd
import os
import sys


FEATURES_TO_KEEP = ['credit_score', 'maturity_date', 'mi', 'number_units', 'occupancy_status',
                    'cltv', 'dti', 'original_upb', 'original_rate', 'channel', 'property_type',
                    'postal_code', 'sequence_number', 'loan_purpose', 'loan_term',
                    'number_borrowers', 'seller_name', 'delinquency_status', 'loan_age',
                    'zero_balance_code', 'property_state', 'postal_code']


def drop_missing(df):
    '''
    Helper function to remove missing values based on data guide

    df: pd.DataFrame
        Merged DF containing origination and performance data
    '''
    # Subset on relevant / good quality data feature columns
    df_sub = df[FEATURES_TO_KEEP].copy()
    # Convert for nan check
    df_sub['delinquency_status'] = df_sub['delinquency_status'].astype(str)
    df_clean = df_sub[(df_sub['credit_score'] != 999) &
                      (df_sub['mi'] != 999) &
                      (df_sub['number_units'] != 99) &
                      (df_sub['occupancy_status'] != '9') &
                      (df_sub['cltv'] != 999) &
                      (df_sub['dti'] != 999) &
                      (df_sub['channel'] != '9') &
                      (df_sub['property_type'] != '99') &
                      (df_sub['loan_purpose'] != '9') &
                      (df_sub['number_borrowers'] != 99) &
                      (df_sub['delinquency_status'] != 'nan')]
    return df_clean


def clean_and_merge_perf_orig(path_to_data, quarter, year):
	'''
	Helper function to load and merge performance and origination data

	Subsets to latest performance info and joins

	Parameters
	----------
	path_to_data: str
		Local path to folder containing quarterly files
	quarter: str
		Quarter to process
	year: str
		Year to process

	Returns
	-------
	merge_df: pd.DataFrame
		DF containing merged origination and final performance data
	'''

	performance_df = pd.read_csv(
		f'{path_to_data}/historical_data1_time_{quarter}{year}.txt',
		sep='|',
    	header=None,
    	names=['sequence_number', 'reporting_period', 'actual_upb',
    	       'delinquency_status', 'loan_age', 'months_to_maturity',
           	   'repurchase_flag', 'modification_flag', 'zero_balance_code',
           	   'zero_balance_date', 'current_interest_rate', 'current_deferred_upb',
           	   'ddlpi', 'mi_recoveries', 'net_sales_proceeds', 'non_mi_recoveries',
           	   'expenses', 'legal_costs', 'maintenance_costs', 'taxes_insurance',
           	   'misc_expenses', 'actual_loss_calculation', 'modification_cost',
           	   'step_mod_flag', 'deferred_payment_mod', 'eltv'],
    	usecols=[0, 1, 2, 3, 4, 8],
    	dtype={'delinquency_status': 'str',
    	       'zero_balance_code': 'str'})

	total_performance = len(performance_df)
	print(f'There are {total_performance} rows of performance data overall')
	final_idx = performance_df.groupby(['sequence_number'])['loan_age'].transform(max) == performance_df['loan_age']

	performance_final = performance_df[final_idx].copy()

	origination_df = pd.read_csv(
		f'{path_to_data}/historical_data1_{quarter}{year}.txt',
        sep='|',
        header=None,
        names=['credit_score', 'first_payment_date', 'homebuyer_flag', 'maturity_date', 'msa',
               'mi', 'number_units', 'occupancy_status', 'cltv', 'dti', 'original_upb', 'ltv',
               'original_rate', 'channel', 'ppm_flag', 'product_type', 'property_state',
               'property_type', 'postal_code', 'sequence_number', 'loan_purpose', 'loan_term',
               'number_borrowers', 'seller_name', 'servicer_name', 'conforming_flag',
               'pre_harp_sequence'],
        dtype={'sequence_number': str})

	merge_df =  pd.merge(origination_df, performance_final,
						 how='left', on='sequence_number')

	total_merge = len(merge_df)
	print(f'After merging {total_merge} rows of origination and performance data remain')
	print(f'Cleaning merged DF and subsetting on predictive features')
	clean_df = drop_missing(merge_df)

	return clean_df


@click.command()
@click.option('--quarter', default='Q1', show_default=True,
		      help='Quarter of loan data to process in format Q#')
@click.option('--year', default='2009', show_default=True,
		      help='Year of loan data to process in format YYYY')
def main(quarter, year):
	print(f'Processing and merging data for {quarter}{year}')

	data_folder = f'historical_data1_{year}/historical_data1_{quarter}{year}'

	if os.path.exists(data_folder) == False:
		sys.exit(f'No folder for {quarter}{year} exists')
	else:
		merge_df = clean_and_merge_perf_orig(data_folder, quarter, year)

	print(f'Saving cleaned and merged DF for {quarter}{year}')
	merge_df.to_csv(f'{data_folder}/{quarter}{year}_cleaned.csv')


if __name__ == '__main__':
	main()
