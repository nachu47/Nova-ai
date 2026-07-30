import hashlib
import math
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import KnowledgeChunk, KnowledgeDocument
from app.services.openai_service import create_embedding


def chunk_text(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return []
    chunks: list[str] = []
    cursor = 0
    while cursor < len(clean):
        end = min(len(clean), cursor + size)
        if end < len(clean):
            boundary = clean.rfind(". ", cursor, end)
            if boundary > cursor + size // 2:
                end = boundary + 1
        chunks.append(clean[cursor:end].strip())
        if end == len(clean):
            break
        cursor = max(cursor + 1, end - overlap)
    return chunks


def index_document(db: Session, document: KnowledgeDocument, content: str) -> int:
    pieces = chunk_text(content)
    for position, piece in enumerate(pieces):
        db.add(
            KnowledgeChunk(
                document_id=document.id,
                organization_id=document.organization_id,
                content=piece,
                position=position,
                token_count=max(1, len(piece) // 4),
                embedding=create_embedding(piece),
                metadata_json={"title": document.title, "source_url": document.source_url},
            )
        )
    document.status = "ready"
    db.commit()
    return len(pieces)


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    numerator = sum(x * y for x, y in zip(a, b, strict=True))
    denominator = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return numerator / denominator if denominator else 0.0


def search_knowledge(db: Session, organization_id: str, query: str, limit: int = 5) -> list[dict]:
    query_vector = create_embedding(query)
    chunks = db.scalars(
        select(KnowledgeChunk).where(KnowledgeChunk.organization_id == organization_id).limit(2000)
    ).all()
    ranked = sorted(((cosine(query_vector, c.embedding), c) for c in chunks), key=lambda item: item[0], reverse=True)
    return [
        {"chunk_id": chunk.id, "score": round(score, 4), "content": chunk.content, "metadata": chunk.metadata_json}
        for score, chunk in ranked[:limit]
        if score > 0
    ]


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()
