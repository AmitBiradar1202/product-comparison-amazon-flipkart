import os

# Google Custom Search API Configuration
API_KEY = os.environ.get("API_KEY", "Get Your Own")
SEARCH_ENGINE_ID = os.environ.get("SEARCH_ENGINE_ID", "Get Your Own")

# Chrome Driver Configuration
# In production, this path needs to be configured correctly
CHROME_DRIVER_PATH = os.environ.get("CHROME_DRIVER_PATH", "/usr/bin/chromedriver")

# Flask Configuration
SECRET_KEY = os.environ.get("SESSION_SECRET", "default-secret-key")
