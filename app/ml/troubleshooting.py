"""Suggests a fix for a complaint by matching its description against the knowledge base — by
meaning, not exact wording, so "it's leaking" and "water is dripping out of it" can match the
same entry even though they share no words in common.

The model (sentence-transformers, see requirements.txt) turns text into a vector such that
similar meanings land close together; matching is then just cosine similarity between the
complaint's vector and each knowledge-base entry's. The knowledge base is small and hand-seeded
(see the seed_knowledge_base migration), so its entries are embedded once per process and cached,
rather than re-embedded on every request.
"""

import logging
from functools import lru_cache

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import KnowledgeBaseEntry

logger = logging.getLogger(__name__)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MIN_SIMILARITY = 0.35

_corpus_cache: dict[tuple, np.ndarray] = {}


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer  # heavy import; deferred until first use

    return SentenceTransformer(MODEL_NAME)


def _corpus_embeddings(entries: list[KnowledgeBaseEntry]) -> np.ndarray:
    # Keyed on the entries themselves, so editing the knowledge base invalidates the cache
    # automatically instead of ever serving embeddings for text that's since changed.
    key = tuple((entry.id, entry.issue_pattern) for entry in entries)
    if key not in _corpus_cache:
        _corpus_cache.clear()  # only one knowledge-base snapshot is ever worth keeping
        texts = [entry.issue_pattern for entry in entries]
        _corpus_cache[key] = _model().encode(texts, normalize_embeddings=True)
    return _corpus_cache[key]


def suggest_fixes(db: Session, description: str, limit: int = 3) -> list[tuple[KnowledgeBaseEntry, float]]:
    """The closest knowledge-base entries to `description`, each paired with a 0-1 similarity
    score, best first. Empty if the knowledge base is empty, the model can't be loaded (e.g. it
    hasn't been downloaded yet), or nothing clears MIN_SIMILARITY."""
    entries = db.scalars(select(KnowledgeBaseEntry)).all()
    if not entries:
        return []
    try:
        corpus = _corpus_embeddings(entries)
        query = _model().encode([description], normalize_embeddings=True)[0]
    except Exception:
        logger.exception("Troubleshooting suggestion failed")
        return []
    scores = corpus @ query
    ranked = sorted(zip(entries, scores), key=lambda pair: pair[1], reverse=True)
    return [(entry, float(score)) for entry, score in ranked[:limit] if score >= MIN_SIMILARITY]
