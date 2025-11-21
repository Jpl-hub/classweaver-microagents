import type { KnowledgeDocumentSummary } from "../types";

export interface KnowledgeBaseItem {
  id: string;
  name: string;
  updated: string;
  size: string;
}

export const KNOWLEDGE_BASE_STORAGE_KEY = "classweaver:knowledge-bases";
export const KNOWLEDGE_BASE_SELECTION_KEY = "classweaver:knowledge-base-current";

export const DEFAULT_KNOWLEDGE_BASE: KnowledgeBaseItem = {
  id: "__default__",
  name: "无知识库",
  updated: "刚刚",
  size: "2.3 MB",
};

export function formatRelativeTime(value?: string): string {
  if (!value) return "刚刚";
  const target = new Date(value);
  if (Number.isNaN(target.getTime())) {
    return new Intl.DateTimeFormat("zh-CN", { month: "numeric", day: "numeric" }).format(new Date());
  }
  const diffMs = target.getTime() - Date.now();
  const minute = 60 * 1000;
  const hour = 60 * minute;
  const day = 24 * hour;
  try {
    const rtf = new Intl.RelativeTimeFormat("zh-CN", { numeric: "auto" });
    if (Math.abs(diffMs) < minute) {
      return "刚刚";
    }
    if (Math.abs(diffMs) < hour) {
      return rtf.format(Math.round(diffMs / minute), "minute");
    }
    if (Math.abs(diffMs) < day) {
      return rtf.format(Math.round(diffMs / hour), "hour");
    }
    return rtf.format(Math.round(diffMs / day), "day");
  } catch {
    return new Intl.DateTimeFormat("zh-CN", {
      month: "numeric",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(target);
  }
}

export function formatDocSize(meta?: Record<string, unknown>): string {
  if (!meta) return "-";
  const bytesValue = meta["size_bytes"];
  const bytes = typeof bytesValue === "number" ? bytesValue : Number(bytesValue ?? 0);
  if (Number.isFinite(bytes) && bytes > 0) {
    if (bytes >= 1024 * 1024) {
      return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
    }
    if (bytes >= 1024) {
      return `${Math.round(bytes / 1024)} KB`;
    }
    return `${Math.round(bytes)} B`;
  }
  const lengthValue = meta["length"];
  const length = typeof lengthValue === "number" ? lengthValue : Number(lengthValue ?? 0);
  if (Number.isFinite(length) && length > 0) {
    return `${length} 字符`;
  }
  return "-";
}

export function mapDocumentToKnowledgeBase(doc: KnowledgeDocumentSummary): KnowledgeBaseItem {
  return {
    id: doc.doc_id,
    name: doc.title?.trim() || "",
    updated: formatRelativeTime(doc.updated_at),
    size: formatDocSize(doc.metadata),
  };
}

export function normalizeKnowledgeBaseList(list: KnowledgeBaseItem[]): KnowledgeBaseItem[] {
  const seen = new Set<string>();
  const result: KnowledgeBaseItem[] = [];
  [DEFAULT_KNOWLEDGE_BASE, ...list].forEach((item) => {
    if (!item) return;
    const normalizedId =
      item.id === DEFAULT_KNOWLEDGE_BASE.name || item.id === DEFAULT_KNOWLEDGE_BASE.id ? DEFAULT_KNOWLEDGE_BASE.id : item.id?.trim();
    if (!normalizedId) return;
    if (seen.has(normalizedId)) return;
    seen.add(normalizedId);
    if (normalizedId === DEFAULT_KNOWLEDGE_BASE.id) {
      result.push(DEFAULT_KNOWLEDGE_BASE);
    } else {
      const fallbackName =
        item.name?.trim() ||
        (normalizedId.length > 8 ? `资料 ${normalizedId.slice(0, 6).toUpperCase()}` : `资料 ${normalizedId.toUpperCase()}`);
      result.push({
        ...item,
        id: normalizedId,
        name: fallbackName,
        updated: item.updated || "刚刚",
        size: item.size || "-",
      });
    }
  });
  return result;
}

export function resolveKnowledgeBaseName(
  docId: string | null | undefined,
  bases: KnowledgeBaseItem[],
  fallback?: string,
): string {
  if (!docId) {
    return fallback ?? "知识库";
  }
  const match = bases.find((base) => base.id === docId);
  if (match) return match.name;
  if (fallback) return fallback;
  return docId.length > 8 ? `资料 ${docId.slice(0, 6).toUpperCase()}` : docId.toUpperCase();
}
