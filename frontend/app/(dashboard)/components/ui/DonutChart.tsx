export function DonutChart({
  segments,
  size = 140,
  thickness = 16,
  centerLabel,
  centerSub,
}: {
  segments: { label: string; value: number; color: string }[];
  size?: number;
  thickness?: number;
  centerLabel?: string;
  centerSub?: string;
}) {
  const radius = (size - thickness) / 2;
  const circumference = 2 * Math.PI * radius;
  const total = segments.reduce((s, x) => s + x.value, 0) || 1;
  let offset = 0;

  return (
    <div className="flex items-center gap-5">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            strokeWidth={thickness}
            className="stroke-slate-100 dark:stroke-slate-800"
          />
          {segments.map((seg, i) => {
            const len = (seg.value / total) * circumference;
            const circle = (
              <circle
                key={i}
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="none"
                stroke={seg.color}
                strokeWidth={thickness}
                strokeDasharray={`${len} ${circumference - len}`}
                strokeDashoffset={-offset}
                strokeLinecap="round"
              />
            );
            offset += len;
            return circle;
          })}
        </svg>
        {centerLabel && (
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-xl font-bold text-slate-900 dark:text-white">{centerLabel}</span>
            {centerSub && <span className="text-[10px] text-slate-400">{centerSub}</span>}
          </div>
        )}
      </div>
      <div className="space-y-2">
        {segments.map((seg) => (
          <div key={seg.label} className="flex items-center gap-2 text-xs">
            <span className="h-2.5 w-2.5 rounded-sm" style={{ background: seg.color }} />
            <span className="text-slate-600 dark:text-slate-400">{seg.label}</span>
            <span className="ml-auto font-semibold tabular-nums text-slate-900 dark:text-white">{seg.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
