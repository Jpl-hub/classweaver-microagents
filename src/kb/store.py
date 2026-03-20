import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from django.conf import settings
from django.db import connection
from pgvector.django import CosineDistance

from src.core.models import KnowledgeChunk

try:
    import faiss  # type: ignore
except ImportError:  # pragma: no cover - handled via runtime checks
    faiss = None

logger = logging.getLogger(__name__)


class VectorStoreError(RuntimeError):
    """Raised when vector store operations fail."""


class FaissStore:
    def __init__(self, index_path: Path, meta_path: Path):
        if faiss is None:
            raise VectorStoreError("faiss-cpu is required for FAISS backend but is not installed.")

        self.index_path = index_path
        self.meta_path = meta_path
        self.index = None
        self.metadata: List[Dict[str, Any]] = []
        self.dimension: int | None = None
        self._load()

    def _load(self) -> None:
        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            self.dimension = self.index.d
        if self.meta_path.exists():
            with self.meta_path.open("r", encoding="utf-8") as handle:
                self.metadata = json.load(handle)
        else:
            self.metadata = []

    def _ensure_index(self, dimension: int) -> None:
        if self.index is None:
            self.index = faiss.IndexFlatIP(dimension)
            self.dimension = dimension
        elif self.dimension != dimension:
            logger.warning(
                "Embedding dimension mismatch detected for %s (expected %s, received %s). Resetting FAISS index.",
                self.index_path,
                self.dimension,
                dimension,
            )
            self._reset_index(dimension)

    def upsert(self, embeddings: List[List[float]], metadata: List[Dict[str, Any]]) -> None:
        if not embeddings:
            return
        array = np.array(embeddings, dtype="float32")
        if array.ndim != 2:
            raise VectorStoreError("Embeddings must be a 2D array.")
        dimension = array.shape[1]
        self._ensure_index(dimension)
        faiss.normalize_L2(array)
        self.index.add(array)
        self.metadata.extend(metadata)
        self._save()

    def _reset_index(self, dimension: int) -> None:
        """Drop existing FAISS data on dimension mismatch."""
        self.index = faiss.IndexFlatIP(dimension)
        self.dimension = dimension
        self.metadata = []
        if self.index_path.exists():
            self.index_path.unlink()
        if self.meta_path.exists():
            self.meta_path.unlink()
        self._save()

    def count(self, *, base_id: int | None = None, doc_ids: List[str] | None = None) -> int:
        if base_id is None and not doc_ids:
            return len(self.metadata)
        doc_id_set = set(doc_ids or [])
        return sum(
            1
            for item in self.metadata
            if (base_id is None or str(item.get("base_id")) == str(base_id))
            and (not doc_id_set or item.get("doc_id") in doc_id_set)
        )

    def search(
        self,
        embedding: List[float],
        top_k: int,
        *,
        base_id: int | None = None,
        doc_ids: List[str] | None = None,
    ) -> List[Tuple[float, Dict[str, Any]]]:
        if self.index is None or self.index.ntotal == 0:
            return []
        vector = np.array([embedding], dtype="float32")
        faiss.normalize_L2(vector)
        distances, indices = self.index.search(vector, top_k)
        doc_id_set = set(doc_ids or [])
        results: List[Tuple[float, Dict[str, Any]]] = []
        for score, idx in zip(distances[0], indices[0], strict=False):
            if idx == -1:
                continue
            try:
                meta = self.metadata[idx]
            except IndexError:
                continue
            if base_id is not None and str(meta.get("base_id")) != str(base_id):
                continue
            if doc_id_set and meta.get("doc_id") not in doc_id_set:
                continue
            results.append((float(score), meta))
        return results

    def _save(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.meta_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_path))
        with self.meta_path.open("w", encoding="utf-8") as handle:
            json.dump(self.metadata, handle, ensure_ascii=False, indent=2)

    def upsert_embeddings(self, *, embeddings: List[List[float]], metadata: List[Dict[str, Any]]) -> None:
        """Compatibility wrapper used by ingestion pipeline."""
        self.upsert(embeddings, metadata)


class PgVectorStore:
    def __init__(self) -> None:
        self.vendor = connection.vendor

    def _ensure_postgres(self) -> None:
        if self.vendor != "postgresql":
            raise VectorStoreError("pgvector backend requires a PostgreSQL database connection.")

    def count(self, *, base_id: int | None = None, doc_ids: List[str] | None = None) -> int:
        queryset = KnowledgeChunk.objects.select_related("document")
        if base_id is not None:
            queryset = queryset.filter(document__base_id=base_id)
        if doc_ids:
            queryset = queryset.filter(document__doc_id__in=doc_ids)
        return queryset.exclude(embedding_vector__isnull=True).count()

    def search(
        self,
        embedding: List[float],
        top_k: int,
        *,
        base_id: int | None = None,
        doc_ids: List[str] | None = None,
    ) -> List[Tuple[float, Dict[str, Any]]]:
        self._ensure_postgres()
        queryset = KnowledgeChunk.objects.select_related("document")
        if base_id is not None:
            queryset = queryset.filter(document__base_id=base_id)
        if doc_ids:
            queryset = queryset.filter(document__doc_id__in=doc_ids)
        queryset = queryset.exclude(embedding_vector__isnull=True)
        queryset = queryset.annotate(distance=CosineDistance("embedding_vector", embedding)).order_by("distance")[:top_k]

        results: List[Tuple[float, Dict[str, Any]]] = []
        for chunk in queryset:
            distance = float(getattr(chunk, "distance", 1.0) or 1.0)
            similarity = 1.0 - distance
            results.append(
                (
                    similarity,
                    {
                        "doc_id": chunk.document.doc_id,
                        "chunk_id": chunk.chunk_id,
                        "text": chunk.text,
                        "base_id": chunk.document.base_id,
                        "title": chunk.document.title,
                        "metadata": chunk.metadata or {},
                    },
                )
            )
        return results

    def upsert_embeddings(self, *, embeddings: List[List[float]], metadata: List[Dict[str, Any]]) -> None:
        self._ensure_postgres()
        if not embeddings or not metadata:
            return
        embedding_map = {
            item["chunk_id"]: list(vector)
            for item, vector in zip(metadata, embeddings, strict=False)
            if item.get("chunk_id")
        }
        if not embedding_map:
            return
        chunks = list(KnowledgeChunk.objects.filter(chunk_id__in=embedding_map.keys()))
        for chunk in chunks:
            vector = embedding_map.get(chunk.chunk_id)
            if vector is None:
                continue
            chunk.embedding = vector
            chunk.embedding_vector = vector
        if chunks:
            KnowledgeChunk.objects.bulk_update(chunks, ["embedding", "embedding_vector"])


_STORE_CACHE: Dict[str, Any] = {}


def _faiss_store() -> FaissStore:
    agent_settings = settings.AGENT_SETTINGS
    index_path = Path(agent_settings["vstore_path"])
    meta_path = Path(agent_settings["vstore_meta"])
    cache_key = f"faiss::{index_path}"
    if cache_key not in _STORE_CACHE:
        _STORE_CACHE[cache_key] = FaissStore(index_path=index_path, meta_path=meta_path)
    return _STORE_CACHE[cache_key]


def get_store(backend: str) -> Any:
    backend = (backend or "faiss").lower()
    if backend == "faiss":
        return _faiss_store()
    if backend == "pgvector":
        return PgVectorStore()
    raise VectorStoreError(f"Unsupported vector backend: {backend}")


def upsert_embeddings(*, embeddings: List[List[float]], metadata: List[Dict[str, Any]]) -> None:
    store = get_store(settings.AGENT_SETTINGS["vector_backend"])
    store.upsert_embeddings(embeddings=embeddings, metadata=metadata)


def clear_store_cache() -> None:
    """Clear cached vector-store instances (used by management commands/tests)."""
    _STORE_CACHE.clear()


def clear_store_files() -> None:
    """Delete on-disk FAISS index and metadata for a clean rebuild."""
    try:
        store = _STORE_CACHE.get(f"faiss::{Path(settings.AGENT_SETTINGS['vstore_path'])}")
        if store:
            if Path(store.index_path).exists():
                Path(store.index_path).unlink()
            if Path(store.meta_path).exists():
                Path(store.meta_path).unlink()
    finally:
        clear_store_cache()
