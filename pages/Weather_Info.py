import streamlit as st
import pandas as pd
from datetime import datetime
from backend.utils.utils import get_weather_info


def _process_weather_data(weather_info: dict) -> pd.DataFrame:
    if weather_info.get("error") or not weather_info.get("data"):
        return pd.DataFrame()

    all_records = []
    for date, hourly_data in weather_info["data"].items():
        for record in hourly_data:
            record_copy = record.copy()
            record_copy["date"] = date
            all_records.append(record_copy)

    return pd.DataFrame(all_records)


def _filter_by_hour_range(df: pd.DataFrame, date: str, start_hour: int, end_hour: int) -> pd.DataFrame:
    date_df = df[df["date"] == date].copy()
    date_df["hour_num"] = date_df["hour"].str.split(":").str[0].astype(int)
    filtered_df = date_df[(date_df["hour_num"] >= start_hour) & (date_df["hour_num"] <= end_hour)]
    filtered_df["hour_label"] = filtered_df["hour_num"].apply(lambda x: f"{int(x):02d}:00")
    return filtered_df.sort_values("hour_num")


def display_temperature_humidity_chart(df: pd.DataFrame) -> None:
    chart_data = pd.DataFrame({
        "Hour": df["hour_label"],
        "Temperature (°C)": df["temperature_2m"].values,
        "Humidity (%)": df["relative_humidity_2m"].values
    })

    st.line_chart(
        data=chart_data,
        x="Hour",
        y=["Temperature (°C)", "Humidity (%)"],
        color=["#FF4B4B", "#4B9EFF"]
    )


def display_wind_precipitation_chart(df: pd.DataFrame) -> None:
    chart_data = pd.DataFrame({
        "Hour": df["hour_label"],
        "Wind Speed (km/h)": df["wind_speed_10m"].values,
        "Precipitation (mm)": df["precipitation"].values
    })

    st.line_chart(
        data=chart_data,
        x="Hour",
        y=["Wind Speed (km/h)", "Precipitation (mm)"],
        color=["#00CC88", "#AA44FF"]
    )


def display_cloud_cover_chart(df: pd.DataFrame) -> None:
    chart_data = pd.DataFrame({
        "Hour": df["hour_label"],
        "Cloud Cover (%)": df["cloud_cover"].values
    })

    st.area_chart(
        data=chart_data,
        x="Hour",
        y="Cloud Cover (%)",
        color="#87CEEB"
    )


st.set_page_config(
    page_title="Weather Visualizations",
    page_icon="🌤️",
)

necessary_session_keys = ["weather_data_df", "location", "available_dates"]

for key in necessary_session_keys:
    if key not in st.session_state:
        if key == "weather_data_df":
            st.session_state[key] = pd.DataFrame()
        elif key == "location":
            st.session_state[key] = ""
        elif key == "available_dates":
            st.session_state[key] = []

st.title("Weather Data Visualizations 🌤️")
st.write("Interactive weather graphs with hourly data")
st.divider()

st.subheader("Enter Location")
location_input = st.text_input(
    "Type a location (e.g., Atlanta, New York, London):",
    value=st.session_state.location,
    placeholder="Enter city name"
)

col1, col2, col3 = st.columns(3)

with col2:
    if st.button("Fetch Weather Data"):
        if location_input:
            with st.spinner(f"Fetching weather data for {location_input}..."):
                try:
                    today_date = datetime.now().strftime("%Y-%m-%d")
                    weather_response = get_weather_info(location_input, today_date)

                    if weather_response.get("error"):
                        st.error(f"Error fetching data: {weather_response['error']}")
                    else:
                        st.session_state.weather_data_df = _process_weather_data(weather_response)
                        st.session_state.location = location_input
                        st.session_state.available_dates = sorted(
                            st.session_state.weather_data_df["date"].unique().tolist())
                        st.success(f"Successfully loaded weather data for {location_input}!")
                except Exception as e:
                    st.error(f"Failed to fetch weather data: {str(e)}")
        else:
            st.warning("Please enter a location")

st.divider()

if not st.session_state.weather_data_df.empty:
    st.header("Weather Graphs")
    st.write(f"**Location:** {st.session_state.location}")

    st.subheader("Graph 1: Temperature and Humidity")
    st.write(
        "This graph shows the relationship between temperature and relative humidity throughout the selected time period.")

    selected_date_1 = st.selectbox(
        "Select Date:",
        options=st.session_state.available_dates,
        index=0,
        key="date_selector_1"
    )

    col1, col2 = st.columns(2)
    with col1:
        start_hour_1 = st.slider(
            "Start Hour:",
            min_value=0,
            max_value=23,
            value=0,
            key="start_hour_1"
        )
    with col2:
        end_hour_1 = st.slider(
            "End Hour:",
            min_value=0,
            max_value=23,
            value=23,
            key="end_hour_1"
        )

    if start_hour_1 <= end_hour_1:
        filtered_data_1 = _filter_by_hour_range(
            st.session_state.weather_data_df,
            selected_date_1,
            start_hour_1,
            end_hour_1
        )
        if not filtered_data_1.empty:
            display_temperature_humidity_chart(filtered_data_1)
        else:
            st.warning("No data available for selected time range")
    else:
        st.error("Start hour must be less than or equal to end hour")

    st.divider()

    st.subheader("Graph 2: Wind Speed and Precipitation")
    st.write("This graph displays wind speed patterns and precipitation levels throughout the day.")

    selected_date_2 = st.selectbox(
        "Select Date:",
        options=st.session_state.available_dates,
        index=0,
        key="date_selector_2"
    )

    col3, col4 = st.columns(2)
    with col3:
        start_hour_2 = st.slider(
            "Start Hour:",
            min_value=0,
            max_value=23,
            value=0,
            key="start_hour_2"
        )
    with col4:
        end_hour_2 = st.slider(
            "End Hour:",
            min_value=0,
            max_value=23,
            value=23,
            key="end_hour_2"
        )

    if start_hour_2 <= end_hour_2:
        filtered_data_2 = _filter_by_hour_range(
            st.session_state.weather_data_df,
            selected_date_2,
            start_hour_2,
            end_hour_2
        )
        if not filtered_data_2.empty:
            display_wind_precipitation_chart(filtered_data_2)
        else:
            st.warning("No data available for selected time range")
    else:
        st.error("Start hour must be less than or equal to end hour")

    st.divider()

    st.subheader("Graph 3: Cloud Cover")
    st.write("This graph shows cloud cover percentage throughout the selected time period.")

    selected_date_3 = st.selectbox(
        "Select Date:",
        options=st.session_state.available_dates,
        index=0,
        key="date_selector_3"
    )

    col5, col6 = st.columns(2)
    with col5:
        start_hour_3 = st.slider(
            "Start Hour:",
            min_value=0,
            max_value=23,
            value=0,
            key="start_hour_3"
        )
    with col6:
        end_hour_3 = st.slider(
            "End Hour:",
            min_value=0,
            max_value=23,
            value=23,
            key="end_hour_3"
        )

    if start_hour_3 <= end_hour_3:
        filtered_data_3 = _filter_by_hour_range(
            st.session_state.weather_data_df,
            selected_date_3,
            start_hour_3,
            end_hour_3
        )
        if not filtered_data_3.empty:
            display_cloud_cover_chart(filtered_data_3)
        else:
            st.warning("No data available for selected time range")
    else:
        st.error("Start hour must be less than or equal to end hour")

else:
    st.info("Enter a location and click 'Fetch Weather Data' to view visualizations")