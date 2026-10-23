"""Suggests a fix for a complaint by matching its description against the knowledge base — by
meaning, not exact wording, so "it's leaking" and "water is dripping out of it" can match the
same entry even though they share no words in common.

The model (sentence-transformers, see requirements.txt) turns text into a vector such that
similar meanings land close together; matching is then just cosine similarity between the
complaint's vector and each knowledge-base entry's. The knowledge base is small and hand-seeded
(see the seed_knowledge_base migration), so its entries are embedded once per process and cached,
rather than re-embedded on every request. Each shop has its own entries, so each gets its own
cache slot.
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

# shop_id -> (the entries the embeddings were made from, the embeddings)
_corpus_cache: dict[int, tuple[tuple, np.ndarray]] = {}


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer  # heavy import; deferred until first use

    return SentenceTransformer(MODEL_NAME)


def _corpus_embeddings(shop_id: int, entries: list[KnowledgeBaseEntry]) -> np.ndarray:
    # Checked against the entries themselves, so editing the knowledge base invalidates the cache
    # automatically instead of ever serving embeddings for text that's since changed. Only the
    # latest snapshot per shop is ever worth keeping.
    key = tuple((entry.id, entry.issue_pattern) for entry in entries)
    cached = _corpus_cache.get(shop_id)
    if cached is None or cached[0] != key:
        texts = [entry.issue_pattern for entry in entries]
        _corpus_cache[shop_id] = (key, _model().encode(texts, normalize_embeddings=True))
    return _corpus_cache[shop_id][1]


def suggest_fixes(
    db: Session, description: str, *, shop_id: int, limit: int = 3
) -> list[tuple[KnowledgeBaseEntry, float]]:
    """The closest of the shop's knowledge-base entries to `description`, each paired with a 0-1 similarity
    score, best first. Empty if the knowledge base is empty, the model can't be loaded (e.g. it
    hasn't been downloaded yet), or nothing clears MIN_SIMILARITY."""
    entries = db.scalars(
        select(KnowledgeBaseEntry).where(KnowledgeBaseEntry.shop_id == shop_id).order_by(KnowledgeBaseEntry.id)
    ).all()
    if not entries:
        return []
    try:
        corpus = _corpus_embeddings(shop_id, entries)
        query = _model().encode([description], normalize_embeddings=True)[0]
    except Exception:
        logger.exception("Troubleshooting suggestion failed")
        return []
    scores = corpus @ query
    ranked = sorted(zip(entries, scores), key=lambda pair: pair[1], reverse=True)
    return [(entry, float(score)) for entry, score in ranked[:limit] if score >= MIN_SIMILARITY]


def preload() -> None:
    """Loads the model ahead of the first suggestion (see main.py's startup), which otherwise pays
    several seconds for it. A failure here is only logged: suggest_fixes copes on its own."""
    try:
        _model().encode(["warm up"])
    except Exception:
        logger.exception("Couldn't preload the troubleshooting model")
