import { confidenceColor, confidenceBar } from "../../../../lib/helpers";

export function ConfidenceBadge({ value, showBar = false }: { value: number; showBar?: boolean }) {
  if (value === 0) {
    return <span className="text-xs text-slate-400 dark:text-slate-600">—</span>;
  }
  return (
    <div className="flex items-center gap-2">
      <span className={`text-xs font-semibold tabular-nums ${confidenceColor(value)}`}>
        {value}%
      </span>
      {showBar && (
        <div className="h-1.5 w-12 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
          <div className={`h-full rounded-full ${confidenceBar(value)}`} style={{ width: `${value}%` }} />
        </div>
      )}
    </div>
  );
}
