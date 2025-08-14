#!/usr/bin/env python3
"""
Research Brief Generator - Main CLI Entry Point

This is the command-line interface for the Research Brief Generator.
It uses LangGraph for workflow orchestration and Gemini 1.5 Flash for AI generation.
"""
import argparse
import sys
import os
import time
import json
from typing import Optional

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.workflow import workflow
    from src.config import config
    from src.state import get_state_summary
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure you're running from the project root directory and have installed all dependencies.")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)

def print_banner():
    """Print the application banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                  🔬 Research Brief Generator                  ║
║              AI-Powered Research with LangGraph              ║
╠══════════════════════════════════════════════════════════════╣
║  📝 Context-Aware Research Brief Generation                  ║
║  🧠 Gemini 1.5 Flash AI Model                              ║ 
║  🔍 Web Search Integration                                   ║
║  📊 Structured Output with Pydantic                         ║
║  ⚡ Fast and Reliable Workflow                               ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def validate_environment() -> bool:
    """Validate that the environment is properly configured."""
    try:
        if not config.validate_config():
            print("❌ Configuration Error:")
            print("   No Gemini API key found!")
            print("   Please set GEMINI_API_KEY or GOOGLE_API_KEY environment variable.")
            print("   You can get a free API key from: https://ai.google.dev/")
            return False
        
        print("✅ Configuration validated successfully!")
        print(f"   Using model: {config.GEMINI_MODEL}")
        return True
        
    except Exception as e:
        print(f"❌ Environment validation failed: {e}")
        return False

def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate AI-powered research briefs using LangGraph and Gemini",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --topic "Artificial Intelligence in Healthcare" --depth 3
  %(prog)s --topic "Climate Change Impacts" --depth 4 --follow-up --user-id john_doe
  %(prog)s --topic "Quantum Computing" --depth 2 --output brief.json
  %(prog)s --web-app  # Start the web application
  %(prog)s --api      # Start the REST API server

For more information, visit: https://github.com/your-repo/research-brief-generator
        """
    )
    
    # Main operation modes
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--topic", "-t",
        type=str,
        help="Research topic to generate a brief for"
    )
    mode_group.add_argument(
        "--web-app", "-w",
        action="store_true",
        help="Start the Flask web application"
    )
    mode_group.add_argument(
        "--api", "-a", 
        action="store_true",
        help="Start the FastAPI REST API server"
    )
    
    # Research parameters
    parser.add_argument(
        "--depth", "-d",
        type=int,
        choices=[1, 2, 3, 4, 5],
        default=3,
        help="Research depth level (1=basic, 5=comprehensive). Default: 3"
    )
    
    parser.add_argument(
        "--follow-up", "-f",
        action="store_true", 
        help="Mark this as a follow-up query (will use previous context)"
    )
    
    parser.add_argument(
        "--user-id", "-u",
        type=str,
        default="cli_user",
        help="User identifier for context tracking. Default: cli_user"
    )
    
    # Output options
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file path (JSON format). If not specified, prints to stdout"
    )
    
    parser.add_argument(
        "--format",
        choices=["json", "text", "markdown"],
        default="text",
        help="Output format. Default: text"
    )
    
    # Workflow options
    parser.add_argument(
        "--thread-id",
        type=str,
        help="Thread ID for workflow checkpointing"
    )
    
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Stream workflow progress (experimental)"
    )
    
    # Server options
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host address for web app/API server. Default: 0.0.0.0"
    )
    
    parser.add_argument(
        "--port", "-p",
        type=int,
        help="Port for web app/API server. Default: 5000 (Flask), 8000 (FastAPI)"
    )
    
    # Debugging and utilities
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true", 
        help="Enable debug mode"
    )
    
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Check system health and configuration"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Research Brief Generator v1.0.0"
    )
    
    return parser

def generate_research_brief(
    topic: str,
    depth: int = 3, 
    follow_up: bool = False,
    user_id: str = "cli_user",
    thread_id: Optional[str] = None,
    verbose: bool = False,
    stream: bool = False
) -> dict:
    """Generate a research brief using the workflow."""
    
    print(f"🚀 Starting research brief generation...")
    print(f"   📝 Topic: {topic}")
    print(f"   📊 Depth Level: {depth}")
    print(f"   👤 User ID: {user_id}")
    print(f"   🔄 Follow-up: {'Yes' if follow_up else 'No'}")
    print(f"   🧵 Thread ID: {thread_id or 'Auto-generated'}")
    print("")
    
    start_time = time.time()
    
    try:
        if stream:
            print("🔄 Streaming workflow execution...")
            result = {}
            
            for step in workflow.stream_run(
                topic=topic,
                depth=depth,
                follow_up=follow_up,
                user_id=user_id,
                thread_id=thread_id
            ):
                if verbose:
                    print(f"   📍 Step: {json.dumps(step, indent=2, default=str)}")
                else:
                    # Extract current node if available
                    current_node = step.get("current_node", "unknown")
                    print(f"   ⚙️  Processing: {current_node}")
                
                # Store the last step as result
                result.update(step)
                
        else:
            result = workflow.run(
                topic=topic,
                depth=depth,
                follow_up=follow_up,
                user_id=user_id,
                thread_id=thread_id
            )
        
        execution_time = time.time() - start_time
        
        print(f"\\n⏱️  Total execution time: {execution_time:.1f} seconds")
        
        if result.get("success", False):
            print("✅ Research brief generated successfully!")
        else:
            print("❌ Research brief generation failed!")
            if result.get("error"):
                print(f"   Error: {result['error']}")
        
        if verbose:
            state_summary = get_state_summary(result)
            print(f"\\n🔍 Workflow Summary:")
            for key, value in state_summary.items():
                print(f"   {key}: {value}")
        
        return result
        
    except KeyboardInterrupt:
        print("\\n\\n⚠️  Generation interrupted by user")
        return {"success": False, "error": "Interrupted by user"}
    except Exception as e:
        print(f"\\n❌ Unexpected error: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        return {"success": False, "error": str(e)}

def format_output(result: dict, format_type: str = "text") -> str:
    """Format the result for output."""
    if not result.get("success", False):
        return f"Error: {result.get('error', 'Unknown error')}"
    
    final_brief = result.get("final_brief")
    if not final_brief:
        return "Error: No brief generated"
    
    if format_type == "json":
        # Convert Pydantic model to dict if needed
        if hasattr(final_brief, 'dict'):
            brief_dict = final_brief.dict()
        else:
            brief_dict = final_brief
        
        return json.dumps(brief_dict, indent=2, default=str)
    
    elif format_type == "markdown":
        return format_as_markdown(final_brief)
    
    else:  # text format
        return format_as_text(final_brief)

def format_as_text(brief) -> str:
    """Format brief as plain text."""
    output = []
    
    output.append("=" * 80)
    output.append(f"RESEARCH BRIEF: {brief.topic}")
    output.append("=" * 80)
    output.append(f"Generated: {brief.generated_at}")
    output.append(f"Confidence: {brief.confidence_score:.0%}")
    output.append("")
    
    output.append("EXECUTIVE SUMMARY")
    output.append("-" * 40)
    output.append(brief.executive_summary)
    output.append("")
    
    output.append("KEY FINDINGS")
    output.append("-" * 40)
    for i, finding in enumerate(brief.key_findings, 1):
        output.append(f"{i}. {finding}")
    output.append("")
    
    output.append("DETAILED ANALYSIS")
    output.append("-" * 40) 
    output.append(brief.detailed_analysis)
    output.append("")
    
    output.append("RECOMMENDATIONS")
    output.append("-" * 40)
    for i, rec in enumerate(brief.recommendations, 1):
        output.append(f"{i}. {rec}")
    output.append("")
    
    if brief.sources:
        output.append("SOURCES")
        output.append("-" * 40)
        for i, source in enumerate(brief.sources, 1):
            output.append(f"{i}. {source.title}")
            output.append(f"   URL: {source.url}")
            output.append(f"   Summary: {source.summary}")
            output.append("")
    
    if brief.limitations:
        output.append("LIMITATIONS")
        output.append("-" * 40)
        for i, limitation in enumerate(brief.limitations, 1):
            output.append(f"{i}. {limitation}")
        output.append("")
    
    output.append("=" * 80)
    output.append("Generated by Research Brief Generator")
    output.append("Built with LangGraph, Gemini 1.5 Flash, and Python")
    output.append("=" * 80)
    
    return "\\n".join(output)

def format_as_markdown(brief) -> str:
    """Format brief as Markdown."""
    output = []
    
    output.append(f"# Research Brief: {brief.topic}")
    output.append("")
    output.append(f"**Generated:** {brief.generated_at}  ")
    output.append(f"**Confidence:** {brief.confidence_score:.0%}")
    output.append("")
    
    output.append("## Executive Summary")
    output.append("")
    output.append(brief.executive_summary)
    output.append("")
    
    output.append("## Key Findings")
    output.append("")
    for i, finding in enumerate(brief.key_findings, 1):
        output.append(f"{i}. {finding}")
    output.append("")
    
    output.append("## Detailed Analysis")
    output.append("")
    output.append(brief.detailed_analysis)
    output.append("")
    
    output.append("## Recommendations")
    output.append("")
    for i, rec in enumerate(brief.recommendations, 1):
        output.append(f"{i}. {rec}")
    output.append("")
    
    if brief.sources:
        output.append("## Sources")
        output.append("")
        for i, source in enumerate(brief.sources, 1):
            output.append(f"{i}. **{source.title}**")
            output.append(f"   - URL: [{source.url}]({source.url})")
            output.append(f"   - Summary: {source.summary}")
            output.append("")
    
    if brief.limitations:
        output.append("## Limitations")
        output.append("")
        for i, limitation in enumerate(brief.limitations, 1):
            output.append(f"{i}. {limitation}")
        output.append("")
    
    output.append("---")
    output.append("*Generated by Research Brief Generator*  ")
    output.append("*Built with LangGraph, Gemini 1.5 Flash, and Python*")
    
    return "\\n".join(output)

def start_web_app(host: str = "0.0.0.0", port: int = 5000):
    """Start the Flask web application."""
    try:
        from web_app.app import app
        print(f"🌐 Starting Flask web application...")
        print(f"   Host: {host}")
        print(f"   Port: {port}")
        print(f"   URL: http://{host}:{port}")
        print("")
        print("   Press Ctrl+C to stop the server")
        
        app.run(host=host, port=port, debug=False)
        
    except ImportError:
        print("❌ Web application dependencies not found.")
        print("   Make sure Flask is installed: pip install flask")
    except Exception as e:
        print(f"❌ Failed to start web application: {e}")

def start_api_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the FastAPI server.""" 
    try:
        import uvicorn
        from api.api import app
        
        print(f"⚡ Starting FastAPI server...")
        print(f"   Host: {host}")
        print(f"   Port: {port}") 
        print(f"   URL: http://{host}:{port}")
        print(f"   Docs: http://{host}:{port}/docs")
        print("")
        print("   Press Ctrl+C to stop the server")
        
        uvicorn.run(app, host=host, port=port)
        
    except ImportError:
        print("❌ API server dependencies not found.")
        print("   Make sure FastAPI and Uvicorn are installed: pip install fastapi uvicorn")
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")

def health_check():
    """Perform a system health check."""
    print("🏥 System Health Check")
    print("=" * 50)
    
    # Check configuration
    print("📋 Configuration:")
    try:
        is_configured = config.validate_config()
        print(f"   ✅ API Key: {'Configured' if is_configured else 'Missing'}")
        print(f"   📊 Model: {config.GEMINI_MODEL}")
        print(f"   🔥 Temperature: {config.TEMPERATURE}")
        print(f"   🔄 Max Retries: {config.MAX_RETRIES}")
    except Exception as e:
        print(f"   ❌ Configuration Error: {e}")
    
    # Check dependencies
    print("\\n📦 Dependencies:")
    dependencies = [
        ("langgraph", "LangGraph"),
        ("langchain", "LangChain"), 
        ("langchain_google_genai", "LangChain Google GenAI"),
        ("pydantic", "Pydantic"),
        ("requests", "Requests"),
        ("flask", "Flask (optional)"),
        ("fastapi", "FastAPI (optional)"),
    ]
    
    for module, name in dependencies:
        try:
            __import__(module)
            print(f"   ✅ {name}: Available")
        except ImportError:
            print(f"   ❌ {name}: Not installed")
    
    # Test basic workflow
    print("\\n🧪 Basic Workflow Test:")
    try:
        # This would be a minimal test
        from src.state import create_initial_state
        test_state = create_initial_state("Test topic", user_id="health_check")
        print("   ✅ Workflow initialization: OK")
    except Exception as e:
        print(f"   ❌ Workflow test failed: {e}")
    
    print("\\n" + "=" * 50)
    print("Health check completed!")

def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Show banner unless in quiet mode
    if not args.__dict__.get('quiet', False):
        print_banner()
    
    # Handle special commands first
    if args.health_check:
        health_check()
        return
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Handle different modes
    if args.web_app:
        port = args.port or 5000
        start_web_app(args.host, port)
        
    elif args.api:
        port = args.port or 8000
        start_api_server(args.host, port)
        
    elif args.topic:
        # Generate research brief
        result = generate_research_brief(
            topic=args.topic,
            depth=args.depth,
            follow_up=args.follow_up,
            user_id=args.user_id,
            thread_id=args.thread_id,
            verbose=args.verbose,
            stream=args.stream
        )
        
        # Format and output result
        formatted_output = format_output(result, args.format)
        
        if args.output:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(formatted_output)
                print(f"\\n💾 Output saved to: {args.output}")
            except Exception as e:
                print(f"\\n❌ Failed to save output: {e}")
                print("\\n" + formatted_output)
        else:
            print("\\n" + "=" * 80)
            print("RESEARCH BRIEF OUTPUT")
            print("=" * 80)
            print(formatted_output)
    
    else:
        # No mode specified, show help
        parser.print_help()

if __name__ == "__main__":
    main()