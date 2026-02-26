import { useEffect, useState } from 'react';
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
    setHotspots,
    setGreenCoverIncrease,
    setFloodSeverity,
    toggleLayer,
    resetScenario,
  } = useCityStore();

  const { toast } = useToast();

  // Extended scenario parameters grouped A–F
  // A. Environmental & Ecological
  const [treePlantingRate, setTreePlantingRate] = useState(0); // %
  const [wetlandRestoration, setWetlandRestoration] = useState(0); // hectares (scaled)

  // B. Urban Heat
  const [coolRoofCoverage, setCoolRoofCoverage] = useState(0); // %

  // C. Flood & Hydrological
  const [drainageImprovement, setDrainageImprovement] = useState(0); // %
  const [permeableSurfaceGain, setPermeableSurfaceGain] = useState(0); // %

  // D. Urban Growth & Infrastructure
  const [densificationRate, setDensificationRate] = useState(0); // % per year

  // E. Socio-Economic Vulnerability
  const [lowIncomeShare, setLowIncomeShare] = useState(0); // %

  // F. Policy & Planning
  const [zoningEnforcement, setZoningEnforcement] = useState(0); // 0–100

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
      setHotspots(result.hotspots ?? []);

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
      tree_planting_rate: treePlantingRate,
      wetland_restoration: wetlandRestoration,
      cool_roof_coverage: coolRoofCoverage,
      drainage_improvement: drainageImprovement,
      permeable_surface_gain: permeableSurfaceGain,
      densification_rate: densificationRate,
      low_income_share: lowIncomeShare,
      zoning_enforcement: zoningEnforcement,
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
          A. Environmental & Ecological
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
        <div className="mt-3 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Tree planting rate</span>
            <span className="text-foreground">{treePlantingRate}%</span>
          </div>
          <Slider
            value={[treePlantingRate]}
            onValueChange={([val]) => setTreePlantingRate(val)}
            min={0}
            max={50}
            step={5}
          />
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Wetland restoration</span>
            <span className="text-foreground">{wetlandRestoration} units</span>
          </div>
          <Slider
            value={[wetlandRestoration]}
            onValueChange={([val]) => setWetlandRestoration(val)}
            min={0}
            max={20}
            step={2}
          />
        </div>
      </div>

      {/* Flood & Heat */}
      <div className="glass-panel-solid p-4 space-y-4">
        <div className="space-y-3">
          <div className="section-title flex items-center gap-1.5">
            <Droplets className="h-3.5 w-3.5" />
            B. Urban Heat & C. Flood
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Cool roof coverage</span>
            <span className="text-foreground">{coolRoofCoverage}%</span>
          </div>
          <Slider
            value={[coolRoofCoverage]}
            onValueChange={([val]) => setCoolRoofCoverage(val)}
            min={0}
            max={100}
            step={5}
          />
        </div>
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Drainage improvement</span>
            <span className="text-foreground">{drainageImprovement}%</span>
          </div>
          <Slider
            value={[drainageImprovement]}
            onValueChange={([val]) => setDrainageImprovement(val)}
            min={0}
            max={100}
            step={10}
          />
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Permeable surfaces</span>
            <span className="text-foreground">{permeableSurfaceGain}%</span>
          </div>
          <Slider
            value={[permeableSurfaceGain]}
            onValueChange={([val]) => setPermeableSurfaceGain(val)}
            min={0}
            max={40}
            step={5}
          />
        </div>
        <div className="space-y-2">
          <div className="text-xs font-medium text-secondary-foreground">
            Flash flood severity
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
      </div>

      {/* D–F: Growth, vulnerability, policy */}
      <div className="glass-panel-solid p-4 space-y-3">
        <div className="section-title">D–F. Growth, Vulnerability & Policy</div>
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Densification rate</span>
          <span className="text-foreground">{densificationRate}%/yr</span>
        </div>
        <Slider
          value={[densificationRate]}
          onValueChange={([val]) => setDensificationRate(val)}
          min={0}
          max={5}
          step={0.5}
        />
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Low-income population</span>
          <span className="text-foreground">{lowIncomeShare}%</span>
        </div>
        <Slider
          value={[lowIncomeShare]}
          onValueChange={([val]) => setLowIncomeShare(val)}
          min={0}
          max={100}
          step={5}
        />
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Zoning enforcement strength</span>
          <span className="text-foreground">{zoningEnforcement}/100</span>
        </div>
        <Slider
          value={[zoningEnforcement]}
          onValueChange={([val]) => setZoningEnforcement(val)}
          min={0}
          max={100}
          step={10}
        />
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

