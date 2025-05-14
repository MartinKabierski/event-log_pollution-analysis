from typing import Tuple, Any
import pm4py

def discover_net(
    log: Any, 
    algo: str, 
    noise_threshold: float = 0.2, 
    dependency_threshold: float = 0.5, 
    and_threshold: float = 0.65, 
    loop_two_threshold: float = 0.5,
    alpha_ilp: float = 1.0
) -> Tuple[Any, Any, Any]:
    """Discover a Petri net from an event log using specified algorithm.

    Args:
        log (Any): Event log to discover process model from.
        algo (str): Algorithm to use ("inductive", "heuristic", "alpha", or "ilp").
        noise_threshold (float, optional): Used by inductive miner. Defaults to 0.2.
        dependency_threshold (float, optional): Used by heuristics miner. Defaults to 0.5.
        and_threshold (float, optional): Used by heuristics miner. Defaults to 0.65.
        loop_two_threshold (float, optional): Used by heuristics miner. Defaults to 0.5.
        alpha_ilp (float, optional): Used by ILP miner. Defaults to 1.0.

    Raises:
        ValueError: If an unknown discovery algorithm is specified.

    Returns:
        Tuple[Any, Any, Any]: Discovered Petri net, initial marking, and final marking.
    """
    if algo == "inductive":
        return pm4py.discover_petri_net_inductive(log, noise_threshold=noise_threshold)
    elif algo == "heuristic":
        return pm4py.discover_petri_net_heuristic(
            log, 
            dependency_threshold=dependency_threshold, 
            and_threshold=and_threshold, 
            loop_two_threshold=loop_two_threshold
        )
    elif algo == "alpha":
        return pm4py.discover_petri_net_alpha(log)
    elif algo == "ilp":
        return pm4py.discover_petri_net_ilp(log, alpha=alpha_ilp)
    else:
        raise ValueError(f"Unknown discovery algorithm: '{algo}'")