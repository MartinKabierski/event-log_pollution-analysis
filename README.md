# Framework: data quality impact on process discovery

## Description

This is the github repository containing implementation of the framework for the evaluation of the impact of data quality issues presented in:
> How much can we improve process mining? An analysis of the impact of data quality on process discovery
> Yannis Bertrand, Martin Kabierski, Jari Peeperkorn & Seppe vanden Broucke
Submitted to ICPM (2025).


## The Framework

To use our pipeline, you can simply run the main.py file while specifying the following four parameters:
- Original event log (provided by user)
- DQIs (currently supported: see below in description of log_pollution.py)
- Discovery techniques (currently supported: IM, alpha, ILP)
- Model evaluation approach (currently supported: token-based replay, alignments)
