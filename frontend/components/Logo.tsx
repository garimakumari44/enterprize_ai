import { FileStack } from 'lucide-react';

type LogoProps = {
  variant?: 'light' | 'dark';
  size?: 'sm' | 'md' | 'lg';
};

const sizes = {
  sm: { mark: 'h-7 w-7', icon: 16, title: 'text-base', sub: 'text-[10px]' },
  md: { mark: 'h-9 w-9', icon: 20, title: 'text-lg', sub: 'text-[11px]' },
  lg: { mark: 'h-12 w-12', icon: 26, title: 'text-2xl', sub: 'text-xs' },
};

export function Logo({ variant = 'light', size = 'md' }: LogoProps) {
  const s = sizes[size];
  const titleColor = variant === 'light' ? 'text-white' : 'text-slate-900';
  const subColor = variant === 'light' ? 'text-slate-400' : 'text-slate-500';

  return (
    <div className="flex items-center gap-3 select-none">
      <div
        className={`${s.mark} relative grid place-items-center rounded-xl bg-gradient-to-br from-sky-400 via-cyan-500 to-teal-500 shadow-lg shadow-cyan-500/30`}
      >
        <FileStack size={s.icon} className="text-white" strokeWidth={2.2} />
        <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-emerald-400 ring-2 ring-slate-950" />
      </div>
      <div className="leading-tight">
        <div className={`${s.title} font-semibold tracking-tight ${titleColor}`}>
          Document<span className="text-cyan-400">IQ</span>
        </div>
        <div className={`${s.sub} uppercase tracking-[0.18em] font-medium ${subColor}`}>
          Enterprise Intelligence
        </div>
      </div>
    </div>
  );
}
