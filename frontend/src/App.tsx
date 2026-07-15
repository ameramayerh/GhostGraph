import { useState, useEffect, useCallback, lazy, Suspense } from 'react';
import { HashRouter as Router, Routes, Route, Link, useParams, useNavigate } from 'react-router-dom';
import { Sidebar } from './components/layout/Sidebar';
import { TutorialOverlay } from './components/layout/TutorialOverlay';
import { CreateEngagementForm } from './components/engagements/CreateEngagementForm';
import { LiveTerminal } from './components/LiveTerminal';
import { apiUrl } from './lib/api';
import { errorMessage } from './lib/errors';
import type { Engagement, EngagementDetails } from './types/api';
import { Shield, FileText, Activity, Clock, Code } from 'lucide-react';
import { Toaster, toast } from 'sonner';

const AnalyticsDashboard = lazy(() => import('./components/analytics/AnalyticsDashboard').then((module) => ({ default: module.AnalyticsDashboard })));
const ThreatIntelView = lazy(() => import('./components/intel/ThreatIntelView').then((module) => ({ default: module.ThreatIntelView })));
const SettingsPage = lazy(() => import('./components/settings/SettingsPage').then((module) => ({ default: module.SettingsPage })));

function DashboardLayout() {
  const [engagements, setEngagements] = useState<Engagement[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [showTutorial, setShowTutorial] = useState(false);

  const fetchEngagements = async () => {
    try {
      const res = await fetch(apiUrl('/engagements'));
      if (res.ok) {
        const data = await res.json();
        setEngagements(data);
      }
    } catch (error) {
      console.error("Failed to fetch engagements", error);
    }
  };

  useEffect(() => {
    fetchEngagements();
  }, []);

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-neutral-950 text-gray-900 dark:text-gray-100 overflow-hidden font-sans">
      <Sidebar onTourClick={() => setShowTutorial(true)} />
      
      <main className="flex-1 overflow-y-auto">
        <header className="h-16 border-b border-gray-200 dark:border-neutral-800 bg-white/50 dark:bg-neutral-950/50 backdrop-blur-sm sticky top-0 z-10 px-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-sm font-semibold tracking-wide">Command Center</h1>
            <nav className="flex gap-4 ml-8">
              <Link to="/" className="text-sm text-gray-500 hover:text-gray-900 dark:hover:text-gray-100 transition-colors">Overview</Link>
              <Link to="/threat-intel" className="text-sm text-gray-500 hover:text-gray-900 dark:hover:text-gray-100 transition-colors">Threat Intel</Link>
            </nav>
          </div>
          <button 
            id="nav-engagements"
            onClick={() => setShowCreate(true)}
            className="px-4 py-1.5 bg-black dark:bg-white text-white dark:text-black rounded-md text-sm font-medium hover:bg-neutral-800 dark:hover:bg-neutral-200 transition-colors shadow-sm"
          >
            New Project Scan
          </button>
        </header>

        <div className="p-8 max-w-7xl mx-auto h-[calc(100vh-4rem)] flex flex-col">
          {showCreate ? (
            <div className="bg-white dark:bg-neutral-900 p-6 rounded-lg border border-gray-200 dark:border-neutral-800 shadow-sm">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold">New Source Code Scan</h2>
                <button onClick={() => setShowCreate(false)} className="text-sm text-gray-500 hover:text-gray-900">Cancel</button>
              </div>
              <CreateEngagementForm onSuccess={() => {
                setShowCreate(false);
                fetchEngagements();
              }} />
            </div>
          ) : (
            <Suspense fallback={<div className="p-6 text-gray-500">Loading view...</div>}>
              <Routes>
                <Route path="/analytics" element={<AnalyticsDashboard />} />
                <Route path="/threat-intel" element={<ThreatIntelView />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="/" element={<Overview engagements={engagements} />} />
                <Route path="/engagement/:id" element={<EngagementDetail />} />
              </Routes>
            </Suspense>
          )}
        </div>
        {showTutorial && <TutorialOverlay onClose={() => setShowTutorial(false)} />}
      </main>
      <Toaster position="top-right" richColors />
    </div>
  );
}

function Overview({ engagements }: { engagements: Engagement[] }) {
  const navigate = useNavigate();
  
  const totalFindings = engagements.reduce((sum, eng) => sum + (eng.total_findings || 0), 0);
  const reviewedFindings = engagements.reduce((sum, eng) => sum + (eng.filtered_findings || 0), 0);
  
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-gray-900 to-gray-500 dark:from-white dark:to-gray-400 bg-clip-text text-transparent">
            Dashboard Overview
          </h2>
          <p className="text-gray-500 mt-1">Monitor your security posture and active scans.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-neutral-900 p-6 rounded-2xl border border-gray-200 dark:border-neutral-800 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-gray-500 mb-4">
            <h3 className="font-medium text-sm">Active Projects</h3>
            <Activity className="w-5 h-5 text-indigo-500" />
          </div>
          <p className="text-4xl font-bold">{engagements.length}</p>
        </div>
        <div className="bg-white dark:bg-neutral-900 p-6 rounded-2xl border border-gray-200 dark:border-neutral-800 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-gray-500 mb-4">
            <h3 className="font-medium text-sm">Total Raw Findings</h3>
            <Shield className="w-5 h-5 text-orange-500" />
          </div>
          <p className="text-4xl font-bold">{totalFindings}</p>
        </div>
        <div className="bg-white dark:bg-neutral-900 p-6 rounded-2xl border border-gray-200 dark:border-neutral-800 shadow-sm flex flex-col justify-between relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 to-emerald-500/5" />
          <div className="relative flex items-center justify-between text-gray-500 mb-4">
            <h3 className="font-medium text-sm">Findings Review Progress</h3>
            <Activity className="w-5 h-5 text-green-500" />
          </div>
          <p className="relative text-4xl font-bold text-green-600 dark:text-green-400">{reviewedFindings}</p>
        </div>
      </div>

      <div>
        <h3 className="text-xl font-semibold mb-4">Recent Scans</h3>
        <div className="grid grid-cols-1 gap-4">
          {engagements.length === 0 ? (
            <div className="p-12 border-2 border-dashed border-gray-200 dark:border-neutral-800 rounded-2xl text-center">
              <Shield className="w-12 h-12 text-gray-300 dark:text-neutral-700 mx-auto mb-4" />
              <p className="text-gray-500 dark:text-gray-400">No active projects. Start by creating a New Project Scan.</p>
            </div>
          ) : (
            engagements.map(eng => (
              <div 
                key={eng.id} 
                className="group p-5 bg-white dark:bg-neutral-900 border border-gray-200 dark:border-neutral-800 rounded-xl flex items-center justify-between cursor-pointer hover:border-indigo-300 dark:hover:border-indigo-500/50 hover:shadow-md transition-all duration-200" 
                onClick={() => navigate(`/engagement/${eng.id}`)}
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-gray-100 dark:bg-neutral-800 flex items-center justify-center group-hover:bg-indigo-50 dark:group-hover:bg-indigo-500/10 transition-colors">
                    <FileText className="w-6 h-6 text-gray-500 group-hover:text-indigo-500 transition-colors" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg">{eng.name}</h3>
                    <p className="text-sm text-gray-500 mt-0.5">Authorized by {eng.authorized_by}</p>
                  </div>
                </div>
                <div className="text-right flex items-center gap-6">
                  <div className="hidden md:block text-sm text-gray-500">
                    <div>Scope</div>
                    <div className="font-medium text-gray-900 dark:text-gray-100 truncate max-w-[200px]">{eng.scope}</div>
                  </div>
                  <span className="inline-flex items-center rounded-full bg-green-50 dark:bg-green-500/10 px-3 py-1 text-xs font-medium text-green-700 dark:text-green-400 ring-1 ring-inset ring-green-600/20 shadow-sm">
                    {eng.status}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

function EngagementDetail() {
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState<'findings'|'audit'|'noise'>('findings');
  const [data, setData] = useState<EngagementDetails>({ findings: [], audit_logs: [] });
  const [analyzingId, setAnalyzingId] = useState<number | null>(null);

  const [uploading, setUploading] = useState(false);

  const fetchEngagementData = useCallback(async () => {
    try {
        const res = await fetch(apiUrl(`/engagements/${id}/details`));
      if (res.ok) {
        const details = await res.json();
        setData(details);
      }
    } catch (error) {
      console.error("Failed to fetch details", error);
    }
  }, [id]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    
    setUploading(true);
    const toastId = toast.loading('Uploading and extracting ZIP file...');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const res = await fetch(apiUrl(`/engagements/${id}/scan`), {
        method: 'POST',
        body: formData
      });
      
      if (!res.ok) {
        const errText = await res.text();
        throw new Error(errText || "Backend returned an error");
      }
      
      toast.success('Static analysis complete!', { id: toastId });
      fetchEngagementData();
    } catch (error: unknown) {
      toast.error(errorMessage(error, 'Scan failed.'), { id: toastId });
    } finally {
      setUploading(false);
      // Reset input
      e.target.value = '';
    }
  };

  const handleAnalyze = async (findingId: number) => {
    setAnalyzingId(findingId);
    const toastId = toast.loading('GhostGraph AI is reviewing this code snippet...');
    try {
      const res = await fetch(apiUrl(`/findings/${findingId}/analyze`), { method: 'POST' });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errData.detail || `Server returned ${res.status}`);
      }
      toast.success('AI review complete!', { id: toastId });
      fetchEngagementData();
    } catch (error: unknown) {
      toast.error(errorMessage(error, 'AI analysis failed.'), { id: toastId });
    } finally {
      setAnalyzingId(null);
    }
  };

  useEffect(() => {
    fetchEngagementData();
    // Poll every 3 seconds to catch background AI updates
    const interval = setInterval(() => {
      fetchEngagementData();
    }, 3000);
    return () => clearInterval(interval);
  }, [fetchEngagementData]);

  return (
    <div className="flex flex-col h-full gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight flex items-center gap-3">
            <Code className="text-indigo-500" />
            Static Analysis Dashboard
          </h2>
          <p className="text-sm text-gray-500 mt-1">Rule-based findings with optional AI guidance</p>
        </div>
        <div className="flex gap-3">
          <button 
            onClick={() => {
              const link = document.createElement('a');
              link.href = apiUrl(`/engagements/${id}/report/pdf`);
              link.download = `report_${id}.pdf`;
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);
            }}
            className="px-4 py-2 border border-gray-300 dark:border-neutral-700 hover:bg-gray-50 dark:hover:bg-neutral-800 rounded-md text-sm font-medium flex items-center gap-2 transition-colors"
          >
            <FileText size={16}/> Export Report
          </button>
          
          <label id="btn-upload-scan" className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md text-sm font-medium flex items-center gap-2 transition-colors shadow-sm cursor-pointer disabled:opacity-50">
            <Activity size={16} className={uploading ? "animate-pulse" : ""} />
            {uploading ? 'Scanning...' : 'Upload & Scan Source ZIP'}
            <input 
              type="file" 
              accept=".zip" 
              className="hidden" 
              onChange={handleUpload} 
              disabled={uploading}
            />
          </label>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
        <div className="lg:col-span-2 flex flex-col bg-white dark:bg-neutral-900 border border-gray-200 dark:border-neutral-800 rounded-lg overflow-hidden">
          <div className="flex border-b border-gray-200 dark:border-neutral-800">
            <button onClick={() => setActiveTab('findings')} className={`px-4 py-3 text-sm font-medium flex items-center gap-2 border-b-2 ${activeTab === 'findings' ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400' : 'border-transparent text-gray-500'}`}>
              <Shield size={16}/> Security Findings ({data.findings.filter((finding) => !finding.is_false_positive).length})
            </button>
            <button onClick={() => setActiveTab('noise')} className={`px-4 py-3 text-sm font-medium flex items-center gap-2 border-b-2 ${activeTab === 'noise' ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400' : 'border-transparent text-gray-500'}`}>
              <Activity size={16}/> Likely False Positives ({data.findings.filter((finding) => finding.is_false_positive).length})
            </button>
            <button onClick={() => setActiveTab('audit')} className={`px-4 py-3 text-sm font-medium flex items-center gap-2 border-b-2 ${activeTab === 'audit' ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400' : 'border-transparent text-gray-500'}`}>
              <Clock size={16}/> Scan History
            </button>
          </div>

          {data.engagement && data.engagement.total_findings > 0 && data.engagement.filtered_findings < data.engagement.total_findings && (
            <div className="bg-indigo-50 dark:bg-indigo-900/20 p-3 border-b border-indigo-100 dark:border-indigo-900/50">
              <div className="flex justify-between items-center mb-1.5">
                <span className="text-xs font-semibold text-indigo-700 dark:text-indigo-400 flex items-center gap-2">
                  <Activity size={12} className="animate-pulse" /> Optional AI Review in Progress...
                </span>
                <span className="text-xs font-medium text-indigo-700 dark:text-indigo-400">
                  {data.engagement.filtered_findings} / {data.engagement.total_findings} Findings Reviewed
                </span>
              </div>
              <div className="w-full bg-indigo-200 dark:bg-indigo-900/50 rounded-full h-2">
                <div 
                  className="bg-indigo-600 dark:bg-indigo-500 h-2 rounded-full transition-all duration-500" 
                  style={{ width: `${Math.round((data.engagement.filtered_findings / data.engagement.total_findings) * 100)}%` }}
                ></div>
              </div>
            </div>
          )}
          
          <div className="p-4 overflow-y-auto flex-1 custom-scrollbar bg-gray-50/50 dark:bg-neutral-950/50">
            {activeTab === 'findings' && (
              <div className="grid gap-4">
                {data.findings.filter((finding) => !finding.is_false_positive).length === 0 ? (
                  <div className="p-12 border-2 border-dashed border-gray-200 dark:border-neutral-800 rounded-xl text-center">
                    <p className="text-gray-500 dark:text-gray-400">No active vulnerabilities found or scan is in progress.</p>
                  </div>
                ) : (
                  data.findings.filter((finding) => !finding.is_false_positive).map((f) => (
                    <div key={f.id} className="p-4 bg-white dark:bg-neutral-900 border border-gray-200 dark:border-neutral-800 rounded-lg shadow-sm">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="flex items-center gap-3 mb-2">
                            <span className={`px-2 py-0.5 text-xs font-medium rounded-md ${f.severity === 'High' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' : 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400'}`}>{f.severity}</span>
                            <span className="text-sm font-medium text-gray-500">{f.file_path}:{f.line_number}</span>
                            {f.filtering_status === 'Pending' || f.filtering_status === 'In Progress' ? (
                              <span className="px-2 py-0.5 text-xs font-medium rounded-md bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 animate-pulse">AI Checking...</span>
                            ) : f.filtering_status === 'Reviewed' ? (
                              <span className="px-2 py-0.5 text-xs font-medium rounded-md bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">AI Reviewed</span>
                            ) : (
                              <span className="px-2 py-0.5 text-xs font-medium rounded-md bg-gray-100 text-gray-600 dark:bg-neutral-800 dark:text-gray-400">Human Review Required</span>
                            )}
                          </div>
                          <h4 className="font-semibold">{f.title}</h4>
                        </div>
                        {!f.ai_explanation && (
                          <button id="btn-ai-analyze" onClick={() => handleAnalyze(f.id)} disabled={analyzingId === f.id} className="px-3 py-1.5 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 dark:bg-indigo-900/30 dark:text-indigo-400 rounded-md text-sm font-medium transition-colors border border-indigo-200 dark:border-indigo-800 flex items-center gap-2">
                            {analyzingId === f.id ? (
                              <>
                                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                </svg>
                                Reviewing Code...
                              </>
                            ) : 'Request AI Explanation'}
                          </button>
                        )}
                      </div>

                      <div className="mt-3">
                         <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">{f.description}</p>
                         <div className="bg-[#1e1e1e] p-3 rounded-md overflow-x-auto border border-neutral-800">
                           <pre className="text-sm text-gray-300 font-mono">
                             <code>{f.code_snippet}</code>
                           </pre>
                         </div>
                      </div>
                      
                      {f.ai_explanation && (
                        <div className="mt-4 pt-4 border-t border-gray-100 dark:border-neutral-800 grid gap-4 lg:grid-cols-2">
                          <div className="bg-blue-50/50 dark:bg-blue-950/20 p-4 rounded-lg border border-blue-100 dark:border-blue-900/50">
                            <h5 className="text-xs font-bold text-blue-800 dark:text-blue-300 uppercase mb-2">Vulnerability Explanation</h5>
                            <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{f.ai_explanation}</p>
                          </div>
                          <div className="bg-orange-50/50 dark:bg-orange-950/20 p-4 rounded-lg border border-orange-100 dark:border-orange-900/50">
                            <h5 className="text-xs font-bold text-orange-800 dark:text-orange-300 uppercase mb-2">Business Impact</h5>
                            <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{f.business_impact}</p>
                          </div>
                          <div className="lg:col-span-2 bg-green-50/50 dark:bg-green-950/20 p-4 rounded-lg border border-green-100 dark:border-green-900/50">
                            <h5 className="text-xs font-bold text-green-800 dark:text-green-300 uppercase mb-2">Secure Refactoring Recommendation (Confidence: {f.confidence_level})</h5>
                            <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{f.remediation}</p>
                            {f.code_patch && (
                              <pre className="mt-2 p-3 bg-neutral-900 text-green-400 rounded-md border border-neutral-800 text-sm overflow-x-auto font-mono">
                                {f.code_patch}
                              </pre>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            )}

            {activeTab === 'noise' && (
              <div className="grid gap-4">
                {data.findings.filter((finding) => finding.is_false_positive).length === 0 ? (
                  <div className="p-12 border-2 border-dashed border-gray-200 dark:border-neutral-800 rounded-xl text-center">
                    <p className="text-gray-500 dark:text-gray-400">No false positives detected yet.</p>
                  </div>
                ) : (
                  data.findings.filter((finding) => finding.is_false_positive).map((f) => (
                    <div key={f.id} className="p-4 bg-gray-50 dark:bg-neutral-900/50 border border-gray-200 dark:border-neutral-800 rounded-lg shadow-sm opacity-75">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="flex items-center gap-3 mb-2">
                            <span className="px-2 py-0.5 text-xs font-medium rounded-md bg-gray-200 text-gray-700 dark:bg-neutral-800 dark:text-gray-400">False Positive</span>
                            <span className="text-sm font-medium text-gray-500 line-through">{f.file_path}:{f.line_number}</span>
                            <span className="px-2 py-0.5 text-xs font-medium rounded-md bg-green-100 text-green-700">AI Flagged</span>
                          </div>
                          <h4 className="font-semibold text-gray-600 dark:text-gray-400">{f.title}</h4>
                        </div>
                      </div>
                      <div className="mt-3">
                         <p className="text-sm text-gray-500 italic mb-3">Marked as a likely false positive by optional AI review. Human verification is still required.</p>
                         <div className="bg-[#1e1e1e] p-3 rounded-md overflow-x-auto border border-neutral-800 opacity-50">
                           <pre className="text-sm text-gray-300 font-mono">
                             <code>{f.code_snippet}</code>
                           </pre>
                         </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
            
            {activeTab === 'audit' && (
              <div className="space-y-4">
                {data.audit_logs.map((log) => (
                  <div key={log.id} className="flex gap-4 p-4 bg-white dark:bg-neutral-900 border border-gray-200 dark:border-neutral-800 rounded-lg shadow-sm">
                    <div className="mt-1">
                      <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400">
                        <Clock size={16} />
                      </div>
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h4 className="font-semibold">{log.action}</h4>
                        <span className="text-xs text-gray-500 font-mono">{new Date(log.timestamp).toLocaleString()}</span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{log.details}</p>
                      <p className="text-xs text-gray-500 mt-2">Actor: {log.user}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Live Terminal Widget */}
        <div className="lg:col-span-1 h-full">
          <LiveTerminal />
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <DashboardLayout />
    </Router>
  );
}
