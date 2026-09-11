import { useState, useCallback } from 'react';

const DEFAULT_API_URL = import.meta.env.VITE_API_URL || (
  typeof window !== 'undefined' && window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : 'http://localhost:8000'
);

export function useSSE() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [traceCards, setTraceCards] = useState([]);
  const [finalAnswer, setFinalAnswer] = useState(null);
  const [routerInfo, setRouterInfo] = useState(null);
  const [error, setError] = useState(null);
  const [apiUrl, setApiUrl] = useState(() => {
    return localStorage.getItem('orca_api_url') || DEFAULT_API_URL;
  });

  const updateApiUrl = (newUrl) => {
    setApiUrl(newUrl);
    localStorage.setItem('orca_api_url', newUrl);
  };

  const reset = useCallback(() => {
    setIsStreaming(false);
    setTraceCards([]);
    setFinalAnswer(null);
    setRouterInfo(null);
    setError(null);
  }, []);

  const sendQuestion = useCallback(async (question, location) => {
    reset();
    setIsStreaming(true);

    try {
      const targetBase = apiUrl.replace(/\/+$/, '');
      const endpoint = `${targetBase}/ask`;

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question, location }),
      });

      if (!response.ok) {
        if (response.status === 405 && window.location.hostname.includes('github.io')) {
          throw new Error(
            "GitHub Pages is a static file host and cannot run Python/FastAPI backends. " +
            "Please run the backend locally or set your backend server URL in the Backend Settings modal."
          );
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        
        buffer = lines.pop() || '';

        for (const block of lines) {
          if (!block.trim()) continue;
          
          let eventName = 'message';
          let data = '';

          const parts = block.split('\n');
          for (const p of parts) {
            if (p.startsWith('event: ')) eventName = p.substring(7).trim();
            if (p.startsWith('data: ')) data = p.substring(6).trim();
          }

          try {
            if (eventName === 'router') {
              setRouterInfo(JSON.parse(data));
            } else if (eventName === 'agent_result') {
              setTraceCards(prev => [...prev, JSON.parse(data)]);
            } else if (eventName === 'synthesis') {
              setFinalAnswer(JSON.parse(data));
            } else if (eventName === 'done') {
              setIsStreaming(false);
            } else if (eventName === 'error') {
              setError(JSON.parse(data).error || data);
              setIsStreaming(false);
            }
          } catch (jsonErr) {
            console.warn("Could not parse SSE payload:", data, jsonErr);
          }
        }
      }
    } catch (err) {
      setError(err.message);
      setIsStreaming(false);
    }
  }, [apiUrl, reset]);

  return { isStreaming, traceCards, finalAnswer, routerInfo, error, sendQuestion, reset, apiUrl, updateApiUrl };
}
