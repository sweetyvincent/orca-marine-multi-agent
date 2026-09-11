import React, { useState } from 'react';
import { Settings, Server, Check } from 'lucide-react';
import ChatPanel from './components/ChatPanel';
import TracePanel from './components/TracePanel';
import { useSSE } from './hooks/useSSE';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [showSettings, setShowSettings] = useState(false);
  const sse = useSSE();
  const [tempUrl, setTempUrl] = useState(sse.apiUrl);

  const handleSend = async (question, location) => {
    const newUserMsg = { id: Date.now(), type: 'user', content: question, location };
    const tempAssistantId = Date.now() + 1;
    const tempAssistantMsg = { 
      id: tempAssistantId, 
      type: 'assistant', 
      content: '', 
      traceCards: [], 
      routerInfo: null, 
      riskLevel: null, 
      isStreaming: true 
    };
    
    setMessages(prev => [...prev, newUserMsg, tempAssistantMsg]);
    await sse.sendQuestion(question, location);
  };

  React.useEffect(() => {
    setMessages(prev => {
      const msgs = [...prev];
      if (msgs.length > 0 && msgs[msgs.length - 1].type === 'assistant') {
        const lastMsg = msgs[msgs.length - 1];
        lastMsg.traceCards = sse.traceCards;
        lastMsg.routerInfo = sse.routerInfo;
        lastMsg.content = sse.finalAnswer?.final_answer || (sse.isStreaming ? 'Thinking...' : (sse.error || ''));
        lastMsg.riskLevel = sse.finalAnswer?.risk_level || null;
        lastMsg.isStreaming = sse.isStreaming;
      }
      return msgs;
    });
  }, [sse.traceCards, sse.routerInfo, sse.finalAnswer, sse.isStreaming, sse.error]);

  const saveSettings = (e) => {
    e.preventDefault();
    sse.updateApiUrl(tempUrl);
    setShowSettings(false);
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-ocean-950">
      <header className="px-6 py-4 border-b border-ocean-800/50 glass-card mx-2 mt-2 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🌊</span>
          <div>
            <h1 className="text-xl font-bold text-ocean-100 tracking-wide">ORCA</h1>
            <p className="text-xs text-ocean-400 font-medium tracking-wider uppercase">Marine Multi-Agent System</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button 
            onClick={() => { setTempUrl(sse.apiUrl); setShowSettings(true); }}
            className="flex items-center gap-1.5 text-xs bg-ocean-900/80 hover:bg-ocean-800 text-ocean-300 border border-ocean-700/60 rounded-lg px-3 py-1.5 transition-colors"
            title="Configure Backend API URL"
          >
            <Server className="w-3.5 h-3.5 text-ocean-400" />
            <span className="hidden sm:inline">Backend:</span>
            <span className="text-ocean-100 max-w-[150px] truncate">{sse.apiUrl}</span>
            <Settings className="w-3.5 h-3.5 ml-1 text-ocean-400" />
          </button>
        </div>
      </header>
      
      {showSettings && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-ocean-900 border border-ocean-700 rounded-2xl p-6 max-w-md w-full shadow-2xl">
            <h3 className="text-lg font-bold text-ocean-100 mb-2 flex items-center gap-2">
              <Server className="w-5 h-5 text-ocean-400" /> Backend API Configuration
            </h3>
            <p className="text-xs text-ocean-300 mb-4 leading-relaxed">
              When hosted on GitHub Pages (static), ORCA communicates with your running Python/FastAPI backend. Set your local or remote URL below:
            </p>
            <form onSubmit={saveSettings}>
              <label className="block text-xs font-semibold text-ocean-300 mb-1">Backend URL</label>
              <input 
                type="text"
                value={tempUrl}
                onChange={(e) => setTempUrl(e.target.value)}
                placeholder="http://localhost:8000"
                className="w-full bg-ocean-950 border border-ocean-700 rounded-lg px-3 py-2 text-sm text-ocean-100 focus:outline-none focus:border-ocean-400 mb-4"
              />
              <div className="flex justify-end gap-2">
                <button 
                  type="button" 
                  onClick={() => setShowSettings(false)}
                  className="px-4 py-2 rounded-lg text-xs text-ocean-300 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button 
                  type="submit"
                  className="px-4 py-2 rounded-lg text-xs bg-ocean-600 hover:bg-ocean-500 text-white font-medium flex items-center gap-1.5 transition-colors"
                >
                  <Check className="w-3.5 h-3.5" /> Save Configuration
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <main className="flex-1 flex flex-col md:flex-row gap-4 p-4 overflow-hidden">
        <div className="flex-1 md:w-[60%] flex flex-col glass-card overflow-hidden">
          <ChatPanel messages={messages} onSend={handleSend} isStreaming={sse.isStreaming} />
        </div>
        <div className="md:w-[40%] flex flex-col glass-card overflow-hidden hidden md:flex">
          {messages.length > 0 && (
             <TracePanel 
                routerInfo={sse.routerInfo || (messages[messages.length-1].type === 'assistant' ? messages[messages.length-1].routerInfo : null)} 
                traceCards={sse.traceCards || (messages[messages.length-1].type === 'assistant' ? messages[messages.length-1].traceCards : [])}
                riskLevel={sse.finalAnswer?.risk_level || (messages[messages.length-1].type === 'assistant' ? messages[messages.length-1].riskLevel : null)}
                isStreaming={sse.isStreaming}
             />
          )}
        </div>
      </main>
    </div>
  );
}
