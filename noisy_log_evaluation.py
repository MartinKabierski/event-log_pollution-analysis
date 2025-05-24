import pandas
from log_pollution import *

INPUTS = [
            ("RTFM_perfect_fitting_cases.xes", "RTFM_inductive.pnml"),
            ("Sepsis_perfect_fitting_cases.xes", "Sepsis_inductive.pnml"),
            ("BPI_Challenge_2012_perfect_fitting_cases.xes", "BPI_Challenge_2012_inductive.pnml"),
            ("Helpdesk_perfect_fitting_cases.xes", "Helpdesk_inductive.pnml"),
            ("HospitalBilling_perfect_fitting_cases.xes", "HospitalBilling_inductive.pnml")
]

ALGORITHMS = ["IM_0.0", "IM_0.2", "ALPHA", "ILP_0.8", "ILP_1.0"]

def run_algorithm(l ,alg_ID):
    if alg_ID == "IM_0.0":
        return  pm4py.discover_petri_net_inductive(l, noise_threshold=0.0)
    elif alg_ID == "IM_0.2":
        return  pm4py.discover_petri_net_inductive(l, noise_threshold=0.2)
    elif alg_ID == "ALPHA":
        return pm4py.discovery.discover_petri_net_alpha(l)
    elif alg_ID == "ILP_1.0":
        return pm4py.discovery.discover_petri_net_ilp(l, 1.0)
    elif alg_ID == "ILP_0.8":
        return pm4py.discovery.discover_petri_net_ilp(l, 0.8)
    else:
        print("ERROR: provided algorithm unknown")
        return

def sensitivity_analysis_discovery(clean_log, baseline_model, baseline_im, baseline_fm, log_name):
    sensitivity_results = []

    print(log_name+ " - Baseline Analysis")
    print("> Clean Log vs Baseline Model")

    fitness_tbr_cl_bm = pm4py.conformance.fitness_token_based_replay(clean_log, baseline_model, baseline_im, baseline_fm)
    precision_tbr_cl_bm = pm4py.conformance.precision_token_based_replay(clean_log, baseline_model, baseline_im,
                                                                   baseline_fm)
    generalization_tbr_cl_bm = pm4py.conformance.generalization_tbr(clean_log, baseline_model, baseline_im, baseline_fm)

    for algorithm in ALGORITHMS:

        print(log_name+ " - Clean Log Analysis: "+algorithm)
        clean_model, clean_im, clean_fm = run_algorithm(clean_log ,algorithm)

        #clean log - token-based replay metrics
        print("> Clean Log vs Clean Model")

        fitness_tbr_cl_cm = pm4py.conformance.fitness_token_based_replay(clean_log, clean_model, clean_im, clean_fm)
        precision_tbr_cl_cm = pm4py.conformance.precision_token_based_replay(clean_log, clean_model, clean_im, clean_fm)
        generalization_tbr_cl_cm = pm4py.conformance.generalization_tbr(clean_log, clean_model, clean_im, clean_fm)


    #sensitivity analysis
        for polluter in create_pollution_testbed():
            print(log_name+ " - POLLUTION: "+algorithm, str(polluter.get_properties()))

            #apply pollution pattern
            #TODO copy the log here already and remove from each of the function calls
            polluted_log = polluter.pollute(clean_log)

            #coduct analysis on polluted log and retrieve relevant metrics
            polluted_model, polluted_im, polluted_fm = run_algorithm(polluted_log, algorithm)

            #polluted log vs polluted model
            print("> Polluted Log vs Polluted Model")
            polluted_fitness_tbr_pl_pm = pm4py.conformance.fitness_token_based_replay(polluted_log, polluted_model, polluted_im, polluted_fm)
            polluted_precision_tbr_pl_pm = pm4py.conformance.precision_token_based_replay(polluted_log, polluted_model, polluted_im, polluted_fm)
            polluted_generalization_tbr_pl_pm = pm4py.conformance.generalization_tbr(polluted_log, polluted_model, polluted_im, polluted_fm)

            #polluted log vs clean model
            print("> Polluted Log vs Clean Model")
            polluted_fitness_tbr_pl_cm = pm4py.conformance.fitness_token_based_replay(polluted_log, clean_model, clean_im, clean_fm)
            polluted_precision_tbr_pl_cm = pm4py.conformance.precision_token_based_replay(polluted_log, clean_model, clean_im, clean_fm)
            polluted_generalization_tbr_pl_cm = pm4py.conformance.generalization_tbr(polluted_log, clean_model, clean_im, clean_fm)

            #clean log vs polluted model
            print("> Clean Log vs Clean Model")
            polluted_fitness_tbr_cl_pm = pm4py.conformance.fitness_token_based_replay(clean_log, polluted_model, polluted_im, polluted_fm)
            polluted_precision_tbr_cl_pm = pm4py.conformance.precision_token_based_replay(clean_log, polluted_model, polluted_im, polluted_fm)
            polluted_generalization_tbr_cl_pm = pm4py.conformance.generalization_tbr(clean_log, polluted_model, polluted_im, polluted_fm)
            print()
            print(log_name+ " - POLLUTION: "+algorithm, str(polluter.get_properties()))

            print("-" * 78)
            print("     \t{:<24}{:<24}{:<24}".format("Fitness", "Precision", "Generalization"))
            print("-" * 78)
            print("cl-bm:\t{:<24}{:<24}{:<24}".format(str(fitness_tbr_cl_bm['log_fitness']), str(precision_tbr_cl_bm), str(generalization_tbr_cl_bm)))
            print("cl-cm:\t{:<24}{:<24}{:<24}".format(str(fitness_tbr_cl_cm['log_fitness']),str(precision_tbr_cl_cm), str(generalization_tbr_cl_cm)))
            print("pl-pm:\t{:<24}{:<24}{:<24}".format(str(polluted_fitness_tbr_pl_pm['log_fitness']),str(polluted_precision_tbr_pl_pm), str(polluted_generalization_tbr_pl_pm)))
            print("pl-cm:\t{:<24}{:<24}{:<24}".format(str(polluted_fitness_tbr_pl_cm['log_fitness']),str(polluted_precision_tbr_pl_cm), str(polluted_generalization_tbr_pl_cm)))
            print("cl-pm:\t{:<24}{:<24}{:<24}".format(str(polluted_fitness_tbr_cl_pm['log_fitness']), str(polluted_precision_tbr_cl_pm), str(polluted_generalization_tbr_cl_pm)))

            print()
            print()
            #algorithm properties
            results = {"algorithm": algorithm}

            #polluter properties
            results.update(polluter.get_properties())

            #sensitivity results

            # Clean Log vs. Baseline Model
            results["fitness_tbr_cl-bm"] = str(fitness_tbr_cl_bm['average_trace_fitness'])
            results["precision_tbr_cl-bm"] = str(precision_tbr_cl_bm)
            results["generalization_tbr_cl-bm"] = str(generalization_tbr_cl_bm)

            # Clean Log vs. Clean Model
            results["fitness_tbr_cl-cm"] = str(fitness_tbr_cl_cm['average_trace_fitness'])
            results["precision_tbr_cl-cm"] = str(precision_tbr_cl_cm)
            results["generalization_tbr_cl-cm"] = str(generalization_tbr_cl_cm)

            # Polluted Log vs. Polluted Model
            results["fitness_tbr_pl-pm"] = str(polluted_fitness_tbr_pl_pm['average_trace_fitness'])
            results["precision_tbr_pl-pm"] = str(polluted_precision_tbr_pl_pm)
            results["generalization_tbr_pl-pm"] = str(polluted_generalization_tbr_pl_pm)

            # Polluted Log vs. Clean Model
            results["fitness_tbr_pl-cm"] = str(polluted_fitness_tbr_pl_cm['average_trace_fitness'])
            results["precision_tbr_pl-cm"] = str(polluted_precision_tbr_pl_cm)
            results["generalization_tbr_pl-cm"] = str(polluted_generalization_tbr_pl_cm)

            #Clean Log vs. Polluted Model
            results["fitness_tbr_cl-pm"] = str(polluted_fitness_tbr_cl_pm['average_trace_fitness'])
            results["precision_tbr_cl-pm"] = str(polluted_precision_tbr_cl_pm)
            results["generalization_tbr_cl-pm"] = str(polluted_generalization_tbr_cl_pm)

            sensitivity_results.append(results)


    return sensitivity_results


#Load inputs
for (in_log, in_model) in INPUTS:

    #Load ground truth log
    log = pm4py.read_xes(os.path.join("in","logs",in_log), return_legacy_log_object=True)
    #Load ground truth model
    net, im, fm = pm4py.read_pnml(os.path.join("in","models",in_model))

    results = sensitivity_analysis_discovery(log, net, im, fm, in_log)

    #save results as csv
    polluted_df = pandas.DataFrame(results)
    polluted_df.to_csv(os.path.join("out", in_model+"discovery_sensitivity.csv"), index = False)