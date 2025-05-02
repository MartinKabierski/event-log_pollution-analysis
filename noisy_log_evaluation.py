import itertools
import os.path

import pandas
import pm4py

from log_pollution import *
from special4pm.simulation.simulation import simulate_model
from tqdm import tqdm


def sensitivity_analysis_conformance(logs):
    IM_NOISE = [0.0, 0.2]

    baseline_results = []
    sensitivity_results = []

    #baseline analysis
    for noise in IM_NOISE:
        for idx, log in enumerate(logs):
            model, im, fm = pm4py.discover_petri_net_inductive(log, noise_threshold=noise)

            fitness = pm4py.conformance.fitness_alignments(log, model, im, fm)
            precision = pm4py.conformance.precision_alignments(log, model, im, fm)
            generalization = pm4py.conformance.generalization_tbr(log, model, im, fm)


            baseline_results.append({"noise": noise,
                                    "log_id": idx,
                                    "fitness": fitness['averageFitness'],
                                    "precision": precision,
                                    "generalization": generalization})


    #sensitivity analysis
    for noise, polluter in itertools.product(IM_NOISE, create_pollution_testbed()):
        for idx, log in enumerate(logs):
            print("POLLUTION: "+str(noise), str(polluter.get_properties()), str(idx))

            #apply pollution pattern
            polluted_log = polluter.pollute(log)

            #coduct analysis on polluted log and retrieve relevant metrics
            model, im, fm = pm4py.discover_petri_net_inductive(polluted_log, noise_threshold=noise)

            polluted_fitness = pm4py.conformance.fitness_alignments(polluted_log, model, im, fm)
            polluted_precision = pm4py.conformance.precision_alignments(polluted_log, model, im, fm)
            polluted_generalization = pm4py.conformance.generalization_tbr(polluted_log, model, im, fm)

            sensitivity_results.append({"noise": noise,
                                    "log_id": idx,
                                    "pollution_type": polluter.get_properties()["pollution_pattern"],
                                    "percentage": polluter.percentage,
                                    "fitness": polluted_fitness['averageFitness'],
                                    "precision": polluted_precision,
                                    "generalization": polluted_generalization})

    return baseline_results, sensitivity_results


#Load dataset
log = pm4py.read_xes(os.path.join("in","Road_Traffic_Fines_Management_Process.xes"))

#Discover Ground Truth Model
net, im, fm = pm4py.discover_petri_net_inductive(log)

#Simulate sample logs
simulated_logs = [simulate_model(net, im, fm, 100) for _ in tqdm(range(1), "Simulating Logs")]

#conduct sensitivity analysis
baseline_results, sensitivity_results = sensitivity_analysis_conformance(simulated_logs)

#save results to disk
baseline_df = pandas.DataFrame(baseline_results)
baseline_df.to_csv(os.path.join("out", "conformance_baseline.csv"), index=False)

polluted_df = pandas.DataFrame(sensitivity_results)
polluted_df.to_csv(os.path.join("out","conformance_sensitivity.csv"), index = False)