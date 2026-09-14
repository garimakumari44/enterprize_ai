import { Zap, Brain, Library, Wrench, Database, Bot, Activity, ShieldCheck } from 'lucide-react';

const nodes = [
  { icon: Zap, label: 'Trigger', top: '8%', left: '50%', delay: '0s' },
  { icon: Brain, label: 'Planning', top: '22%', left: '78%', delay: '0.4s' },
  { icon: Library, label: 'RAG', top: '44%', left: '88%', delay: '0.8s' },
  { icon: Wrench, label: 'Tools', top: '64%', left: '78%', delay: '1.2s' },
  { icon: Database, label: 'Memory', top: '78%', left: '50%', delay: '1.6s' },
  { icon: Bot, label: 'Inference', top: '64%', left: '22%', delay: '2.0s' },
  { icon: Activity, label: 'Observability', top: '44%', left: '12%', delay: '2.4s' },
  { icon: ShieldCheck, label: 'Approvals', top: '22%', left: '22%', delay: '2.8s' },
];

export function BrandStage() {
  return (
    <div className="relative h-full w-full overflow-hidden bg-slate-950">
      {/* Ambient gradients */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -left-32 top-1/4 h-96 w-96 rounded-full bg-cyan-500/20 blur-[120px]" />
        <div className="absolute right-0 top-0 h-80 w-80 rounded-full bg-sky-500/15 blur-[100px]" />
        <div className="absolute bottom-0 left-1/3 h-80 w-80 rounded-full bg-teal-500/15 blur-[110px]" />
      </div>

      {/* Grid overlay */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.07]"
        style={{
          backgroundImage:
            'linear-gradient(to right, white 1px, transparent 1px), linear-gradient(to bottom, white 1px, transparent 1px)',
          backgroundSize: '48px 48px',
        }}
      />

      <div className="relative z-10 flex h-full flex-col justify-between p-10 lg:p-14">
        {/* Top: workflow ring */}
        <div className="relative mx-auto mt-2 hidden aspect-square w-full max-w-md lg:block">
          {/* Concentric rings */}
          <div className="absolute inset-0 rounded-full border border-white/5" />
          <div className="absolute inset-[12%] rounded-full border border-white/5" />
          <div className="absolute inset-[26%] rounded-full border border-white/5" />
          <div className="absolute inset-[40%] rounded-full border border-white/10" />

          {/* Rotating orbit */}
          <div className="absolute inset-[12%] animate-[spin_40s_linear_infinite] rounded-full">
            <div className="absolute left-1/2 top-0 h-2 w-2 -translate-x-1/2 rounded-full bg-cyan-400 shadow-[0_0_12px_4px_rgba(34,211,238,0.6)]" />
          </div>
          <div className="absolute inset-[26%] animate-[spin_28s_linear_infinite_reverse] rounded-full">
            <div className="absolute left-0 top-1/2 h-1.5 w-1.5 -translate-y-1/2 rounded-full bg-teal-400 shadow-[0_0_10px_3px_rgba(45,212,191,0.6)]" />
          </div>

          {/* Center core */}
          <div className="absolute left-1/2 top-1/2 flex -translate-x-1/2 -translate-y-1/2 flex-col items-center">
            <div className="relative grid h-20 w-20 place-items-center rounded-2xl bg-gradient-to-br from-sky-400 via-cyan-500 to-teal-500 shadow-2xl shadow-cyan-500/40">
              <Bot size={36} className="text-white" strokeWidth={1.8} />
              <span className="absolute inset-0 animate-ping rounded-2xl bg-cyan-400/20" />
            </div>
            <div className="mt-3 text-[10px] uppercase tracking-[0.2em] text-slate-400">
              Orchestration Core
            </div>
          </div>

          {/* Workflow nodes */}
          {nodes.map(({ icon: Icon, label, top, left, delay }) => (
            <div
              key={label}
              className="group absolute -translate-x-1/2 -translate-y-1/2"
              style={{ top, left }}
            >
              <div
                className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 backdrop-blur-md transition-colors hover:border-cyan-400/50 hover:bg-cyan-400/10"
                style={{ animation: `float 6s ease-in-out infinite`, animationDelay: delay }}
              >
                <Icon size={14} className="text-cyan-300" strokeWidth={2} />
                <span className="text-[11px] font-medium text-slate-200">{label}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Bottom: value proposition */}
        <div className="max-w-xl">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-medium uppercase tracking-wider text-cyan-300 backdrop-blur">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-cyan-400" />
            AI Workflow Orchestration Platform
          </div>
          <h2 className="text-3xl font-semibold leading-tight tracking-tight text-white lg:text-4xl">
            Turn enterprise documents into
            <span className="bg-gradient-to-r from-cyan-300 to-teal-300 bg-clip-text text-transparent">
              {' '}intelligent, orchestrated workflows.
            </span>
          </h2>
          <p className="mt-4 text-sm leading-relaxed text-slate-400 lg:text-base">
            Retrieval, planning, tool execution, memory, and human-in-the-loop approvals —
            unified into one reliable, observable system.
          </p>

          <div className="mt-8 flex items-center gap-6 text-xs text-slate-500">
            <span className="flex items-center gap-2">
              <ShieldCheck size={14} className="text-emerald-400" /> SOC 2 Type II
            </span>
            <span className="h-3 w-px bg-slate-700" />
            <span>99.99% uptime SLA</span>
            <span className="h-3 w-px bg-slate-700" />
            <span>Private-cloud deployable</span>
          </div>
        </div>
      </div>
    </div>
  );
}
