# Research Brief Generator - Setup Instructions

## Step-by-Step Setup Guide

### 1. Prerequisites Check
- ✅ Python 3.9+ installed (check with `python --version`)
- ✅ Visual Studio Code installed (optional but recommended)
- ✅ Internet connection for API access

### 2. Get Your Free Gemini API Key
1. Visit https://ai.google.dev/
2. Sign in with your Google account
3. Click "Get API Key" → "Create API Key"
4. Copy your API key (keep it secure!)

### 3. Project Setup

```bash
# Clone the repository (or download and extract)
cd research_brief_generator

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env file and add your GEMINI_API_KEY
```

### 4. Configuration

Edit the `.env` file:
```
GEMINI_API_KEY=your_api_key_here_from_google_ai_studio
SERPER_API_KEY=your_serper_api_key_here
GEMINI_MODEL=gemini-1.5-flash
TEMPERATURE=0.7
MAX_RETRIES=3 
MAX_SEARCH_RESULTS=10
SEARCH_TIMEOUT=30
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_SECRET_KEY=your_secret_key_here_change_in_production
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
BRIEF_HISTORY_FILE=brief_history.json
LANGSMITH_API_KEY=
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=
MAX_SEARCH_RESULTS=10
SEARCH_TIMEOUT=30
SERPER_SEARCH_TYPE=search
SERPER_GL=us
SERPER_HL=en



```

### 5. Test Installation

```bash
# Run health check
python main.py --health-check

# Run demo
python demo.py

# Generate your first brief
python main.py --topic "Artificial Intelligence in Healthcare" --depth 3
```

### 6. Visual Studio Code Setup (Recommended)

1. Open VS Code
2. Open the `research_brief_generator` folder
3. Install recommended extensions (VS Code will prompt you)
4. Select Python interpreter: Ctrl+Shift+P → "Python: Select Interpreter" → Choose venv/Scripts/python.exe

### 7. Usage Options

**Command Line:**
```bash
python main.py --topic "Your research topic" --depth 3
```

**Web Interface:**
```bash
python main.py --web-app
# Open http://localhost:5000 in your browser
```

**API Server:**
```bash
python main.py --api
# API docs at http://localhost:8000/docs
```

### 8. Troubleshooting

**Common Issues:**

1. **API Key Error**: Make sure GEMINI_API_KEY is set in .env
2. **Import Errors**: Run `pip install -r requirements.txt`
3. **Port Issues**: Use different ports with `--port 5001`

**Getting Help:**
- Check the README.md for detailed documentation
- Run `python main.py --help` for CLI options
- Visit https://ai.google.dev/ for Gemini API help

### 9. What's Included

- ✅ Complete LangGraph workflow implementation
- ✅ Web UI with Flask
- ✅ REST API with FastAPI  
- ✅ CLI interface
- ✅ Unit tests
- ✅ VS Code configuration
- ✅ Documentation and examples

### 10. Next Steps

1. **Explore the Code**: Look at `src/workflow.py` for the main logic
2. **Run Tests**: `python -m pytest tests/ -v`
3. **Customize**: Modify nodes in `src/nodes.py`
4. **Deploy**: Use the provided deployment guides

## Quick Commands Reference

```bash
# Health check
python main.py --health-check

# Generate brief
python main.py --topic "Your topic" --depth 3 --verbose

# Web app
python main.py --web-app --port 5000

# API server  
python main.py --api --port 8000

# Run tests
make test
# or
python -m pytest tests/ -v

# Format code
make format
# or  
black src/ tests/ --line-length=100
```

**You're all set! 🎉**

The Research Brief Generator is now ready to use. Start with the demo script (`python demo.py`) or jump straight into generating your first research brief!
