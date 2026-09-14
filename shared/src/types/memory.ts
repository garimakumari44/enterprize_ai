export interface MemoryRecord {
  id: string;

  namespace: string;

  content: string;

  metadata?: Record<string, unknown>;

  createdAt: number;
}