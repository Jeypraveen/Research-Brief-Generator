#!/usr/bin/env python3
"""
Demo script for the Research Brief Generator.
Run this after setting up your environment to test the system.
"""
import os
import sys
import time

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_demo():
    """Run a demonstration of the Research Brief Generator."""
    print("🎬 Research Brief Generator Demo")
    print("=" * 50)

    try:
        from src.config import config

        # Check configuration
        print("🔧 Checking configuration...")
        if not config.validate_config():
            print("❌ Configuration error: No API key found!")
            print("   Please set GEMINI_API_KEY in your .env file")
            print("   Get a free API key from: https://ai.google.dev/")
            return False

        print("✅ Configuration OK!")
        print(f"   Model: {config.GEMINI_MODEL}")
        print()

        # Import workflow
        print("📦 Loading workflow...")
        from src.workflow import workflow
        print("✅ Workflow loaded!")
        print()

        # Demo topics
        demo_topics = [
            ("Renewable Energy Trends", 2),
            ("AI in Education", 3),
            ("Future of Work", 2)
        ]

        print("🚀 Running demo queries...")
        print()

        for i, (topic, depth) in enumerate(demo_topics, 1):
            print(f"📝 Demo {i}/3: {topic} (Depth: {depth})")
            print("-" * 40)

            start_time = time.time()

            try:
                result = workflow.run(
                    topic=topic,
                    depth=depth,
                    user_id="demo_user",
                    follow_up=False
                )

                execution_time = time.time() - start_time

                if result.get("success", False):
                    brief = result.get("final_brief")
                    print(f"✅ Success! ({execution_time:.1f}s)")
                    if brief:
                        print(f"   Executive Summary: {brief.executive_summary[:100]}...")
                        print(f"   Key Findings: {len(brief.key_findings)} findings")
                        print(f"   Sources: {len(brief.sources)} sources")
                        print(f"   Confidence: {brief.confidence_score:.0%}")
                else:
                    print(f"❌ Failed: {result.get('error', 'Unknown error')}")

            except Exception as e:
                print(f"❌ Error: {str(e)}")

            print()
            time.sleep(1)  # Brief pause between demos

        print("🎉 Demo completed!")
        print()
        print("Next steps:")
        print("  1. Try the CLI: python main.py --topic 'Your topic' --depth 3")
        print("  2. Start web app: python main.py --web-app")
        print("  3. Start API: python main.py --api")
        print("  4. Run tests: python -m pytest tests/ -v")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you've installed dependencies: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = run_demo()
    sys.exit(0 if success else 1)
