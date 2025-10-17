"""
Weather Agent Tool - uses a mini Strands Agent with http_request + current_time
to fetch and format forecast data per the weather-focused system prompt.
"""

from typing import Any, Optional
from .base_tool import BaseTool
from strands import Agent
from strands_tools import http_request, current_time

WEATHER_SYSTEM_PROMPT = """You are a weather assistant with HTTP capabilities. You can:

1. Make HTTP requests to the National Weather Service API
2. Process and display weather forecast data
3. Provide weather information for locations in the United States

When retrieving weather information:
1. First get the coordinates or grid information using https://api.weather.gov/points/{latitude},{longitude} or https://api.weather.gov/points/{zipcode}
2. Then use the returned forecast URL to get the actual forecast

When displaying responses:
- Format weather data in a human-readable way
- Highlight important information like temperature, precipitation, and alerts
- Handle errors appropriately
- Convert technical terms to user-friendly language

Always explain the weather conditions clearly and provide context for the forecast.
"""

class WeatherAgentTool(BaseTool):
    """
    Delegates weather queries to a nested Strands Agent (http_request + current_time)
    with a weather-specific system prompt.

    Input:
        location: str  (ZIP "10001", lat/lon "40.71,-74.00", or a US place query)
    Output:
        str: human-readable weather summary produced by the inner Agent.
    """

    def __init__(self) -> None:
        # Lazy-initialized agent (created on first call); keeps BaseTool sync.
        self._agent: Optional[Agent] = None

    @property
    def name(self) -> str:
        # Distinct name so it doesn't clash with your dummy get_weather tool
        return "get_weather_agent"

    @property
    def description(self) -> str:
        return """Get U.S. weather by delegating to a weather-specialized Agent that can make HTTP requests to api.weather.gov and format user-friendly forecasts.
Args:
    location: ZIP (e.g., "10001"), "lat,lon" (e.g., "40.71,-74.00"), or a US place string.
Returns:
    A human-readable weather summary (temps, precip, wind, alerts).
"""

    def _ensure_agent(self) -> Agent:
        if self._agent is None:
            self._agent = Agent(
                tools=[http_request, current_time],
                system_prompt=WEATHER_SYSTEM_PROMPT
            )
        return self._agent

    def execute(self, location: str) -> str:
        if not isinstance(location, str) or not location.strip():
            raise ValueError("Parameter 'location' must be a non-empty string.")
        location = location.strip()

        try:
            agent = self._ensure_agent()
            # Call synchronously so we don't need async BaseTool
            result = agent(location)

            # Normalize result shapes
            if hasattr(result, "content") and result.content:
                return result.content
            if hasattr(result, "response") and result.response:
                return result.response
            return str(result)

        except Exception as e:
            return f"Sorry, I couldn't retrieve the weather right now. Details: {str(e)}"
