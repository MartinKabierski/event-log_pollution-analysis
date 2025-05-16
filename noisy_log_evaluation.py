import itertools
import os.path

import pandas
import pm4py

from log_pollution import *
from special4pm.simulation.simulation import simulate_model
from tqdm import tqdm

INPUTS = [("BPI_Challenge_2012_perfect_fitting_cases.xes", "BPI_Challenge_2012_inductive.pnml"),
          ("Helpdesk_perfect_fitting_cases.xes", "Helpdesk_inductive.pnml"),
          ("HospitalBilling_perfect_fitting_cases.xes", "HospitalBilling_inductive.pnml"),
          ("RTFM_perfect_fitting_cases.xes", "RTFM_inductive.pnml"),
          ("Sepsis_perfect_fitting_cases.xes","Sepsis_inductive.pnml")]

ALGORITHMS = ["IM_0.0", "IM_0.2", "ALPHA", "ILP_1.0", "ILP_0.8"]

def run_algorithm(alg_ID):
    if alg_ID == "IM_0.0":
        return  pm4py.discover_petri_net_inductive(log, noise_threshold=0.0)
    elif alg_ID == "IM_0.2":
        return  pm4py.discover_petri_net_inductive(log, noise_threshold=0.2)
    elif alg_ID == "ALPHA":
        return pm4py.discovery.discover_petri_net_alpha(log)
    elif alg_ID == "ILP_1.0":
        return pm4py.discovery.discover_petri_net_ilp(log, 1.0)
    elif alg_ID == "ILP_0.8":
        return pm4py.discovery.discover_petri_net_ilp(log, 0.8)
    else:
        print("ERROR: provided algorithm unknown")
        return

def sensitivity_analysis_discovery(logs):
    baseline_results = []
    sensitivity_results = []

    #baseline analysis
    for algorithm in ALGORITHMS:
        for idx, log in enumerate(logs):
            print("Baseline Analysis: "+algorithm +" "+str(idx))
            model, im, fm = run_algorithm(algorithm)

            #clean log - token-based replay metrics
            fitness_tbr = pm4py.conformance.fitness_token_based_replay(log, model, im, fm)
            precision_tbr = pm4py.conformance.precision_token_based_replay(log, model, im, fm)
            generalization_tbr = pm4py.conformance.generalization_tbr(log, model, im, fm)

            #clean log - alignment-based metrics
            #fitness_alignment = pm4py.conformance.fitness_alignments(log, model, im, fm)
            #precision_alignment = pm4py.conformance.precision_alignments(log, model, im, fm)
            #print(fitness_tbr)
            #print(precision_tbr)

            baseline_results.append({"algorithm": algorithm,
                                    "log_id": idx,
                                    "fitness_tbr": fitness_tbr['average_trace_fitness'],
                                    "precision_tbr": precision_tbr,
                                    "generalization_tbr": generalization_tbr})


    #sensitivity analysis
    for algorithm, polluter in itertools.product(ALGORITHMS, create_pollution_testbed()):
        for idx, log in enumerate(logs):
            print("POLLUTION: "+algorithm, str(polluter.get_properties()), str(idx))

            #apply pollution pattern
            #TODO call log.deepcopy() here and remove it from pollution functions
            polluted_log = polluter.pollute(log)

            #coduct analysis on polluted log and retrieve relevant metrics
            model, im, fm = run_algorithm(algorithm)

            #polluted log - token-based replay metrics
            polluted_fitness_tbr = pm4py.conformance.fitness_token_based_replay(polluted_log, model, im, fm)
            polluted_precision_tbr = pm4py.conformance.precision_token_based_replay(polluted_log, model, im, fm)
            polluted_generalization_tbr = pm4py.conformance.generalization_tbr(polluted_log, model, im, fm)

            #polluted log - alignment-based metrics
            #polluted_fitness_alignment = pm4py.conformance.fitness_alignments(polluted_log, model, im, fm)
            #polluted_precision_alignment = pm4py.conformance.precision_alignments(polluted_log, model, im, fm)
            #polluted_generalization_alignment = pm4py.conformance.generalization_tbr(polluted_log, model, im, fm)

            sensitivity_results.append({"algorithm": algorithm,
                                    "log_id": idx,
                                    "pollution_type": polluter.get_properties()["pollution_pattern"],
                                    "percentage": polluter.percentage,
                                    "fitness_tbr": polluted_fitness_tbr['average_trace_fitness'],
                                    "precision_tbr": polluted_precision_tbr,
                                    "generalization_tbr": polluted_generalization_tbr})

    return baseline_results, sensitivity_results


#Load inputs
for (in_log, in_model) in INPUTS:
    #Load ground truth log
    log = pm4py.read_xes(os.path.join("in","logs",in_log))

    #Load GRound Truth model
    net, im, fm = pm4py.read_pnml(os.path.join("in","models",in_model))
    #net, im, fm = pm4py.discover_petri_net_inductive(log)

    #Simulate sample logs from ground truth model
    simulated_logs = [simulate_model(net, im, fm, 100) for _ in tqdm(range(1), "Simulating Logs")]

    #conduct sensitivity analysis
    baseline_results, sensitivity_results = sensitivity_analysis_discovery(simulated_logs)

    #save results to disk
    baseline_df = pandas.DataFrame(baseline_results)
    baseline_df.to_csv(os.path.join("out", in_model+"_discovery_baseline.csv"), index=False)

    polluted_df = pandas.DataFrame(sensitivity_results)
    polluted_df.to_csv(os.path.join("out", in_model+"discovery_sensitivity.csv"), index = False)