import unittest

from weather_server import parse_weather


class T(unittest.TestCase):
    def test_parse(self):
        self.assertIn(
            "30°C",
            parse_weather(
                {"results": [{"name": "Singapore"}]},
                {"current": {"temperature_2m": 30, "wind_speed_10m": 8}},
            ),
        )


if __name__ == "__main__":
    unittest.main()
