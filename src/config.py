"""
Configuration settings for the Research Brief Generator.
"""
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
    SERPER_API_KEY: Optional[str] = os.getenv("SERPER_API_KEY")  # For web search
    
    # Model Configuration
    GEMINI_MODEL: str = "gemini-1.5-flash"
    TEMPERATURE: float = 0.7
    MAX_TOKENS: Optional[int] = None
    MAX_RETRIES: int = 3
    
    # Search Configuration
    MAX_SEARCH_RESULTS: int = 10
    SEARCH_TIMEOUT: int = 30
    SERPER_SEARCH_TYPE: str = "search"  # Options: search, news, images, videos
    SERPER_GL: str = "us"  # Geolocation
    SERPER_HL: str = "en"  # Host language
    
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
    def get_gemini_api_key(cls) -> str:
        """Get the Gemini API key, trying both environment variable names."""
        api_key = cls.GEMINI_API_KEY or cls.GOOGLE_API_KEY
        if not api_key:
            raise ValueError(
                "No Gemini API key found. Please set GEMINI_API_KEY or GOOGLE_API_KEY environment variable."
            )
        return api_key
    
    @classmethod
    def get_serper_api_key(cls) -> Optional[str]:
        """Get the Serper API key for web search."""
        return cls.SERPER_API_KEY
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that required configuration is present."""
        try:
            cls.get_gemini_api_key()
            return True
        except ValueError:
            return False
    
    @classmethod
    def has_serper_key(cls) -> bool:
        """Check if Serper API key is available for real web search."""
        return bool(cls.get_serper_api_key())

# Global config instance
config = Config()
