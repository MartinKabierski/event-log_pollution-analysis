#import itertools
import os.path

import pandas
import pandas as pd
import pm4py

from log_pollution import *
#from special4pm.simulation.simulation import simulate_model
#from tqdm import tqdm

INPUT_PATH = 'GT_log_creation'

INPUTS = [#("Sepsis Cases - Event Log_0_1_perfect_fitting_cases.xes", "Sepsis Cases - Event Log_0_1_inductive.pnml"),
          ("Sepsis Cases - Event Log_0_2_perfect_fitting_cases.xes", "Sepsis Cases - Event Log_0_2_inductive.pnml")#,
          #("Sepsis Cases - Event Log_0_3_perfect_fitting_cases.xes", "Sepsis Cases - Event Log_0_3_inductive.pnml"),
          #("Sepsis Cases - Event Log_0_4_perfect_fitting_cases.xes", "Sepsis Cases - Event Log_0_4_inductive.pnml"),
          #("Sepsis Cases - Event Log_0_5_perfect_fitting_cases.xes", "Sepsis Cases - Event Log_0_5_inductive.pnml")
            ]

ALGORITHMS = ["IM_0.0", "IM_0.2", "IM_0.4", "ALPHA", "ILP_1.0", "ILP_0.8", "ILP_0.6"]

def run_algorithm(alg_ID, log):
    if alg_ID == "IM_0.0":
        return  pm4py.discover_petri_net_inductive(log, noise_threshold=0.0)
    elif alg_ID == "IM_0.2":
        return  pm4py.discover_petri_net_inductive(log, noise_threshold=0.2)
    elif alg_ID == "IM_0.4":
        return pm4py.discover_petri_net_inductive(log, noise_threshold=0.4)
    elif alg_ID == "ALPHA":
        return pm4py.discovery.discover_petri_net_alpha(log)
    elif alg_ID == "ILP_1.0":
        return pm4py.discovery.discover_petri_net_ilp(log, 1.0)
    elif alg_ID == "ILP_0.8":
        return pm4py.discovery.discover_petri_net_ilp(log, 0.8)
    elif alg_ID == "ILP_0.6":
        return pm4py.discovery.discover_petri_net_ilp(log, 0.6)
    else:
        raise ValueError("ERROR: provided algorithm " + alg_ID + " unknown")

# added support for multiple DQIs
# added computation of TBR with different logs and models
def scenario_analysis_discovery(clean_log, baseline_model, baseline_im, baseline_fm):

    #baseline analysis
    scenario_results = []

    # Comparing Baseline Model vs Cleaned Log
    print("Baseline Analysis")
    fitness_tbr = pm4py.conformance.fitness_token_based_replay(clean_log, baseline_model, baseline_im, baseline_fm)
    precision_tbr = pm4py.conformance.precision_token_based_replay(clean_log, baseline_model, baseline_im,
                                                                   baseline_fm)
    generalization_tbr = pm4py.conformance.generalization_tbr(clean_log, baseline_model, baseline_im, baseline_fm)

    scenario_results.append({"algorithm": "None",
                                "pollution_type": "None",
                                "fitness_tbr": fitness_tbr['average_trace_fitness'],
                                "precision_tbr": precision_tbr,
                                "generalization_tbr": generalization_tbr})

    for algorithm in ALGORITHMS:

        # create some lists to store info about pollution patterns applied
        pollution_types = []
        pollution_percentages = []

        # Comparing
        print("Clean Log Analysis: " + algorithm)
        clean_model, clean_im, clean_fm = run_algorithm(algorithm, clean_log)

        # clean log - token-based replay metrics
        fitness_tbr = pm4py.conformance.fitness_token_based_replay(clean_log, clean_model, clean_im, clean_fm)
        precision_tbr = pm4py.conformance.precision_token_based_replay(clean_log, clean_model, clean_im, clean_fm)
        generalization_tbr = pm4py.conformance.generalization_tbr(clean_log, clean_model, clean_im, clean_fm)

        # clean log - alignment-based metrics
        # fitness_alignment = pm4py.conformance.fitness_alignments(log, model, im, fm)
        # precision_alignment = pm4py.conformance.precision_alignments(log, model, im, fm)
        # print(fitness_tbr)
        # print(precision_tbr)

        scenario_results.append({"algorithm": algorithm,
                                    "pollution_type": "None",
                                    "fitness_tbr": fitness_tbr['average_trace_fitness'],
                                    "precision_tbr": precision_tbr,
                                    "generalization_tbr": generalization_tbr})

        # initialise the polluted log as identical to the clean log
        polluted_log = copy.deepcopy(clean_log)

        # scenario analysis
        for polluter in create_pollution_testbed():
            print("POLLUTION: " + str(polluter.get_properties()))

            # apply pollution patterns successively and keep track of which pollution patterns were applied
            polluted_log = polluter.pollute(polluted_log)
            pollution_types.append(polluter.get_properties()["pollution_pattern"])
            pollution_percentages.append(polluter.percentage)

        # conduct analysis on polluted log and retrieve relevant metrics
        polluted_model, polluted_im, polluted_fm = run_algorithm(algorithm, polluted_log)

        # polluted log - token-based replay metrics
        polluted_fitness_tbr = pm4py.conformance.fitness_token_based_replay(polluted_log, polluted_model,
                                                                            polluted_im, polluted_fm)
        polluted_precision_tbr = pm4py.conformance.precision_token_based_replay(polluted_log,
                                                                                polluted_model, polluted_im,
                                                                                polluted_fm)
        polluted_generalization_tbr = pm4py.conformance.generalization_tbr(polluted_log, polluted_model,
                                                                           polluted_im, polluted_fm)

        # polluted log - alignment-based metrics
        # polluted_fitness_alignment = pm4py.conformance.fitness_alignments(polluted_log, model, im, fm)
        # polluted_precision_alignment = pm4py.conformance.precision_alignments(polluted_log, model, im, fm)
        # polluted_generalization_alignment = pm4py.conformance.generalization_tbr(polluted_log, model, im, fm)

        scenario_results.append({"algorithm": algorithm,
                                    "pollution_type": pollution_types,
                                    "percentage": pollution_percentages,
                                    "fitness_tbr": polluted_fitness_tbr['average_trace_fitness'],
                                    "precision_tbr": polluted_precision_tbr,
                                    "generalization_tbr": polluted_generalization_tbr})

    return scenario_results

def apply_optimised_discovery(results_path, original_log):
    results = pd.read_csv(results_path, header=0)
    best_f1 = 0
    #polluted_results = results.loc[results['pollution_type'] is not None]

    # loop over the scenario_results of the sensitivity analysis to find out algorithm with best f1-score
    for row in results.index:
        if (results.loc[row, 'pollution_type'] is not None) and (results.loc[row, 'pollution_type'] not in ['nan', np.nan]):
            model = results.loc[row,:]
            f1_score = 2/(1/(model['fitness_tbr']) + 1/(model['precision_tbr']))
            if f1_score > best_f1:
                best_algorithm = model['algorithm']
                best_f1 = f1_score

    # run best algorithm to obtain a "DQI optimised" process model
    print('Applying optimised process discovery')
    opt_model, opt_im, opt_fm = run_algorithm(best_algorithm, original_log)

    # Save the process model
    pm4py.write_pnml(opt_model, opt_im, opt_fm, results_path + '_optimised_' + best_algorithm + '.pnml')
    pm4py.save_vis_petri_net(opt_model, opt_im, opt_fm, file_path=results_path + '_optimised_' + best_algorithm +'_inductive_view.png')  # This will save a view for the Petri net

    # compute model quality metrics and return the scenario_results in a dataframe
    opt_fitness_tbr = pm4py.conformance.fitness_token_based_replay(original_log, opt_model,
                                                                        opt_im, opt_fm)
    opt_precision_tbr = pm4py.conformance.precision_token_based_replay(original_log,
                                                                            opt_model, opt_im,
                                                                            opt_fm)
    opt_generalization_tbr = pm4py.conformance.generalization_tbr(original_log, opt_model,
                                                                       opt_im, opt_fm)

    opt_results = pd.DataFrame.from_dict({"algorithm": [best_algorithm],
                             "scenario": [results_path],
                             "fitness_tbr": [opt_fitness_tbr['average_trace_fitness']],
                             "precision_tbr": [opt_precision_tbr],
                             "generalization_tbr": [opt_generalization_tbr]})

    return opt_results


#Load inputs
for (in_log, in_model) in INPUTS:
    out_path = in_model.removesuffix('.pnml')

    """
    #Load ground truth log
    log = pm4py.read_xes(os.path.join(INPUT_PATH, 'cleaned_event_logs', in_log), return_legacy_log_object=True)

    #Load Ground Truth model
    net, im, fm = pm4py.read_pnml(os.path.join(INPUT_PATH, "process_models", in_model))
    #net, im, fm = pm4py.discover_petri_net_inductive(log)

    # use log as baseline. get scenario_results from original model and log as well
    #conduct sensitivity analysis
    scenario_results = scenario_analysis_discovery(log, net, im, fm)
    
    #save scenario_results to disk
    #baseline_df = pandas.DataFrame(baseline_results)
    #baseline_df.to_csv(os.path.join("out", in_model+"_discovery_baseline.csv"), index=False)

    out_path = in_model.removesuffix('.pnml')

    polluted_df = pandas.DataFrame(scenario_results)
    polluted_df['f1-score'] = 2/((1/polluted_df['fitness_tbr']) + (1/polluted_df['precision_tbr']))
    polluted_df.round(4)
    polluted_df.to_csv(os.path.join("scenario_results", out_path + "_scenario_results.csv"), index = False)
    """

    # Apply optimised process discovery
    original_log = pm4py.read_xes(os.path.join(INPUT_PATH, 'original_event_logs', 'Sepsis Cases - Event Log.xes.gz'))

    optimised_df = apply_optimised_discovery(os.path.join('scenario_results', out_path + '_scenario_results.csv'),
                                             original_log)
    optimised_df.to_csv(os.path.join("scenario_results", out_path + "_optimised_scenario_results.csv"),
                        index=False)
