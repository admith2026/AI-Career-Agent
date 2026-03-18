"""Vector embedding & Qdrant integration for semantic job matching."""

import logging
import hashlib
from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
)

logger = logging.getLogger(__name__)

COLLECTION_NAME = "job_embeddings"
EMBEDDING_DIM = 1536  # OpenAI text-embedding-3-small dimension


class VectorStore:
    """Async-compatible wrapper around Qdrant for job embeddings."""

    def __init__(self, host: str = "localhost", port: int = 6333):
        self._client = QdrantClient(host=host, port=port, timeout=30)
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Create the collection if it doesn't already exist."""
        collections = [c.name for c in self._client.get_collections().collections]
        if COLLECTION_NAME not in collections:
            self._client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIM,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("Created Qdrant collection '%s'", COLLECTION_NAME)

    def _point_id(self, job_id: UUID) -> str:
        """Deterministic point ID from job UUID."""
        return hashlib.md5(str(job_id).encode()).hexdigest()

    def upsert_embedding(
        self,
        job_id: UUID,
        embedding: list[float],
        payload: dict | None = None,
    ) -> str:
        """Store or update a job embedding in Qdrant."""
        point_id = self._point_id(job_id)
        self._client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "job_id": str(job_id),
                        **(payload or {}),
                    },
                )
            ],
        )
        return point_id

    def search_similar(
        self,
        query_vector: list[float],
        limit: int = 20,
        score_threshold: float = 0.5,
    ) -> list[dict]:
        """Find jobs most similar to the query embedding."""
        results = self._client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
        )
        return [
            {
                "job_id": hit.payload.get("job_id"),
                "score": round(hit.score, 4),
                "payload": hit.payload,
            }
            for hit in results
        ]

    def delete_embedding(self, job_id: UUID) -> None:
        point_id = self._point_id(job_id)
        self._client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=[point_id],
        )

    def count(self) -> int:
        info = self._client.get_collection(COLLECTION_NAME)
        return info.points_count


async def generate_embedding(text: str, openai_client) -> list[float]:
    """Generate an embedding using OpenAI's embedding model."""
    response = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text[:8000],
    )
    return response.data[0].embedding


def build_job_text(job_title: str, company: str | None, description: str | None) -> str:
    """Combine job fields into a single text block for embedding."""
    parts = [job_title]
    if company:
        parts.append(f"Company: {company}")
    if description:
        parts.append(description[:3000])
    return "\n".join(parts)


def build_profile_text(
    headline: str | None,
    summary: str | None,
    skills: list[str],
    preferred_technologies: list[str],
) -> str:
    """Combine user profile fields for embedding."""
    parts = []
    if headline:
        parts.append(headline)
    if summary:
        parts.append(summary)
    if skills:
        parts.append("Skills: " + ", ".join(skills))
    if preferred_technologies:
        parts.append("Technologies: " + ", ".join(preferred_technologies))
    return "\n".join(parts)
