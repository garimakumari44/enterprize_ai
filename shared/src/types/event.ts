export interface PlatformEvent<T = unknown> {
  id: string;
  type: string;
  source: string;
  timestamp: number;
  payload: T;
}



export interface Event<T = any> {
  id: string;
  type: string;
  source: string;
  timestamp: number;
  payload: T;
}

export interface EventHandler<T = any> {
  handle(event: Event<T>): Promise<void>;
}