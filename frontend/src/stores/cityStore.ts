import { create } from 'zustand';

export interface Metrics {
  density: number;
  greenCover: number;
  heatStress: number;
  floodRisk: number;
}

export type FloodSeverity = 'none' | 'mild' | 'moderate' | 'extreme';

export type LayerKey = 'landUse' | 'greenCover' | 'heatIslands' | 'floodZones' | 'buildings';

interface CityState {
  greenCoverIncrease: number;
  floodSeverity: FloodSeverity;
  scenarioApplied: boolean;
  layers: Record<LayerKey, boolean>;
  baseMetrics: Metrics;
  currentMetrics: Metrics;

  setGreenCoverIncrease: (val: number) => void;
  setFloodSeverity: (val: FloodSeverity) => void;
  toggleLayer: (layer: LayerKey) => void;
  applyScenario: () => void;
  resetScenario: () => void;
}

const BASE_METRICS: Metrics = {
  density: 72,
  greenCover: 34,
  heatStress: 68,
  floodRisk: 45,
};

const FLOOD_SEVERITY_BONUS: Record<FloodSeverity, number> = {
  none: 0,
  mild: 10,
  moderate: 25,
  extreme: 45,
};

function calculateMetrics(
  base: Metrics,
  greenIncrease: number,
  floodSeverity: FloodSeverity
): Metrics {
  const newGreenCover = Math.min(
    100,
    base.greenCover + greenIncrease * (1 - base.greenCover / 100)
  );
  const greenDelta = newGreenCover - base.greenCover;
  const newHeatStress = Math.max(0, Math.round(base.heatStress - greenDelta * 0.8));
  const floodBonus = FLOOD_SEVERITY_BONUS[floodSeverity];
  const greenMitigation = greenDelta * 0.3;
  const newFloodRisk = Math.min(
    100,
    Math.max(0, Math.round(base.floodRisk + floodBonus - greenMitigation))
  );
  const newDensity = Math.max(0, Math.round(base.density - greenDelta * 0.15));

  return {
    density: newDensity,
    greenCover: Math.round(newGreenCover),
    heatStress: newHeatStress,
    floodRisk: newFloodRisk,
  };
}

export const useCityStore = create<CityState>((set, get) => ({
  greenCoverIncrease: 0,
  floodSeverity: 'none',
  scenarioApplied: false,
  layers: {
    landUse: true,
    greenCover: true,
    heatIslands: true,
    floodZones: true,
    buildings: true,
  },
  baseMetrics: BASE_METRICS,
  currentMetrics: BASE_METRICS,

  setGreenCoverIncrease: (val) => set({ greenCoverIncrease: val }),
  setFloodSeverity: (val) => set({ floodSeverity: val as FloodSeverity }),
  toggleLayer: (layer) =>
    set((state) => ({
      layers: { ...state.layers, [layer]: !state.layers[layer] },
    })),
  applyScenario: () => {
    const { baseMetrics, greenCoverIncrease, floodSeverity } = get();
    set({
      scenarioApplied: true,
      currentMetrics: calculateMetrics(baseMetrics, greenCoverIncrease, floodSeverity),
    });
  },
  resetScenario: () =>
    set({
      scenarioApplied: false,
      greenCoverIncrease: 0,
      floodSeverity: 'none',
      currentMetrics: BASE_METRICS,
    }),
}));
