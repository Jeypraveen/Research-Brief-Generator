from typing import TypedDict, Annotated, List, Optional, Dict, Any
from typing_extensions import NotRequired
import operator
from langchain_core.messages import BaseMessage
from .schemas import (
    ContextSummary, ResearchPlan, SearchResult, 
    SourceSummary, FinalBrief, ResearchStep
)

class ResearchBriefState(TypedDict):
    """
    State schema for the Research Brief Generator workflow.
    This defines the structure of data that flows through the LangGraph nodes.
    """
    
    # Input parameters
    topic: str
    depth: int
    follow_up: bool
    user_id: str
    
    # Conversation and context
    messages: Annotated[List[BaseMessage], operator.add]
    
    # Context summarization (for follow-up queries)
    context_summary: NotRequired[Optional[ContextSummary]]
    context_summarization_attempts: NotRequired[int]
    
    # Planning phase
    research_plan: NotRequired[Optional[ResearchPlan]]
    planning_attempts: NotRequired[int]
    
    # Search and content fetching
    search_results: Annotated[List[SearchResult], operator.add]
    search_attempts: NotRequired[int]
    
    # Source processing
    source_summaries: Annotated[List[SourceSummary], operator.add]
    processing_attempts: NotRequired[int]
    
    # Synthesis
    final_brief: NotRequired[Optional[FinalBrief]]
    synthesis_attempts: NotRequired[int]
    
    # Workflow control
    current_node: NotRequired[str]
    completed_nodes: Annotated[List[str], operator.add]
    next_node: NotRequired[Optional[str]]
    
    # Error handling and retries
    error_messages: Annotated[List[str], operator.add]
    retry_count: NotRequired[int]
    max_retries: NotRequired[int]
    
    # Workflow status
    workflow_complete: NotRequired[bool]
    workflow_success: NotRequired[bool]
    
    # Tracing and debugging
    node_execution_times: NotRequired[Dict[str, float]]
    total_processing_time: NotRequired[float]
    
    # Token usage tracking (if available)
    total_tokens_used: NotRequired[int]
    
    # Checkpointing support
    # Custom thread tracking (renamed from checkpoint_id)
    thread_id: NotRequired[Optional[str]]

    
def create_initial_state(
    topic: str,
    depth: int = 3,
    follow_up: bool = False,
    user_id: str = "default",
    max_retries: int = 3
) -> ResearchBriefState:
    """
    Create initial state for the Research Brief workflow.
    
    Args:
        topic: Research topic
        depth: Research depth level (1-5)
        follow_up: Whether this is a follow-up query
        user_id: User identifier for context tracking
        max_retries: Maximum number of retries for each node
        
    Returns:
        Initial state dictionary
    """
    return ResearchBriefState(
        # Input parameters
        topic=topic,
        depth=depth,
        follow_up=follow_up,
        user_id=user_id,
        
        # Initialize lists
        messages=[],
        search_results=[],
        source_summaries=[],
        completed_nodes=[],
        error_messages=[],
        
        # Initialize counters
        context_summarization_attempts=0,
        planning_attempts=0,
        search_attempts=0,
        processing_attempts=0,
        synthesis_attempts=0,
        retry_count=0,
        max_retries=max_retries,
        
        # Initialize workflow status
        workflow_complete=False,
        workflow_success=False,
        
        # Initialize optional fields
        context_summary=None,
        research_plan=None,
        final_brief=None,
        current_node="start",
        next_node=None,
        
        # Initialize tracking
        node_execution_times={},
        total_processing_time=0.0,
        total_tokens_used=0,
        thread_id=None,

    )

def update_node_status(state: ResearchBriefState, node_name: str, execution_time: float = 0.0) -> Dict[str, Any]:
    """
    Update state with node completion status.
    
    Args:
        state: Current workflow state
        node_name: Name of the completed node
        execution_time: Time taken to execute the node
        
    Returns:
        State updates to apply
    """
    updates = {
        "current_node": node_name,
        "completed_nodes": [node_name],
    }
    
    # Update execution times
    if execution_time > 0:
        current_times = state.get("node_execution_times", {})
        current_times[node_name] = execution_time
        updates["node_execution_times"] = current_times
        
        # Update total processing time
        updates["total_processing_time"] = state.get("total_processing_time", 0.0) + execution_time
    
    return updates

def should_retry_node(state: ResearchBriefState, node_name: str) -> bool:
    """
    Determine if a node should be retried based on current state.
    
    Args:
        state: Current workflow state
        node_name: Name of the node to check
        
    Returns:
        True if the node should be retried, False otherwise
    """
    max_retries = state.get("max_retries", 3)
    current_retry = state.get("retry_count", 0)
    
    # Check node-specific retry counts
    node_attempts_map = {
        "context_summarization": state.get("context_summarization_attempts", 0),
        "planning": state.get("planning_attempts", 0),
        "search": state.get("search_attempts", 0),
        "processing": state.get("processing_attempts", 0),
        "synthesis": state.get("synthesis_attempts", 0),
    }
    
    node_attempts = node_attempts_map.get(node_name, current_retry)
    
    return node_attempts < max_retries

def get_state_summary(state: ResearchBriefState) -> Dict[str, Any]:
    """
    Get a summary of the current state for debugging/monitoring.
    
    Args:
        state: Current workflow state
        
    Returns:
        Summary dictionary
    """
    return {
        "topic": state.get("topic"),
        "user_id": state.get("user_id"),
        "current_node": state.get("current_node"),
        "completed_nodes": len(state.get("completed_nodes", [])),
        "workflow_complete": state.get("workflow_complete", False),
        "workflow_success": state.get("workflow_success", False),
        "error_count": len(state.get("error_messages", [])),
        "retry_count": state.get("retry_count", 0),
        "total_processing_time": state.get("total_processing_time", 0.0),
        "has_research_plan": state.get("research_plan") is not None,
        "search_results_count": len(state.get("search_results", [])),
        "source_summaries_count": len(state.get("source_summaries", [])),
        "has_final_brief": state.get("final_brief") is not None,
    }