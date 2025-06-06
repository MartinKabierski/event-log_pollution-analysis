import argparse
from log_pollution import run_pipeline  # Assuming your pipeline logic is in log_pollution.py

def main():
    parser = argparse.ArgumentParser(description="Run the event log pollution analysis pipeline.")
    parser.add_argument('--event_log', type=str, required=True, help='Path to the original event log file.')
    parser.add_argument('--dqis', type=str, nargs='+', required=True, help='List of DQIs to apply (see log_pollution.py for supported values).')
    parser.add_argument('--discovery', type=str, choices=['IM', 'alpha', 'ILP'], required=True, help='Discovery technique to use.')
    parser.add_argument('--evaluation', type=str, choices=['token-based replay', 'alignments'], required=True, help='Model evaluation approach.')

    args = parser.parse_args()

    run_pipeline(
        event_log_path=args.event_log,
        dqis=args.dqis,
        discovery_technique=args.discovery,
        evaluation_method=args.evaluation
    )

if __name__ == "__main__":
    main()