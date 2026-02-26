import { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl/dist/maplibre-gl-csp';
import 'maplibre-gl/dist/maplibre-gl.css';

import { useCityStore } from '@/stores/cityStore';

const BASEMAP_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';

// Use the explicit CSP worker bundle to avoid runtime helper issues in dev pre-bundling.
maplibregl.setWorkerUrl(
  new URL('maplibre-gl/dist/maplibre-gl-csp-worker.js', import.meta.url).toString()
);

/** Compute centroid of a polygon's first ring */
function polygonCentroid(coords: number[][]): [number, number] {
  const len = coords.length;
  const sum = coords.reduce((acc, c) => [acc[0] + c[0], acc[1] + c[1]], [0, 0]);
  return [sum[0] / len, sum[1] / len];
}

/** Build a pulsing marker DOM element */
function createPulseMarker(color: string, label: string): HTMLDivElement {
  const el = document.createElement('div');
  el.className = 'danger-marker-wrapper';
  el.innerHTML = `
    <div class="danger-pulse-ring" style="border-color:${color};box-shadow:0 0 12px ${color}"></div>
    <div class="danger-pulse-ring danger-pulse-ring-delayed" style="border-color:${color};box-shadow:0 0 8px ${color}"></div>
    <div class="danger-core" style="background:${color};box-shadow:0 0 10px ${color}"></div>
    <div class="danger-label" style="color:${color}">${label}</div>
  `;
  return el;
}

export function CityMap() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);
  const {
    cities,
    currentCityId,
    layers,
    scenarioApplied,
    greenCoverIncrease,
    floodSeverity,
    hotspots,
  } = useCityStore();

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || mapRef.current || !currentCityId) return;

    const city = cities.find((c) => c.id === currentCityId);
    const center = city?.center ?? [0, 0];
    const zoom = city?.zoom ?? 11;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: BASEMAP_STYLE,
      center,
      zoom,
      pitch: 50,
      bearing: -15,
      // @ts-expect-error antialias is valid but not in type defs
      antialias: true,
    });

    map.addControl(new maplibregl.NavigationControl(), 'top-right');

    map.on('load', () => {
      // 3D Buildings from vector tiles
      const style = map.getStyle();
      const vectorSource = Object.keys(style.sources).find(
        (key) => (style.sources[key] as any).type === 'vector'
      );

      if (vectorSource) {
        map.addLayer({
          id: 'buildings-3d',
          source: vectorSource,
          'source-layer': 'building',
          type: 'fill-extrusion',
          minzoom: 13,
          paint: {
            'fill-extrusion-color': 'hsl(220, 20%, 14%)',
            'fill-extrusion-height': [
              'coalesce',
              ['get', 'render_height'],
              12,
            ],
            'fill-extrusion-base': ['coalesce', ['get', 'render_min_height'], 0],
            'fill-extrusion-opacity': 0.65,
          },
        });
      }

      // Thematic layers: these are now styled overlays that will be driven by
      // backend-provided tiles or vector data. For now we keep them as empty
      // sources whose visibility and styling are still controlled by the UI.

      map.addSource('green-cover', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
      map.addLayer({
        id: 'green-cover-fill',
        type: 'fill',
        source: 'green-cover',
        paint: {
          'fill-color': '#22c55e',
          'fill-opacity': 0.35,
        },
      });

      map.addSource('new-green', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
      map.addLayer({
        id: 'new-green-fill',
        type: 'fill',
        source: 'new-green',
        paint: {
          'fill-color': '#4ade80',
          'fill-opacity': 0,
        },
      });
      map.addLayer({
        id: 'new-green-outline',
        type: 'line',
        source: 'new-green',
        paint: {
          'line-color': '#4ade80',
          'line-dasharray': [3, 2],
          'line-width': 1.5,
          'line-opacity': 0,
        },
      });

      map.addSource('heat-islands', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
      map.addLayer({
        id: 'heat-islands-fill',
        type: 'fill',
        source: 'heat-islands',
        paint: {
          'fill-color': '#f97316',
          'fill-opacity': 0.3,
        },
      });

      map.addSource('flood-zones', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
      map.addLayer({
        id: 'flood-zones-fill',
        type: 'fill',
        source: 'flood-zones',
        paint: {
          'fill-color': '#06b6d4',
          'fill-opacity': 0.25,
        },
      });
      map.addLayer({
        id: 'flood-zones-outline',
        type: 'line',
        source: 'flood-zones',
        paint: {
          'line-color': '#06b6d4',
          'line-width': 2,
          'line-opacity': 0.5,
        },
      });
    });

    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [cities, currentCityId]);

  // Update layer visibility
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    const setVis = (id: string, visible: boolean) => {
      if (map.getLayer(id)) {
        map.setLayoutProperty(id, 'visibility', visible ? 'visible' : 'none');
      }
    };

    setVis('buildings-3d', layers.buildings);
    setVis('land-use-fill', layers.landUse);
    setVis('land-use-outline', layers.landUse);
    setVis('green-cover-fill', layers.greenCover);
    setVis('new-green-fill', layers.greenCover);
    setVis('new-green-outline', layers.greenCover);
    setVis('heat-islands-fill', layers.heatIslands);
    setVis('flood-zones-fill', layers.floodZones);
    setVis('flood-zones-outline', layers.floodZones);
  }, [layers]);

  // Update scenario visual effects
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    const greenOpacity = scenarioApplied ? Math.min(greenCoverIncrease / 30, 1) * 0.55 : 0;
    const heatReduction = scenarioApplied ? greenCoverIncrease * 0.012 : 0;
    const floodBoost = scenarioApplied
      ? { none: 0, mild: 0.15, moderate: 0.35, extreme: 0.55 }[floodSeverity]
      : 0;

    // New green areas — bright, high contrast
    if (map.getLayer('new-green-fill')) {
      map.setPaintProperty('new-green-fill', 'fill-color', scenarioApplied ? '#22ff66' : '#4ade80');
      map.setPaintProperty('new-green-fill', 'fill-opacity', greenOpacity);
    }
    if (map.getLayer('new-green-outline')) {
      map.setPaintProperty('new-green-outline', 'line-color', scenarioApplied ? '#22ff66' : '#4ade80');
      map.setPaintProperty('new-green-outline', 'line-width', scenarioApplied ? 3 : 1.5);
      map.setPaintProperty('new-green-outline', 'line-opacity', greenOpacity > 0 ? 0.9 : 0);
    }

    // Heat islands — intensify remaining or dim with greening
    if (map.getLayer('heat-islands-fill')) {
      const heatOpacity = Math.max(0.05, 0.3 - heatReduction);
      map.setPaintProperty('heat-islands-fill', 'fill-color', scenarioApplied && heatReduction < 0.1 ? '#ff4500' : '#f97316');
      map.setPaintProperty('heat-islands-fill', 'fill-opacity', heatOpacity);
    }

    // Flood zones — dramatic danger highlighting
    const floodColor = scenarioApplied && floodBoost > 0.2 ? '#ff2d55' : '#06b6d4';
    const floodOutlineColor = scenarioApplied && floodBoost > 0.2 ? '#ff6b8a' : '#06b6d4';
    if (map.getLayer('flood-zones-fill')) {
      map.setPaintProperty('flood-zones-fill', 'fill-color', floodColor);
      map.setPaintProperty('flood-zones-fill', 'fill-opacity', Math.min(0.7, 0.25 + floodBoost));
    }
    if (map.getLayer('flood-zones-outline')) {
      map.setPaintProperty('flood-zones-outline', 'line-color', floodOutlineColor);
      map.setPaintProperty('flood-zones-outline', 'line-width', scenarioApplied ? 4 : 2);
      map.setPaintProperty('flood-zones-outline', 'line-opacity', Math.min(1, 0.5 + floodBoost));
    }
  }, [scenarioApplied, greenCoverIncrease, floodSeverity]);

  // Pulsing danger markers based on backend-provided hotspots
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // Remove existing markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    if (!scenarioApplied || hotspots.length === 0) return;

    hotspots.forEach((spot) => {
      const color = spot.type === 'flood' ? '#ff2d55' : '#ff7f11';
      const marker = new maplibregl.Marker({
        element: createPulseMarker(color, spot.label),
      })
        .setLngLat([spot.lng, spot.lat])
        .addTo(map);
      markersRef.current.push(marker);
    });

    return () => {
      markersRef.current.forEach((m) => m.remove());
      markersRef.current = [];
    };
  }, [scenarioApplied, hotspots]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="absolute inset-0" />
      {/* Map overlay title */}
      <div className="absolute top-4 left-4 glass-panel px-3 py-2 pointer-events-none">
        <span className="text-xs font-medium text-foreground mono">
          {currentCityId
            ? cities.find((c) => c.id === currentCityId)?.name
            : 'Select a city'}
        </span>
      </div>
      {/* Scenario active banner */}
      {scenarioApplied && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 glass-panel px-4 py-2 flex items-center gap-2 animate-fade-in border-destructive/50">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-destructive opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-destructive" />
          </span>
          <span className="text-xs font-semibold text-destructive mono uppercase tracking-wider">
            Scenario Active — Danger zones highlighted
          </span>
        </div>
      )}
    </div>
  );
}
