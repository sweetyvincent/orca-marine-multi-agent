import io
import httpx
import numpy as np
import xarray as xr
import logging
from typing import Dict, Union

from config import ERDDAP_BASE, CHL_DATASET_8DAY, BBOX_RADIUS_DEG

logger = logging.getLogger(__name__)

async def run_chlorophyll_agent(lat: float, lon: float, location_name: str) -> Dict[str, Union[str, float, dict]]:
    """
    Fetches Chlorophyll-a data for a given location using ERDDAP.
    Uses NOAA CoastWatch VIIRS DINEOF Gap-filled near real-time global dataset.
    """
    lat_min = round(lat - BBOX_RADIUS_DEG, 4)
    lat_max = round(lat + BBOX_RADIUS_DEG, 4)
    lon_min = round(lon - BBOX_RADIUS_DEG, 4)
    lon_max = round(lon + BBOX_RADIUS_DEG, 4)

    # Note: nesdisVHNnoaaSNPPnoaa20NRTchlaGapfilledDaily dimensions:
    # [time][altitude][latitude][longitude]
    # variable: chlor_a
    url = (
        f"{ERDDAP_BASE}/{CHL_DATASET_8DAY}.nc?"
        f"chlor_a[(last)][(0.0):1:(0.0)][({lat_min}):1:({lat_max})][({lon_min}):1:({lon_max})]"
    )
    
    logger.info(f"Chlorophyll Agent querying URL: {url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            # Load into xarray
            ds = xr.open_dataset(io.BytesIO(response.content))
            
            # Squeeze altitude if present
            if 'altitude' in ds.dims:
                ds = ds.squeeze('altitude')
            
            # Get latest time slice
            latest_ds = ds.isel(time=-1)
            var_name = 'chlor_a' if 'chlor_a' in latest_ds else 'chlorophyll'
            chl_values = latest_ds[var_name].values
            
            # Mask out NaNs
            valid_chl = chl_values[~np.isnan(chl_values)]

            if len(valid_chl) == 0:
                raise ValueError("No valid chlorophyll data found in bounding box (might be over land).")

            mean_chl = float(np.nanmean(valid_chl))
            max_chl = float(np.nanmax(valid_chl))
            obs_date = str(latest_ds.time.values)
            
            # Classification
            if mean_chl < 1.0:
                classification = "oligotrophic"
            elif mean_chl <= 4.0:
                classification = "normal"
            elif mean_chl <= 10.0:
                classification = "elevated"
            else:
                classification = "bloom"
                
            return {
                "agent": "chlorophyll",
                "location": {"lat": lat, "lon": lon, "name": location_name},
                "mean_chl_mg_m3": round(mean_chl, 2),
                "max_chl_mg_m3": round(max_chl, 2),
                "classification": classification,
                "observation_date": obs_date,
                "data_source": "NOAA CoastWatch VIIRS DINEOF Gap-filled Daily",
                "confidence_note": f"Based on {len(valid_chl)} valid pixels in bounding box."
            }
            
    except Exception as e:
        logger.error(f"Chlorophyll Agent error: {str(e)}")
        return {
            "agent": "chlorophyll",
            "location": {"lat": lat, "lon": lon, "name": location_name},
            "error": f"Failed to retrieve or process Chlorophyll data: {str(e)}"
        }
