import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { Leaf, Droplets, Layers, RotateCcw, Play } from 'lucide-react';
import { useMutation, useQuery } from '@tanstack/react-query';

import { Slider } from '@/components/ui/slider';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';
import {
  useCityStore,
  type FloodSeverity,
  type LayerKey,
} from '@/stores/cityStore';
import {
  fetchCities,
  fetchCityData,
  fetchImpactStory,
  fetchSdgScores,
  simulateScenario,
} from '@/services/api';

const FLOOD_OPTIONS: { value: FloodSeverity; label: string }[] = [
  { value: 'none', label: 'None' },
  { value: 'mild', label: 'Mild' },
  { value: 'moderate', label: 'Moderate' },
  { value: 'extreme', label: 'Extreme' },
];

const LAYER_LABELS: Record<LayerKey, string> = {
  buildings: '3D Buildings',
  landUse: 'Land Use',
  greenCover: 'Green Cover',
  heatIslands: 'Heat Islands',
  floodZones: 'Flood Zones',
};

export function ScenarioPanel() {
  const {
    cities,
    currentCityId,
    greenCoverIncrease,
    floodSeverity,
    scenarioApplied,
    layers,
    setCities,
    setCurrentCity,
    setBaseline,
    setScenarioMetrics,
    setSdgScores,
    setImpactStory,
    setGreenCoverIncrease,
    setFloodSeverity,
    toggleLayer,
    resetScenario,
  } = useCityStore();

  const { toast } = useToast();

  // Load supported cities once
  const citiesQuery = useQuery({
    queryKey: ['cities'],
    queryFn: fetchCities,
  });

  useEffect(() => {
    if (citiesQuery.data) {
      setCities(citiesQuery.data);
    }
  }, [citiesQuery.data, setCities]);

  // Load baseline metrics whenever the current city changes
  const cityDataQuery = useQuery({
    queryKey: ['city-data', currentCityId],
    enabled: !!currentCityId,
    queryFn: () => fetchCityData(currentCityId!),
  });

  useEffect(() => {
    if (cityDataQuery.data) {
      const m = cityDataQuery.data.metrics;
      setBaseline({
        density: m.builtUp,
        greenCover: m.greenCover,
        heatStress: m.heatStress,
        floodRisk: m.floodRisk,
      });
    }
  }, [cityDataQuery.data, setBaseline]);

  const scenarioMutation = useMutation({
    mutationFn: simulateScenario,
    onSuccess: async (result) => {
      setScenarioMetrics(result.scenario_metrics);

      const sdg = await fetchSdgScores({
        city: result.city,
        green_increase: result.config.green_increase,
        flood_intensity: result.config.flood_intensity,
        sprawl_horizon: result.config.sprawl_horizon,
      });
      setSdgScores(sdg.scores);

      const explain = await fetchImpactStory({
        city: result.city,
        baseline: result.baseline_metrics,
        scenario: result.scenario_metrics,
        config: result.config,
      });
      setImpactStory(explain.story);
    },
    onError: (err: unknown) => {
      console.error(err);
      toast({
        title: 'Scenario failed',
        description:
          err instanceof Error ? err.message : 'Unable to run scenario. Please try again.',
        variant: 'destructive',
      });
    },
  });

  const handleApplyScenario = () => {
    if (!currentCityId) return;
    scenarioMutation.mutate({
      city: currentCityId,
      green_increase: greenCoverIncrease,
      flood_event: floodSeverity !== 'none',
      flood_intensity: floodSeverity,
      sprawl_horizon: 2030,
    });
  };

  return (
    <motion.div
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.4 }}
      className="h-full flex flex-col p-5 gap-6 overflow-y-auto"
    >
      {/* Header */}
      <div>
        <h1 className="text-lg font-bold text-foreground flex items-center gap-2">
          <Leaf className="h-5 w-5 text-primary" />
          Urban Digital Twin
        </h1>
        <p className="text-xs text-muted-foreground mt-1">
          SDG 11 · Sustainable Cities & Communities
        </p>
      </div>

      {/* City selector */}
      <div className="glass-panel-solid p-4 space-y-2">
        <div className="section-title">City</div>
        <div className="flex flex-wrap gap-1.5">
          {cities.map((c) => (
            <Button
              key={c.id}
              size="xs"
              variant={currentCityId === c.id ? 'default' : 'outline'}
              onClick={() => setCurrentCity(c.id)}
            >
              {c.name}
            </Button>
          ))}
        </div>
      </div>

      {/* Green Cover Slider */}
      <div className="glass-panel-solid p-4 space-y-3">
        <div className="section-title flex items-center gap-1.5">
          <Leaf className="h-3.5 w-3.5" />
          Green Cover Increase
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-foreground">+{greenCoverIncrease}%</span>
          <span className="text-xs text-muted-foreground">0–30%</span>
        </div>
        <Slider
          value={[greenCoverIncrease]}
          onValueChange={([val]) => setGreenCoverIncrease(val)}
          min={0}
          max={30}
          step={5}
          className="w-full"
        />
      </div>

      {/* Flood Severity */}
      <div className="glass-panel-solid p-4 space-y-3">
        <div className="section-title flex items-center gap-1.5">
          <Droplets className="h-3.5 w-3.5" />
          Flash Flood Severity
        </div>
        <div className="grid grid-cols-2 gap-1.5">
          {FLOOD_OPTIONS.map((opt) => (
            <Button
              key={opt.value}
              variant={floodSeverity === opt.value ? 'default' : 'outline'}
              size="sm"
              className="text-xs h-8"
              onClick={() => setFloodSeverity(opt.value)}
            >
              {opt.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Apply / Reset */}
      <div className="flex gap-2">
        <Button
          onClick={handleApplyScenario}
          className="flex-1 gap-1.5"
          size="sm"
          disabled={!currentCityId || scenarioMutation.isPending}
        >
          <Play className="h-3.5 w-3.5" />
          {scenarioMutation.isPending ? 'Running…' : 'Run Scenario'}
        </Button>
        <Button
          onClick={resetScenario}
          variant="outline"
          size="sm"
          disabled={!scenarioApplied}
          className="gap-1.5"
        >
          <RotateCcw className="h-3.5 w-3.5" />
          Reset
        </Button>
      </div>

      {/* Layer Toggles */}
      <div className="glass-panel-solid p-4 space-y-3">
        <div className="section-title flex items-center gap-1.5">
          <Layers className="h-3.5 w-3.5" />
          Map Layers
        </div>
        <div className="space-y-2.5">
          {(Object.keys(layers) as LayerKey[]).map((key) => (
            <div key={key} className="flex items-center justify-between">
              <Label className="text-sm text-secondary-foreground cursor-pointer">
                {LAYER_LABELS[key]}
              </Label>
              <Switch
                checked={layers[key]}
                onCheckedChange={() => toggleLayer(key)}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Info */}
      <div className="mt-auto pt-4 border-t border-border">
        <p className="text-[10px] text-muted-foreground leading-relaxed">
          Powered by live satellite indices, ML models, and Gemini explanations
          from the Resilient City API.
        </p>
      </div>
    </motion.div>
  );
}

