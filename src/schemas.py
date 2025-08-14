from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class ResearchStep(BaseModel):
    """Schema for individual research steps."""
    step_number: int = Field(description="Sequential step number")
    action: str = Field(description="Description of the research action taken")
    source: Optional[str] = Field(default=None, description="Source used for this step")
    key_findings: Optional[str] = Field(default=None, description="Key findings from this step")

class SourceSummary(BaseModel):
    """Schema for individual source summaries."""
    url: str = Field(description="Source URL")
    title: str = Field(description="Source title")
    summary: str = Field(description="Summary of the source content")
    relevance_score: float = Field(ge=0.0, le=1.0, description="Relevance score from 0 to 1")
    key_points: List[str] = Field(description="Key points extracted from the source")

class ContextSummary(BaseModel):
    """Schema for context summarization of previous briefs."""
    user_id: str = Field(description="User identifier")
    previous_topics: List[str] = Field(description="Topics from previous briefs")
    common_themes: List[str] = Field(description="Common themes across previous briefs")
    relevant_context: str = Field(description="Relevant context for the current query")
    should_reference_previous: bool = Field(description="Whether to reference previous briefs")

class ResearchPlan(BaseModel):
    """Schema for research planning."""
    topic: str = Field(description="Main research topic")
    research_questions: List[str] = Field(description="Key research questions to investigate")
    search_queries: List[str] = Field(description="Specific search queries to execute")
    expected_sources: List[str] = Field(description="Types of sources expected to find")
    depth_level: int = Field(ge=1, le=5, description="Research depth level from 1 (basic) to 5 (comprehensive)")

class FinalBrief(BaseModel):
    """Schema for the final research brief output."""
    topic: str = Field(description="Research topic")
    executive_summary: str = Field(description="Executive summary of findings")
    key_findings: List[str] = Field(description="List of key findings")
    detailed_analysis: str = Field(description="Detailed analysis section")
    recommendations: List[str] = Field(description="Actionable recommendations")
    sources: List[SourceSummary] = Field(description="Sources used in the research")
    research_steps: List[ResearchStep] = Field(description="Steps taken during research")
    limitations: List[str] = Field(description="Limitations of the research")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Overall confidence in findings")
    generated_at: str = Field(description="Timestamp when brief was generated")
    
class BriefRequest(BaseModel):
    """Schema for API request to generate a brief."""
    topic: str = Field(description="Research topic", min_length=5, max_length=500)
    depth: int = Field(default=3, ge=1, le=5, description="Research depth level")
    follow_up: bool = Field(default=False, description="Whether this is a follow-up query")
    user_id: str = Field(description="User identifier", min_length=1, max_length=100)

class BriefResponse(BaseModel):
    """Schema for API response."""
    success: bool = Field(description="Whether the request was successful")
    brief: Optional[FinalBrief] = Field(default=None, description="Generated brief if successful")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    processing_time: float = Field(description="Time taken to process the request")

class SearchResult(BaseModel):
    """Schema for search results."""
    title: str = Field(description="Title of the search result")
    url: str = Field(description="URL of the search result")
    content: str = Field(description="Content snippet from the search result")
    relevance_score: float = Field(ge=0.0, le=1.0, description="Relevance score")
    source_type: str = Field(description="Type of source (academic, news, blog, etc.)")

class WorkflowState(BaseModel):
    """Schema for workflow state tracking."""
    current_node: str = Field(description="Current node in the workflow")
    completed_steps: List[str] = Field(description="List of completed workflow steps")
    context_summary: Optional[ContextSummary] = Field(default=None, description="Context from previous interactions")
    research_plan: Optional[ResearchPlan] = Field(default=None, description="Generated research plan")
    search_results: List[SearchResult] = Field(default=[], description="Collected search results")
    source_summaries: List[SourceSummary] = Field(default=[], description="Processed source summaries")
    final_brief: Optional[FinalBrief] = Field(default=None, description="Final generated brief")
    error_count: int = Field(default=0, description="Number of errors encountered")
    retry_count: int = Field(default=0, description="Number of retries attempted")