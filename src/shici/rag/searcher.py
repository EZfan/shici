"""Corpus search for similar classical poetry lines.

Uses a sentence-transformer model to embed query strings, then searches
the pre-built Chroma index of chinese-poetry corpora.

Run `shici index` first to build the index from the bundled data files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from sentence_transformers import SentenceTransformer
    import chromadb
    _HAS_DEPS = True
except ImportError:  # pragma: no cover
    SentenceTransformer = None  # type: ignore[assignment]
    chromadb = None  # type: ignore[assignment]
    _HAS_DEPS = False


_DATA_DIR = Path(__file__).resolve().parent.parent / "prosody" / "data"
_INDEX_DIR = Path.home() / ".cache" / "shici" / "vectors"
_DEFAULT_MODEL = "BAAI/bge-small-zh-v1.5"


class CorpusSearcher:
    """Search engine for classical poetry lines."""

    def __init__(
        self,
        index_dir: Path | str | None = None,
        model_name: str = _DEFAULT_MODEL,
    ) -> None:
        if not _HAS_DEPS:
            raise ImportError(
                "RAG requires the 'rag' extra: uv add shici --extra rag"
            )
        self.index_dir = Path(index_dir or _INDEX_DIR)
        if not self.index_dir.exists():
            raise FileNotFoundError(
                f"Index not found at {self.index_dir}. "
                "Run `shici index` to build it."
            )
        self.client = chromadb.PersistentClient(path=str(self.index_dir))
        self.collection = self.client.get_collection(name="poetry_lines")
        self.model = SentenceTransformer(model_name)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Find top-k similar lines."""
        embedding = self.model.encode([query]).tolist()
        result = self.collection.query(
            query_embeddings=embedding,
            n_results=top_k,
        )
        hits = []
        for i, (doc, meta, dist) in enumerate(
            zip(result["documents"][0], result["metadatas"][0], result["distances"][0])
        ):
            hits.append({
                "line": doc,
                "author": meta.get("author", ""),
                "title": meta.get("title", ""),
                "source": meta.get("source", ""),
                "score": 1.0 - float(dist),  # cosine similarity
            })
        return hits


def build_index(
    source_dir: Path | str,
    index_dir: Path | str | None = None,
    model_name: str = _DEFAULT_MODEL,
    batch_size: int = 256,
) -> int:
    """Build a Chroma index from chinese-poetry JSONL files.

    Returns the number of indexed documents.
    """
    if not _HAS_DEPS:
        raise ImportError(
            "RAG requires the 'rag' extra: uv add shici --extra rag"
        )
    source_dir = Path(source_dir)
    index_dir = Path(index_dir or _INDEX_DIR)
    index_dir.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(index_dir))
    collection = client.create_collection(
        name="poetry_lines",
        metadata={"model": model_name},
    )
    model = SentenceTransformer(model_name)

    docs: list[str] = []
    metas: list[dict] = []
    ids: list[str] = []

    for jsonl_file in source_dir.glob("*.jsonl"):
        with jsonl_file.open(encoding="utf-8") as f:
            for line_no, raw in enumerate(f):
                if not raw.strip():
                    continue
                import json
                rec = json.loads(raw)
                docs.append(rec["line"])
                metas.append({
                    "author": rec.get("author", ""),
                    "title": rec.get("title", ""),
                    "source": jsonl_file.stem,
                    "dynasty": rec.get("dynasty", ""),
                })
                ids.append(f"{jsonl_file.stem}:{line_no}")

                if len(docs) >= batch_size:
                    _flush(collection, model, docs, metas, ids)
                    docs, metas, ids = [], [], []

    if docs:
        _flush(collection, model, docs, metas, ids)
    return collection.count()


def _flush(collection, model, docs, metas, ids) -> None:
    embeddings = model.encode(docs, normalize_embeddings=True).tolist()
    collection.add(
        documents=docs,
        embeddings=embeddings,
        metadatas=metas,
        ids=ids,
    )


__all__ = ["CorpusSearcher", "build_index"]