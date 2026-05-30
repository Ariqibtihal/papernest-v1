import { memo, useMemo } from 'react';
import { PaperCard } from '../PaperCard';
import { PaperListSkeleton } from './PaperCardSkeleton';
import type { PaperDTO } from '@/types/paper';

interface OptimizedPaperListProps {
  papers: PaperDTO[];
  loading?: boolean;
  onPaperClick?: (paper: PaperDTO) => void;
}

// Memoized individual paper card to prevent unnecessary re-renders
const MemoizedPaperCard = memo(PaperCard);

export function OptimizedPaperList({ papers, loading, onPaperClick }: OptimizedPaperListProps) {
  // Memoize the paper list to prevent re-renders when parent updates
  const memoizedPapers = useMemo(() => papers, [papers]);

  if (loading) {
    return <PaperListSkeleton count={8} />;
  }

  if (memoizedPapers.length === 0) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center rounded-lg border border-border bg-card p-8 text-center">
        <p className="text-muted-foreground">No papers found</p>
        <p className="mt-2 text-sm text-muted-foreground">
          Try adjusting your search or filters
        </p>
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {memoizedPapers.map((paper, index) => (
        <MemoizedPaperCard
          key={`${paper.doi || paper.title}-${index}`}
          paper={paper}
          onSelect={() => onPaperClick?.(paper)}
        />
      ))}
    </div>
  );
}
