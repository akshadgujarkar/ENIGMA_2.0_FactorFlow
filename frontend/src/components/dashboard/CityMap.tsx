import { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useCityStore } from '@/stores/cityStore';
import {
  MAP_CENTER,
  MAP_ZOOM,
  landUseData,
  greenCoverData,
  newGreenData,
  heatIslandData,
  floodZoneData,
  LAND_USE_COLORS,
} from '@/data/mockGeoData';

const BASEMAP_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';

export function CityMap() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const {
    layers,
    scenarioApplied,
    greenCoverIncrease,
    floodSeverity,
  } = useCityStore();

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: BASEMAP_STYLE,
      center: MAP_CENTER,
      zoom: MAP_ZOOM,
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

      // Land Use
      map.addSource('land-use', { type: 'geojson', data: landUseData });
      map.addLayer({
        id: 'land-use-fill',
        type: 'fill',
        source: 'land-use',
        paint: {
          'fill-color': [
            'match',
            ['get', 'type'],
            'residential', LAND_USE_COLORS.residential,
            'commercial', LAND_USE_COLORS.commercial,
            'industrial', LAND_USE_COLORS.industrial,
            'mixed', LAND_USE_COLORS.mixed,
            '#888',
          ],
          'fill-opacity': 0.25,
        },
      });
      map.addLayer({
        id: 'land-use-outline',
        type: 'line',
        source: 'land-use',
        paint: {
          'line-color': [
            'match',
            ['get', 'type'],
            'residential', LAND_USE_COLORS.residential,
            'commercial', LAND_USE_COLORS.commercial,
            'industrial', LAND_USE_COLORS.industrial,
            'mixed', LAND_USE_COLORS.mixed,
            '#888',
          ],
          'line-width': 1.5,
          'line-opacity': 0.6,
        },
      });

      // Green Cover
      map.addSource('green-cover', { type: 'geojson', data: greenCoverData });
      map.addLayer({
        id: 'green-cover-fill',
        type: 'fill',
        source: 'green-cover',
        paint: {
          'fill-color': '#22c55e',
          'fill-opacity': 0.35,
        },
      });

      // New Green (scenario)
      map.addSource('new-green', { type: 'geojson', data: newGreenData });
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

      // Heat Islands
      map.addSource('heat-islands', { type: 'geojson', data: heatIslandData });
      map.addLayer({
        id: 'heat-islands-fill',
        type: 'fill',
        source: 'heat-islands',
        paint: {
          'fill-color': '#f97316',
          'fill-opacity': 0.3,
        },
      });

      // Flood Zones
      map.addSource('flood-zones', { type: 'geojson', data: floodZoneData });
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

      // Popups on click
      const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: true });

      ['land-use-fill', 'green-cover-fill', 'heat-islands-fill', 'flood-zones-fill'].forEach(
        (layerId) => {
          map.on('click', layerId, (e) => {
            const props = e.features?.[0]?.properties;
            if (!props) return;
            const name = props.name || props.type || 'Unknown';
            popup
              .setLngLat(e.lngLat)
              .setHTML(
                `<div style="color:#e2e8f0;font-size:12px;font-weight:600;">${name}</div>`
              )
              .addTo(map);
          });
          map.on('mouseenter', layerId, () => {
            map.getCanvas().style.cursor = 'pointer';
          });
          map.on('mouseleave', layerId, () => {
            map.getCanvas().style.cursor = '';
          });
        }
      );
    });

    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

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

    const greenOpacity = scenarioApplied ? Math.min(greenCoverIncrease / 30, 1) * 0.4 : 0;
    const heatReduction = scenarioApplied ? greenCoverIncrease * 0.01 : 0;
    const floodBoost = scenarioApplied
      ? { none: 0, mild: 0.1, moderate: 0.2, extreme: 0.4 }[floodSeverity]
      : 0;

    if (map.getLayer('new-green-fill')) {
      map.setPaintProperty('new-green-fill', 'fill-opacity', greenOpacity);
    }
    if (map.getLayer('new-green-outline')) {
      map.setPaintProperty('new-green-outline', 'line-opacity', greenOpacity > 0 ? 0.7 : 0);
    }
    if (map.getLayer('heat-islands-fill')) {
      map.setPaintProperty('heat-islands-fill', 'fill-opacity', Math.max(0.05, 0.3 - heatReduction));
    }
    if (map.getLayer('flood-zones-fill')) {
      map.setPaintProperty('flood-zones-fill', 'fill-opacity', 0.25 + floodBoost);
    }
    if (map.getLayer('flood-zones-outline')) {
      map.setPaintProperty('flood-zones-outline', 'line-opacity', 0.5 + floodBoost);
    }
  }, [scenarioApplied, greenCoverIncrease, floodSeverity]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="absolute inset-0" />
      {/* Map overlay title */}
      <div className="absolute top-4 left-4 glass-panel px-3 py-2 pointer-events-none">
        <span className="text-xs font-medium text-foreground mono">
          Barcelona · Eixample District
        </span>
      </div>
    </div>
  );
}
