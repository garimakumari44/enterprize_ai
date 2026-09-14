
'use client';

import {
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  Sparkles,
  AlertTriangle,
  Info,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

import { Card } from './ui/Card';
import { Sparkline } from './ui/Sparkline';
import { StatusBadge } from './ui/StatusBadge';
import { ConfidenceBadge } from './ui/ConfidenceBadge';
import { IconByName } from './ui/IconByName';

import { typeIcon, typeColors } from '../../../lib/helpers';
import { useNav } from '../../../context/NavContext';

export type DashboardDocument = {
  id: string;
  name: string;
  type: keyof typeof typeIcon;
  workflow: string;
  status: Parameters<typeof StatusBadge>[0]['status'];
  confidence: number;
};

export type DashboardInsight = {
  id: string;
  type: 'positive' | 'warning' | 'info';
  title: string;
  detail: string;
};

export type DashboardWorkflow = {
  id: string;
  name: string;
  icon: string;
  description: string;
  documentsProcessed: number;
  successRate: number;
  lastExecution: string;
};

export type DashboardMetric = {
  label: string;
  value: string;
  trend: number;
  icon: LucideIcon;
  spark: number[];
  color: string;
};

type DashboardHomeProps = {
  metrics?: DashboardMetric[];
  documents?: DashboardDocument[];
  aiInsights?: DashboardInsight[];
  workflows?: DashboardWorkflow[];
  loading?: boolean;
};

const insightIcon = {
  positive: TrendingUp,
  warning: AlertTriangle,
  info: Info,
};

const insightStyle = {
  positive: {
    bg: 'bg-emerald-50 dark:bg-emerald-500/10',
    text: 'text-emerald-600 dark:text-emerald-400',
    border: 'border-emerald-200 dark:border-emerald-500/20',
  },

  warning: {
    bg: 'bg-amber-50 dark:bg-amber-500/10',
    text: 'text-amber-600 dark:text-amber-400',
    border: 'border-amber-200 dark:border-amber-500/20',
  },

  info: {
    bg: 'bg-sky-50 dark:bg-sky-500/10',
    text: 'text-sky-600 dark:text-sky-400',
    border: 'border-sky-200 dark:border-sky-500/20',
  },
};

export function DashboardHome({
  metrics = [],
  documents = [],
  aiInsights = [],
  workflows = [],
  loading = false,
}: DashboardHomeProps) {
  const { setPage, setSelectedDocId } = useNav();

  /*
   * Defensive defaults above guarantee these are always arrays.
   * This prevents the dashboard from crashing when API data has
   * not arrived yet or Dashboard.tsx does not provide a value.
   */
  const recentDocs = documents.slice(0, 6);

  const openDoc = (id: string) => {
    setSelectedDocId(id);
    setPage('documents');
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-fade-in">
        {/* Metrics skeleton */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <Card
              key={index}
              className="h-36 animate-pulse bg-slate-100 dark:bg-slate-800"
            >
              <div />
            </Card>
          ))}
        </div>

        {/* Documents + insights skeleton */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <Card className="h-80 animate-pulse bg-slate-100 dark:bg-slate-800 lg:col-span-2">
            <div />
          </Card>

          <Card className="h-80 animate-pulse bg-slate-100 dark:bg-slate-800">
            <div />
          </Card>
        </div>

        {/* Workflow skeleton */}
        <Card className="h-64 animate-pulse bg-slate-100 dark:bg-slate-800">
          <div />
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* =========================================================
          METRICS
      ========================================================= */}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          const isPositive = metric.trend >= 0;

          return (
            <Card
              key={metric.label}
              hover
              className="p-5"
            >
              <div className="flex items-start justify-between">
                <div className="grid h-10 w-10 place-items-center rounded-lg bg-gradient-to-br from-sky-50 to-cyan-50 text-cyan-600 dark:from-slate-800 dark:to-slate-800/50 dark:text-cyan-400">
                  <Icon
                    size={18}
                    strokeWidth={2}
                  />
                </div>

                <div
                  className={`flex items-center gap-1 text-xs font-semibold ${
                    isPositive
                      ? 'text-emerald-600 dark:text-emerald-400'
                      : 'text-rose-600 dark:text-rose-400'
                  }`}
                >
                  {isPositive ? (
                    <TrendingUp size={14} />
                  ) : (
                    <TrendingDown size={14} />
                  )}

                  {Math.abs(metric.trend)}%
                </div>
              </div>

              <div className="mt-4">
                <div className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                  {metric.value}
                </div>

                <div className="mt-0.5 text-xs font-medium text-slate-500 dark:text-slate-400">
                  {metric.label}
                </div>
              </div>

              <div className="mt-3">
                <Sparkline
                  data={metric.spark}
                  color={metric.color}
                  width={200}
                  height={32}
                />
              </div>
            </Card>
          );
        })}

        {metrics.length === 0 && (
          <Card className="p-5 sm:col-span-2 lg:col-span-4">
            <div className="py-6 text-center text-sm text-slate-400">
              No dashboard metrics available.
            </div>
          </Card>
        )}
      </div>

      {/* =========================================================
          RECENT DOCUMENTS + AI INSIGHTS
      ========================================================= */}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Recent Documents */}

        <Card className="lg:col-span-2">
          <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4 dark:border-slate-800">
            <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
              Recent Documents
            </h2>

            <button
              type="button"
              onClick={() => setPage('documents')}
              className="flex items-center gap-1 text-xs font-medium text-cyan-600 transition-colors hover:text-cyan-700 dark:text-cyan-400"
            >
              View all
              <ArrowUpRight size={13} />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:border-slate-800">
                  <th className="px-5 py-2.5">
                    Document
                  </th>

                  <th className="px-3 py-2.5">
                    Workflow
                  </th>

                  <th className="px-3 py-2.5">
                    Status
                  </th>

                  <th className="px-5 py-2.5 text-right">
                    Confidence
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-50 dark:divide-slate-800/50">
                {recentDocs.map((doc) => (
                  <tr
                    key={doc.id}
                    onClick={() => openDoc(doc.id)}
                    className="cursor-pointer transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/40"
                  >
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2.5">
                        <IconByName
                          name={typeIcon[doc.type]}
                          size={16}
                          className={typeColors[doc.type]}
                        />

                        <span className="truncate font-medium text-slate-700 dark:text-slate-200">
                          {doc.name}
                        </span>
                      </div>
                    </td>

                    <td className="px-3 py-3 text-xs text-slate-500 dark:text-slate-400">
                      {doc.workflow}
                    </td>

                    <td className="px-3 py-3">
                      <StatusBadge status={doc.status} />
                    </td>

                    <td className="px-5 py-3 text-right">
                      <ConfidenceBadge
                        value={doc.confidence}
                        showBar
                      />
                    </td>
                  </tr>
                ))}

                {recentDocs.length === 0 && (
                  <tr>
                    <td
                      colSpan={4}
                      className="px-5 py-12 text-center text-sm text-slate-400"
                    >
                      No documents available.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>

        {/* AI Insights */}

        <Card>
          <div className="flex items-center gap-2 border-b border-slate-100 px-5 py-4 dark:border-slate-800">
            <Sparkles
              size={16}
              className="text-cyan-500"
            />

            <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
              AI Insights
            </h2>
          </div>

          <div className="space-y-3 p-4">
            {aiInsights.map((insight) => {
              const style = insightStyle[insight.type];
              const Icon = insightIcon[insight.type];

              return (
                <div
                  key={insight.id}
                  className={`rounded-lg border p-3 ${style.bg} ${style.border}`}
                >
                  <div className="flex items-start gap-2.5">
                    <Icon
                      size={16}
                      className={`mt-0.5 shrink-0 ${style.text}`}
                    />

                    <div>
                      <p className="text-sm font-medium text-slate-800 dark:text-slate-200">
                        {insight.title}
                      </p>

                      <p className="mt-1 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
                        {insight.detail}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}

            {aiInsights.length === 0 && (
              <div className="py-10 text-center text-xs text-slate-400">
                No insights available.
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* =========================================================
          ACTIVE WORKFLOWS
      ========================================================= */}

      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
            Active Workflows
          </h2>

          <button
            type="button"
            onClick={() => setPage('workflows')}
            className="flex items-center gap-1 text-xs font-medium text-cyan-600 transition-colors hover:text-cyan-700 dark:text-cyan-400"
          >
            Manage workflows
            <ArrowUpRight size={13} />
          </button>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {workflows.map((workflow) => (
            <Card
              key={workflow.id}
              hover
              className="p-5"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="grid h-10 w-10 place-items-center rounded-lg bg-gradient-to-br from-sky-50 to-cyan-50 dark:from-slate-800 dark:to-slate-800/50">
                    <IconByName
                      name={workflow.icon}
                      size={18}
                      className="text-cyan-600 dark:text-cyan-400"
                    />
                  </div>

                  <div>
                    <div className="text-sm font-semibold text-slate-800 dark:text-white">
                      {workflow.name}
                    </div>

                    <div className="mt-0.5 text-xs text-slate-400">
                      {workflow.documentsProcessed.toLocaleString()} processed
                    </div>
                  </div>
                </div>
              </div>

              <p className="mt-3 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
                {workflow.description}
              </p>

              <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3 dark:border-slate-800">
                <div className="flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />

                  <span className="text-xs font-medium text-slate-600 dark:text-slate-400">
                    {workflow.successRate}% success
                  </span>
                </div>

                <span className="text-xs text-slate-400">
                  {workflow.lastExecution}
                </span>
              </div>
            </Card>
          ))}
        </div>

        {workflows.length === 0 && (
          <Card className="py-12 text-center">
            <p className="text-sm text-slate-400">
              No active workflows.
            </p>
          </Card>
        )}
      </div>
    </div>
  );
}

