import { FileStack, ShieldCheck, Clock, ClipboardCheck, TrendingUp, TrendingDown } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { Card } from './ui/Card';
import { BarsChart } from './ui/BarsChart';
import { DonutChart } from './ui/DonutChart';
import { Sparkline } from './ui/Sparkline';


const metricCards: { label: string; value: string; trend: number; icon: LucideIcon; spark: number[]; color: string }[] = [
  { label: 'Documents Processed', value: '128,540', trend: 12.5, icon: FileStack, spark: [82, 95, 88, 110, 102, 124, 128], color: '#06b6d4' },
  { label: 'Accuracy Rate', value: '96.4%', trend: 4.0, icon: ShieldCheck, spark: [91, 92, 90, 93, 94, 95, 96], color: '#10b981' },
  { label: 'Avg Processing Time', value: '12s', trend: -8.2, icon: Clock, spark: [22, 19, 18, 16, 15, 13, 12], color: '#0ea5e9' },
  { label: 'Review Rate', value: '3.2%', trend: -1.1, icon: ClipboardCheck, spark: [5.1, 4.5, 4.2, 3.8, 3.5, 3.3, 3.2], color: '#f59e0b' },
];

const volumeData = [4200, 3800, 5100, 4800, 6200, 5900, 7400, 6800, 8100, 7600, 9200, 8800];
const volumeLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const accuracyData = [88, 89, 87, 90, 91, 92, 93, 94, 93, 95, 96, 96];
const accuracyLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const statusSegments = [
  { label: 'Completed', value: 12130, color: '#10b981' },
  { label: 'Needs Review', value: 43, color: '#f59e0b' },
  { label: 'Processing', value: 12, color: '#06b6d4' },
  { label: 'Failed', value: 8, color: '#f43f5e' },
];

export function AnalyticsPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top metrics */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metricCards.map((m) => {
          const Icon = m.icon;
          const up = m.trend > 0;
          return (
            <Card key={m.label} hover className="p-5">
              <div className="flex items-start justify-between">
                <div className="grid h-10 w-10 place-items-center rounded-lg bg-gradient-to-br from-sky-50 to-cyan-50 text-cyan-600 dark:from-slate-800 dark:to-slate-800/50 dark:text-cyan-400">
                  <Icon size={18} strokeWidth={2} />
                </div>
                <div className="flex items-center gap-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                  {up ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                  {Math.abs(m.trend)}%
                </div>
              </div>
              <div className="mt-4">
                <div className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">{m.value}</div>
                <div className="mt-0.5 text-xs font-medium text-slate-500 dark:text-slate-400">{m.label}</div>
              </div>
              <div className="mt-3"><Sparkline data={m.spark} color={m.color} width={200} height={32} /></div>
            </Card>
          );
        })}
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <div className="border-b border-slate-100 px-5 py-4 dark:border-slate-800">
            <h2 className="text-sm font-semibold text-slate-900 dark:text-white">Processing Volume</h2>
            <p className="mt-0.5 text-xs text-slate-400">Documents processed per month (last 12 months)</p>
          </div>
          <div className="p-5">
            <BarsChart data={volumeData} labels={volumeLabels} height={200} color="#06b6d4" />
          </div>
        </Card>

        <Card>
          <div className="border-b border-slate-100 px-5 py-4 dark:border-slate-800">
            <h2 className="text-sm font-semibold text-slate-900 dark:text-white">Document Status</h2>
            <p className="mt-0.5 text-xs text-slate-400">Current processing breakdown</p>
          </div>
          <div className="p-5">
            <DonutChart segments={statusSegments} centerLabel="128K" centerSub="total" />
          </div>
        </Card>
      </div>

      {/* Charts row 2 */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <div className="border-b border-slate-100 px-5 py-4 dark:border-slate-800">
            <h2 className="text-sm font-semibold text-slate-900 dark:text-white">Accuracy Trend</h2>
            <p className="mt-0.5 text-xs text-slate-400">AI extraction accuracy over time</p>
          </div>
          <div className="p-5">
            <BarsChart data={accuracyData} labels={accuracyLabels} height={200} color="#10b981" />
          </div>
        </Card>

        <Card>
          <div className="border-b border-slate-100 px-5 py-4 dark:border-slate-800">
            <h2 className="text-sm font-semibold text-slate-900 dark:text-white">Workflow Performance</h2>
            <p className="mt-0.5 text-xs text-slate-400">Success rate by workflow</p>
          </div>
          <div className="space-y-3 p-5">
            
          </div>
        </Card>
      </div>
    </div>
  );
}
