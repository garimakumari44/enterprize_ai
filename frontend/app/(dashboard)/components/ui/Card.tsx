import type { ReactNode } from 'react';

export function Card({
  children,
  className = '',
  hover = false,
}: {
  children: ReactNode;
  className?: string;
  hover?: boolean;
}) {
  return (
    <div
      className={`rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 ${
        hover ? 'transition-all hover:-translate-y-0.5 hover:border-cyan-300 dark:hover:border-cyan-700 hover:shadow-lg hover:shadow-cyan-500/5' : ''
      } ${className}`}
    >
      {children}
    </div>
  );
}
