import asyncio
from typing import Dict, Union
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import logging

logger = logging.getLogger(__name__)

PRESET_LOCATIONS = {
    "chennai": {"lat": 13.0827, "lon": 80.2707},
    "mumbai": {"lat": 18.9220, "lon": 72.8347},
    "gulf of mexico": {"lat": 25.0, "lon": -90.0},
    "california coast": {"lat": 36.7783, "lon": -122.0},
    "chesapeake bay": {"lat": 37.5, "lon": -76.0},
    "florida keys": {"lat": 24.5551, "lon": -81.7800},
    "great barrier reef": {"lat": -18.2871, "lon": 147.6992},
    "north sea": {"lat": 56.0, "lon": 3.0}
}

async def resolve_location(name: str) -> Dict[str, Union[str, float]]:
    """
    Resolves a location name to its latitude and longitude.
    Checks presets first, then falls back to geopy.
    """
    name_lower = name.lower().strip()
    for preset_name, coords in PRESET_LOCATIONS.items():
        if preset_name in name_lower or name_lower in preset_name:
            return {
                "name": preset_name.title(),
                "lat": coords["lat"],
                "lon": coords["lon"],
                "source": "preset"
            }
    
    # Fallback to geopy
    geolocator = Nominatim(user_agent="orca_marine_system")
    
    loop = asyncio.get_running_loop()
    try:
        location = await loop.run_in_executor(None, geolocator.geocode, name)
        if location:
            return {
                "name": location.address,
                "lat": location.latitude,
                "lon": location.longitude,
                "source": "geocoder"
            }
        else:
            raise ValueError(f"Could not resolve location: '{name}'. Try a major coastal city or body of water.")
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        logger.error(f"Geocoding service error for {name}: {str(e)}")
        raise ValueError(f"Geocoding service unavailable for '{name}'. Please use a preset location.")
