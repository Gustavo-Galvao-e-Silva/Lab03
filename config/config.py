import dotenv
import os

dotenv.load_dotenv()

GEMINI_API_SECRET = os.getenv("GEMINI_API_SECRET")  
GEMINI_MODEL = "gemini-1.5-flash"