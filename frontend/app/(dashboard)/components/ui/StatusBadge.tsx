import type { DocStatus } from '../../../../types';

type ExecutionStatus =
  | 'pending'
  | 'queued'
  | 'processing'
  | 'running'
  | 'completed'
  | 'failed'
  | 'review_required'
  | 'cancelled';

type Status = DocStatus | ExecutionStatus;

interface StatusBadgeProps {
  status: Status;
}

const statusConfig: Partial<
  Record<
    Status,
    {
      label: string;
      className: string;
    }
  >
> = {
  /* =========================================================
     COMMON / EXECUTION STATUSES
  ========================================================= */

  pending: {
    label: 'Pending',
    className:
      'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300',
  },

  queued: {
    label: 'Queued',
    className:
      'bg-violet-50 text-violet-600 dark:bg-violet-500/10 dark:text-violet-400',
  },

  processing: {
    label: 'Processing',
    className:
      'bg-cyan-50 text-cyan-600 dark:bg-cyan-500/10 dark:text-cyan-400',
  },

  running: {
    label: 'Running',
    className:
      'bg-cyan-50 text-cyan-600 dark:bg-cyan-500/10 dark:text-cyan-400',
  },

  completed: {
    label: 'Completed',
    className:
      'bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400',
  },

  failed: {
    label: 'Failed',
    className:
      'bg-rose-50 text-rose-600 dark:bg-rose-500/10 dark:text-rose-400',
  },

  review_required: {
    label: 'Needs Review',
    className:
      'bg-amber-50 text-amber-600 dark:bg-amber-500/10 dark:text-amber-400',
  },

  cancelled: {
    label: 'Cancelled',
    className:
      'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400',
  },
};

export function StatusBadge({
  status,
}: StatusBadgeProps) {
  const config = statusConfig[status];

  /*
   * Fallback for any existing DocStatus value
   * that isn't explicitly configured above.
   */
  if (!config) {
    return (
      <span
        className="
          inline-flex
          items-center
          rounded-full
          px-2
          py-0.5
          text-[10px]
          font-semibold
          bg-slate-100
          text-slate-600
          dark:bg-slate-800
          dark:text-slate-300
        "
      >
        {formatStatus(status)}
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ${config.className}`}
    >
      {config.label}
    </span>
  );
}

function formatStatus(status: string): string {
  return status
    .replace(/_/g, ' ')
    .replace(/\b\w/g, char =>
      char.toUpperCase()
    );
}