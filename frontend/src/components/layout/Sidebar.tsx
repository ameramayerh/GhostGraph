import React from 'react';
import { Shield, LayoutDashboard, History, Settings, PieChart, Database, HelpCircle } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

export function Sidebar({ onTourClick }: { onTourClick?: () => void }) {
  const location = useLocation();
  const isActive = (path: string) => location.pathname === path ? "bg-gray-200 dark:bg-neutral-800 text-gray-900 dark:text-gray-100" : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-neutral-800";

  return (
    <aside className="w-64 border-r border-gray-200 dark:border-neutral-800 bg-gray-50 dark:bg-neutral-900 h-screen flex flex-col">
      <div className="p-6 flex items-center gap-3">
        <Shield className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
        <span className="font-semibold text-lg tracking-tight">GhostGraph</span>
      </div>
      <nav className="flex-1 px-4 space-y-1">
        <Link to="/" className={`flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md ${isActive('/')}`}>
          <LayoutDashboard className="w-4 h-4" />
          Engagements
        </Link>
        <Link to="/analytics" className={`flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md ${isActive('/analytics')}`}>
          <PieChart className="w-4 h-4" />
          Analytics
        </Link>
        <Link to="/threat-intel" className={`flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md ${isActive('/threat-intel')}`}>
          <Database className="w-4 h-4" />
          Threat Intel (RAG)
        </Link>
        <Link to="/settings" id="nav-settings" className={`flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md ${isActive('/settings')}`}>
          <Settings className="w-4 h-4" />
          Settings
        </Link>
      </nav>
      <div className="p-4 border-t border-gray-200 dark:border-neutral-800">
        {onTourClick && (
          <button 
            onClick={onTourClick}
            className="flex items-center w-full px-3 py-2 mb-2 text-sm font-medium rounded-md text-blue-600 dark:text-blue-400 hover:bg-gray-100 dark:hover:bg-neutral-800"
          >
            <HelpCircle className="w-4 h-4 mr-3" />
            Take a Tour
          </button>
        )}
        <div className="text-xs text-gray-500">Authorized Environments Only</div>
      </div>
    </aside>
  );
}
