import { useState, useCallback } from 'react';
import { useToast } from '@/hooks/use-toast';
import { searchPapers } from '@/services/api';
import type { PaperDTO, SearchFilters, SearchRequest } from '@/types/paper';

export function useSearch() {
  const [results, setResults] = useState<PaperDTO[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const search = useCallback(async (query: string, filters: SearchFilters, limit = 25, offset = 0) => {
    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const request: SearchRequest = {
        query: query.trim(),
        filters,
        limit,
        offset,
      };

      const response = await searchPapers(request);
      
      setResults(response.results);
      setTotal(response.total);

      if (response.warnings && response.warnings.length > 0) {
        response.warnings.forEach((warning) => {
          toast({
            title: 'Data Source Warning',
            description: warning,
            variant: 'destructive',
          });
        });
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Search failed';
      setError(errorMessage);
      toast({
        title: 'Search failed',
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  const clearResults = useCallback(() => {
    setResults([]);
    setTotal(0);
    setError(null);
  }, []);

  return {
    results,
    total,
    isLoading,
    error,
    search,
    clearResults,
  };
}
