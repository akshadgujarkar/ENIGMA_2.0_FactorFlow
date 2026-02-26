import { QueryClient } from '@tanstack/react-query';

import type { CityMeta, Metrics, SdgScores } from '@/stores/cityStore';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api';

export const queryClient = new QueryClient();

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed with status ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchCities(): Promise<CityMeta[]> {
  return json<CityMeta[]>('/cities');
}

export interface CityDataResponse {
  city: string;
  ndvi_mean: number;
  ndbi_mean: number;
  lst_mean_c: number;
  flood_index_mean: number;
  metrics: {
    greenCover: number;
    builtUp: number;
    heatStress: number;
    floodRisk: number;
  };
}

export async function fetchCityData(cityId: string): Promise<CityDataResponse> {
  return json<CityDataResponse>(`/city/${cityId}/data`);
}

export interface ScenarioSimulateConfig {
  city: string;
  green_increase: number;
  flood_event: boolean;
  flood_intensity: 'none' | 'mild' | 'moderate' | 'extreme';
  sprawl_horizon: number;
}

export interface ScenarioSimulateResponse {
  city: string;
  config: ScenarioSimulateConfig;
  baseline_metrics: {
    density: number;
    greenCover: number;
    heatStress: number;
    floodRisk: number;
  };
  scenario_metrics: Metrics;
}

export async function simulateScenario(
  config: ScenarioSimulateConfig,
): Promise<ScenarioSimulateResponse> {
  return json<ScenarioSimulateResponse>('/scenario/simulate', {
    method: 'POST',
    body: JSON.stringify(config),
  });
}

export interface SdgHealthResponse {
  city: string;
  scores: SdgScores;
}

export async function fetchSdgScores(params: {
  city: string;
  green_increase: number;
  flood_intensity: string;
  sprawl_horizon: number;
}): Promise<SdgHealthResponse> {
  const search = new URLSearchParams({
    city: params.city,
    green_increase: String(params.green_increase),
    flood_intensity: params.flood_intensity,
    sprawl_horizon: String(params.sprawl_horizon),
  });
  return json<SdgHealthResponse>(`/sdg/health-scores?${search.toString()}`);
}

export interface ExplainResponse {
  story: string;
}

export async function fetchImpactStory(body: unknown): Promise<ExplainResponse> {
  return json<ExplainResponse>('/explain', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

