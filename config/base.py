import os
import dotenv
import streamlit as st

dotenv.load_dotenv()

ENV = os.getenv("ENV", "prod").lower()
CHATBOT_NAME = "Skye"

def get_api_key(secret_key_name: str) -> str:
    """Fetch API key from environment (dev) or Streamlit secrets (prod)."""
    if ENV == "dev":
        key = os.getenv(secret_key_name)
        source = "environment variables"
    else:
        key = st.secrets.get(secret_key_name)
        source = "Streamlit secrets"
    
    if not key:
        raise ValueError(f"{secret_key_name} not found in {source} (ENV={ENV})")
    
    return key
