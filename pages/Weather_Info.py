import streamlit as st
from datetime import datetime
import matplotlib.pyplot as plt

from backend.utils.utils import get_weather_info


st.set_page_config(page_title="5-Day Weather Forecast", layout="wide")

st.title("5-Day Weather Forecast")

st.write("Enter a location (e.g., Atlanta)")

location = st.text_input("Location", "Atlanta")

if st.button("Get Forecast"):
    today_str = datetime.today().strftime("%y-%m-%d")
    weather_info = get_weather_info(location, today_str)