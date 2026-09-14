"use client"
import { useState } from 'react';
import { User, Cpu, Key, Plug, Building2, Save, Eye, EyeOff, Check } from 'lucide-react';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import { useAuth } from '../../../context/AuthContext';

type Tab = 'workspace' | 'profile' | 'ai' | 'api' | 'integrations';

const tabs: { key: Tab; label: string; icon: typeof User }[] = [
  { key: 'workspace', label: 'Workspace', icon: Building2 },
  { key: 'profile', label: 'User Profile', icon: User },
  { key: 'ai', label: 'AI Model', icon: Cpu },
  { key: 'api', label: 'API Keys', icon: Key },
  { key: 'integrations', label: 'Integrations', icon: Plug },
];

export function SettingsPage() {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>('workspace');
  const [showKey, setShowKey] = useState(false);
  const [saved, setSaved] = useState(false);

  const save = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="grid grid-cols-1 gap-4 animate-fade-in lg:grid-cols-[200px_1fr]">
      {/* Tabs */}
      <Card className="h-fit p-2">
        {tabs.map((t) => {
          const Icon = t.icon;
          return (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-all ${
                tab === t.key
                  ? 'bg-cyan-50 text-cyan-700 dark:bg-cyan-500/10 dark:text-cyan-300'
                  : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800'
              }`}
            >
              <Icon size={16} /> {t.label}
            </button>
          );
        })}
      </Card>

      {/* Content */}
      <Card className="p-6">
        {tab === 'workspace' && (
          <div className="space-y-5">
            <SectionTitle title="Workspace Settings" desc="Configure your organization workspace" />
            <Field label="Workspace Name" value="Acme Enterprise" />
            <Field label="Industry" value="Technology" />
            <div className="grid grid-cols-2 gap-4">
              <Field label="Default Language" value="English (US)" />
              <Field label="Timezone" value="UTC-08:00 Pacific" />
            </div>
            <Toggle label="Auto-approve high-confidence results" desc="Documents above 95% confidence skip review" defaultOn />
            <Toggle label="Email notifications" desc="Receive alerts for failed workflows" defaultOn />
            <SaveBar saved={saved} onSave={save} />
          </div>
        )}

        {tab === 'profile' && (
          <div className="space-y-5">
            <SectionTitle title="User Profile" desc="Your personal account information" />
            <div className="flex items-center gap-4">
              <span className="grid h-16 w-16 place-items-center rounded-full bg-gradient-to-br from-slate-700 to-slate-900 text-xl font-bold text-white dark:from-cyan-500 dark:to-teal-600">
                {user?.email?.charAt(0).toUpperCase() ?? 'U'}
              </span>
              <div>
                <Button variant="secondary" size="sm">Change avatar</Button>
                <p className="mt-1 text-xs text-slate-400">JPG or PNG, max 2MB</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Full Name" value="Workspace Admin" />
              <Field label="Email" value={user?.email ?? ''} />
            </div>
            <Field label="Role" value="Workspace Administrator" disabled />
            <SaveBar saved={saved} onSave={save} />
          </div>
        )}

        {tab === 'ai' && (
          <div className="space-y-5">
            <SectionTitle title="AI Model Configuration" desc="Configure the AI models powering document intelligence" />
            <Field label="Primary Model" value="GPT-4o (Production)" />
            <Field label="Fallback Model" value="Claude 3.5 Sonnet" />
            <div className="grid grid-cols-2 gap-4">
              <Field label="Temperature" value="0.1" />
              <Field label="Max Tokens" value="4096" />
            </div>
            <Toggle label="Enable OCR pre-processing" desc="Run OCR on all image-based documents before AI extraction" defaultOn />
            <Toggle label="Enable risk detection" desc="AI flags risky clauses and discrepancies automatically" defaultOn />
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-400">Confidence Threshold</label>
                <input defaultValue="85%" className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200" />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-400">Review Threshold</label>
                <input defaultValue="75%" className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200" />
              </div>
            </div>
            <SaveBar saved={saved} onSave={save} />
          </div>
        )}

        {tab === 'api' && (
          <div className="space-y-5">
            <SectionTitle title="API Keys" desc="Manage keys for programmatic access" />
            <div>
              <label className="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-400">Production API Key</label>
              <div className="flex items-center gap-2">
                <input
                  type={showKey ? 'text' : 'password'}
                  value="diq_live_sk_a4f8b2c9d1e7f3a6b5c8d2e9f1a4b7c3"
                  readOnly
                  className="flex-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 font-mono text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
                />
                <Button variant="secondary" size="md" onClick={() => setShowKey((s) => !s)}>
                  {showKey ? <EyeOff size={15} /> : <Eye size={15} />}
                </Button>
              </div>
            </div>
            <Field label="Webhook URL" value="https://api.acme.com/diq/webhooks" />
            <Toggle label="Rate limiting" desc="Limit to 1000 requests per minute" defaultOn />
            <SaveBar saved={saved} onSave={save} />
          </div>
        )}

        {tab === 'integrations' && (
          <div className="space-y-4">
            <SectionTitle title="Integrations" desc="Connect external services and data sources" />
            {[
              { name: 'Slack', desc: 'Send workflow notifications to channels', connected: true, initials: 'Sl' },
              { name: 'Google Drive', desc: 'Import documents from Drive folders', connected: true, initials: 'GD' },
              { name: 'Microsoft 365', desc: 'Sync documents from SharePoint', connected: false, initials: 'M3' },
              { name: 'Salesforce', desc: 'Push extracted data to CRM records', connected: false, initials: 'SF' },
              { name: 'AWS S3', desc: 'Archive processed documents to S3', connected: true, initials: 'S3' },
            ].map((int) => (
              <div key={int.name} className="flex items-center gap-3 rounded-lg border border-slate-200 p-4 dark:border-slate-800">
                <span className="grid h-10 w-10 place-items-center rounded-lg bg-gradient-to-br from-slate-100 to-slate-200 text-sm font-bold text-slate-600 dark:from-slate-800 dark:to-slate-700 dark:text-slate-300">
                  {int.initials}
                </span>
                <div className="flex-1">
                  <div className="text-sm font-medium text-slate-800 dark:text-white">{int.name}</div>
                  <div className="text-xs text-slate-400">{int.desc}</div>
                </div>
                {int.connected ? (
                  <span className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400">
                    <Check size={13} /> Connected
                  </span>
                ) : (
                  <Button variant="secondary" size="sm">Connect</Button>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

function SectionTitle({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="border-b border-slate-100 pb-4 dark:border-slate-800">
      <h2 className="text-base font-semibold text-slate-900 dark:text-white">{title}</h2>
      <p className="mt-0.5 text-xs text-slate-400">{desc}</p>
    </div>
  );
}

function Field({ label, value, disabled }: { label: string; value: string; disabled?: boolean }) {
  return (
    <div>
      <label className="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-400">{label}</label>
      <input
        defaultValue={value}
        disabled={disabled}
        className={`w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 transition-all focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 ${
          disabled ? 'opacity-60' : ''
        }`}
      />
    </div>
  );
}

function Toggle({ label, desc, defaultOn }: { label: string; desc: string; defaultOn?: boolean }) {
  const [on, setOn] = useState(defaultOn ?? false);
  return (
    <div className="flex items-center justify-between rounded-lg border border-slate-200 p-3 dark:border-slate-800">
      <div>
        <div className="text-sm font-medium text-slate-700 dark:text-slate-200">{label}</div>
        <div className="text-xs text-slate-400">{desc}</div>
      </div>
      <button
        onClick={() => setOn((o) => !o)}
        className={`relative h-6 w-11 shrink-0 rounded-full transition-colors ${on ? 'bg-cyan-500' : 'bg-slate-200 dark:bg-slate-700'}`}
      >
        <span className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow-sm transition-transform ${on ? 'left-[22px]' : 'left-0.5'}`} />
      </button>
    </div>
  );
}

function SaveBar({ saved, onSave }: { saved: boolean; onSave: () => void }) {
  return (
    <div className="flex items-center gap-3 border-t border-slate-100 pt-4 dark:border-slate-800">
      <Button size="sm" onClick={onSave}><Save size={14} /> Save changes</Button>
      {saved && <span className="flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400"><Check size={14} /> Saved successfully</span>}
    </div>
  );
}
