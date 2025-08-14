import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the Research Brief Generator."""
    
    # API Keys
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")  # Alternative name
    
    # Model Configuration
    GEMINI_MODEL: str = "gemini-1.5-flash"
    TEMPERATURE: float = 0.7
    MAX_TOKENS: Optional[int] = None
    MAX_RETRIES: int = 3
    
    # Search Configuration
    MAX_SEARCH_RESULTS: int = 10
    SEARCH_TIMEOUT: int = 30
    
    # Workflow Configuration
    MAX_CONTEXT_SUMMARIZATION_ATTEMPTS: int = 3
    MAX_PLANNING_ATTEMPTS: int = 3
    MAX_SYNTHESIS_ATTEMPTS: int = 3
    
    # Flask Configuration
    FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    FLASK_HOST: str = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000"))
    
    # FastAPI Configuration
    FASTAPI_HOST: str = os.getenv("FASTAPI_HOST", "0.0.0.0")
    FASTAPI_PORT: int = int(os.getenv("FASTAPI_PORT", "8000"))
    
    # Data Storage
    BRIEF_HISTORY_FILE: str = "brief_history.json"
    
    @classmethod
    def get_api_key(cls) -> str:
        """Get the API key, trying both environment variable names."""
        api_key = cls.GEMINI_API_KEY or cls.GOOGLE_API_KEY
        if not api_key:
            raise ValueError(
                "No API key found. Please set GEMINI_API_KEY or GOOGLE_API_KEY environment variable."
            )
        return api_key
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that required configuration is present."""
        try:
            cls.get_api_key()
            return True
        except ValueError:
            return False

# Global config instance
config = Config()