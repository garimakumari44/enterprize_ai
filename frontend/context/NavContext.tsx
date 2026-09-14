"use client"

import { createContext, useContext, useState, type ReactNode } from 'react';
import type { PageKey } from '../types';

type NavContextValue = {
  page: PageKey;
  setPage: (p: PageKey) => void;
  selectedDocId: string | null;
  setSelectedDocId: (id: string | null) => void;
  selectedWorkflowId: string | null;
  setSelectedWorkflowId: (id: string | null) => void;
};

const NavContext = createContext<NavContextValue | undefined>(undefined);

export function NavProvider({ children }: { children: ReactNode }) {
  const [page, setPage] = useState<PageKey>('dashboard');
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null);

  return (
    <NavContext.Provider
      value={{ page, setPage, selectedDocId, setSelectedDocId, selectedWorkflowId, setSelectedWorkflowId }}
    >
      {children}
    </NavContext.Provider>
  );
}

export function useNav() {
  const ctx = useContext(NavContext);
  if (!ctx) throw new Error('useNav must be used within NavProvider');
  return ctx;
}
