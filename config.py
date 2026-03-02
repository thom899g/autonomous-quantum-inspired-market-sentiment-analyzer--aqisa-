"""
AQISA Configuration Manager
Architectural Choice: Centralized config with environment validation
Why: Ensures consistent configuration access, prevents import-order issues,
and provides runtime validation of critical dependencies.
"""
import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class FirebaseConfig:
    """Firebase configuration with validation"""
    project_id: str
    database_url: str
    credentials_path: str
    
    def __post_init__(self):
        """Validate Firebase configuration"""
        if not os.path.exists(self.credentials_path):
            logger.error(f"Firebase credentials not found at: {self.credentials_path}")
            raise FileNotFoundError(f"Firebase credentials missing: {self.credentials_path}")
        
        # Check file permissions (should not be world-readable)
        if os.stat(self.credentials_path).st_mode & 0o777 > 0o600:
            logger.warning(f"Firebase credentials file has insecure permissions: {self.credentials_path}")

@dataclass
class APIConfig:
    """API credentials configuration"""
    twitter_api_key: Optional[str] = None
    twitter_api_secret: Optional[str] = None
    twitter_access_token: Optional[str] = None
    twitter_access_secret: Optional[str] = None
    
    newsapi_key: Optional[str] = None
    finnhub_key: Optional[str] = None
    
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_user_agent: Optional[str] = None
    
    def validate_credentials(self) -> Dict[str, bool]:
        """Validate which API credentials are available"""
        available = {
            'twitter': all([
                self.twitter_api_key,
                self.twitter_api_secret,
                self.twitter_access_token,
                self.twitter_access_secret
            ]),
            'newsapi': bool(self.newsapi_key),
            'finnhub': bool(self.finnhub_key),
            'reddit': all([
                self.reddit_client_id,
                self.reddit_client_secret,
                self.reddit_user_agent
            ])
        }
        
        for service, is_available in available.items():
            if is_available:
                logger.info(f"{service.upper()} credentials available")
            else:
                logger.warning(f"{service.upper()} credentials missing - service will be disabled")
        
        return available

@dataclass
class SystemConfig:
    """System runtime configuration"""
    max_concurrent_streams: int
    sentiment_batch_size: int
    quantum_state_dimensions: int
    
    def __post_init__(self):
        """Validate system configuration"""
        if self.max_concurrent_streams < 1 or self.max_concurrent_streams > 10:
            logger.warning(f"max_concurrent_streams {self.max_concurrent_streams} outside recommended range (1-10)")
        
        if self.sentiment_batch_size < 100 or self.sentiment_batch_size > 10000:
            logger.warning(f"sentiment_batch_size {self.sentiment_batch_size} outside recommended range (100-10000)")
        
        if self.quantum_state_dimensions not in [4, 8, 16, 32]:
            logger.warning(f"quantum_state_dimensions {self.quantum_state_dimensions} not standard - using 8")
            self.quantum_state_dimensions = 8

class Config:
    """Main configuration singleton"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialize