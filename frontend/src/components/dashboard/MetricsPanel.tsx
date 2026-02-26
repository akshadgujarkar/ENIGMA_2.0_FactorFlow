import { motion } from 'framer-motion';
import { Activity, TreePine, Thermometer, Waves } from 'lucide-react';
import { RadialProgress } from './RadialProgress';
import { useCityStore } from '@/stores/cityStore';

export function MetricsPanel() {
  const { currentMetrics, scenarioApplied } = useCityStore();

  const indicators = [
    {
      key: 'density',
      label: 'Urban Density',
      value: currentMetrics.density,
      color: 'hsl(var(--indicator-density))',
      icon: <Activity className="h-3.5 w-3.5" />,
      inverted: true,
    },
    {
      key: 'greenCover',
      label: 'Green Cover',
      value: currentMetrics.greenCover,
      color: 'hsl(var(--indicator-green))',
      icon: <TreePine className="h-3.5 w-3.5" />,
      inverted: false,
    },
    {
      key: 'heatStress',
      label: 'Heat Stress',
      value: currentMetrics.heatStress,
      color: 'hsl(var(--indicator-heat))',
      icon: <Thermometer className="h-3.5 w-3.5" />,
      inverted: true,
    },
    {
      key: 'floodRisk',
      label: 'Flood Risk',
      value: currentMetrics.floodRisk,
      color: 'hsl(var(--indicator-flood))',
      icon: <Waves className="h-3.5 w-3.5" />,
      inverted: true,
    },
  ];

  return (
    <motion.div
      initial={{ x: 20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.4 }}
      className="h-full flex flex-col p-5 gap-5 overflow-y-auto"
    >
      <div>
        <h2 className="text-sm font-bold text-foreground">SDG 11 Health Scores</h2>
        <p className="text-[10px] text-muted-foreground mt-0.5">
          {scenarioApplied ? 'Scenario applied — projected values' : 'Current baseline metrics'}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {indicators.map((ind, i) => (
          <motion.div
            key={ind.key}
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.1 * i, duration: 0.3 }}
            className="glass-panel-solid p-3 flex flex-col items-center"
          >
            <RadialProgress
              value={ind.value}
              color={ind.color}
              label={ind.label}
              icon={ind.icon}
              inverted={ind.inverted}
            />
          </motion.div>
        ))}
      </div>

      {/* Legend */}
      <div className="glass-panel-solid p-3 space-y-1.5">
        <div className="section-title">Status Legend</div>
        <div className="flex items-center gap-2 text-xs">
          <span className="indicator-badge-good">Good</span>
          <span className="indicator-badge-warning">Warning</span>
          <span className="indicator-badge-critical">Critical</span>
        </div>
      </div>

      {/* Summary Card */}
      {scenarioApplied && (
        <motion.div
          initial={{ y: 10, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="glass-panel p-3 border-primary/30 space-y-1"
        >
          <div className="text-xs font-semibold text-primary">Scenario Impact</div>
          <p className="text-[10px] text-muted-foreground leading-relaxed">
            Adding green cover reduces heat stress through evapotranspiration and
            mitigates flood risk via natural absorption. Urban density decreases
            slightly as green corridors replace impervious surfaces.
          </p>
        </motion.div>
      )}
    </motion.div>
  );
}
