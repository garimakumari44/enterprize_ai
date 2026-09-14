"use client"
import { useState, useRef, useEffect, type ReactNode } from 'react';
import { Search, Bell, ChevronDown, Sun, Moon, Menu, Check, LogOut } from 'lucide-react';
import { useTheme } from '../../../context/ThemeContext';
import { useAuth } from '../../../context/AuthContext';
import { useNav } from '../../../context/NavContext';
import type { PageKey } from '../../../types';

const pageTitles: Record<PageKey, { title: string; subtitle: string }> = {
  dashboard: { title: 'Enterprise Document Intelligence', subtitle: 'AI-powered document automation and intelligent workflows' },
  documents: { title: 'Document Library', subtitle: 'Search, filter, and manage all processed documents' },
  upload: { title: 'Upload Documents', subtitle: 'Upload files to process with AI workflows' },
  workflows: { title: 'AI Workflows', subtitle: 'Automated document intelligence pipelines' },
  executions: { title: 'Execution History', subtitle: 'Track AI workflow runs and processing timelines' },
  knowledge: { title: 'Knowledge Search', subtitle: 'Search across all enterprise documents' },
  assistant: { title: 'AI Assistant', subtitle: 'Ask questions about your documents' },
  review: { title: 'Human Review', subtitle: 'Review AI-flagged documents before approval' },
  analytics: { title: 'Analytics', subtitle: 'Business intelligence and processing metrics' },
  settings: { title: 'Settings', subtitle: 'Workspace, profile, and integration configuration' },
};



export function DashboardHeader({ onOpenMobile }: { onOpenMobile: () => void }) {
  const { theme, toggle } = useTheme();
  const { user, signOut } = useAuth();
  const { page } = useNav();
  const [wsOpen, setWsOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const wsRef = useRef<HTMLDivElement>(null);
  const notifRef = useRef<HTMLDivElement>(null);
  const profileRef = useRef<HTMLDivElement>(null);

  const { title, subtitle } = pageTitles[page];

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (wsRef.current && !wsRef.current.contains(e.target as Node)) setWsOpen(false);
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) setNotifOpen(false);
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) setProfileOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/80 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-900/80">
      <div className="flex h-16 items-center gap-3 px-4 lg:px-6">
        {/* Mobile menu */}
        <button
          onClick={onOpenMobile}
          className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 lg:hidden dark:hover:bg-slate-800"
        >
          <Menu size={20} />
        </button>

        {/* Title */}
        <div className="min-w-0 flex-1 lg:flex-none">
          <h1 className="truncate text-base font-semibold text-slate-900 dark:text-white lg:text-lg">{title}</h1>
          <p className="hidden truncate text-xs text-slate-500 dark:text-slate-400 sm:block">{subtitle}</p>
        </div>

        {/* Search */}
        <div className="hidden flex-1 justify-center px-4 md:flex lg:max-w-md">
          <div className="group relative w-full max-w-sm">
            <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              placeholder="Search documents…"
              className="w-full rounded-lg border border-slate-200 bg-slate-50 py-2 pl-9 pr-16 text-sm text-slate-700 placeholder:text-slate-400 transition-all focus:border-cyan-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-cyan-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:focus:bg-slate-800"
            />
            <kbd className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded border border-slate-200 bg-white px-1.5 py-0.5 text-[10px] font-medium text-slate-400 dark:border-slate-600 dark:bg-slate-700">⌘K</kbd>
          </div>
        </div>

        {/* Right cluster */}
        <div className="flex items-center gap-3">
          {/* Theme toggle */}
         
          

          {/* Profile */}
          <div className="relative" ref={profileRef}>
            <button
              onClick={() => setProfileOpen((o) => !o)}
              className="flex items-center gap-2 rounded-lg p-1 transition-colors hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <span className="grid h-8 w-8 place-items-center rounded-full bg-gradient-to-br from-slate-700 to-slate-900 text-xs font-bold text-white dark:from-cyan-500 dark:to-teal-600">
                {user?.email?.charAt(0).toUpperCase() ?? 'U'}
              </span>
              <ChevronDown size={14} className={`hidden text-slate-400 transition-transform sm:block ${profileOpen ? 'rotate-180' : ''}`} />
            </button>
            {profileOpen && (
              <Dropdown>
                <div className="border-b border-slate-100 px-4 py-3 dark:border-slate-800">
                  <p className="truncate text-sm font-medium text-slate-900 dark:text-white">{user?.email}</p>
                  <p className="text-xs text-slate-400">Workspace Admin</p>
                </div>
                <button onClick={signOut} className="flex w-full items-center gap-2 px-4 py-2.5 text-sm text-slate-700 transition-colors hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-800">
                  <LogOut size={15} className="text-slate-400" />
                  Sign out
                </button>
              </Dropdown>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

function Dropdown({ children }: { children: ReactNode }) {
  return (
    <div className="absolute right-0 top-full z-50 mt-2 w-72 origin-top-right rounded-xl border border-slate-200 bg-white shadow-xl shadow-slate-900/10 animate-scale-in dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/30">
      {children}
    </div>
  );
}
