import {
  FileInput,
  ScanText,
  FileText,
  Split,
  Layers,
  Sparkles,
  Brain,
  Tags,
  AlignLeft,
  WandSparkles,
  Database,
  Boxes,
  Search,
  GitBranch,
  ShieldCheck,
  UserCheck,
  Save,
  Download,
  Webhook,
  Eraser,
  ListTree,
} from 'lucide-react';

import type { LucideIcon } from 'lucide-react';

import type {
  WorkflowNodeType,
  WorkflowOperation,
} from '../types/workflow';

export interface PaletteItem {
  operation: WorkflowOperation;

  label: string;

  description: string;

  icon: LucideIcon;

  defaultConfig?: Record<string, unknown>;
}

export interface PaletteCategory {
  type: WorkflowNodeType;

  label: string;

  color: 'sky' | 'violet' | 'cyan' | 'indigo' | 'amber' | 'emerald';

  items: PaletteItem[];
}

export const workflowPalette: PaletteCategory[] = [
  {
    type: 'input',
    label: 'Input',
    color: 'sky',
    items: [
      {
        operation: 'library_document',
        label: 'Library Document',
        description: 'Select an existing document',
        icon: FileInput,
      },
    ],
  },

  {
    type: 'document_processing',
    label: 'Document Processing',
    color: 'sky',
    items: [
      {
        operation: 'ocr',
        label: 'OCR',
        description: 'Extract text from scanned documents',
        icon: ScanText,
      },
      {
        operation: 'text_extraction',
        label: 'Text Extraction',
        description: 'Extract text from PDF, DOCX, XLSX, etc.',
        icon: FileText,
      },
      {
        operation: 'document_classification',
        label: 'Document Classification',
        description: 'Identify document type',
        icon: Tags,
      },
      {
        operation: 'document_splitting',
        label: 'Document Splitting',
        description: 'Split multi-document files',
        icon: Split,
      },
    ],
  },

  {
    type: 'transformation',
    label: 'Transformation',
    color: 'violet',
    items: [
      {
        operation: 'chunking',
        label: 'Chunking',
        description: 'Split text into retrieval chunks',
        icon: Layers,
      },
      {
        operation: 'cleaning',
        label: 'Cleaning',
        description: 'Clean extracted text',
        icon: Eraser,
      },
      {
        operation: 'normalization',
        label: 'Normalization',
        description: 'Normalize document data',
        icon: ListTree,
      },
    ],
  },

  {
    type: 'ai',
    label: 'AI',
    color: 'cyan',
    items: [
      {
        operation: 'extraction',
        label: 'Extraction',
        description: 'Extract structured fields',
        icon: Sparkles,
      },
      {
        operation: 'summarization',
        label: 'Summarization',
        description: 'Generate document summary',
        icon: AlignLeft,
      },
      {
        operation: 'classification',
        label: 'AI Classification',
        description: 'Classify using an AI model',
        icon: Tags,
      },
      {
        operation: 'ai_model',
        label: 'AI Model',
        description: 'Run a configurable LLM',
        icon: Brain,
      },
    ],
  },

  {
    type: 'knowledge',
    label: 'Knowledge',
    color: 'indigo',
    items: [
      {
        operation: 'embedding',
        label: 'Embedding',
        description: 'Generate vector embeddings',
        icon: WandSparkles,
      },
      {
        operation: 'vector_store',
        label: 'Vector Store',
        description: 'Store vectors in pgvector',
        icon: Database,
      },
      {
        operation: 'index',
        label: 'Index',
        description: 'Create searchable index',
        icon: Search,
      },
    ],
  },

  {
    type: 'logic',
    label: 'Logic',
    color: 'amber',
    items: [
      {
        operation: 'condition',
        label: 'Condition',
        description: 'Branch workflow execution',
        icon: GitBranch,
      },
      {
        operation: 'validation',
        label: 'Validation',
        description: 'Validate extracted data',
        icon: ShieldCheck,
      },
      {
        operation: 'human_review',
        label: 'Human Review',
        description: 'Send result for manual review',
        icon: UserCheck,
      },
    ],
  },

  {
    type: 'output',
    label: 'Output',
    color: 'emerald',
    items: [
      {
        operation: 'save_result',
        label: 'Save Result',
        description: 'Persist processing result',
        icon: Save,
      },
      {
        operation: 'export',
        label: 'Export',
        description: 'Export result to a file or API',
        icon: Download,
      },
      {
        operation: 'webhook',
        label: 'Webhook',
        description: 'Send result to an external service',
        icon: Webhook,
      },
    ],
  },
];