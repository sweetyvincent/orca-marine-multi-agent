import React, { useState } from 'react';
import TracePanel from './TracePanel';
import { ChevronDown, ChevronUp } from 'lucide-react';

export default function MessageBubble({ message }) {
  const isUser = message.type === 'user';
  const [showTrace, setShowTrace] = useState(false);

  return (
    <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
      <div 
        className={`max-w-[85%] rounded-2xl px-5 py-3.5 shadow-sm ${
          isUser 
            ? 'bg-ocean-600 text-white rounded-tr-sm' 
            : 'glass-card border border-ocean-700/50 rounded-tl-sm text-ocean-50'
        }`}
      >
        <div className="prose prose-invert max-w-none text-sm leading-relaxed">
          {message.content || (
            <span className="flex items-center text-ocean-400">
              <span className="animate-pulse">Thinking</span>
              <span className="animate-bounce mx-[1px]">.</span>
              <span className="animate-bounce delay-100 mx-[1px]">.</span>
              <span className="animate-bounce delay-200 mx-[1px]">.</span>
            </span>
          )}
        </div>
      </div>

      {!isUser && (message.traceCards?.length > 0 || message.routerInfo) && (
        <div className="mt-2 w-full md:hidden">
          <button 
            onClick={() => setShowTrace(!showTrace)}
            className="flex items-center text-xs text-ocean-400 hover:text-ocean-300 ml-1"
          >
            {showTrace ? <ChevronUp className="w-3 h-3 mr-1" /> : <ChevronDown className="w-3 h-3 mr-1" />}
            {showTrace ? 'Hide Agent Trace' : 'View Agent Trace'}
          </button>
          
          {showTrace && (
            <div className="mt-2 bg-ocean-900/40 rounded-xl p-2 border border-ocean-800/50">
              <TracePanel 
                routerInfo={message.routerInfo} 
                traceCards={message.traceCards} 
                riskLevel={message.riskLevel}
                isStreaming={message.isStreaming}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
