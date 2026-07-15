import { useEffect, useState } from 'react';
import { Save, Cpu, Key } from 'lucide-react';
import { toast } from 'sonner';
import { apiUrl } from '../../lib/api';

export function SettingsPage() {
  const [llmProvider, setLlmProvider] = useState('local-llama3');
  const [apiKey, setApiKey] = useState('');
  const [hasSavedApiKey, setHasSavedApiKey] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(apiUrl('/settings'))
      .then(res => res.json())
      .then(data => {
        setLlmProvider(data.llm_provider || 'local-llama3');
        setHasSavedApiKey(Boolean(data.has_api_key));
        setLoading(false);
      })
      .catch(() => {
        toast.error("Failed to load settings from DB");
        setLoading(false);
      });
  }, []);

  const handleSave = async () => {
    const payload = {
      llm_provider: llmProvider,
      api_key: apiKey
    };
    
    try {
      const res = await fetch(apiUrl('/settings'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error("Failed to save settings");
      setHasSavedApiKey(Boolean(apiKey) || hasSavedApiKey);
      setApiKey('');
      toast.success('Configuration saved successfully. New scans will use the selected provider.');
    } catch (e: any) {
      toast.error(e.message);
    }
  };

  if (loading) return <div className="p-6 text-gray-500">Loading Configuration...</div>;

  return (
    <div className="flex flex-col h-full space-y-6 max-w-4xl">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">System Configuration</h2>
        <p className="text-sm text-gray-500 mt-1">Manage Multi-Agent AI providers and scanning engine thresholds.</p>
      </div>

      <div className="space-y-6">
        {/* AI Engine Settings */}
        <div className="bg-white dark:bg-neutral-900 border border-gray-200 dark:border-neutral-800 rounded-xl overflow-hidden shadow-sm">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-neutral-800 bg-gray-50 dark:bg-neutral-950 flex items-center gap-2">
            <Cpu size={18} className="text-gray-500" />
            <h3 className="font-semibold">AI Orchestration Engine</h3>
          </div>
          <div className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Primary LLM Provider</label>
              <select 
                value={llmProvider}
                onChange={(e) => setLlmProvider(e.target.value)}
                className="w-full bg-gray-50 dark:bg-neutral-950 border border-gray-300 dark:border-neutral-700 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="local-llama3">Local (Ollama / Llama 3 8B) - Recommended for Privacy</option>
                <option value="local-mistral">Local (Ollama / Mistral 7B)</option>
                <option value="openai-gpt4">Cloud (OpenAI GPT-4o) - Requires API Key</option>
                <option value="anthropic-claude">Cloud (Anthropic Claude 3.5 Sonnet)</option>
                <option value="cloud-gemini-2.5-flash">Cloud (Google Gemini 2.5 Flash) - Requires API Key</option>
              </select>
            </div>
            
            {['openai-gpt4', 'anthropic-claude', 'cloud-gemini-2.5-flash'].includes(llmProvider) && (
              <div>
                <label className="block text-sm font-medium mb-2 flex items-center gap-2">
                  <Key size={14} /> API Key
                </label>
                <input 
                  type="password" 
                  placeholder="sk-..."
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="w-full bg-gray-50 dark:bg-neutral-950 border border-gray-300 dark:border-neutral-700 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
                />
                {hasSavedApiKey && !apiKey && <p className="mt-2 text-xs text-green-600 dark:text-green-400">An API key is already saved. Enter a new value only to replace it.</p>}
              </div>
            )}
          </div>
        </div>

        <div className="flex justify-end pt-4">
          <button 
            onClick={handleSave}
            className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md shadow-sm font-medium transition-colors"
          >
            <Save size={16} />
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
}
