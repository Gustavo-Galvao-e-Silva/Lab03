from config.base import get_api_key

GEMINI_MODEL = "gemini-2.5-flash"
TOOLS_LIST = ["get_weather_info"]
GEMINI_SECRET_KEY_NAME = "GEMINI_API_SECRET"
GEMINI_API_SECRET = get_api_key(GEMINI_SECRET_KEY_NAME)
