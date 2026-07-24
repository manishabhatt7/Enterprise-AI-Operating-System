from __future__ import annotations

import httpx


class OpenMeteoClient:

    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

    async def get_weather(
        self,
        city: str,
    ) -> dict:

        async with httpx.AsyncClient(timeout=10) as client:

            geo = await client.get(
                self.GEOCODING_URL,
                params={
                    "name": city,
                    "count": 1,
                },
            )

            geo.raise_for_status()

            results = geo.json().get("results")

            if not results:
                raise ValueError(
                    f"City '{city}' not found."
                )

            location = results[0]

            weather = await client.get(
                self.WEATHER_URL,
                params={
                    "latitude": location["latitude"],
                    "longitude": location["longitude"],
                    "current": [
                        "temperature_2m",
                        "wind_speed_10m",
                        "weather_code",
                    ],
                },
            )

            weather.raise_for_status()

            current = weather.json()["current"]

            return {
                "city": location["name"],
                "country": location.get("country"),
                "temperature": current["temperature_2m"],
                "wind_speed": current["wind_speed_10m"],
                "weather_code": current["weather_code"],
            }


open_meteo_client = OpenMeteoClient()