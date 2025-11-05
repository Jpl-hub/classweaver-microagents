import io
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from django.conf import settings
from django.db import transaction

from docx import Document as DocxDocument
from PyPDF2 import PdfReader

from src.agents.utils import build_client
from src.core.models import KnowledgeChunk, KnowledgeDocument
from src.services.ppt import extract_text as extract_ppt_text

from .store import get_store

ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx", ".pptx"}


def _read_text_file(file_obj: Any) -> str:
    file_obj.seek(0)
    data = file_obj.read()
    if isinstance(data, bytes):
        return data.decode("utf-8", errors="ignore")
    return str(data)


def _read_pdf_file(file_obj: Any) -> str:
    file_obj.seek(0)
    reader = PdfReader(file_obj)
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text.strip())
    return "\n".join(pages)


def _read_docx_file(file_obj: Any) -> str:
    file_obj.seek(0)
    if hasattr(file_obj, "read"):
        data = file_obj.read()
        stream = io.BytesIO(data)
    else:
        stream = file_obj
    document = DocxDocument(stream)
    paragraphs = [para.text.strip() for para in document.paragraphs if para.text.strip()]
    return "\n".join(paragraphs)


def _extract_text(file_obj: Any, name: str) -> str:
    suffix = Path(name).suffix.lower()
    if suffix == ".txt":
        return _read_text_file(file_obj)
    if suffix == ".pdf":
        return _read_pdf_file(file_obj)
    if suffix == ".docx":
        return _read_docx_file(file_obj)
    if suffix == ".pptx":
        return extract_ppt_text(file_obj)
    raise ValueError(f"Unsupported file extension: {suffix}")


def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> List[str]:
    sanitized = " ".join(text.split())
    if not sanitized:
        return []
    chunks: List[str] = []
    step = max(chunk_size - overlap, 1)
    start = 0
    while start < len(sanitized):
        chunk = sanitized[start : start + chunk_size]
        chunks.append(chunk)
        start += step
    return chunks


@transaction.atomic
def ingest_documents(*, files: Iterable[Any]) -> Dict[str, Any]:
    """Ingest uploaded documents, create knowledge chunks, and persist embeddings."""
    agent_settings = settings.AGENT_SETTINGS
    backend = agent_settings["vector_backend"]
    store = get_store(backend)
    client = build_client(agent_settings)

    chunk_records: List[Dict[str, Any]] = []
    chunk_texts: List[str] = []
    documents_created: List[Tuple[str, str]] = []

    for file_obj in files:
        if not file_obj:
            continue
        name = getattr(file_obj, "name", f"doc-{uuid.uuid4().hex}.txt")
        suffix = Path(name).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {suffix}")

        text = _extract_text(file_obj, name).strip()
        if not text:
            continue

        doc_id = uuid.uuid4().hex
        title = Path(name).stem
        document, _created = KnowledgeDocument.objects.get_or_create(
            doc_id=doc_id,
            defaults={
                "title": title,
                "source_path": name,
                "metadata": {"length": len(text)},
            },
        )
        if _created:
            documents_created.append((doc_id, title))

        chunks = _chunk_text(text)
        for index, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}-{index}"
            chunk_texts.append(chunk)
            chunk_records.append(
                {
                    "doc_id": doc_id,
                    "chunk_id": chunk_id,
                    "text": chunk,
                    "metadata": {
                        "position": index,
                        "source": name,
                    },
                    "document": document,
                }
            )

    if not chunk_records:
        return {"docs_created": 0, "chunks": 0, "backend": backend, "dim": 0}

    embedding_vectors = client.embed(model=agent_settings["embedding_model"], texts=chunk_texts)

    for record, embedding in zip(chunk_records, embedding_vectors, strict=False):
        KnowledgeChunk.objects.update_or_create(
            document=record["document"],
            chunk_id=record["chunk_id"],
            defaults={
                "text": record["text"],
                "embedding": list(embedding),
                "metadata": record["metadata"],
            },
        )

    metadata_payload = [
        {
            "doc_id": record["doc_id"],
            "chunk_id": record["chunk_id"],
            "text": record["text"],
            "title": record["document"].title,
            "metadata": record["metadata"],
        }
        for record in chunk_records
    ]
    store.upsert_embeddings(embeddings=embedding_vectors, metadata=metadata_payload)

    dimension = len(embedding_vectors[0]) if embedding_vectors else 0
    return {
        "docs_created": len(documents_created),
        "chunks": len(chunk_records),
        "backend": backend,
        "dim": dimension,
    }
