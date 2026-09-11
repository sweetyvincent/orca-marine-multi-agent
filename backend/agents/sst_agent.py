import io
import httpx
import xarray as xr
import numpy as np
from scipy import stats
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Union

from config import ERDDAP_BASE, OISST_DATASET, BBOX_RADIUS_DEG

logger = logging.getLogger(__name__)

async def run_sst_agent(lat: float, lon: float, location_name: str) -> Dict[str, Union[str, float, dict]]:
    """
    Fetches SST and anomaly data for a given location using ERDDAP.
    Calculates current SST, anomaly, and 7-day trend.
    """
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=30)
    
    start_str = start_time.strftime('%Y-%m-%dT12:00:00Z')
    end_str = "last"
    
    lat_min = lat - BBOX_RADIUS_DEG
    lat_max = lat + BBOX_RADIUS_DEG
    lon_min = lon - BBOX_RADIUS_DEG
    lon_max = lon + BBOX_RADIUS_DEG

    url = (
        f"{ERDDAP_BASE}/{OISST_DATASET}.nc?"
        f"sst[({start_str}):1:({end_str})][(0.0):1:(0.0)][({lat_min}):1:({lat_max})][({lon_min}):1:({lon_max})],"
        f"anom[({start_str}):1:({end_str})][(0.0):1:(0.0)][({lat_min}):1:({lat_max})][({lon_min}):1:({lon_max})]"
    )
    
    logger.info(f"SST Agent querying URL: {url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            # Load into xarray
            ds = xr.open_dataset(io.BytesIO(response.content))
            
            # Squeeze zlev dimension
            if 'zlev' in ds.dims:
                ds = ds.squeeze('zlev')

            # Get nearest cell to target point
            # Note: OISST uses -180 to 180 for this variant, so no conversion needed for lon
            nearest = ds.sel(latitude=lat, longitude=lon, method="nearest")
            
            # Extract current data
            current_data = nearest.isel(time=-1)
            current_sst = float(current_data.sst.values)
            current_anom = float(current_data.anom.values)
            obs_date = str(current_data.time.values)
            
            # Calculate 7-day trend
            recent_7d = nearest.isel(time=slice(-7, None))
            times = np.arange(len(recent_7d.time))
            sst_vals = recent_7d.sst.values
            
            # Handle potential NaNs
            valid_mask = ~np.isnan(sst_vals)
            if np.sum(valid_mask) > 2:
                slope, _, _, _, _ = stats.linregress(times[valid_mask], sst_vals[valid_mask])
                trend_7day = float(slope * 7) # scale to per week
            else:
                trend_7day = 0.0

            if trend_7day > 0.5:
                direction = "warming"
            elif trend_7day < -0.5:
                direction = "cooling"
            else:
                direction = "stable"
                
            return {
                "agent": "sst",
                "location": {"lat": lat, "lon": lon, "name": location_name},
                "current_sst_c": round(current_sst, 2),
                "anomaly_c": round(current_anom, 2),
                "trend_7day_c_per_week": round(trend_7day, 2),
                "trend_direction": direction,
                "observation_date": obs_date,
                "data_source": "NOAA OISST v2.1 (0.25° daily)",
                "confidence_note": "Data fetched successfully from ERDDAP nearest grid cell."
            }
            
    except Exception as e:
        logger.error(f"SST Agent error: {str(e)}")
        return {
            "agent": "sst",
            "location": {"lat": lat, "lon": lon, "name": location_name},
            "error": f"Failed to retrieve or process SST data: {str(e)}"
        }
