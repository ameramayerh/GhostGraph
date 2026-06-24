import React, { useEffect, useState, useRef } from 'react';
import { Terminal } from 'lucide-react';

interface LogMessage {
  level: string;
  message: string;
  timestamp: Date;
}

export const LiveTerminal: React.FC = () => {
  const [logs, setLogs] = useState<LogMessage[]>([]);
  const ws = useRef<WebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    ws.current = new WebSocket('ws://127.0.0.1:8000/ws/logs');
    
    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLogs(prev => [...prev, {
          level: data.level,
          message: data.message,
          timestamp: new Date()
        }]);
      } catch (e) {
        console.error("Invalid WS payload", event.data);
      }
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <div className="bg-neutral-950 border border-neutral-800 rounded-lg overflow-hidden flex flex-col h-full">
      <div className="bg-neutral-900 border-b border-neutral-800 px-4 py-2 flex items-center gap-2">
        <Terminal size={14} className="text-gray-400" />
        <span className="text-xs font-mono text-gray-400 font-medium">Engine Logs (Live)</span>
        <div className="ml-auto flex gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500/20 border border-red-500/50"></div>
          <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/20 border border-yellow-500/50"></div>
          <div className="w-2.5 h-2.5 rounded-full bg-green-500/50 shadow-[0_0_8px_rgba(34,197,94,0.4)]"></div>
        </div>
      </div>
      <div className="p-4 overflow-y-auto flex-1 font-mono text-xs space-y-1.5 custom-scrollbar">
        {logs.length === 0 ? (
          <div className="text-gray-600 italic">Listening for raw engine telemetry...</div>
        ) : (
          logs.map((log, i) => (
            <div key={i} className="flex gap-3">
              <span className="text-gray-500 shrink-0">
                [{log.timestamp.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}]
              </span>
              <span className={`
                ${log.level === 'error' ? 'text-red-400' : ''}
                ${log.level === 'warning' ? 'text-yellow-400' : ''}
                ${log.level === 'success' ? 'text-green-400' : ''}
                ${log.level === 'info' ? 'text-blue-300' : 'text-gray-300'}
              `}>
                {log.message}
              </span>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};
