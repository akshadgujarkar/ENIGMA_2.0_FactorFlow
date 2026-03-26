from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import ee
from flask import current_app

from ..routes.cities import SUPPORTED_CITIES
from .cache import cache_json


class UnknownCityError(ValueError):
  pass


def _is_ee_initialized() -> bool:
  """Check if Earth Engine is properly initialized and authorized."""
  try:
    return ee.data.is_initialized()
  except Exception:
    return False


def _get_mock_indices(city_id: str) -> dict[str, Any]:
  """Return mock data for development when Earth Engine is unavailable."""
  return {
    "city": city_id,
    "dataSource": "mock",
    "ndvi_mean": 0.35,
    "ndbi_mean": 0.15,
    "lst_mean_c": 28.5,
    "flood_index_mean": -0.2,
    "metrics": {
      "greenCover": 67.5,
      "builtUp": 57.5,
      "heatStress": 38.5,
      "floodRisk": 30.0,
    },
  }


def _get_mock_timeseries(city_id: str, start: str, end: str) -> dict[str, Any]:
  """Return mock timeseries data for development when Earth Engine is unavailable."""
  return {
    "city": city_id,
    "dataSource": "mock",
    "series": [
      {
        "date": "2026-01",
        "ndvi_mean": 0.30,
        "lst_mean_c": 26.0,
        "flood_index_mean": -0.25,
      },
      {
        "date": "2026-02",
        "ndvi_mean": 0.35,
        "lst_mean_c": 28.5,
        "flood_index_mean": -0.20,
      },
    ],
  }


@dataclass
class CityExtent:
  id: str
  lon: float
  lat: float
  zoom: float

  @property
  def point(self) -> ee.Geometry:
    return ee.Geometry.Point([self.lon, self.lat])


def _get_city_extent(city_id: str) -> CityExtent:
  for c in SUPPORTED_CITIES:
    if c["id"] == city_id:
      return CityExtent(
        id=c["id"],
        lon=float(c["center"][0]),
        lat=float(c["center"][1]),
        zoom=float(c["zoom"]),
      )
  raise UnknownCityError(city_id)


def _sentinel2_collection(geometry: ee.Geometry, start: str, end: str) -> ee.ImageCollection:
  return (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(geometry)
    .filterDate(start, end)
    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
  )


def _landsat_collection(geometry: ee.Geometry, start: str, end: str) -> ee.ImageCollection:
  return (
    ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
    .merge(ee.ImageCollection("LANDSAT/LC09/C02/T1_L2"))
    .filterBounds(geometry)
    .filterDate(start, end)
  )


def _sentinel1_collection(geometry: ee.Geometry, start: str, end: str) -> ee.ImageCollection:
  return (
    ee.ImageCollection("COPERNICUS/S1_GRD")
    .filterBounds(geometry)
    .filterDate(start, end)
    .filter(ee.Filter.eq("instrumentMode", "IW"))
    .filter(ee.Filter.eq("resolution_meters", 10))
    .filter(ee.Filter.eq("orbitProperties_pass", "DESCENDING"))
  )


def _compute_ndvi(image: ee.Image) -> ee.Image:
  return image.normalizedDifference(["B8", "B4"]).rename("NDVI")


def _compute_ndbi(image: ee.Image) -> ee.Image:
  return image.normalizedDifference(["B11", "B8"]).rename("NDBI")


def _compute_ndwi(image: ee.Image) -> ee.Image:
  return image.normalizedDifference(["B3", "B8"]).rename("NDWI")


def _compute_lst_landsat(image: ee.Image) -> ee.Image:
  """Simplified Land Surface Temperature estimate from Landsat 8/9.

  This is a placeholder split-window style approximation intended to be
  scientifically reasonable but lightweight.
  """
  toa = image.select("ST_B10").multiply(0.00341802).add(149.0)  # to Kelvin
  lst_celsius = toa.subtract(273.15).rename("LST")
  return lst_celsius


@cache_json(ttl_seconds=3600)
def get_city_realtime_indices(city_id: str) -> dict[str, Any]:
  """Compute current NDVI, LST, flood risk, built-up % for a city.

  Results are cached in Redis to avoid repeated heavy GEE calls.
  Falls back to mock data if Earth Engine is not available in development.
  """
  # Check if Earth Engine is available and initialized
  if not _is_ee_initialized():
    app = current_app
    if app.config.get("ENV") == "development":
      print(f"⚠️  WARNING: Using mock data for {city_id} (Earth Engine unavailable)")
      return _get_mock_indices(city_id)
    raise RuntimeError(
      f"Earth Engine is not initialized for city {city_id}. "
      "Configure GEE_PROJECT and authentication in environment."
    )

  try:
    extent = _get_city_extent(city_id)
    geom = extent.point.buffer(10_000)  # 10 km radius

    today = datetime.utcnow().date()
    start = today.replace(day=1).isoformat()
    end = today.isoformat()

    s2 = _sentinel2_collection(geom, start, end).median()
    ndvi = _compute_ndvi(s2)
    ndbi = _compute_ndbi(s2)
    ndwi = _compute_ndwi(s2)

    l8 = _landsat_collection(geom, start, end).median()
    lst = _compute_lst_landsat(l8)

    s1 = _sentinel1_collection(geom, start, end).median()
    vv = s1.select("VV")
    vh = s1.select("VH")
    flood_index = vh.subtract(vv).rename("FLOOD")

    scale = 1000  # meters
    ndvi_stats = ndvi.reduceRegion(
      reducer=ee.Reducer.mean(),
      geometry=geom,
      scale=scale,
      maxPixels=1_000_000,
    )
    ndbi_stats = ndbi.reduceRegion(
      reducer=ee.Reducer.mean(),
      geometry=geom,
      scale=scale,
      maxPixels=1_000_000,
    )
    lst_stats = lst.reduceRegion(
      reducer=ee.Reducer.mean(),
      geometry=geom,
      scale=scale,
      maxPixels=1_000_000,
    )
    flood_stats = flood_index.reduceRegion(
      reducer=ee.Reducer.mean(),
      geometry=geom,
      scale=scale,
      maxPixels=1_000_000,
    )

    ndvi_mean = float(ndvi_stats.get("NDVI").getInfo() or 0)
    ndbi_mean = float(ndbi_stats.get("NDBI").getInfo() or 0)
    lst_mean = float(lst_stats.get("LST").getInfo() or 0)
    flood_mean = float(flood_stats.get("FLOOD").getInfo() or 0)

    # Simple heuristic mappings (0–100) for the dashboard
    green_cover = max(0, min(100, (ndvi_mean + 1) * 50))
    built_up = max(0, min(100, (ndbi_mean + 1) * 50))
    heat_stress = max(0, min(100, (lst_mean + 10)))  # relative scale
    flood_risk = max(0, min(100, (flood_mean + 5) * 10))

    return {
      "city": city_id,
      "dataSource": "google-earth-engine",
      "ndvi_mean": ndvi_mean,
      "ndbi_mean": ndbi_mean,
      "lst_mean_c": lst_mean,
      "flood_index_mean": flood_mean,
      "metrics": {
        "greenCover": round(green_cover, 1),
        "builtUp": round(built_up, 1),
        "heatStress": round(heat_stress, 1),
        "floodRisk": round(flood_risk, 1),
      },
    }
  except ee.ee_exception.EEException as e:
    app = current_app
    if app.config.get("ENV") == "development":
      print(f"⚠️  WARNING: Earth Engine error for {city_id}: {e}")
      print("   Falling back to mock data.")
      return _get_mock_indices(city_id)
    raise
  ndvi_stats = ndvi.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=geom,
    scale=scale,
    maxPixels=1_000_000,
  )
  ndbi_stats = ndbi.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=geom,
    scale=scale,
    maxPixels=1_000_000,
  )
  lst_stats = lst.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=geom,
    scale=scale,
    maxPixels=1_000_000,
  )
  flood_stats = flood_index.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=geom,
    scale=scale,
    maxPixels=1_000_000,
  )

  ndvi_mean = float(ndvi_stats.get("NDVI").getInfo() or 0)
  ndbi_mean = float(ndbi_stats.get("NDBI").getInfo() or 0)
  lst_mean = float(lst_stats.get("LST").getInfo() or 0)
  flood_mean = float(flood_stats.get("FLOOD").getInfo() or 0)

  # Simple heuristic mappings (0–100) for the dashboard
  green_cover = max(0, min(100, (ndvi_mean + 1) * 50))
  built_up = max(0, min(100, (ndbi_mean + 1) * 50))
  heat_stress = max(0, min(100, (lst_mean + 10)))  # relative scale
  flood_risk = max(0, min(100, (flood_mean + 5) * 10))

  return {
    "city": city_id,
    "dataSource": "google-earth-engine",
    "ndvi_mean": ndvi_mean,
    "ndbi_mean": ndbi_mean,
    "lst_mean_c": lst_mean,
    "flood_index_mean": flood_mean,
    "metrics": {
      "greenCover": round(green_cover, 1),
      "builtUp": round(built_up, 1),
      "heatStress": round(heat_stress, 1),
      "floodRisk": round(flood_risk, 1),
    },
  }


@cache_json(ttl_seconds=6 * 3600)
def get_city_timeseries(city_id: str, start: str, end: str) -> dict[str, Any]:
  """Return monthly NDVI, LST, and flood risk timeseries between dates.
  
  Falls back to mock data if Earth Engine is not available in development.
  """
  # Check if Earth Engine is available and initialized
  if not _is_ee_initialized():
    app = current_app
    if app.config.get("ENV") == "development":
      print(f"⚠️  WARNING: Using mock timeseries for {city_id} (Earth Engine unavailable)")
      return _get_mock_timeseries(city_id, start, end)
    raise RuntimeError(
      f"Earth Engine is not initialized for city {city_id}. "
      "Configure GEE_PROJECT and authentication in environment."
    )

  try:
    extent = _get_city_extent(city_id)
    geom = extent.point.buffer(10_000)

    start_date = ee.Date(start)
    end_date = ee.Date(end)

    def _month_seq(s: ee.Date, e: ee.Date):
      months = ee.List.sequence(0, e.difference(s, "month").subtract(1))
      def _map_month(m):
        m = ee.Number(m)
        month_start = s.advance(m, "month")
        month_end = month_start.advance(1, "month")

        s2 = _sentinel2_collection(geom, month_start.format("YYYY-MM-dd"), month_end.format("YYYY-MM-dd")).median()
        ndvi = _compute_ndvi(s2)
        ndbi = _compute_ndbi(s2)

        l8 = _landsat_collection(geom, month_start.format("YYYY-MM-dd"), month_end.format("YYYY-MM-dd")).median()
        lst = _compute_lst_landsat(l8)

        s1 = _sentinel1_collection(geom, month_start.format("YYYY-MM-dd"), month_end.format("YYYY-MM-dd")).median()
        flood_index = s1.select("VH").subtract(s1.select("VV")).rename("FLOOD")

        scale = 1000
        ndvi_mean = ee.Number(
          ndvi.reduceRegion(ee.Reducer.mean(), geom, scale, 1_000_000).get("NDVI")
        )
        lst_mean = ee.Number(
          lst.reduceRegion(ee.Reducer.mean(), geom, scale, 1_000_000).get("LST")
        )
        flood_mean = ee.Number(
          flood_index.reduceRegion(ee.Reducer.mean(), geom, scale, 1_000_000).get("FLOOD")
        )

        return ee.Dictionary(
          {
            "date": month_start.format("YYYY-MM"),
            "ndvi_mean": ndvi_mean,
            "lst_mean_c": lst_mean,
            "flood_index_mean": flood_mean,
          }
        )

      return months.map(_map_month)

    series = _month_seq(start_date, end_date)
    records = series.getInfo()
    return {"city": city_id, "dataSource": "google-earth-engine", "series": records}
  except ee.ee_exception.EEException as e:
    app = current_app
    if app.config.get("ENV") == "development":
      print(f"⚠️  WARNING: Earth Engine error for {city_id} timeseries: {e}")
      print("   Falling back to mock data.")
      return _get_mock_timeseries(city_id, start, end)
    raise

