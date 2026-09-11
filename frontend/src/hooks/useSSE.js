import { useState, useCallback } from 'react';

export function useSSE() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [traceCards, setTraceCards] = useState([]);
  const [finalAnswer, setFinalAnswer] = useState(null);
  const [routerInfo, setRouterInfo] = useState(null);
  const [error, setError] = useState(null);

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
      const response = await fetch('/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question, location }),
      });

      if (!response.ok) {
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
        
        buffer = lines.pop() || ''; // keep the incomplete part

        for (const block of lines) {
          if (!block.trim()) continue;
          
          let eventName = 'message';
          let data = '';

          const parts = block.split('\n');
          for(const p of parts) {
            if (p.startsWith('event: ')) eventName = p.substring(7).trim();
            if (p.startsWith('data: ')) data = p.substring(6).trim();
          }

          if (eventName === 'router') {
            setRouterInfo(JSON.parse(data));
          } else if (eventName === 'agent_result') {
            setTraceCards(prev => [...prev, JSON.parse(data)]);
          } else if (eventName === 'synthesis') {
            setFinalAnswer(JSON.parse(data));
          } else if (eventName === 'done') {
            setIsStreaming(false);
          } else if (eventName === 'error') {
            setError(JSON.parse(data).message || data);
            setIsStreaming(false);
          }
        }
      }
    } catch (err) {
      setError(err.message);
      setIsStreaming(false);
    }
  }, [reset]);

  return { isStreaming, traceCards, finalAnswer, routerInfo, error, sendQuestion, reset };
}
