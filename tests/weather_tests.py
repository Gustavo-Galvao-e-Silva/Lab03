import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import numpy as np


# Assuming your module is named weather_service
# from weather_service import get_weather_info, _get_location_coordinates, _datetime_is_valid


class TestDateValidation:
    """Test the date validation helper function"""

    def test_datetime_is_valid_today(self):
        """Test that today's datetime is valid"""
        from backend.utils.utils import _datetime_is_valid
        today = datetime.now()
        assert _datetime_is_valid(today) == True

    def test_datetime_is_valid_future_within_range(self):
        """Test that datetimes within 6 days are valid"""
        from backend.utils.utils import _datetime_is_valid
        future_datetime = datetime.now() + timedelta(days=3)
        assert _datetime_is_valid(future_datetime) == True

    def test_datetime_is_valid_max_range(self):
        """Test that exactly 6 days from now is valid"""
        from backend.utils.utils import _datetime_is_valid
        max_datetime = datetime.now() + timedelta(days=6)
        assert _datetime_is_valid(max_datetime) == True

    def test_datetime_is_invalid_past(self):
        """Test that past datetimes are invalid"""
        from backend.utils.utils import _datetime_is_valid
        past_datetime = datetime.now() - timedelta(days=1)
        assert _datetime_is_valid(past_datetime) == False

    def test_datetime_is_invalid_too_far_future(self):
        """Test that datetimes beyond 6 days are invalid"""
        from backend.utils.utils import _datetime_is_valid
        far_future = datetime.now() + timedelta(days=7)
        assert _datetime_is_valid(far_future) == False


class TestConvertDateStr:
    """Test the date string conversion helper function"""

    def test_valid_date_string(self):
        """Test converting valid date string"""
        from backend.utils.utils import _convert_date_str_to_datetime
        result = _convert_date_str_to_datetime("2024-12-25")
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 25

    def test_invalid_date_format(self):
        """Test that invalid format raises ValueError"""
        from backend.utils.utils import _convert_date_str_to_datetime
        with pytest.raises(ValueError):
            _convert_date_str_to_datetime("25-12-2024")

    def test_invalid_date_string(self):
        """Test that invalid date raises ValueError"""
        from backend.utils.utils import _convert_date_str_to_datetime
        with pytest.raises(ValueError):
            _convert_date_str_to_datetime("not a date")


class TestGetLocationCoordinates:
    """Test the geocoding helper function"""

    @patch('utils.utils.requests.get')
    def test_successful_geocoding(self, mock_get):
        """Test successful city geocoding"""
        from backend.utils.utils import _get_location_coordinates

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"latitude": 40.7128, "longitude": -74.0060}
            ]
        }
        mock_get.return_value = mock_response

        lat, lon = _get_location_coordinates("New York")

        assert lat == 40.7128
        assert lon == -74.0060
        mock_get.assert_called_once()

    @patch('utils.utils.requests.get')
    def test_geocoding_city_not_found(self, mock_get):
        """Test handling of city not found"""
        from backend.utils.utils import _get_location_coordinates

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="City not found"):
            _get_location_coordinates("NonexistentCity123")

    @patch('utils.utils.requests.get')
    def test_geocoding_api_error(self, mock_get):
        """Test handling of API error"""
        from backend.utils.utils import _get_location_coordinates

        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        with pytest.raises(Exception, match="Error getting location coordinates"):
            _get_location_coordinates("New York")


class TestGetWeatherInfo:
    """Test the main weather info function"""

    def test_invalid_date_format(self):
        """Test that invalid date format returns error"""
        from backend.utils.utils import get_weather_info

        result = get_weather_info("New York", "25-12-2024")

        assert result["error"] is not None
        assert "Invalid date format" in result["error"]
        assert result["data"] is None
        assert result["location"] == "New York"
        assert result["date"] == "25-12-2024"

    def test_invalid_date_string(self):
        """Test that non-date string returns error"""
        from backend.utils.utils import get_weather_info

        result = get_weather_info("New York", "not a date")

        assert result["error"] is not None
        assert "Invalid date format" in result["error"]
        assert result["data"] is None

    def test_invalid_date_past(self):
        """Test that past dates return error"""
        from backend.utils.utils import get_weather_info

        past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        result = get_weather_info("New York", past_date)

        assert result["error"] is not None
        assert "within the next 7 days" in result["error"]
        assert result["data"] is None
        assert result["location"] == "New York"
        assert result["date"] == past_date

    def test_invalid_date_too_far_future(self):
        """Test that dates too far in future return error"""
        from backend.utils.utils import get_weather_info

        far_future = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
        result = get_weather_info("New York", far_future)

        assert result["error"] is not None
        assert "within the next 7 days" in result["error"]
        assert result["data"] is None

    @patch('utils.utils._get_location_coordinates')
    @patch('utils.utils._create_openmeteo_client')
    def test_successful_weather_fetch(self, mock_create_client, mock_get_coords):
        """Test successful weather data fetch"""
        from backend.utils.utils import get_weather_info

        # Mock geocoding
        mock_get_coords.return_value = (40.7128, -74.0060)

        # Mock OpenMeteo response
        mock_hourly = Mock()
        mock_hourly.Time.return_value = 1699200000  # Start timestamp
        mock_hourly.TimeEnd.return_value = 1699372800  # End timestamp (48 hours later)
        mock_hourly.Interval.return_value = 3600  # 1 hour intervals

        # Mock weather variables
        mock_var_0 = Mock()
        mock_var_0.ValuesAsNumpy.return_value = np.array([20.5] * 48)
        mock_var_1 = Mock()
        mock_var_1.ValuesAsNumpy.return_value = np.array([65.0] * 48)
        mock_var_2 = Mock()
        mock_var_2.ValuesAsNumpy.return_value = np.array([30.0] * 48)
        mock_var_3 = Mock()
        mock_var_3.ValuesAsNumpy.return_value = np.array([10.5] * 48)
        mock_var_4 = Mock()
        mock_var_4.ValuesAsNumpy.return_value = np.array([0.0] * 48)
        mock_var_5 = Mock()
        mock_var_5.ValuesAsNumpy.return_value = np.array([0.0] * 48)
        mock_var_6 = Mock()
        mock_var_6.ValuesAsNumpy.return_value = np.array([20.0] * 48)

        mock_hourly.Variables.side_effect = [
            mock_var_0, mock_var_1, mock_var_2, mock_var_3,
            mock_var_4, mock_var_5, mock_var_6
        ]

        mock_response = Mock()
        mock_response.Hourly.return_value = mock_hourly

        mock_client = Mock()
        mock_client.weather_api.return_value = [mock_response]
        mock_create_client.return_value = mock_client

        # Test
        event_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        result = get_weather_info("New York", event_date)

        assert result["error"] is None
        assert result["data"] is not None
        assert result["location"] == "New York"
        assert result["date"] == event_date

        # Check data structure
        assert "time" in result["data"]
        assert "temperature_2m" in result["data"]
        assert "precipitation" in result["data"]
        assert len(result["data"]["time"]) == 48
        assert len(result["data"]["temperature_2m"]) == 48

    @patch('utils.utils._get_location_coordinates')
    def test_geocoding_failure(self, mock_get_coords):
        """Test handling of geocoding failure"""
        from backend.utils.utils import get_weather_info

        mock_get_coords.side_effect = ValueError("City not found")

        event_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        result = get_weather_info("InvalidCity", event_date)

        assert result["error"] is not None
        assert "City not found" in result["error"]
        assert result["data"] is None

    @patch('utils.utils._get_location_coordinates')
    @patch('utils.utils._create_openmeteo_client')
    def test_api_request_failure(self, mock_create_client, mock_get_coords):
        """Test handling of API request failure"""
        from backend.utils.utils import get_weather_info

        mock_get_coords.return_value = (40.7128, -74.0060)
        mock_client = Mock()
        mock_client.weather_api.side_effect = Exception("API connection failed")
        mock_create_client.return_value = mock_client

        event_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        result = get_weather_info("New York", event_date)

        assert result["error"] is not None
        assert "Unable to fetch weather information" in result["error"]
        assert result["data"] is None

    @patch('utils.utils._get_location_coordinates')
    @patch('utils.utils._create_openmeteo_client')
    def test_data_structure_completeness(self, mock_create_client, mock_get_coords):
        """Test that all expected weather variables are present"""
        from backend.utils.utils import get_weather_info

        # Setup mocks
        mock_get_coords.return_value = (40.7128, -74.0060)

        mock_hourly = Mock()
        mock_hourly.Time.return_value = 1699200000
        mock_hourly.TimeEnd.return_value = 1699203600
        mock_hourly.Interval.return_value = 3600

        # Create mock variables
        mock_vars = []
        for _ in range(7):
            mock_var = Mock()
            mock_var.ValuesAsNumpy.return_value = np.array([1.0])
            mock_vars.append(mock_var)

        mock_hourly.Variables.side_effect = mock_vars

        mock_response = Mock()
        mock_response.Hourly.return_value = mock_hourly

        mock_client = Mock()
        mock_client.weather_api.return_value = [mock_response]
        mock_create_client.return_value = mock_client

        event_date = datetime.now().strftime("%Y-%m-%d")
        result = get_weather_info("New York", event_date)

        # Verify all expected keys are present
        expected_keys = [
            "time", "temperature_2m", "relative_humidity_2m",
            "cloud_cover", "wind_speed_10m", "precipitation",
            "snowfall", "precipitation_probability"
        ]

        assert result["error"] is None
        for key in expected_keys:
            assert key in result["data"], f"Missing key: {key}"

    @patch('utils.utils._get_location_coordinates')
    @patch('utils.utils._create_openmeteo_client')
    def test_timestamp_conversion(self, mock_create_client, mock_get_coords):
        """Test that timestamps are properly converted to datetime strings"""
        from backend.utils.utils import get_weather_info

        mock_get_coords.return_value = (40.7128, -74.0060)

        # Use known timestamps
        mock_hourly = Mock()
        mock_hourly.Time.return_value = 1699200000  # 2023-11-05 18:00:00
        mock_hourly.TimeEnd.return_value = 1699203600  # 2023-11-05 19:00:00
        mock_hourly.Interval.return_value = 3600

        mock_vars = []
        for _ in range(7):
            mock_var = Mock()
            mock_var.ValuesAsNumpy.return_value = np.array([1.0])
            mock_vars.append(mock_var)

        mock_hourly.Variables.side_effect = mock_vars

        mock_response = Mock()
        mock_response.Hourly.return_value = mock_hourly

        mock_client = Mock()
        mock_client.weather_api.return_value = [mock_response]
        mock_create_client.return_value = mock_client

        event_date = datetime.now().strftime("%Y-%m-%d")
        result = get_weather_info("New York", event_date)

        assert result["error"] is None
        assert len(result["data"]["time"]) == 1
        # Verify it's a properly formatted datetime string
        time_str = result["data"]["time"][0]
        assert isinstance(time_str, str)
        # Should be able to parse it back
        parsed = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        assert isinstance(parsed, datetime)


class TestIntegration:
    """Integration tests that hit real APIs"""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_end_to_end_flow_real_api(self):
        """Test complete flow from location to weather data using real APIs

        Note: This test makes real API calls and may be slow.
        Skip with: pytest -m "not integration"
        """
        from backend.utils.utils import get_weather_info

        # Execute with real API calls
        event_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        result = get_weather_info("London", event_date)

        print(result)

        # Verify successful response
        assert result["error"] is None, f"API call failed: {result.get('error')}"
        assert result["location"] == "London"
        assert result["date"] == event_date
        assert result["data"] is not None

        # Verify data structure
        assert "time" in result["data"]
        assert "temperature_2m" in result["data"]
        assert "precipitation" in result["data"]
        assert "relative_humidity_2m" in result["data"]
        assert "cloud_cover" in result["data"]
        assert "wind_speed_10m" in result["data"]
        assert "snowfall" in result["data"]
        assert "precipitation_probability" in result["data"]

        # Verify data has values
        assert len(result["data"]["time"]) > 0
        assert len(result["data"]["temperature_2m"]) > 0

        # Verify temperature values are reasonable (sanity check)
        temps = result["data"]["temperature_2m"]
        assert all(isinstance(t, (int, float)) for t in temps), "Temperatures should be numeric"
        assert all(-50 <= t <= 60 for t in temps), "Temperatures should be in reasonable range"

    @pytest.mark.integration
    @pytest.mark.slow
    def test_multiple_locations_real_api(self):
        """Test multiple different locations with real API"""
        from backend.utils.utils import get_weather_info

        locations = ["New York", "Tokyo", "Sydney"]
        event_date = datetime.now().strftime("%Y-%m-%d")

        for location in locations:
            result = get_weather_info(location, event_date)

            print(result)
            assert result["error"] is None, f"Failed for {location}: {result.get('error')}"
            assert result["location"] == location
            assert result["data"] is not None
            assert len(result["data"]["time"]) > 0

    @pytest.mark.integration
    @pytest.mark.slow
    def test_invalid_location_real_api(self):
        """Test that invalid location is handled properly with real API"""
        from backend.utils.utils import get_weather_info

        event_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        result = get_weather_info("XYZ123InvalidCity", event_date)

        # Should return an error for invalid city
        assert result["error"] is not None
        assert result["data"] is None


# Fixtures
@pytest.fixture
def mock_weather_response():
    """Fixture providing a standard mock weather response"""
    mock_hourly = Mock()
    mock_hourly.Time.return_value = 1699200000
    mock_hourly.TimeEnd.return_value = 1699372800
    mock_hourly.Interval.return_value = 3600

    mock_vars = []
    for _ in range(7):
        mock_var = Mock()
        mock_var.ValuesAsNumpy.return_value = np.array([20.0] * 48)
        mock_vars.append(mock_var)

    mock_hourly.Variables.side_effect = mock_vars

    mock_response = Mock()
    mock_response.Hourly.return_value = mock_hourly

    return mock_response


@pytest.fixture
def valid_future_date():
    """Fixture providing a valid future date string"""
    return (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")


@pytest.fixture
def invalid_past_date():
    """Fixture providing an invalid past date string"""
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])