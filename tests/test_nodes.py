import pytest
from unittest.mock import Mock, patch

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.nodes import nodes
from src.state import create_initial_state
from src.schemas import ResearchPlan, SourceSummary, FinalBrief

class TestResearchBriefNodes:
    """Test cases for individual workflow nodes."""
    
    def test_context_summarization_node_no_followup(self):
        """Test context summarization when follow_up is False."""
        state = create_initial_state(
            topic="Test topic",
            follow_up=False,
            user_id="test_user"
        )
        
        result = nodes.context_summarization_node(state)
        
        assert result["context_summary"] is None
        assert len(result["messages"]) > 0
        assert "No context summarization needed" in result["messages"][0].content
    
    def test_context_summarization_node_with_followup(self):
        """Test context summarization when follow_up is True."""
        state = create_initial_state(
            topic="Follow-up topic",
            follow_up=True,
            user_id="test_user"
        )
        
        with patch('src.tools.brief_history_manager.get_relevant_context') as mock_context:
            mock_context.return_value = {
                "previous_topics": ["Previous topic"],
                "common_themes": ["AI", "healthcare"],
                "relevant_context": "Previous research on AI",
                "should_reference_previous": True
            }
            
            with patch.object(nodes, 'context_llm') as mock_llm:
                mock_llm.return_value = Mock()
                
                result = nodes.context_summarization_node(state)
                
                assert "context_summarization_attempts" in result
                assert result["context_summarization_attempts"] == 1
    
    def test_planning_node_success(self):
        """Test successful planning node execution."""
        state = create_initial_state(topic="AI in healthcare", depth=3)
        
        with patch.object(nodes, 'planning_llm') as mock_llm:
            mock_response = ResearchPlan(
                topic="AI in healthcare",
                research_questions=["How does AI improve diagnostics?"],
                search_queries=["AI healthcare diagnostics", "machine learning medicine"],
                expected_sources=["academic papers", "medical journals"],
                depth_level=3
            )
            mock_llm.invoke.return_value = mock_response
            
            result = nodes.planning_node(state)
            
            assert result["research_plan"] == mock_response
            assert result["planning_attempts"] == 1
            assert len(result["messages"]) > 0
    
    def test_planning_node_failure(self):
        """Test planning node with LLM failure."""
        state = create_initial_state(topic="Test topic")
        
        with patch.object(nodes, 'planning_llm') as mock_llm:
            mock_llm.invoke.side_effect = Exception("LLM Error")
            
            result = nodes.planning_node(state)
            
            assert "research_plan" not in result or result["research_plan"] is None
            assert result["planning_attempts"] == 1
            assert len(result["error_messages"]) > 0
            assert "Planning failed" in result["error_messages"][0]
    
    def test_search_node_success(self):
        """Test successful search node execution."""
        state = create_initial_state(topic="Test topic")
        state["research_plan"] = ResearchPlan(
            topic="Test topic",
            research_questions=["Test question?"],
            search_queries=["test query"],
            expected_sources=["web"],
            depth_level=2
        )
        
        with patch('src.tools.web_search_tool.search') as mock_search:
            mock_search.return_value = [
                Mock(title="Test Result", url="http://test.com", 
                     content="Test content", relevance_score=0.9, source_type="web")
            ]
            
            result = nodes.search_node(state)
            
            assert len(result["search_results"]) > 0
            assert result["search_attempts"] == 1
    
    def test_search_node_no_plan(self):
        """Test search node without research plan."""
        state = create_initial_state(topic="Test topic")
        # No research plan set
        
        result = nodes.search_node(state)
        
        assert len(result["error_messages"]) > 0
        assert "No research plan found" in result["error_messages"][0]
    
    def test_content_fetching_node_success(self):
        """Test successful content fetching."""
        state = create_initial_state(topic="Test topic")
        state["search_results"] = [
            Mock(title="Test", url="http://test.com", content="Test content", source_type="web")
        ]
        
        with patch.object(nodes, 'source_summary_llm') as mock_llm:
            mock_response = SourceSummary(
                url="http://test.com",
                title="Test Source",
                summary="Test summary",
                relevance_score=0.8,
                key_points=["Point 1", "Point 2"]
            )
            mock_llm.invoke.return_value = mock_response
            
            result = nodes.content_fetching_node(state)
            
            assert len(result["source_summaries"]) > 0
            assert result["processing_attempts"] == 1
    
    def test_content_fetching_node_no_results(self):
        """Test content fetching with no search results."""
        state = create_initial_state(topic="Test topic")
        # No search results
        
        result = nodes.content_fetching_node(state)
        
        assert len(result["error_messages"]) > 0
        assert "No search results found" in result["error_messages"][0]
    
    def test_synthesis_node_success(self):
        """Test successful synthesis node execution."""
        state = create_initial_state(topic="Test topic")
        state["research_plan"] = ResearchPlan(
            topic="Test topic",
            research_questions=["Test question?"],
            search_queries=["test query"],
            expected_sources=["web"],
            depth_level=2
        )
        state["source_summaries"] = [
            SourceSummary(
                url="http://test.com",
                title="Test Source",
                summary="Test summary", 
                relevance_score=0.8,
                key_points=["Point 1", "Point 2"]
            )
        ]
        
        with patch.object(nodes, 'final_brief_llm') as mock_llm:
            mock_response = FinalBrief(
                topic="Test topic",
                executive_summary="Test summary",
                key_findings=["Finding 1", "Finding 2"],
                detailed_analysis="Test analysis",
                recommendations=["Rec 1", "Rec 2"],
                sources=[],
                research_steps=[],
                limitations=["Limitation 1"],
                confidence_score=0.8,
                generated_at="2024-01-01T00:00:00Z"
            )
            mock_llm.invoke.return_value = mock_response
            
            with patch('src.tools.brief_history_manager.save_brief') as mock_save:
                result = nodes.synthesis_node(state)
                
                assert result["final_brief"] is not None
                assert result["workflow_complete"] is True
                assert result["workflow_success"] is True
                mock_save.assert_called_once()
    
    def test_synthesis_node_missing_dependencies(self):
        """Test synthesis node with missing dependencies."""
        state = create_initial_state(topic="Test topic")
        # Missing research_plan and source_summaries
        
        result = nodes.synthesis_node(state)
        
        assert len(result["error_messages"]) > 0
        assert "Missing research plan or source summaries" in result["error_messages"][0]
    
    def test_post_processing_node_success(self):
        """Test successful post-processing."""
        state = create_initial_state(topic="Test topic")
        state["final_brief"] = FinalBrief(
            topic="Test topic",
            executive_summary="Test summary",
            key_findings=["Finding 1"],
            detailed_analysis="Test analysis",
            recommendations=["Rec 1"],
            sources=[],
            research_steps=[],
            limitations=[],
            confidence_score=0.8,
            generated_at="2024-01-01T00:00:00Z"
        )
        
        result = nodes.post_processing_node(state)
        
        assert result["workflow_complete"] is True
        assert result["workflow_success"] is True
        assert "total_processing_time" in result
    
    def test_post_processing_node_no_brief(self):
        """Test post-processing with no final brief."""
        state = create_initial_state(topic="Test topic")
        # No final brief
        
        result = nodes.post_processing_node(state)
        
        assert len(result["error_messages"]) > 0
        assert "No final brief found" in result["error_messages"][0]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])