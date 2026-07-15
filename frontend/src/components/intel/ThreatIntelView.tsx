import { useEffect, useState } from 'react';
import { Database, Search, ShieldCheck } from 'lucide-react';
import { toast } from 'sonner';
import { apiUrl } from '../../lib/api';

export function ThreatIntelView() {
  const [query, setQuery] = useState('');
  const [intelData, setIntelData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(apiUrl('/threat-intel'))
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch threat intel');
        return res.json();
      })
      .then(json => {
        setIntelData(json);
        setLoading(false);
      })
      .catch(err => {
        toast.error(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div className="flex flex-col h-full space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight flex items-center gap-3">
          <Database className="text-purple-500" />
          Threat Intelligence (RAG Context)
        </h2>
        <p className="text-sm text-gray-500 mt-1">Live vector database viewer. This data provides grounding context to the Multi-Agent engine.</p>
      </div>

      <div className="bg-white dark:bg-neutral-900 border border-gray-200 dark:border-neutral-800 rounded-xl p-6 shadow-sm">
        <div className="relative mb-6">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-neutral-700 rounded-md leading-5 bg-transparent placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
            placeholder="Simulate Semantic Vector Search (e.g. 'SSH exploit')..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>

        <div className="space-y-4">
          <div className="grid grid-cols-12 gap-4 px-4 py-2 bg-gray-50 dark:bg-neutral-950 border border-gray-200 dark:border-neutral-800 rounded-t-md text-xs font-medium text-gray-500 uppercase tracking-wider">
            <div className="col-span-2">ID</div>
            <div className="col-span-2">Source</div>
            <div className="col-span-3">Type</div>
            <div className="col-span-5">Description Extract</div>
          </div>
          
          <div className="divide-y divide-gray-200 dark:divide-neutral-800">
            {loading ? (
               <div className="p-4 text-gray-500">Connecting to ChromaDB Vector Store...</div>
            ) : intelData.filter(i => i.id.toLowerCase().includes(query.toLowerCase()) || i.description.toLowerCase().includes(query.toLowerCase())).map((intel) => (
              <div key={intel.id} className="grid grid-cols-12 gap-4 px-4 py-3 items-start hover:bg-gray-50 dark:hover:bg-neutral-800/50 transition-colors">
                <div className="col-span-2 font-mono text-sm font-medium text-purple-600 dark:text-purple-400">{intel.id}</div>
                <div className="col-span-2">
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800 dark:bg-neutral-800 dark:text-gray-300 border border-gray-200 dark:border-neutral-700">
                    {intel.source}
                  </span>
                </div>
                <div className="col-span-3 text-sm">{intel.type}</div>
                <div className="col-span-5 text-sm text-gray-600 dark:text-gray-400 line-clamp-2">{intel.description}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-6 flex items-center justify-between border-t border-gray-200 dark:border-neutral-800 pt-4">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <ShieldCheck size={16} className="text-green-500" />
            <span>ChromaDB Connection Active</span>
          </div>
          <p className="text-sm text-gray-500">Showing {intelData.length} ingested threat vectors</p>
        </div>
      </div>
    </div>
  );
}
