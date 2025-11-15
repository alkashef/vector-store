"""CV vectorization: embed document and chunks, then upsert into Weaviate.

Responsibilities
- Accept a persisted final JSON (as produced by /api/docs/vectorize-local)
- Compute embeddings using OpenAI (one model across doc+chunks)
- Truncate overly long chunk text; embed normalized text only
- Upsert a Document object and Section objects with metadata and vectors
- Record embedding model and content hashes to allow idempotent re-indexing

Notes
- We rely on requests-driven WeaviateStore (no client dependency here)
- Cosine similarity is Weaviate default for HNSW; leave vectorizer="none"
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Dict, Iterable, List, Optional, Tuple

from config.settings import AppConfig
from utils.logger import AppLogger
from utils.openai_manager import OpenAIManager
from store.weaviate_store import WeaviateStore


MAX_CHARS_PER_CHUNK = 4000  # ~3k chars was OK; keep a guardrail
EMBED_MODEL_DEFAULT = "text-embedding-3-large"


def _hash_text(s: str, model: str) -> str:
    h = hashlib.sha256()
    h.update(model.encode("utf-8"))
    h.update(b"\x00")
    h.update((s or "").encode("utf-8", errors="ignore"))
    return h.hexdigest()


def _truncate(s: str, max_chars: int = MAX_CHARS_PER_CHUNK) -> str:
    if not s:
        return ""
    if len(s) <= max_chars:
        return s
    return s[:max_chars]


@dataclass
class VectorizeResult:
    document_sha: str
    document_vector_dim: int
    sections_indexed: int
    model: str


def vectorize_and_upsert(
    final_json: Dict[str, Any],
    *,
    cfg: Optional[AppConfig] = None,
    logger: Optional[AppLogger] = None,
    openai_mgr: Optional[OpenAIManager] = None,
    store: Optional[WeaviateStore] = None,
    embed_model: Optional[str] = None,
    batch_size: int = 64,
) -> VectorizeResult:
    """Embed a CV document and its chunks, then write to Weaviate.

    Inputs
    - final_json: Aggregated JSON persisted under store/results/cv_json/<sha>.json
      Expected keys: candidate_id, source, sections (list of {text, section, subsection, page_start, page_end})

    Returns
    - VectorizeResult with counts and model info
    """
    cfg = cfg or AppConfig()
    logger = logger or AppLogger(cfg.log_file_path)
    openai_mgr = openai_mgr or OpenAIManager(cfg, logger)
    store = store or WeaviateStore(cfg)
    model = embed_model or EMBED_MODEL_DEFAULT


    candidate_id = str(final_json.get("candidate_id") or "")
    source = str(final_json.get("source") or "")
    sections = final_json.get("sections") or []
    extraction = final_json.get("extraction") or {}

    # Derive sha from source content (path may have changed); prefer file sha in name
    # If not available, hash concatenated chunk text
    doc_text_concat = "\n\n".join([str((s or {}).get("text") or "") for s in sections])
    doc_hash = _hash_text(doc_text_concat, model)

    # Prepare chunk texts with truncation
    items: List[Tuple[str, Dict[str, Any]]] = []
    for ch in sections:
        txt = _truncate(str(ch.get("text") or ""))
        if not txt:
            continue
        meta = {
            "section": (ch.get("section") or "").strip(),
            "subsection": (ch.get("subsection") or "").strip(),
            "page_start": ch.get("page_start"),
            "page_end": ch.get("page_end"),
        }
        items.append((txt, meta))

    # Early exit if nothing to index
    if not items:
        logger.log_kv("CV_VEC_SKIP_EMPTY", source=source)
        return VectorizeResult(document_sha=doc_hash, document_vector_dim=0, sections_indexed=0, model=model)

    # Compute embeddings in batches
    texts = [t for t, _ in items]
    vectors: List[List[float]] = []
    for i in range(0, len(texts), max(1, int(batch_size))):
        batch = texts[i:i + batch_size]
        vecs = openai_mgr.embed_texts(batch, model=model)
        vectors.extend(vecs)

    # Optional document-level vector (coarse recall)
    doc_vector: List[float] = []
    try:
        doc_vector = openai_mgr.embed_texts([_truncate(doc_text_concat, MAX_CHARS_PER_CHUNK * 2)], model=model)[0]
    except Exception:
        doc_vector = []


    # Extract normalized metadata for routing (if present in extraction)
    def _lower_list(lst):
        return [str(x).strip().lower() for x in lst if x]

    skills_norm = []
    if isinstance(extraction, dict):
        skills = extraction.get("skills_norm", []) or []
        if isinstance(skills, str):
            # If skills_norm is a comma-separated string, split it
            skills = [s.strip() for s in skills.split(",") if s.strip()]
        skills_norm = _lower_list(skills)
    alma_mater = str(extraction.get("alma_mater") or "") if isinstance(extraction, dict) else ""
    industries_norm = []
    if isinstance(extraction, dict):
        inds = extraction.get("industries_norm", []) or []
        if isinstance(inds, str):
            inds = [s.strip() for s in inds.split(",") if s.strip()]
        industries_norm = _lower_list(inds)

    # Upsert Document (filename from path)
    filename = source.split("/")[-1].split("\\")[-1]
    attrs = {
        "candidate_id": candidate_id,
        "source": source,
        "skills_norm": skills_norm,
        "alma_mater": alma_mater,
        "industries_norm": industries_norm,
        "extraction": extraction,
        "embed_model": model,
        "embed_hash": doc_hash,
    }
    doc_obj = store.docs.write(doc_hash, filename, doc_text_concat, attrs, vector=doc_vector)
    if not doc_obj:
        raise RuntimeError("Document write failed or could not be verified in Weaviate")

    # Upsert Sections with vectors
    for (text, meta), vec in zip(items, vectors):
        embed_hash = _hash_text(text, model)
        if logger:
            logger.log_kv("VECTORIZE_SECTION_UPSERT", parent_sha=doc_hash, section=meta.get('section'), page_start=meta.get('page_start'), vector_dim=(len(vec) if vec else 0))
        res = store.upsert_section(
            parent_sha=doc_hash,
            section=meta.get("section") or "",
            subsection=meta.get("subsection") or "",
            text=text,
            page_start=meta.get("page_start"),
            page_end=meta.get("page_end"),
            vector=vec,
            model=model,
            embed_hash=embed_hash,
            skills_norm=skills_norm,
            alma_mater=alma_mater,
            industries_norm=industries_norm,
        )
        # Check upsert result and fail fast so callers see errors instead of silent drops
        if not isinstance(res, dict) or not res.get("ok"):
            err = res.get("error") if isinstance(res, dict) else str(res)
            if logger:
                logger.log_kv("VECTORIZE_SECTION_UPSERT_FAIL", parent_sha=doc_hash, section=meta.get('section'), page_start=meta.get('page_start'), error=err)
            raise RuntimeError(f"Section upsert failed: {err}")

    return VectorizeResult(
        document_sha=doc_hash,
        document_vector_dim=(len(doc_vector) if doc_vector else 0),
        sections_indexed=len(items),
        model=model,
    )


__all__ = ["vectorize_and_upsert", "VectorizeResult"]
