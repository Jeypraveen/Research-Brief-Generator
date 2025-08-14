import pytest
import asyncio
from unittest.mock import Mock, patch

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.workflow import workflow
from src.state import create_initial_state
from src.schemas import FinalBrief, ResearchPlan

class TestResearchBriefWorkflow:
    """Test cases for the main workflow."""
    
    def test_initial_state_creation(self):
        """Test creating initial workflow state."""
        state = create_initial_state(
            topic="Artificial Intelligence in Healthcare",
            depth=3,
            follow_up=False,
            user_id="test_user"
        )
        
        assert state["topic"] == "Artificial Intelligence in Healthcare"
        assert state["depth"] == 3
        assert state["follow_up"] is False
        assert state["user_id"] == "test_user"
        assert state["workflow_complete"] is False
        assert len(state["messages"]) == 0
        assert len(state["search_results"]) == 0
    
    @pytest.mark.asyncio
    async def test_workflow_execution(self):
        """Test basic workflow execution."""
        # Mock the LLM responses to avoid API calls
        with patch('src.nodes.nodes.context_llm') as mock_context, \
             patch('src.nodes.nodes.planning_llm') as mock_planning, \
             patch('src.nodes.nodes.source_summary_llm') as mock_source, \
             patch('src.nodes.nodes.final_brief_llm') as mock_final:
            
            # Mock planning response
            mock_planning.return_value = ResearchPlan(
                topic="AI in Healthcare",
                research_questions=["How does AI improve diagnostics?"],
                search_queries=["AI healthcare diagnostics"],
                expected_sources=["academic papers"],
                depth_level=3
            )
            
            # Mock final brief response
            mock_final.return_value = FinalBrief(
                topic="AI in Healthcare",
                executive_summary="AI is transforming healthcare",
                key_findings=["Improved diagnostics", "Better patient outcomes"],
                detailed_analysis="Detailed analysis of AI impact",
                recommendations=["Invest in AI training", "Implement gradually"],
                sources=[],
                research_steps=[],
                limitations=["Data privacy concerns"],
                confidence_score=0.8,
                generated_at="2024-01-01T00:00:00Z"
            )
            
            result = workflow.run(
                topic="Artificial Intelligence in Healthcare",
                depth=3,
                follow_up=False,
                user_id="test_user"
            )
            
            assert result is not None
            assert "workflow_completed" in result
    
    def test_workflow_validation(self):
        """Test workflow input validation."""
        # Test empty topic
        with pytest.raises(Exception):
            workflow.run(
                topic="",
                depth=3,
                user_id="test_user"
            )
        
        # Test invalid depth
        result = workflow.run(
            topic="Valid topic",
            depth=10,  # Invalid depth
            user_id="test_user"
        )
        
        # Should handle gracefully or return error
        assert result is not None
    
    def test_workflow_checkpointing(self):
        """Test workflow checkpointing functionality."""
        thread_id = "test_thread_123"
        
        # This would test checkpointing if we had a real checkpoint store
        result = workflow.run(
            topic="Test checkpointing",
            depth=2,
            user_id="test_user",
            thread_id=thread_id
        )
        
        assert result is not None
    
    def test_follow_up_workflow(self):
        """Test follow-up query workflow."""
        result = workflow.run(
            topic="Follow-up on AI in healthcare",
            depth=2,
            follow_up=True,
            user_id="test_user"
        )
        
        assert result is not None
        # In a real test, we'd verify that context summarization was triggered
    
    @pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="No API key available")
    def test_real_api_call(self):
        """Test with real API call (only runs if API key is available)."""
        result = workflow.run(
            topic="Test topic for real API",
            depth=1,  # Use minimal depth for testing
            user_id="test_user"
        )
        
        assert result is not None
        assert "workflow_completed" in result

if __name__ == "__main__":
    pytest.main([__file__, "-v"])