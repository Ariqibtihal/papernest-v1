import { create } from 'zustand';
import type { PaperDTO, SearchFilters } from '@/types/paper';

interface SearchState {
  query: string;
  filters: SearchFilters;
  results: PaperDTO[];
  total: number;
  isLoading: boolean;
  error: string | null;
  page: number;
  hasMore: boolean;

  // Actions
  setQuery: (query: string) => void;
  setFilters: (filters: SearchFilters) => void;
  setResults: (results: PaperDTO[], total: number) => void;
  appendResults: (results: PaperDTO[], total: number) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setPage: (page: number) => void;
  reset: () => void;
}

const initialFilters: SearchFilters = {
  year_from: null,
  year_to: null,
  sources: ["arxiv", "core", "crossref", "doaj", "europepmc", "openalex", "pubmed", "semantic_scholar"],
  open_access: null,
  min_citations: null,
  venue_contains: null,
  topic: null,
  institution: null,
  type: null,
};

export const useSearchStore = create<SearchState>((set) => ({
  query: '',
  filters: initialFilters,
  results: [],
  total: 0,
  isLoading: false,
  error: null,
  page: 1,
  hasMore: false,

  setQuery: (query) => set({ query }),
  
  setFilters: (filters) => set({ filters, page: 1 }),
  
  setResults: (results, total) => set({ 
    results, 
    total,
    hasMore: results.length < total 
  }),
  
  appendResults: (newResults, total) => set((state) => ({
    results: [...state.results, ...newResults],
    total,
    hasMore: state.results.length + newResults.length < total
  })),
  
  setLoading: (isLoading) => set({ isLoading }),
  
  setError: (error) => set({ error }),
  
  setPage: (page) => set({ page }),
  
  reset: () => set({
    query: '',
    filters: initialFilters,
    results: [],
    total: 0,
    isLoading: false,
    error: null,
    page: 1,
    hasMore: false,
  }),
}));
