import unittest

from weather_server import parse_weather


class WeatherTests(unittest.TestCase):
    def test_parse_canned_response(self):
        geo = {"results": [{"name": "Singapore", "country": "Singapore"}]}
        forecast = {"current": {"temperature_2m": 30, "wind_speed_10m": 12}}
        self.assertIn("30°C", parse_weather(geo, forecast))

    def test_missing_city(self):
        self.assertIn("not find", parse_weather({}, {}))


if __name__ == "__main__":
    unittest.main()
