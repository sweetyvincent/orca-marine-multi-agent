import React, { useState } from 'react';
import { Thermometer, Leaf, Fish, Check, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';

const AGENT_CONFIG = {
  sst: { icon: Thermometer, label: '🌡️ SST Agent', color: 'text-red-400', border: 'border-red-900/50', bg: 'bg-red-950/20' },
  chlorophyll: { icon: Leaf, label: '🌿 Chlorophyll Agent', color: 'text-green-400', border: 'border-green-900/50', bg: 'bg-green-950/20' },
  fisheries: { icon: Fish, label: '🐟 Fisheries Agent', color: 'text-blue-400', border: 'border-blue-900/50', bg: 'bg-blue-950/20' },
};

const DEFAULT_CONFIG = { icon: AlertCircle, label: 'Agent', color: 'text-ocean-400', border: 'border-ocean-700/50', bg: 'bg-ocean-900/20' };

function getSummary(data) {
  const agentType = data.agent;
  if (data.error) return `⚠️ ${data.error}`;
  
  if (agentType === 'sst') {
    const sst = data.current_sst_c;
    const anom = data.anomaly_c;
    const trend = data.trend_direction;
    if (sst !== undefined) {
      return `SST: ${sst}°C (${anom >= 0 ? '+' : ''}${anom}°C anomaly, ${trend})`;
    }
  }
  
  if (agentType === 'chlorophyll') {
    const mean = data.mean_chl_mg_m3;
    const cls = data.classification;
    if (mean !== undefined) {
      return `Chlorophyll-a: ${mean} mg/m³ (${cls})`;
    }
  }
  
  if (agentType === 'fisheries') {
    const risk = data.risk_level;
    const advisory = data.advisory;
    if (risk) {
      return `HAB Risk: ${risk.toUpperCase()} — ${advisory}`;
    }
  }
  
  return 'Data processed.';
}

export default function TraceCard({ data }) {
  const [expanded, setExpanded] = useState(false);
  const agentType = data.agent || 'unknown';
  const config = AGENT_CONFIG[agentType] || DEFAULT_CONFIG;
  const Icon = config.icon;
  const hasError = !!data.error;

  return (
    <div className={`rounded-xl border ${config.border} ${config.bg} p-3 overflow-hidden transition-all`}>
      <div className="flex items-center justify-between cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center gap-2">
          <Icon className={`w-4 h-4 ${config.color}`} />
          <span className="text-sm font-semibold text-ocean-50">{config.label}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] bg-ocean-800/80 px-2 py-0.5 rounded text-ocean-300">
            {data.data_source || 'Analysis'}
          </span>
          {hasError ? (
            <AlertCircle className="w-4 h-4 text-red-500" />
          ) : (
            <Check className="w-4 h-4 text-green-500" />
          )}
        </div>
      </div>
      
      <p className={`text-sm mt-2 font-medium ${hasError ? 'text-red-300' : 'text-ocean-200'}`}>
        {getSummary(data)}
      </p>

      {data.observation_date && (
        <p className="text-[10px] text-ocean-500 mt-1">
          Observed: {new Date(data.observation_date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}
        </p>
      )}

      {expanded && (
        <div className="mt-3 pt-3 border-t border-ocean-800/50">
          <pre className="text-[10px] text-ocean-400 bg-ocean-950/50 p-2 rounded overflow-x-auto max-h-40">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      )}
      
      <div className="mt-2 text-center" onClick={() => setExpanded(!expanded)}>
        {expanded ? <ChevronUp className="w-3 h-3 mx-auto text-ocean-600 cursor-pointer" /> : <ChevronDown className="w-3 h-3 mx-auto text-ocean-600 cursor-pointer" />}
      </div>
    </div>
  );
}
