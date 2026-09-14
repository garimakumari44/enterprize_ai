export function Sparkline({
  data,
  color = '#06b6d4',
  height = 40,
  width = 120,
}: {
  data: number[];
  color?: string;
  height?: number;
  width?: number;
}) {
  if (data.length === 0) return null;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const step = width / (data.length - 1 || 1);

  const points = data.map((v, i) => {
    const x = i * step;
    const y = height - ((v - min) / range) * (height - 4) - 2;
    return [x, y];
  });

  const linePath = points.map(([x, y]) => `${x},${y}`).join(' ');
  const areaPath = `${points.map(([x, y]) => `${x},${y}`).join(' ')} ${width},${height} 0,${height}`;

  return (
    <svg width={width} height={height} className="overflow-visible">
      <defs>
        <linearGradient id={`spark-${color}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity={0.25} />
          <stop offset="100%" stopColor={color} stopOpacity={0} />
        </linearGradient>
      </defs>
      <polygon points={areaPath} fill={`url(#spark-${color})`} />
      <polyline
        points={linePath}
        fill="none"
        stroke={color}
        strokeWidth={1.8}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx={points[points.length - 1][0]} cy={points[points.length - 1][1]} r={2.5} fill={color} />
    </svg>
  );
}
