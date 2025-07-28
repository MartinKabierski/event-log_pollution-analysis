# Framework: data quality impact on process discovery

## Description

This is the github repository containing implementation of the framework for the evaluation of the impact of data quality issues presented in:
> How much can we improve process mining? A framework for measuring data quality sensitivity in process discovery
> Yannis Bertrand, Martin Kabierski, Jari Peeperkorn & Seppe vanden Broucke
Submitted to EdbA'25.


## How to use the framework?

To use our pipeline, you can simply run the main.py file while specifying the following four parameters:
- Original event log (provided by user)
- DQIs (currently supported: see below in description of log_pollution.py)
- Discovery techniques (currently supported: IM, alpha, ILP)
- Model evaluation approach (currently supported: token-based replay, alignments)

```further tutorials & examples to be added```

## Structure

```TO BE RESTRUCTURED AND CLEANED UP```

```
├── GT_log_creation/                # Contains evertyhing needed to create the clean event logs in the experiments
│   └──  original_event_logs/        # Contains the original event logs
│   └──  clean_event_logs/           # Contains the clean event logs
│   └── process_models/             # Different discovered process models that could be used to filter the event log (we used the 0.2 variants)
    trace_by_trace_filtering.py     # The script used for filtering
    utils.py                        # Script containing the discovery setup used
├── out/                            # The experiment's in the paper full outputs 
├── main.py                         # The script to use the pipeline
├── create_plots.py                 # Used in experiments
├── log_pollution.py                # Scripts containing the pollution functions
├── noisy_log_evaluation.py         # Scripts containing the evaluation
├── scenario_evaluation.py          # Used in experiments
├── requirements.txt                # Python dependencies
├── README.md                       # This file
```

```Script to recreate experiments with one click to be added soon as well```
