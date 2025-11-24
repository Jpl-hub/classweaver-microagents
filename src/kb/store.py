import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from django.conf import settings

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

    def search(self, embedding: List[float], top_k: int) -> List[Tuple[float, Dict[str, Any]]]:
        if self.index is None or self.index.ntotal == 0:
            return []
        vector = np.array([embedding], dtype="float32")
        faiss.normalize_L2(vector)
        distances, indices = self.index.search(vector, top_k)
        results: List[Tuple[float, Dict[str, Any]]] = []
        for score, idx in zip(distances[0], indices[0], strict=False):
            if idx == -1:
                continue
            try:
                meta = self.metadata[idx]
            except IndexError:
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
        raise VectorStoreError("pgvector backend is not yet implemented.")
    raise VectorStoreError(f"Unsupported vector backend: {backend}")


def upsert_embeddings(*, embeddings: List[List[float]], metadata: List[Dict[str, Any]]) -> None:
    store = get_store(settings.AGENT_SETTINGS["vector_backend"])
    store.upsert(embeddings, metadata)


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
