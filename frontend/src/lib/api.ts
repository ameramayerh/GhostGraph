const configuredApiUrl = import.meta.env.VITE_API_URL?.replace(/\/$/, '');

export const API_BASE_URL = configuredApiUrl || 'http://127.0.0.1:8000';

export function apiUrl(path: string): string {
  return `${API_BASE_URL}/api${path}`;
}

export const logsWebSocketUrl = `${API_BASE_URL.replace(/^http/, 'ws')}/api/ws/logs`;
