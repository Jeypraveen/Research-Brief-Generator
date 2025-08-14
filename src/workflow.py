import time
from typing import Dict, Any, Optional, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import ResearchBriefState, create_initial_state, should_retry_node
from .nodes import nodes
from .config import config

class ResearchBriefWorkflow:
    """Main workflow orchestrator for research brief generation."""
    
    def __init__(self, enable_checkpoints: bool = True):
        self.enable_checkpoints = enable_checkpoints
        self.checkpointer = MemorySaver() if enable_checkpoints else None
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        # Create the state graph
        graph_builder = StateGraph(ResearchBriefState)
        
        # Add nodes
        graph_builder.add_node("context_summarization", nodes.context_summarization_node)
        graph_builder.add_node("planning", nodes.planning_node) 
        graph_builder.add_node("search", nodes.search_node)
        graph_builder.add_node("content_fetching", nodes.content_fetching_node)
        graph_builder.add_node("synthesis", nodes.synthesis_node)
        graph_builder.add_node("post_processing", nodes.post_processing_node)
        
        # Set entry point
        graph_builder.set_entry_point("context_summarization")
        
        # Add conditional edges with routing logic
        graph_builder.add_conditional_edges(
            "context_summarization",
            self._route_from_context_summarization,
            {
                "planning": "planning",
                "retry": "context_summarization", 
                "end": END
            }
        )
        
        graph_builder.add_conditional_edges(
            "planning",
            self._route_from_planning,
            {
                "search": "search",
                "retry": "planning",
                "end": END
            }
        )
        
        graph_builder.add_conditional_edges(
            "search", 
            self._route_from_search,
            {
                "content_fetching": "content_fetching",
                "retry": "search",
                "end": END
            }
        )
        
        graph_builder.add_conditional_edges(
            "content_fetching",
            self._route_from_content_fetching, 
            {
                "synthesis": "synthesis",
                "retry": "content_fetching",
                "end": END
            }
        )
        
        graph_builder.add_conditional_edges(
            "synthesis",
            self._route_from_synthesis,
            {
                "post_processing": "post_processing",
                "retry": "synthesis", 
                "end": END
            }
        )
        
        # Post-processing always ends
        graph_builder.add_edge("post_processing", END)
        
        # Compile graph
        if self.checkpointer:
            return graph_builder.compile(checkpointer=self.checkpointer)
        else:
            return graph_builder.compile()
    
    def _route_from_context_summarization(self, state: ResearchBriefState) -> Literal["planning", "retry", "end"]:
        """Route from context summarization node."""
        if self._has_errors(state) and should_retry_node(state, "context_summarization"):
            return "retry"
        elif self._has_fatal_errors(state):
            return "end" 
        else:
            return "planning"
    
    def _route_from_planning(self, state: ResearchBriefState) -> Literal["search", "retry", "end"]:
        """Route from planning node."""
        if not state.get("research_plan"):
            if should_retry_node(state, "planning"):
                return "retry"
            else:
                return "end"
        return "search"
    
    def _route_from_search(self, state: ResearchBriefState) -> Literal["content_fetching", "retry", "end"]:
        """Route from search node."""
        search_results = state.get("search_results", [])
        if not search_results:
            if should_retry_node(state, "search"):
                return "retry"
            else:
                return "end"
        return "content_fetching"
    
    def _route_from_content_fetching(self, state: ResearchBriefState) -> Literal["synthesis", "retry", "end"]:
        """Route from content fetching node.""" 
        source_summaries = state.get("source_summaries", [])
        if not source_summaries:
            if should_retry_node(state, "processing"):
                return "retry"
            else:
                return "end"
        return "synthesis"
    
    def _route_from_synthesis(self, state: ResearchBriefState) -> Literal["post_processing", "retry", "end"]:
        """Route from synthesis node."""
        if not state.get("final_brief"):
            if should_retry_node(state, "synthesis"):
                return "retry"
            else:
                return "end"
        return "post_processing"
    
    def _has_errors(self, state: ResearchBriefState) -> bool:
        """Check if state has any errors."""
        return len(state.get("error_messages", [])) > 0
    
    def _has_fatal_errors(self, state: ResearchBriefState) -> bool:
        """Check if state has fatal errors that should stop execution."""
        error_messages = state.get("error_messages", [])
        return len(error_messages) > 3  # Stop if too many errors
    
    def run(
        self, 
        topic: str, 
        depth: int = 3,
        follow_up: bool = False,
        user_id: str = "default",
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run the research brief generation workflow.
        
        Args:
            topic: Research topic
            depth: Research depth (1-5)
            follow_up: Whether this is a follow-up query
            user_id: User identifier
            thread_id: Thread ID for checkpointing
            
        Returns:
            Dictionary containing the final state and results
        """
        start_time = time.time()
        
        try:
            # Create initial state
            initial_state = create_initial_state(
                topic=topic,
                depth=depth, 
                follow_up=follow_up,
                user_id=user_id,
                max_retries=config.MAX_CONTEXT_SUMMARIZATION_ATTEMPTS
            )
            
            # Prepare config for execution
            run_config = {}
            if self.checkpointer and thread_id:
                run_config["configurable"] = {"thread_id": thread_id}
            
            # Execute workflow
            result = self.graph.invoke(initial_state, run_config)
            
            # Calculate total time
            total_time = time.time() - start_time
            result["total_execution_time"] = total_time
            
            # Add success indicator
            result["workflow_completed"] = True
            result["success"] = result.get("workflow_success", False)
            
            return result
            
        except Exception as e:
            total_time = time.time() - start_time
            return {
                "workflow_completed": False,
                "success": False,
                "error": str(e),
                "total_execution_time": total_time,
                "topic": topic,
                "user_id": user_id
            }
    
    def stream_run(
        self,
        topic: str,
        depth: int = 3, 
        follow_up: bool = False,
        user_id: str = "default",
        thread_id: Optional[str] = None
    ):
        """
        Stream the workflow execution for real-time updates.
        
        Args:
            topic: Research topic
            depth: Research depth (1-5) 
            follow_up: Whether this is a follow-up query
            user_id: User identifier
            thread_id: Thread ID for checkpointing
            
        Yields:
            State updates as they occur
        """
        try:
            # Create initial state
            initial_state = create_initial_state(
                topic=topic,
                depth=depth,
                follow_up=follow_up, 
                user_id=user_id,
                max_retries=config.MAX_CONTEXT_SUMMARIZATION_ATTEMPTS
            )
            
            # Prepare config
            run_config = {}
            if self.checkpointer and thread_id:
                run_config["configurable"] = {"thread_id": thread_id}
            
            # Stream execution
            for step in self.graph.stream(initial_state, run_config):
                yield step
                
        except Exception as e:
            yield {"error": str(e), "node": "workflow", "success": False}
    
    def get_graph_visualization(self) -> bytes:
        """Get a visual representation of the workflow graph."""
        try:
            return self.graph.get_graph().draw_mermaid_png()
        except Exception as e:
            print(f"Could not generate graph visualization: {e}")
            return None
    
    def get_state_at_step(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get the current state for a specific thread (if checkpointing is enabled)."""
        if not self.checkpointer:
            return None
            
        try:
            config = {"configurable": {"thread_id": thread_id}}
            return self.graph.get_state(config)
        except Exception as e:
            print(f"Could not retrieve state: {e}")
            return None
    
    def resume_from_checkpoint(
        self, 
        thread_id: str, 
        new_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Resume execution from a checkpoint."""
        if not self.checkpointer:
            raise ValueError("Checkpointing not enabled")
        
        try:
            config = {"configurable": {"thread_id": thread_id}}
            
            if new_input:
                # Continue with new input
                result = self.graph.invoke(new_input, config)
            else:
                # Resume from current state
                current_state = self.graph.get_state(config)
                result = self.graph.invoke(current_state.values, config)
            
            return result
            
        except Exception as e:
            return {
                "workflow_completed": False, 
                "success": False,
                "error": f"Resume failed: {str(e)}"
            }

# Global workflow instance  
workflow = ResearchBriefWorkflow()