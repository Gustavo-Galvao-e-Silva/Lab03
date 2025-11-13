import google.generativeai as genai

from backend.utils.utils import get_weather_info
from config.base import get_api_key, CHATBOT_NAME
from backend.data_models.data_models import Tool
from backend.prompts.build_prompt import generate_tooled_system_prompt, generate_data_processor_system_prompt

GEMINI_MODEL: str = "gemini-2.5-flash"
MODEL_CONFIG: genai.GenerationConfig = genai.GenerationConfig(
    temperature=0.4
)

TOOLS_LIST: list[Tool] = [
    Tool(
        name="get_weather_info",
        function=get_weather_info,
        description="Fetches 7-day hourly weather forecast data for a specific location. Returns temperature, humidity, cloud cover, wind speed, precipitation, snowfall, and precipitation probability.",
        params={
            "location": {
                "type": "string",
                "description": "City name (e.g., 'New York', 'London', 'Tokyo'). Will be geocoded to coordinates automatically.",
                "required": True
            },
            "event_date": {
                "type": "string",
                "description": "Date for the weather forecast in YYYY-MM-DD format (e.g., '2024-12-25').",
                "required": True
            }
        },
        constraints=(
            "Only works for dates within the next 7 days (today through 6 days from now). "
            "Date must be in YYYY-MM-DD format. "
            "Returns full 7-day forecast regardless of requested date. "
            "If past dates or dates beyond 7 days are requested, will return an error."
        ),
        usage_examples=[
            "User asks about weather conditions for an upcoming event",
            "User wants to know if it will rain on a specific date",
            "User is planning an outdoor event and needs forecast data",
            "User asks about temperature, precipitation, or wind conditions"
        ]
    )
]

GEMINI_SECRET_KEY_NAME: str = "GEMINI_API_SECRET"
GEMINI_API_SECRET: str = get_api_key(GEMINI_SECRET_KEY_NAME)

tooled_system_prompt = generate_tooled_system_prompt(CHATBOT_NAME, TOOLS_LIST)
data_processor_system_prompt = generate_data_processor_system_prompt()

genai.configure(api_key=GEMINI_API_SECRET)

tooled_model: genai.GenerativeModel = genai.GenerativeModel(
    model_name=GEMINI_MODEL,
    generation_config=MODEL_CONFIG,
    tools=[tool.function for tool in TOOLS_LIST],
    system_instruction=tooled_system_prompt
)

data_processor_model: genai.GenerativeModel = genai.GenerativeModel(
    model_name=GEMINI_MODEL,
    generation_config=MODEL_CONFIG,
    system_instruction=data_processor_system_prompt
)