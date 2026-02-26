import { create } from 'zustand';

export interface Metrics {
  density: number;
  greenCover: number;
  heatStress: number;
  floodRisk: number;
}

export interface SdgScores {
  greenScore: number;
  heatResilienceScore: number;
  floodRiskScore: number;
  urbanSprawlScore: number;
  sdg11CompositeScore: number;
}

export type FloodSeverity = 'none' | 'mild' | 'moderate' | 'extreme';

export type LayerKey =
  | 'landUse'
  | 'greenCover'
  | 'heatIslands'
  | 'floodZones'
  | 'buildings';

export interface CityMeta {
  id: string;
  name: string;
  country: string;
  center: [number, number];
  zoom: number;
}

interface CityState {
  cities: CityMeta[];
  currentCityId: string | null;

  greenCoverIncrease: number;
  floodSeverity: FloodSeverity;
  scenarioApplied: boolean;
  layers: Record<LayerKey, boolean>;

  baseMetrics: Metrics | null;
  currentMetrics: Metrics | null;
  sdgScores: SdgScores | null;
  impactStory: string | null;

  setCities: (cities: CityMeta[]) => void;
  setCurrentCity: (cityId: string) => void;

  setBaseline: (metrics: Metrics) => void;
  setScenarioMetrics: (metrics: Metrics) => void;
  setSdgScores: (scores: SdgScores) => void;
  setImpactStory: (story: string | null) => void;

  setGreenCoverIncrease: (val: number) => void;
  setFloodSeverity: (val: FloodSeverity) => void;
  toggleLayer: (layer: LayerKey) => void;

  applyScenarioLocally: () => void;
  resetScenario: () => void;
}

export const useCityStore = create<CityState>((set, get) => ({
  cities: [],
  currentCityId: null,

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

  baseMetrics: null,
  currentMetrics: null,
  sdgScores: null,
  impactStory: null,

  setCities: (cities) =>
    set((state) => ({
      cities,
      currentCityId: state.currentCityId ?? cities[0]?.id ?? null,
    })),
  setCurrentCity: (cityId) =>
    set({
      currentCityId: cityId,
      scenarioApplied: false,
      greenCoverIncrease: 0,
      floodSeverity: 'none',
      impactStory: null,
    }),

  setBaseline: (metrics) =>
    set({
      baseMetrics: metrics,
      currentMetrics: metrics,
    }),
  setScenarioMetrics: (metrics) =>
    set({
      currentMetrics: metrics,
      scenarioApplied: true,
    }),
  setSdgScores: (scores) => set({ sdgScores: scores }),
  setImpactStory: (story) => set({ impactStory: story }),

  setGreenCoverIncrease: (val) => set({ greenCoverIncrease: val }),
  setFloodSeverity: (val) => set({ floodSeverity: val as FloodSeverity }),
  toggleLayer: (layer) =>
    set((state) => ({
      layers: { ...state.layers, [layer]: !state.layers[layer] },
    })),

  // Fallback local-only scenario toggle to keep map animations responsive
  applyScenarioLocally: () => {
    const { scenarioApplied } = get();
    if (!scenarioApplied) {
      set({ scenarioApplied: true });
    }
  },

  resetScenario: () =>
    set((state) => ({
      scenarioApplied: false,
      greenCoverIncrease: 0,
      floodSeverity: 'none',
      currentMetrics: state.baseMetrics,
      impactStory: null,
    })),
}));

