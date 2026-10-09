import React, { useState, useEffect, useRef } from 'react';

export default function LiveSessionState({ jobData, onCancel }) {
  const [status, setStatus] = useState('Connecting...');
  const [history, setHistory] = useState([]);
  const [isListening, setIsListening] = useState(false);
  
  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  useEffect(() => {
    wsRef.current = new WebSocket('ws://localhost:8000/ws/live');
    
    wsRef.current.onopen = () => {
      setStatus('Connected');
      wsRef.current.send(JSON.stringify({ type: 'init', topic: jobData.chapter, doubt: jobData.doubt }));
    };
    
    wsRef.current.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'status') {
        setStatus(msg.text);
      } else if (msg.type === 'user_text') {
        setHistory(prev => [...prev, { role: 'user', content: msg.text }]);
      } else if (msg.type === 'audio') {
        setHistory(prev => [...prev, { role: 'assistant', content: msg.text }]);
        playAudio(msg.audio);
      }
    };
    
    wsRef.current.onerror = () => {
      setStatus('Connection error');
    };
    
    wsRef.current.onclose = () => {
      setStatus('Disconnected');
    };
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [jobData]);

  const playAudio = (base64Audio) => {
    const audio = new Audio('data:audio/wav;base64,' + base64Audio);
    audio.play();
    audio.onended = () => {
      // Auto start listening after Priya ma'am stops speaking
      startListening();
    };
  };

  const startListening = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];
      
      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };
      
      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = () => {
          const base64data = reader.result.split(',')[1];
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'audio', data: base64data }));
          }
        };
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorderRef.current.start();
      setIsListening(true);
      setStatus('Listening... (Click button to send)');
    } catch (err) {
      console.error('Mic error:', err);
      setStatus('Microphone access denied');
    }
  };

  const stopListening = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsListening(false);
      setStatus('Sending audio...');
    }
  };

  return (
    <div style={{ width: '100%', maxWidth: 600, margin: '0 auto', background: '#0a0f1a', borderRadius: 16, padding: 30, border: '1px solid #1e293b' }}>
      <div style={{ textAlign: 'center', marginBottom: 20 }}>
        <div style={{
          width: 120, height: 120, borderRadius: '50%', margin: '0 auto 20px',
          background: 'linear-gradient(135deg, #1a2744, #0f172a)', border: '3px solid #10b981',
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 60,
          boxShadow: isListening ? '0 0 40px rgba(239,68,68,0.4)' : '0 0 40px rgba(16,185,129,0.4)',
          animation: status === 'Speaking...' ? 'pulse-dot 2s infinite' : 'none'
        }}>
          ?????
        </div>
        <h2 style={{ color: '#fff' }}>Live Session</h2>
        <p style={{ color: '#64748b' }}>{status}</p>
      </div>

      <div style={{ height: 300, overflowY: 'auto', marginBottom: 20, padding: 10, border: '1px solid #1e293b', borderRadius: 8 }}>
        {history.map((msg, idx) => (
          <div key={idx} style={{ marginBottom: 10, textAlign: msg.role === 'user' ? 'right' : 'left' }}>
            <span style={{ 
              display: 'inline-block', padding: '8px 12px', borderRadius: 16,
              background: msg.role === 'user' ? '#3b82f6' : '#1e293b',
              color: '#fff', fontSize: 14
            }}>
              {msg.content}
            </span>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <button onClick={onCancel} style={{ padding: '10px 20px', background: 'transparent', border: '1px solid #ef4444', color: '#ef4444', borderRadius: 8, cursor: 'pointer' }}>
          End Session
        </button>
        {isListening ? (
          <button onClick={stopListening} style={{ padding: '10px 20px', background: '#ef4444', border: 'none', color: '#fff', borderRadius: 8, cursor: 'pointer', fontWeight: 'bold' }}>
            Stop & Send
          </button>
        ) : (
          <button onClick={startListening} disabled={status === 'Speaking...' || status === 'Connecting...'} style={{ padding: '10px 20px', background: '#10b981', border: 'none', color: '#fff', borderRadius: 8, cursor: status === 'Speaking...' ? 'not-allowed' : 'pointer' }}>
            Start Speaking
          </button>
        )}
      </div>
    </div>
  );
}
