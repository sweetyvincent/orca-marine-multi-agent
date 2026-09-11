import React, { useState, useEffect, useRef } from 'react';
import { Send } from 'lucide-react';
import MessageBubble from './MessageBubble';
import LocationPicker from './LocationPicker';

const PRESET_QUESTIONS = [
  "What's the current SST near Chennai coast?",
  "What are chlorophyll levels in the Gulf of Mexico?",
  "Will conditions favour a harmful algal bloom near Florida Keys next week?",
  "Is it safe to harvest shellfish from Chesapeake Bay?"
];

export default function ChatPanel({ messages, onSend, isStreaming }) {
  const [input, setInput] = useState('');
  const [location, setLocation] = useState('Chennai');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    onSend(input, location);
    setInput('');
  };

  const handleChipClick = (question) => {
    if (isStreaming) return;
    onSend(question, location);
  };

  return (
    <div className="flex flex-col h-full bg-ocean-950/30 rounded-xl overflow-hidden relative">
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-ocean-200/60">
            <span className="text-6xl mb-4 opacity-50">🐋</span>
            <h2 className="text-xl font-medium mb-2 text-ocean-100">Welcome to ORCA</h2>
            <p className="text-sm max-w-md">Your AI assistant for marine data analysis and Harmful Algal Bloom risk assessment.</p>
          </div>
        ) : (
          messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 bg-ocean-900/80 border-t border-ocean-700/50 backdrop-blur-md">
        {messages.length === 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {PRESET_QUESTIONS.map((q, idx) => (
              <button 
                key={idx} 
                onClick={() => handleChipClick(q)}
                className="text-xs bg-ocean-800/50 hover:bg-ocean-700/80 text-ocean-200 border border-ocean-700/50 rounded-full px-3 py-1.5 transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="flex gap-2">
          <LocationPicker value={location} onChange={setLocation} />
          <div className="flex-1 relative flex items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about ocean conditions..."
              disabled={isStreaming}
              className="w-full bg-ocean-950 border border-ocean-700 rounded-lg pl-4 pr-12 py-3 text-sm text-ocean-50 placeholder-ocean-400 focus:outline-none focus:border-ocean-400 focus:ring-1 focus:ring-ocean-400 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!input.trim() || isStreaming}
              className="absolute right-2 p-1.5 rounded-md bg-ocean-600 hover:bg-ocean-500 disabled:opacity-50 disabled:hover:bg-ocean-600 text-white transition-colors"
            >
              {isStreaming ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
