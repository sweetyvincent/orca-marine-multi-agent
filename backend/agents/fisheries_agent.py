import logging
from typing import Dict, Union, Optional

from config import (
    CHL_ELEVATED_THRESHOLD,
    CHL_HIGH_THRESHOLD,
    SST_ANOMALY_WARM_THRESHOLD,
    SST_ANOMALY_HOT_THRESHOLD
)

logger = logging.getLogger(__name__)

async def run_fisheries_agent(
    lat: float, 
    lon: float, 
    location_name: str, 
    sst_result: Optional[Dict] = None, 
    chl_result: Optional[Dict] = None
) -> Dict[str, Union[str, dict, list]]:
    """
    Evaluates HAB (Harmful Algal Bloom) risk based on SST and Chlorophyll data.
    """
    risk_level = "low"
    advisory = "Conditions appear normal. Standard fishing and monitoring practices recommended."
    factors = []
    
    chl_mean = None
    sst_anom = None

    if chl_result and "error" not in chl_result:
        chl_mean = chl_result.get("mean_chl_mg_m3")
    
    if sst_result and "error" not in sst_result:
        sst_anom = sst_result.get("anomaly_c")
        
    # Apply heuristics
    if chl_mean is not None and sst_anom is not None:
        if chl_mean > CHL_HIGH_THRESHOLD:
            risk_level = "high"
            factors.append(f"Chlorophyll extremely high ({chl_mean} mg/m³ > {CHL_HIGH_THRESHOLD})")
            advisory = "High risk of algal blooms (potential HAB). Immediate water quality testing advised. Limit aquaculture harvesting until cleared."
        elif chl_mean > CHL_ELEVATED_THRESHOLD and sst_anom > SST_ANOMALY_WARM_THRESHOLD:
            risk_level = "elevated"
            factors.append(f"Elevated chlorophyll ({chl_mean} mg/m³) combined with warm anomalies (+{sst_anom} °C)")
            advisory = "Elevated risk of blooms. Anomalous warming and high nutrients detected. Increase monitoring frequency."
        elif chl_mean > CHL_ELEVATED_THRESHOLD:
            risk_level = "moderate"
            factors.append(f"Elevated chlorophyll ({chl_mean} mg/m³ > {CHL_ELEVATED_THRESHOLD})")
            advisory = "Moderate risk. Plankton concentrations are elevated. Monitor for localized blooms."
        elif sst_anom > SST_ANOMALY_HOT_THRESHOLD:
            risk_level = "moderate"
            factors.append(f"High surface temperature anomaly (+{sst_anom} °C > {SST_ANOMALY_HOT_THRESHOLD})")
            advisory = "Moderate risk due to marine heatwave conditions, which can trigger rapid bloom development if nutrients become available."
        else:
            factors.append("SST and Chlorophyll within normal baseline levels.")
            
    elif chl_mean is not None:
        if chl_mean > CHL_HIGH_THRESHOLD:
            risk_level = "high"
            factors.append(f"Chlorophyll extremely high ({chl_mean} mg/m³ > {CHL_HIGH_THRESHOLD})")
            advisory = "High risk of algal blooms. SST data unavailable, but high biomass indicates action needed."
        elif chl_mean > CHL_ELEVATED_THRESHOLD:
            risk_level = "moderate"
            factors.append(f"Elevated chlorophyll ({chl_mean} mg/m³ > {CHL_ELEVATED_THRESHOLD})")
            advisory = "Moderate risk based on chlorophyll levels. SST data unavailable."
    
    elif sst_anom is not None:
         if sst_anom > SST_ANOMALY_HOT_THRESHOLD:
            risk_level = "moderate"
            factors.append(f"High surface temperature anomaly (+{sst_anom} °C > {SST_ANOMALY_HOT_THRESHOLD})")
            advisory = "Moderate risk due to marine heatwave conditions. Chlorophyll data unavailable."
            
    else:
        advisory = "Unable to assess risk due to missing environmental data."
        risk_level = "unknown"
        factors.append("No valid SST or Chlorophyll data provided.")

    return {
        "agent": "fisheries",
        "location": {"lat": lat, "lon": lon, "name": location_name},
        "risk_level": risk_level,
        "advisory": advisory,
        "factors": factors,
        "data_source": "Rule-based heuristic (ORCA v1)",
        "confidence_note": "This is a simplified rule-based assessment, not a forecast model. Consult local authorities for official advisories."
    }
