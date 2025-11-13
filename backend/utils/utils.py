import requests
import openmeteo_requests
import requests_cache
from retry_requests import retry
from datetime import datetime, timedelta
import streamlit as st
from google.generativeai import GenerativeModel
from collections import defaultdict


def _get_location_coordinates(city_name: str) -> tuple[float, float]:
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city_name, "count": 1, "language": "en", "format": "json"}
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception("Error getting location coordinates")

    data = response.json()
    if "results" in data and len(data["results"]) > 0:
        result = data["results"][0]
        return result["latitude"], result["longitude"]
    else:
        raise ValueError("City not found")


def _create_openmeteo_client(expire_time: int, max_retries: int, backoff_factor: float) -> openmeteo_requests.Client:
    cache_session = requests_cache.CachedSession('.cache', expire_after=expire_time)
    retry_session = retry(cache_session, retries=max_retries, backoff_factor=backoff_factor)
    return openmeteo_requests.Client(session=retry_session)


def _convert_date_str_to_datetime(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d")


def _datetime_is_valid(date: datetime.date) -> bool:
    today = datetime.now().date()
    event_date = date.date()
    return today <= event_date <= today + timedelta(days=6)


def invoke_gemini_tooled_model(model: GenerativeModel, user_prompt: str, conversation_history: list, tools_list: list) -> str:
    conversation_history.append({"role": "user", "parts": [user_prompt]})

    tools_dict = {tool.name: tool.function for tool in tools_list}

    response = model.generate_content(conversation_history)

    while response.candidates[0].content.parts[0].function_call:
        function_call = response.candidates[0].content.parts[0].function_call
        function_name = function_call.name
        function_args = dict(function_call.args)

        if function_name in tools_dict:
            function_result = tools_dict[function_name](**function_args)
        else:
            function_result = {"error": f"Function {function_name} not found"}

        conversation_history.append({
            "role": "model",
            "parts": [{"function_call": function_call}]
        })

        conversation_history.append({
            "role": "user",
            "parts": [{
                "function_response": {
                    "name": function_name,
                    "response": {"result": function_result}
                }
            }]
        })

        response = model.generate_content(conversation_history)

    return response.candidates[0].content.parts[0].text


def invoke_gemini_data_processor_model(model: GenerativeModel, user_prompt: str) -> str:
    response = model.generate_content({"role": "user", "parts": [user_prompt]})
    return response.candidates[0].content.parts[0].text


def get_weather_info(location: str, event_date: str) -> dict[str, any]:
    if 'weather_cache' not in st.session_state:
        st.session_state.weather_cache = {}

    cache_key = location.lower().strip()
    if cache_key in st.session_state.weather_cache:
        cached = st.session_state.weather_cache[cache_key]
        if datetime.now() - cached['timestamp'] < timedelta(minutes=30):
            cached_result = cached['data'].copy()
            cached_result['from_cache'] = True
            return cached_result

    try:
        event_datetime = _convert_date_str_to_datetime(event_date)
    except ValueError as e:
        return {
            "location": location,
            "date": event_date,
            "data": None,
            "error": f"Invalid date format. Expected YYYY-MM-DD: {e}",
        }

    if not _datetime_is_valid(event_datetime):
        return {
            "location": location,
            "date": event_date,
            "data": None,
            "error": "Event date must be within the next 7 days (today through 6 days from now)",
        }

    try:
        start = datetime.now().date()
        end = start + timedelta(days=6)

        url = "https://api.open-meteo.com/v1/forecast"
        lat, lon = _get_location_coordinates(location)

        start_date_str = start.strftime('%Y-%m-%d')
        end_date_str = end.strftime('%Y-%m-%d')

        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": ["temperature_2m", "relative_humidity_2m", "cloud_cover",
                       "wind_speed_10m", "precipitation", "snowfall",
                       "precipitation_probability"],
            "start_date": start_date_str,
            "end_date": end_date_str,
            "timezone": "America/New_York",
        }

        client = _create_openmeteo_client(expire_time=3600, max_retries=5, backoff_factor=0.2)
        responses = client.weather_api(url, params=params)
        response = responses[0]

        hourly = response.Hourly()

        time_start = hourly.Time()
        time_end = hourly.TimeEnd()
        time_interval = hourly.Interval()

        timestamps = range(time_start, time_end, time_interval)

        hourly_data = {
            "time": [datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S') for t in timestamps],
            "temperature_2m": hourly.Variables(0).ValuesAsNumpy().tolist(),
            "relative_humidity_2m": hourly.Variables(1).ValuesAsNumpy().tolist(),
            "cloud_cover": hourly.Variables(2).ValuesAsNumpy().tolist(),
            "wind_speed_10m": hourly.Variables(3).ValuesAsNumpy().tolist(),
            "precipitation": hourly.Variables(4).ValuesAsNumpy().tolist(),
            "snowfall": hourly.Variables(5).ValuesAsNumpy().tolist(),
            "precipitation_probability": hourly.Variables(6).ValuesAsNumpy().tolist(),
        }

        daily_grouped = defaultdict(list)

        for i in range(len(hourly_data["time"])):
            dt = datetime.strptime(hourly_data["time"][i], '%Y-%m-%d %H:%M:%S')
            date_key = dt.strftime('%Y-%m-%d')
            time_key = dt.strftime('%H:%M:%S')

            hour_dict = {
                "hour": time_key,
                "temperature_2m": hourly_data["temperature_2m"][i],
                "relative_humidity_2m": hourly_data["relative_humidity_2m"][i],
                "cloud_cover": hourly_data["cloud_cover"][i],
                "wind_speed_10m": hourly_data["wind_speed_10m"][i],
                "precipitation": hourly_data["precipitation"][i],
                "snowfall": hourly_data["snowfall"][i],
                "precipitation_probability": hourly_data["precipitation_probability"][i],
            }

            daily_grouped[date_key].append(hour_dict)

        result = {
            "error": None,
            "data": dict(daily_grouped),
            "location": location,
            "date": event_date,
            "from_cache": False
        }

        st.session_state.weather_cache[cache_key] = {
            'data': result,
            'timestamp': datetime.now()
        }

        return result

    except Exception as e:
        return {
            "error": f"Unable to fetch weather information: {e}",
            "data": None,
            "location": location,
            "date": event_date,
        }