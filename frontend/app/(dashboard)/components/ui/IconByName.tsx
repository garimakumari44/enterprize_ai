import * as Icons from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

const iconMap = Icons as unknown as Record<string, LucideIcon>;

export function IconByName({ name, size = 18, className = '' }: { name: string; size?: number; className?: string }) {
  const Icon = iconMap[name];
  if (!Icon) return null;
  return <Icon size={size} className={className} strokeWidth={2} />;
}
