from datetime import datetime, timedelta

from backend.prompts.gemini_prompts import tooled_system_prompt, data_processor_system_prompt, data_processor_user_prompt
from backend.data_models.data_models import Tool


def generate_tooled_system_prompt(chatbot_name: str, tools_list: list[Tool]) -> str:
    current_date = datetime.now()
    tomorrow = current_date + timedelta(days=1)
    next_week = current_date + timedelta(days=7)

    return tooled_system_prompt.format(
        current_date.strftime('%A, %B %d, %Y'),
        tomorrow.strftime('%A, %B %d, %Y'),
        tomorrow.strftime('%Y-%m-%d'),
        next_week.strftime('%A, %B %d, %Y'),
        next_week.strftime('%Y-%m-%d'),
        tomorrow.strftime('%Y-%m-%d'),
        current_date.strftime('%A'),
        chatbot_name,
        tools_list
    )


def generate_data_processor_system_prompt() -> str:
    return data_processor_system_prompt.format()


def generate_data_processor_user_prompt(weather_data: dict[str, any], location: str, date: str) -> str:
    return data_processor_user_prompt.format(
        location,
        date,
        weather_data
    )