import React, { useEffect, useState, useRef } from 'react';
import { Activity, Trash2 } from 'lucide-react';
import { logsWebSocketUrl } from '../lib/api';

type ActivityLevel = 'info' | 'success' | 'warning' | 'error';

interface LogMessage {
  level: ActivityLevel;
  message: string;
  timestamp: Date;
  repeats: number;
}

const MAX_VISIBLE_EVENTS = 25;
const MAX_MESSAGE_LENGTH = 180;

const normalizeLevel = (level: unknown): ActivityLevel =>
  level === 'success' || level === 'warning' || level === 'error' ? level : 'info';

const levelColor: Record<ActivityLevel, string> = {
  error: 'text-red-400',
  warning: 'text-yellow-400',
  success: 'text-green-400',
  info: 'text-blue-300',
};

const cleanMessage = (message: unknown): string => {
  const value = typeof message === 'string' ? message : 'Scan activity updated.';
  const singleLine = value.replace(/\s+/g, ' ').trim();
  return singleLine.length > MAX_MESSAGE_LENGTH
    ? `${singleLine.slice(0, MAX_MESSAGE_LENGTH - 1)}…`
    : singleLine;
};

export const LiveTerminal: React.FC = () => {
  const [logs, setLogs] = useState<LogMessage[]>([]);
  const ws = useRef<WebSocket | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    ws.current = new WebSocket(logsWebSocketUrl);
    
    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLogs((previous) => {
          const message = cleanMessage(data.message);
          const level = normalizeLevel(data.level);
          const last = previous[previous.length - 1];

          if (last?.message === message && last.level === level) {
            return [
              ...previous.slice(0, -1),
              { ...last, timestamp: new Date(), repeats: last.repeats + 1 },
            ];
          }

          return [...previous, {
            level,
            message,
            timestamp: new Date(),
            repeats: 1,
          }].slice(-MAX_VISIBLE_EVENTS);
        });
      } catch {
        console.error('Invalid scan activity payload');
      }
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="bg-neutral-950 border border-neutral-800 rounded-lg overflow-hidden flex flex-col h-full">
      <div className="bg-neutral-900 border-b border-neutral-800 px-4 py-2 flex items-center gap-2">
        <Activity size={14} className="text-blue-400" />
        <span className="text-xs text-gray-300 font-medium">Scan Activity</span>
        <span className="text-[10px] text-gray-500">latest {MAX_VISIBLE_EVENTS}</span>
        <button
          type="button"
          onClick={() => setLogs([])}
          disabled={logs.length === 0}
          className="ml-auto inline-flex items-center gap-1 text-[11px] text-gray-500 hover:text-gray-200 disabled:opacity-40 disabled:cursor-not-allowed"
          aria-label="Clear scan activity"
        >
          <Trash2 size={12} />
          Clear
        </button>
      </div>
      <div ref={containerRef} className="p-4 overflow-y-auto flex-1 font-mono text-xs space-y-1.5 custom-scrollbar">
        {logs.length === 0 ? (
          <div className="text-gray-600 italic">Scan updates will appear here.</div>
        ) : (
          logs.map((log, i) => (
            <div key={i} className="flex gap-3">
              <span className="text-gray-500 shrink-0">
                [{log.timestamp.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}]
              </span>
              <span className={levelColor[log.level]}>
                {log.message}
                {log.repeats > 1 && <span className="ml-2 text-gray-500">×{log.repeats}</span>}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
