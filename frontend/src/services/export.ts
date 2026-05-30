import { PaperDTO } from "@/types/paper";

export async function exportPapers(papers: PaperDTO[], format: "json" | "csv" | "bibtex"): Promise<Blob> {
  const res = await fetch(`/api/v1/export?format=${format}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(papers),
  });
  if (!res.ok) throw new Error("Export failed");
  return res.blob();
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}
