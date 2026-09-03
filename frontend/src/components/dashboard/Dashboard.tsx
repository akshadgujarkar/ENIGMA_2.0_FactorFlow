/** @jsxRuntime classic */
import React from 'react';
import { ScenarioPanel } from './ScenarioPanel';
import { CityMap } from './CityMap';
import { MetricsPanel } from './MetricsPanel';

export function Dashboard() {
  return (
    <div className="flex flex-col lg:flex-row h-screen w-full bg-slate-950 overflow-hidden">
      {/* Left: Scenario Controls */}
      <aside className="w-full lg:w-80 flex-shrink-0 border-b lg:border-b-0 lg:border-r border-slate-800 bg-slate-900/60 overflow-y-auto max-h-[40vh] lg:max-h-none">
        <ScenarioPanel />
      </aside>

      {/* Center: Map */}
      <main className="flex-1 relative min-h-[300px] lg:min-h-0 bg-slate-950">
        <CityMap />
      </main>

      {/* Right: Metrics */}
      <aside className="w-full lg:w-80 flex-shrink-0 border-t lg:border-t-0 lg:border-l border-slate-800 bg-slate-900/60 overflow-y-auto max-h-[40vh] lg:max-h-none">
        <MetricsPanel />
      </aside>
    </div>
  );
}