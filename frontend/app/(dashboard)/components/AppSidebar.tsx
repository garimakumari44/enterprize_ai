"use client"
import {
  LayoutDashboard,
  FileText,
  Upload,
  Workflow,
  Activity,
  Search,
  Bot,
  ClipboardCheck,
  BarChart3,
  Settings,
  ChevronLeft,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import type { PageKey } from '../../../types';
import { useNav } from '../../../context/NavContext';
import { Logo } from './Logo';

type NavItem = { key: PageKey; label: string; icon: LucideIcon; badge?: number };

const workspaceNav: NavItem[] = [
  { key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { key: 'documents', label: 'Documents', icon: FileText },
  { key: 'upload', label: 'Upload', icon: Upload },
  { key: 'workflows', label: 'Workflows', icon: Workflow },
  { key: 'executions', label: 'Executions', icon: Activity },
  { key: 'knowledge', label: 'Knowledge', icon: Search },
  { key: 'assistant', label: 'AI Assistant', icon: Bot },
  { key: 'review', label: 'Human Review', icon: ClipboardCheck, badge: 12 },
  { key: 'analytics', label: 'Analytics', icon: BarChart3 },
];

const settingsNav: NavItem[] = [{ key: 'settings', label: 'Settings', icon: Settings }];

export function AppSidebar({ collapsed, onToggle, mobileOpen, onCloseMobile }: {
  collapsed: boolean;
  onToggle: () => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}) {
  const { page, setPage } = useNav();

  const go = (key: PageKey) => {
    setPage(key);
    onCloseMobile();
  };

  const renderItem = (item: NavItem) => {
    const active = page === item.key;
    const Icon = item.icon;
    return (
      <button
        key={item.key}
        onClick={() => go(item.key)}
        className={`group relative flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all ${
          active
            ? 'bg-cyan-50 text-cyan-700 dark:bg-cyan-500/10 dark:text-cyan-300'
            : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'
        } ${collapsed ? 'justify-center' : ''}`}
      >
        {active && (
          <span className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-gradient-to-b from-cyan-400 to-teal-500" />
        )}
        <Icon size={18} strokeWidth={2} className="shrink-0" />
        {!collapsed && <span className="flex-1 text-left">{item.label}</span>}
        {!collapsed && item.badge && (
          <span className="rounded-full bg-amber-100 px-1.5 py-0.5 text-[10px] font-bold text-amber-700 dark:bg-amber-500/15 dark:text-amber-400">
            {item.badge}
          </span>
        )}
        {collapsed && item.badge && (
          <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-amber-500" />
        )}
      </button>
    );
  };

  const sidebarContent = (
    <div className="flex h-full flex-col">
      {/* Logo / collapse */}
      <div className={`flex items-center border-b border-slate-200 dark:border-slate-800 ${collapsed ? 'px-3 py-4' : 'px-5 py-4'}`}>
        <div className={`flex items-center ${collapsed ? 'w-full justify-center' : 'flex-1'}`}>
          {collapsed ? (
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-sky-400 via-cyan-500 to-teal-500 shadow-lg shadow-cyan-500/30">
              <FileText size={20} className="text-white" strokeWidth={2.2} />
            </div>
          ) : (
            <Logo variant="dark" size="md" />
          )}
        </div>
        {!collapsed && (
          <button
            onClick={onToggle}
            className="hidden rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 lg:block dark:hover:bg-slate-800"
          >
            <ChevronLeft size={18} />
          </button>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        {!collapsed && (
          <div className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.15em] text-slate-400 dark:text-slate-600">
            Workspace
          </div>
        )}
        <div className="space-y-1">
          {workspaceNav.map(renderItem)}
        </div>

        {!collapsed && (
          <div className="mb-2 mt-6 px-3 text-[10px] font-semibold uppercase tracking-[0.15em] text-slate-400 dark:text-slate-600">
            Settings
          </div>
        )}
        <div className={`space-y-1 ${collapsed ? 'mt-4' : 'mt-3'}`}>
          {settingsNav.map(renderItem)}
        </div>
      </nav>

      {/* Status footer */}
      {!collapsed && (
        <div className="border-t border-slate-200 p-4 dark:border-slate-800">
          <div className="rounded-lg bg-gradient-to-br from-slate-50 to-slate-100 p-3 dark:from-slate-800/50 dark:to-slate-900">
            <div className="flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
              </span>
              <span className="text-xs font-medium text-slate-700 dark:text-slate-300">Engine operational</span>
            </div>
            <p className="mt-1 text-[10px] text-slate-400">All AI workflows running normally</p>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Desktop */}
      <aside
        className={`relative z-30 hidden shrink-0 border-r border-slate-200 bg-white transition-all duration-300 dark:border-slate-800 dark:bg-slate-900 lg:block ${
          collapsed ? 'w-[72px]' : 'w-64'
        }`}
      >
        {sidebarContent}
        {collapsed && (
          <button
            onClick={onToggle}
            className="absolute -right-3 top-20 grid h-6 w-6 place-items-center rounded-full border border-slate-200 bg-white text-slate-400 shadow-sm transition-colors hover:text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:hover:text-white"
          >
            <ChevronLeft size={14} className="rotate-180" />
          </button>
        )}
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm animate-fade-in" onClick={onCloseMobile} />
          <aside className="absolute left-0 top-0 h-full w-64 border-r border-slate-200 bg-white animate-slide-in-right dark:border-slate-800 dark:bg-slate-900">
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  );
}
