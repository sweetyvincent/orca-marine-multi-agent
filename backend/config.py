import os

# ERDDAP endpoints
ERDDAP_BASE = "https://coastwatch.pfeg.noaa.gov/erddap/griddap"
OISST_DATASET = "ncdcOisst21Agg_LonPM180"  # Use the -180/+180 longitude variant
CHL_DATASET_8DAY = "nesdisVHNnoaaSNPPnoaa20NRTchlaGapfilledDaily"  # Active VIIRS NRT gap-filled daily chlorophyll
CHL_DATASET_MONTHLY = "nesdisVHNnoaaSNPPnoaa20chlaGapfilledDaily"  # Science quality fallback

# HAB risk thresholds (from marine science literature)
CHL_ELEVATED_THRESHOLD = 4.0    # mg/m³
CHL_HIGH_THRESHOLD = 10.0       # mg/m³
SST_ANOMALY_WARM_THRESHOLD = 1.0  # °C
SST_ANOMALY_HOT_THRESHOLD = 2.0   # °C

# Data query parameters
BBOX_RADIUS_DEG = 1.0  # ±1° around target point

# LLM
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
