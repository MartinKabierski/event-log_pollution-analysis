import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# here we define some necessary input to generate the plots
METRICS = ["fitness_tbr", "precision_tbr", "generalization_tbr", "f1-score_tbr"] # metrics we want to plot
LOG_MODEL_COMB = ['cl-pm'] # log-model combination we want to plot
RESULTS_PATH = Path('out') # path where the results csv files are located
IGNORE_COLS = ['alien_activity_nr', 'target_precision', 'distribution', 'parameters', 'mean_delay',
               'precise_activity_labels', 'new_activity_label'] # columns in the results csv files that do not contain
                                                                # values (typically, parameters of the polluters)

# these dictionaries are defined to get clearer titles for the plots
metrics_labels = {'fitness_tbr': 'fitness', 'precision_tbr': 'precision', 'generalization_tbr': 'generalisation', 'f1-score_tbr': 'f1-score'}
log_model_comb_labels = {'cl-pm': 'clean log - polluted model'}


# return the f1-score of a model by computing the harmonic mean of fitness and precision
def compute_f1_score(fitness, precision):
    return 2/(1/fitness + 1/precision)

# aggregate the results for all logs and clean up the resulting dataframe a bit
# parameters: results_path: a Path to a directory containing the results output by noisy_log_evaluation in csv format
# to_ignore_columns: list of columns from the results output that do not contain results (= parameters of the polluters
#                                                                                          , e.g., 'distribution')
def compute_average_across_dfs(results_path, to_ignore_columns):
    # Get list of all CSV files in the folder
    csv_files = list(results_path.glob("*.csv"))

    # Read all CSVs into a list of DataFrames
    dfs_list = [pd.read_csv(f) for f in csv_files]

    # Create an empty DataFrame to store results
    result_df = pd.DataFrame()

    # Loop through columns
    for col in dfs_list[0].columns:
        if col not in to_ignore_columns:
            # If column is numeric
            if pd.api.types.is_numeric_dtype(dfs_list[0][col]):
                # Average the column across all dataframes
                # -> the behaviour is a bit weird as it also averages the percentage column but result is fine
                col_avg = sum(df[col] for df in dfs_list) / len(dfs_list)
                result_df[col] = col_avg
            else:
                # Non-numeric: keep values from the first dataframe (assumes they are identical)

                # unless the column is the pollution pattern, in which case I concatenate its value with the target
                # precision to fix issues with AggregatedEventLogging /!\ dirty fix
                if col == 'pollution_pattern':
                    dfs_list[0]['target_precision'].fillna('', inplace=True)
                    #dfs_list[0]['mean_delay'] = dfs_list[0]['mean_delay'].astype(str)
                    dfs_list[0]['mean_delay'].fillna('', inplace=True)
                    dfs_list[0]['mean_delay'] = dfs_list[0]['mean_delay'].astype(str)
                    dfs_list[0]['mean_delay'] = dfs_list[0]['mean_delay'].str.replace('.', '_')
                    result_df[col] = dfs_list[0][col] + dfs_list[0]['target_precision'] + dfs_list[0]['mean_delay']

                else:
                    result_df[col] = dfs_list[0][col]

    return result_df

# call to the compute_average_across_dfs function to average the results over the four logs and save the resulting
# dataframe for easy access later

#results = compute_average_across_dfs(RESULTS_PATH, IGNORE_COLS)
#results.loc[results['pollution_pattern'] == 'ImpreciseActivityPolluter', 'percentage'] = 1.0
#results.to_csv('out/derived_results/aggregated_results.csv')

results = pd.read_csv('out/derived_results/aggregated_results.csv')

# gather the different pollution patterns and algorithms present in the results
DQI_types = list(results['pollution_pattern'].unique())
ALGORITHMS = list(results['algorithm'].unique())

# loop over the DQIs, metrics and log-model combinations to access the results we want to plot
for dqi in DQI_types:
    results_dqi = results.loc[(results['pollution_pattern'] == dqi)]
    for metric in METRICS:
        for lm in LOG_MODEL_COMB:

            # if f1-score metric is requested, compute it from fitness and precision
            if metric == 'f1-score_tbr':
                results_dqi['f1-score_tbr'+'_'+lm] = compute_f1_score(results_dqi['fitness_tbr'+'_'+lm], results_dqi['precision_tbr'+'_'+lm])
                baseline_value = compute_f1_score(results_dqi['fitness_tbr'+'_cl-cm'].iat[0], results_dqi['precision_tbr'+'_cl-cm'].iat[0])
            else:
                # compute the baseline value for the metric, without DQIs
                baseline_value = results_dqi[metric + '_cl-cm'].iat[0]

            # create string with human-readable title for the plot
            plot_title = 'Sensitivity of ' + metrics_labels[metric] + ' to ' + dqi + ' in ' + log_model_comb_labels[lm]
            col = metric + '_' + lm

            # create plot
            for var, group in results_dqi.groupby('algorithm'):
                # create lists with the values to plot to easily add the baseline value (without DQIs) at the beginning of the values list
                plot_x = [0.0] + group['percentage'].to_list()
                plot_y = [baseline_value] + group[col].to_list()
                plt.plot(plot_x, plot_y, label=var)

            plt.title(plot_title, wrap=True)
            plt.legend()
            plt.savefig('out/plots/' + plot_title)
            plt.close()
