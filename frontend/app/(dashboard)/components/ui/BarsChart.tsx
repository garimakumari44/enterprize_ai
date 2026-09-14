export function BarsChart({
  data,
  labels,
  height = 180,
  color = '#06b6d4',
}: {
  data: number[];
  labels: string[];
  height?: number;
  color?: string;
}) {
  const max = Math.max(...data) * 1.15;
  return (
    <div className="flex items-end gap-2" style={{ height }}>
      {data.map((v, i) => (
        <div key={i} className="group flex flex-1 flex-col items-center gap-2">
          <div className="relative flex w-full flex-1 items-end justify-center">
            <div
              className="w-full max-w-[36px] rounded-t-md transition-all duration-300 hover:opacity-80"
              style={{
                height: `${(v / max) * 100}%`,
                background: `linear-gradient(to top, ${color}33, ${color})`,
              }}
            />
            <div className="pointer-events-none absolute -top-7 left-1/2 -translate-x-1/2 rounded bg-slate-900 px-1.5 py-0.5 text-[10px] font-medium text-white opacity-0 transition-opacity group-hover:opacity-100 dark:bg-slate-700">
              {v}
            </div>
          </div>
          <span className="text-[10px] font-medium text-slate-400 dark:text-slate-500">{labels[i]}</span>
        </div>
      ))}
    </div>
  );
}
