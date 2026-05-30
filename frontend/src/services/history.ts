import { SearchFilters } from "@/types/paper";

const STORAGE_KEY = "paperlens_search_history";
const MAX_ITEMS = 10;

export interface HistoryEntry {
  query: string;
  filters: SearchFilters;
  timestamp: number;
}

export function getHistory(): HistoryEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as HistoryEntry[]) : [];
  } catch {
    return [];
  }
}

export function addHistory(entry: Omit<HistoryEntry, "timestamp">) {
  const items = getHistory();
  const next = [{ ...entry, timestamp: Date.now() }, ...items];
  const deduped = next.filter(
    (item, idx, arr) =>
      arr.findIndex(
        (i) => i.query === item.query && JSON.stringify(i.filters) === JSON.stringify(item.filters)
      ) === idx
  );
  localStorage.setItem(STORAGE_KEY, JSON.stringify(deduped.slice(0, MAX_ITEMS)));
}

export function clearHistory() {
  localStorage.removeItem(STORAGE_KEY);
}
