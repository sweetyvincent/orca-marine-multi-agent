import React from 'react';
import { Loader, Check } from 'lucide-react';

export default function AgentStatusBar({ routerInfo, traceCards = [], isStreaming }) {
  if (!routerInfo) return null;

  const agents = routerInfo.agents || [];
  
  const isRouterDone = !!routerInfo;
  const isAgentsDone = traceCards.length >= agents.length && agents.length > 0;
  const isSynthesisDone = !isStreaming && isAgentsDone;

  const Step = ({ label, status }) => (
    <div className="flex flex-col items-center relative z-10">
      <div className={`w-6 h-6 rounded-full flex items-center justify-center border-2 ${
        status === 'complete' ? 'bg-green-900 border-green-500 text-green-400' :
        status === 'running' ? 'bg-blue-900 border-blue-500 text-blue-400' :
        'bg-ocean-900 border-ocean-700 text-ocean-600'
      }`}>
        {status === 'complete' ? <Check className="w-3 h-3" /> :
         status === 'running' ? <Loader className="w-3 h-3 animate-spin" /> : 
         <div className="w-2 h-2 rounded-full bg-ocean-700" />}
      </div>
      <span className={`text-[10px] mt-1 font-medium ${
        status === 'pending' ? 'text-ocean-600' : 'text-ocean-200'
      }`}>{label}</span>
    </div>
  );

  return (
    <div className="relative flex items-start justify-between w-full max-w-xs mx-auto">
      <div className="absolute top-3 left-3 right-3 h-[2px] bg-ocean-800 -z-0"></div>
      
      <Step label="Router" status="complete" />
      <Step label="Agents" status={isAgentsDone ? 'complete' : (isRouterDone && isStreaming ? 'running' : 'pending')} />
      <Step label="Synthesis" status={isSynthesisDone ? 'complete' : (isAgentsDone && isStreaming ? 'running' : 'pending')} />
    </div>
  );
}
