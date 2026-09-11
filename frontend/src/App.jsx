import React, { useState } from 'react';
import ChatPanel from './components/ChatPanel';
import TracePanel from './components/TracePanel';
import { useSSE } from './hooks/useSSE';

export default function App() {
  const [messages, setMessages] = useState([]);
  const sse = useSSE();

  const handleSend = async (question, location) => {
    // Add user message
    const newUserMsg = { id: Date.now(), type: 'user', content: question, location };
    const tempAssistantId = Date.now() + 1;
    const tempAssistantMsg = { id: tempAssistantId, type: 'assistant', content: '', traceCards: [], routerInfo: null, riskLevel: null, isStreaming: true };
    
    setMessages(prev => [...prev, newUserMsg, tempAssistantMsg]);
    
    // Connect to SSE for the response
    // But since useSSE handles the state for one request, we'll keep it simple: 
    // App acts as a container, ChatPanel uses App's messages.
    // When stream updates, we update the last assistant message.
    
    // Reset SSE and start new stream
    await sse.sendQuestion(question, location);
  };

  // Sync SSE state to the last assistant message
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


  return (
    <div className="flex flex-col h-screen overflow-hidden bg-ocean-950">
      <header className="px-6 py-4 border-b border-ocean-800/50 glass-card mx-2 mt-2">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🌊</span>
          <div>
            <h1 className="text-xl font-bold text-ocean-100 tracking-wide">ORCA</h1>
            <p className="text-xs text-ocean-400 font-medium tracking-wider uppercase">Marine Multi-Agent System</p>
          </div>
        </div>
      </header>
      
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
