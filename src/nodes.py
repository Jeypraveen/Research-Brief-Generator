import time
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from .config import config
from .state import ResearchBriefState, update_node_status
from .schemas import (
    ContextSummary, ResearchPlan, SearchResult, 
    SourceSummary, FinalBrief, ResearchStep
)
from .tools import web_search_tool, content_fetcher, brief_history_manager

class ResearchBriefNodes:
    """Collection of nodes for the Research Brief Generator workflow."""
    
    def __init__(self):
        # Initialize the LLM
        self.llm = ChatGoogleGenerativeAI(
            model=config.GEMINI_MODEL,
            api_key=config.get_api_key(),
            temperature=config.TEMPERATURE,
            max_tokens=config.MAX_TOKENS,
            max_retries=config.MAX_RETRIES
        )
        
        # Create LLMs with structured output for different tasks
        self.context_llm = self.llm.with_structured_output(ContextSummary)
        self.planning_llm = self.llm.with_structured_output(ResearchPlan)
        self.source_summary_llm = self.llm.with_structured_output(SourceSummary)
        self.final_brief_llm = self.llm.with_structured_output(FinalBrief)
    
    def context_summarization_node(self, state: ResearchBriefState) -> Dict[str, Any]:
        """
        Node for summarizing context from previous user interactions.
        Only runs if follow_up is True.
        """
        start_time = time.time()
        node_name = "context_summarization"
        
        try:
            if not state.get("follow_up", False):
                # Skip context summarization for non-follow-up queries
                return {
                    "context_summary": None,
                    "messages": [AIMessage(content="No context summarization needed for new query.")],
                    **update_node_status(state, node_name, time.time() - start_time)
                }
            
            user_id = state["user_id"]
            current_topic = state["topic"]
            
            # Get relevant context from history
            context_data = brief_history_manager.get_relevant_context(user_id, current_topic)
            
            if not context_data["should_reference_previous"]:
                return {
                    "context_summary": None,
                    "messages": [AIMessage(content="No relevant previous context found.")],
                    **update_node_status(state, node_name, time.time() - start_time)
                }
            
            # Create context summary using LLM
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are a research context analyzer. Your task is to analyze previous research interactions and summarize relevant context for the current query.

Create a structured summary that includes:
1. Previous topics researched by this user
2. Common themes across previous research
3. Relevant context that might inform the current research
4. Whether previous research should be referenced

Be concise but comprehensive."""),
                HumanMessage(content=f"""
Current research topic: {current_topic}
Previous topics: {context_data['previous_topics']}
Previous context: {context_data['relevant_context']}
Common themes found: {context_data['common_themes']}

Create a context summary for this follow-up research query.
""")
            ])
            
            response = self.context_llm.invoke(prompt.format_messages())
            
            return {
                "context_summary": response,
                "context_summarization_attempts": state.get("context_summarization_attempts", 0) + 1,
                "messages": [AIMessage(content=f"Context summarized. Found {len(context_data['previous_topics'])} previous topics.")],
                **update_node_status(state, node_name, time.time() - start_time)
            }
            
        except Exception as e:
            error_msg = f"Context summarization failed: {str(e)}"
            return {
                "context_summarization_attempts": state.get("context_summarization_attempts", 0) + 1,
                "error_messages": [error_msg],
                "messages": [AIMessage(content=error_msg)],
                **update_node_status(state, node_name, time.time() - start_time)
            }
    
    def planning_node(self, state: ResearchBriefState) -> Dict[str, Any]:
        """
        Node for creating a research plan based on the topic and context.
        """
        start_time = time.time()
        node_name = "planning"
        
        try:
            topic = state["topic"]
            depth = state["depth"]
            context_summary = state.get("context_summary")
            
            # Build context for planning
            context_info = ""
            if context_summary:
                context_info = f"""
Previous research context:
- Previous topics: {', '.join(context_summary.previous_topics)}
- Common themes: {', '.join(context_summary.common_themes)}
- Relevant context: {context_summary.relevant_context}
"""
            
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=f"""You are a research planning expert. Create a comprehensive research plan for the given topic.

The research depth level is {depth} (1=basic, 5=comprehensive).

Your plan should include:
1. Main research topic (cleaned and focused)
2. 3-7 key research questions to investigate
3. 5-10 specific search queries to execute
4. Types of sources expected to find
5. Appropriate depth level for the research

Consider any previous research context provided to avoid duplication and build upon previous work."""),
                HumanMessage(content=f"""
Research topic: {topic}
Research depth level: {depth}
{context_info}

Create a structured research plan for this topic.
""")
            ])
            
            response = self.planning_llm.invoke(prompt.format_messages())
            
            return {
                "research_plan": response,
                "planning_attempts": state.get("planning_attempts", 0) + 1,
                "messages": [AIMessage(content=f"Research plan created with {len(response.research_questions)} questions and {len(response.search_queries)} search queries.")],
                **update_node_status(state, node_name, time.time() - start_time)
            }
            
        except Exception as e:
            error_msg = f"Planning failed: {str(e)}"
            return {
                "planning_attempts": state.get("planning_attempts", 0) + 1,
                "error_messages": [error_msg],
                "messages": [AIMessage(content=error_msg)],
                **update_node_status(state, node_name, time.time() - start_time)
            }
    
    def search_node(self, state: ResearchBriefState) -> Dict[str, Any]:
        """
        Node for executing web searches based on the research plan.
        """
        start_time = time.time()
        node_name = "search"
        
        try:
            research_plan = state.get("research_plan")
            if not research_plan:
                raise ValueError("No research plan found")
            
            search_results = []
            
            # Execute each search query
            for query in research_plan.search_queries:
                try:
                    results = web_search_tool.search(
                        query, 
                        num_results=min(config.MAX_SEARCH_RESULTS // len(research_plan.search_queries), 5)
                    )
                    search_results.extend(results)
                    time.sleep(0.5)  # Rate limiting
                except Exception as e:
                    print(f"Search failed for query '{query}': {e}")
                    continue
            
            # Sort results by relevance score
            search_results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Limit total results
            search_results = search_results[:config.MAX_SEARCH_RESULTS]
            
            return {
                "search_results": search_results,
                "search_attempts": state.get("search_attempts", 0) + 1,
                "messages": [AIMessage(content=f"Found {len(search_results)} search results across {len(research_plan.search_queries)} queries.")],
                **update_node_status(state, node_name, time.time() - start_time)
            }
            
        except Exception as e:
            error_msg = f"Search failed: {str(e)}"
            return {
                "search_attempts": state.get("search_attempts", 0) + 1,
                "error_messages": [error_msg],
                "messages": [AIMessage(content=error_msg)],
                **update_node_status(state, node_name, time.time() - start_time)
            }
    
    def content_fetching_node(self, state: ResearchBriefState) -> Dict[str, Any]:
        """
        Node for fetching and processing content from search results.
        """
        start_time = time.time()
        node_name = "content_fetching"
        
        try:
            search_results = state.get("search_results", [])
            if not search_results:
                raise ValueError("No search results found")
            
            # Select top results for content fetching
            top_results = search_results[:min(len(search_results), 5)]
            
            source_summaries = []
            
            for result in top_results:
                try:
                    # In a real implementation, fetch actual content
                    # content = content_fetcher.fetch_content(result.url)
                    
                    # For now, create summary from search result
                    prompt = ChatPromptTemplate.from_messages([
                        SystemMessage(content="""You are a content summarization expert. Create a structured summary of the given search result.

Extract key points and assess relevance to the research topic. Be comprehensive but concise."""),
                        HumanMessage(content=f"""
Search result to summarize:
Title: {result.title}
URL: {result.url}
Content: {result.content}
Source Type: {result.source_type}

Topic being researched: {state['topic']}

Create a structured source summary with key points and relevance assessment.
""")
                    ])
                    
                    summary = self.source_summary_llm.invoke(prompt.format_messages())
                    source_summaries.append(summary)
                    
                except Exception as e:
                    print(f"Failed to process result {result.url}: {e}")
                    continue
            
            return {
                "source_summaries": source_summaries,
                "processing_attempts": state.get("processing_attempts", 0) + 1,
                "messages": [AIMessage(content=f"Processed {len(source_summaries)} sources successfully.")],
                **update_node_status(state, node_name, time.time() - start_time)
            }
            
        except Exception as e:
            error_msg = f"Content processing failed: {str(e)}"
            return {
                "processing_attempts": state.get("processing_attempts", 0) + 1,
                "error_messages": [error_msg],
                "messages": [AIMessage(content=error_msg)],
                **update_node_status(state, node_name, time.time() - start_time)
            }
    
    def synthesis_node(self, state: ResearchBriefState) -> Dict[str, Any]:
        """
        Node for synthesizing all research into a final brief.
        """
        start_time = time.time()
        node_name = "synthesis"
        
        try:
            topic = state["topic"]
            research_plan = state.get("research_plan")
            source_summaries = state.get("source_summaries", [])
            context_summary = state.get("context_summary")
            
            if not research_plan or not source_summaries:
                raise ValueError("Missing research plan or source summaries")
            
            # Build context for synthesis
            sources_text = "\\n\\n".join([
                f"Source: {summary.title}\\nURL: {summary.url}\\nSummary: {summary.summary}\\nKey Points: {'; '.join(summary.key_points)}"
                for summary in source_summaries
            ])
            
            context_info = ""
            if context_summary and context_summary.should_reference_previous:
                context_info = f"""
Previous research context to consider:
{context_summary.relevant_context}
"""
            
            # Create research steps
            research_steps = [
                {
                    "step_number": 1,
                    "action": f"Planned research with {len(research_plan.research_questions)} key questions",
                    "source": "Research Planning",
                    "key_findings": f"Identified {len(research_plan.search_queries)} search strategies"
                },
                {
                    "step_number": 2, 
                    "action": f"Conducted web search across {len(research_plan.search_queries)} queries",
                    "source": "Web Search",
                    "key_findings": f"Found {len(source_summaries)} relevant sources"
                },
                {
                    "step_number": 3,
                    "action": "Analyzed and summarized source content",
                    "source": "Content Analysis", 
                    "key_findings": "Extracted key insights and evidence"
                }
            ]
            
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=f"""You are a research synthesis expert. Create a comprehensive research brief by analyzing and synthesizing all provided sources.

The brief should be professional, evidence-based, and well-structured. Include:
1. Executive summary highlighting key findings
2. List of key findings with evidence
3. Detailed analysis synthesizing all sources
4. Actionable recommendations
5. Research limitations
6. Confidence assessment

Research topic: {topic}
Research depth level: {state['depth']}

Generate timestamp as current time in ISO format.
{context_info}"""),
                HumanMessage(content=f"""
Research Question: {research_plan.research_questions[0] if research_plan.research_questions else topic}

Source Material:
{sources_text}

Research Steps Taken:
{chr(10).join([f"{step['step_number']}. {step['action']}" for step in research_steps])}

Create a comprehensive final research brief synthesizing all this information.
""")
            ])
            
            final_brief = self.final_brief_llm.invoke(prompt.format_messages())
            
            # Add metadata
            final_brief.topic = topic
            final_brief.generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            final_brief.sources = source_summaries
            final_brief.research_steps = [
                ResearchStep(**step) for step in research_steps
            ]
            
            # Save to history
            brief_history_manager.save_brief(
                state["user_id"], 
                final_brief.dict()
            )
            
            return {
                "final_brief": final_brief,
                "synthesis_attempts": state.get("synthesis_attempts", 0) + 1,
                "workflow_complete": True,
                "workflow_success": True,
                "messages": [AIMessage(content="Research brief completed successfully!")],
                **update_node_status(state, node_name, time.time() - start_time)
            }
            
        except Exception as e:
            error_msg = f"Synthesis failed: {str(e)}"
            return {
                "synthesis_attempts": state.get("synthesis_attempts", 0) + 1,
                "error_messages": [error_msg],
                "messages": [AIMessage(content=error_msg)],
                **update_node_status(state, node_name, time.time() - start_time)
            }
    
    def post_processing_node(self, state: ResearchBriefState) -> Dict[str, Any]:
        """
        Node for final post-processing and validation.
        """
        start_time = time.time()
        node_name = "post_processing"
        
        try:
            final_brief = state.get("final_brief")
            if not final_brief:
                raise ValueError("No final brief found for post-processing")
            
            # Validate the brief
            validation_results = self._validate_brief(final_brief)
            
            # Calculate total processing time
            total_time = sum(state.get("node_execution_times", {}).values())
            
            return {
                "total_processing_time": total_time,
                "workflow_complete": True,
                "workflow_success": True,
                "messages": [AIMessage(content=f"Post-processing completed. Brief validation: {validation_results}")],
                **update_node_status(state, node_name, time.time() - start_time)
            }
            
        except Exception as e:
            error_msg = f"Post-processing failed: {str(e)}"
            return {
                "error_messages": [error_msg],
                "messages": [AIMessage(content=error_msg)],
                **update_node_status(state, node_name, time.time() - start_time)
            }
    
    def _validate_brief(self, brief: FinalBrief) -> Dict[str, bool]:
        """Validate the final brief structure and content."""
        return {
            "has_executive_summary": bool(brief.executive_summary),
            "has_key_findings": len(brief.key_findings) > 0,
            "has_detailed_analysis": bool(brief.detailed_analysis),
            "has_recommendations": len(brief.recommendations) > 0,
            "has_sources": len(brief.sources) > 0,
            "has_research_steps": len(brief.research_steps) > 0,
            "confidence_in_range": 0.0 <= brief.confidence_score <= 1.0
        }

# Global nodes instance
nodes = ResearchBriefNodes()