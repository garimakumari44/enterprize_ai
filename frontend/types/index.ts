export type DocStatus = 'processing' | 'completed' | 'needs_review' | 'failed'| 'pending';
export type DocType = 'pdf' | 'image' | 'docx' | 'xlsx' | 'email' | 'contract';

export interface Document {
  id: string;
  name: string;
  type: DocType;
  workflow: string;
  status: DocStatus;
  confidence: number;
  createdAt: string;
  size: string;
  pages?: number;
  preview?: {
    vendor?: string;
    amount?: string;
    date?: string;
    invoiceNumber?: string;
    summary?: string;
    riskLevel?: 'low' | 'medium' | 'high';
    extractedFields?: ExtractedField[];
    annotations?: DocAnnotation[];
  };
}

export interface ExtractedField {
  label: string;
  value: string;
  confidence: number;
}

export interface DocAnnotation {
  id: string;
  page: number;
  text: string;
  type: 'field' | 'risk';
  label: string;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  documentsProcessed: number;
  successRate: number;
  lastExecution: string;
  icon: string;
  color: string;
  steps: WorkflowStep[];
}

export interface WorkflowStep {
  id: string;
  type: 'document' | 'ai' | 'logic' | 'output';
  label: string;
  description: string;
}

export interface Execution {
  id: string;
  workflowName: string;
  documentName: string;
  status: DocStatus;
  duration: string;
  createdAt: string;
  steps: ExecutionStep[];
}

export interface ExecutionStep {
  id: string;
  label: string;
  status: 'done' | 'active' | 'pending' | 'failed';
  duration?: string;
}

export interface ReviewItem {
  id: string;
  documentName: string;
  confidence: number;
  issue: string;
  reason: string;
  type: DocType;
}

export interface AIInsight {
  id: string;
  type: 'positive' | 'warning' | 'info';
  title: string;
  detail: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: { doc: string; page: number; excerpt: string }[];
}

export interface SearchResult {
  id: string;
  docName: string;
  excerpt: string;
  confidence: number;
  page: number;
  workflow: string;
}

export type PageKey =
  | 'dashboard'
  | 'documents'
  | 'upload'
  | 'workflows'
  | 'executions'
  | 'knowledge'
  | 'assistant'
  | 'review'
  | 'analytics'
  | 'settings';
