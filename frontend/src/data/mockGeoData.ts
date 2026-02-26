import type { FeatureCollection } from 'geojson';

// Centered on Barcelona's Eixample district
export const MAP_CENTER: [number, number] = [2.17, 41.389];
export const MAP_ZOOM = 14;

export const landUseData: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { type: 'residential', name: 'Eixample Residential' },
      geometry: {
        type: 'Polygon',
        coordinates: [[[2.155, 41.385], [2.175, 41.385], [2.175, 41.396], [2.155, 41.396], [2.155, 41.385]]],
      },
    },
    {
      type: 'Feature',
      properties: { type: 'commercial', name: 'Diagonal Commercial' },
      geometry: {
        type: 'Polygon',
        coordinates: [[[2.140, 41.393], [2.173, 41.393], [2.173, 41.399], [2.140, 41.399], [2.140, 41.393]]],
      },
    },
    {
      type: 'Feature',
      properties: { type: 'industrial', name: 'Zona Franca Industrial' },
      geometry: {
        type: 'Polygon',
        coordinates: [[[2.130, 41.350], [2.158, 41.350], [2.158, 41.364], [2.130, 41.364], [2.130, 41.350]]],
      },
    },
    {
      type: 'Feature',
      properties: { type: 'mixed', name: 'Gothic Quarter Mixed' },
      geometry: {
        type: 'Polygon',
        coordinates: [[[2.175, 41.378], [2.190, 41.378], [2.190, 41.387], [2.175, 41.387], [2.175, 41.378]]],
      },
    },
  ],
};

export const greenCoverData: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { name: 'Parc de la Ciutadella', intensity: 0.9 },
      geometry: {
        type: 'Polygon',
        coordinates: [[[2.183, 41.386], [2.192, 41.386], [2.192, 41.392], [2.183, 41.392], [2.183, 41.386]]],
      },
    },
    {
      type: 'Feature',
      properties: { name: 'Montjuïc Park', intensity: 0.85 },
      geometry: {
        type: 'Polygon',
        coordinates: [[[2.148, 41.358], [2.165, 41.358], [2.165, 41.370], [2.148, 41.370], [2.148, 41.358]]],
      },
    },
    {
      type: 'Feature',
      properties: { name: 'Jardins del Turó', intensity: 0.7 },
      geometry: {
        type: 'Polygon',
        coordinates: [[[2.147, 41.393], [2.153, 41.393], [2.153, 41.397], [2.147, 41.397], [2.147, 41.393]]],
      },
    },
  ],
};

export const newGreenData: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { name: 'New Green Corridor A', intensity: 0.6 },
      geometry: {
        type: 'Polygon',
        coordinates: [[[2.158, 41.388], [2.163, 41.388], [2.163, 41.392], [2.158, 41.392], [2.158, 41.388]]],
      },
    },
    {
      type: 'Feature',
      properties: { name: 'New Green Corridor B', intensity: 0.5 },
      geometry: {
        type: 'Polygon',
        coordinates: [[[2.170, 41.395], [2.176, 41.395], [2.176, 41.398], [2.170, 41.398], [2.170, 41.395]]],
      },
    },
    {
      type: 'Feature',
      properties: { name: 'New Green Pocket C', intensity: 0.4 },
      geometry: {
        type: 'Polygon',
        coordinates: [[[2.165, 41.383], [2.170, 41.383], [2.170, 41.386], [2.165, 41.386], [2.165, 41.383]]],
      },
    },
  ],
};

export const heatIslandData: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { name: 'Central Heat Zone', intensity: 0.85 },
      geometry: {
        type: 'Polygon',
        coordinates: [[[2.164, 41.383], [2.182, 41.383], [2.182, 41.393], [2.164, 41.393], [2.164, 41.383]]],
      },
    },
    {
      type: 'Feature',
      properties: { name: 'Industrial Heat Zone', intensity: 0.7 },
      geometry: {
        type: 'Polygon',
        coordinates: [[[2.135, 41.352], [2.155, 41.352], [2.155, 41.362], [2.135, 41.362], [2.135, 41.352]]],
      },
    },
  ],
};

export const floodZoneData: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { name: 'Barceloneta Coastal', risk: 'high', intensity: 0.7 },
      geometry: {
        type: 'Polygon',
        coordinates: [[[2.186, 41.375], [2.200, 41.375], [2.200, 41.384], [2.186, 41.384], [2.186, 41.375]]],
      },
    },
    {
      type: 'Feature',
      properties: { name: 'Besòs River Area', risk: 'medium', intensity: 0.5 },
      geometry: {
        type: 'Polygon',
        coordinates: [[[2.195, 41.405], [2.212, 41.405], [2.212, 41.418], [2.195, 41.418], [2.195, 41.405]]],
      },
    },
  ],
};

export const LAND_USE_COLORS: Record<string, string> = {
  residential: '#6366f1',
  commercial: '#f59e0b',
  industrial: '#ef4444',
  mixed: '#8b5cf6',
};
