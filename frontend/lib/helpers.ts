import type { DocStatus, DocType } from '../types';

export function formatRelativeDate(iso: string): string {
  const d = new Date(iso);
  const now = new Date('2024-10-14T10:30:00Z');
  const diff = now.getTime() - d.getTime();

  const mins = Math.floor(diff / 60000);

  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;

  const hours = Math.floor(mins / 60);

  if (hours < 24) return `${hours}h ago`;

  const days = Math.floor(hours / 24);

  return `${days}d ago`;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export const statusConfig: Record<
  DocStatus,
  {
    label: string;
    dot: string;
    text: string;
    bg: string;
    border: string;
  }
> = {
  pending: {
    label: 'Pending',
    dot: 'bg-slate-400',
    text: 'text-slate-600 dark:text-slate-400',
    bg: 'bg-slate-50 dark:bg-slate-500/10',
    border: 'border-slate-200 dark:border-slate-500/20',
  },

  completed: {
    label: 'Completed',
    dot: 'bg-emerald-500',
    text: 'text-emerald-700 dark:text-emerald-400',
    bg: 'bg-emerald-50 dark:bg-emerald-500/10',
    border: 'border-emerald-200 dark:border-emerald-500/20',
  },

  processing: {
    label: 'Processing',
    dot: 'bg-cyan-500',
    text: 'text-cyan-700 dark:text-cyan-400',
    bg: 'bg-cyan-50 dark:bg-cyan-500/10',
    border: 'border-cyan-200 dark:border-cyan-500/20',
  },

  needs_review: {
    label: 'Needs Review',
    dot: 'bg-amber-500',
    text: 'text-amber-700 dark:text-amber-400',
    bg: 'bg-amber-50 dark:bg-amber-500/10',
    border: 'border-amber-200 dark:border-amber-500/20',
  },

  failed: {
    label: 'Failed',
    dot: 'bg-rose-500',
    text: 'text-rose-700 dark:text-rose-400',
    bg: 'bg-rose-50 dark:bg-rose-500/10',
    border: 'border-rose-200 dark:border-rose-500/20',
  },
};

export const typeIcon: Record<DocType, string> = {
  pdf: 'FileText',
  image: 'Image',
  docx: 'FileType',
  xlsx: 'Sheet',
  email: 'Mail',
  contract: 'FileSignature',
};

export const typeColors: Record<DocType, string> = {
  pdf: 'text-rose-600 dark:text-rose-400',
  image: 'text-violet-600 dark:text-violet-400',
  docx: 'text-sky-600 dark:text-sky-400',
  xlsx: 'text-emerald-600 dark:text-emerald-400',
  email: 'text-amber-600 dark:text-amber-400',
  contract: 'text-cyan-600 dark:text-cyan-400',
};

export function confidenceColor(c: number): string {
  if (c >= 90) return 'text-emerald-600 dark:text-emerald-400';
  if (c >= 75) return 'text-amber-600 dark:text-amber-400';

  return 'text-rose-600 dark:text-rose-400';
}

export function confidenceBar(c: number): string {
  if (c >= 90) return 'bg-emerald-500';
  if (c >= 75) return 'bg-amber-500';

  return 'bg-rose-500';
}

export function riskConfig(level: 'low' | 'medium' | 'high') {
  switch (level) {
    case 'low':
      return {
        label: 'Low Risk',
        color: 'text-emerald-600 dark:text-emerald-400',
        bg: 'bg-emerald-50 dark:bg-emerald-500/10',
      };

    case 'medium':
      return {
        label: 'Medium Risk',
        color: 'text-amber-600 dark:text-amber-400',
        bg: 'bg-amber-50 dark:bg-amber-500/10',
      };

    case 'high':
      return {
        label: 'High Risk',
        color: 'text-rose-600 dark:text-rose-400',
        bg: 'bg-rose-50 dark:bg-rose-500/10',
      };
  }
}