

import pandas as pd
import pm4py
from pm4py.algo.conformance.tokenreplay import algorithm as token_replay
import utils


def filter_perfect_fitting_cases_one_by_one(
    df_log: pd.DataFrame,
    net,
    initial_marking,
    final_marking,
    case_id_col: str = "case:concept:name") -> pd.DataFrame:
    """
    Keep only those cases in df_log whose token‐replay fitness is perfect (trace_is_fit == True).
    This does a per‐case conversion & replay, avoiding the bulk diagnostics API.

    Parameters
    ----------
    df_log : pd.DataFrame
        Your flat event log.
    net : PetriNet
        The Petri net model.
    initial_marking : Marking
        Initial marking for the net.
    final_marking : Marking
        Final marking for the net.

    Returns
    -------
    pd.DataFrame
        Subset of df_log containing only perfectly fitting cases.
    """
    perfect_cases = []
    i = 0
    # iterate through each case
    for case_id, single_log in df_log.groupby(case_id_col):

        # replay returns a list of dicts—here it will be length 1
        result = token_replay.apply(single_log, net, initial_marking, final_marking)

        # check its fit-flag
        if result[0]['trace_is_fit']:
            # if the trace is fit, add the case_id to the list
            perfect_cases.append(case_id)
        i += 1 
        if i % 1000 == 0:
            print(f"Processed {i} cases...")

    # filter original DataFrame
    return df_log[df_log[case_id_col].isin(perfect_cases)].copy()


def do_slow_filtering(logname, noise_threshold= 0.2, zipfile=False):
    """
    Perform slow filtering of the event log to keep only perfectly fitting cases.

    Parameters
    ----------
    logname : str
        The name of the event log file (without extension).
    """
    # Load the event log
    if zipfile:
        log = pm4py.read_xes('original_event_logs/' + logname + '.xes.gz')
    else:
        log = pm4py.read_xes('original_event_logs/' + logname + '.xes')  # Replace with your log file path

    # Discover the process model
    net, im, fm = utils.discover_net(log, algo='inductive', noise_threshold=noise_threshold)

    # Save the process model
    pm4py.write_pnml(net, im, fm, 'process_models/' + logname + '_' + str(noise_threshold).replace('.', '_') + '_inductive.pnml')  # Replace with your desired output path

    # Show view of the process model
    pm4py.save_vis_petri_net(net, im, fm, file_path='process_models/' + logname + '_' + str(noise_threshold).replace('.', '_') +'_inductive_view.png')  # This will save a view for the Petri net

    # Filter the log to keep only the perfectly fitting cases
    new_log = filter_perfect_fitting_cases_one_by_one(log, net, im, fm)

    # Save the filtered log
    print(len(new_log))
    pm4py.write_xes(new_log, 'cleaned_event_logs/' + logname + '_' + str(noise_threshold).replace('.', '_') + '_perfect_fitting_cases.xes')  # Replace with your desired output path
   

'''
do_slow_filtering('Helpdesk', zipfile=False)

do_slow_filtering('Sepsis', zipfile=True)

do_slow_filtering('RTFM', zipfile=False)
'''

# Apply the filtering to all logs with different thresholds (from 0.1 to 0.5)

do_slow_filtering('BPI_Challenge_2012', noise_threshold=0.1, zipfile=True)
do_slow_filtering('BPI_Challenge_2012', noise_threshold=0.2, zipfile=True)
do_slow_filtering('BPI_Challenge_2012', noise_threshold=0.3, zipfile=True)
do_slow_filtering('BPI_Challenge_2012', noise_threshold=0.4, zipfile=True)
do_slow_filtering('BPI_Challenge_2012', noise_threshold=0.5, zipfile=True)

do_slow_filtering('Hospital Billing - Event Log', noise_threshold=0.1, zipfile=True)
do_slow_filtering('Hospital Billing - Event Log', noise_threshold=0.2, zipfile=True)
do_slow_filtering('Hospital Billing - Event Log', noise_threshold=0.3, zipfile=True)
do_slow_filtering('Hospital Billing - Event Log', noise_threshold=0.4, zipfile=True)
do_slow_filtering('Hospital Billing - Event Log', noise_threshold=0.5, zipfile=True)

do_slow_filtering('Sepsis Cases - Event Log', noise_threshold=0.1, zipfile=True)
do_slow_filtering('Sepsis Cases - Event Log', noise_threshold=0.2, zipfile=True)
do_slow_filtering('Sepsis Cases - Event Log', noise_threshold=0.3, zipfile=True)
do_slow_filtering('Sepsis Cases - Event Log', noise_threshold=0.4, zipfile=True)
do_slow_filtering('Sepsis Cases - Event Log', noise_threshold=0.5, zipfile=True)

do_slow_filtering('Road_Traffic_Fine_Management_Process', noise_threshold=0.1, zipfile=True)
do_slow_filtering('Road_Traffic_Fine_Management_Process', noise_threshold=0.2, zipfile=True)
do_slow_filtering('Road_Traffic_Fine_Management_Process', noise_threshold=0.3, zipfile=True)
do_slow_filtering('Road_Traffic_Fine_Management_Process', noise_threshold=0.4, zipfile=True)
do_slow_filtering('Road_Traffic_Fine_Management_Process', noise_threshold=0.5, zipfile=True)

# Converting the helpdesk log to an XES
df_log = pd.read_csv('original_event_logs/' + 'Helpdesk - Event Log' + '.csv')
df_log = pm4py.format_dataframe(df_log, case_id='Case ID', activity_key='Activity', timestamp_key='Complete Timestamp')
log = pm4py.convert_to_event_log(df_log)
pm4py.write_xes(log, 'original_event_logs/' + 'Helpdesk - Event Log' + '.xes')  # Replace with your desired output path

do_slow_filtering('Helpdesk - Event Log', noise_threshold=0.1, zipfile=False)
do_slow_filtering('Helpdesk - Event Log', noise_threshold=0.2, zipfile=False)
do_slow_filtering('Helpdesk - Event Log', noise_threshold=0.3, zipfile=False)
do_slow_filtering('Helpdesk - Event Log', noise_threshold=0.4, zipfile=False)
do_slow_filtering('Helpdesk - Event Log', noise_threshold=0.5, zipfile=False)
