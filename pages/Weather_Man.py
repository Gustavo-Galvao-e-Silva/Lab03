import streamlit as st
from datetime import datetime, timedelta

from backend.utils.utils import get_weather_info, invoke_gemini_data_processor_model
from backend.prompts.build_prompt import generate_data_processor_user_prompt
from config.gemini import data_processor_model

st.set_page_config(page_title="Weather Man", layout="wide")

st.title("Weather Man")
st.header("Your friendly weather man. Enter a location and date to receive a detailed weather overview.")

with st.container():
    st.write("### Enter Forecast Details")
    col1, col2 = st.columns(2)

    with col1:
        location = st.text_input(
            label="Location",
            value="Atlanta",
            placeholder="e.g., Atlanta, New York, Tokyo...",
        )

    with col2:
        date = st.date_input(
            label="Date (within 7 days)",
            value="today",
            format="YYYY/MM/DD",
            min_value="today",
            max_value=datetime.now().date() + timedelta(days=6),
        )

center_button = st.columns([4, 1, 4])[1]
with center_button:
    get_forecast = st.button("🔍 Get Forecast", use_container_width=True)

if get_forecast:
    with st.spinner("Fetching weather data..."):
        weather_info = get_weather_info(location, date.strftime("%Y-%m-%d"))
        prompt = generate_data_processor_user_prompt(weather_info, location, date)
        response = invoke_gemini_data_processor_model(data_processor_model, prompt)

    st.markdown("---")
    st.subheader("📄 Forecast Report")
    st.markdown(response)
