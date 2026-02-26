/**
 * Service layer for metrics data.
 * Currently returns mock data; designed for easy swap to real API/WebSocket.
 */

import type { Metrics } from '@/stores/cityStore';

const BASE_METRICS: Metrics = {
  density: 72,
  greenCover: 34,
  heatStress: 68,
  floodRisk: 45,
};

/** Fetch current city metrics (mock) */
export async function fetchMetrics(): Promise<Metrics> {
  // TODO: Replace with real API call
  // return fetch('/api/metrics').then(r => r.json());
  return BASE_METRICS;
}

/** Simulate slight random walk for pseudo-real-time updates */
export function createMetricsStream(
  callback: (metrics: Metrics) => void,
  intervalMs = 20000
): () => void {
  let current = { ...BASE_METRICS };

  const id = setInterval(() => {
    current = {
      density: clamp(current.density + randDelta(1), 0, 100),
      greenCover: clamp(current.greenCover + randDelta(0.5), 0, 100),
      heatStress: clamp(current.heatStress + randDelta(1.5), 0, 100),
      floodRisk: clamp(current.floodRisk + randDelta(1), 0, 100),
    };
    callback(current);
  }, intervalMs);

  return () => clearInterval(id);
}

function randDelta(magnitude: number): number {
  return Math.round((Math.random() - 0.5) * 2 * magnitude);
}

function clamp(val: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, val));
}

// Placeholder for future WebSocket integration
// export function connectWebSocket(url: string, onMessage: (data: any) => void) {
//   const ws = new WebSocket(url);
//   ws.onmessage = (event) => onMessage(JSON.parse(event.data));
//   return () => ws.close();
// }
