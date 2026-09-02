from typing import TypedDict, List, Dict, Any

class FinanceReconciliationState(TypedDict):
    """
    The memory object that gets passed from node to node in the LangGraph agent.
    """
    run_id: str
    ambiguous_pairs: List[Dict[str, Any]]  # The records that deterministic matching failed on
    current_index: int                     # Which pair we are currently analyzing
    resolved_matches: List[Dict[str, Any]] # Pairs the AI successfully matched
    final_exceptions: List[Dict[str, Any]] # Pairs the AI agrees are actually unmatched