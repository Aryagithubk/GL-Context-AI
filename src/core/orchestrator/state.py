"""
OmniQueryState — TypedDict that flows through the LangGraph orchestrator.
Each node reads from and writes to this shared state.
"""

from typing import TypedDict, List, Dict, Any, Optional


class AgentPlan(TypedDict):
    """Plan for executing a single agent"""
    agent_name: str
    confidence: float
    priority: int


class OmniQueryState(TypedDict):
    """Shared state flowing through the orchestrator graph"""
    # Input
    query: str
    original_query: str
    session_id: str

    # Classification
    intent: str
    entities: Dict[str, Any]

    # Routing
    agent_plans: List[AgentPlan]
    current_agent_index: int

    # Execution
    agent_results: List[Dict[str, Any]]
    failed_agents: List[str]

    # Synthesis
    synthesized_answer: str
    final_sources: List[Dict[str, Any]]
    agents_used: List[str]
    overall_confidence: float

    # Output
    formatted_response: str
    execution_time_ms: float
    error: Optional[str]
