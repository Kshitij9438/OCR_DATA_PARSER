import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

def get_env_var(name: str) -> str:
    """Get environment variable or raise a clear error if missing."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"❌ Missing required environment variable: {name}\n"
            f"👉 Did you copy .env.example to .env and fill in your keys?"
        )
    return value

# Example usage
GOOGLE_API_KEY = get_env_var("GOOGLE_API_KEY")

# Try to get credentials path, but don't fail if not provided
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Alternative: Use individual credential environment variables
GOOGLE_CLOUD_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
GOOGLE_CLOUD_PRIVATE_KEY = os.getenv("GOOGLE_CLOUD_PRIVATE_KEY")
GOOGLE_CLOUD_CLIENT_EMAIL = os.getenv("GOOGLE_CLOUD_CLIENT_EMAIL")
GOOGLE_CLOUD_CLIENT_ID = os.getenv("GOOGLE_CLOUD_CLIENT_ID")

# Debug logging
print(f"DEBUG - GOOGLE_CLOUD_PROJECT_ID: {'SET' if GOOGLE_CLOUD_PROJECT_ID else 'NOT SET'}")
print(f"DEBUG - GOOGLE_CLOUD_PRIVATE_KEY: {'SET' if GOOGLE_CLOUD_PRIVATE_KEY else 'NOT SET'}")
print(f"DEBUG - GOOGLE_CLOUD_CLIENT_EMAIL: {'SET' if GOOGLE_CLOUD_CLIENT_EMAIL else 'NOT SET'}")
print(f"DEBUG - GOOGLE_CLOUD_CLIENT_ID: {'SET' if GOOGLE_CLOUD_CLIENT_ID else 'NOT SET'}")

# Optional vars (with defaults)
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
PORT = int(os.getenv("PORT", "8000"))
