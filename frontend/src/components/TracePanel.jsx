import React from 'react';
import TraceCard from './TraceCard';
import AgentStatusBar from './AgentStatusBar';
import { AlertTriangle, ShieldCheck, ShieldAlert } from 'lucide-react';

const RISK_CONFIG = {
  high: { bg: 'bg-red-950/30', border: 'border-red-900/50', text: 'text-red-200', icon: 'text-red-400', label: 'HIGH' },
  elevated: { bg: 'bg-orange-950/30', border: 'border-orange-900/50', text: 'text-orange-200', icon: 'text-orange-400', label: 'ELEVATED' },
  moderate: { bg: 'bg-yellow-950/30', border: 'border-yellow-900/50', text: 'text-yellow-200', icon: 'text-yellow-400', label: 'MODERATE' },
  low: { bg: 'bg-green-950/30', border: 'border-green-900/50', text: 'text-green-200', icon: 'text-green-400', label: 'LOW' },
};

export default function TracePanel({ routerInfo, traceCards = [], riskLevel, isStreaming }) {
  if (!routerInfo && traceCards.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-ocean-500 text-sm p-6">
        <div className="text-center">
          <span className="text-4xl block mb-3 opacity-40">🔬</span>
          <p>Agent trace will appear here</p>
          <p className="text-xs mt-1 text-ocean-600">Ask a question to see the multi-agent reasoning</p>
        </div>
      </div>
    );
  }

  const agents = routerInfo?.agents || [];
  const riskConfig = riskLevel ? RISK_CONFIG[riskLevel.toLowerCase()] || null : null;
  
  return (
    <div className="flex flex-col h-full bg-ocean-950/20">
      <div className="p-4 border-b border-ocean-800/50">
        <h3 className="text-sm font-semibold text-ocean-200 mb-4 flex items-center">
          <span className="mr-2">🔬</span> Agentic Reasoning Trace
        </h3>
        <AgentStatusBar routerInfo={routerInfo} traceCards={traceCards} isStreaming={isStreaming} />
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {routerInfo && (
          <div className="glass-card p-3 border-ocean-700/40">
            <h4 className="text-xs font-semibold text-ocean-300 mb-1 uppercase tracking-wider">Router Decision</h4>
            <p className="text-sm text-ocean-100">{routerInfo.reasoning}</p>
            <div className="flex gap-2 mt-2 flex-wrap">
              {agents.map(a => (
                <span key={a} className="text-xs bg-ocean-800/60 text-ocean-200 px-2 py-0.5 rounded border border-ocean-700">
                  {a === 'sst' ? '🌡️ SST' : a === 'chlorophyll' ? '🌿 Chlorophyll' : a === 'fisheries' ? '🐟 Fisheries' : a}
                </span>
              ))}
            </div>
          </div>
        )}

        {traceCards.map((card, idx) => (
          <TraceCard key={`${card.agent}-${idx}`} data={card} />
        ))}
        
        {riskConfig && (
           <div className={`p-4 rounded-xl flex items-start gap-3 border ${riskConfig.bg} ${riskConfig.border} ${riskConfig.text}`}>
             <AlertTriangle className={`w-5 h-5 mt-0.5 ${riskConfig.icon}`} />
             <div>
               <h4 className="text-sm font-bold">HAB Risk Assessment: {riskConfig.label}</h4>
               <p className="text-xs mt-1 opacity-80">Based on synthesized agent data from SST anomaly and chlorophyll concentration.</p>
             </div>
           </div>
        )}

        {isStreaming && (
          <div className="flex items-center gap-2 text-ocean-400 text-xs">
            <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
            Processing...
          </div>
        )}
      </div>
    </div>
  );
}
