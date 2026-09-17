import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.graph_models import DocumentChunk

logger = logging.getLogger(__name__)


class RAGService:
    """
    ATHENA Local RAG Engine:
    Processes user-uploaded research papers, PDFs, guidelines, and specs.
    Chunks text, stores in PostgreSQL DocumentChunk table, and retrieves context for agents.
    """
    def __init__(self, db: Session):
        self.db = db

    def ingesting_document(self, project_id: str, filename: str, content: str, chunk_size: int = 500) -> List[DocumentChunk]:
        """
        Splits text content into chunks and stores them in the database.
        """
        words = content.split()
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunk_text = " ".join(words[i:i + chunk_size])
            chunk_obj = DocumentChunk(
                project_id=project_id,
                filename=filename,
                chunk_index=len(chunks),
                content=chunk_text,
                metadata_json={"word_count": len(words[i:i + chunk_size])}
            )
            self.db.add(chunk_obj)
            chunks.append(chunk_obj)

        self.db.commit()
        logger.info(f"Ingested {len(chunks)} chunks for file '{filename}' in project '{project_id}'.")
        return chunks

    def search_context(self, project_id: str, query: str, top_k: int = 3) -> str:
        """
        Retrieves top-k relevant document chunks for an agent query.
        """
        chunks = self.db.query(DocumentChunk).filter(
            DocumentChunk.project_id == project_id
        ).all()

        if not chunks:
            return ""

        # Basic keyword relevance scoring for local execution without external embedding services
        query_words = set(query.lower().split())
        scored_chunks = []
        for chunk in chunks:
            chunk_words = set(chunk.content.lower().split())
            overlap = len(query_words.intersection(chunk_words))
            scored_chunks.append((overlap, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [c[1].content for c in scored_chunks[:top_k] if c[0] > 0]

        return "\n\n---\n\n".join(top_chunks) if top_chunks else ""
