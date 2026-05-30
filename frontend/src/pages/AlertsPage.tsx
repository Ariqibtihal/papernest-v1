import { AlertsPanel } from '@/components/AlertsPanel';

export function AlertsPage() {
  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-6">Search Alerts</h1>
      <AlertsPanel />
    </div>
  );
}
