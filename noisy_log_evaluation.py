import itertools
import os.path

import pandas
import pm4py

from log_pollution import *
from special4pm.simulation.simulation import simulate_model
from tqdm import tqdm


def sensitivity_analysis_discovery(logs):
    IM_NOISE = [0.0, 0.2]

    baseline_results = []
    sensitivity_results = []

    #baseline analysis
    for noise in IM_NOISE:
        for idx, log in enumerate(logs):
            model, im, fm = pm4py.discover_petri_net_inductive(log, noise_threshold=noise)

            #clean log - token-based replay metrics
            fitness_tbr = pm4py.conformance.fitness_token_based_replay(log, model, im, fm)
            precision_tbr = pm4py.conformance.precision_token_based_replay(log, model, im, fm)
            generalization_tbr = pm4py.conformance.generalization_tbr(log, model, im, fm)

            #clean log - alignment-based metrics
            #fitness_alignment = pm4py.conformance.fitness_alignments(log, model, im, fm)
            #precision_alignment = pm4py.conformance.precision_alignments(log, model, im, fm)
            #print(fitness_tbr)
            #print(precision_tbr)

            baseline_results.append({"noise": noise,
                                    "log_id": idx,
                                    "fitness_tbr": fitness_tbr['average_trace_fitness'],
                                    "precision_tbr": precision_tbr,
                                    "generalization_tbr": generalization_tbr})


    #sensitivity analysis
    for noise, polluter in itertools.product(IM_NOISE, create_pollution_testbed()):
        for idx, log in enumerate(logs):
            print("POLLUTION: "+str(noise), str(polluter.get_properties()), str(idx))

            #apply pollution pattern
            polluted_log = polluter.pollute(log)

            #coduct analysis on polluted log and retrieve relevant metrics
            model, im, fm = pm4py.discover_petri_net_inductive(polluted_log, noise_threshold=noise)

            #polluted log - token-based replay metrics
            polluted_fitness_tbr = pm4py.conformance.fitness_token_based_replay(polluted_log, model, im, fm)
            polluted_precision_tbr = pm4py.conformance.precision_token_based_replay(polluted_log, model, im, fm)
            polluted_generalization_tbr = pm4py.conformance.generalization_tbr(polluted_log, model, im, fm)

            #polluted log - alignment-based metrics
            #polluted_fitness_alignment = pm4py.conformance.fitness_alignments(polluted_log, model, im, fm)
            #polluted_precision_alignment = pm4py.conformance.precision_alignments(polluted_log, model, im, fm)
            #polluted_generalization_alignment = pm4py.conformance.generalization_tbr(polluted_log, model, im, fm)

            sensitivity_results.append({"noise": noise,
                                    "log_id": idx,
                                    "pollution_type": polluter.get_properties()["pollution_pattern"],
                                    "percentage": polluter.percentage,
                                    "fitness_tbr": polluted_fitness_tbr['average_trace_fitness'],
                                    "precision_tbr": polluted_precision_tbr,
                                    "generalization_tbr": polluted_generalization_tbr})

    return baseline_results, sensitivity_results


#Load dataset
log = pm4py.read_xes(os.path.join("in","Road_Traffic_Fines_Management_Process.xes"))

#Discover Ground Truth Model
net, im, fm = pm4py.discover_petri_net_inductive(log)

#Simulate sample logs
simulated_logs = [simulate_model(net, im, fm, 100) for _ in tqdm(range(1), "Simulating Logs")]

#conduct sensitivity analysis
baseline_results, sensitivity_results = sensitivity_analysis_discovery(simulated_logs)

#save results to disk
baseline_df = pandas.DataFrame(baseline_results)
baseline_df.to_csv(os.path.join("out", "conformance_baseline.csv"), index=False)

polluted_df = pandas.DataFrame(sensitivity_results)
polluted_df.to_csv(os.path.join("out","conformance_sensitivity.csv"), index = False)