export type ActionStatusState = "pending" | "running" | "completed";

export interface ActionStatusEntry {
  status: ActionStatusState;
  note?: string;
  updated_at: number;
}

const ACTION_STATUS_PREFIX = "classweaver:action-status::";

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

function storageKey(jobId: string): string {
  return `${ACTION_STATUS_PREFIX}${jobId}`;
}

function safeParse<T>(value: string | null): T | null {
  if (!value) {
    return null;
  }
  try {
    return JSON.parse(value) as T;
  } catch {
    return null;
  }
}

export function getActionStatusMap(jobId: string | number | undefined | null): Record<string, ActionStatusEntry> {
  if (!isBrowser() || !jobId) {
    return {};
  }
  const key = storageKey(String(jobId));
  const parsed = safeParse<Record<string, ActionStatusEntry>>(window.sessionStorage.getItem(key));
  if (!parsed) {
    return {};
  }
  return parsed;
}

function persistActionStatus(jobId: string, map: Record<string, ActionStatusEntry>): void {
  if (!isBrowser()) {
    return;
  }
  const key = storageKey(jobId);
  window.sessionStorage.setItem(key, JSON.stringify(map));
}

export function setActionStatus(
  jobId: string | number | undefined | null,
  actionId: string | undefined,
  status: ActionStatusState,
  note?: string,
): ActionStatusEntry | null {
  if (!jobId || !actionId) {
    return null;
  }
  const id = String(jobId);
  const map = getActionStatusMap(id);
  const entry: ActionStatusEntry = {
    status,
    note,
    updated_at: Date.now(),
  };
  map[actionId] = entry;
  persistActionStatus(id, map);
  return entry;
}

export function clearActionStatuses(jobId: string | number | undefined | null): void {
  if (!isBrowser() || !jobId) {
    return;
  }
  const key = storageKey(String(jobId));
  window.sessionStorage.removeItem(key);
}
