"use client"
import { useState } from 'react';
import { AppSidebar } from './AppSidebar';
import { DashboardHeader } from './DashboardHeader';
import { DashboardHome } from './DashboardHome';
import { DocumentsPage } from './DocumentsPage';
import { DocumentViewer } from './DocumentViewer';
import { UploadPage } from './UploadPage';
import { WorkflowsPage } from './WorkflowsPage';
import { ExecutionsPage } from './ExecutionsPage';
import { KnowledgeSearchPage } from './KnowledgeSearchPage';
import { AIAssistantPage } from './AIAssistantPage';
import { HumanReviewPage } from './HumanReviewPage';
import { AnalyticsPage } from './AnalyticsPage';
import { SettingsPage } from './SettingsPage';
import { useNav } from '../../../context/NavContext';

export function Dashboard() {
  const { page, selectedDocId } = useNav();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const renderPage = () => {
    if (page === 'documents' && selectedDocId) return <DocumentViewer docId={selectedDocId} />;
    switch (page) {
      case 'dashboard': return <DashboardHome />;
      case 'documents': return <DocumentsPage />;
      case 'upload': return <UploadPage />;
      case 'workflows': return <WorkflowsPage />;
      case 'executions': return <ExecutionsPage />;
      case 'knowledge': return <KnowledgeSearchPage />;
      case 'assistant': return <AIAssistantPage />;
      case 'review': return <HumanReviewPage />;
      case 'analytics': return <AnalyticsPage />;
      case 'settings': return <SettingsPage />;
      default: return <DashboardHome />;
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 dark:bg-slate-950">
      <AppSidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed((c) => !c)}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
      />
      <div className="flex flex-1 flex-col overflow-hidden">
        <DashboardHeader onOpenMobile={() => setMobileOpen(true)} />
        <main className="flex-1 overflow-y-auto px-4 py-6 lg:px-6">
          <div className="mx-auto max-w-6xl">
            {renderPage()}
          </div>
        </main>
      </div>
    </div>
  );
}
