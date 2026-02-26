import { ScenarioPanel } from './ScenarioPanel';
import { CityMap } from './CityMap';
import { MetricsPanel } from './MetricsPanel';

export function Dashboard() {
  return (
    <div className="flex flex-col lg:flex-row h-screen w-full bg-background overflow-hidden">
      {/* Left: Scenario Controls */}
      <aside className="w-full lg:w-80 flex-shrink-0 border-b lg:border-b-0 lg:border-r border-border bg-card/50 overflow-y-auto max-h-[40vh] lg:max-h-none">
        <ScenarioPanel />
      </aside>

      {/* Center: Map */}
      <main className="flex-1 relative min-h-[300px] lg:min-h-0">
        <CityMap />
      </main>

      {/* Right: Metrics */}
      <aside className="w-full lg:w-80 flex-shrink-0 border-t lg:border-t-0 lg:border-l border-border bg-card/50 overflow-y-auto max-h-[40vh] lg:max-h-none">
        <MetricsPanel />
      </aside>
    </div>
  );
}
