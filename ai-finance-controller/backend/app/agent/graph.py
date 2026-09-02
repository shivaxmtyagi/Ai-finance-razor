from langgraph.graph import StateGraph, END
from app.agent.state import FinanceReconciliationState
from app.agent.llm_factory import llm_service
from app.matching.semantic_matcher import SemanticMatcher

def analyze_next_pair(state: FinanceReconciliationState) -> FinanceReconciliationState:
    """
    Agent Node: Takes the current ambiguous pair, calculates semantic similarity,and asks the LLM to decide if it's a match.
    """
    idx = state["current_index"]
    if idx >= len(state["ambiguous_pairs"]):
        return state
        
    pair = state["ambiguous_pairs"][idx]
    bank_record = pair["bank"]
    ledger_record = pair["ledger"]
    similarities = pair["similarities"]
    
    # 1. Calculate Semantic Meaning
    bank_text = f"{bank_record['description']} {bank_record['reference']}"
    ledger_text = f"{ledger_record['vendor']} {ledger_record['description']}"
    semantic_score = SemanticMatcher.calculate_similarity(bank_text, ledger_text)
    
    similarities["semantic_similarity"] = semantic_score
    
    # 2. Ask the LLM to Reason
    decision = llm_service.analyze_ambiguous_pair(bank_record, ledger_record, similarities)
    
    # 3. Route the Decision
    if decision.match and decision.confidence >= 0.80:
        state["resolved_matches"].append({
            "bank_id": bank_record["transaction_id"],
            "ledger_id": ledger_record["ledger_id"],
            "confidence": decision.confidence,
            "reasoning": decision.reasoning_summary,
            "risk_flags": decision.risk_flags
        })
    else:
        state["final_exceptions"].append({
            "bank_id": bank_record["transaction_id"],
            "ledger_id": ledger_record["ledger_id"],
            "confidence": decision.confidence,
            "reasoning": decision.reasoning_summary,
            "risk_flags": decision.risk_flags
        })
        
    state["current_index"] += 1
    return state

def routing_logic(state: FinanceReconciliationState) -> str:
    """Decides whether to keep looping or end the workflow."""
    if state["current_index"] >= len(state["ambiguous_pairs"]):
        return "end"
    return "analyze_next_pair"

# Build the LangGraph Workflow
workflow = StateGraph(FinanceReconciliationState)

# Add our single powerful reasoning node
workflow.add_node("analyze_next_pair", analyze_next_pair)

# Set the entry point
workflow.set_entry_point("analyze_next_pair")

# Add conditional edges to loop through all pairs
workflow.add_conditional_edges(
    "analyze_next_pair",
    routing_logic,
    {
        "analyze_next_pair": "analyze_next_pair",
        "end": END
    }
)
reconciliation_agent = workflow.compile()