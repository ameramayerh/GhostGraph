import React, { useState } from 'react';
import { ShieldAlert, CheckCircle2 } from 'lucide-react';

interface Engagement {
  name: string;
  scope: string;
  authorized_by: string;
}

export function CreateEngagementForm({ onSuccess }: { onSuccess: () => void }) {
  const [formData, setFormData] = useState<Engagement>({ name: '', scope: '', authorized_by: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://127.0.0.1:8000/api/engagements', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create engagement');
      }

      onSuccess();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl w-full bg-white dark:bg-neutral-900 border border-gray-200 dark:border-neutral-800 rounded-xl p-8 shadow-sm">
      <div className="mb-8 border-b border-gray-100 dark:border-neutral-800 pb-5">
        <h2 className="text-xl font-semibold mb-1">Create Project Scan</h2>
        <p className="text-sm text-gray-500">Explicit authorization is required to perform static analysis on source code.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-2">
          <label className="text-sm font-medium">Project Name</label>
          <input
            type="text"
            required
            placeholder="e.g., Q3 Web Application Assessment"
            className="w-full px-3 py-2 bg-transparent border border-gray-300 dark:border-neutral-700 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Project Description</label>
          <textarea
            required
            rows={3}
            placeholder="e.g., Main frontend repository or monorepo"
            className="w-full px-3 py-2 bg-transparent border border-gray-300 dark:border-neutral-700 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            value={formData.scope}
            onChange={(e) => setFormData({ ...formData, scope: e.target.value })}
          />
          <p className="text-xs text-gray-500">A brief description of the source code being analyzed.</p>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Authorized By (Full Name)</label>
          <input
            type="text"
            required
            placeholder="John Doe, CISO"
            className="w-full px-3 py-2 bg-transparent border border-gray-300 dark:border-neutral-700 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            value={formData.authorized_by}
            onChange={(e) => setFormData({ ...formData, authorized_by: e.target.value })}
          />
        </div>

        {error && (
          <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-950/30 text-red-600 dark:text-red-400 rounded-md text-sm">
            <ShieldAlert className="w-4 h-4" />
            <span>{error}</span>
          </div>
        )}

        <div className="pt-4 border-t border-gray-100 dark:border-neutral-800 flex justify-end gap-3">
          <button type="button" className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-neutral-800 rounded-md">
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md disabled:opacity-50"
          >
            <CheckCircle2 className="w-4 h-4" />
            {loading ? 'Creating...' : 'Confirm Authorization & Create'}
          </button>
        </div>
      </form>
    </div>
  );
}
